import { useEffect, useMemo, useState } from "react";
import { fetchJson } from "./api.js";

const fmtDate = (iso) => new Date(iso).toLocaleString();

const formatHourLabel = (iso) => {
  const base = new Date(iso);
  const start = new Date(base);
  start.setMinutes(0, 0, 0);
  const end = new Date(start);
  end.setMinutes(59, 59, 999);
  const compress = (date) =>
    date
      .toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
      .replace(/\s+/g, "");
  return `${start.toLocaleDateString()} • ${compress(start)}-${compress(end)}`;
};

function Header({ onRefresh, onCapture, isCapturing }) {
  return (
    <header className="header">
      <div>
        <h1 className="title">PetCam</h1>
        <p className="subtitle">Latest snapshot and browse history</p>
      </div>
      <div className="header-actions">
        <button className="btn" onClick={onCapture} disabled={isCapturing}>
          {isCapturing ? "Capturing…" : "Capture"}
        </button>
        <button className="btn" onClick={onRefresh} disabled={isCapturing}>
          Refresh
        </button>
      </div>
    </header>
  );
}

function InfoBanner({ baseUrl }) {
  return (
    <div className="banner">
      Backend: <code>{baseUrl}</code>
    </div>
  );
}

function Latest({ latest }) {
  if (!latest) {
    return <div className="card">No images yet.</div>;
  }
  return (
    <div className="card">
      <div className="card-header">
        <strong>Latest</strong> — {fmtDate(latest.timestamp)}
      </div>
      <img
        className="latest-img"
        src={latest.image_url}
        alt="Latest capture"
        loading="eager"
      />
    </div>
  );
}

function List({ bucket, onSelect, onPrev, onNext, hasPrev, hasNext }) {
  if (!bucket || !bucket.items?.length) {
    return <div className="card">No images to show.</div>;
  }
  const items = bucket.items;
  return (
    <div className="card">
      <div className="grid-controls">
        <button className="btn btn-ghost" onClick={onPrev} disabled={!hasPrev}>
          ← Previous
        </button>
        <div className="grid-title">{bucket.label}</div>
        <button className="btn btn-ghost" onClick={onNext} disabled={!hasNext}>
          Next →
        </button>
      </div>
      <div className="grid">
        {items.map((img) => (
          <button
            key={img.id}
            className="card card-clickable"
            onClick={() => onSelect(img)}
            title="View full image"
          >
            <div className="card-header">{fmtDate(img.timestamp)}</div>
            <img
              className="thumb"
              src={img.thumbnail_url}
              alt={img.filename}
              loading="lazy"
            />
            <div className="meta">
              <div>{img.filename}</div>
              <div>{(img.filesize / 1024).toFixed(1)} KB</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function DetailView({ image, onBack }) {
  if (!image) return null;
  return (
    <div className="card detail-card">
      <div className="detail-header">
        <div>
          <div className="card-header">{fmtDate(image.timestamp)}</div>
          <div className="meta">{image.filename}</div>
        </div>
        <button className="btn btn-ghost" onClick={onBack}>
          Back to grid
        </button>
      </div>
      <img className="detail-img" src={image.image_url} alt={image.filename} />
    </div>
  );
}

export default function App() {
  const apiBase = useMemo(
    () => (import.meta.env.VITE_API_BASE || "http://localhost:5000/api").replace(/\/$/, ""),
    []
  );
  const [latest, setLatest] = useState(null);
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [hourIndex, setHourIndex] = useState(0);

  const hourBuckets = useMemo(() => {
    if (!list.length) return [];
    const buckets = [];
    list.forEach((img) => {
      const ts = new Date(img.timestamp);
      const key = `${ts.getFullYear()}-${ts.getMonth()}-${ts.getDate()}-${ts.getHours()}`;
      const last = buckets[buckets.length - 1];
      if (!last || last.key !== key) {
        buckets.push({
          key,
          label: formatHourLabel(img.timestamp),
          items: [img],
        });
      } else {
        last.items.push(img);
      }
    });
    return buckets;
  }, [list]);

  useEffect(() => {
    setHourIndex(0);
  }, [list]);

  const currentBucket = hourBuckets[hourIndex] || null;

  const load = async () => {
    setLoading(true);
    setError("");
    setSelected(null);
    try {
      const [latestResp, listResp] = await Promise.allSettled([
        fetchJson(`${apiBase}/latest`),
        fetchJson(`${apiBase}/list?per_page=50`)
      ]);

      if (latestResp.status === "fulfilled") {
        setLatest(latestResp.value);
      } else {
        setLatest(null);
      }

      if (listResp.status === "fulfilled") {
        setList(listResp.value.items || []);
      } else {
        setList([]);
        throw listResp.reason;
      }
    } catch (err) {
      setError(err?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const triggerCapture = async () => {
    if (capturing) return;
    setCapturing(true);
    setError("");
    try {
      await fetchJson(`${apiBase}/capture`, { method: "POST" });
      await load();
    } catch (err) {
      setError(err?.message || "Failed to capture image");
    } finally {
      setCapturing(false);
    }
  };

  const goPrevHour = () => {
    setHourIndex((idx) => Math.max(0, idx - 1));
    setSelected(null);
  };

  const goNextHour = () => {
    setHourIndex((idx) => Math.min(hourBuckets.length - 1, idx + 1));
    setSelected(null);
  };

  return (
    <div className="page">
      <Header onRefresh={load} onCapture={triggerCapture} isCapturing={capturing} />
      <InfoBanner baseUrl={apiBase} />
      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading…</div>}
      {!loading && (
        <>
          <Latest latest={latest} />
          {selected ? (
            <DetailView image={selected} onBack={() => setSelected(null)} />
          ) : (
            <List
              bucket={currentBucket}
              onSelect={setSelected}
              onPrev={goPrevHour}
              onNext={goNextHour}
              hasPrev={hourIndex > 0}
              hasNext={hourIndex < hourBuckets.length - 1}
            />
          )}
        </>
      )}
    </div>
  );
}
