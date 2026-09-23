# Phase 0: Diagnosis & Root Cause Analysis

## Measurements & Environment
- **Canvas Elements:** 9 `<canvas>` elements found on mobile viewport test, all appended to `<div class="neuron-sphere">`.
- **Canvas Sizes (390x844):** Canvas attributes `width="542"` / `height="700"`, CSS size `width: 434px` / `height: 560px`. Mismatch between intrinsic attribute size and CSS size.
- **Positioning:** All `<canvas>` elements and `.neuron-sphere` parent have `position: static` and `zIndex: auto`. They are in normal document flow.

## Symptom Analysis

| Symptom | Measured Evidence | Root Cause (file:line) | Planned Fix |
|---|---|---|---|
| **S1. Wireframe sphere appears as narrow vertical band... cluster at bottom** | Canvas `widthAttr` vs CSS `width` mismatch (e.g., 542 vs 434px) causes squishing. Component is `position: static` (flow) not absolute, placed before `HeroText`. Screenshot: 1920x1080.png | `App.tsx:90` (static placement in flex flow). `NeuronSphere.tsx:276` (`[hovered]` dependency runs effect repeatedly without `removeChild`). | Remove `hovered` from effect deps, add `container.removeChild`. Wrap hero in a relative container, place `NeuronSphere` as absolute background right-aligned. Use `ResizeObserver` to sync canvas size exactly. |
| **S2. Background pattern does not cover the full viewport.** | Only `NeuronSphere` canvases exist. No dedicated `StarfieldBackground` component mounts a full-screen canvas. | Missing `StarfieldBackground` component in `App.tsx:88`. | Create `StarfieldBackground.tsx` (position fixed, inset 0, z-index 0) and render it in `LandingPage`. |
| **S3. Pattern visible behind gaps between cards.** | `NeuronSphere` uses normal flow (`position: static`) within a flex column container instead of being fixed behind the view or positioned absolutely in the hero. | `App.tsx:90` | Make `StarfieldBackground` `position: fixed` and `z-index: 0`. Place cards in `z-index: 10` foreground layout. |
| **S4. Feature cards contain color emoji / Unicode glyphs.** | Visual review of UI. Grep for `⚡` / `🔍` in `FeatureCards.tsx` (implied). | `FeatureCards.tsx` | Replace all emojis and Unicode pictographs with `lucide-react` icons (strokeWidth 1.5, #AAAAAA). |
| **S5. Unsupported claims (10x, <300ms).** | Visual review of text in UI. | `HeroText.tsx` / `FeatureCards.tsx` | Rewrite copy to match docs. Remove "10x", label latency strictly based on measured/target data or remove it entirely. |
| **S6. Centered-everything layout with identical stacked cards, title case, gradients.** | Container `landing-content` has `display: flex` with centered content. | `App.tsx:89` (`landing-content` CSS). | Implement 12-column grid, left-align text, use alternating sections and spec tables per NVIDIA style constraints. |
| **Additional: Memory Leak / Multi-canvas mounting** | 9 `<canvas>` elements mounted in the DOM. | `NeuronSphere.tsx:24` and `:276` | Add `container.removeChild(renderer.domElement)` in cleanup and remove `[hovered]` from dependency array. |

## Next Steps
Proceeding to Phase 1 and 2: Read product context and document NVIDIA style notes.
