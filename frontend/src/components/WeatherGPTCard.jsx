function WeatherGPTCard({ onOpenChat }) {
  return (
    <section className="gpt-card">
      <div className="gpt-mark" aria-hidden="true">✦</div>
      <div className="gpt-copy">
        <span className="eyebrow">WeatherGPT</span>
        <h2>Ask about your weather</h2>
        <p>Get a simple answer about today&apos;s weather, rain, travel, or what to do next.</p>
      </div>
      <button className="ask-button" type="button" onClick={onOpenChat}>
        Ask WeatherGPT
      </button>
    </section>
  )
}

export default WeatherGPTCard
