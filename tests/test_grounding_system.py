"""Exercise review evidence failure modes, not an agent's choice of wording."""
import json
from pathlib import Path
import subprocess

import pytest

from scripts import check_grounding as review


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '--allow-empty', '-qm', 'Fixture'], cwd=root, check=True)
    (root / 'static').mkdir()
    (root / 'static' / 'scene.svg').write_text('<svg/>')
    return root


def successful_command(command, **kwargs):
    kwargs['stdout'].write('mechanical check executed\n')
    for arg in command:
        if arg.startswith('--junitxml='):
            Path(arg.split('=', 1)[1]).write_text(
                '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="0"/></testsuites>')
    return subprocess.CompletedProcess(command, 0)


@pytest.fixture
def receipt(project, tmp_path, monkeypatch):
    # Mock only launched checks, never fingerprints or receipt validation.
    real_run = subprocess.run
    def run(command, **kwargs):
        if command[0] == 'git':
            return real_run(command, **kwargs)
        return successful_command(command, **kwargs)
    monkeypatch.setattr(review.subprocess, 'run', run)
    output = tmp_path / 'evidence'
    assert review.run_checks(output, 1, project) == 0
    return output / 'receipt.json'


def test_success_still_requires_visual_review(receipt, project):
    assert review.verify_receipt(receipt, project) == []
    assert json.loads(receipt.read_text())['visual_review'] == 'required'


@pytest.mark.parametrize('change', ['source', 'rules', 'guard', 'new-asset', 'deleted-asset'])
def test_stale_evidence_is_rejected(receipt, project, change):
    if change == 'source':
        (project / 'static/scene.svg').write_text('<svg><circle/></svg>')
    elif change == 'rules':
        (project / 'AGENTS.md').write_text('New owner rule')
    elif change == 'guard':
        (project / 'scripts').mkdir()
        (project / 'scripts/check_canonical_fidelity.py').write_text('print("PASS")')
    elif change == 'new-asset':
        (project / 'static/extra.svg').write_text('<svg/>')
    else:
        (project / 'static/scene.svg').unlink()
    assert any('current source' in e for e in review.verify_receipt(receipt, project))


@pytest.mark.parametrize('change', ['missing-log', 'edited-log', 'missing-stage',
                                   'visual-pass', 'incomplete', 'wrong-command', 'missing-xml'])
def test_misleading_receipts_do_not_pass(receipt, project, change):
    data = json.loads(receipt.read_text())
    if change == 'missing-log':
        (receipt.parent / 'fit-and-material.log').unlink()
    elif change == 'edited-log':
        (receipt.parent / 'fit-and-material.log').write_text('PASS')
    elif change == 'missing-stage':
        data['checks'].pop()
    elif change == 'visual-pass':
        data['visual_review'] = 'approved'
    elif change == 'incomplete':
        data['status'] = 'incomplete'
    elif change == 'wrong-command':
        data['checks'][0]['command'] = ['echo', 'PASS']
    elif change == 'missing-xml':
        data['checks'][0]['artifacts'].pop('fit-and-material.xml')
    receipt.write_text(json.dumps(data))
    assert review.verify_receipt(receipt, project)


@pytest.mark.parametrize('mode', ['failure', 'timeout', 'skipped', 'empty'])
def test_failed_or_missing_coverage_cannot_become_success(project, tmp_path, monkeypatch, mode):
    real_run = subprocess.run
    def run(command, **kwargs):
        if command[0] == 'git':
            return real_run(command, **kwargs)
        if mode == 'timeout':
            raise subprocess.TimeoutExpired(command, 1)
        result = successful_command(command, **kwargs)
        if mode == 'failure':
            return subprocess.CompletedProcess(command, 1)
        for arg in command:
            if arg.startswith('--junitxml='):
                Path(arg.split('=', 1)[1]).write_text(
                    f'<testsuites><testsuite tests="{0 if mode == "empty" else 1}" '
                    f'skipped="{1 if mode == "skipped" else 0}"/></testsuites>')
        return result
    monkeypatch.setattr(review.subprocess, 'run', run)
    output = tmp_path / 'failure'
    assert review.run_checks(output, 1, project) == 1
    assert review.verify_receipt(output / 'receipt.json', project)


def test_existing_evidence_is_never_overwritten(receipt, project):
    before = receipt.read_bytes()
    with pytest.raises(FileExistsError):
        review.run_checks(receipt.parent, 1, project)
    assert receipt.read_bytes() == before
