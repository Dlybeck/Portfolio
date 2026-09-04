from pathlib import Path


def test_cloud_run_deploy_enables_themes_without_replacing_existing_environment() -> None:
    deployment = Path("cloudbuild.yaml").read_text()

    assert "- '--update-env-vars'" in deployment
    assert "- 'THEMES_ENABLED=True'" in deployment
    assert "- '--set-env-vars'" not in deployment
