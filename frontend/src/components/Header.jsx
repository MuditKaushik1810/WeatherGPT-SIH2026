function Header({ location }) {
  return (
    <header className="header">
      <button
        className="icon-button"
        type="button"
        aria-label="Open menu"
        title="Menu"
        onClick={() => {}}
      >
        <span className="hamburger-line" />
        <span className="hamburger-line" />
        <span className="hamburger-line" />
      </button>

      <div className="location-block">
        <div className="location-row">
          <span className="location-pin" aria-hidden="true">⌖</span>
          <span className="location-name">{location}</span>
        </div>
        <span className="updated-text">Updated just now</span>
      </div>

      <button
        className="profile-button"
        type="button"
        aria-label="Account"
        title="Account"
        onClick={() => {}}
      >
        <span className="profile-icon" aria-hidden="true">●</span>
      </button>
    </header>
  )
}

export default Header
