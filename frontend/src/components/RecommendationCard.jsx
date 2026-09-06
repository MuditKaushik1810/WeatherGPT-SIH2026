function RecommendationCard({ recommendation }) {
  return (
    <section className="recommendation-card">
      <div className="recommendation-icon" aria-hidden="true">✦</div>
      <div>
        <span className="eyebrow">Today&apos;s Recommendation</span>
        <h2>{recommendation.title}</h2>
        <p>{recommendation.message}</p>
      </div>
    </section>
  )
}

export default RecommendationCard
