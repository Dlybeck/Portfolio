# Personal Portfolio

An evolving, nonlinear portrait of David Lybeck expressed through the things he has made, done, learned, and enjoyed. It exists to reward exploration rather than deliver a prescribed professional pitch.

## Language

**Living Self-Portrait**:
The portfolio as a continuously evolving expression of David's personal, professional, educational, and recreational history.
_Avoid_: Resume site, hiring funnel, static archive

**Viewer**:
A person exploring the self-portrait, whether arriving with prior context or discovering it through search or a shared link. The viewer's ability to understand and enjoy the experience has priority.
_Avoid_: Recruiter, customer, user

**Exploration**:
Viewer-directed discovery of related parts of the self-portrait without a prescribed reading order.
_Avoid_: Conversion path, content funnel

**Discovery**:
The moment a viewer infers how the self-portrait works from its visual cues and brief in-world guidance, then chooses to explore it further.
_Avoid_: External onboarding, guided tour

**Neighborhood**:
A centered section and at most four directly related sections: its Parent and up to three Children. It is both the visible navigation unit and the keyboard focus cycle.
_Avoid_: Menu, sitemap

**Parent**:
The directly related broader section one step closer to Home.
_Avoid_: Back button, previous page

**Child**:
A directly related narrower section one step farther from Home. A section has no more than three Children.
_Avoid_: Subpage, menu item

**Board Theme**:
A coherent visual treatment of the board and its opened documents. A theme may change styling but never the navigation structure or general interaction experience; Canonical remains the fail-closed fallback.
_Avoid_: Random skin, replacement theme

**Theme Pack**:
A versioned, declarative bundle of visual tokens and sanitized assets that completely describes one Board Theme without executable theme-specific code.
_Avoid_: Theme stylesheet, renderer plugin, skin

Current implementation and review authority for Theme Pack naturalism is
recorded in `docs/theme-naturalism-restoration.md`. It is the active source of
truth when it conflicts with the earlier refinement specification.

**Theme Instance**:
A selected Theme Pack and its deterministic per-location identities applied throughout one exploration. Refreshing without an explicit pin may select a new complete instance.
_Avoid_: Theme, random skin

**Theme Engine**:
The isolated system that discovers, validates, selects, and applies Theme Packs while preserving the Interaction Structure.
_Avoid_: Theme switcher, theme script

**Depth Layer**:
An optional, ordered, pointer-inert Theme Pack background asset with a bounded movement factor from fixed viewport (`0`) to full Board movement (`1`). Depth Layers may decorate a world but never contain tiles, labels, relationships, focus surfaces, hit targets, or documents.
_Avoid_: Parallax navigation, moving content plane

**Interaction Structure**:
The invariant parent-child navigation, Neighborhood limits, document flow, and responsive behavior shared by every Board Theme. During Board focus and motion, neighboring destinations remain visible and directly actionable through the same pointer, touch, and keyboard relationships.
_Avoid_: Theme, visual treatment

**Real-World Coherence**:
The rule that a Board Theme's objects, surfaces, and motion follow a familiar real-life metaphor closely enough for the Viewer to recognize them and infer their behavior. A decorative or readability treatment needs an understandable in-world reason rather than existing only to solve an interface problem.
_Avoid_: Abstract visual consistency, arbitrary decoration

**Personal Mark**:
The stable visual identifier representing David across themes and asset sizes. A Board Theme may alter its border, badge, or surrounding treatment without replacing its recognizable core.
_Avoid_: Theme logo, social-preview image

**Document Grammar**:
The uniform structure and visual language shared by opened documents to keep the self-portrait coherent and maintainable as it grows.
_Avoid_: Bespoke microsite, page-specific framework

**Historical Work**:
A completed artifact retained because it contributes to the self-portrait, regardless of its age or current professional relevance.
_Avoid_: Obsolete content, low-signal work

**Artifact Label**:
Current explanatory copy, links, titles, and status information surrounding Historical Work. Labels are corrected as mistakes or stale facts are found without rewriting the underlying artifact's history.
_Avoid_: Historical artifact

**Destination Link**:
A shareable address that restores a specific place in the self-portrait with its document open while retaining the surrounding board.
_Avoid_: Standalone page, detached document

**Preserved Demo**:
The publicly accessible demonstration of a former service, retained to show what the service did without representing an active business or service offering.
_Avoid_: Live service, current business

**Professional Discovery Layer**:
Search, social-preview, and machine-readable information that foregrounds David's current identity as an Innovation AI Developer and software builder while the visible self-portrait remains broader and personal.
_Avoid_: Professional homepage, recruiter funnel
