import { useEffect, useState } from 'react'
import Home from './pages/Home'
import Disaster from './pages/Disaster'

function getPageFromHash() {
  const page = window.location.hash.replace('#', '')
  return ['home', 'travel', 'disaster'].includes(page) ? page : 'home'
}

function TravelPlaceholder() {
  return (
    <main className="app-shell">
      <div className="travel-placeholder">
        <h1>Travel</h1>
        <p>Travel Planner is the next frontend tab.</p>
        <p>This placeholder keeps the shared navigation wired without inventing a Travel API.</p>
      </div>
    </main>
  )
}

function App() {
  const [page, setPage] = useState(getPageFromHash)

  useEffect(() => {
    const handleHashChange = () => setPage(getPageFromHash())
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  if (page === 'disaster') return <Disaster />
  if (page === 'travel') return <TravelPlaceholder />
  return <Home />
}

export default App
