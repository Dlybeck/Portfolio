#!/usr/bin/env python3
"""Run mechanical grounding guards; never certify visual coherence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATHS = (
    'apis', 'core', 'static', 'templates', 'main.py', 'Dockerfile',
    'cloudbuild.yaml', 'requirements.txt', 'requirements-dev.txt', 'pyproject.toml', 'AGENTS.md', 'CONTEXT.md',
    'docs/theme-grounding-review.md', '.agents/skills/portfolio-grounding',
    'scripts/check_grounding.py', 'scripts/capture_grounding.py',
    'scripts/check_canonical_fidelity.py', 'tests',
)
CHECKS = (
    ('fit-and-material', ('-m', 'pytest', 'tests/test_theme_grounding.py',
        'tests/test_theme_comfort.py', 'tests/test_cloudscape_refinement.py')),
    ('navigation-and-motion', ('-m', 'pytest', 'tests/test_themes.py',
        'tests/test_theme_reveal.py', '-k',
        'keyboard_hierarchy or phone_touch_navigation or theme_switch_replaces '
        'or focus_exit_finishes or original_open_document or '
        'swap_is_opaque or swap_reverses or swap_touch or natural_world_grow')),
    ('pack-contract', ('-m', 'pytest', 'tests/test_theme_packs.py',
        'tests/test_returning_themes.py', 'tests/test_new_theme_packs.py')),
    ('original-fidelity', ('scripts/check_canonical_fidelity.py',)),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_fingerprint(root: Path = ROOT) -> str:
    names = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z',
         '--', *SOURCE_PATHS], cwd=root).split(b'\0')
    result = hashlib.sha256()
    for name in sorted(set(names) - {b''}):
        relative = name.decode()
        if relative.startswith('tests/results/'):
            continue
        path = root / relative
        result.update(name + b'\0')
        if path.is_symlink():
            result.update(str(path.readlink()).encode())
        elif path.is_file():
            result.update(bytes.fromhex(digest(path)))
        else:
            result.update(b'<missing>')
    return result.hexdigest()


def run_checks(output: Path, timeout: float, root: Path = ROOT) -> int:
    # Never erase another run or let its artifacts masquerade as fresh evidence.
    output.mkdir(parents=True, exist_ok=False)
    receipt_path = output / 'receipt.json'
    receipt = {
        'version': 1, 'status': 'incomplete', 'visual_review': 'required',
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'source_fingerprint': source_fingerprint(root),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'checks': [],
    }

    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')

    save()
    try:
        for name, arguments in CHECKS:
            log = output / f'{name}.log'
            command = [sys.executable, *arguments]
            junit = output / f'{name}.xml' if arguments[:2] == ('-m', 'pytest') else None
            if junit:
                command += ['-q', '--tb=short', '--show-capture=no', f'--junitxml={junit}']
            check = {'name': name, 'command': command, 'exit_code': None,
                     'artifacts': {}, 'error': None}
            receipt['checks'].append(check)
            save()
            try:
                with log.open('x') as stream:
                    completed = subprocess.run(command, cwd=root, stdout=stream,
                        stderr=subprocess.STDOUT, timeout=timeout, check=False)
                check['exit_code'] = completed.returncode
                if completed.returncode == 0 and junit:
                    suites = ET.parse(junit).getroot().iter('testsuite')
                    counts = {key: 0 for key in ('tests', 'failures', 'errors', 'skipped')}
                    for suite in suites:
                        for key in counts:
                            counts[key] += int(suite.get(key, '0'))
                    check['counts'] = counts
                    if counts['tests'] == 0 or any(counts[k] for k in ('failures', 'errors', 'skipped')):
                        check['error'] = 'Required coverage failed, was empty, or was skipped.'
            except (subprocess.TimeoutExpired, OSError, ET.ParseError, ValueError) as error:
                check['error'] = str(error)
            for artifact in (log, junit):
                if artifact and artifact.is_file():
                    check['artifacts'][artifact.name] = digest(artifact)
            save()
            if check['exit_code'] != 0 or check['error']:
                receipt['status'] = 'failed'
                break
        else:
            receipt['status'] = 'mechanical_checks_passed'
        if source_fingerprint(root) != receipt['source_fingerprint']:
            receipt['status'] = 'stale'
    finally:
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save()
    print(f"{receipt['status']}: {receipt_path}; visual grounding review is still required")
    return 0 if receipt['status'] == 'mechanical_checks_passed' else 1


def verify_receipt(path: Path, root: Path = ROOT) -> list[str]:
    """Reject stale, edited, missing and incomplete mechanical evidence."""
    try:
        data = json.loads(path.read_text())
        errors = []
        if data.get('version') != 1 or data.get('status') != 'mechanical_checks_passed':
            errors.append('Mechanical run did not complete successfully.')
        if data.get('visual_review') != 'required':
            errors.append('Mechanical evidence cannot certify visual approval.')
        if data.get('source_fingerprint') != source_fingerprint(root):
            errors.append('Evidence does not match current source/rules/tests.')
        checks = data['checks']
        if [c['name'] for c in checks] != [name for name, _ in CHECKS]:
            errors.append('Required check coverage is missing or reordered.')
        for check in checks:
            expected_args = dict(CHECKS).get(check['name'])
            if expected_args is None:
                errors.append(f"Unknown check: {check['name']}")
                continue
            command = check.get('command', [])
            if command[1:1 + len(expected_args)] != list(expected_args):
                errors.append(f"Wrong command: {check['name']}")
            required_artifacts = {f"{check['name']}.log"}
            if expected_args[:2] == ('-m', 'pytest'):
                required_artifacts.add(f"{check['name']}.xml")
            if set(check.get('artifacts', {})) != required_artifacts:
                errors.append(f"Missing required artifacts: {check['name']}")
            if check.get('exit_code') != 0 or check.get('error') or not check.get('artifacts'):
                errors.append(f"Incomplete evidence: {check['name']}")
            for name, expected in check['artifacts'].items():
                artifact = path.parent / name
                if (Path(name).name != name or artifact.is_symlink()
                        or not artifact.is_file() or digest(artifact) != expected):
                    errors.append(f'Artifact missing or changed: {name}')
            if expected_args[:2] == ('-m', 'pytest'):
                suites = list(ET.parse(path.parent / f"{check['name']}.xml").getroot().iter('testsuite'))
                if not suites or sum(int(s.get('tests', '0')) for s in suites) == 0 or any(
                        int(s.get(k, '0')) for s in suites for k in ('errors', 'failures', 'skipped')):
                    errors.append(f"Required coverage incomplete: {check['name']}")
        return errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as error:
        return [f'Invalid receipt: {error}']


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    run = sub.add_parser('run', help='Run guards into a new output directory.')
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--timeout', type=float, default=300, help='Seconds per check group.')
    verify = sub.add_parser('verify', help='Verify mechanical evidence against current files.')
    verify.add_argument('receipt', type=Path)
    args = parser.parse_args()
    if args.action == 'run':
        if args.timeout <= 0:
            parser.error('--timeout must be positive')
        return run_checks(args.output.resolve(), args.timeout)
    errors = verify_receipt(args.receipt.resolve())
    print('\n'.join(errors) if errors else 'Mechanical evidence is current; visual review is still required.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
