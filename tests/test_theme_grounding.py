from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'static/themes'


def test_planets_are_round_and_surface_features_belong_to_the_globe():
    issues = []
    for path in (ROOT / 'planets/assets/tiles').glob('*.svg'):
        root = ET.parse(path).getroot()
        body = root.find(".//*[@data-visual-axis='silhouette']")
        if body.get('rx') != body.get('ry'):
            issues.append(f'{path.name}: oval body')
        surface = root.find(".//*[@data-visual-axis='surface']")
        if surface.get('clip-path') != 'url(#planet-surface)':
            issues.append(f'{path.name}: surface can extend past globe')
    assert issues == []


def test_ring_systems_have_rear_and_front_segments():
    for path in (ROOT / 'planets/assets/tiles').glob('*.svg'):
        root = ET.parse(path).getroot()
        companion = root.find(".//*[@data-visual-axis='companion']")
        if companion.get('data-visual-value') in {'1', '2'}:
            assert root.find(".//*[@data-theme-ring-half='rear']") is not None, path.name
            assert root.find(".//*[@data-theme-ring-half='front']") is not None, path.name


def test_pond_ripples_are_behind_the_leaf():
    for path in (ROOT / 'lily/assets/tiles').glob('*.svg'):
        root = ET.parse(path).getroot()
        palette = root.find(".//*[@data-visual-axis='palette']")
        accent = palette.find("./*[@data-visual-axis='accent']")
        if accent.get('data-visual-value') == '3':
            assert list(palette)[0] is accent, path.name


@pytest.mark.parametrize('width', [320, 1440])
def test_planet_bodies_remain_round_when_rendered(browser_page, width):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(f'{origin}/?theme=planets#Programs', wait_until='networkidle')
    bodies = page.locator('.theme-object [data-visual-axis="silhouette"]')
    assert bodies.count() == 34
    assert bodies.evaluate_all('''nodes => nodes.every(node => {
        const matrix = node.getScreenCTM();
        const xScale = Math.hypot(matrix.a, matrix.b);
        const yScale = Math.hypot(matrix.c, matrix.d);
        return Math.abs(node.rx.baseVal.value * xScale - node.ry.baseVal.value * yScale) < .1;
    })''')
