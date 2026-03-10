# Intelli-Credit: Next-Gen Corporate Credit Appraisal

**Theme:** Bridging the Intelligence Gap

Welcome to the Intelli-Credit prototype! This is an end-to-end AI-powered Credit Decisioning Engine designed to streamline the Indian corporate lending landscape. It tackles the "Data Paradox" where credit managers are overwhelmed with structured, unstructured, and external data sources, taking weeks to process a single loan application.

## Key Features

Our prototype is built on three core pillars:

1. **The Data Ingestor (Multi-Format Support):** A high-latency pipeline that extracts commitments and risks from messy, scanned Indian-context PDFs (e.g., sanction letters). It automatically synthesizes structured data (GST vs. Bank statements) to identify "circular trading" and revenue inflation.
2. **The Research Agent ("Digital Credit Manager"):** Performs deep secondary research for sector-specific headwinds (e.g., RBI regulations) and litigation history via e-Courts/MCA. Includes a portal for integrating primary qualitative notes.
3. **The Recommendation Engine:** A transparent, explainable ML-based scoring model that summarizes the **Five Cs of Credit** (Character, Capacity, Capital, Collateral, Conditions). It outputs a loan limit recommendation, risk premium, and a professional Credit Appraisal Memo (CAM) in standard formats.

## Unique Value Proposition (UVP)

- **100% Explainable AI (XAI):** Not a black box. Explains the rationale behind rejected limits or approved premiums with specific evidence.
- **Deep Indian Context Sensitivity:** Localized for datasets like GSTR-2A vs. GSTR-3B disparities and CIBIL Commercial reports.
- **"Web-Scale" Contextual Research:** Autonomously crawls e-Courts and local news to detect promoter-level litigation and sector headwinds.
- **End-to-End Automation:** Parses unstructured sanction letters and cross-references bank statements to flag complex fraud patterns.
- **Enterprise-Ready:** Designed out-of-the-box for high-latency, multi-source ingestion (natively Databricks-compatible).

## Technical Architecture

The architecture is a completely decoupled, high-latency capable system:

- **Frontend / Client UI:** `Next.js 15` (App Router), `React`, `TypeScript`, `TailwindCSS`, and `shadcn/ui`.
- **Backend / API Engine:** `Python` and `FastAPI`.
- **Data & State Management:** `Redis` (for async state) and native Databricks compatibility.
- **Infrastructure:** Containerized using `Docker` and `Docker Compose`.

### How to Run

Ensure you have Docker and Docker Compose installed.

1. Clone the repository.
2. Ensure you have the `.env` configured appropriately.
3. Run the following command:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend (Next.js Application) and backend (FastAPI) as defined in the compose file.

## Structure

For detailed documentation, refer to the files in the `docs/` folder:
- `docs/Presentation.md`
- `docs/PRD.md`
- `docs/Structure.md`
- `docs/Hackathon_Problem_Statement.pdf`

---
*Developed for the Intelli-Credit Challenge hackathon.*

## 🚀 Deployment Guide

### 1. Backend Deployment (Railway)

We recommend deploying the FastAPI backend on **Railway** because it natively supports Dockerfiles and assigns dynamic ports securely out-of-the-box.

1. Create a [Railway](https://railway.app/) account and click **New Project** -> **Deploy from GitHub repo**.
2. Select your `AI_APP` repository.
3. Under the deployment settings, configure the **Root Directory** to be `/backend`.
4. Railway will automatically detect the `Dockerfile` and build the Python API container. 
5. The container successfully binds to Railway's dynamic `$PORT`.
6. Once deployed, note down the generated public URL (e.g., `https://intellicredit-backend.up.railway.app`).

### 2. Frontend Deployment (Vercel)

We recommend deploying the Next.js frontend on **Vercel** as it has first-party support and handles edge optimization perfectly.

1. Create a [Vercel](https://vercel.com) account and click **Add New Project**.
2. Import your `AI_APP` repository from GitHub.
3. In the project configuration:
   - **CRITICAL:** Set the **Root Directory** to `frontend`.
   - Expand the **Environment Variables** section.
   - Add a new variable: 
     - **Name:** `NEXT_PUBLIC_API_URL`
     - **Value:** `[Your Railway backend URL]` (no trailing slash, e.g., `https://intellicredit-backend.up.railway.app`)
4. Click **Deploy**. Vercel will automatically build the Next.js framework and securely map API requests to your Railway backend.
