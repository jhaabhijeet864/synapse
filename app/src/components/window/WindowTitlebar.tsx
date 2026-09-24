import { Minus, Square, X } from 'lucide-react'

interface WindowTitlebarProps {
  title?: string
  subtitle?: string
  state?: string
  onClose?: () => void
}

export function WindowTitlebar({
  title = "SYNAPSE",
  subtitle = "Ambient Cognitive Layer",
  state,
  onClose
}: WindowTitlebarProps) {
  // Use Tauri v2 window API if available, else gracefully fallback for browser testing
  const handleMinimize = async () => {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window')
      await getCurrentWindow().minimize()
    } catch {
      console.log('Window minimize triggered')
    }
  }

  const handleMaximize = async () => {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window')
      await getCurrentWindow().toggleMaximize()
    } catch {
      console.log('Window toggle maximize triggered')
    }
  }

  const handleClose = async () => {
    if (onClose) {
      onClose()
      return
    }
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window')
      await getCurrentWindow().close()
    } catch {
      console.log('Window close triggered')
    }
  }

  return (
    <div className="nv-window-titlebar" data-tauri-drag-region>
      <div className="nv-window-titlebar__left">
        <span className="nv-window-titlebar__icon">▌</span>
        <span className="nv-window-titlebar__title">{title}</span>
        <span className="nv-window-titlebar__sep">|</span>
        <span className="nv-window-titlebar__subtitle">{subtitle}</span>
        {state && (
          <span className="nv-window-titlebar__badge">{state}</span>
        )}
      </div>

      <div className="nv-window-titlebar__controls">
        <button
          className="nv-window-btn nv-window-btn--min"
          onClick={handleMinimize}
          title="Minimize"
          aria-label="Minimize"
        >
          <Minus size={13} />
        </button>
        <button
          className="nv-window-btn nv-window-btn--max"
          onClick={handleMaximize}
          title="Maximize"
          aria-label="Maximize"
        >
          <Square size={11} />
        </button>
        <button
          className="nv-window-btn nv-window-btn--close"
          onClick={handleClose}
          title="Close"
          aria-label="Close"
        >
          <X size={13} />
        </button>
      </div>
    </div>
  )
}
