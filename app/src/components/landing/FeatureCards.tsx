const features = [
  {
    icon: '⬡',
    title: 'Screen-Aware Context',
    desc: 'OCR reads your active window — errors, code, unselectable text — and feeds it to Nemotron automatically.',
  },
  {
    icon: '◈',
    title: 'Persistent Memory',
    desc: 'PGVector on Nebius Token Factory stores every fix. Synapse recalls solutions from weeks ago.',
  },
  {
    icon: '⚡',
    title: 'Hybrid Routing',
    desc: 'Nemotron Nano triages in <300ms. Only complex reasoning hits Ultra. Credits stretch 10x further.',
  },
  {
    icon: '🔍',
    title: 'Tavily Research',
    desc: 'When local context isn\'t enough, auto-searches the web and saves compiled Markdown to your disk.',
  },
]

export function FeatureCards() {
  return (
    <div className="feature-cards">
      {features.map((f, i) => (
        <div key={i} className="hw-card feature-card">
          <span className="feature-icon">{f.icon}</span>
          <h3 className="feature-title">{f.title}</h3>
          <p className="feature-desc">{f.desc}</p>
        </div>
      ))}
    </div>
  )
}