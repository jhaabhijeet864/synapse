import { useState, useEffect } from 'react'
import { LandingPage } from '@/components/landing/LandingPage'
import { DesktopApp } from '@/components/app/DesktopApp'

export default function App() {
  // Check URL params or localStorage to determine initial view
  const [currentView, setCurrentView] = useState<'landing' | 'app'>(() => {
    // If in Tauri desktop mode, we can default to 'app' or check window.__TAURI_INTERNALS__
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      if (params.get('view') === 'app') return 'app'
      if (params.get('view') === 'landing') return 'landing'
      // If launched via Tauri desktop app, default to 'app'
      if ((window as any).__TAURI_INTERNALS__ || (window as any).__TAURI__) {
        return 'app'
      }
    }
    return 'landing'
  })

  // Keyboard shortcut listener to toggle between views (e.g. F1 or Esc)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && currentView === 'app') {
        // Option to go back to landing
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentView])

  if (currentView === 'app') {
    return <DesktopApp onBackToLanding={() => setCurrentView('landing')} />
  }

  return <LandingPage onEnterApp={() => setCurrentView('app')} />
}
