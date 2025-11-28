import { useEffect, useState, useRef } from 'react'
import StatusBadge  from './StatusBadge'
import EmailModal   from './EmailModal'

const API = '/api/meetings'

function fmtDur(s) { if (!s) return ''; const m = Math.floor(s/60); return `${m}m ${s%60}s` }
function fmtDate(d) { if (!d) return ''; return new Date(d).toLocaleString() }
function fmtTime(ms) { if (!ms) return '0:00'; const s=Math.round(ms/1000); return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}` }

export default function DetailPage({ meetingId, onBack }) {
  const [meeting, setMeeting]     = useState(null)
  const [tab, setTab]             = useState('summary')
  const [emailOpen, setEmailOpen] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const pollRef = useRef(null)

  const load = async () => {
    try {
      const res = await fetch(`${API}/${meetingId}`)
      if (!res.ok) return
      const data = await res.json()
      setMeeting(data)
      if (data.status === 'pending' || data.status === 'processing') {
        pollRef.current = setTimeout(load, 3000)
      }
    } catch (_) {}
  }

  useEffect(() => {
    load()
    return () => clearTimeout(pollRef.current)
  }, [meetingId])

  const downloadPdf = async () => {
    setPdfLoading(true)
    try {
      const res = await fetch(`${API}/${meetingId}/export/pdf`)
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = Object.assign(document.createElement('a'), { href: url, download: `${meeting?.title || 'meeting'}.pdf` })
      a.click(); URL.revokeObjectURL(url)
    } catch (e) { alert(e.message) }
    finally { setPdfLoading(false) }
  }

  if (!meeting) return <div style={{ padding: 40, textAlign: 'center' }}><span className="spinner" /></div>

  const speakers  = meeting.speakers  || []
  const chapters  = meeting.chapters  || []
  const actions   = meeting.action_items || []
  const keywords  = meeting.keywords  || []

  const tabs = [
    { id: 'summary',    label: '📝 Summary'         },
    { id: 'transcript', label: '📄 Transcript'       },
    ...(actions.length   ? [{ id: 'actions',    label: `✅ Actions (${actions.length})`    }] : []),
    ...(speakers.length  ? [{ id: 'speakers',   label: `👥 Speakers (${speakers.length})` }] : []),
    ...(chapters.length  ? [{ id: 'chapters',   label: `📚 Chapters (${chapters.length})` }] : []),
    ...(keywords.length  ? [{ id: 'keywords',   label: '🏷️ Keywords'                       }] : []),
  ]

  const isProcessing = meeting.status === 'pending' || meeting.status === 'processing'

  return (
    <>
      {emailOpen && (
        <EmailModal
          meetingId={meetingId}
          onClose={() => setEmailOpen(false)}
        />
      )}

      <div className="detail-header">
        <div>
          <button className="btn btn-secondary btn-sm" onClick={onBack} style={{ marginBottom: 10 }}>← Back</button>
          <div className="detail-title">{meeting.title || 'Untitled Meeting'}</div>
          <div className="detail-meta">
            <StatusBadge status={meeting.status} />
            {meeting.created_at && <span>Processed {fmtDate(meeting.created_at)}</span>}
            {meeting.duration_seconds && <span>Duration: {fmtDur(meeting.duration_seconds)}</span>}
            {meeting.source_type === 'youtube' && <span>Source: YouTube</span>}
          </div>
        </div>
        <div className="detail-actions">
          {meeting.status === 'done' && (
            <>
              <button className="btn btn-secondary btn-sm" onClick={downloadPdf} disabled={pdfLoading}>
                {pdfLoading ? <><span className="spinner" /> Exporting…</> : '⬇ PDF'}
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => setEmailOpen(true)}>
                📧 Email
              </button>
            </>
          )}
        </div>
      </div>

      {isProcessing && (
        <div className="card" style={{ marginBottom: 24, display: 'flex', gap: 14, alignItems: 'center' }}>
          <span className="spinner" />
          <span style={{ color: 'var(--muted)', fontSize: '.88rem' }}>
            Your meeting is being processed. This usually takes 1–3 minutes. This page will update automatically.
          </span>
        </div>
      )}

      {meeting.status === 'error' && (
        <div className="card" style={{ borderColor: 'rgba(239,68,68,.3)', marginBottom: 24 }}>
          <p className="error-msg">⚠ Processing failed: {meeting.error_message || 'Unknown error'}</p>
        </div>
      )}

      {meeting.status === 'done' && (
        <>
          <div className="tabs">
            {tabs.map(t => (
              <button key={t.id} className={`tab-btn ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'summary' && (
            <div className="card">
              <p className="summary-text">{meeting.summary || 'No summary available.'}</p>
            </div>
          )}

          {tab === 'transcript' && (
            <div className="transcript-box">{meeting.transcript || 'No transcript available.'}</div>
          )}

          {tab === 'actions' && (
            <div className="card">
              <ul className="action-list">
                {actions.map((a, i) => (
                  <li key={i} className="action-item">
                    <span className="action-num">{i + 1}.</span>
                    <span>{typeof a === 'string' ? a : a.text || JSON.stringify(a)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {tab === 'speakers' && (
            <div className="speaker-list">
              {speakers.map((seg, i) => (
                <div key={i} className="speaker-seg">
                  <div>
                    <div className="speaker-label">{seg.speaker || `Speaker ${i}`}</div>
                    <div className="speaker-time">{fmtTime(seg.start)} – {fmtTime(seg.end)}</div>
                  </div>
                  <div className="speaker-bubble">{seg.text}</div>
                </div>
              ))}
            </div>
          )}

          {tab === 'chapters' && (
            <div className="chapter-list">
              {chapters.map((ch, i) => (
                <div key={i} className="chapter-item">
                  <div className="chapter-time">{fmtTime(ch.start)} – {fmtTime(ch.end)}</div>
                  <div className="chapter-title">{ch.headline || ch.title || `Chapter ${i + 1}`}</div>
                  <div className="chapter-summary">{ch.summary || ch.gist}</div>
                </div>
              ))}
            </div>
          )}

          {tab === 'keywords' && (
            <div className="card">
              <div className="keyword-list">
                {keywords.map((kw, i) => (
                  <span key={i} className="keyword-tag">
                    {typeof kw === 'string' ? kw : kw.text || kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}
