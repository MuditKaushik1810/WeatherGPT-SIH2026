import { useI18n } from '../i18n'

function BottomNav({ active }) {
  const { t } = useI18n()
  const items = [
    { id: 'home', labelKey: 'nav.home', symbol: '⌂' },
    { id: 'travel', labelKey: 'nav.travel', symbol: '▣' },
    { id: 'disaster', labelKey: 'nav.disaster', symbol: '▲' },
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
          <span>{t(item.labelKey)}</span>
        </button>
      ))}
    </nav>
  )
}

export default BottomNav
