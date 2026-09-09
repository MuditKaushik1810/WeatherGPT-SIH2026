import { useI18n } from '../i18n'

function RecommendationCard({ recommendation }) {
  const { t } = useI18n()
  return (
    <section className="recommendation-card">
      <div className="recommendation-icon" aria-hidden="true">✦</div>
      <div>
        <span className="eyebrow">{t('rec.eyebrow')}</span>
        <h2>{recommendation.title}</h2>
        <p>{recommendation.message}</p>
      </div>
    </section>
  )
}

export default RecommendationCard
