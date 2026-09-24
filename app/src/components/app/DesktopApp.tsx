import { useState } from 'react'
import {
  Terminal,
  Activity,
  ArrowRight,
  Layers,
  Play
} from 'lucide-react'
import { WindowTitlebar } from '@/components/window/WindowTitlebar'
import { SynapseCard } from '@/components/hud/SynapseCard'
import { DiffViewer } from '@/components/hud/DiffViewer'
import {
  useDaemonSocket,
  SynapseState,
  SynapseCard as SynapseCardType
} from '@/hooks/useDaemonSocket'

interface DesktopAppProps {
  onBackToLanding: () => void
}

export function DesktopApp({ onBackToLanding }: DesktopAppProps) {
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

  const handleInvoke = () => {
    if (query.trim()) {
      invoke(query.trim())
    }
  }

  // Pre-loaded sample trigger for quick testing
  const handleTestTrigger = () => {
    setActiveCard({
      trigger: "TypeError: Cannot read properties of undefined (reading 'token')",
      response: `The error indicates that the \`user\` object or \`user.token\` is undefined prior to evaluating \`.valid\`.

\`\`\`diff
- if (user.token.valid) {
+ if (user && user.token && user.token.valid) {
    executeAuthentication();
  }
\`\`\``,
      model_used: "ultra",
      latency_ms: 142,
      active_app: "VS Code (python.exe)",
      memory_used: true,
      tavily: null,
      usage: {
        total_tokens: 420,
        nano_calls: 1,
        ultra_calls: 1,
        estimated_spend_usd: 0.0012,
        budget_remaining_usd: 48.95
      }
    })
  }

  return (
    <div className="nv-desktop-app">
      {/* 1. Standard Windows Window Titlebar */}
      <WindowTitlebar
        title="SYNAPSE"
        subtitle="Desktop HUD & Inference Runtime"
        state={status === 'connected' ? daemonState : 'OFFLINE'}
        onClose={onBackToLanding}
      />

      {/* 2. Main Desktop App Workspace */}
      <div className="nv-desktop-app__body">
        {/* App Sidebar / Controls */}
        <aside className="nv-desktop-sidebar">
          <div className="nv-sidebar__section">
            <span className="nv-sidebar__label">DAEMON STATUS</span>
            <div className="nv-status-card" data-status={status}>
              <div className="nv-status-card__header">
                <span className="nv-status-card__indicator"></span>
                <strong>{status === 'connected' ? 'DAEMON ONLINE' : 'DAEMON OFFLINE'}</strong>
              </div>
              <p className="nv-status-card__info">
                {status === 'connected'
                  ? 'FastAPI WebSocket listening on port 8420.'
                  : 'Run "python core/server.py" to activate live telemetry.'}
              </p>
            </div>
          </div>

          <div className="nv-sidebar__section">
            <span className="nv-sidebar__label">NAVIGATION</span>
            <button className="nv-sidebar-btn nv-sidebar-btn--active">
              <Layers size={15} />
              <span>Active Inference</span>
            </button>
            <button className="nv-sidebar-btn" onClick={onBackToLanding}>
              <ArrowRight size={15} />
              <span>Product Page</span>
            </button>
          </div>

          <div className="nv-sidebar__section">
            <span className="nv-sidebar__label">QUICK TEST SIMULATION</span>
            <p className="nv-sidebar__help">
              Simulate an ambient Win32 OCR capture without launching external processes:
            </p>
            <button className="nv-btn-outline" onClick={handleTestTrigger}>
              <Play size={13} />
              <span>Simulate OCR Error</span>
            </button>
          </div>
        </aside>

        {/* Primary Viewport Area */}
        <main className="nv-desktop-main">
          <div className="nv-desktop-main__header">
            <div>
              <h2 className="nv-desktop-main__title">Ambient Workspace Monitor</h2>
              <p className="nv-desktop-main__subtitle">
                Monitoring active display buffer, clipboard stream, and terminal logs.
              </p>
            </div>
            <div className="nv-active-telemetry-badge">
              <Activity size={13} className="nv-pulse-icon" />
              <span>WIN32 HOOK: ACTIVE</span>
            </div>
          </div>

          {/* Interactive Manual Query Bar */}
          <div className="nv-desktop-query-box">
            <span className="nv-query-icon"><Terminal size={16} /></span>
            <input
              className="nv-query-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleInvoke()}
              placeholder="Ask Nemotron or manually feed terminal context... (Press Enter)"
            />
            <button
              className="nv-btn-primary nv-query-btn"
              onClick={handleInvoke}
            >
              Inference
            </button>
          </div>

          {/* Ambient Overlay HUD Simulation or Active Result */}
          <div className="nv-desktop-feed">
            {activeCard ? (
              <div className="nv-feed-card-wrapper">
                <span className="nv-feed-label">LAST GENERATED SYNAPSE CARD</span>
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
              </div>
            ) : streaming ? (
              <div className="synapse-card loading" role="dialog" aria-live="polite">
                <header className="synapse-card__header">
                  <div className="synapse-card__brand">
                    <span className="synapse-logo">▌</span>
                    <span>STREAMING REASONING</span>
                  </div>
                </header>
                <div className="synapse-card__response">
                  <DiffViewer text={streaming} />
                </div>
              </div>
            ) : (
              <div className="nv-empty-feed">
                <div className="nv-empty-feed__icon"><Activity size={32} /></div>
                <h3>Awaiting Workspace Telemetry</h3>
                <p>
                  Copy an error trace, trigger a compiler fault in your IDE, or click <strong>"Simulate OCR Error"</strong> in the sidebar to review active inference cards.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
