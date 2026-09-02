"""Authoritative mapping between Destination Links, Documents, and Board Sections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioDocument:
    route: str
    board_title: str
    page_title: str
    template: str

    def destination_state(self) -> dict[str, str]:
        return {"route": self.route, "title": self.board_title}


DOCUMENTS = (
    PortfolioDocument("/jobs", "Work Experience", "Work Experience", "pages/jobs.html"),
    PortfolioDocument("/education/college", "College", "College", "pages/education/college.html"),
    PortfolioDocument(
        "/education/early_education", "Early Education", "Early Education",
        "pages/education/early_education.html",
    ),
    PortfolioDocument(
        "/education/agile_report", "College", "Agile Management Report",
        "pages/education/agile_report.html",
    ),
    PortfolioDocument("/hobbies/tennis", "Tennis", "Tennis", "pages/hobbies/tennis.html"),
    PortfolioDocument("/hobbies/gaming", "Gaming", "Gaming", "pages/hobbies/gaming.html"),
    PortfolioDocument(
        "/hobbies/3d_printing/puzzles", "Puzzles", "Puzzles",
        "pages/hobbies/3d_printing/puzzles.html",
    ),
    PortfolioDocument(
        "/hobbies/3d_printing/other_models", "Other Models", "Other Models",
        "pages/hobbies/3d_printing/other_models.html",
    ),
    PortfolioDocument(
        "/projects/programs", "Programs", "Programs", "pages/projects/programs.html"
    ),
    PortfolioDocument(
        "/projects/nba_predictions", "Programs", "NBA Predictions",
        "pages/projects/nba_predictions.html",
    ),
    PortfolioDocument(
        "/projects/websites/digital_planner", "Digital Planner", "Digital Planner",
        "pages/projects/websites/digital_planner.html",
    ),
    PortfolioDocument(
        "/projects/websites/scribblescan", "ScribbleScan", "ScribbleScan",
        "pages/projects/websites/scribblescan.html",
    ),
    PortfolioDocument(
        "/projects/websites/this_website", "This website", "This Website",
        "pages/projects/websites/this_website.html",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v1", "This website", "This Website v1",
        "pages/projects/websites/this_website/v1.html",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v2", "This website", "This Website v2",
        "pages/projects/websites/this_website/v2.html",
    ),
    PortfolioDocument(
        "/projects/websites/this_website/v3", "This website", "This Website v3",
        "pages/projects/websites/this_website/v3.html",
    ),
)

DOCUMENTS_BY_ROUTE = {document.route: document for document in DOCUMENTS}


def document_for_route(route: str) -> PortfolioDocument | None:
    normalized = "/" + route.strip("/")
    return DOCUMENTS_BY_ROUTE.get(normalized)


def portfolio_state(
    initial_document: PortfolioDocument | None = None,
) -> dict[str, object]:
    return {
        "initialDestination": (
            initial_document.destination_state() if initial_document else None
        ),
        "destinationMap": {
            document.route: document.board_title for document in DOCUMENTS
        },
        "documentPrefix": "/_documents",
    }
