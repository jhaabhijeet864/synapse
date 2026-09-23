# NVIDIA Style Notes & Design Patterns

Extracted from official properties: nvidia.com, developer.nvidia.com, build.nvidia.com

## 1. Section Order (Hero to Footer)
1. **Global Navigation:** Slim black bar. Left-aligned NVIDIA wordmark, followed by product category links. Right-aligned single primary CTA (often a login or buy button).
2. **Hero:** Full-bleed background (often dark grey/black with a subtle visual texture or 3D render). Left-aligned content block.
3. **Introduction / Problem Statement:** A short, impactful, full-width text section that defines the product category before getting into features.
4. **How It Works / Architecture:** Step-by-step or logical flow diagrams. Often uses numbered steps or a tight grid of 3-4 columns.
5. **Capabilities / Feature Grids:** Alternating left-right image/text blocks for deep dives, or dense 3-column feature grids for capabilities.
6. **Specs / Models Table:** Highly structured, dense tabular data comparing models, specs, or requirements. 
7. **Developer Resources:** Documentation links, API snippets, GitHub repos. 
8. **Final CTA:** "Get Started" section with terminal commands or download buttons.
9. **Footer:** Dark grey background, multi-column sitemap, legal links, copyright, and social icons.

## 2. Hero Layout Rules
- **Headline (H1):** 3 to 6 words maximum. Left-aligned. Uses the primary display typeface (often DIN Pro or a grotesque sans-serif like Space Grotesk/Inter). Extremely bold (weight 800+).
- **Subhead:** 1 to 2 sentences. Max width constrained (e.g., ~600px). Left-aligned. Explains exactly what the product is.
- **CTAs:** 1 or 2 CTAs max. Primary is NVIDIA Green (`#76B900`) with black text. Secondary is often an outlined button or plain text link with a green arrow.
- **Background:** Never a flat, bright color. Always deep black (`#000000`) or very dark grey (`#111111` or `#1A1A1A`) with a highly polished 3D hardware render, particle simulation, or abstract technical pattern sitting *behind* the text or offset to the right.

## 3. Copy Voice
- **Tone:** Declarative, specific, technical, third-person, present tense. No fluff, no exclamation marks.
- **Naming:** Product names are Title Case (e.g., "NVIDIA Nemotron 3 Ultra"). General features are sentence case.
- **Description Pattern:** "[Product Name] is a [category] that [core action] to [primary benefit]."
- **Common Verbs:** Accelerate, deploy, build, scale, integrate, capture, reason.
- **Benefits:** Stated as concrete metrics ("3x faster", "4096-dimension embeddings") rather than vague adjectives ("revolutionary", "supercharge").
- **Tense & POV:** Always third-person ("Synapse reads on-screen context") rather than second-person ("You can read your screen").

## 4. Introducing a Service or Model
- **Header:** [Model Name] (e.g., Nemotron-4-340B-Instruct).
- **Category Line:** A single line identifying the family/class.
- **Capability Blocks:** 3 to 4 distinct use cases (e.g., Code Generation, Reasoning, Roleplay).
- **Spec Table:** Hard numbers: Parameters, Context Length, Supported Languages, License type.
- **Links:** "Get started" (direct action) and "Learn more" (docs/details).

## 5. Component Metrics & Styling
- **Type Sizes (Desktop):** H1 (72px+), H2 (32px - 48px), Body (16px or 18px), Meta/Code (13px - 14px).
- **Weights:** Headings are extremely heavy (700-900). Body text is regular (400) or medium (500) for contrast.
- **Section Padding:** Very generous. Typically `120px` to `160px` top and bottom for major sections.
- **Container Max-Width:** Typically bounded to `1200px` or `1440px` centrally, even on ultra-wide displays.
- **Radii:** Sharp, hardware-like corners. 0px to 4px border-radius. No pill buttons or fully rounded cards.

## 6. Strict Green Usage (`#76B900`)
- **Where it appears:** Primary CTA button fills, active states (tabs, selected items), link hover states, thin 1px accent lines (e.g., top border of a card or section), and focus rings.
- **Where it DOES NOT appear:** Section backgrounds, large container fills, regular body text.
- **Contrast Rule:** Text placed *on* NVIDIA Green must be pure Black (`#000000`) or very dark grey (`#1A1A1A`), never white (`#FFFFFF`), as white on #76B900 fails WCAG AA accessibility standards.
