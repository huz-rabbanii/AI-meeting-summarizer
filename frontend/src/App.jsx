import { useState } from 'react'
import Navbar     from './components/Navbar'
import UploadPage from './components/UploadPage'
import MeetingsPage from './components/MeetingsPage'
import DetailPage from './components/DetailPage'
import SearchPage from './components/SearchPage'

export default function App() {
  const [page, setPage]             = useState('upload')   // upload | meetings | detail | search
  const [selectedId, setSelectedId] = useState(null)
  const [refresh, setRefresh]       = useState(0)

  const goToDetail = (id) => { setSelectedId(id); setPage('detail') }
  const goBack     = ()   => { setPage('meetings'); setRefresh(r => r + 1) }

  return (
    <div className="app">
      <Navbar page={page} setPage={setPage} />
      <main className="main-content">
        {page === 'upload' && (
          <UploadPage onUploaded={(id) => goToDetail(id)} />
        )}
        {page === 'meetings' && (
          <MeetingsPage key={refresh} onSelect={goToDetail} />
        )}
        {page === 'detail' && selectedId && (
          <DetailPage meetingId={selectedId} onBack={goBack} />
        )}
        {page === 'search' && (
          <SearchPage onSelect={goToDetail} />
        )}
      </main>
    </div>
  )
}
