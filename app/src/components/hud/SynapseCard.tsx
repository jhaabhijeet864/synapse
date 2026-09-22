import { SynapseCard as SynapseCardType } from '@/types'
import { DiffViewer, extractPatch } from './DiffViewer'

interface SynapseCardProps {
  card: SynapseCardType
  state: 'IDLE' | 'CAPTURING' | 'REASONING' | 'READY' | 'SUPPRESSED'
  onDismiss: () => void
  onApplyFix: (patch: string) => void
  onSave: () => void
}

export function SynapseCard({ card, state, onDismiss, onApplyFix, onSave }: SynapseCardProps) {
  const isLoading = state === 'CAPTURING' || state === 'REASONING'
  const patch = extractPatch(card.response)

  return (
    <div
      className={`synapse-card ${isLoading ? 'loading' : ''}`}
      role="dialog"
      aria-live="polite"
    >
      <header className="synapse-card__header">
        <div className="synapse-card__brand">
          <span className="synapse-logo">▌</span>
          <span>SYNAPSE</span>
        </div>
        <div className="synapse-card__controls">
          {patch && (
            <button className="btn-ghost btn-sm" onClick={() => onApplyFix(patch)}>
              Apply Fix
            </button>
          )}
          <button className="btn-ghost btn-sm" onClick={onSave}>Save</button>
          <button className="btn-ghost btn-sm" onClick={onDismiss}>×</button>
        </div>
      </header>

      <div className="synapse-card__meta">
        <span className="context-badge">
          ⬡ {card.active_app || 'Desktop'} · {Math.round(card.latency_ms)}ms · {card.model_used}
        </span>
        {card.memory_used && (
          <span className="memory-badge">◈ Memory: {card.active_app} context</span>
        )}
      </div>

      <div className="synapse-card__response">
        <DiffViewer text={card.response} />
      </div>

      {card.tavily && (
        <div className="synapse-card__tavily">
          <span className="tavily-label">Tavily Research</span>
          <a href={card.tavily.sources[0]?.url} target="_blank" rel="noopener" className="tavily-link">
            {card.tavily.sources[0]?.title}
          </a>
          <span className="tavily-saved">Saved to {card.tavily.saved_path}</span>
        </div>
      )}

      <footer className="synapse-card__action-bar">
        <span className="model-badge">{card.model_used} · {card.latency_ms}ms</span>
        <span className="usage-badge">
          ~${card.usage.estimated_spend_usd.toFixed(4)} / ${card.usage.budget_remaining_usd?.toFixed(2) || '50.00'} remaining
        </span>
      </footer>
    </div>
  )
}
