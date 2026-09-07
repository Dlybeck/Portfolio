"""Replay real material failures in isolated assets; preserve approved controls."""
import runpy
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def guard(tmp_path):
    # Reuse the real guard functions. Never mutate installed theme assets.
    namespace = runpy.run_path(str(ROOT / 'tests/test_theme_grounding.py'))
    for theme in ('planets', 'lily'):
        shutil.copytree(ROOT / 'static/themes' / theme / 'assets/tiles',
                        tmp_path / theme / 'assets/tiles')
    def run(name):
        function = namespace[name]
        function.__globals__['ROOT'] = tmp_path
        function()
    return tmp_path, run


def test_approved_round_globes_inclined_rings_and_water_ripples_pass(guard):
    _, run = guard
    for name in ('test_planets_are_round_and_surface_features_belong_to_the_globe',
                 'test_ring_systems_have_rear_and_front_segments',
                 'test_pond_ripples_are_behind_the_leaf'):
        run(name)


@pytest.mark.parametrize('defect', ['oval-globe', 'floating-surface', 'missing-ring-half', 'leaf-top-ripple'])
def test_known_material_failures_are_rejected(guard, defect):
    root, run = guard
    theme = 'lily' if defect == 'leaf-top-ripple' else 'planets'
    changed = False
    for file in sorted((root / theme / 'assets/tiles').glob('*.svg')):
        tree = ET.parse(file)
        svg = tree.getroot()
        if defect == 'oval-globe':
            node = svg.find(".//*[@data-visual-axis='silhouette']")
            node.set('ry', str(float(node.get('rx')) * .65))
            check = 'test_planets_are_round_and_surface_features_belong_to_the_globe'
        elif defect == 'floating-surface':
            svg.find(".//*[@data-visual-axis='surface']").attrib.pop('clip-path')
            check = 'test_planets_are_round_and_surface_features_belong_to_the_globe'
        elif defect == 'missing-ring-half':
            node = svg.find(".//*[@data-theme-ring-half='rear']")
            if node is None:
                continue
            node.attrib.pop('data-theme-ring-half')
            check = 'test_ring_systems_have_rear_and_front_segments'
        else:
            palette = svg.find(".//*[@data-visual-axis='palette']")
            accent = palette.find("./*[@data-visual-axis='accent']")
            if accent.get('data-visual-value') != '3':
                continue
            palette.remove(accent)
            palette.append(accent)
            check = 'test_pond_ripples_are_behind_the_leaf'
        tree.write(file)
        changed = True
        with pytest.raises(AssertionError):
            run(check)
        break
    assert changed, f'The fixture no longer contains the required case: {defect}'
