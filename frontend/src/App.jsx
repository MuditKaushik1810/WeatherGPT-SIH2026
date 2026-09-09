import { useEffect, useState } from 'react'
import Home from './pages/Home'
import Travel from './pages/Travel'
import Disaster from './pages/Disaster'
import CropWatch from './pages/CropWatch'
import CropPlanning from './pages/CropPlanning'
import BottomNav from './components/BottomNav'

function getPageFromHash() {
  const page = window.location.hash.replace('#', '').split('?')[0]
  return ['home', 'travel', 'disaster', 'farmer/planning', 'farmer/watch'].includes(page) ? page : 'home'
}

function App() {
  const [page, setPage] = useState(getPageFromHash)

  useEffect(() => {
    const handleHashChange = () => setPage(getPageFromHash())
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  if (page === 'farmer/planning') return <CropPlanning />
  if (page === 'farmer/watch') return <CropWatch />

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