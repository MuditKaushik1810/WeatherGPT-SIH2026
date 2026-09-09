import farmerCropWatch from '../mocks/farmerCropWatch.json'

const stageItems = [
  { label: 'Germination', state: 'complete', symbol: '01' },
  { label: 'Vegetative', state: 'current', symbol: '02' },
  { label: 'Flowering', state: 'next', symbol: '03' },
  { label: 'Grain Filling', state: 'future', symbol: '04' },
  { label: 'Maturity', state: 'future', symbol: '05' },
]

const threatSymbols = {
  hail: 'H',
  disease: 'D',
  heat: 'S',
  rain: 'R',
}

function goTo(hash) {
  window.location.hash = hash
}

function CropWatch() {
  return (
    <main className="app-shell farmer-shell">
      <div className="farmer-page">
        <header className="farmer-header">
          <button
            className="farmer-menu-button"
            type="button"
            aria-label="Open menu"
            title="Menu"
            onClick={() => {}}
          >
            <span />
            <span />
            <span />
          </button>

          <div className="farmer-brand" aria-label="WeatherGPT">
            <span className="farmer-brand-mark" aria-hidden="true">W</span>
            <strong>WeatherGPT</strong>
          </div>

          <button
            className="farmer-mode-switch"
            type="button"
            onClick={() => goTo('#home')}
            aria-label="Switch to normal WeatherGPT mode"
          >
            <span aria-hidden="true">◆</span>
            Farmer Mode
            <span aria-hidden="true">⌄</span>
          </button>
        </header>

        <section className="farmer-location-card" aria-label="Farm location">
          <div className="farmer-landscape" aria-hidden="true">
            <span className="farmer-sun" />
            <span className="farmer-mountain mountain-one" />
            <span className="farmer-mountain mountain-two" />
            <span className="farmer-field field-back" />
            <span className="farmer-field field-front" />
          </div>
          <div className="farmer-location-label">
            <span aria-hidden="true">●</span>
            {farmerCropWatch.location}
          </div>
        </section>

        <section className="farmer-title-card">
          <div className="farmer-leaf-mark" aria-hidden="true">✦</div>
          <div>
            <h1>Crop Watch</h1>
            <p>Protect what you're growing</p>
            <span>Real-time insights on weather risks, crop health and personalised actions for your farm.</span>
          </div>
        </section>


        <section className="crop-details-card" aria-labelledby="crop-details-heading">
          <div className="farmer-section-heading">
            <span className="section-icon crop-icon" aria-hidden="true">✦</span>
            <h2 id="crop-details-heading">Your Crop Details</h2>
          </div>

          <div className="crop-detail-grid">
            <div>
              <span>Crop Type</span>
              <strong>{farmerCropWatch.crop}</strong>
            </div>
            <div>
              <span>Days After Sowing</span>
              <strong>{farmerCropWatch.days_after_sowing} days</strong>
            </div>
            <div>
              <span>Crop Stage</span>
              <strong>{farmerCropWatch.crop_stage} → {farmerCropWatch.next_stage}</strong>
            </div>
          </div>

          <div className="crop-stage-timeline" aria-label="Crop growth stage">
            {stageItems.map((stage, index) => (
              <div key={stage.label} className={`crop-stage ${stage.state}`}>
                <span className="crop-stage-node">{stage.symbol}</span>
                <span>{stage.label}</span>
                {index < stageItems.length - 1 && <i aria-hidden="true" />}
              </div>
            ))}
          </div>
        </section>

        <section className="weather-threats-card" aria-labelledby="threats-heading">
          <div className="farmer-section-heading">
            <span className="section-icon alert-icon" aria-hidden="true">!</span>
            <div>
              <h2 id="threats-heading">Weather Threats</h2>
              <p>Based on current conditions, forecast and crop stage</p>
            </div>
          </div>

          <div className="threat-list">
            {farmerCropWatch.threats.map((threat) => (
              <button key={threat.id} className="threat-row" type="button">
                <span className={`threat-icon ${threat.id}`} aria-hidden="true">{threatSymbols[threat.id]}</span>
                <span className="threat-copy">
                  <strong>{threat.label}</strong>
                  <small>{threat.detail}</small>
                </span>
                <span className={`threat-level ${threat.level.toLowerCase()}`}>{threat.level}</span>
                <span className="threat-arrow" aria-hidden="true">›</span>
              </button>
            ))}
          </div>
        </section>

        <section className="farmer-action-card" aria-labelledby="action-heading">
          <span className="action-icon" aria-hidden="true">!</span>
          <div>
            <h2 id="action-heading">Recommended Action</h2>
            <strong>{farmerCropWatch.recommended_action.title}</strong>
            <ul>
              {farmerCropWatch.recommended_action.items.map((item) => <li key={item}>{item}</li>)}
            </ul>
            <small>Based on demo weather + forecast + crop stage</small>
          </div>
          <span className="action-arrow" aria-hidden="true">›</span>
        </section>

        <section className="climate-context-card" aria-labelledby="climate-heading">
          <span className="climate-icon" aria-hidden="true">◎</span>
          <div>
            <h2 id="climate-heading">Climate Context</h2>
            <div className="climate-title-row">
              <strong>{farmerCropWatch.climate_context.title}</strong>
              <span className="threat-level moderate">{farmerCropWatch.climate_context.level}</span>
            </div>
            <p>{farmerCropWatch.climate_context.detail}</p>
          </div>
          <span className="action-arrow" aria-hidden="true">›</span>
        </section>

        <p className="farmer-demo-note">
          Demo data · This screen uses a frontend fixture and is not live farm advice.
        </p>

        <nav className="farmer-bottom-nav" aria-label="Farmer Mode navigation">
          <button
            type="button"
            disabled
            aria-label="Crop Planning, coming next"
          >
            <span aria-hidden="true">◇</span>
            <span>Crop Planning</span>
          </button>
          <button
            type="button"
            className="active"
            aria-current="page"
          >
            <span aria-hidden="true">◆</span>
            <span>Crop Watch</span>
          </button>
        </nav>
      </div>
    </main>
  )
}

export default CropWatch

