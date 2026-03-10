import Link from "next/link";

export default function HomePage() {
  return (
    <div className="page-wrapper">
      {/* Nav */}
      <nav
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "var(--space-4) var(--space-6)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <span style={{ fontWeight: 800, fontSize: "1.25rem" }}>
          <span className="text-gradient">Intelli</span>-Credit
        </span>
        <Link href="/demo/upload" className="btn btn-primary" style={{ textDecoration: "none" }}>
          Launch Demo →
        </Link>
      </nav>

      {/* Hero */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "var(--space-16) var(--space-6)",
        }}
      >
        <div className="animate-in">
          <span className="badge badge-accent" style={{ marginBottom: "var(--space-6)", display: "inline-block" }}>
            AI-Powered Credit Analysis
          </span>
        </div>

        <h1 className="animate-in stagger-1" style={{ maxWidth: "780px", marginBottom: "var(--space-6)" }}>
          Turn Financial Documents into{" "}
          <span className="text-gradient">Instant Credit Decisions</span>
        </h1>

        <p
          className="animate-in stagger-2"
          style={{
            maxWidth: "600px",
            fontSize: "1.125rem",
            color: "var(--text-secondary)",
            marginBottom: "var(--space-8)",
            lineHeight: 1.7,
          }}
        >
          Upload balance sheets, P&L statements, GST returns, and bank statements.
          Get automated 5Cs scoring, risk analysis, and a complete Credit Appraisal
          Memorandum in seconds.
        </p>

        <div className="animate-in stagger-3" style={{ display: "flex", gap: "var(--space-4)" }}>
          <Link href="/demo/upload" className="btn btn-primary" style={{ textDecoration: "none" }}>
            Start Demo
          </Link>
          <a href="#features" className="btn btn-secondary" style={{ textDecoration: "none" }}>
            How It Works
          </a>
        </div>

        {/* Stats row */}
        <div
          className="animate-in stagger-4"
          style={{
            display: "flex",
            gap: "var(--space-12)",
            marginTop: "var(--space-16)",
            padding: "var(--space-6) var(--space-10)",
            background: "var(--bg-card)",
            borderRadius: "var(--radius-xl)",
            border: "1px solid var(--border)",
          }}
        >
          {[
            { value: "< 30s", label: "Analysis Time" },
            { value: "5Cs", label: "Credit Framework" },
            { value: "100%", label: "Automated CAM" },
          ].map((stat) => (
            <div key={stat.label} style={{ textAlign: "center" }}>
              <div style={{ fontWeight: 800, fontSize: "1.5rem" }} className="text-gradient">
                {stat.value}
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Features */}
      <section
        id="features"
        style={{ padding: "var(--space-16) var(--space-6)" }}
      >
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: "var(--space-10)" }}>
            How <span className="text-gradient">Intelli-Credit</span> Works
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "var(--space-6)",
            }}
          >
            {[
              { icon: "📄", title: "1. Upload Documents", desc: "Drop PDFs of financial statements, GST returns, and bank statements." },
              { icon: "🔍", title: "2. AI Extraction", desc: "Automatically parse and extract key financial metrics and ratios." },
              { icon: "🌐", title: "3. Risk Research", desc: "Check MCA records, news sentiment, and litigation history." },
              { icon: "📊", title: "4. 5Cs Scoring", desc: "Score across Character, Capacity, Capital, Collateral, and Conditions." },
              { icon: "📋", title: "5. CAM Generation", desc: "Get a complete Credit Appraisal Memorandum with recommendation." },
            ].map((f) => (
              <div key={f.title} className="card">
                <div style={{ fontSize: "2rem", marginBottom: "var(--space-3)" }}>{f.icon}</div>
                <h4 style={{ marginBottom: "var(--space-2)" }}>{f.title}</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
