import { useRef, useEffect } from 'react'
import * as THREE from 'three'

interface NeuronSphereProps {
  className?: string
}

export function NeuronSphere({ className }: NeuronSphereProps) {
  const mountRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    // Mutable state for interactivity without triggering re-renders
    const state = {
      isHovered: false,
      mouseX: 0,
      mouseY: 0
    }

    // Scene setup
    const scene = new THREE.Scene()
    
    // Initial size
    let width = container.clientWidth || 560
    let height = container.clientHeight || 560

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000)
    camera.position.z = 500

    // Parameters from DESIGN.md
    const PARTICLE_COUNT = 200
    const SPHERE_RADIUS = 280
    const NODE_COLOR = new THREE.Color(0xAAAAAA)
    const PULSE_COLOR = new THREE.Color(0x76B900)
    const WIREFRAME_COLOR = new THREE.Color(0x2A2A2A)

    // Create particle positions
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const colors = new Float32Array(PARTICLE_COUNT * 3)
    const sizes = new Float32Array(PARTICLE_COUNT)
    const velocities = new Float32Array(PARTICLE_COUNT * 3)

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Random point in sphere
      const radius = Math.random() * SPHERE_RADIUS * 0.8
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = radius * Math.cos(phi)

      // Random velocity for Brownian motion
      velocities[i * 3] = (Math.random() - 0.5) * 0.3
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.3
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.3

      colors[i * 3] = NODE_COLOR.r
      colors[i * 3 + 1] = NODE_COLOR.g
      colors[i * 3 + 2] = NODE_COLOR.b

      sizes[i] = 2 + Math.random() * 2
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    // Particle material
    const particleMaterial = new THREE.PointsMaterial({
      size: 3,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      depthWrite: false,
    })

    const particles = new THREE.Points(geometry, particleMaterial)
    scene.add(particles)

    // Wireframe sphere
    const wireGeometry = new THREE.IcosahedronGeometry(SPHERE_RADIUS, 3)
    const wireMaterial = new THREE.MeshBasicMaterial({
      color: WIREFRAME_COLOR,
      wireframe: true,
      transparent: true,
      opacity: 0.3,
    })
    const wireframe = new THREE.Mesh(wireGeometry, wireMaterial)
    scene.add(wireframe)

    // Pulse tracer line
    const tracerGeometry = new THREE.BufferGeometry()
    const tracerPositions = new Float32Array(3 * 2)
    tracerGeometry.setAttribute('position', new THREE.BufferAttribute(tracerPositions, 3))
    const tracerMaterial = new THREE.LineBasicMaterial({
      color: PULSE_COLOR,
      transparent: true,
      opacity: 0.4,
      linewidth: 2,
    })
    const tracer = new THREE.Line(tracerGeometry, tracerMaterial)
    scene.add(tracer)
    tracer.visible = false

    // Pulse state
    let pulseProgress = 1
    let pulseStart: THREE.Vector3 | null = null
    let pulseEnd: THREE.Vector3 | null = null
    let pulseTargetNode = -1
    let lastPulseTime = 0
    let nextPulseInterval = 2000 + Math.random() * 2000

    const triggerPulse = () => {
      const posAttr = geometry.attributes.position
      const nodeA = Math.floor(Math.random() * PARTICLE_COUNT)
      const nodeB = Math.floor(Math.random() * PARTICLE_COUNT)
      if (nodeA === nodeB) return

      pulseStart = new THREE.Vector3(
        posAttr.getX(nodeA),
        posAttr.getY(nodeA),
        posAttr.getZ(nodeA)
      )
      pulseEnd = new THREE.Vector3(
        posAttr.getX(nodeB),
        posAttr.getY(nodeB),
        posAttr.getZ(nodeB)
      )
      pulseTargetNode = nodeB
      pulseProgress = 0
      tracer.visible = true
      lastPulseTime = performance.now()
      nextPulseInterval = state.isHovered ? 800 + Math.random() * 700 : 2000 + Math.random() * 2000
    }

    // Animation loop
    let animationId: number

    const animate = (time: number) => {
      animationId = requestAnimationFrame(animate)

      // Sphere rotation
      wireframe.rotation.y += 0.001
      particles.rotation.y += 0.001

      // Parallax tilt from mouse
      wireframe.rotation.x += (state.mouseY * 0.15 - wireframe.rotation.x) * 0.05
      wireframe.rotation.z += (-state.mouseX * 0.15 - wireframe.rotation.z) * 0.05
      particles.rotation.x = wireframe.rotation.x
      particles.rotation.z = wireframe.rotation.z

      // Brownian motion for particles
      const posAttr = geometry.attributes.position
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        posAttr.setX(i, posAttr.getX(i) + velocities[i * 3])
        posAttr.setY(i, posAttr.getY(i) + velocities[i * 3 + 1])
        posAttr.setZ(i, posAttr.getZ(i) + velocities[i * 3 + 2])

        // Bounds check - keep in sphere
        const x = posAttr.getX(i)
        const y = posAttr.getY(i)
        const z = posAttr.getZ(i)
        const dist = Math.sqrt(x * x + y * y + z * z)
        if (dist > SPHERE_RADIUS) {
          const scale = SPHERE_RADIUS / dist * 0.95
          posAttr.setX(i, x * scale)
          posAttr.setY(i, y * scale)
          posAttr.setZ(i, z * scale)
          // Reflect velocity
          velocities[i * 3] *= -0.5
          velocities[i * 3 + 1] *= -0.5
          velocities[i * 3 + 2] *= -0.5
        }
      }
      posAttr.needsUpdate = true

      // Pulse animation
      if (pulseStart && pulseEnd && pulseProgress < 1) {
        pulseProgress += 0.025
        const currentPos = new THREE.Vector3().lerpVectors(pulseStart, pulseEnd, pulseProgress)
        const tracerPos = tracer.geometry.attributes.position
        tracerPos.setXYZ(0, pulseStart.x, pulseStart.y, pulseStart.z)
        tracerPos.setXYZ(1, currentPos.x, currentPos.y, currentPos.z)
        tracerPos.needsUpdate = true

        if (pulseProgress >= 1) {
          // Flash target node
          flashNode(pulseTargetNode)
          tracer.visible = false
          pulseStart = null
          pulseEnd = null
        }
      }

      // Auto-trigger pulse
      if (time - lastPulseTime > nextPulseInterval && !pulseStart) {
        triggerPulse()
      }

      renderer.render(scene, camera)
    }

    const flashNode = (index: number) => {
      const colorAttr = geometry.attributes.color
      const originalR = colorAttr.getX(index)
      const originalG = colorAttr.getY(index)
      const originalB = colorAttr.getZ(index)

      colorAttr.setXYZ(index, PULSE_COLOR.r, PULSE_COLOR.g, PULSE_COLOR.b)
      colorAttr.needsUpdate = true

      // Fade back over 400ms
      const startTime = performance.now()
      const fadeAnimation = (t: number) => {
        const elapsed = t - startTime
        if (elapsed < 400) {
          const progress = elapsed / 400
          const eased = 1 - Math.pow(1 - progress, 3)
          colorAttr.setXYZ(
            index,
            originalR + (PULSE_COLOR.r - originalR) * (1 - eased),
            originalG + (PULSE_COLOR.g - originalG) * (1 - eased),
            originalB + (PULSE_COLOR.b - originalB) * (1 - eased)
          )
          colorAttr.needsUpdate = true
          requestAnimationFrame(fadeAnimation)
        } else {
          colorAttr.setXYZ(index, originalR, originalG, originalB)
          colorAttr.needsUpdate = true
        }
      }
      requestAnimationFrame(fadeAnimation)
    }

    // Interaction Handlers
    const onMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      state.mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1
      state.mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1
    }
    const onClick = () => {
      for (let i = 0; i < 5; i++) {
        setTimeout(() => triggerPulse(), i * 150)
      }
    }
    const onMouseEnter = () => { state.isHovered = true }
    const onMouseLeave = () => { state.isHovered = false }

    container.addEventListener('mousemove', onMouseMove)
    container.addEventListener('click', onClick)
    container.addEventListener('mouseenter', onMouseEnter)
    container.addEventListener('mouseleave', onMouseLeave)

    // Resize Handling
    const handleResize = () => {
      if (!container) return
      width = container.clientWidth
      height = container.clientHeight
      
      // Prevent division by zero
      if (width === 0 || height === 0) return

      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }

    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(container)

    // Start loop
    animate(0)

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      resizeObserver.disconnect()
      container.removeEventListener('mousemove', onMouseMove)
      container.removeEventListener('click', onClick)
      container.removeEventListener('mouseenter', onMouseEnter)
      container.removeEventListener('mouseleave', onMouseLeave)
      
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      
      renderer.dispose()
      geometry.dispose()
      particleMaterial.dispose()
      wireGeometry.dispose()
      wireMaterial.dispose()
      tracerGeometry.dispose()
      tracerMaterial.dispose()
    }
  }, []) // Empty deps list! We rely on mutable state for interaction

  return (
    <div
      ref={mountRef}
      className={`neuron-sphere ${className || ''}`}
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        top: 0,
        left: 0,
      }}
    />
  )
}