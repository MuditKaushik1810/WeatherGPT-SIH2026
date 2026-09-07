import { useMemo, useState } from 'react'
import BottomNav from '../components/BottomNav'
import disasterAlerts from '../mocks/disasterAlerts.json'
import disasterActiveAlert from '../mocks/disasterActiveAlert.json'
import rescueCenters from '../mocks/disasterRescueCenters.json'

const LOCATION = 'Noida, Uttar Pradesh'
const DEMO_NOW = new Date('2026-09-06T12:00:00')

function Icon({ name, size = 24 }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.9,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': 'true',
  }

  const paths = {
    warning: <><path d="M10.3 3.6 2.5 17.5a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" /><path d="M12 8v5" /><path d="M12 16.5h.01" /></>,
    shield: <><path d="M12 3 19 6v5.3c0 4.7-3 7.9-7 9.7-4-1.8-7-5-7-9.7V6l7-3Z" /><path d="m8.5 12 2.2 2.2 4.8-5" /></>,
    document: <><path d="M6 3.5h8l4 4v13H6z" /><path d="M14 3.5v4h4M9 12h6M9 16h6" /></>,
    rescue: <><path d="m3 10 9-7 9 7" /><path d="M5 9v11h14V9" /><path d="M9 20v-6h6v6" /></>,
    phone: <path d="M7.1 3.8 4.8 5.1c-.8.5-.9 1.6-.5 2.5 2.3 5.1 6.2 9 11.3 11.3.9.4 2 .3 2.5-.5l1.3-2.3c.4-.7.2-1.6-.5-2l-2.8-1.7c-.6-.4-1.4-.3-1.9.2l-1.1 1.1a15.4 15.4 0 0 1-3.8-3.8l1.1-1.1c.5-.5.6-1.3.2-1.9L8.9 4.3c-.4-.7-1.3-.9-1.8-.5Z" />,
    pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
    clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
    arrow: <path d="m9 6 6 6-6 6" />,
    home: <><path d="m3.5 10.5 8.5-7 8.5 7" /><path d="M5.5 9.5v10h13v-10M9.5 19.5v-5h5v5" /></>,
    travel: <><rect x="5" y="6" width="14" height="15" rx="2" /><path d="M9 6V4h6v2M9 11h6M9 15h6" /></>,
    bell: <><path d="M18 10a6 6 0 0 0-12 0c0 7-3 7-3 8h18c0-1-3-1-3-8" /><path d="M10 21h4" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  }

  return <svg {...common}>{paths[name]}</svg>
}

function formatValidUntil(value) {
  return new Date(value).toLocaleTimeString('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function severityLabel(severity) {
  return severity === 'high' ? 'High' : severity === 'medium' ? 'Moderate' : 'Low'
}

function hazardLabel(value) {
  return value.replaceAll('_', ' ')
}

function isActive(alert) {
  return new Date(alert.valid_until) > DEMO_NOW
}

function AlertUpdates({ alerts }) {
  return (
    <section className="disaster-updates" aria-labelledby="updates-heading">
      <h2 id="updates-heading">Weather &amp; Disaster Updates</h2>
      <div className="disaster-update-list">
        {alerts.map((alert) => (
          <article className="disaster-update-card" key={`${alert.region}-${alert.hazard_type}`}>
            <div>
              <h3>{hazardLabel(alert.hazard_type)}</h3>
              <p>{alert.region}</p>
              <span>{alert.source} · {severityLabel(alert.severity)}</span>
            </div>
            <button type="button" className="disaster-arrow" aria-label={`View ${alert.region} alert`}>
              <Icon name="arrow" size={23} />
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

function ActiveAlert({ alert, onDetails, onRescue, onNumbers, onSos }) {
  return (
    <>
      <section className="active-alert" aria-labelledby="active-alert-title">
        <div className="active-alert-banner">
          <span className="active-alert-icon"><Icon name="warning" size={30} /></span>
          <strong>Active Alert in Your Area</strong>
        </div>
        <div className="active-alert-body">
          <h2 id="active-alert-title">{hazardLabel(alert.hazard_type)} warning</h2>
          <div className="active-alert-meta">
            <span><Icon name="pin" size={21} /> {LOCATION}</span>
            <span><Icon name="clock" size={21} /> Valid until {formatValidUntil(alert.valid_until)}</span>
          </div>
          <p className="active-alert-advice"><Icon name="shield" size={22} /> Stay indoors and avoid exposed or waterlogged areas.</p>
          <div className="disaster-source-line">Official alert · {alert.source}</div>
        </div>
      </section>

      <div className="disaster-actions">
        <ActionCard icon="document" tone="red" title="View Alert Details" description="See the current government warning, affected area and safety guidance." onClick={onDetails} />
        <ActionCard icon="rescue" tone="green" title="Find Rescue Centers" description="Find nearby police, fire stations and government hospitals." onClick={onRescue} />
        <ActionCard icon="phone" tone="blue" title="Emergency Numbers" description="Important emergency contacts and national helplines." onClick={onNumbers} />
        <ActionCard icon="warning" tone="sos" title="SEND SOS" description="Share your location and emergency information." onClick={onSos} urgent />
      </div>
    </>
  )
}

function ActionCard({ icon, tone, title, description, onClick, urgent = false }) {
  return (
    <button type="button" className={`disaster-action ${tone} ${urgent ? 'urgent' : ''}`} onClick={onClick}>
      <span className="disaster-action-icon"><Icon name={icon} size={30} /></span>
      <span className="disaster-action-copy">
        <strong>{title}</strong>
        <span>{description}</span>
      </span>
      <Icon name="arrow" size={25} />
    </button>
  )
}

function RescuePanel({ onClose }) {
  return (
    <section className="disaster-panel" aria-labelledby="rescue-heading">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Nearby emergency help</span>
          <h2 id="rescue-heading">Find nearby facilities</h2>
        </div>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Close rescue centers">×</button>
      </div>
      <p className="panel-note">These are emergency-support facilities, not designated relief camps. Verify availability before relying on them.</p>
      <div className="facility-list">
        {rescueCenters.facilities.map((facility) => (
          <article className="facility-card" key={facility.name}>
            <div className={`facility-icon ${facility.type}`}>
              <Icon name={facility.type === 'police_station' ? 'shield' : facility.type === 'fire_station' ? 'warning' : 'rescue'} size={25} />
            </div>
            <div className="facility-copy">
              <strong>{facility.name}</strong>
              <span>{facility.address}</span>
              <small>{facility.distance_km} km · {facility.source} · {facility.data_tier}</small>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function EmergencyPanel({ onClose }) {
  return (
    <section className="disaster-panel" aria-labelledby="numbers-heading">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Verified helpline block</span>
          <h2 id="numbers-heading">Emergency numbers</h2>
        </div>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Close emergency numbers">×</button>
      </div>
      <div className="helpline-list">
        <a href="tel:1078" className="helpline"><strong>1078</strong><span>NDMA National Helpline</span></a>
        <a href="tel:112" className="helpline"><strong>112</strong><span>India General Emergency</span></a>
        <div className="helpline muted"><strong>Local</strong><span>District control-room number must be looked up locally — it varies by location.</span></div>
      </div>
    </section>
  )
}

function SosPanel({ onClose }) {
  const [type, setType] = useState('Trapped / stranded')
  const [message, setMessage] = useState('')
  const [saved, setSaved] = useState(false)

  const submit = (event) => {
    event.preventDefault()
    setSaved(true)
  }

  return (
    <section className="disaster-panel sos-panel" aria-labelledby="sos-heading">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Emergency request</span>
          <h2 id="sos-heading">Send SOS</h2>
        </div>
        <button type="button" className="panel-close" onClick={onClose} aria-label="Close SOS">×</button>
      </div>
      <p className="panel-note">Demo only: this mock does not send a real emergency request. The future flow attaches GPS, emergency type and an optional message.</p>
      {saved ? (
        <div className="sos-saved"><Icon name="shield" size={28} /><strong>SOS saved — waiting for network</strong><span>No emergency service was contacted by this frontend mock.</span></div>
      ) : (
        <form onSubmit={submit} className="sos-form">
          <label>Emergency type<select value={type} onChange={(event) => setType(event.target.value)}>{['Trapped / stranded', 'Medical emergency', 'Flooding', 'Fire', 'Building damage', 'Other'].map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Optional message<textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Tell responders what happened..." rows="3" /></label>
          <button className="sos-submit" type="submit">Save SOS for delivery</button>
        </form>
      )}
    </section>
  )
}

function Disaster() {
  const [panel, setPanel] = useState(null)
  const locationAlerts = useMemo(
    () => disasterAlerts.alerts.filter((alert) => alert.region.toLowerCase().includes('delhi') || alert.region.toLowerCase().includes('noida')),
    [],
  )
  const demoActiveAlert = new URLSearchParams(window.location.hash.split('?')[1] || '').get('state') === 'active'
    ? disasterActiveAlert.alerts[0]
    : null
  const activeAlert = demoActiveAlert ?? locationAlerts.find(isActive)

  return (
    <main className="app-shell disaster-shell">
      <div className="disaster-page">
        <header className="disaster-header">
          <button className="disaster-icon-button" type="button" aria-label="Open menu"><Icon name="menu" size={29} /></button>
          <h1>Disaster</h1>
          <button className="disaster-icon-button" type="button" aria-label="Notifications"><Icon name="bell" size={27} /></button>
        </header>

        <div className="disaster-location">
          <Icon name="pin" size={22} />
          <span>{LOCATION}</span>
          <span className="location-chevron">⌄</span>
        </div>

        <section className="disaster-content">
          {activeAlert ? (
            <ActiveAlert
              alert={activeAlert}
              onDetails={() => setPanel('details')}
              onRescue={() => setPanel('rescue')}
              onNumbers={() => setPanel('numbers')}
              onSos={() => setPanel('sos')}
            />
          ) : (
            <>
              <section className="safe-status" aria-label="No active disaster warning">
                <div className="safe-icon"><Icon name="shield" size={45} /></div>
                <div>
                  <h2>No active disaster warning</h2>
                  <p>Your area is currently not under an active government disaster warning.</p>
                  <span className="disaster-source-line">Checked against available official alert data.</span>
                </div>
              </section>
              <AlertUpdates alerts={disasterAlerts.alerts} />
            </>
          )}

          {panel === 'details' && (
            <section className="disaster-panel" aria-labelledby="details-heading">
              <div className="panel-heading"><div><span className="eyebrow">Official alert</span><h2 id="details-heading">Alert details</h2></div><button type="button" className="panel-close" onClick={() => setPanel(null)} aria-label="Close alert details">×</button></div>
              <p className="panel-note">The active warning shown here is sourced from the disaster alert mock and is ready to be replaced one-for-one by the future <code>GET /disaster/alerts</code> response.</p>
              <div className="detail-grid"><span>Hazard<strong>{hazardLabel(activeAlert.hazard_type)}</strong></span><span>Severity<strong>{severityLabel(activeAlert.severity)}</strong></span><span>Source<strong>{activeAlert.source}</strong></span><span>Valid until<strong>{formatValidUntil(activeAlert.valid_until)}</strong></span></div>
            </section>
          )}
          {panel === 'rescue' && <RescuePanel onClose={() => setPanel(null)} />}
          {panel === 'numbers' && <EmergencyPanel onClose={() => setPanel(null)} />}
          {panel === 'sos' && <SosPanel onClose={() => setPanel(null)} />}
        </section>

        <BottomNav active="disaster" />
      </div>
    </main>
  )
}

export default Disaster
