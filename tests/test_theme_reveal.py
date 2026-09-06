import json
from pathlib import Path
import shutil

import pytest
from playwright.sync_api import expect

from core.theme_packs import InvalidThemeAsset, load_theme_pack

ROOT = Path(__file__).resolve().parents[1]


def fixture_pack(tmp_path):
    folder = tmp_path/'independent-reveal'
    shutil.copytree(ROOT/'static/themes/postcards', folder)
    manifest = json.loads((folder/'theme.json').read_text())
    manifest['id'] = 'independent-reveal'
    (folder/'theme.json').write_text(json.dumps(manifest))
    return folder


def test_reveal_compiles_as_data_without_a_known_theme_id(tmp_path):
    pack = load_theme_pack(fixture_pack(tmp_path))
    assert pack.id == 'independent-reveal'
    assert all(tile.reveal.content_part == 'card' for _, tile in pack.tiles)


@pytest.mark.parametrize('theme', ['vinyl', 'postcards'])
def test_reveal_assets_match_the_authoring_recipe(theme):
    from scripts.refine_collection_reveals import compile_svg
    folder = ROOT/'static/themes'/theme
    catalog = json.loads((folder/'tiles.json').read_text())
    for assignment in catalog['assignments'].values():
        for state in ('base', 'expanded'):
            markup, reveal = compile_svg(theme, assignment['factors'], state)
            assert (folder/assignment[state]).read_text() == markup
            assert assignment['reveal'] == reveal


@pytest.mark.parametrize('change', ['missing', 'unknown-part', 'flipped-text', 'foreground-text', 'oversized', 'nonfinite', 'title-missing'])
def test_invalid_reveal_is_rejected(tmp_path, change):
    folder = fixture_pack(tmp_path)
    data = json.loads((folder/'tiles.json').read_text())
    tile = data['assignments']['Home']
    if change == 'missing':
        del tile['reveal']
    elif change == 'unknown-part':
        tile['reveal']['parts']['unknown'] = {}
    elif change == 'flipped-text':
        tile['reveal']['parts']['card']['flipY'] = -1
    elif change == 'foreground-text':
        tile['reveal']['parts']['card']['foreground'] = True
    elif change == 'oversized':
        tile['reveal']['parts']['card']['scale'] = 100
    elif change == 'nonfinite':
        tile['reveal']['parts']['card']['x'] = float('nan')
    else:
        tile['reveal']['titlePart'] = 'card'
    (folder/'tiles.json').write_text(json.dumps(data))
    with pytest.raises((InvalidThemeAsset, ValueError)):
        load_theme_pack(folder)


@pytest.mark.parametrize('theme', ['vinyl', 'postcards'])
@pytest.mark.parametrize('width', [390, 1440])
def test_reveal_reverses_same_parts_and_preserves_neighbors(theme, width, browser_page):
    page, origin = browser_page
    page.set_viewport_size({'width':width, 'height':844})
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    page.wait_for_timeout(750)
    page.evaluate('''() => {
        window.originalAssembly = document.querySelector('[data-title="Home"] [data-theme-size="expanded"]');
        window.originalParts = [...window.originalAssembly.querySelectorAll(':scope > [data-theme-part]')];
        window.centerOnTile('Hobbies');
    }''')
    page.wait_for_timeout(100)
    result = page.evaluate('''() => {
        const part = window.originalParts[0];
        const before = getComputedStyle(part).transform;
        window.centerOnTile('Home');
        const after = getComputedStyle(part).transform;
        return {before, after, same: window.originalAssembly === document.querySelector('[data-title="Home"] [data-theme-size="expanded"]'),
            leaving:document.querySelectorAll('[data-theme-reveal] .cover-leaving').length};
    }''')
    assert result['same'] and result['leaving'] == 0
    assert result['before'] == result['after'], result
    assert result['before'] != 'matrix(1, 0, 0, 1, 0, 0)'
    page.wait_for_timeout(750)
    assert page.evaluate('originalParts.every(p => getComputedStyle(p).transform === "matrix(1, 0, 0, 1, 0, 0)")')
    page.get_by_role('button', name='Go to Hobbies', exact=True).click()
    page.get_by_role('button', name='Go to Tennis', exact=True).click()
    page.locator('.tile-container.expanded .expanded-open').click()
    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')
    page.keyboard.press('Escape')
    expect(page.locator('.tile-container.expanded')).to_have_attribute('data-title', 'Tennis')


@pytest.mark.parametrize('theme', ['vinyl', 'postcards'])
def test_reveal_reduced_motion_and_cleanup(theme, browser_page):
    page, origin = browser_page
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    page.evaluate("window.centerOnTile('Hobbies')")
    page.wait_for_timeout(50)
    assert page.locator('.expanded .theme-reveal-part').evaluate_all('nodes => nodes.every(n => getComputedStyle(n).transform === "matrix(1, 0, 0, 1, 0, 0)")')
    page.evaluate("window.themeEngine.activate('canonical')")
    expect(page.locator('[data-theme-reveal]')).to_have_count(0)
    expect(page.locator('.theme-reveal-foreground')).to_have_count(0)
    expect(page.locator('[data-reveal-title]')).to_have_count(0)
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'canonical')
    page.evaluate(f"window.themeEngine.activate('{theme}')")
    expect(page.locator('[data-theme-reveal]')).to_have_count(17)


@pytest.mark.parametrize('theme,contained,carrier', [('vinyl', 'record', 'sleeve'), ('postcards', 'card', 'back')])
def test_contained_object_fits_its_carrier_when_closed(theme, contained, carrier, browser_page):
    page, origin = browser_page
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    page.evaluate("window.centerOnTile('Hobbies')")
    page.wait_for_timeout(50)
    svg = page.locator('[data-title="Home"] [data-theme-size="expanded"]')
    inner = svg.locator(f':scope > [data-theme-part="{contained}"]').bounding_box()
    outer = svg.locator(f':scope > [data-theme-part="{carrier}"]').bounding_box()
    assert inner['x'] >= outer['x'] - 2
    assert inner['y'] >= outer['y'] - 2
    assert inner['x']+inner['width'] <= outer['x']+outer['width']+2
    assert inner['y']+inner['height'] <= outer['y']+outer['height']+2
