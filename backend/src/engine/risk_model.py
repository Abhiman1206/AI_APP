"""Risk model utilities for PRD-aligned ML scoring and explainability.

This module provides a robust fallback path so the pipeline remains usable even
when training data or optional ML packages are unavailable in hackathon setups.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np


try:
	from imblearn.over_sampling import SMOTE
except Exception:  # pragma: no cover
	SMOTE = None

try:
	import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
	plt = None

try:
	from pandas_datareader import data as pdr_data
except Exception:  # pragma: no cover
	pdr_data = None

try:
	import shap
except Exception:  # pragma: no cover
	shap = None

try:
	from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover
	IsolationForest = None

try:
	from xgboost import XGBClassifier
except Exception:  # pragma: no cover
	XGBClassifier = None


FEATURE_ORDER = [
	"current_ratio",
	"debt_to_equity",
	"net_profit_margin",
	"avg_monthly_credits",
	"gst_bank_variance_pct",
	"gst_filings_on_time",
	"litigation_count",
	"news_sentiment_score",
	"fed_funds",
	"inflation_yoy",
	"gdp_growth_proxy",
]


def _safe_float(value, default: float) -> float:
	try:
		if value is None:
			return default
		return float(value)
	except (TypeError, ValueError):
		return default


def _news_to_score(news_sentiment: str | None) -> float:
	mapping = {
		"positive": 0.85,
		"mostly positive": 0.75,
		"neutral": 0.55,
		"mostly negative": 0.35,
		"negative": 0.20,
	}
	if not news_sentiment:
		return 0.55
	return mapping.get(str(news_sentiment).strip().lower(), 0.55)


def get_macro_indicators() -> dict:
	"""Fetch macro proxies (FRED) with resilient defaults when offline."""
	defaults = {
		"fed_funds": 6.0,
		"inflation_yoy": 5.0,
		"gdp_growth_proxy": 6.5,
		"source": "default-fallback",
	}
	if pdr_data is None:
		return defaults

	try:
		end = datetime.utcnow().date()
		start = end - timedelta(days=500)
		series = pdr_data.DataReader(["FEDFUNDS", "CPIAUCSL", "GDP"], "fred", start, end)

		fed_funds = float(series["FEDFUNDS"].dropna().iloc[-1])

		cpi = series["CPIAUCSL"].dropna()
		if len(cpi) >= 13:
			inflation_yoy = float((cpi.iloc[-1] / cpi.iloc[-13] - 1.0) * 100)
		else:
			inflation_yoy = defaults["inflation_yoy"]

		gdp = series["GDP"].dropna()
		if len(gdp) >= 2:
			gdp_growth_proxy = float((gdp.iloc[-1] / gdp.iloc[-2] - 1.0) * 400)
		else:
			gdp_growth_proxy = defaults["gdp_growth_proxy"]

		return {
			"fed_funds": round(fed_funds, 2),
			"inflation_yoy": round(inflation_yoy, 2),
			"gdp_growth_proxy": round(gdp_growth_proxy, 2),
			"source": "fred",
		}
	except Exception:
		return defaults


def build_risk_features(
	financial_highlights: dict,
	bank_data: dict,
	gst_data: dict,
	research_data: dict,
) -> dict:
	"""Build a feature vector from extracted pipeline outputs."""
	bank_summary = (bank_data or {}).get("summary") or {}
	gst_summary = (gst_data or {}).get("last_12_months") or {}

	revenue = _safe_float(financial_highlights.get("revenue"), 0.0)
	net_profit = _safe_float(financial_highlights.get("net_profit"), 0.0)
	net_margin = (net_profit / revenue * 100.0) if revenue > 0 else 0.0

	avg_monthly_credits = _safe_float(bank_summary.get("avg_monthly_credits"), 0.0)
	total_turnover = _safe_float(gst_summary.get("total_turnover"), 0.0)
	annual_credits = avg_monthly_credits * 12.0 if avg_monthly_credits > 0 else 0.0
	gst_bank_variance_pct = abs(total_turnover - annual_credits) / annual_credits * 100.0 if annual_credits > 0 else 0.0

	macro = get_macro_indicators()

	features = {
		"current_ratio": _safe_float(financial_highlights.get("current_ratio"), 1.0),
		"debt_to_equity": _safe_float(financial_highlights.get("debt_to_equity"), 1.0),
		"net_profit_margin": round(net_margin, 2),
		"avg_monthly_credits": avg_monthly_credits,
		"gst_bank_variance_pct": round(gst_bank_variance_pct, 2),
		"gst_filings_on_time": _safe_float(gst_summary.get("filings_on_time"), 10.0),
		"litigation_count": float(len((research_data or {}).get("litigation_flags") or [])),
		"news_sentiment_score": _news_to_score((research_data or {}).get("news_sentiment")),
		"fed_funds": _safe_float(macro.get("fed_funds"), 6.0),
		"inflation_yoy": _safe_float(macro.get("inflation_yoy"), 5.0),
		"gdp_growth_proxy": _safe_float(macro.get("gdp_growth_proxy"), 6.5),
	}
	features["macro_source"] = macro.get("source", "unknown")
	return features


def _synthetic_training_frame(seed: int = 42, n_samples: int = 900) -> tuple[np.ndarray, np.ndarray]:
	rng = np.random.default_rng(seed)
	current_ratio = rng.normal(1.3, 0.35, n_samples).clip(0.2, 3.5)
	debt_to_equity = rng.normal(1.2, 0.8, n_samples).clip(0.0, 6.0)
	net_profit_margin = rng.normal(9.0, 8.0, n_samples).clip(-20.0, 35.0)
	avg_monthly_credits = rng.normal(1.8e7, 1.2e7, n_samples).clip(5e4, 9e7)
	gst_bank_variance_pct = rng.normal(14.0, 9.0, n_samples).clip(0.0, 100.0)
	gst_filings_on_time = rng.integers(5, 13, n_samples).astype(float)
	litigation_count = rng.poisson(1.1, n_samples).clip(0, 12).astype(float)
	news_sentiment_score = rng.normal(0.58, 0.2, n_samples).clip(0.0, 1.0)
	fed_funds = rng.normal(5.8, 1.0, n_samples).clip(0.0, 12.0)
	inflation_yoy = rng.normal(5.0, 2.0, n_samples).clip(1.0, 15.0)
	gdp_growth_proxy = rng.normal(6.2, 1.6, n_samples).clip(-2.0, 12.0)

	x = np.column_stack(
		[
			current_ratio,
			debt_to_equity,
			net_profit_margin,
			avg_monthly_credits,
			gst_bank_variance_pct,
			gst_filings_on_time,
			litigation_count,
			news_sentiment_score,
			fed_funds,
			inflation_yoy,
			gdp_growth_proxy,
		]
	)

	risk_signal = (
		1.2 * (debt_to_equity > 2.2).astype(float)
		+ 1.1 * (gst_bank_variance_pct > 28).astype(float)
		+ 1.0 * (current_ratio < 0.9).astype(float)
		+ 0.7 * (litigation_count > 2).astype(float)
		+ 0.6 * (news_sentiment_score < 0.45).astype(float)
		+ 0.4 * (net_profit_margin < 0).astype(float)
	)
	noise = rng.normal(0, 0.6, n_samples)
	y = ((risk_signal + noise) > 2.0).astype(int)
	return x, y


@dataclass
class CreditModelOutput:
	default_probability: float
	ml_credit_score: float
	model_recommendation: str
	risk_premium_bps: int
	loan_limit_pct: int
	feature_contributions: dict
	explainability: dict


class RiskScoringEngine:
	"""Train/use XGBoost + SMOTE and produce SHAP explanations."""

	def __init__(self) -> None:
		self.model = None
		self.explainer = None
		self.trained = False

	def _fit(self) -> None:
		if self.trained:
			return

		if XGBClassifier is None:
			self.trained = False
			return

		x, y = _synthetic_training_frame()

		if SMOTE is not None:
			x_res, y_res = SMOTE(random_state=42).fit_resample(x, y)
		else:
			x_res, y_res = x, y

		model = XGBClassifier(
			n_estimators=180,
			max_depth=4,
			learning_rate=0.06,
			subsample=0.9,
			colsample_bytree=0.9,
			objective="binary:logistic",
			eval_metric="logloss",
			random_state=42,
		)
		model.fit(x_res, y_res)

		self.model = model
		if shap is not None:
			try:
				self.explainer = shap.TreeExplainer(model)
			except Exception:
				self.explainer = None
		self.trained = True

	def _build_shap_plot(self, shap_values: np.ndarray) -> str | None:
		if plt is None:
			return None

		contributions = {name: float(val) for name, val in zip(FEATURE_ORDER, shap_values)}
		top = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:8]
		labels = [k for k, _ in top][::-1]
		values = [v for _, v in top][::-1]

		fig, ax = plt.subplots(figsize=(7.5, 3.8))
		colors = ["#059669" if val >= 0 else "#DC2626" for val in values]
		ax.barh(labels, values, color=colors)
		ax.axvline(0, color="#111827", linewidth=1)
		ax.set_title("SHAP Feature Contributions", fontsize=10)
		ax.set_xlabel("Impact on Default Probability (log-odds scale)", fontsize=8)
		ax.tick_params(axis="y", labelsize=7)
		ax.tick_params(axis="x", labelsize=7)
		plt.tight_layout()

		image_buf = io.BytesIO()
		fig.savefig(image_buf, format="png", dpi=180)
		plt.close(fig)
		image_buf.seek(0)
		return base64.b64encode(image_buf.read()).decode("ascii")

	def score(self, features: dict) -> CreditModelOutput:
		self._fit()

		x_row = np.array([features.get(name, 0.0) for name in FEATURE_ORDER], dtype=float).reshape(1, -1)

		if self.model is None:
			# Heuristic fallback if XGBoost is unavailable.
			risk = 0.15
			risk += 0.20 if features.get("debt_to_equity", 1.0) > 2.0 else 0.0
			risk += 0.20 if features.get("gst_bank_variance_pct", 0.0) > 30.0 else 0.0
			risk += 0.15 if features.get("current_ratio", 1.0) < 1.0 else 0.0
			risk += 0.10 if features.get("litigation_count", 0.0) >= 2 else 0.0
			risk += 0.10 if features.get("news_sentiment_score", 0.55) < 0.45 else 0.0
			default_probability = float(max(0.02, min(0.95, risk)))
			contributions = {
				"debt_to_equity": round(float(features.get("debt_to_equity", 1.0)), 4),
				"gst_bank_variance_pct": round(float(features.get("gst_bank_variance_pct", 0.0)), 4),
				"current_ratio": round(float(features.get("current_ratio", 1.0)), 4),
				"litigation_count": round(float(features.get("litigation_count", 0.0)), 4),
				"news_sentiment_score": round(float(features.get("news_sentiment_score", 0.55)), 4),
			}
			explainability = {
				"method": "heuristic-fallback",
				"shap_plot_png_b64": None,
			}
		else:
			default_probability = float(self.model.predict_proba(x_row)[0][1])
			contributions = {}
			shap_plot_b64 = None
			if self.explainer is not None:
				try:
					shap_vals = self.explainer.shap_values(x_row)
					if isinstance(shap_vals, list):
						shap_arr = np.array(shap_vals[1][0], dtype=float)
					else:
						shap_arr = np.array(shap_vals[0], dtype=float)

					contributions = {
						name: round(float(val), 6)
						for name, val in zip(FEATURE_ORDER, shap_arr)
					}
					shap_plot_b64 = self._build_shap_plot(shap_arr)
				except Exception:
					contributions = {}
			explainability = {
				"method": "shap" if contributions else "xgboost-no-shap",
				"shap_plot_png_b64": shap_plot_b64,
			}

		ml_credit_score = round((1.0 - default_probability) * 100.0, 1)
		if default_probability <= 0.25:
			model_recommendation = "APPROVE"
		elif default_probability <= 0.45:
			model_recommendation = "REFER"
		else:
			model_recommendation = "REJECT"

		risk_premium_bps = int(max(75, min(600, 80 + default_probability * 500)))
		loan_limit_pct = int(max(30, min(100, 100 - default_probability * 70)))

		top_contribs = dict(
			sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:8]
		)

		return CreditModelOutput(
			default_probability=round(default_probability, 4),
			ml_credit_score=ml_credit_score,
			model_recommendation=model_recommendation,
			risk_premium_bps=risk_premium_bps,
			loan_limit_pct=loan_limit_pct,
			feature_contributions=top_contribs,
			explainability=explainability,
		)


_RISK_ENGINE = RiskScoringEngine()


def score_credit_application(features: dict) -> dict:
	"""Public scoring helper used by the FastAPI pipeline."""
	result = _RISK_ENGINE.score(features)
	return {
		"default_probability": result.default_probability,
		"ml_credit_score": result.ml_credit_score,
		"model_recommendation": result.model_recommendation,
		"risk_premium_bps": result.risk_premium_bps,
		"loan_limit_pct": result.loan_limit_pct,
		"feature_contributions": result.feature_contributions,
		"explainability": result.explainability,
		"features_used": {k: features.get(k) for k in FEATURE_ORDER},
	}


_ANOMALY_MODEL = None


def _get_anomaly_model():
	global _ANOMALY_MODEL
	if _ANOMALY_MODEL is not None:
		return _ANOMALY_MODEL
	if IsolationForest is None:
		return None

	baseline_x, _ = _synthetic_training_frame(seed=7, n_samples=800)
	model = IsolationForest(
		n_estimators=150,
		contamination=0.08,
		random_state=42,
	)
	model.fit(baseline_x)
	_ANOMALY_MODEL = model
	return _ANOMALY_MODEL


def detect_application_anomaly(features: dict) -> dict:
	"""Run IsolationForest on application features and return explainable alerts."""
	model = _get_anomaly_model()
	x_row = np.array([features.get(name, 0.0) for name in FEATURE_ORDER], dtype=float).reshape(1, -1)

	alerts = []
	if features.get("gst_bank_variance_pct", 0.0) > 30:
		alerts.append("GST-Bank turnover variance above 30% threshold")
	if features.get("debt_to_equity", 1.0) > 3:
		alerts.append("Debt-to-equity unusually high for standard SME profile")
	if features.get("news_sentiment_score", 0.55) < 0.30:
		alerts.append("Strongly adverse external sentiment detected")

	if model is None:
		return {
			"detected": bool(alerts),
			"anomaly_score": None,
			"method": "rule-based-fallback",
			"alerts": alerts,
		}

	pred = int(model.predict(x_row)[0])
	score = float(model.score_samples(x_row)[0])
	detected = pred == -1 or bool(alerts)

	if pred == -1 and not alerts:
		alerts.append("IsolationForest outlier detected against baseline borrower distribution")

	return {
		"detected": detected,
		"anomaly_score": round(score, 4),
		"method": "isolation-forest",
		"alerts": alerts,
	}
