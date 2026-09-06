// Provenance chip — shows which source produced the data and how specific it is
// (`data_tier`). Every screen reads the same two contract fields, `source` and
// `data_tier`, so this one small element is the app-wide "where did this come
// from" affordance that makes the grounding story visible to the user
// (Architecture doc, Section 2.1; contract fields in CLAUDE.md).

const TIER_LABEL = {
  exact: 'Exact',
  regional_fallback: 'Regional estimate',
  historical_baseline: 'Historical baseline',
  source_unavailable: 'Source unavailable',
  unresolved_location: 'Location unresolved',
}

function ProvenanceChip({ source, dataTier }) {
  const tierLabel = TIER_LABEL[dataTier] ?? dataTier ?? 'Unknown'
  return (
    <span
      className={`provenance-chip provenance-${dataTier ?? 'unknown'}`}
      title={`Data tier: ${dataTier ?? 'unknown'}`}
    >
      <span className="provenance-dot" aria-hidden="true" />
      <span className="provenance-text">
        {source ?? 'No source'} · {tierLabel}
      </span>
    </span>
  )
}

export default ProvenanceChip
