---
id: "00"
title: Preserve and extend the living portfolio
status: ready-for-agent
type: spec
phases:
  - 1
  - 2
child_issues:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
  - "06"
  - "07"
  - "08"
---

# Preserve and extend the living portfolio

## Problem Statement

The portfolio already succeeds at its central purpose: it is a hand-authored, living, explorable self-portrait whose spatial Board invites people to discover how it works. It is not intended to behave like a conventional résumé, professional landing page, or guided product funnel. Changes that optimize it for immediate résumé-style consumption would erase part of what makes it personal.

The experience nevertheless has accidental barriers that are not part of that intent. Historical images are missing, some content and markup contain mechanical errors, direct content links can detach documents from the Board that gives them context, visible controls are not consistently available to keyboard and assistive-technology users, reduced-motion preferences are not honored, and the site lacks a reliable professional discovery layer for search and social sharing. The codebase also needs a safe way to explore future visual themes without losing the current design or allowing presentation experiments to alter the navigation model.

The challenge is to repair those defects and add inclusive discovery while preserving the authored experience: self-guided exploration, the parent-child Board, the conversational voice, historical material, default motion, and the current visual theme.

## Solution

Deliver the work in two phases around one visitor-visible Board contract.

Phase 1 establishes a trustworthy canonical portfolio. It restores historical content, makes every canonical destination reconstruct its Board context, gives the visible Neighborhood a coherent keyboard model, supplies accurate accessibility semantics and reduced-motion adaptation, and adds professional search and social metadata without rewriting the visible site into a résumé.

Phase 2 begins only after Phase 1 is complete. It introduces a development-only Board Theme selector and a theme boundary that can restyle both the Board and its documents without changing content, topology, URLs, controls, navigation sequence, responsive structure, or general interaction behavior. An alternate shared Document Grammar is then prototyped against dissimilar content and compared with the unchanged canonical theme. Nothing experimental becomes public without separate owner approval.

Both phases are accepted primarily through the highest available seam: a real visitor entering and operating the rendered portfolio in a browser. Route-contract, asset, markup, and metadata checks support diagnosis and fast feedback, but the externally observable Board experience defines correctness.

## User Stories

1. As a first-time Viewer, I want to understand that the Board is interactive after a quick glance, so that I can begin exploring without a tutorial.
2. As a curious Viewer, I want to discover the navigation model myself, so that learning the Board remains part of the experience.
3. As a Viewer who needs a clue, I want any hint to feel like part of Home, so that the portfolio does not turn into a guided product tour.
4. As a returning Viewer, I want Home to remain the root of the experience, so that I always have a recognizable place to return to.
5. As a Viewer, I want each Board location to show a deliberately limited Neighborhood, so that the unusual navigation remains approachable.
6. As a Viewer, I want a Neighborhood to contain no more than its centered Section, one Parent, and three Children, so that exploration stays curated.
7. As a Viewer, I want professional, educational, recreational, and historical work to coexist, so that I encounter a person rather than a résumé taxonomy.
8. As a Viewer, I want old portfolio generations to remain explorable, so that I can see how the author and the site evolved.
9. As a Viewer of historical work, I want referenced images to load, so that the retrospective is complete rather than accidentally broken.
10. As the portfolio Owner, I want missing historical media recovered from trustworthy evidence where practical, so that repairs preserve the original artifact.
11. As the portfolio Owner, I want ambiguous replacements or removals returned to me for review, so that an automated repair does not rewrite my history.
12. As the portfolio Owner, I want obvious spelling, title, identifier, label, and markup errors corrected, so that accidents are not mistaken for intentional personality.
13. As the portfolio Owner, I want my conversational voice preserved, so that cleanup does not make the site sound generic or corporate.
14. As the portfolio Owner, I want Technology Services shown as ending in May 2025, so that the confirmed employment timeline is accurate.
15. As the portfolio Owner, I want historical ScribbleScan performance claims preserved on their original pages, so that the project remains represented as it was authored.
16. As a Viewer following a shared link, I want the requested document to open inside its correct Board location, so that I retain the context of the self-portrait.
17. As a Viewer refreshing a content destination, I want the same Board location and document restored, so that the URL is dependable.
18. As a Viewer following a link inside a document, I want the next destination to remain within the Board experience, so that navigation never unexpectedly becomes a detached website.
19. As a Viewer, I want Home, Open, Close, Back, and nested document actions to work from every supported entry point, so that I do not become stranded.
20. As a Viewer, I want content routes to avoid embedding and redirect loops, so that direct destinations load reliably.
21. As a pointer or touch user, I want the interactions I already understand to keep working, so that accessibility improvements do not replace the established experience.
22. As a keyboard user, I want focus to follow the currently visible Neighborhood, so that hidden implementation details do not create a confusing tab order.
23. As a keyboard user, I want no more than the visible Parent, Children, and actionable center in my Board focus cycle, so that keyboard and visual navigation describe the same place.
24. As a keyboard user, I want Enter or Space to move to a neighbor or open the centered document, so that activation is predictable.
25. As a keyboard user inside nested document content, I want Escape to return one document level, so that I can back out progressively.
26. As a keyboard user in a top-level document, I want Escape to close the document, so that I return to its Board location.
27. As a keyboard user on the Board, I want Escape to move one Parent step toward Home, so that the spatial hierarchy has a consistent reverse action.
28. As a keyboard user at Home, I want Escape to do nothing, so that the root behaves as a stable endpoint.
29. As a keyboard user, I want a visible focus treatment that fits the current theme, so that I can locate myself without the interface feeling bolted on.
30. As an assistive-technology user, I want Home, Close, Back, and other actions exposed as semantic controls, so that their roles and names are understandable.
31. As an assistive-technology user, I want meaningful images and embedded documents described accurately, so that important content is not silent.
32. As an assistive-technology user, I want decorative media ignored, so that visual texture does not become noise.
33. As a Viewer who requests reduced motion, I want Board and document transitions adapted to that preference, so that I can explore comfortably.
34. As a Viewer who has not requested reduced motion, I want the current animations preserved, so that the canonical experience retains its character.
35. As a recruiter searching for David Lybeck, I want an accurate professional title and description, so that I understand the current professional identity before choosing to explore.
36. As a search engine, I want a stable canonical identity for the portfolio and its linkable destinations, so that duplicate or detached representations are avoided.
37. As a search engine, I want structured Person identity links for the approved GitHub and LinkedIn profiles, so that public identities can be associated correctly.
38. As the portfolio Owner, I want Denali Advanced Integration represented as my employer since August 2025, so that search metadata reflects my current role.
39. As the portfolio Owner, I want my email excluded from structured metadata, so that professional discovery does not create unnecessary exposure.
40. As the portfolio Owner, I want numerical and `industry-leading` ScribbleScan claims excluded from metadata, so that historical promotional copy is not amplified as a current search claim.
41. As someone sharing the portfolio, I want a stable wide preview of the Home Board, so that the link communicates the site's personality on social platforms.
42. As a recipient of a shared portfolio link, I want an accurate title, description, and preview image, so that I know what I am about to open.
43. As the portfolio Owner, I want the existing Personal Mark used for the initial social preview, so that metadata work does not force an unfinished logo decision.
44. As the portfolio Owner, I want the current Board Theme preserved as the canonical public default, so that experimentation cannot erase a design I already like.
45. As a developer, I want to select themes from the navigation area during development, so that I can compare alternatives without editing source for each trial.
46. As a public Viewer, I want unfinished theme controls absent from the deployed experience, so that development machinery does not leak into the portfolio.
47. As a developer, I want unknown themes to fall back to the canonical theme, so that stale or malformed selection state cannot break the site.
48. As a developer, I want themes to own presentation without owning navigation or content, so that variants remain comparable versions of the same portfolio.
49. As the portfolio Owner, I want Board and document styling grouped into the same theme effort, so that a visual direction can feel coherent across the whole experience.
50. As the portfolio Owner, I want an alternate Document Grammar tested on at least two dissimilar content types, so that a redesign proves generality rather than flattering one page.
51. As the portfolio Owner, I want desktop and phone comparisons between the canonical and experimental treatments, so that I can judge them concretely.
52. As the portfolio Owner, I want the alternate treatment to remain development-only until I approve it, so that a prototype is not mistaken for a redesign decision.
53. As the portfolio Owner, I want the Phase 1 baseline completed before theme work begins, so that experiments are evaluated against a trustworthy and accessible product.
54. As the portfolio Owner, I want one integrated acceptance receipt after both phases, so that I can see what passed, what failed, and what still needs my judgment.
55. As the portfolio Owner, I want commits, pushes, publication, and deployment treated as separate approvals, so that planning and implementation do not silently change the live portfolio.

## Implementation Decisions

- The portfolio is a living, explorable self-portrait. It will not be redesigned as a résumé, hiring funnel, or conventional professional landing page.
- The Viewer is the primary actor. The interface should be novel while remaining understandable at a glance, and exploration should remain self-directed.
- The Board remains the primary navigation module, with Home as its root and a parent-child topology as its organizing model.
- The domain term **Neighborhood** means the currently centered Section plus one Parent and up to three Children. It contains no more than five visible Sections.
- The domain term **Document** means content opened within its Board context. Public content destinations must not present Documents as detached standalone sites.
- Canonical destination handling will map each linkable Document to its Board location, reconstruct that location on entry, and open the Document.
- The internal Document-rendering interface may differ from its canonical public destination to avoid redirects or recursive embedding. The internal representation is not itself a public navigation contract.
- Perfect reproduction of every intermediate Board movement through browser Back and Forward is not required. Correct canonical entry, Home behavior, and visible actions are required.
- Home, Open, Close, Back, and nested Document actions will share explicit navigation semantics across supported entry states.
- Historical repair work will distinguish mechanical correction from editorial change. Mechanical defects may be fixed directly; disputed claims, unconfirmed dates, tone, and historical meaning require owner review.
- Missing historical assets will be recovered from reproducible evidence where practical. Unrecoverable or ambiguous media will not be silently removed or substituted.
- Technology Services ends in May 2025. Other employment or historical changes require separate evidence or owner confirmation.
- ScribbleScan's historical performance language remains visible on its authored pages but is excluded from structured and search-facing metadata.
- Keyboard navigation will be derived from the current Neighborhood state, not incidental rendered order or the complete offscreen Board graph.
- The centered Section participates in the keyboard cycle only when it exposes an actionable Document.
- Enter and Space share the pointer activation semantics for moving or opening.
- Escape is hierarchical: nested Document back, top-level Document close, Board Parent, then no action at Home.
- Semantic interactive elements will represent Home, Close, Back, and other actions. Focus styling belongs to the active theme and appears through focus-visible behavior.
- Images will be classified as meaningful or decorative before alternatives are assigned. Embedded Documents and interactive controls receive names that describe their actual purpose.
- Reduced motion is controlled only by the visitor's operating-system or browser preference. No separate accessibility mode or settings panel will be introduced.
- The default animated experience remains unchanged for visitors who have not requested reduced motion.
- The canonical site identity is `https://davidlybeck.com/`.
- The primary search title is `David Lybeck | Innovation AI Developer`.
- The primary search description is `David Lybeck is an Innovation AI Developer and software builder exploring AI, handwriting recognition, 3D design, tennis, and personal projects through an interactive portfolio.`
- Professional metadata represents David Lybeck as an Innovation AI Developer at Denali Advanced Integration since August 2025.
- Person structured data associates only the approved GitHub and LinkedIn identities. It does not contain an email address.
- Canonical, destination-specific, Open Graph, social-preview, and Person metadata will be derived from a small authoritative identity model rather than the stale bundled résumé.
- The initial social preview is a stable wide rendering of the canonical Home Board and uses the existing Personal Mark.
- The current Board Theme is the canonical theme and comparison baseline.
- A Board Theme may change presentation across the Board and Documents, including backgrounds, textures, colors, borders, typography, controls, and page styling.
- A Board Theme may not change topology, content, URLs, control meaning, navigation sequence, keyboard behavior, responsive structural rules, or the general user experience.
- Theme registration, selection, and fallback will be centralized behind one theme boundary rather than spread through navigation logic.
- The theme selector appears only during development and is absent or disabled in deployment-equivalent builds.
- Missing or unknown theme selections fall back to the canonical Board Theme.
- A diagnostic development theme may prove the selector mechanics. Random public theme assignment is not part of this effort.
- The shared Document Grammar remains uniform for maintainability. An alternate grammar must serve at least two dissimilar Documents without page-specific navigation or structural exceptions.
- Phase 1 comprises Historical Work integrity, Board-aware destinations, keyboard operation, accessible adaptation, and professional discovery.
- Phase 2 comprises the development theme system, alternate Document Grammar prototype, and integrated acceptance gate.
- Phase 2 is blocked until every Phase 1 ticket is complete.
- The implementation is decomposed into child issues 01 through 08. Each child issue must contribute its own externally observable verification rather than relying only on the final gate.
- This specification and its tickets authorize planning only. Source changes, commits, pushes, publication, and deployment require separate authorization.

## Testing Decisions

- The primary and preferred test seam is the complete portfolio as a Viewer experiences it in a real browser. Tests enter through Home or a canonical destination and observe the rendered Board, open Document, visible controls, URL behavior, keyboard behavior, accessibility semantics, metadata, and responsive presentation.
- Tests will assert external behavior rather than private JavaScript functions, template organization, CSS implementation details, or internal state representation.
- The same visitor-visible behavioral contract will run against the canonical Board Theme and each registered development theme. Theme-specific assertions will be limited to presentation outcomes and production visibility.
- Browser coverage will include representative desktop and phone viewports because responsive spatial behavior is part of the product contract.
- The browser matrix will cover pointer, touch where supported by the harness, forward keyboard operation, reverse keyboard operation, and every level of the Escape hierarchy.
- Canonical destination tests will cover fresh entry, refresh, Document opening, in-Document navigation, Home, Close, Back, and loop prevention.
- Accessibility tests will inspect semantic roles, accessible names, image alternatives, embedded Document titles, focus visibility, and hidden/offscreen focus exclusion through rendered behavior.
- Motion tests will compare the default preference with reduced-motion preference and verify that content and navigation remain available in both states.
- Metadata tests will inspect the public response and rendered page for canonical identity, destination-specific descriptions, social metadata, Person structured data, approved identity links, excluded email, and excluded performance claims.
- Theme tests will exercise canonical defaulting, development selection, unknown-theme fallback, preservation of the Board interaction contract, and absence of the selector in a deployment-equivalent build.
- Visual comparisons will use the canonical desktop and phone experience as the baseline. Expected repairs may change affected content, but unrelated Board composition and default presentation should remain equivalent.
- Supporting route-contract tests may exercise the server boundary directly for fast verification of canonical mappings, response status, redirect behavior, and internal rendering separation.
- Supporting static checks may detect missing local assets, malformed references, duplicate identifiers, missing alternatives, missing frame titles, and invalid metadata. These checks are diagnostic aids and do not replace the browser seam.
- Visible external links will be checked with bounded network-aware validation and distinguished from failures caused by remote availability or access policy.
- The codebase does not currently provide a mature product-level automated test convention. New coverage should therefore establish a small, cohesive browser contract rather than multiplying low-level seams. Existing framework route-testing facilities may support fast checks beneath it.
- Each child issue must leave repeatable validation for the behavior it delivers. The final acceptance issue reruns and integrates those checks; it does not postpone all verification until the end.
- The final receipt will record environment, reproducible commands, phase results, unresolved failures, and owner decisions. It will explicitly state whether any commit, push, publication, or deployment occurred.

## Out of Scope

- Replacing the portfolio with a résumé site, professional landing page, or hiring funnel.
- Adding an external tutorial, onboarding sequence, guided tour, or instruction-heavy navigation.
- Removing coursework, personal material, hobbies, or old projects merely because they are not current professional work.
- Rewriting the author's conversational voice or polishing historical content into uniform corporate copy.
- Rewriting unverified dates, claims, employment facts, or historical meaning without owner review.
- Removing ScribbleScan's historical on-page performance claims as part of metadata cleanup.
- Replacing or rewriting the stale bundled résumé.
- Designing a new Personal Mark or producing its complete favicon, navigation, full-resolution, and social derivative system.
- Guaranteeing perfect browser Back and Forward reconstruction of every intermediate spatial movement.
- Adding a separate accessibility mode, accessibility settings panel, or default reduction of the canonical motion.
- Publicly exposing the development theme selector.
- Randomly assigning themes to public visitors.
- Adopting an alternate Board Theme or Document Grammar without a separate owner decision.
- Changing Board topology, content, URLs, control meaning, navigation sequence, responsive structural rules, or general interaction behavior per theme.
- Committing, pushing, publishing, or deploying the implementation without separate authorization.

## Further Notes

- This specification synthesizes the confirmed September 2026 design discussion, the portfolio design plan, and the four accepted architectural decisions governing self-discovered navigation, Board-aware content links, canonical theming, and hierarchical keyboard behavior.
- `Person.sameAs` is structured-data vocabulary for associating a person with authoritative public identity pages. In this portfolio it is limited to the approved GitHub and LinkedIn profiles.
- A social preview is the title, description, and image shown when a portfolio link is shared by services that consume Open Graph or equivalent metadata.
- The bundled résumé predates the Denali role and must not be treated as the authoritative source for current metadata.
- Phase 1 child issues are 01 through 05. Phase 2 child issues are 06 through 08.
- The final acceptance issue is evidence-oriented and does not itself authorize deployment.
