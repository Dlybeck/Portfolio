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

Current realism review authority is `docs/theme-grounding-review.md`; earlier
catalog decisions in `docs/full-realism-polish.md` are historical. The Original
fidelity baselines remain in `docs/theme-naturalism-restoration.md`. The owner
rejected the earlier Reveal interpretation: Swap must extract an object,
bring it in front, and lay it on top, keeping each surface's writing attached.
A theme that cannot remain physically coherent and readable is removed from
selection, not rescued through magical text changes or distorted materials.

**Theme Instance**:
A selected Theme Pack and its deterministic per-location identities applied throughout one exploration. Unpinned loads use Original; explicit theme URLs retain their selected pack across refreshes.
_Avoid_: Theme, random skin

**Theme Engine**:
The isolated system that discovers, validates, selects, and applies Theme Packs while preserving the Interaction Structure.
_Avoid_: Theme switcher, theme script

**Depth Layer**:
An optional, ordered, pointer-inert Theme Pack background asset with a bounded movement factor from fixed viewport (`0`) to full Board movement (`1`). Depth Layers may decorate a world but never contain tiles, labels, relationships, focus surfaces, hit targets, or documents.
_Avoid_: Parallax navigation, moving content plane

**Action Treatment**:
The pack-selected visual grammar for the invariant expanded-tile destination link. `annotation` renders the action as writing on the object; `marker` renders a larger, high-contrast in-world label. Its destination, placement, keyboard behavior, and minimum touch size remain part of the Interaction Structure.
_Avoid_: Theme-specific button logic, alternate navigation

**Interaction Structure**:
The invariant point-and-click, tile-based navigation: the same spatial layout rules, Parent/Child relationships, Neighborhood limits, destinations, input behavior, and document flow across every Board Theme. Themes may change appearance and visual animation, but never rearrange the navigation or alter how the Viewer moves through it; neighboring destinations remain visible and directly actionable throughout.
_Avoid_: Theme, visual treatment

**Real-World Coherence**:
The rule that a Board Theme's scene, objects, surfaces, connecting cues, and motion form a physically believable whole aligned with the owner's design instructions. Changes in displayed information have a coherent visible cause rather than silently rewriting an unchanged surface; backgrounds, connections, and opened Documents belong to the scene without requiring an invented explanation.
_Avoid_: Abstract visual consistency, arbitrary decoration

**Grounding Review**:
A Portfolio-specific assessment of a proposed or rendered Board Theme against Real-World Coherence and the owner's established design constraints. It judges the scene and its transitions, not merely whether its assets validate or its text fits.
_Avoid_: General agent audit, aesthetic approval, geometry-only validation

**Personal Mark**:
The stable visual identifier representing David across themes and asset sizes. A Board Theme may alter its border, badge, or surrounding treatment without replacing its recognizable core.
_Avoid_: Theme logo, social-preview image

**Document Grammar**:
The uniform structure and visual language shared by opened documents to keep the self-portrait coherent and maintainable as it grows.
_Avoid_: Bespoke microsite, page-specific framework

**Viewer Artifact**:
A bounded, Theme-Pack-selected real-world carrier surrounding an opened Document, such as a field notebook, observation window, or expedition log. Its presentation is pack-owned while its Document flow and controls remain invariant.
_Avoid_: Shell prototype, page skin, theme-specific viewer

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
