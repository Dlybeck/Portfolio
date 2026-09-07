import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import pytest
from playwright.sync_api import expect

from core.theme_packs import BOARD_LOCATIONS, ThemePackRegistry, load_theme_pack
from scripts.audit_theme_variants import audit_world

NEW_THEMES = ('vinyl', 'botanical', 'workbench', 'postcards')
ACTIVE_NEW_THEMES = ('postcards', 'vinyl')
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('theme', NEW_THEMES)
def test_new_pack_is_complete_and_selectable(theme, client):
    registry = ThemePackRegistry.discover()
    assert registry.diagnostics == ()
    expected = theme if theme in ACTIVE_NEW_THEMES else 'canonical'
    assert registry.resolve(theme, enabled=True).id == expected
    assert (theme in {pack.id for pack in registry.random_candidates}) == (theme == 'postcards')
    data = json.loads((ROOT / 'static/themes' / theme / 'tiles.json').read_text())
    assert set(data['assignments']) == BOARD_LOCATIONS
    response = client.get(f'/?theme={theme}')
    assert response.status_code == 200
    assert f'data-board-theme="{expected}"' in response.text


@pytest.mark.parametrize('theme', ACTIVE_NEW_THEMES)
def test_new_pack_variation_is_visible_and_continuous(theme, browser_page):
    page, origin = browser_page
    audit = audit_world(page, origin, theme)
    assert audit['passed'], audit


@pytest.mark.parametrize('theme', ACTIVE_NEW_THEMES)
@pytest.mark.parametrize('width', [390, 1440])
def test_new_theme_page_flow_and_neighbor_navigation(theme, width, browser_page):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(f'{origin}/hobbies/tennis?theme={theme}', wait_until='networkidle')
    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')
    expect(page.locator('html')).to_have_attribute('data-board-theme', theme)
    page.keyboard.press('Escape')
    expect(page.locator('.mini-window-container')).not_to_have_class(re.compile(r'\bshow\b'))
    surface = page.locator('.tile-container.expanded [data-theme-size="expanded"]')
    expect(surface).to_have_css('opacity', '1')
    page.evaluate("window.returnHome()")
    expect(page.locator('.tile-container.expanded')).to_have_attribute('data-title', 'Home')
    expect(page.locator('.home-theme-selector select')).to_be_attached()
    assert page.locator('.tile-container.connected').count() >= 2
    page.get_by_role('button', name='Go to Hobbies', exact=True).click()
    expect(page.locator('.tile-container.expanded')).to_have_attribute('data-title', 'Hobbies')
    page.get_by_role('button', name='Go to Tennis', exact=True).click()
    expect(page.locator('.tile-container.expanded')).to_have_attribute('data-title', 'Tennis')
    page.locator('.tile-container.expanded .expanded-open').click()
    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')


def test_vinyl_records_remain_round():
    for path in (ROOT / 'static/themes/vinyl/assets/tiles').glob('*.svg'):
        disc = ET.parse(path).getroot().find(".//*[@data-theme-record='disc']")
        assert disc is not None
        assert disc.tag.endswith('circle')
        assert float(disc.get('r')) >= 70


@pytest.mark.parametrize('width', [390, 1440])
def test_revisited_vinyl_is_available_for_direct_review(width, browser_page):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(f'{origin}/?theme=vinyl', wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'vinyl')


def test_collection_builder_targets_only_the_four_new_themes():
    from scripts.build_collection_themes import WORLDS
    assert set(WORLDS) == set(NEW_THEMES)


@pytest.mark.parametrize('theme', ['canonical', 'lily', 'planets', 'islands'])
def test_existing_pack_artwork_retains_its_original_opacity(theme, browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    expect(page.locator('.tile-container.expanded .tile-expanded .theme-object')).to_have_css('opacity', '0.98')


@pytest.mark.parametrize('theme', NEW_THEMES)
def test_document_ink_and_captions_have_readable_contrast(theme):
    def luminance(value):
        channels = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
        return sum(weight*(channel/12.92 if channel <= .04045 else ((channel+.055)/1.055)**2.4)
                   for weight, channel in zip((.2126, .7152, .0722), channels))

    document = load_theme_pack(ROOT/'static/themes'/theme).client_payload()['variables']['document']
    for role in ('ink', 'link', 'secondary-ink', 'caption-ink'):
        dark, light = sorted((luminance(document[role]), luminance(document['page-bg'])))
        assert (light+.05)/(dark+.05) >= 4.5, (theme, role)
