# Visual identity and documentation graphics

graver's visual system should make engine behavior, research flow, provenance, and
human decision points easier to understand. Graphics are part of the documented
contract when they teach workflow or evidence meaning; they are not decoration
applied after the text is finished.

## Brand relationship

- **Kinship Ledger** is the publishing and community identity.
- **graver** is the research engine, command, Python package, and distinct
  application identity.
- The future professional desktop experience is a separate product layer over the
  graver engine and earns its own readiness claim and acceptance gates.
- The graver mark should support the name's “digger” sense: patient research that
  uncovers and preserves evidence. It should not imply that graver proves facts,
  manages cemeteries, or limits its future to grave records.
- The shared verbal direction is archival fieldwork: evidence tags, ink, paper,
  ledger marks, restrained earth tones, and one warm accent. The Kinship Ledger
  tagline is “Where family history keeps its receipts.”

## Icon brief

No icon direction is yet approved. A lowercase **g**, magnifying glass, gravestone,
root, record page, evidence seal, archival tab, marginal mark, excavation layer, or
research receipt may be explored, but tree- and tombstone-based genealogy imagery
is familiar enough to risk becoming generic. A concept must earn selection through
distinctiveness and meaning rather than merely announcing “genealogy.” The finished
mark must:

- remain recognizable at 16, 24, 32, 64, and 128 pixels;
- work in light, dark, monochrome, and high-contrast settings;
- avoid tiny text, gradients essential to recognition, embedded fonts, and embedded
  raster images;
- avoid generic family-tree clip art, DNA helices, heraldic imagery, and unexamined
  reliance on familiar cemetery symbolism;
- remain visually distinct from the Kinship Ledger organization mark; and
- have an original editable SVG master plus reviewed PNG exports.

Concept generation may use an AI-assisted vector tool such as Recraft. A final
asset generated with Recraft must be created under terms that grant the project the
necessary ownership and commercial rights; free-plan output is not acceptable for
the final mark. Retain the dated tool, plan, prompt or design brief, exported source,
and human modifications in the asset provenance record. AI output is a design
input, not evidence of originality or trademark availability.

Before adoption, inspect the SVG for unexpected metadata, scripts, remote resources,
embedded raster content, inaccessible color dependence, excessive path complexity,
and poor rendering. Conduct a reasonable similarity and name/mark conflict review.
Human judgment owns the final geometry, meaning, licensing decision, and approval.

## First documentation diagrams

The first visual slice should contain three small, purposeful diagrams:

1. **The researcher journey:** the current Find a Grave path from choosing a research
   file through bounded acquisition, review, and researcher-directed next actions.
2. **Evidence reasoning:** source observation → comparison → assessment →
   researcher-authored conclusion, with ordering explicitly separated from
   confidence and proof.
3. **Client architecture:** the supported operational CLI and future preferred
   desktop product sharing the typed graver engine application layer without
   implying equal user-experience roles.

Use Mermaid for diagrams whose structure changes frequently and reviewed SVG for
stable researcher-facing graphics. Every diagram requires nearby explanatory text,
a useful text alternative, legible contrast, and a readable narrow-screen rendering.
Never encode a critical distinction by color alone.

## Review cadence

Visual assets are reviewed when introduced and whenever a material change affects
their meaning, accessibility, rendering, or provenance:

- Pull requests identify added or changed icons, diagrams, screenshots, colors, or
  generated assets and record their source and license.
- Release review checks that researcher-facing diagrams still match current
  behavior and that badges, screenshots, version labels, and branding are current.
- Professional-researcher reviews include any diagram that frames evidence,
  confidence, identity, kinship, provenance, or workflow decisions.
- Technical-publications reviews check whether graphics clarify the text, remain
  understandable without hidden implementation knowledge, and have adequate text
  alternatives.
- Front-end UX reviews cover visual hierarchy, interaction continuity,
  accessibility, light/dark rendering, icon comprehension, and consistency with
  the documented visual system.
- External reviews receive the graphics in their ordinary context and are invited
  to report misleading implications, not merely aesthetic preferences.

A visual change becomes release-blocking when it could direct a researcher to the
wrong action, overstate evidence, hide provenance, misrepresent current behavior,
or create a material accessibility failure. Cosmetic refinements may remain
follow-ups when their deferral is explicit.
