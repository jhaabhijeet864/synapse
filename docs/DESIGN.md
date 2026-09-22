# SYNAPSE Design Document

## 1. Visual Identity & Theme

SYNAPSE adheres to a minimalist, high-tech aesthetic inspired by NVIDIA hardware designs. The look is structured, slightly angular, and focuses on highlighting complex information through intelligent lighting effects. Every design decision reinforces one idea: **this is precision engineering for your cognition**.

### 1.1 Strictly Limited Color Palette

This project must strictly limit color usage to the following HEX codes. No deviations are permitted without major design review.

| Element | Description | HEX Code |
| :--- | :--- | :--- |
| **Deep Background** | Main window background | `#000000` (Pure Black) |
| **Containers / Cards** | Surface level for UI elements | `#1A1A1A` (Dark Gray) |
| **Hardware Accent** | Subtler lighting / structural details | `#2A2A2A` (Mid-Dark Gray) |
| **NVIDIA Green** | **SIGNAL ONLY.** CTAs, Active States, Connections | `#76B900` |
| **Primary Text** | Headlines, important data | `#FFFFFF` |
| **Secondary Text** | Subtitles, descriptions, captions | `#AAAAAA` |

> **Design Law:** Green is a signal, not a color. If something glows green, it means something is happening. Overuse destroys meaning.

### 1.2 Typography

| Role | Font | Size | Weight | Color |
|------|------|------|--------|-------|
| Hero H1 (SYNAPSE wordmark) | `Inter` or `Space Grotesk` | 72–96px | 800 | `#FFFFFF` |
| Section H2 | `Inter` | 32px | 700 | `#FFFFFF` |
| Card title | `Inter` | 16px | 600 | `#FFFFFF` |
| Body / description | `Inter` | 14px | 400 | `#AAAAAA` |
| Code / terminal | `JetBrains Mono` | 13px | 400 | `#AAAAAA` |
| CTA button label | `Inter` | 14px | 700 | `#FFFFFF` |
| Meta / timestamps | `Inter` | 11px | 500 | `#555555` |

### 1.3 Spacing & Shape Language

- **Grid:** 8px base unit. All spacing is multiples of 8.
- **Border radius:** Cards use `4px` (slightly angular, hardware feel). Buttons use `4px`. No rounded pill shapes.
- **Borders:** `1px solid #2A2A2A` as default. Active elements get `1px solid #76B900`.
- **Shadows:** Never use colored drop shadows except green glow on active elements.

---

## 2. Landing Page UI: Implementation Guide

### 2.1 The "Neuron Sphere" Central Animation — The Wow Moment

The landing page must feature a dominant, central animation that visualizes the ambient AI connection process. This is the first thing a visitor sees. It must be immediately impressive.

**Concept:** A decentralized, pulsing network of neurons — a living brain — contained within a subtle geometric sphere. It visualizes Synapse "thinking" about your screen in real time.

#### Technology
- **Primary:** Three.js (WebGL) — particle system with BufferGeometry for performance
- **Fallback:** Optimized 2D Canvas with `requestAnimationFrame`
- Target: **60fps, < 5ms frame time** on mid-range hardware

#### Visual Structure

```
                    ┌─────────────────────────────────┐
                    │   Spherical wireframe #2A2A2A   │
                    │                                  │
                    │     ·  ·    ✦ ← green pulse     │
                    │   ·       ·    ·                 │
                    │      ·  ·   ·      ·             │
                    │   ·     ·━━━━━✦    ·             │
                    │      ·     ·    ·                │
                    │   ·    ·      ·   ·              │
                    │                                  │
                    └─────────────────────────────────┘
                    · = gray node (#AAAAAA)
                    ━ = fine connection line
                    ✦ = green pulse node (#76B900)
```

#### Particle System Specs
| Property | Value |
|----------|-------|
| Node count | ~200 particles |
| Node color (idle) | `#AAAAAA` with opacity 0.6 |
| Node size | 2–4px, randomized |
| Connection lines | Max 3 per node, opacity 0.15, color `#AAAAAA` |
| Sphere radius | 280px (desktop), 180px (mobile) |
| Wireframe | `#2A2A2A`, opacity 0.3, icosahedron geometry |

#### Animation Behavior

**Idle State:**
- Nodes drift slowly within the sphere bounds (Brownian motion, max velocity 0.3px/frame)
- Connection lines are `opacity: 0` — invisible
- Sphere very slowly rotates on Y-axis (0.001 rad/frame)

**Active Pulse (the money shot):**
- Triggers every 2–4 seconds (randomized interval)
- A green arc (`#76B900`) traces a path between two random nodes
- Arc travels at ~120px/frame along the shortest node path
- When pulse reaches a node: node flashes green, opacity spikes to 1.0, then fades back over 400ms
- Connection lines briefly appear along the pulse path (`opacity: 0.4`) then fade
- Green glow: `box-shadow: 0 0 8px #76B900` on the node element

**Mouse Interactivity:**
- Mouse position maps to sphere rotation (parallax): sphere tilts ±15° following cursor
- Mouse hover over sphere: pulse frequency doubles (triggers every 0.8–1.5s)
- Mouse click: triggers an immediate multi-node cascade pulse (3–5 nodes light up in sequence)

#### Implementation Skeleton (Three.js)
```javascript
// Key parameters
const PARTICLE_COUNT = 200;
const SPHERE_RADIUS = 280;
const PULSE_INTERVAL_MS = { min: 2000, max: 4000 };
const PULSE_COLOR = new THREE.Color(0x76B900);
const NODE_COLOR = new THREE.Color(0xAAAAAA);

// Pulse logic: pick two random nodes, lerp a tracer between them
function triggerPulse(nodeA, nodeB) {
  const tracer = createTracer(nodeA.position, nodeB.position);
  tracer.onArrive = () => flashNode(nodeB, PULSE_COLOR, 400);
  scene.add(tracer);
}
```

---

### 2.2 Hero Text Section

Minimalism is key. The sphere dominates. Text supports.

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│           [NEURON SPHERE ANIMATION — CENTER]             │
│                                                          │
│                      SYNAPSE                             │  ← H1, #FFFFFF, 80px, weight 800
│                                                          │
│       The AI that lives between your brain               │  ← subtitle, #AAAAAA, 18px
│              and your computer.                          │
│                                                          │
│              [  Download for Windows  ]                  │  ← CTA button, #76B900 bg
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**H1 treatment:**
- Font: `Space Grotesk` 800 weight, letter-spacing `-0.02em`
- Color: `#FFFFFF`
- Effect: Subtle `text-shadow: 0 0 40px rgba(118, 185, 0, 0.15)` — barely-there green ambient glow
- Do NOT use heavy glow; keep it sharp

**Subheadline:**
- Color: `#AAAAAA`, 18px, weight 400
- Max-width: 480px, centered
- Line-height: 1.6

---

### 2.3 The Main CTA Button

The CTA must be the most visually striking actionable element on the page.

```css
.cta-button {
  background: #76B900;
  color: #FFFFFF;
  font-weight: 700;
  font-size: 14px;
  padding: 14px 32px;
  border-radius: 4px;
  border: none;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cta-button:hover {
  background: radial-gradient(circle at center, #8ED000 0%, #76B900 70%);
  box-shadow: 0 0 24px rgba(118, 185, 0, 0.35);
  transform: translateY(-1px);
}

.cta-button:active {
  transform: translateY(0);
  box-shadow: 0 0 12px rgba(118, 185, 0, 0.2);
}
```

> **Rule:** The green hover shouldn't just lighten — it should look like light is radiating from the center. The `radial-gradient` achieves this.

---

### 2.4 Feature Containers — The "Hardware" Look

Instead of traditional rounded cards, containers should look like brushed metal PCB segments or high-end GPU packaging sections.

```css
.feature-card {
  background: linear-gradient(145deg, #2A2A2A 0%, #1A1A1A 100%);
  border-left: 1px solid #3A3A3A;    /* highlight edge — light hitting metal */
  border-top: 1px solid #3A3A3A;
  border-right: 1px solid #2A2A2A;   /* shadow edge */
  border-bottom: 1px solid #2A2A2A;
  border-radius: 4px;
  padding: 24px;
  position: relative;
}

/* Green signal line at top of active/selected card */
.feature-card.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: #76B900;
}

/* Ambient green under-glow on active/hover */
.feature-card.active,
.feature-card:hover {
  box-shadow:
    0 0 0 1px #2A2A2A,
    0 4px 24px rgba(118, 185, 0, 0.08);
}
```

**Beveled edge simulation (key detail):**
- Top-left border: `#3A3A3A` — simulates light source from top-left
- Bottom-right border: `#1A1A1A` — shadow side
- Background gradient: `#2A2A2A → #1A1A1A` — depth illusion

---

## 3. Overlay Card Design (In-App UI)

The floating Synapse card that appears over the user's desktop follows the same hardware aesthetic.

### Card Anatomy

```
┌──────────────────────────────────────────┐  ← border: 1px #2A2A2A
│▌ SYNAPSE                      [×]  [–]  │  ← header, bg #1A1A1A
│  ───────── 1px #76B900 top line ─────── │  ← always green on active card
├──────────────────────────────────────────┤
│  ⬡ VS Code  ·  47s ago                  │  ← context badge, #AAAAAA 11px
│  ◈ Memory: auth module, 3 days ago      │
├──────────────────────────────────────────┤
│                                          │
│  The TypeError on line 47 occurs        │  ← response text, #FFFFFF 13px
│  because user.token is not initialized  │
│  before the guard check.                │
│                                          │
│  ┌──────────────────────────────────┐   │  ← code block, bg #0D0D0D
│  │ - if user.token.valid:           │   │
│  │ + if user and user.token and     │   │
│  │ +    user.token.valid:           │   │
│  └──────────────────────────────────┘   │
├──────────────────────────────────────────┤
│  [Apply Fix]  [Save]  [More ▾]  nano·0.3s│  ← action bar
└──────────────────────────────────────────┘
```

```css
.synapse-card {
  background: #1A1A1A;
  border: 1px solid #2A2A2A;
  border-radius: 4px;
  width: 380px;
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.6),
    0 0 0 1px #2A2A2A;
  position: fixed;
  bottom: 24px;
  right: 24px;
}

.synapse-card__header {
  background: #1A1A1A;
  border-bottom: 1px solid #76B900;  /* always green — this is "active" */
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.synapse-card__response {
  padding: 16px 14px;
  color: #FFFFFF;
  font-size: 13px;
  line-height: 1.6;
}

.synapse-card__code {
  background: #0D0D0D;
  border: 1px solid #2A2A2A;
  border-radius: 2px;
  padding: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.synapse-card__action-bar {
  padding: 10px 14px;
  border-top: 1px solid #2A2A2A;
  display: flex;
  gap: 8px;
  align-items: center;
}
```

---

## 4. General Implementation Rules

### 4.1 Loading States — No Spinners

Do not use default "spinning loaders." SYNAPSE must maintain the perception of speed at all times.

When the agent is reasoning (calling Nemotron via Nebius), the UI must respond immediately with a low-cost local animation.

**Implementation: The "Data Pulse" Border Effect**

```css
@keyframes dataPulse {
  0%   { border-color: #2A2A2A; box-shadow: none; }
  50%  { border-color: #76B900; box-shadow: 0 0 12px rgba(118,185,0,0.2); }
  100% { border-color: #2A2A2A; box-shadow: none; }
}

.synapse-card.loading {
  animation: dataPulse 1.2s ease-in-out infinite;
}
```

A green pulse ripples through the card border while the model reasons. This tells the user "data is moving" without breaking the ambient feel.

**Never use:**
- Default browser spinners
- Progress bars
- Skeleton loaders with rounded shapes
- Any animation with non-palette colors

### 4.2 Hover and Active States

All interactive elements respond within the approved palette:

| Element | Idle | Hover | Active/Selected |
|---------|------|-------|----------------|
| Text button | `#AAAAAA` | `#FFFFFF` | `#FFFFFF` |
| Green CTA | `#76B900` | radial-gradient brighter | `#5A8F00` |
| Feature card | `#1A1A1A` bg | `+#2A2A2A` border | `+#76B900` top line + glow |
| Icon | `#555555` | `#AAAAAA` | `#FFFFFF` |
| Nav link | `#AAAAAA` | `#FFFFFF` | `#76B900` underline |

### 4.3 Transitions

```css
/* Standard transition — fast, hardware feel */
transition: all 0.12s ease;

/* For glow effects — slightly slower for smoothness */
transition: box-shadow 0.2s ease, border-color 0.2s ease;

/* No transitions longer than 250ms in the app UI */
/* Landing page animations (sphere, hero) can be longer */
```

### 4.4 What to Avoid

| ❌ Never do | ✅ Instead |
|------------|----------|
| Rounded pill buttons | `border-radius: 4px` max |
| Blue, purple, orange accents | Only the 6 palette colors |
| Heavy green glow everywhere | Green glow ONLY on active/loading states |
| Full-screen color backgrounds | Always on `#000000` or `#1A1A1A` |
| Gradient text (rainbow) | `#FFFFFF` or `#AAAAAA` only |
| Animated gradients on cards (loud) | Static gradient, motion only via border pulses |
| Generic spinner loaders | Data pulse border animation |
| Soft, rounded card shapes | Sharp 4px, beveled border look |

---

## 5. Reference Mood

The design target is: **NVIDIA RTX packaging meets ambient OS intelligence**. Think the feel of opening a high-end GPU box — dark, precise, purposeful — but it lives on your screen as a quiet, intelligent layer.

Every pixel should ask: *"Does this look like it belongs on premium hardware?"*