import farmerCropPlanning from '../mocks/farmerCropPlanning.json'

function goTo(hash) {
  window.location.hash = hash
}

export default function CropPlanning() {
  return (
    <main className="app-shell farmer-shell">
      <section className="farmer-page">
        <header className="farmer-header">
          <button
            className="farmer-menu-button"
            type="button"
            aria-label="Open menu"
          >
            ☰
          </button>

          <div className="farmer-brand">
            <span className="farmer-brand-mark">W</span>
            <span>WeatherGPT</span>
          </div>

          <button
            className="farmer-mode-switch"
            type="button"
            onClick={() => goTo('#home')}
          >
            Farmer Mode
          </button>
        </header>

        <section className="farmer-location-card">
          <div className="farmer-landscape" aria-hidden="true">
            <div className="farmer-sun" />
            <div className="farmer-hill farmer-hill-back" />
            <div className="farmer-hill farmer-hill-front" />
            <div className="farmer-field" />
          </div>

          <div className="farmer-location-content">
            <span>Current location</span>
            <strong>{farmerCropPlanning.location}</strong>
          </div>
        </section>

        <section className="farmer-title-card">
          <div className="farmer-leaf-mark" aria-hidden="true">
            🌱
          </div>

          <div>
            <h1>Crop Planning</h1>
            <p>Choose what to grow</p>
          </div>
        </section>

        <section className="crop-planning-intro">
          <p>
            Recommendations based on your location, season and climate
            suitability.
          </p>
        </section>

        <section className="crop-recommendation-card">
          <div className="farmer-section-heading">
            <span className="section-icon" aria-hidden="true">
              ✦
            </span>

            <div>
              <h2>Recommended crops</h2>
              <p>Best-fit options for this season</p>
            </div>
          </div>

          <div className="crop-recommendation-list">
            {farmerCropPlanning.recommendations.map((crop, index) => (
              <article
                className={`crop-recommendation-item ${
                  index === 0 ? 'featured' : ''
                }`}
                key={crop.crop}
              >
                <div className="crop-recommendation-main">
                  <h3>{crop.crop}</h3>
                  <span className="crop-suitability">
                    {crop.suitability} fit
                  </span>
                </div>

                <p>{crop.reason}</p>

                <div className="crop-harvest-window">
                  <span>Approx. harvest</span>
                  <strong>{crop.harvest_window}</strong>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="climate-context-card">
          <div className="farmer-section-heading">
            <span className="climate-icon" aria-hidden="true">
              ☁
            </span>

            <div>
              <h2>Climate fit</h2>
              <p>{farmerCropPlanning.season} season</p>
            </div>
          </div>

          <p>{farmerCropPlanning.climate_context.summary}</p>

          <div className="historical-climate-note">
            <strong>Historical climate</strong>
            <span>{farmerCropPlanning.climate_context.historical_note}</span>
          </div>
        </section>

        <p className="farmer-demo-note">
          Demo data · This screen uses a frontend fixture and is not live
          farming advice.
        </p>

        <nav className="farmer-bottom-nav" aria-label="Farmer Mode navigation">
          <button
            className="active"
            type="button"
            aria-current="page"
          >
            <span aria-hidden="true">🌱</span>
            <span>Crop Planning</span>
          </button>

          <button
            type="button"
            onClick={() => goTo('#farmer/watch')}
          >
            <span aria-hidden="true">◉</span>
            <span>Crop Watch</span>
          </button>
        </nav>
      </section>
    </main>
  )
}
