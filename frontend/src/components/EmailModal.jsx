import { useState } from 'react'

const API = '/api/meetings'

export default function EmailModal({ meetingId, onClose }) {
  const [emails, setEmails]   = useState('')
  const [sending, setSending] = useState(false)
  const [done, setDone]       = useState(false)
  const [error, setError]     = useState('')

  const send = async () => {
    const recipients = emails.split(/[\n,]+/).map(e => e.trim()).filter(Boolean)
    if (!recipients.length) { setError('Enter at least one email address.'); return }
    setSending(true); setError('')
    try {
      const res = await fetch(`${API}/${meetingId}/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipients }),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed to send')
      setDone(true)
    } catch (e) {
      setError(e.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>📧 Email Summary</h2>
        {done ? (
          <>
            <p style={{ color: 'var(--green)', fontSize: '.9rem' }}>✅ Summary sent successfully!</p>
            <div className="modal-actions">
              <button className="btn btn-secondary btn-sm" onClick={onClose}>Close</button>
            </div>
          </>
        ) : (
          <>
            <label>Recipient email addresses (one per line or comma-separated)</label>
            <textarea
              rows={4}
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              placeholder="alice@example.com, bob@example.com"
            />
            {error && <p className="error-msg">{error}</p>}
            <div className="modal-actions">
              <button className="btn btn-secondary btn-sm" onClick={onClose}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={send} disabled={sending}>
                {sending ? <><span className="spinner" /> Sending…</> : 'Send Email'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
