"""Authoritative mapping between Destination Links, Documents, and Board Sections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioDocument:
    route: str
    board_title: str
    page_title: str
    template: str
    description: str

    def destination_state(self) -> dict[str, str]:
        return {"route": self.route, "title": self.board_title}


DOCUMENTS = (
    PortfolioDocument(
        "/jobs", "Work Experience", "Work Experience", "pages/jobs.html",
        "Explore David Lybeck's professional history, including his Innovation AI Developer role at Denali Advanced Integration since August 2025.",
    ),
    PortfolioDocument(
        "/education/college", "College", "College", "pages/education/college.html",
        "Explore David Lybeck's computer science degree, mathematics minor, coursework, tennis, and campus activities at the University of Puget Sound.",
    ),
    PortfolioDocument(
        "/education/early_education", "Early Education", "Early Education",
        "pages/education/early_education.html",
        "Visit the schools and early education history that preceded David Lybeck's computer science work and personal projects.",
    ),
    PortfolioDocument(
        "/education/agile_report", "College", "Agile Management Report",
        "pages/education/agile_report.html",
        "Read David Lybeck's 2024 report exploring agile management strategies, benefits, and limitations.",
    ),
    PortfolioDocument(
        "/hobbies/tennis", "Tennis", "Tennis", "pages/hobbies/tennis.html",
        "Explore David Lybeck's lifelong interest in competitive tennis, from school teams to current player profiles.",
    ),
    PortfolioDocument(
        "/hobbies/gaming", "Gaming", "Gaming", "pages/hobbies/gaming.html",
        "Browse a personal collection of video games David Lybeck has especially enjoyed playing.",
    ),
    PortfolioDocument(
        "/hobbies/3d_printing/puzzles", "Puzzles", "Puzzles",
        "pages/hobbies/3d_printing/puzzles.html",
        "Explore interactive models of puzzle boxes designed and 3D printed by David Lybeck.",
    ),
    PortfolioDocument(
        "/hobbies/3d_printing/other_models", "Other Models", "Other Models",
        "pages/hobbies/3d_printing/other_models.html",
        "Explore interactive models of phone cases, organizers, and other objects designed by David Lybeck for 3D printing.",
    ),
    PortfolioDocument(
        "/projects/programs", "Programs", "Programs", "pages/projects/programs.html",
        "Explore software experiments, class projects, and personal programs built by David Lybeck.",
    ),
    PortfolioDocument(
        "/projects/nba_predictions", "Programs", "NBA Predictions",
        "pages/projects/nba_predictions.html",
        "Try an NBA game prediction demo built from a custom basketball statistics dataset and a neural network model.",
    ),
    PortfolioDocument(
        "/projects/websites/digital_planner", "Digital Planner", "Digital Planner",
        "pages/projects/websites/digital_planner.html",
        "Explore a collaborative digital planner project combining calendars and task management in one interface.",
    ),
    PortfolioDocument(
        "/projects/websites/scribblescan", "ScribbleScan", "ScribbleScan",
        "pages/projects/websites/scribblescan.html",
        "Explore the preserved ScribbleScan demo and development history of David Lybeck's handwriting digitization project.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website", "This website", "This Website",
        "pages/projects/websites/this_website.html",
        "Explore how David Lybeck hand-built this interactive portfolio and how its unusual navigation evolved.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v1", "This website", "This Website v1",
        "pages/projects/websites/this_website/v1.html",
        "See the first hand-coded generation of DavidLybeck.com evolve from a static layout into an exploratory map.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v2", "This website", "This Website v2",
        "pages/projects/websites/this_website/v2.html",
        "See the second hand-coded generation of DavidLybeck.com turn its map into the portfolio's primary interface.",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v3", "This website", "This Website v3",
        "pages/projects/websites/this_website/v3.html",
        "See the current paper-and-chalkboard generation of DavidLybeck.com take shape through three development milestones.",
    ),
)

DOCUMENTS_BY_ROUTE = {document.route: document for document in DOCUMENTS}


def document_for_route(route: str) -> PortfolioDocument | None:
    normalized = "/" + route.strip("/")
    return DOCUMENTS_BY_ROUTE.get(normalized)


def portfolio_state(
    initial_document: PortfolioDocument | None = None,
) -> dict[str, object]:
    board_routes: dict[str, str] = {}
    for document in DOCUMENTS:
        board_routes.setdefault(document.board_title, document.route)

    return {
        "initialDestination": (
            initial_document.destination_state() if initial_document else None
        ),
        "destinationMap": {
            document.route: document.board_title for document in DOCUMENTS
        },
        "documentTitles": {
            document.route: document.page_title for document in DOCUMENTS
        },
        "boardRoutes": board_routes,
        "documentPrefix": "/_documents",
    }
