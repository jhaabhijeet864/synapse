import { useState } from 'react'
import { NeuronSphere } from '@/components/landing/NeuronSphere'
import { StarfieldBackground } from '@/components/landing/StarfieldBackground'
import { HeroText } from '@/components/landing/HeroText'
import { FeatureCards } from '@/components/landing/FeatureCards'
import { SynapseCard } from '@/components/hud/SynapseCard'
import { DiffViewer } from '@/components/hud/DiffViewer'
import { useDaemonSocket, SynapseState, SynapseCard as SynapseCardType } from '@/hooks/useDaemonSocket'

function App() {
  const [isLanding, setIsLanding] = useState(true)
  const [activeCard, setActiveCard] = useState<SynapseCardType | null>(null)
  const [daemonState, setDaemonState] = useState<SynapseState>('IDLE')
  const [query, setQuery] = useState('')

  const { status, streaming, invoke, dismiss, applyFix, storeMemory } = useDaemonSocket({
    onCard: (card) => {
      setActiveCard(card)
    },
    onStateChange: (state) => {
      setDaemonState(state)
    },
  })

  if (isLanding) {
    return (
      <LandingPage onEnterApp={() => setIsLanding(false)} />
    )
  }

  const handleInvoke = () => {
    if (query.trim()) invoke(query.trim())
  }

  return (
    <div className="app">
      {activeCard && (
        <SynapseCard
          card={activeCard}
          state={daemonState}
          onDismiss={() => {
            dismiss()
            setActiveCard(null)
          }}
          onApplyFix={(patch) => applyFix(patch)}
          onSave={() => {
            if (!activeCard) return
            storeMemory({
              app_context: activeCard.active_app || 'unknown',
              problem: activeCard.trigger,
              resolution: activeCard.response.slice(0, 2000),
            })
          }}
        />
      )}
      <div className="invoke-bar">
        <input
          className="invoke-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleInvoke()}
          placeholder={status === 'connected' ? 'Ask Synapse… (Ctrl+Shift+Space)' : 'Connecting to daemon…'}
          disabled={status !== 'connected'}
        />
        <button className="btn-primary btn-sm" onClick={handleInvoke} disabled={status !== 'connected'}>
          Ask
        </button>
      </div>
      {!activeCard && streaming && (
        <div className="synapse-card loading" role="dialog" aria-live="polite">
          <header className="synapse-card__header">
            <div className="synapse-card__brand">
              <span className="synapse-logo">▌</span>
              <span>SYNAPSE</span>
            </div>
          </header>
          <div className="synapse-card__response">
            <DiffViewer text={streaming} />
          </div>
        </div>
      )}
      <StatusIndicator state={daemonState} connected={status === 'connected'} />
    </div>
  )
}

function LandingPage({ onEnterApp }: { onEnterApp: () => void }) {
  return (
    <div className="landing-page">
      <StarfieldBackground />
      <div className="landing-content">
        <div className="hero-container">
          <div className="hero-left">
            <HeroText />
            <button className="cta-button" onClick={onEnterApp}>
              Launch Synapse
            </button>
          </div>
          <div className="hero-right" style={{ position: 'relative', width: '100%', minHeight: '500px' }}>
            <NeuronSphere />
          </div>
        </div>
        <FeatureCards />
      </div>
    </div>
  )
}

function StatusIndicator({ state, connected }: { state: SynapseState; connected: boolean }) {
  if (connected && state === 'IDLE') return null

  return (
    <div className="status-indicator" data-state={connected ? state : 'OFFLINE'}>
      <span className="status-dot" />
      <span>{connected ? state : 'OFFLINE — LOCAL MODE'}</span>
      {connected && <span className="pulse-ring" />}
    </div>
  )
}

export default App
