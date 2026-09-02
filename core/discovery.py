"""Authoritative public identity and search/social metadata."""

from __future__ import annotations

from dataclasses import dataclass

from core.portfolio import PortfolioDocument


SITE_URL = "https://davidlybeck.com"
PRIMARY_TITLE = "David Lybeck | Innovation AI Developer"
PRIMARY_DESCRIPTION = (
    "David Lybeck is an Innovation AI Developer and software builder exploring "
    "AI, handwriting recognition, 3D design, tennis, and personal projects "
    "through an interactive portfolio."
)
SOCIAL_IMAGE_URL = f"{SITE_URL}/static/images/social/home-board.webp"


@dataclass(frozen=True, slots=True)
class DiscoveryMetadata:
    title: str
    description: str
    canonical_url: str
    social_image_url: str = SOCIAL_IMAGE_URL
    social_image_alt: str = "David Lybeck's interactive portfolio Board"


PERSON_SCHEMA = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": "David Lybeck",
    "url": f"{SITE_URL}/",
    "jobTitle": "Innovation AI Developer",
    "description": (
        "Innovation AI Developer at Denali Advanced Integration since August "
        "2025 and software builder behind an interactive personal portfolio."
    ),
    "worksFor": {
        "@type": "Organization",
        "name": "Denali Advanced Integration",
    },
    "sameAs": [
        "https://github.com/Dlybeck",
        "https://www.linkedin.com/in/davidlybeck/",
    ],
}


def metadata_for(document: PortfolioDocument | None = None) -> DiscoveryMetadata:
    if document is None:
        return DiscoveryMetadata(
            title=PRIMARY_TITLE,
            description=PRIMARY_DESCRIPTION,
            canonical_url=f"{SITE_URL}/",
        )

    return DiscoveryMetadata(
        title=f"{document.page_title} | David Lybeck",
        description=document.description,
        canonical_url=f"{SITE_URL}{document.route}",
    )
