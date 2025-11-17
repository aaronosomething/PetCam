import { useEffect, useMemo, useState } from "react";
import { fetchJson } from "./api.js";

const fmtDate = (iso) => new Date(iso).toLocaleString();

function Header({ onRefresh }) {
  return (
    <header className="header">
      <div>
        <h1 className="title">PetCam</h1>
        <p className="subtitle">Latest snapshot and browse history</p>
      </div>
      <button className="btn" onClick={onRefresh}>
        Refresh
      </button>
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

function List({ items, onSelect }) {
  if (!items?.length) {
    return <div className="card">No images to show.</div>;
  }
  return (
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

  const load = async () => {
    setLoading(true);
    setError("");
    setSelected(null);
    try {
      const [latestResp, listResp] = await Promise.allSettled([
        fetchJson(`${apiBase}/latest`),
        fetchJson(`${apiBase}/list?per_page=30`)
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

  return (
    <div className="page">
      <Header onRefresh={load} />
      <InfoBanner baseUrl={apiBase} />
      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Loading…</div>}
      {!loading && (
        <>
          <Latest latest={latest} />
          {selected ? (
            <DetailView image={selected} onBack={() => setSelected(null)} />
          ) : (
            <List items={list} onSelect={setSelected} />
          )}
        </>
      )}
    </div>
  );
}
