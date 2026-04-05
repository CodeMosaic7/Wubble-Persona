import { useState, useRef, useCallback } from "react";

const CLIP_COLORS = [
  "#E8321A","#1DBF73","#378ADD","#F5A623",
  "#9B59B6","#D4537E","#639922","#0F6E56",
];

const PLATFORMS = [
  { id: "reels",   label: "Reels / TikTok", res: "1080×1920", icon: "📱" },
  { id: "youtube", label: "YouTube",         res: "1920×1080", icon: "🖥" },
  { id: "square",  label: "Square",          res: "1080×1080", icon: "⬜" },
];

const PROG_STEPS = [
  "Fetching song from Wubble API",
  "Analyzing audio with librosa",
  "Detecting BPM & energy peaks",
  "Building beat map",
  "Asking Groq to plan the edit",
  "Constructing FFmpeg filter chain",
  "Rendering beat-synced video",
  "Encoding H.264 + AAC 192k",
  "Finalizing output file",
];
const PROG_PCTS = [8, 18, 30, 40, 55, 65, 78, 90, 97];

function genEnergies(n = 64) {
  return Array.from({ length: n }, (_, i) => {
    const a = 0.35 + 0.6 * Math.abs(Math.sin(i * 0.31 + 1.2));
    const b = 0.20 + 0.5 * Math.abs(Math.sin(i * 0.73 + 0.4));
    return Math.min(1, Math.max(0.05, (a + b) / 2 + (Math.random() - 0.5) * 0.15));
  });
}

function Waveform({ energies, pulsing }) {
  return (
    <div className="waveform">
      {energies.map((e, i) => (
        <div
          key={i}
          className={`wave-bar${pulsing ? " pulsing" : ""}`}
          style={{
            height: Math.max(3, e * 44) + "px",
            animationDelay: pulsing ? i * 0.02 + "s" : "0s",
            background:
              e > 0.78 ? "#E8321A" :
              e > 0.55 ? "#F5A623" :
              "rgba(245,242,237,0.18)",
          }}
        />
      ))}
    </div>
  );
}

function Timeline({ files, energies }) {
  const totalSec = 30;
  const clipCount = Math.min(files.length * 4, 24);
  const clips = Array.from({ length: clipCount }, (_, i) => {
    const fileIdx = i % files.length;
    const eIdx = Math.floor((i / clipCount) * energies.length);
    const e = energies[eIdx] || 0.5;
    const base = totalSec / clipCount;
    const dur = e > 0.75 ? base * 0.65 : e < 0.4 ? base * 1.3 : base;
    return { fileIdx, dur, name: files[fileIdx].name.replace(/\.[^.]+$/, "").slice(0, 5) };
  });
  return (
    <div className="timeline-section">
      <div className="section-label">edit plan preview</div>
      <div className="tl-track">
        {clips.map((c, i) => (
          <div
            key={i}
            className="tl-clip"
            style={{
              flex: (c.dur / totalSec * 100).toFixed(2),
              background: CLIP_COLORS[c.fileIdx % CLIP_COLORS.length],
              opacity: 0.8 + (c.fileIdx % 3) * 0.07,
            }}
          >
            {c.name}
          </div>
        ))}
      </div>
      <div className="tl-ruler">
        <span>0s</span>
        <span>{Math.round(totalSec / 2)}s</span>
        <span>{totalSec}s</span>
      </div>
    </div>
  );
}

function ProgressPanel({ step, pct }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="panel-head-left">
          <span className="panel-icon">⚙</span>
          <span className="panel-title">Generating</span>
        </div>
        <span className="badge badge-red">{pct}%</span>
      </div>
      <div className="panel-body">
        <div className="prog-bar-bg">
          <div className="prog-bar-fill" style={{ width: pct + "%" }} />
        </div>
        <div className="prog-steps">
          {PROG_STEPS.map((label, i) => (
            <div
              key={i}
              className={`prog-step${i === step ? " active" : i < step ? " done" : ""}`}
            >
              <div className="prog-dot" />
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ResultPanel({ bpm, cuts, duration, platform, onDownload }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <div className="panel-head-left">
          <span className="panel-icon">✓</span>
          <span className="panel-title">Ready to post</span>
        </div>
        <span className="badge badge-green">done</span>
      </div>
      <div className="panel-body">
        <div className="result-top">
          <div className="result-check">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M4 10l4.5 4.5L16 6" stroke="#1DBF73" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <div className="result-title">Beat-synced video</div>
            <div className="result-meta">{platform} · {bpm} BPM · {cuts} cuts · {duration}s</div>
          </div>
        </div>
        <button className="dl-btn" onClick={() => onDownload(platform)}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 2v10M5 8l4 4 4-4M2 15h14" stroke="#0A0A0A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          DOWNLOAD MP4
        </button>
        <div className="dl-formats">
          {PLATFORMS.map(p => (
            <button key={p.id} className="dl-fmt-btn" onClick={() => onDownload(p.id)}>
              {p.label.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function BeatSyncStudio() {
  const [reqId, setReqId]         = useState("");
  const [platform, setPlatform]   = useState("reels");
  const [files, setFiles]         = useState([]);
  const [energies, setEnergies]   = useState([]);
  const [dragging, setDragging]   = useState(false);
  const [status, setStatus]       = useState("idle"); // idle | running | done | error
  const [progStep, setProgStep]   = useState(-1);
  const [progPct, setProgPct]     = useState(0);
  const [error, setError]         = useState("");
  const [result, setResult]       = useState(null);
  const [downloadUrl, setDlUrl]   = useState(null);
  const timerRef = useRef(null);
  const inputRef = useRef(null);

  const canGenerate = reqId.trim().length > 3 && files.length > 0;

  // ── Files ──
  const addFiles = useCallback((incoming) => {
    const arr = Array.from(incoming).filter(
      f => !files.find(x => x.name === f.name && x.size === f.size)
    );
    if (!arr.length) return;
    const next = [...files, ...arr];
    setFiles(next);
    setEnergies(genEnergies());
  }, [files]);

  const removeFile = (i) => {
    const next = files.filter((_, idx) => idx !== i);
    setFiles(next);
    if (next.length === 0) setEnergies([]);
  };

  // ── Drag ──
  const onDragOver  = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = ()  => setDragging(false);
  const onDrop      = (e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); };

  // ── Progress animation ──
  const animateProgress = () => {
    let idx = 0;
    const tick = () => {
      if (idx >= PROG_STEPS.length) return;
      setProgStep(idx);
      setProgPct(PROG_PCTS[idx]);
      idx++;
      const delay = idx === 1 ? 600 : 1800 + Math.random() * 1200;
      timerRef.current = setTimeout(tick, delay);
    };
    tick();
  };

  // ── Generate ──
  const generate = async () => {
    setError("");
    setStatus("running");
    setProgStep(-1);
    setProgPct(0);
    setResult(null);
    animateProgress();

    const form = new FormData();
    form.append("req_id", reqId.trim());
    form.append("platform", platform);
    files.forEach(f => form.append("media", f));

    try {
      const res = await fetch("/generate-video/beat-sync", { method: "POST", body: form });
      clearTimeout(timerRef.current);

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Server error");
      }

      setProgStep(PROG_STEPS.length);
      setProgPct(100);

      const bpm      = parseFloat(res.headers.get("X-BPM") || "0").toFixed(1);
      const cuts     = res.headers.get("X-Total-Cuts") || "—";
      const duration = parseFloat(res.headers.get("X-Audio-Duration") || "0").toFixed(0);

      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      setDlUrl(url);
      setResult({ bpm, cuts, duration });

      setTimeout(() => setStatus("done"), 500);
    } catch (err) {
      clearTimeout(timerRef.current);
      setError(err.message);
      setStatus("error");
    }
  };

  const triggerDownload = (plat) => {
    if (!downloadUrl) return;
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `beatsync_${plat}.mp4`;
    a.click();
  };

  return (
    <div className="app">

      {/* Hero */}
      <header className="hero">
        <div className="hero-left">
          <div className="hero-wordmark">
            <div className="hero-logo">
              <svg viewBox="0 0 26 26" fill="none" width="26" height="26">
                <rect x="3"  y="10" width="3" height="14" rx="1.5" fill="white"/>
                <rect x="8"  y="5"  width="3" height="19" rx="1.5" fill="white"/>
                <rect x="13" y="1"  width="3" height="23" rx="1.5" fill="white"/>
                <rect x="18" y="6"  width="3" height="17" rx="1.5" fill="white"/>
              </svg>
            </div>
            <span className="wordmark-sub">persona / studio</span>
          </div>
          <h1 className="hero-title">BEAT<br/><em>SYNC</em></h1>
          <p className="hero-sub">every cut lands on a beat drop — automatically</p>
        </div>
        {result && (
          <div className="bpm-display">
            <div className="bpm-number">{result.bpm}</div>
            <div className="bpm-label">BPM detected</div>
          </div>
        )}
      </header>

      {/* Main grid */}
      <div className="main-grid">

        {/* LEFT */}
        <div className="left-col">

          {/* Song panel */}
          <div className="panel" style={{ marginBottom: 20 }}>
            <div className="panel-head">
              <div className="panel-head-left">
                <span className="panel-icon">🎵</span>
                <span className="panel-title">Song source</span>
              </div>
              <span className={`badge ${reqId.length > 3 ? "badge-green" : ""}`}>
                {reqId.length > 3 ? "set" : "required"}
              </span>
            </div>
            <div className="panel-body">
              <div className="field">
                <label className="field-label">Wubble Request ID</label>
                <input
                  type="text"
                  className="text-input"
                  placeholder="req_abc123xyz…"
                  value={reqId}
                  onChange={e => setReqId(e.target.value)}
                />
              </div>
              <div className="field" style={{ marginBottom: 0 }}>
                <label className="field-label">Platform format</label>
                <div className="platform-row">
                  {PLATFORMS.map(p => (
                    <button
                      key={p.id}
                      className={`plat-btn${platform === p.id ? " sel" : ""}`}
                      onClick={() => setPlatform(p.id)}
                    >
                      <span className="plat-icon">{p.icon}</span>
                      <div className="plat-name">{p.label}</div>
                      <div className="plat-res">{p.res}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Media panel */}
          <div className="panel">
            <div className="panel-head">
              <div className="panel-head-left">
                <span className="panel-icon">🖼</span>
                <span className="panel-title">Media files</span>
              </div>
              <span className={`badge ${files.length > 0 ? "badge-green" : ""}`}>
                {files.length === 0 ? "0 files" : `${files.length} file${files.length > 1 ? "s" : ""}`}
              </span>
            </div>
            <div className="panel-body">

              {/* Drop zone */}
              <div
                className={`drop-zone${dragging ? " dragover" : ""}`}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
              >
                <input
                  ref={inputRef}
                  type="file"
                  multiple
                  accept="image/*,video/*"
                  style={{ display: "none" }}
                  onChange={e => addFiles(e.target.files)}
                />
                <div className="dz-icon-wrap">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <path d="M11 3v12M7 7l4-4 4 4" stroke="rgba(245,242,237,0.5)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M3 17h16" stroke="rgba(245,242,237,0.3)" strokeWidth="1.6" strokeLinecap="round"/>
                  </svg>
                </div>
                <div className="dz-title">Drop files here</div>
                <div className="dz-sub">JPG · PNG · MP4 · MOV — mix freely</div>
              </div>

              {/* Thumbnails */}
              {files.length > 0 && (
                <div className="thumb-grid">
                  {files.map((f, i) => {
                    const isVid = f.type.startsWith("video");
                    return (
                      <div key={i} className="thumb">
                        {isVid
                          ? <div className="thumb-vid-icon">▶</div>
                          : <img src={URL.createObjectURL(f)} alt={f.name} />
                        }
                        <span className="thumb-tag">{isVid ? "VID" : "IMG"}</span>
                        <button className="thumb-rm" onClick={() => removeFile(i)}>×</button>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Waveform */}
              {energies.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div className="section-label">beat energy map (simulated)</div>
                  <Waveform energies={energies} pulsing={status === "running"} />
                </div>
              )}

              {/* Timeline */}
              {files.length > 0 && energies.length > 0 && (
                <Timeline files={files} energies={energies} />
              )}

              {/* Stats */}
              {files.length > 0 && (
                <div className="stats-strip">
                  <div className="stat-cell">
                    <div className="stat-val">{files.length}</div>
                    <div className="stat-lbl">files</div>
                  </div>
                  <div className="stat-cell">
                    <div className="stat-val">{Math.min(files.length * 4, 24)}</div>
                    <div className="stat-lbl">est. cuts</div>
                  </div>
                  <div className="stat-cell">
                    <div className="stat-val">~30s</div>
                    <div className="stat-lbl">target dur.</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT */}
        <div className="right-col">

          {/* Error */}
          {(status === "error") && (
            <div className="error-bar">✕  {error}</div>
          )}

          {/* Progress */}
          {status === "running" && (
            <ProgressPanel step={progStep} pct={progPct} />
          )}

          {/* Result */}
          {status === "done" && result && (
            <ResultPanel
              bpm={result.bpm}
              cuts={result.cuts}
              duration={result.duration}
              platform={platform}
              onDownload={triggerDownload}
            />
          )}

          {/* Generate button */}
          <button
            className="gen-btn"
            disabled={!canGenerate || status === "running"}
            onClick={generate}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2v8m0 0l-3-3m3 3l3-3M3 14l2 3h10l2-3" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {status === "running" ? "GENERATING…" : "GENERATE VIDEO"}
          </button>

          {/* How it works */}
          <div className="panel">
            <div className="panel-head">
              <div className="panel-head-left">
                <span className="panel-icon">?</span>
                <span className="panel-title">How it works</span>
              </div>
            </div>
            <div className="panel-body">
              {[
                ["01", "Beat detection",  "librosa analyzes BPM, beat timestamps and energy levels per beat"],
                ["02", "AI edit plan",    "Groq LLM assigns media to beats — short cuts on drops, long on verses"],
                ["03", "FFmpeg render",   "Hard cuts on every beat timestamp — zoom_in, zoom_out, flash effects"],
                ["04", "Download & post", "MP4 exported at platform resolution — ready to upload instantly"],
              ].map(([num, title, desc]) => (
                <div key={num} className="how-step">
                  <span className="how-num">{num}</span>
                  <div>
                    <div className="how-title">{title}</div>
                    <div className="how-desc">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}