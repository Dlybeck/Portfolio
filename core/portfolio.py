"""Public routes: each one opens the notebook at one page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioDocument:
    route: str
    page: str  # id of the notebook page this route opens (see core/notebook.py)
    page_title: str
    description: str
    anchor: str | None = None  # a part of that page to scroll to or slide to


DOCUMENTS = (
    PortfolioDocument(
        "/jobs", "work", "Work Experience",
        "Explore David Lybeck's professional history, including his Innovation AI Developer role at Denali Advanced Integration since August 2025.",
    ),
    PortfolioDocument(
        "/education/college", "school", "College",
        "Explore David Lybeck's computer science degree, mathematics minor, coursework, tennis, and campus activities at the University of Puget Sound.",
    ),
    PortfolioDocument(
        "/education/early_education", "school", "Early Education",
        "Visit the schools and early education history that preceded David Lybeck's computer science work and personal projects.",
        anchor="early-education",
    ),
    PortfolioDocument(
        "/education/agile_report", "school", "Agile Management Report",
        "Read David Lybeck's 2024 report exploring agile management strategies, benefits, and limitations.",
        anchor="agile-report",
    ),
    PortfolioDocument(
        "/hobbies/tennis", "tennis", "Tennis",
        "Explore David Lybeck's lifelong interest in competitive tennis, from school teams to current player profiles.",
    ),
    PortfolioDocument(
        "/hobbies/gaming", "gaming", "Gaming",
        "Browse a personal collection of video games David Lybeck has especially enjoyed playing.",
    ),
    PortfolioDocument(
        "/hobbies/3d_printing/puzzles", "printing", "Puzzles",
        "Explore interactive models of puzzle boxes designed and 3D printed by David Lybeck.",
        anchor="puzzles",
    ),
    PortfolioDocument(
        "/hobbies/3d_printing/other_models", "printing", "Other Models",
        "Explore interactive models of phone cases, organizers, and other objects designed by David Lybeck for 3D printing.",
        anchor="other-models",
    ),
    PortfolioDocument(
        "/projects/programs", "programs", "Programs",
        "Explore current software projects, earlier experiments, and selected coursework built by David Lybeck.",
    ),
    PortfolioDocument(
        "/projects/nba_predictions", "nba", "NBA Predictions",
        "Try an NBA game prediction demo built from a custom basketball statistics dataset and a neural network model.",
    ),
    PortfolioDocument(
        "/projects/websites/digital_planner", "planner", "Digital Planner",
        "Explore a collaborative digital planner project combining calendars and task management in one interface.",
    ),
    PortfolioDocument(
        "/projects/websites/scribblescan", "scribblescan", "ScribbleScan",
        "Explore the preserved ScribbleScan demo and development history of David Lybeck's handwriting digitization project.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website", "site", "This Website",
        "Explore how David Lybeck hand-built this interactive portfolio and how its unusual navigation evolved.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v1", "site", "This Website v1",
        "See the first hand-coded generation of DavidLybeck.com evolve from a static layout into an exploratory map.",
        anchor="v1",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v2", "site", "This Website v2",
        "See the second hand-coded generation of DavidLybeck.com turn its map into the portfolio's primary interface.",
        anchor="v2",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v3", "site", "This Website v3",
        "See the third generation of DavidLybeck.com evolve from handwritten notes on a tabletop into seven visual themes.",
        anchor="v3",
    ),
)

DOCUMENTS_BY_ROUTE = {document.route: document for document in DOCUMENTS}


def document_for_route(route: str) -> PortfolioDocument | None:
    return DOCUMENTS_BY_ROUTE.get("/" + route.strip("/"))
