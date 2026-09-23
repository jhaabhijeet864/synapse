import { useRef, useEffect } from 'react'
import * as THREE from 'three'

export function StarfieldBackground() {
  const mountRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    // Scene setup
    const scene = new THREE.Scene()
    
    // We match innerWidth/Height exactly
    const width = window.innerWidth
    const height = window.innerHeight

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Camera matched to viewport aspect
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 2000)
    camera.position.z = 500

    // Particle system across full volume
    const PARTICLE_COUNT = window.innerWidth < 768 ? 400 : 1200
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const colors = new Float32Array(PARTICLE_COUNT * 3)
    const sizes = new Float32Array(PARTICLE_COUNT)

    // Palette: #2A2A2A to #AAAAAA
    const colorDark = new THREE.Color(0x2A2A2A)
    const colorLight = new THREE.Color(0xAAAAAA)

    const spreadX = 2000
    const spreadY = 1500
    const spreadZ = 1000

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      positions[i * 3] = (Math.random() - 0.5) * spreadX
      positions[i * 3 + 1] = (Math.random() - 0.5) * spreadY
      positions[i * 3 + 2] = (Math.random() - 0.5) * spreadZ

      // Interpolate between dark and light gray
      const c = new THREE.Color().lerpColors(colorDark, colorLight, Math.random())
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b

      sizes[i] = 1 + Math.random() * 2.5
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    const material = new THREE.PointsMaterial({
      size: 3,
      vertexColors: true,
      transparent: true,
      opacity: 0.25, // 0.15 to 0.4 range visually
      depthWrite: false,
    })

    const particles = new THREE.Points(geometry, material)
    scene.add(particles)

    // Check for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Animation loop
    let animationId: number
    let isTabVisible = true

    const handleVisibility = () => {
      isTabVisible = document.visibilityState === 'visible'
    }
    document.addEventListener('visibilitychange', handleVisibility)

    const animate = () => {
      animationId = requestAnimationFrame(animate)

      if (!isTabVisible) return

      if (!prefersReducedMotion) {
        // Slow drift upwards and slight rotation
        particles.position.y += 0.2
        particles.rotation.y += 0.0005
        particles.rotation.x += 0.0002

        // Wrap particles around if they drift too high
        if (particles.position.y > 500) {
          particles.position.y = -500
        }
      }

      renderer.render(scene, camera)
    }

    // Render one frame immediately for reduced-motion, otherwise start loop
    if (prefersReducedMotion) {
      renderer.render(scene, camera)
    } else {
      animate()
    }

    // Handle resize
    const handleResize = () => {
      const w = window.innerWidth
      const h = window.innerHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
      if (prefersReducedMotion) {
        renderer.render(scene, camera) // Re-render on resize
      }
    }

    // ResizeObserver on body and orientationchange for mobile robustness
    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(document.body)
    window.addEventListener('orientationchange', handleResize)

    // Cleanup
    return () => {
      if (animationId) cancelAnimationFrame(animationId)
      resizeObserver.disconnect()
      window.removeEventListener('orientationchange', handleResize)
      document.removeEventListener('visibilitychange', handleVisibility)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      renderer.dispose()
      geometry.dispose()
      material.dispose()
    }
  }, [])

  return (
    <div
      ref={mountRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        background: '#000000', // Deep background
      }}
      aria-hidden="true"
    />
  )
}
