"""The private-beta Cloud Build config: a text check of the settings that matter (no YAML library needed)."""

from __future__ import annotations

from pathlib import Path

CONFIG = (Path(__file__).resolve().parent.parent / "cloudbuild.beta.yaml").read_text()
IMAGE = "us-west1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/portfolio-beta:$BUILD_ID"


def test_the_beta_image_goes_to_artifact_registry_in_us_west1() -> None:
    assert CONFIG.count(IMAGE) == 4  # build, push, deploy and the images list


def test_the_beta_service_is_its_own_service_with_a_secret_passcode_and_small_scale() -> None:
    for line in ("- 'portfolio-beta'", "- 'us-west1'", "- '--allow-unauthenticated'", "- '--min-instances'", "- '--max-instances'"):
        assert line in CONFIG, line
    assert "- '0'" in CONFIG and "- '2'" in CONFIG
    assert "- 'BETA_PASSCODE=PORTFOLIO_BETA_PASSCODE:latest'" in CONFIG
    assert "--set-env-vars" not in CONFIG  # the passcode comes only from Secret Manager, never from the repo
    assert "- 'portfolio'" not in CONFIG  # never touches the production service


def test_the_build_logs_to_cloud_logging_so_it_works_with_any_service_account() -> None:
    assert "logging: CLOUD_LOGGING_ONLY" in CONFIG
