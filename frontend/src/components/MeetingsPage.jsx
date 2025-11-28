import { useEffect, useState } from 'react'
import StatusBadge from './StatusBadge'

const API = '/api/meetings'

function fmt(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function fmtDur(s) {
  if (!s) return null
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}m ${sec}s`
}

export default function MeetingsPage({ onSelect }) {
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading]  = useState(true)
  const [error, setError]      = useState('')

  const load = async () => {
    try {
      const res = await fetch(API + '/')
      if (!res.ok) throw new Error('Failed to load meetings')
      const data = await res.json()
      setMeetings(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const deleteMeeting = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this meeting?')) return
    await fetch(`${API}/${id}`, { method: 'DELETE' })
    setMeetings(m => m.filter(x => x.id !== id))
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}><span className="spinner" /></div>

  if (!meetings.length) return (
    <>
      <div className="page-header"><h1>My Meetings</h1></div>
      <div className="empty-state">
        <div className="icon">📭</div>
        <p>No meetings yet. Upload one to get started.</p>
      </div>
    </>
  )

  return (
    <>
      <div className="page-header">
        <h1>My Meetings</h1>
        <p>{meetings.length} meeting{meetings.length !== 1 ? 's' : ''} found</p>
      </div>
      {error && <p className="error-msg">{error}</p>}
      <div className="meeting-list">
        {meetings.map(m => (
          <div key={m.id} className="meeting-item" onClick={() => onSelect(m.id)}>
            <div className="meeting-item-icon">
              {m.source_type === 'youtube' ? '▶️' : '🎙️'}
            </div>
            <div className="meeting-item-info">
              <div className="meeting-item-title">{m.title || 'Untitled Meeting'}</div>
              <div className="meeting-item-meta">
                {fmt(m.created_at)}
                {m.duration_seconds ? ` · ${fmtDur(m.duration_seconds)}` : ''}
                {m.source_type === 'youtube' ? ' · YouTube' : ''}
              </div>
            </div>
            <StatusBadge status={m.status} />
            <div className="meeting-item-actions" onClick={(e) => e.stopPropagation()}>
              <button className="btn btn-sm btn-danger" onClick={(e) => deleteMeeting(e, m.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
