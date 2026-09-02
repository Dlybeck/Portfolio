---
id: "05"
title: Publish the Professional Discovery Layer
status: resolved
phase: 1
blocked_by:
  - "01"
  - "02"
---

# Publish the Professional Discovery Layer

## Context

The visible portfolio remains personal and exploratory, but search engines, recruiters, social platforms, friends, and people arriving by name search need a concise and accurate professional discovery layer. Metadata must not turn the experience itself into a résumé or amplify historical performance claims.

## Requirements

- Use `https://davidlybeck.com/` as the canonical site identity.
- Use `David Lybeck | Innovation AI Developer` as the primary site title.
- Use this primary description: `David Lybeck is an Innovation AI Developer and software builder exploring AI, handwriting recognition, 3D design, tennis, and personal projects through an interactive portfolio.`
- Represent the Denali Innovation AI Developer role as beginning in August 2025.
- Publish Person structured data with these identity links:
  - GitHub: `https://github.com/Dlybeck`
  - LinkedIn: `https://www.linkedin.com/in/davidlybeck/`
- Do not include an email address in structured metadata.
- Do not include ScribbleScan metrics, performance claims, or `industry-leading` language in metadata.
- Provide canonical destinations and useful page-specific titles and descriptions where content is independently linkable.
- Provide Open Graph and equivalent social metadata.
- Create a stable, wide social preview of the Home Board using the existing logo for now.
- Keep résumé replacement and logo redesign out of scope.
- Add validation for canonical links, structured data, social metadata, and accidental private information.

## Suggested approach

Build metadata from a small authoritative identity model, then derive route-specific values without copying stale résumé content. Render the social preview from a stable Home composition rather than relying on a live animated frame.

## Done when

- Site and destination metadata emit the agreed identity and canonical URLs.
- Person structured data validates and links only the approved public profiles.
- Social sharing produces the intended Home Board preview and accurate copy.
- No email address or excluded performance language appears in metadata.
- Metadata validation and a representative search/social preview inspection pass.
