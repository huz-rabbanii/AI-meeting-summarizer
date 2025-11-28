export default function Navbar({ page, setPage }) {
  const links = [
    { id: 'upload',   label: '+ New Meeting' },
    { id: 'meetings', label: 'My Meetings'   },
    { id: 'search',   label: 'Search'        },
  ]
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="icon">🎙️</span>
        MeetingAI
      </div>
      <div className="nav-links">
        {links.map(l => (
          <button
            key={l.id}
            className={`nav-link ${page === l.id ? 'active' : ''}`}
            onClick={() => setPage(l.id)}
          >
            {l.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
