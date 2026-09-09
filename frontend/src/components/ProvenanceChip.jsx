// Provenance chip — shows which source produced the data and how specific it is
// (`data_tier`). Every screen reads the same two contract fields, `source` and
// `data_tier`, so this one small element is the app-wide "where did this come
// from" affordance that makes the grounding story visible to the user
// (Architecture doc, Section 2.1; contract fields in CLAUDE.md).
import { useI18n } from '../i18n'

const TIER_KEY = {
  exact: 'provenance.exact',
  regional_fallback: 'provenance.regional_fallback',
  historical_baseline: 'provenance.historical_baseline',
  source_unavailable: 'provenance.source_unavailable',
  unresolved_location: 'provenance.unresolved_location',
}

function ProvenanceChip({ source, dataTier }) {
  const { t } = useI18n()
  const tierLabel = TIER_KEY[dataTier] ? t(TIER_KEY[dataTier]) : (dataTier ?? t('provenance.unknown'))
  return (
    <span
      className={`provenance-chip provenance-${dataTier ?? 'unknown'}`}
      title={t('provenance.tierTitle', { tier: dataTier ?? 'unknown' })}
    >
      <span className="provenance-dot" aria-hidden="true" />
      <span className="provenance-text">
        {source ?? t('provenance.noSource')} · {tierLabel}
      </span>
    </span>
  )
}

export default ProvenanceChip
