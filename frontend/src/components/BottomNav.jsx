function BottomNav({ active }) {
  const items = [
    { id: 'home', label: 'Home', symbol: '⌂' },
    { id: 'travel', label: 'Travel', symbol: '▣' },
    { id: 'disaster', label: 'Disaster', symbol: '▲' },
  ]

  return (
    <nav className="bottom-nav" aria-label="Primary navigation">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`bottom-nav-item ${active === item.id ? 'active' : ''}`}
          onClick={() => { window.location.hash = item.id }}
          aria-current={active === item.id ? 'page' : undefined}
        >
          <span className="bottom-nav-symbol" aria-hidden="true">{item.symbol}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default BottomNav
