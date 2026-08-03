import { useState, useEffect } from "react";

const colors = {
  bg: "#f8f9fa", card: "#ffffff", border: "#e5e7eb",
  text: "#1a1a2e", muted: "#6b7280",
  fake: "#ef4444", real: "#16a34a", brand: "#4f46e5",
  warn: "#f59e0b", light: "#f3f4f6",
};

export default function App() {
  const [tab, setTab]       = useState("analyze");
  const [text, setText]     = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoad]  = useState(false);
  const [error, setError]   = useState("");
  const [history, setHist]  = useState([]);
  const [stats, setStats]   = useState(null);

  useEffect(() => {
    if (tab === "history") fetch("https://fake-news-detector-11zt.onrender.com/api/history").then(r => r.json()).then(d => setHist(d.history || [])).catch(() => {});
    if (tab === "stats")   fetch("https://fake-news-detector-11zt.onrender.com/api/stats").then(r => r.json()).then(setStats).catch(() => {});
  }, [tab]);

  const analyse = async () => {
    if (text.trim().length < 20) { setError("Please enter at least 20 characters."); return; }
    setLoad(true); setError(""); setResult(null);
    try {
      const res  = await fetch("https://fake-news-detector-11zt.onrender.com/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      const data = await res.json();
      if (data.success) setResult(data);
      else setError(data.error || "Analysis failed.");
    } catch { setError("Cannot reach server. Is Flask running?"); }
    setLoad(false);
  };

  const deleteOne = async (id) => {
    await fetch(`https://fake-news-detector-11zt.onrender.com/api/history/${id}`, { method: "DELETE" });
    setHist(prev => prev.filter(item => item.id !== id));
  };

  const deleteAll = async () => {
    if (!window.confirm("Delete ALL history?")) return;
    await fetch("https://fake-news-detector-11zt.onrender.com/api/history/all", { method: "DELETE" });
    setHist([]);
  };

  const labelColor = (l) => l === "REAL" ? colors.real : l === "FAKE" ? colors.fake : colors.warn;

  return (
    <div style={{ minHeight: "100vh", background: colors.bg, color: colors.text, fontFamily: "'Segoe UI', system-ui, sans-serif" }}>

      {/* ── NAVBAR ── */}
      <nav style={{ background: "#fff", borderBottom: `1px solid ${colors.border}`, padding: "14px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
        <span style={{ fontWeight: 800, fontSize: "1.1rem", color: colors.brand }}>🔍 FakeNews Analyser</span>
        <div style={{ display: "flex", gap: "4px" }}>
          {["analyze", "history", "stats"].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{ padding: "8px 16px", background: tab === t ? colors.brand : "none", color: tab === t ? "#fff" : colors.muted, border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "0.88rem", fontWeight: tab === t ? 600 : 400 }}>
              {{ analyze: "Analyse", history: "History", stats: "Stats" }[t]}
            </button>
          ))}
        </div>
      </nav>

      <div style={{ maxWidth: "800px", margin: "0 auto", padding: "32px 24px" }}>

        {/* ════════ ANALYSE TAB ════════ */}
        {tab === "analyze" && (
          <>
            {/* Hero */}
            <div style={{ textAlign: "center", padding: "32px 0 28px" }}>
              <h1 style={{ fontSize: "2.2rem", fontWeight: 800, color: colors.text, marginBottom: "10px" }}>
                Is this news <span style={{ color: colors.brand }}>real or fake?</span>
              </h1>
              <p style={{ color: colors.muted, fontSize: "0.97rem" }}>
                Paste any news article — we'll check it using ML + Wikipedia + Google Fact Check.
              </p>
            </div>

            {/* Input card */}
            <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "14px", padding: "24px", marginBottom: "20px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <textarea
                style={{ width: "100%", minHeight: "140px", border: `1px solid ${colors.border}`, borderRadius: "10px", padding: "12px 14px", fontSize: "0.95rem", resize: "vertical", outline: "none", boxSizing: "border-box", fontFamily: "inherit", color: colors.text, background: colors.light, lineHeight: 1.6 }}
                placeholder="Paste your news headline or article here…"
                value={text}
                onChange={e => { setText(e.target.value); setError(""); }}
              />
              {error && <p style={{ color: colors.fake, fontSize: "0.85rem", margin: "6px 0 0" }}>{error}</p>}
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginTop: "12px" }}>
                <button
                  onClick={analyse} disabled={loading}
                  style={{ background: colors.brand, color: "#fff", border: "none", borderRadius: "10px", padding: "11px 28px", fontWeight: 700, fontSize: "0.95rem", cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1 }}
                >
                  {loading ? "Checking…" : "⚡ Analyse"}
                </button>
                <span style={{ color: colors.muted, fontSize: "0.82rem" }}>{text.length} characters</span>
                {loading && <span style={{ color: colors.brand, fontSize: "0.82rem" }}>Searching Wikipedia…</span>}
              </div>
            </div>

            {/* Result */}
            {result && (
              <>
                {/* Final verdict */}
                <div style={{ background: colors.card, border: `2px solid ${labelColor(result.final_label)}`, borderRadius: "14px", padding: "28px", textAlign: "center", marginBottom: "16px", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
                  <div style={{ fontSize: "2.8rem", marginBottom: "6px" }}>
                    {result.final_label === "REAL" ? "✅" : result.final_label === "FAKE" ? "🚨" : "🔶"}
                  </div>
                  <div style={{ fontSize: "1.8rem", fontWeight: 800, color: labelColor(result.final_label), marginBottom: "8px" }}>
                    {result.final_label} NEWS
                  </div>
                  <p style={{ color: colors.muted, margin: 0 }}>{result.final_message}</p>
                </div>

                {/* ML result */}
                <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "14px", padding: "20px", marginBottom: "16px" }}>
                  <div style={{ fontWeight: 700, marginBottom: "14px", color: colors.text }}>🤖 ML Model</div>
                  {[["Real", result.real_probability, colors.real], ["Fake", result.fake_probability, colors.fake]].map(([label, val, color]) => (
                    <div key={label} style={{ marginBottom: "10px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "4px" }}>
                        <span style={{ color: colors.muted }}>{label} probability</span>
                        <span style={{ color, fontWeight: 700 }}>{val.toFixed(1)}%</span>
                      </div>
                      <div style={{ background: colors.light, borderRadius: "99px", height: "8px", overflow: "hidden" }}>
                        <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: "99px", transition: "width 0.8s ease" }} />
                      </div>
                    </div>
                  ))}
                  <p style={{ color: colors.muted, fontSize: "0.82rem", margin: "8px 0 0" }}>Confidence: <strong>{result.confidence.toFixed(1)}%</strong></p>
                </div>

                {/* Fact check */}
                <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "14px", padding: "20px", marginBottom: "16px" }}>
                  <div style={{ fontWeight: 700, marginBottom: "14px", color: colors.text }}>🔍 Fact Check</div>

                  {/* Wikipedia */}
                  <div style={{ background: colors.light, borderRadius: "10px", padding: "14px", marginBottom: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>📖 Wikipedia</span>
                      <span style={{ background: result.fact_check.wikipedia.verdict === "supported" ? colors.real : result.fact_check.wikipedia.verdict === "contradicted" ? colors.fake : colors.muted, color: "#fff", borderRadius: "6px", padding: "2px 10px", fontSize: "0.75rem", fontWeight: 700 }}>
                        {result.fact_check.wikipedia.verdict.toUpperCase()}
                      </span>
                    </div>
                    {result.fact_check.wikipedia.summary && (
                      <p style={{ color: colors.muted, fontSize: "0.85rem", lineHeight: 1.6, margin: "0 0 8px" }}>
                        {result.fact_check.wikipedia.summary}
                      </p>
                    )}
                    {result.fact_check.wikipedia.url && (
                      <a href={result.fact_check.wikipedia.url} target="_blank" rel="noreferrer" style={{ color: colors.brand, fontSize: "0.82rem", textDecoration: "none" }}>
                        Read on Wikipedia →
                      </a>
                    )}
                  </div>


                  {/* Google */}
                  <div style={{ background: colors.light, borderRadius: "10px", padding: "14px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>🔎 Google Fact Check</span>
                      <span style={{ background: result.fact_check.google.verdict === "supported" ? colors.real : result.fact_check.google.verdict === "debunked" ? colors.fake : colors.muted, color: "#fff", borderRadius: "6px", padding: "2px 10px", fontSize: "0.75rem", fontWeight: 700 }}>
                        {result.fact_check.google.verdict.toUpperCase()}
                      </span>
                    </div>
                    {result.fact_check.google.verdict === "skipped" ? (
                      <p style={{ color: colors.muted, fontSize: "0.85rem", margin: 0 }}>
                        Add a Google API key in <code>app.py</code> to enable. Free at <span style={{ color: colors.brand }}>console.cloud.google.com</span>
                      </p>
                    ) : result.fact_check.google.claims?.length > 0 ? (
                      result.fact_check.google.claims.map((c, i) => (
                        <div key={i} style={{ borderTop: `1px solid ${colors.border}`, paddingTop: "8px", marginTop: "8px" }}>
                          <p style={{ fontSize: "0.85rem", margin: "0 0 4px" }}>{c.claim}</p>
                          <p style={{ fontSize: "0.8rem", color: colors.muted, margin: 0 }}>{c.publisher} · <span style={{ color: colors.brand }}>{c.verdict}</span></p>
                        </div>
                      ))
                    ) : (
                      <p style={{ color: colors.muted, fontSize: "0.85rem", margin: 0 }}>No matching records found.</p>
                    )}
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {/* ════════ HISTORY TAB ════════ */}
        {tab === "history" && (
          <div style={{ paddingTop: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <h2 style={{ fontWeight: 800, fontSize: "1.6rem", margin: "0 0 4px" }}>History</h2>
                <p style={{ color: colors.muted, margin: 0, fontSize: "0.88rem" }}>Last 20 articles analysed</p>
              </div>
              {history.length > 0 && (
                <button onClick={deleteAll} style={{ background: "none", border: `1px solid ${colors.fake}`, color: colors.fake, borderRadius: "8px", padding: "8px 14px", cursor: "pointer", fontSize: "0.85rem", fontWeight: 600 }}>
                  🗑 Clear All
                </button>
              )}
            </div>

            <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "14px", overflow: "hidden" }}>
              {history.length === 0 ? (
                <div style={{ textAlign: "center", color: colors.muted, padding: "48px" }}>
                  No history yet. Analyse some articles first!
                </div>
              ) : history.map((item, i) => (
                <div key={item.id} style={{ display: "flex", gap: "12px", padding: "14px 20px", borderBottom: i < history.length - 1 ? `1px solid ${colors.border}` : "none", alignItems: "center" }}>
                  <span style={{ background: item.prediction === "FAKE" ? colors.fake : colors.real, color: "#fff", borderRadius: "6px", padding: "3px 10px", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0 }}>
                    {item.prediction}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: "0.9rem", marginBottom: "3px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.text}</div>
                    <div style={{ color: colors.muted, fontSize: "0.78rem" }}>
                      {item.confidence.toFixed(1)}% confidence · {new Date(item.analyzed_at).toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => deleteOne(item.id)}
                    style={{ background: "none", border: "none", color: colors.muted, cursor: "pointer", fontSize: "1rem", padding: "4px 6px", borderRadius: "6px", flexShrink: 0 }}
                    onMouseEnter={e => e.target.style.color = colors.fake}
                    onMouseLeave={e => e.target.style.color = colors.muted}
                    title="Delete"
                  >🗑</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ════════ STATS TAB ════════ */}
        {tab === "stats" && (
          <div style={{ paddingTop: "24px" }}>
            <h2 style={{ fontWeight: 800, fontSize: "1.6rem", marginBottom: "20px" }}>Statistics</h2>
            {stats && stats.total_analyzed > 0 ? (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "14px", marginBottom: "20px" }}>
                  {[
                    { v: stats.total_analyzed,        l: "Total Analysed", c: colors.brand },
                    { v: `${stats.fake_percentage}%`, l: "Fake News",      c: colors.fake  },
                    { v: `${stats.real_percentage}%`, l: "Real News",      c: colors.real  },
                    { v: `${stats.avg_confidence}%`,  l: "Avg Confidence", c: colors.text  },
                  ].map(({ v, l, c }) => (
                    <div key={l} style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "12px", padding: "18px", textAlign: "center" }}>
                      <div style={{ fontSize: "1.9rem", fontWeight: 800, color: c, marginBottom: "4px" }}>{v}</div>
                      <div style={{ color: colors.muted, fontSize: "0.83rem" }}>{l}</div>
                    </div>
                  ))}
                </div>
                <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "12px", padding: "20px" }}>
                  {[["Fake", stats.fake_percentage, colors.fake], ["Real", stats.real_percentage, colors.real]].map(([label, val, color]) => (
                    <div key={label} style={{ marginBottom: "14px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "6px" }}>
                        <span style={{ color: colors.muted }}>{label} News</span>
                        <span style={{ color, fontWeight: 700 }}>{val}%</span>
                      </div>
                      <div style={{ background: colors.light, borderRadius: "99px", height: "8px", overflow: "hidden" }}>
                        <div style={{ width: `${val}%`, height: "100%", background: color, borderRadius: "99px" }} />
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: "14px", textAlign: "center", color: colors.muted, padding: "48px" }}>
                No data yet. Analyse some articles first!
              </div>
            )}
          </div>
        )}

      </div>

      <footer style={{ textAlign: "center", padding: "24px", color: colors.muted, fontSize: "0.8rem", borderTop: `1px solid ${colors.border}`, marginTop: "32px" }}>
        FakeNews Analyser · ML + NLP + Wikipedia· Flask + React + SQLite
      </footer>
    </div>
  );
}