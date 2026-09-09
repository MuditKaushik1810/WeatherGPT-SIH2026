import { useEffect, useState } from 'react'
import Home from './pages/Home'
import Travel from './pages/Travel'
import Disaster from './pages/Disaster'
import CropWatch from './pages/CropWatch'
import CropPlanning from './pages/CropPlanning'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import BottomNav from './components/BottomNav'
import { getPersona } from './lib/preferences'

function getPageFromHash() {
  const page = window.location.hash.replace('#', '').split('?')[0]
  if (['home', 'travel', 'disaster', 'farmer/planning', 'farmer/watch', 'chat', 'settings'].includes(page)) {
    return page
  }
  // No explicit page in the hash → open into the last-used persona. A farmer
  // reopens straight into Farmer Mode (Crop Watch); everyone else lands on Home.
  if (!page && getPersona() === 'farmer') return 'farmer/watch'
  return 'home'
}

function App() {
  const [page, setPage] = useState(getPageFromHash)

  useEffect(() => {
    const handleHashChange = () => setPage(getPageFromHash())
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  // Focused, self-contained screens (own back control / nav) — no global BottomNav.
  if (page === 'farmer/planning') return <CropPlanning />
  if (page === 'farmer/watch') return <CropWatch />
  if (page === 'chat') return <Chat />
  if (page === 'settings') return <Settings />

  let currentPage

  if (page === 'disaster') {
    currentPage = <Disaster />
  } else if (page === 'travel') {
    currentPage = <Travel />
  } else {
    currentPage = <Home />
  }

  return (
    <>
      {currentPage}
      <BottomNav active={page} />
    </>
  )
}

export default App