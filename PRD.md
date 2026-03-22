# Intelli-Credit: AI-Powered Credit Decisioning Engine
### Product Requirements Document

**Version:** 2.0
**Date:** March 15, 2026
**Owner:** Product Team
**Status:** Hackathon Submission

---

## Executive Summary

Intelli-Credit is an AI-powered credit decisioning engine designed to solve the **"Data Paradox"** in Indian corporate lending: there is more information than ever, yet it takes weeks to process a single loan application. The system automates the end-to-end credit appraisal workflow by ingesting multi-source financial and non-financial data, conducting comprehensive web-scale research, and generating Comprehensive Credit Appraisal Memos (CAMs) with transparent, explainable loan recommendations and risk-based pricing.

**Hackathon Theme:** Next-Gen Corporate Credit Appraisal: Bridging the Intelligence Gap

---

## 1. Problem Statement (Official Hackathon Challenge)

### 1.1 The Data Paradox

In the Indian corporate lending landscape, credit managers are overwhelmed by a **"Data Paradox"**—there is more information than ever, yet it takes weeks to process a single loan application. Assessing the creditworthiness of a mid-sized Indian corporate requires stitching together disparate data points:

#### **Structured Data:**
- GST filings (GSTR-1, 2A, 3B)
- Income Tax Returns (ITR-5, ITR-6)
- Bank Statements (all major Indian banks)

#### **Unstructured Data:**
- Annual Reports
- Financial Statements (Ind AS format)
- Board meeting minutes
- Rating agency Reports (CRISIL, ICRA, CARE)
- Shareholding pattern

#### **External Intelligence:**
- News reports on sector trends (Economic Times, Business Standard, Mint)
- MCA (Ministry of Corporate Affairs) filings
- Legal disputes on the e-Courts portal
- RBI/SEBI regulatory circulars

#### **Primary Insights:**
- Observations from factory site visits (capacity utilization, equipment condition)
- Management interviews (Due Diligence) — responsiveness, transparency, business acumen

**The Problem:** The current manual process is slow (5-7 days per application), prone to human bias, and often misses "early warning signals" buried in unstructured text.

### 1.2 Official Challenge Statement

> **Develop an AI-powered Credit Decisioning Engine that automates the end-to-end preparation of a Comprehensive Credit Appraisal Memo (CAM). The solution must ingest multi-source data (Databricks), perform deep "web-scale" secondary research, and synthesize primary due diligence into a final recommendation (ML based) on whether to lend, what the limit should be, and at what risk premium.**

---

## 2. Vision & Success Criteria

### 2.1 Vision

Build a **"Digital Credit Manager"** that unifies document intelligence, real-time research, and explainable AI to transform corporate credit underwriting in India from a weeks-long manual process to an hours-long intelligent automated workflow.

### 2.2 Hackathon Evaluation Criteria (Aligned Requirements)

| Criterion | Target | Implementation Strategy |
|---|---|---|
| **Extraction Accuracy** | ≥95% on messy, scanned Indian-context PDFs | Enhanced PDF parser with OCR, keyword targeting, table extraction, multi-pass processing for large docs |
| **Research Depth** | Identify 90%+ of publicly available red flags (litigation, regulatory actions, adverse news) | Automated web crawling for news (promoters, sector headwinds), MCA filings, e-Courts litigation history |
| **Explainability** | Can AI "walk the judge through" its logic? Not a black box. | SHAP visualizations, factor contribution breakdowns, source citations for every claim |
| **Indian Context Sensitivity** | Understands GSTR-2A vs 3B, CIBIL Commercial, Ind AS formats | India-first design with GST-Bank-ITR triangulation, circular trading detection, sector-aware adjustments |
| **ML-Based Recommendation** | Transparent, explainable scoring model | XGBoost with SMOTE for imbalanced data, anomaly detection, macroeconomic indicators, 5Cs framework |

### 2.3 Business Success Metrics

| Metric | Target |
|---|---|
| Processing Time | Complete CAM generation in <2 hours vs 5–7 days manual |
| Data Extraction Accuracy | ≥95% on Indian financial documents |
| Research Coverage | 90%+ of red flags surfaced automatically |
| User Adoption | Credit officers accept 80%+ of AI recommendations with minimal edits |
| Explainability Score | 100% of recommendations traceable to specific data points and reasoning steps |

---

## 3. Key Deliverables (Three Pillars)

### 3.1 Pillar 1: The Data Ingestor — High Latency Pipelines

#### **Core Capabilities:**

**A. Multi-Format Document Upload**
- Accept PDF (scanned and native), Excel, Word, images (JPG, PNG)
- Drag-and-drop interface with progress tracking

**B. Unstructured Parsing**
- **Enhanced PDF Processing:**
  - Dynamic page limits (20-50 pages for large docs instead of fixed 15)
  - Neighbor page expansion to capture multi-page financial statements
  - 35+ Indian-specific keywords (revenue from operations, EBITDA, GSTR, DSCR, notes to accounts)
  - OCR via Tesseract + PyMuPDF for scanned/image-heavy PDFs
  - Chunked text processing (20K chars/chunk with 2K overlap) to handle 86 MB annual reports
- **Extract key financial commitments and risks from:**
  - Annual reports (balance sheet, P&L, cash flow, director's report)
  - Legal notices (case numbers, amounts, court dates)
  - Sanction letters from other banks (existing limits, covenants)
  - Rating agency reports (credit ratings, outlook, key ratios)
  - Board meeting minutes (capital expenditure plans, risk disclosures)
  - Shareholding patterns (promoter pledging, FII/DII holdings)

**C. Structured Synthesis**
- **GST-Bank Cross-Verification:**
  - Auto-detect revenue mismatches: GST reported sales vs bank credits over 12 months
  - Variance thresholds: >30% = HIGH RISK, >20% = MODERATE RISK
  - **Circular Trading Detection:** High invoice volume with same counterparties in both inward/outward supplies
- **GST-ITR Triangulation:**
  - Compare GST turnover vs ITR revenue; flag discrepancies >10%
  - Identify sector-specific compliance patterns
- **Batch Processing:**
  - New endpoint: `/api/pipeline/data-folder` — lists all PDFs in Data folder
  - New endpoint: `/api/pipeline/run-batch` — processes all 27 PDFs (352 MB) from Data folder in one API call
  - Smart document routing (bank/GST/financial/other) based on filename + content

**D. Data Quality Dashboard**
- Extraction confidence scores per document and field
- One-click manual correction interface
- All corrections logged for model fine-tuning

#### **Technical Implementation:**
- **Libraries:** pdfplumber, PyMuPDF (fitz), pytesseract, Pillow, Groq API (LLaMA 3.3 70B)
- **Processing SLA:** <5 minutes for 10-document application; batch mode handles 350+ MB in <30 minutes
- **Privacy:** All documents stored in encrypted backend; no raw PII sent to external LLMs without hashing

---

### 3.2 Pillar 2: The Research Agent — "Digital Credit Manager"

#### **Core Capabilities:**

**A. Secondary Research (Automated Web Crawling)**
- **Company & Promoter Intelligence:**
  - MCA portal for charges, director disqualifications, recent filings
  - e-Courts database for ongoing/past litigation (case status, amounts, dates)
  - News aggregators (Google News, Economic Times, Business Standard) for adverse mentions in past 24 months
- **Sector-Specific Headwinds:**
  - RBI/SEBI circulars for regulatory changes (e.g., "new RBI regulations on NBFCs")
  - Industry reports on sector outlook, commodity price trends, regulatory shifts
- **Clustering & Summarization:**
  - Findings grouped into themes: Litigation Risk, Regulatory Risk, Sector Outlook, Reputation Risk
  - AI-extracted key dates, amounts, case status, severity (low/medium/high)
  - Top 3 red flags + top 3 positive signals
  - All claims cited with source URLs for auditor verification

**B. Primary Insight Integration**
- **Portal for Credit Officer Notes:**
  - Free-text input for site visit observations (e.g., "Factory found operating at 40% capacity")
  - Management interview signals (e.g., "Evasive on contingent liabilities")
- **NLP-Based Score Adjustments:**
  - Positive keywords: "full capacity", "modern equipment", "expanding", "good order book" → +3 to +5 score boost
  - Negative keywords: "shut down", "idle machinery", "worker strike", "evasive" → -5 to -10 penalty
  - Automated mapping to 5Cs framework (e.g., "evasive" → Character score penalty)

**C. AI-Powered Risk Intelligence**
- **Chunked LLM Processing:**
  - Extract risk signals from combined corpus (all documents + research)
  - News sentiment: Positive / Mostly Positive / Neutral / Negative
  - Litigation flags with descriptions and severity
  - Risk timeline with dates, events, severity, source
  - Key concerns and strengths arrays
- **Hallucination Prevention:**
  - RAG (Retrieval-Augmented Generation) grounding in source documents
  - Fact verification: cross-check dates, amounts, case numbers
  - Target: <2% hallucination rate

#### **Technical Implementation:**
- **Current:** Mock research engine with LLaMA 3.3 70B risk intelligence extraction
- **Phase 2:** Live scrapers (Scrapy, BeautifulSoup), MCA/e-Courts APIs, news API integrations
- **Research SLA:** <30 minutes per application
- **Privacy:** Anonymize company names in external API calls where possible

---

### 3.3 Pillar 3: The Recommendation Engine & CAM Generator

#### **Core Capabilities:**

**A. ML-Based Scoring (Enhanced with Research Best Practices)**

**Primary Model: XGBoost with SMOTE**
- **Why:** Up to 99.4% accuracy in default classification (research-backed)
- **SMOTE Integration:** Balance rare default events vs healthy loans to prevent false negatives
- **Features:**
  - Financial ratios: Current ratio, debt-to-equity, DSCR, networth, revenue trends
  - GST compliance: Filings on time (out of 12), turnover trend
  - Bank behavior: Avg monthly credits, cheque bounces, EMI regularity
  - Litigation count, news sentiment, sector outlook
  - Site visit qualitative signals (mapped to numeric)
  - **NEW:** Real-time macroeconomic indicators (interest rates, inflation, GDP growth via FRED API)
- **Libraries:** `xgboost`, `imbalanced-learn`, `scikit-learn`, `pandas_datareader`

**Anomaly Detection for Fraud**
- **IsolationForest** on transaction features (velocity, GST-bank ratio shifts, unexplained income jumps)
- Flags anomalies beyond rule-based circular trading detection
- LLM generates natural language explanation for each anomaly

**5 Cs of Credit Framework**
- **Character (20%):** Promoter credit history, litigation count, GST filing timeliness, management interview signals
- **Capacity (25%):** Current ratio, DSCR, revenue trends, capacity utilization
- **Capital (20%):** Debt-to-equity, tangible net worth, retained earnings
- **Collateral (15%):** Asset coverage ratio, quality of security
- **Conditions (20%):** News sentiment, sector outlook, macroeconomic factors (dynamically adjusted)

**B. Decision Logic**
- **Recommendations:** Approve / Approve with Conditions / Reject
- **Loan Amount:** % of requested amount based on collateral and cash flow coverage
- **Risk Premium:** Basis points over base rate with factor-level breakdown
  - Example: +75 bps for sector headwinds, +50 bps for litigation, -25 bps for strong collateral
- **Circular Trading Downgrade:** If variance >30%, downgrade APPROVE → REFER

**C. The CAM Generator**

**Structure (8-12 pages):**
1. **Executive Summary** (1 page): Recommendation, loan amount, interest rate, key risks
2. **Company Background & Industry Overview** (from research agent)
3. **Financial Analysis** (5Cs detailed breakdown with tables and trend charts)
4. **Risk Assessment** (red flags, mitigation measures, anomaly alerts)
5. **Recommendation & Pricing Rationale** (explainable factor contributions)
6. **Appendices** (supporting data, research sources, citations)

**Visual Aids:**
- Revenue/EBITDA trend charts (matplotlib)
- GST-bank mismatch heatmap by month
- Risk factor contribution bars
- **NEW: SHAP waterfall plots** showing how each feature (revenue, litigation, capacity) contributed to the final score

**D. Explainability Interface (Research-Backed XAI)**

**SHAP Integration:**
- Generate SHAP (SHapley Additive exPlanations) visualizations
- Waterfall plot embedded in CAM PDF showing marginal contribution of each variable
- Example: "High GST turnover (+8 points), Low collateral (-5 points), Litigation (-3 points)"
- **Libraries:** `shap`, `matplotlib`

**Provenance Tracking:**
- Every claim cites source document + page number
- Click-through from CAM to original document with highlighted text (in UI)
- Factor contribution view: sliders to see "what-if" scenarios

**Manual Override:**
- Credit officers can edit any CAM section, adjust scores, or override recommendation
- System logs all edits and reasons for model retraining
- What-if mode: tweak inputs (collateral, capacity) → real-time score updates

#### **Technical Implementation:**
- **ML Stack:** XGBoost, SMOTE, IsolationForest, SHAP
- **CAM Generation:** Jinja2 templates, LLaMA 3.3 70B (Groq API), ReportLab (PDF), python-docx
- **CAM SLA:** <10 minutes after data ingestion and research complete
- **Explainability:** 100% of score components traceable to inputs
- **Output Formats:** PDF, Word (DOCX), HTML

---

## 4. User Personas & Use Cases

### Persona 1: Priya (Credit Officer, Mid-sized NBFC)

**Background:** 3 years experience, handles 20–30 corporate loan applications per month, often works late to meet deadlines.

**Pain Points:**
- Spends 40% of time on data entry and document chase
- Struggles to verify GST vs bank statement consistency manually
- Misses obscure litigation or regulatory news due to time constraints

**Goals:**
- Process applications faster without compromising quality
- Get alerts on red flags she might have missed
- Generate well-structured CAMs that her manager approves first time

**Use Case:** Priya uploads a loan applicant's GST returns, bank statements, and annual report to Intelli-Credit. The system auto-extracts data, flags a 15% revenue mismatch between GST and bank credits, and surfaces an ongoing NCLT case against a promoter. Priya adds a site-visit note ("factory at 60% capacity due to raw material shortage") and the system adjusts the capacity score down by 7 points. She reviews the generated CAM with embedded SHAP plots showing exact factor contributions, tweaks one paragraph, and submits for approval — **total time: 90 minutes vs her usual 2 days.**

---

### Persona 2: Rajesh (Credit Manager, Regional Bank)

**Background:** 12 years experience, approves 100+ loans per quarter, responsible for portfolio NPAs.

**Pain Points:**
- Inconsistent CAM quality from junior analysts
- Difficulty auditing pricing decisions when challenged by borrowers or auditors
- No systematic way to track which red flags were checked vs missed

**Goals:**
- Ensure every application gets the same rigorous scrutiny
- Quickly review AI reasoning and override if needed
- Demonstrate due diligence to regulators and auditors

**Use Case:** Rajesh receives a CAM generated by Intelli-Credit for a ₹50 Cr term loan. He clicks through the SHAP waterfall plot to see that the recommended 12% interest rate includes +75 bps for sector headwinds (RBI circular on stressed assets flagged by research agent) and +50 bps for promoter litigation, offset by -25 bps for strong collateral. He agrees, adds a manual note requiring personal guarantee, and approves the loan — **confident in a defensible paper trail that can withstand auditor scrutiny.**

---

## 5. Technical Architecture & Requirements

### 5.1 System Architecture Overview

**High-Level Components:**

| # | Component | Technology |
|---|---|---|
| 1 | Web UI / API Gateway | Next.js (React), FastAPI (REST API) |
| 2 | Document Processing Service | pdfplumber, PyMuPDF, pytesseract, Pillow, Groq API (LLaMA 3.3 70B) |
| 3 | Feature Engineering Pipeline | GST-Bank-ITR triangulation, circular trading detection, ratio calculations, anomaly detection |
| 4 | Research Agent Service | Mock (current), Scrapy/BeautifulSoup (Phase 2), MCA/e-Courts/news APIs |
| 5 | Scoring & Decision Engine | XGBoost, SMOTE, IsolationForest, 5Cs framework, macroeconomic API (FRED) |
| 6 | CAM Generator | Jinja2 templates, LLaMA 3.3 70B, ReportLab (PDF), python-docx |
| 7 | Explainability Module | SHAP, matplotlib, provenance tracking, citation management |
| 8 | Data Store | In-memory (MVP), PostgreSQL + S3/MinIO (Phase 2), Pinecone/Weaviate for RAG (Phase 2) |

### 5.2 AI/ML Requirements

#### 5.2.1 Document Extraction Models
- **OCR Accuracy:** ≥98% on clean scans, ≥95% on noisy/skewed scans
- **Enhanced Parser:** Dynamic page limits (20-50), neighbor expansion, 35+ Indian keywords
- **Table Extraction:** Camelot/pdfplumber for bank statements; validate extracted amounts against checksums
- **Confidence Thresholds:** Flag fields with <80% confidence for manual review

#### 5.2.2 Research Agent LLM (Current: LLaMA 3.3 70B via Groq)
- **RAG Integration (Phase 2):** Embed research documents into vector store; use retrieval to ground summaries
- **Chunked Processing:** Up to 4 chunks × 20K chars = 80K chars per document
- **Prompt Engineering:** Chain-of-thought for multi-step reasoning; few-shot examples for Indian legal/regulatory text
- **Fact Verification:** Cross-check key claims; flag inconsistencies; target <2% hallucination rate

#### 5.2.3 ML-Based Scoring Models (Enhanced)

**XGBoost + SMOTE:**
- **Training Data:** Minimum 500 labeled loan applications with outcomes (default/repaid)
- **SMOTE:** Balance rare default events to prevent model bias toward "good" predictions
- **Feature Engineering:** Financial ratios + GST compliance + bank behavior + litigation + sentiment + macroeconomic indicators
- **Cross-Validation:** 5-fold CV with stratified sampling
- **Hyperparameter Tuning:** GridSearchCV for learning rate, max_depth, n_estimators

**Anomaly Detection:**
- **IsolationForest:** Unsupervised fraud detection on transaction velocity, GST-bank ratio anomalies
- **Threshold:** Flag top 5% as anomalies for manual review
- **Integration:** LLM generates explanation ("Flagged: Sudden 300% spike in monthly credits without corresponding GST increase")

**Explainability:**
- **SHAP:** Post-hoc explanations for XGBoost predictions
- **Waterfall Plots:** Embedded in CAM PDF to show feature contributions
- **Inherently Interpretable Models:** Decision trees, linear models for regulatory ratios (fallback)

**Bias & Fairness Audits:**
- Monthly review for unintended bias by company size, sector, geography
- Demographic parity checks, adversarial debiasing (Phase 2)

#### 5.2.4 CAM Generation
- **Template-Guided:** Structured prompts with JSON schema for consistent format
- **Citation Accuracy:** Every factual claim cites source document + page number; 100% programmatic validation
- **Human-in-the-Loop:** Credit officers review and approve CAM; feedback loop for model improvement

### 5.3 Data Privacy & Security

- **Data Localization:** All raw documents stored in local backend (MVP), India-based VPC (Phase 2)
- **PII Masking:** Hash/mask PAN, CIN, Aadhaar, bank account numbers before external LLM calls
- **Access Control:** RBAC — credit officers see only assigned applications
- **Audit Logging:** Every document access, API call, model inference logged with timestamp and user ID
- **Encryption:** At-rest (future) and in-transit (TLS 1.3) for all data
- **Compliance:** Align with RBI cybersecurity guidelines, IT Act 2000, DPDPA 2023

### 5.4 Scalability & Performance

- **Target Load (MVP):** 10 concurrent users, 50 applications/month
- **Processing SLA:** 95th percentile end-to-end TAT (upload → CAM) <2 hours
- **Batch Mode:** Process 27 PDFs (352 MB) from Data folder in <30 minutes
- **Cost Optimization:** Use Groq API (cost-efficient); cache research results for 30 days

### 5.5 Integration Requirements (Phase 2)

- **LOS Integration:** REST API with webhooks; support for Finacle, Nucleus, FlexCube
- **Document Management:** Integration with SharePoint, Google Drive
- **Email/SMS Notifications:** Alerts to borrowers and credit officers at workflow stages
- **Reporting & BI:** Export data to PowerBI, Tableau for portfolio analytics

---

## 6. Success Metrics & KPIs

### 6.1 Hackathon Evaluation Metrics (Primary)

| Criterion | Target | Current Status |
|---|---|---|
| **Extraction Accuracy** | ≥95% on messy Indian PDFs | ✓ Enhanced parser with OCR, 35+ keywords, dynamic page limits |
| **Research Depth** | ≥90% red flag recall | ✓ AI risk intelligence extraction; Phase 2: live scrapers |
| **Explainability** | Not a black box | ✓ SHAP plots, factor contributions, source citations |
| **Indian Context Sensitivity** | GSTR-2A vs 3B, CIBIL, circular trading | ✓ GST-Bank-ITR triangulation, India-first design |
| **ML-Based Recommendation** | Transparent scoring | ✓ XGBoost + SMOTE + anomaly detection planned |

### 6.2 Product Metrics

| Metric | Target | Measurement Method |
|---|---|---|
| Data Extraction Accuracy | ≥95% | Human validation on 100 random docs/month |
| Research Red Flag Recall | ≥90% | Compare vs manual research on 50 test cases |
| CAM Generation Time | <10 min | System logs (P50, P95, P99) |
| End-to-End TAT | <2 hours (P95) | Timestamp: upload → approval |
| Hallucination Rate | <2% | Fact-checking against source documents |
| Credit Officer Satisfaction | ≥4.5/5 | Monthly NPS survey |

### 6.3 AI Model Metrics

- **XGBoost Accuracy:** ≥95% on test set (AUC-ROC ≥0.90)
- **SMOTE Effectiveness:** Reduce false negatives by 40%
- **Anomaly Detection Precision:** ≥80% of flagged cases are true anomalies
- **SHAP Explainability:** 100% of score components traceable to inputs
- **Model Bias:** No statistically significant difference in approval rates by sector/size after controlling for financials

---

## 7. Implementation Roadmap

### Phase 1: Hackathon MVP — March 2026 (Current)

**Scope:** Proof of concept with core features
**Deliverables:** Working demo, architecture diagram, pitch deck, GitHub repo

**Completed:**
- [x] Document upload API (multi-file support)
- [x] Enhanced PDF parsing (dynamic page limits, neighbor expansion, 35+ keywords, OCR)
- [x] Chunked AI extraction (LLaMA 3.3 70B via Groq, up to 80K chars/doc)
- [x] GST-Bank-ITR triangulation and circular trading detection
- [x] Batch ingestion from Data folder (27 PDFs, 352 MB)
- [x] 5Cs scoring framework with site visit note adjustments
- [x] CAM generation with explainable summary text
- [x] PDF export (ReportLab)
- [x] FastAPI backend + CORS
- [x] Mock research agent (AI risk intelligence extraction)

**In Progress / Planned for Demo:**
- [ ] **XGBoost + SMOTE Model:** Train on sample dataset (500 labeled loans)
- [ ] **IsolationForest Anomaly Detection:** Flag transaction velocity anomalies
- [ ] **SHAP Visualizations:** Embed waterfall plots in CAM PDF
- [ ] **Macroeconomic Data Integration:** Pull live interest rates, inflation from FRED API
- [ ] **Frontend UI:** React dashboard for document upload, CAM review, explainability panel
- [ ] **Demo Video:** Walkthrough of end-to-end workflow with explanations

### Phase 2: Pilot with Partner NBFC — April–June 2026 (3 months)

**Scope:** Production-ready for single lender, 50 applications
**Success Criteria:** Process 50 real loans, achieve <2 hour TAT, ≥4.5/5 user satisfaction

- [ ] Live research agent (Scrapy, MCA/e-Courts/news APIs)
- [ ] Fine-tuned XGBoost on lender's historical data (1,000+ labeled applications)
- [ ] Full SHAP integration with interactive explainability UI
- [ ] Security hardening (encryption, RBAC, audit logs)
- [ ] Integration with pilot lender's LOS
- [ ] Peer benchmarking (industry quartiles from CMIE Prowess)

### Phase 3: Scale & Commercialization — July–December 2026 (6 months)

**Scope:** Multi-tenant SaaS, 5 lenders, 500+ applications/month
**Success Criteria:** 5 paying customers, 80% MoM application growth, <5% monthly churn

- [ ] Multi-tenancy and tenant isolation
- [ ] Advanced analytics dashboard (portfolio insights, NPL predictors)
- [ ] Mobile app for manager approvals
- [ ] API marketplace for third-party integrations
- [ ] Regulatory reporting templates
- [ ] LSTM for time-series analysis (GST/bank trends)
- [ ] Fairness audits and adversarial debiasing

---

## 8. Open Questions & Assumptions

### Open Questions

1. **Training Data Availability:** Can we access anonymized historical loan data (500+ cases with default outcomes) to train XGBoost?
2. **Macroeconomic API Access:** Do we have budget for paid APIs (FRED requires registration; free tier has rate limits)?
3. **SHAP Performance:** Will SHAP computation (<5 sec per prediction) fit within our 10-minute CAM generation SLA?
4. **Anomaly Detection Threshold:** What % of applications should be flagged as anomalies for manual review without overwhelming credit officers? (Currently: top 5%)
5. **Databricks Expectation:** Hackathon mentions "Databricks" for data ingestion — is this a hard requirement or flexible?

### Assumptions

1. Target lenders process primarily corporate loans (not retail), ticket size ₹1–50 Cr
2. Credit officers have basic digital literacy; can use web apps, comfortable with PDF uploads
3. Lenders are willing to adopt AI recommendations with human oversight (not fully automated decisioning)
4. Hackathon judges prioritize **innovation** (XGBoost, SHAP, anomaly detection), **explainability** (SHAP plots, citations), and **Indian context** (GST triangulation) over production-grade scalability
5. Access to Groq API for LLaMA 3.3 70B (currently using free tier; may need paid plan for high volume)
6. MVP does not require live web scraping (mock research acceptable); Phase 2 will implement live scrapers

---

## 9. Compliance & Risk Management

### 9.1 Regulatory Compliance

- **RBI Guidelines:** Align with Master Circular on Loans and Advances, Fair Practices Code
- **CICRA 2005:** Ensure proper consent for credit bureau pulls
- **IT Act 2000 & DPDPA 2023:** Secure data handling, breach notification, user consent
- **KYC/AML Norms:** Integrate with lender's existing KYC processes; flag high-risk sectors per FATF guidelines

### 9.2 Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| OCR errors on critical fields | Incorrect loan decisions | Confidence thresholds, manual review queue, extraction logging |
| LLM hallucinations in CAM | Misleading recommendations | RAG grounding, fact verification, human review, <2% target |
| XGBoost overfitting | Poor generalization to new data | Cross-validation, SMOTE, regularization, monthly retraining |
| Research agent misses red flag | Loan to risky borrower | Multi-source search, AI risk extraction, periodic audits vs manual |
| Data breach / PII leak | Regulatory penalty, reputation loss | Encryption, access controls, audit logs, PII masking before external APIs |
| Model bias (sector/size) | Discrimination, legal liability | Bias audits, fairness metrics, diverse training data, adversarial debiasing |

### 9.3 Human Oversight

- All AI recommendations are **advisory**; final decision authority rests with human credit officer/manager
- High-risk applications (loan amount >₹10 Cr, DSCR <1.2, adverse litigation) escalated to senior management
- Monthly model performance review by credit committee
- Explainability ensures credit officers can justify every decision to auditors/regulators

---

## 10. Appendices

### Appendix A: Glossary

| Term | Definition |
|---|---|
| CAM | Credit Appraisal Memo — structured document summarizing loan application, financial analysis, and recommendation |
| 5 Cs of Credit | Character, Capacity, Capital, Collateral, Conditions — traditional framework for credit risk assessment |
| DSCR | Debt Service Coverage Ratio — measure of cash flow available to pay debt obligations |
| GST | Goods and Services Tax — Indian indirect tax; GSTR-1 (outward supplies), GSTR-2A (inward auto-populated), GSTR-3B (summary) |
| ITR | Income Tax Return — annual tax filing; ITR-5 for partnerships, ITR-6 for companies |
| MCA | Ministry of Corporate Affairs — maintains company registry, filings, director details |
| e-Courts | National portal for court case status in India |
| RAG | Retrieval-Augmented Generation — technique to ground LLM outputs in verified source documents |
| SHAP | SHapley Additive exPlanations — ML model explainability framework to quantify feature contributions |
| SMOTE | Synthetic Minority Over-sampling Technique — balances imbalanced datasets by generating synthetic minority class samples |
| XGBoost | Extreme Gradient Boosting — ensemble ML algorithm known for high accuracy in classification tasks |
| IsolationForest | Unsupervised anomaly detection algorithm that isolates outliers |
| TAT | Turnaround Time |
| NPL/NPA | Non-Performing Loan / Non-Performing Asset |
| NBFC | Non-Banking Financial Company |
| LOS | Loan Origination System |
| RBAC | Role-Based Access Control |
| CIN | Corporate Identity Number (MCA) |
| NCLT | National Company Law Tribunal |
| Ind AS | Indian Accounting Standards (converged with IFRS) |

### Appendix B: Reference Documents

1. **Hackathon Problem Statement:** "The Intelli-Credit Challenge" (Theme: Next-Gen Corporate Credit Appraisal: Bridging the Intelligence Gap)
2. **NotebookLM Research:** AI and ML applications in credit scoring (XGBoost, SHAP, SMOTE, alternative data, bias mitigation)
3. RBI Master Circular on Loans and Advances (2025 edition)
4. DPDPA 2023: Digital Personal Data Protection Act (draft provisions)
5. Credit Bureau data formats (CIBIL, Equifax, Experian)
6. Sample CAM templates from partner NBFCs (confidential)

### Appendix C: Technology Stack Summary

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js (React) | Document upload UI, CAM review, explainability dashboard |
| **Backend API** | FastAPI (Python) | REST API, CORS, file handling, orchestration |
| **Document Processing** | pdfplumber, PyMuPDF, pytesseract, Pillow | PDF parsing, OCR, table extraction |
| **AI Extraction** | Groq API (LLaMA 3.3 70B) | Chunked text processing, financial data extraction |
| **ML Scoring** | XGBoost, imbalanced-learn (SMOTE), scikit-learn | Default prediction, class imbalance handling |
| **Fraud Detection** | IsolationForest (scikit-learn) | Unsupervised anomaly detection |
| **Explainability** | SHAP, matplotlib | Waterfall plots, feature contribution visualization |
| **Macroeconomic Data** | pandas_datareader, FRED API | Real-time interest rates, inflation, GDP |
| **CAM Generation** | Jinja2, ReportLab, python-docx | Template-driven memo generation, PDF/DOCX export |
| **Research (Phase 2)** | Scrapy, BeautifulSoup, MCA/e-Courts APIs | Web scraping, litigation/news aggregation |
| **Deployment** | Railway (backend), Vercel (frontend) | Cloud hosting, CI/CD |

---

## 11. Sign-Off

| Role | Name | Date |
|---|---|---|
| Prepared by | Product Team | March 15, 2026 |
| Reviewed by | Engineering Lead, Credit Domain Expert | March 15, 2026 |
| Approved by | Hackathon Team Lead | March 15, 2026 |

### Version History

- **v2.0** (March 15, 2026):
  - Updated with official hackathon problem statement and evaluation criteria
  - Added ML enhancements: XGBoost, SMOTE, IsolationForest, SHAP, macroeconomic data
  - Incorporated NotebookLM research recommendations on best practices
  - Enhanced data ingestion pipeline with batch processing and chunked AI extraction
  - Refined success metrics to align with hackathon judging criteria
  - Added technology stack summary and implementation roadmap updates
- **v1.0** (March 9, 2026): Initial draft for hackathon submission

---

**Next Actions:**
1. ✅ Backend enhanced with batch ingestion from Data folder (27 PDFs, 352 MB)
2. ✅ NotebookLM integration for research-backed AI/ML recommendations
3. ⏳ Implement XGBoost + SMOTE model with sample training data
4. ⏳ Add IsolationForest anomaly detection module
5. ⏳ Integrate SHAP visualizations into CAM PDF export
6. ⏳ Build React frontend with explainability dashboard
7. ⏳ Record demo video highlighting all three pillars + explainability
