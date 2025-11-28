import { useState, useRef } from 'react'

const API = '/api/meetings'

export default function UploadPage({ onUploaded }) {
  const [drag, setDrag]       = useState(false)
  const [file, setFile]       = useState(null)
  const [title, setTitle]     = useState('')
  const [ytUrl, setYtUrl]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const inputRef = useRef()

  const ACCEPTED = '.mp3,.mp4,.wav,.ogg,.flac,.m4a,.webm,.mov'

  const handleFile = (f) => {
    if (!f) return
    setFile(f)
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''))
    setError('')
  }

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false)
    handleFile(e.dataTransfer.files[0])
  }

  const submitFile = async () => {
    if (!file) return
    setLoading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', title || file.name)
      const res = await fetch(`${API}/upload`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail || 'Upload failed')
      const data = await res.json()
      onUploaded(data.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const submitYoutube = async () => {
    if (!ytUrl) return
    setLoading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('url', ytUrl)
      if (title) fd.append('title', title)
      const res = await fetch(`${API}/youtube`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to queue YouTube URL')
      const data = await res.json()
      onUploaded(data.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <h1>New Meeting</h1>
        <p>Upload an audio / video file or paste a YouTube link to get started.</p>
      </div>

      {/* ── File upload ── */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginBottom: 16, fontSize: '.9rem', color: 'var(--muted)' }}>UPLOAD FILE</h3>
        <div
          className={`upload-zone ${drag ? 'drag-over' : ''}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
        >
          <div className="upload-icon">{file ? '✅' : '📁'}</div>
          {file
            ? <><h3>{file.name}</h3><p>{(file.size / 1024 / 1024).toFixed(1)} MB</p></>
            : <><h3>Drop your file here</h3><p>MP3, MP4, WAV, OGG, FLAC, M4A, WebM — up to 500 MB</p></>
          }
          <input
            ref={inputRef} type="file" accept={ACCEPTED} style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </div>

        {file && (
          <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              className="text-input"
              placeholder="Meeting title (optional)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <button className="btn btn-primary" onClick={submitFile} disabled={loading}>
              {loading ? <><span className="spinner" /> Processing…</> : '▶ Start Processing'}
            </button>
          </div>
        )}
      </div>

      {/* ── YouTube ── */}
      <div className="card">
        <h3 style={{ marginBottom: 16, fontSize: '.9rem', color: 'var(--muted)' }}>YOUTUBE URL</h3>
        <div className="yt-form">
          <input
            className="text-input"
            placeholder="https://www.youtube.com/watch?v=..."
            value={ytUrl}
            onChange={(e) => setYtUrl(e.target.value)}
          />
          <input
            className="text-input"
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{ maxWidth: 220 }}
          />
          <button className="btn btn-primary" onClick={submitYoutube} disabled={loading || !ytUrl}>
            {loading ? <><span className="spinner" /> Downloading…</> : '▶ Process Video'}
          </button>
        </div>
        <p style={{ marginTop: 10, fontSize: '.76rem', color: 'var(--muted)' }}>
          The audio will be extracted and processed. Works with any public YouTube video.
        </p>
      </div>

      {error && <p className="error-msg" style={{ marginTop: 14 }}>⚠ {error}</p>}
    </>
  )
}
