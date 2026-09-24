import { useState } from 'react'
import {
  Activity,
  Cpu,
  Database,
  ExternalLink,
  Layers,
  Search,
  Terminal,
  Shield,
  Zap,
  Check,
  Copy,
  ArrowRight
} from 'lucide-react'
import { NeuronSphere } from './NeuronSphere'
import { StarfieldBackground } from './StarfieldBackground'

interface LandingPageProps {
  onEnterApp: () => void
}

export function LandingPage({ onEnterApp }: LandingPageProps) {
  const [copiedInstall, setCopiedInstall] = useState(false)

  const copyInstall = () => {
    navigator.clipboard.writeText('git clone https://github.com/YOUR_USERNAME/synapse.git && cd synapse && scripts\\setup_env.bat')
    setCopiedInstall(true)
    setTimeout(() => setCopiedInstall(false), 2000)
  }

  return (
    <div className="nvidia-landing">
      <StarfieldBackground />

      {/* 1. Global Navigation Bar */}
      <nav className="nv-nav">
        <div className="nv-nav__inner">
          <div className="nv-nav__brand">
            <span className="nv-brand__badge">NVIDIA</span>
            <span className="nv-brand__divider">|</span>
            <span className="nv-brand__name">SYNAPSE</span>
          </div>

          <div className="nv-nav__links">
            <a href="#how-it-works">Architecture</a>
            <a href="#features">Capabilities</a>
            <a href="#models">Models</a>
            <a href="#specs">Specifications</a>
            <a href="#quickstart">Quickstart</a>
          </div>

          <div className="nv-nav__actions">
            <button className="nv-btn-cta" onClick={onEnterApp}>
              Launch Desktop HUD
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* 2. Hero Section */}
      <section className="nv-hero">
        <div className="nv-container nv-hero__grid">
          <div className="nv-hero__content">
            <div className="nv-category-pill">
              <span className="nv-pulse-dot"></span>
              AMBIENT OS COGNITION LAYER
            </div>
            <h1 className="nv-hero__headline">
              Ambient intelligence for Windows developers.
            </h1>
            <p className="nv-hero__subhead">
              Synapse runs as a background Windows daemon, extracting active window telemetry via OCR and Win32 event hooks, routing problems to NVIDIA Nemotron models, and recalling episodic context from vector memory.
            </p>

            <div className="nv-hero__actions">
              <button className="nv-btn-primary" onClick={onEnterApp}>
                Launch Desktop App
                <ArrowRight size={16} />
              </button>
              <a href="#quickstart" className="nv-btn-secondary">
                View Terminal Setup
              </a>
            </div>

            <div className="nv-hero__stats">
              <div className="nv-stat">
                <span className="nv-stat__num">&lt; 150ms</span>
                <span className="nv-stat__label">Triage latency (Nemotron Nano)</span>
              </div>
              <div className="nv-stat__divider"></div>
              <div className="nv-stat">
                <span className="nv-stat__num">100%</span>
                <span className="nv-stat__label">Local PII sanitization</span>
              </div>
              <div className="nv-stat__divider"></div>
              <div className="nv-stat">
                <span className="nv-stat__num">PGVector</span>
                <span className="nv-stat__label">Episodic memory store</span>
              </div>
            </div>
          </div>

          <div className="nv-hero__visual">
            <div className="nv-sphere-wrapper">
              <NeuronSphere />
            </div>

            {/* Embedded Realistic Hardware HUD Card preview */}
            <div className="nv-mock-hud">
              <div className="nv-mock-hud__header">
                <div className="nv-mock-hud__title">
                  <span className="nv-green-block">▌</span>
                  <span>SYNAPSE ACTIVE INFERENCE</span>
                </div>
                <div className="nv-mock-hud__tag">Ctrl+Shift+Space</div>
              </div>
              <div className="nv-mock-hud__body">
                <div className="nv-mock-hud__meta">
                  <span>Target: VS Code · Process: python.exe</span>
                  <span className="nv-text-green">Model: Nemotron 3 Ultra</span>
                </div>
                <div className="nv-mock-hud__code">
                  <span className="nv-diff-del">- if user.token.valid:</span>
                  <span className="nv-diff-add">+ if user and user.token and user.token.valid:</span>
                </div>
                <div className="nv-mock-hud__footer">
                  <span>Latency: 142ms</span>
                  <span>Vector Cache: Hit</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. How It Works: Pipeline */}
      <section id="how-it-works" className="nv-section nv-section--bordered">
        <div className="nv-container">
          <div className="nv-section__header">
            <span className="nv-eyebrow">SYSTEM PIPELINE</span>
            <h2 className="nv-section__title">Telemetry to inference in milliseconds</h2>
            <p className="nv-section__desc">
              Four synchronous and asynchronous stages bridge Windows windowing hooks to cloud-accelerated Nemotron neural weights.
            </p>
          </div>

          <div className="nv-pipeline-grid">
            <div className="nv-pipeline-card">
              <div className="nv-pipeline-card__step">01</div>
              <div className="nv-pipeline-card__icon"><Terminal size={20} /></div>
              <h3 className="nv-pipeline-card__title">Win32 Context Hook</h3>
              <p className="nv-pipeline-card__text">
                Monitors active processes, clipboard changes, and filesystem updates. Captures the bounding coordinates of errors and active code.
              </p>
            </div>

            <div className="nv-pipeline-card">
              <div className="nv-pipeline-card__step">02</div>
              <div className="nv-pipeline-card__icon"><Shield size={20} /></div>
              <h3 className="nv-pipeline-card__title">Local PII Redaction</h3>
              <p className="nv-pipeline-card__text">
                Regular expressions and entropy scanners sanitize API keys, JWTs, passwords, and private tokens on-device before any transmission.
              </p>
            </div>

            <div className="nv-pipeline-card">
              <div className="nv-pipeline-card__step">03</div>
              <div className="nv-pipeline-card__icon"><Zap size={20} /></div>
              <h3 className="nv-pipeline-card__title">Hybrid Neural Routing</h3>
              <p className="nv-pipeline-card__text">
                Nemotron Nano triages intent in ~150ms. Deterministic logic resolves trivial cases locally; deep queries route to Nemotron 3 Ultra.
              </p>
            </div>

            <div className="nv-pipeline-card">
              <div className="nv-pipeline-card__step">04</div>
              <div className="nv-pipeline-card__icon"><Database size={20} /></div>
              <h3 className="nv-pipeline-card__title">Vector Memory Recall</h3>
              <p className="nv-pipeline-card__text">
                Queries PostgreSQL with PGVector using Nebius text embeddings. Automatically retrieves previous solutions and user conventions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Core Features Section */}
      <section id="features" className="nv-section">
        <div className="nv-container">
          <div className="nv-section__header">
            <span className="nv-eyebrow">ENGINEERING CAPABILITIES</span>
            <h2 className="nv-section__title">Precision telemetry for cognitive tasks</h2>
          </div>

          <div className="nv-grid-2">
            <div className="nv-feature-block">
              <div className="nv-feature-block__icon"><Activity size={24} /></div>
              <h3 className="nv-feature-block__title">Non-intrusive ambient tracking</h3>
              <p className="nv-feature-block__text">
                Eliminates repetitive prompt construction. Synapse ingests compiler errors, traceback logs, and UI states directly from your displays without context switching.
              </p>
            </div>

            <div className="nv-feature-block">
              <div className="nv-feature-block__icon"><Cpu size={24} /></div>
              <h3 className="nv-feature-block__title">NVIDIA Nemotron optimization</h3>
              <p className="nv-feature-block__text">
                Leverages NVIDIA Nemotron models hosted on Nebius Token Factory. High-concurrency serverless execution provides high-throughput tokens with sub-second time-to-first-token.
              </p>
            </div>

            <div className="nv-feature-block">
              <div className="nv-feature-block__icon"><Search size={24} /></div>
              <h3 className="nv-feature-block__title">Autonomous Tavily synthesis</h3>
              <p className="nv-feature-block__text">
                When context requires fresh library specifications or upstream issue tracking, the daemon initiates Tavily web searches and writes structured documentation directly to workspace scratchpads.
              </p>
            </div>

            <div className="nv-feature-block">
              <div className="nv-feature-block__icon"><Layers size={24} /></div>
              <h3 className="nv-feature-block__title">Tauri v2 Native HUD</h3>
              <p className="nv-feature-block__text">
                A minimal desktop window operating via Rust bindings. Renders over native IDEs with minimal memory overhead, zero chromium bloat, and standard Windows titlebar controls.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Models Table */}
      <section id="models" className="nv-section nv-section--bordered">
        <div className="nv-container">
          <div className="nv-section__header">
            <span className="nv-eyebrow">MODEL ARCHITECTURE</span>
            <h2 className="nv-section__title">Specialized inference tiers</h2>
          </div>

          <div className="nv-table-container">
            <table className="nv-table">
              <thead>
                <tr>
                  <th>Model Tier</th>
                  <th>Primary Function</th>
                  <th>Execution Environment</th>
                  <th>Target Latency</th>
                  <th>Context Window</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>NVIDIA Nemotron Nano</strong></td>
                  <td>Fast classification, intent detection, query routing</td>
                  <td>Nebius Serverless Endpoint</td>
                  <td className="nv-text-green">~150 ms</td>
                  <td>8,192 tokens</td>
                </tr>
                <tr>
                  <td><strong>NVIDIA Nemotron 3 Ultra</strong></td>
                  <td>Deep reasoning, unified diff synthesis, code fix generation</td>
                  <td>Nebius Serverless Endpoint</td>
                  <td className="nv-text-green">~1.2 s</td>
                  <td>32,768 tokens</td>
                </tr>
                <tr>
                  <td><strong>Nebius Embeddings</strong></td>
                  <td>Contextual vector embeddings for episodic memory</td>
                  <td>Nebius Token Factory</td>
                  <td className="nv-text-green">&lt; 80 ms</td>
                  <td>4,096 dimensions</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* 6. Hardware Specifications */}
      <section id="specs" className="nv-section">
        <div className="nv-container">
          <div className="nv-section__header">
            <span className="nv-eyebrow">SYSTEM REQUIREMENTS</span>
            <h2 className="nv-section__title">Deployment Specifications</h2>
          </div>

          <div className="nv-specs-grid">
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Operating System</div>
              <div className="nv-spec-card__value">Windows 10 / 11 (64-bit)</div>
            </div>
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Local Runtime</div>
              <div className="nv-spec-card__value">Python 3.11+, Rust 1.75+, Node.js 18+</div>
            </div>
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Desktop GUI</div>
              <div className="nv-spec-card__value">Tauri v2 + React 18 (Native Windows Subsystem)</div>
            </div>
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Database Engine</div>
              <div className="nv-spec-card__value">PostgreSQL 16 with PGVector extension</div>
            </div>
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Interprocess Communication</div>
              <div className="nv-spec-card__value">FastAPI Async WebSocket on 127.0.0.1:8420</div>
            </div>
            <div className="nv-spec-card">
              <div className="nv-spec-card__label">Software License</div>
              <div className="nv-spec-card__value">Open Source — MIT License</div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Quickstart Terminal Section */}
      <section id="quickstart" className="nv-section nv-section--dark">
        <div className="nv-container">
          <div className="nv-section__header">
            <span className="nv-eyebrow">DEPLOYMENT</span>
            <h2 className="nv-section__title">Get Started in Windows Terminal</h2>
            <p className="nv-section__desc">
              Clone the repository and run the automated Windows environment configuration script.
            </p>
          </div>

          <div className="nv-code-block">
            <div className="nv-code-block__header">
              <span>POWERSHELL</span>
              <button className="nv-copy-btn" onClick={copyInstall}>
                {copiedInstall ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedInstall ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <pre className="nv-code-block__content">
<code>git clone https://github.com/YOUR_USERNAME/synapse.git
cd synapse
scripts\setup_env.bat
python -m core.doctor
python core/server.py</code>
            </pre>
          </div>
        </div>
      </section>

      {/* 8. Footer */}
      <footer className="nv-footer">
        <div className="nv-container nv-footer__inner">
          <div className="nv-footer__left">
            <div className="nv-footer__brand">
              <span className="nv-green-block">▌</span>
              <strong>SYNAPSE</strong>
            </div>
            <p className="nv-footer__copy">
              Built for the Nebius × NVIDIA Global AI Hackathon. Released under the MIT License.
            </p>
          </div>

          <div className="nv-footer__links">
            <a href="https://github.com/YOUR_USERNAME/synapse" target="_blank" rel="noreferrer">
              GitHub Repository
              <ExternalLink size={12} />
            </a>
            <a href="https://nebius.com" target="_blank" rel="noreferrer">
              Nebius Token Factory
              <ExternalLink size={12} />
            </a>
            <a href="https://build.nvidia.com" target="_blank" rel="noreferrer">
              NVIDIA NIM & Nemotron
              <ExternalLink size={12} />
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
