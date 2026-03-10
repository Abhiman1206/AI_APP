intelli-credit-prototype/
│
├── README.md                 # Next.js + FastAPI setup + demo instructions
├── docker-compose.yml        # Full stack (Next.js + FastAPI + Redis)
├── .env.example
├── .gitignore
│
├── frontend/                 # Next.js 15 App Router (70% effort)
│   ├── app/                  # App Router pages
│   │   ├── layout.tsx
│   │   ├── page.tsx          # Landing
│   │   ├── demo/
│   │   │   ├── page.tsx      # /demo (main demo flow)
│   │   │   ├── upload/
│   │   │   │   └── page.tsx  # Step 1: File upload
│   │   │   ├── extraction/
│   │   │   │   └── page.tsx  # Step 2: Parsed facts
│   │   │   ├── research/
│   │   │   │   └── page.tsx  # Step 3: Risk timeline
│   │   │   ├── scoring/
│   │   │   │   └── page.tsx  # Step 4: 5Cs + recommendation
│   │   │   └── cam/
│   │   │       └── page.tsx  # Step 5: CAM preview + download
│   │   │
│   │   ├── api/              # API routes (proxy to backend)
│   │   │   └── pipeline/
│   │   │       └── route.ts  # POST /api/pipeline/run
│   │   └── globals.css
│   │
│   ├── components/           # Reusable UI
│   │   ├── ui/               # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   └── progress.tsx
│   │   ├── FileUpload.tsx
│   │   ├── RiskTimeline.tsx
│   │   ├── FiveCsRadar.tsx
│   │   ├── CAMPreview.tsx
│   │   └── WhatIfSlider.tsx
│   │
│   ├── lib/                  # Utils
│   │   ├── api.ts            # Backend fetch wrapper
│   │   ├── pdf.worker.js     # PDF.js for client-side preview
│   │   └── types.ts          # TypeScript interfaces
│   │
│   ├── public/               # Static assets
│   │   ├── logo.png
│   │   └── demo-data/        # Sample PDFs
│   │
│   ├── tailwind.config.ts
│   └── next.config.js
│
├── backend/                  # FastAPI (30% effort)
│   ├── main.py               # /pipeline/run endpoint
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── ingestor/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── gst_analyzer.py
│   │   │   └── bank_extractor.py
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── mock_search.py
│   │   │   └── mca_checker.py
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── five_cs.py
│   │   │   └── cam_generator.py
│   │   └── models.py         # Pydantic schemas
│   ├── tests/
│   └── data/
│       └── mock_research/
│
├── data/                     # Shared mock data
│   ├── test_cases.json
│   └── schemas/
│
└── outputs/                  # Generated files (volume mount)
    ├── cams/
    └── extracted/
