"""Approved treatments must work through the ordinary Theme Pack boundary."""
import json
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET
import pytest
from playwright.sync_api import expect
from copy import deepcopy

from core.theme_packs import load_theme_pack, ThemePackRegistry, InvalidThemeAsset

ROOT = Path(__file__).resolve().parents[1]


def test_independent_pack_can_supply_a_reading_surface_and_ribbons(tmp_path):
    folder = tmp_path / 'independent-surface'
    shutil.copytree(ROOT / 'static/themes/clouds', folder)
    manifest = json.loads((folder / 'theme.json').read_text())
    manifest['id'] = folder.name
    manifest['viewerSurface'] = {'asset': 'assets/surface.svg', 'outsetX': 18, 'outsetY': 12}
    (folder / 'theme.json').write_text(json.dumps(manifest))
    (folder / 'assets/surface.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path d="M0 0H100V100H0Z" fill="#f4f8f8"/></svg>')
    presentation = json.loads((folder / 'presentation.json').read_text())
    presentation['connectors']['ribbons'] = [
        {'width': 4.5, 'offset': 0, 'opacity': .6, 'color': '#eef7f9'}]
    (folder / 'presentation.json').write_text(json.dumps(presentation))
    payload = load_theme_pack(folder).client_payload()
    assert payload['viewerSurface']['outsetX'] == 18
    assert '<path' in payload['viewerSurface']['svg']
    assert payload['connectors']['ribbons'][0]['width'] == 4.5
    # Sanitized groups alone cannot serve as a scalable reading surface.
    (folder / 'assets/surface.svg').write_text('<g xmlns="http://www.w3.org/2000/svg"/>')
    with pytest.raises(InvalidThemeAsset, match='Viewer surface'):
        load_theme_pack(folder)


def test_pack_can_keep_reading_materials_and_a_contained_detail_with_its_tile(tmp_path):
    folder = tmp_path / 'independent-sleeve'
    shutil.copytree(ROOT / 'static/themes/vinyl', folder)
    manifest = json.loads((folder / 'theme.json').read_text())
    manifest['id'] = folder.name
    (folder / 'theme.json').write_text(json.dumps(manifest))
    tiles = json.loads((folder / 'tiles.json').read_text())
    home = tiles['assignments']['Home']
    home['readingSurface'] = {'pageColor': '#faf5e9', 'surroundColor': '#d5a599'}
    home['swap']['details'] = [{'part': 'record', 'element': 'peek',
                               'x': 0, 'y': -66, 'start': .72}]
    svg = ET.fromstring((folder / home['expanded']).read_text())
    moving = next(n for n in svg if n.get('data-theme-part') == 'record')
    ET.SubElement(moving, '{http://www.w3.org/2000/svg}g', {'data-theme-swap-detail': 'peek'})
    (folder / home['expanded']).write_text(ET.tostring(svg, encoding='unicode'))
    (folder / 'tiles.json').write_text(json.dumps(tiles))
    assignment = load_theme_pack(folder).client_payload()['tiles']['assignments']['Home']
    assert assignment['readingSurface']['pageColor'] == '#faf5e9'
    assert assignment['readingSurface']['surroundColor'] == '#d5a599'
    assert assignment['swap']['details'][0]['y'] == -66


@pytest.mark.parametrize('theme', ['clouds', 'lily', 'vinyl'])
def test_approved_treatment_renders_without_comparison_script(theme, browser_page):
    page, origin = browser_page
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-board-theme', theme)
    expect(page.locator('#grounding-prototype,script[src*="theme-grounding.js"]')).to_have_count(0)
    if theme in ('clouds', 'lily'):
        assert page.locator('[data-theme-ribbon]').count() > 0
    if theme == 'clouds':
        expect(page.locator('.theme-viewer-surface')).to_have_count(1)
    if theme == 'vinyl':
        expect(page.locator('.theme-swap-layer [data-theme-swap-detail="disc"]')).to_have_count(17)
        expect(page.locator('.expanded [data-swap-part="record"] [data-theme-swap-detail="disc"]')).to_have_attribute('transform', 'translate(0 -66)')
        expect(page.locator('.expanded [data-swap-part="record"] [data-theme-swap-detail="disc"]')).to_have_css('transform', 'matrix(1, 0, 0, 1, 0, -66)')
    page.get_by_role('button', name='Go to Hobbies', exact=True).click()
    page.get_by_role('button', name='Go to Tennis', exact=True).click()
    page.locator('.expanded .expanded-open').click()
    doc = page.frame_locator('.mini-window')
    expect(doc.locator('#location')).to_have_text('Tennis')
    if theme == 'clouds':
        expect(doc.locator('body')).to_have_css('background-color', 'rgb(244, 248, 248)')
    if theme == 'vinyl':
        paper = page.locator('.expanded [data-swap-part="record"] [data-theme-material="paper"]').evaluate('n => getComputedStyle(n).fill')
        jacket = page.locator('.expanded .tile-base [data-visual-axis="silhouette"] rect').evaluate('n => getComputedStyle(n).fill')
        expect(doc.locator('body')).to_have_css('background-color', paper)
        expect(page.locator('.mini-window-container')).to_have_css('background-color', paper)
        expect(page.locator('.mini-window-container')).to_have_css('border-top-color', jacket)
        assert paper != jacket


@pytest.mark.parametrize('change', ['external-surface', 'oversized-ribbon', 'css-color',
                                  'missing-detail', 'carrier-detail', 'duplicate-detail'])
def test_new_visual_controls_reject_unsafe_or_invalid_data(tmp_path, change):
    folder = tmp_path / 'invalid-pack'
    shutil.copytree(ROOT / 'static/themes/vinyl', folder)
    manifest = json.loads((folder / 'theme.json').read_text())
    manifest['id'] = folder.name
    presentation = json.loads((folder / 'presentation.json').read_text())
    tiles = json.loads((folder / 'tiles.json').read_text())
    home = tiles['assignments']['Home']
    if change == 'external-surface':
        manifest['viewerSurface'] = {'asset': 'https://example.com/surface.svg'}
    elif change == 'oversized-ribbon':
        presentation['connectors']['ribbons'] = [{'width': 100, 'offset': 0, 'opacity': 1, 'color': '#ffffff'}]
    elif change == 'css-color':
        home['readingSurface']['pageColor'] = 'red; background:url(https://example.com/)'
    elif change == 'missing-detail':
        home['swap']['details'][0]['element'] = 'missing'
    elif change == 'carrier-detail':
        home['swap']['details'][0]['part'] = 'sleeve'
    elif change == 'duplicate-detail':
        home['swap']['details'] *= 2
    for name, value in (('theme', manifest), ('presentation', presentation), ('tiles', tiles)):
        (folder / f'{name}.json').write_text(json.dumps(value))
    with pytest.raises(InvalidThemeAsset):
        load_theme_pack(folder)


@pytest.mark.parametrize('route,title', [('/jobs', 'Work Experience'),
    ('/hobbies/tennis', 'Tennis'), ('/education/agile_report', 'College')])
def test_reading_material_is_in_server_html_before_iframe_load(client, route, title):
    pack = load_theme_pack(ROOT / 'static/themes/vinyl')
    material = dict(pack.tiles)[title].reading_surface
    html = client.get(f'/_documents{route}?theme=vinyl').text
    assert f'--theme-pack-page-bg: {material.page_color};' in html
    board = client.get(f'{route}?theme=vinyl').text
    assert f'--theme-pack-viewer-bg: {material.page_color};' in board
    assert f'--theme-pack-viewer-border: {material.surround_color};' in board


def test_approved_vinyl_keeps_jacket_and_record_identity_across_states():
    pack = load_theme_pack(ROOT / 'static/themes/vinyl')
    for _, tile in pack.tiles:
        base, expanded = ET.fromstring(tile.base_svg), ET.fromstring(tile.expanded_svg)
        for part in ('record', 'sleeve'):
            a = next(n for n in base if n.get('data-theme-part') == part)
            b = next(n for n in expanded if n.get('data-theme-part') == part)
            a.attrib.pop('transform', None)
            assert ET.tostring(a) == ET.tostring(b)
        paper = expanded.find('.//*[@data-theme-material="paper"]')
        jacket = expanded.find('.//*[@data-visual-axis="palette"]')[0]
        assert paper.get('fill') == tile.reading_surface.page_color
        assert jacket.get('fill') == tile.reading_surface.surround_color


def test_legacy_exporters_preserve_the_authored_vinyl_pack(tmp_path, monkeypatch):
    from scripts import build_collection_themes, refine_collection_reveals
    folder = tmp_path / 'static/themes/vinyl'
    shutil.copytree(ROOT / 'static/themes/vinyl', folder)
    before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    # Restrict the old generator to Vinyl and the final reveal step to an
    # isolated empty Postcards pack; no real installed files are rewritten.
    postcards = tmp_path / 'static/themes/postcards'
    shutil.copytree(ROOT / 'static/themes/postcards', postcards)
    monkeypatch.setattr(build_collection_themes, 'PACKS', tmp_path / 'static/themes')
    monkeypatch.setattr(build_collection_themes, 'WORLDS', {'vinyl': build_collection_themes.WORLDS['vinyl']})
    monkeypatch.setattr(refine_collection_reveals, 'ROOT', tmp_path)
    build_collection_themes.main()
    after = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert before == after


@pytest.mark.parametrize('width', [390, 1440])
def test_approved_variation_can_be_reauthored_without_runtime_changes(tmp_path, monkeypatch, browser_page, width):
    """A new fixture ID swaps two existing approved identities using JSON only."""
    folder = tmp_path / 'authoring-proof'
    shutil.copytree(ROOT / 'static/themes/vinyl', folder)
    manifest = json.loads((folder / 'theme.json').read_text())
    manifest.update(id=folder.name, label='Authoring proof')
    (folder / 'theme.json').write_text(json.dumps(manifest))
    catalog = json.loads((folder / 'tiles.json').read_text())
    assignments = catalog['assignments']
    assignments['Home'], assignments['Tennis'] = deepcopy(assignments['Tennis']), deepcopy(assignments['Home'])
    (folder / 'tiles.json').write_text(json.dumps(catalog))
    approved = load_theme_pack(ROOT / 'static/themes/vinyl')
    authored = load_theme_pack(folder)
    canonical = load_theme_pack(ROOT / 'static/themes/canonical')
    # Filesystem-discovery boundary only: the actual validator, HTTP routes,
    # renderer, assets, navigation and styles all run unchanged.
    registry = ThemePackRegistry((canonical, authored))
    monkeypatch.setattr(ThemePackRegistry, 'discover', classmethod(lambda cls: registry))
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 844 if width == 390 else 900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme=authoring-proof', wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'authoring-proof')
    expect(page.locator('.expanded .expanded-title')).to_have_text('Home')
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)
    assert dict(authored.tiles)['Home'].expanded_svg == dict(approved.tiles)['Tennis'].expanded_svg
    expect(page.locator('.expanded [data-swap-part="record"] [data-theme-swap-detail="disc"]')).to_have_css('transform', 'matrix(1, 0, 0, 1, 0, -66)')
    page.screenshot(path=str(tmp_path / f'authoring-{width}-home.png'))
    page.get_by_role('button', name='Go to Hobbies', exact=True).click()
    page.get_by_role('button', name='Go to Tennis', exact=True).click()
    page.locator('.expanded .expanded-open').click()
    material = dict(authored.tiles)['Tennis'].reading_surface
    expected_color = 'rgb(' + ', '.join(str(int(material.page_color[i:i+2], 16)) for i in (1,3,5)) + ')'
    expect(page.frame_locator('.mini-window').locator('body')).to_have_css('background-color', expected_color)
    page.screenshot(path=str(tmp_path / f'authoring-{width}-page.png'))
