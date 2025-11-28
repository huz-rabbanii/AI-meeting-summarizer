import { useState } from 'react'
import StatusBadge from './StatusBadge'

const API = '/api/search'

export default function SearchPage({ onSelect }) {
  const [query, setQuery]     = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/?q=${encodeURIComponent(query)}`)
      const data = await res.json()
      setResults(data.results || [])
    } catch (_) {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e) => { if (e.key === 'Enter') search() }

  return (
    <>
      <div className="page-header">
        <h1>Search Meetings</h1>
        <p>Search across all transcripts, summaries, and notes.</p>
      </div>

      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Search for keywords, topics, people…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKey}
        />
        <button className="btn btn-primary" onClick={search} disabled={loading || !query.trim()}>
          {loading ? <span className="spinner" /> : '🔍 Search'}
        </button>
      </div>

      {results === null && (
        <div className="empty-state">
          <div className="icon">🔍</div>
          <p>Type a query and press Search or Enter.</p>
        </div>
      )}

      {results !== null && results.length === 0 && (
        <div className="empty-state">
          <div className="icon">🕵️</div>
          <p>No results found for "{query}".</p>
        </div>
      )}

      {results !== null && results.length > 0 && (
        <div className="meeting-list">
          {results.map(r => (
            <div key={r.id} className="meeting-item card search-result" onClick={() => onSelect(r.id)}>
              <div className="meeting-item-info">
                <div className="meeting-item-title">{r.title || 'Untitled'}</div>
                <div className="meeting-item-meta">
                  {new Date(r.created_at).toLocaleDateString()} ·
                  Matched in: {(r.hit_fields || []).join(', ')}
                </div>
                {r.snippet && <div className="search-snippet">{r.snippet}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
