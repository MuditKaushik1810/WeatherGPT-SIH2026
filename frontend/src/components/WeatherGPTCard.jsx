import { useI18n } from '../i18n'

function WeatherGPTCard({ onOpenChat }) {
  const { t } = useI18n()
  return (
    <section className="gpt-card">
      <div className="gpt-mark" aria-hidden="true">✦</div>
      <div className="gpt-copy">
        <span className="eyebrow">{t('gpt.eyebrow')}</span>
        <h2>{t('gpt.title')}</h2>
        <p>{t('gpt.body')}</p>
      </div>
      <button className="ask-button" type="button" onClick={onOpenChat}>
        {t('gpt.cta')}
      </button>
    </section>
  )
}

export default WeatherGPTCard
