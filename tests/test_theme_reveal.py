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


@pytest.mark.parametrize('theme', ['postcards'])
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


@pytest.mark.parametrize('change', ['missing-swap','unknown-carrier','wrong-moving','nonfinite-lift','positive-lift','unequal-scale','transparent-part'])
def test_invalid_swap_configuration_is_rejected(tmp_path, change):
    folder=fixture_pack(tmp_path)
    data=json.loads((folder/'tiles.json').read_text())
    tile=data['assignments']['Home']
    if change=='missing-swap': del tile['swap']
    elif change=='unknown-carrier': tile['swap']['carrierPart']='absent'
    elif change=='wrong-moving': tile['swap']['movingPart']='back'
    elif change=='nonfinite-lift': tile['swap']['liftY']=float('nan')
    elif change=='unequal-scale': tile['reveal']['parts']['card']['scale']=.8
    elif change=='transparent-part': tile['reveal']['parts']['flap']['openOpacity']=0
    else: tile['swap']['liftY']=50
    (folder/'tiles.json').write_text(json.dumps(data))
    with pytest.raises((InvalidThemeAsset, ValueError)):
        load_theme_pack(folder)


def test_swap_touch_then_keyboard_document_flow(mobile_browser_page):
    page, origin=mobile_browser_page
    page.goto(f'{origin}/?theme=postcards',wait_until='networkidle')
    page.get_by_role('button',name='Go to Hobbies',exact=True).tap()
    page.get_by_role('button',name='Go to Tennis',exact=True).tap()
    page.locator('.expanded .expanded-open').focus()
    page.keyboard.press('Enter')
    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')
    page.keyboard.press('Escape')
    expect(page.locator('.tile-container.expanded')).to_have_attribute('data-title','Tennis')


@pytest.mark.parametrize('theme', ['lily','planets','islands'])
def test_natural_world_grow_does_not_fade_solid_objects(theme, browser_page):
    page, origin=browser_page
    page.goto(f'{origin}/?theme={theme}',wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-theme-focus-motion','grow')
    result=page.evaluate("""async () => {
        window.centerOnTile('Hobbies');
        await new Promise(requestAnimationFrame);
        const surface=document.querySelector('.expanded .tile-expanded');
        const animation=surface.getAnimations().find(a=>a.animationName==='focus-grow-enter');
        animation.pause(); animation.currentTime=40;
        return getComputedStyle(surface).opacity;
    }""")
    assert result=='1'


@pytest.mark.parametrize('theme,moving,carrier', [('postcards','card','front'),('vinyl','record','sleeve')])
@pytest.mark.parametrize('width', [390, 1440])
def test_swap_is_opaque_clears_carrier_and_keeps_writing_attached(theme, moving, carrier, width, browser_page):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 844})
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    result = page.evaluate("""async ([moving,carrier]) => {
        const tile=document.querySelector('[data-title="Home"]');
        const card=tile.querySelector(`[data-swap-part="${moving}"]`);
        const front=tile.querySelector(`[data-swap-part="${carrier}"]`);
        const title=tile.querySelector('.swap-carrier-title');
        const writing=[...card.querySelectorAll('.expanded-title,.expanded-text,.home-theme-selector')];
        const texts=writing.map(n=>n.textContent);
        const samples=[];
        function measure() {
            const c=card.querySelector(`[data-theme-part="${moving}"]`).getBoundingClientRect();
            const f=front.querySelector(`[data-theme-part="${carrier}"]`).getBoundingClientRect();
            const p=Number(tile.dataset.swapProgress);
            samples.push({p, z:Number(card.style.zIndex), cardBottom:c.bottom, carrierTop:f.top,
                opaque:getComputedStyle(card).opacity==='1',
                stable:writing.every((n,i)=>n.parentElement===card && n.textContent===texts[i]) && title.textContent==='Home',
                neighbors:[...document.querySelectorAll('.connected .tile-base')].every(n=>{
                    const b=n.getBoundingClientRect();
                    if (b.x+b.width/2<0 || b.x+b.width/2>=innerWidth || b.y+b.height/2<0 || b.y+b.height/2>=innerHeight) return true;
                    const hit=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);
                    // Fixed site chrome already overlays destinations passing
                    // beneath it during the unchanged map-camera transition.
                    if (hit?.closest('.navbar')) return true;
                    return hit && (hit===n || n.contains(hit));
                })});
        }
        async function leg(destination) {
            window.centerOnTile(destination);
            await new Promise(resolve=>{
                const started=performance.now();
                const tick=()=>{measure();if(performance.now()-started<1300)requestAnimationFrame(tick);else resolve();};
                requestAnimationFrame(tick);
            });
        }
        await leg('Hobbies');
        await leg('Home');
        return {samples, same:card===tile.querySelector(`[data-swap-part="${moving}"]`)};
    }""", [moving,carrier])
    assert result['same']
    samples = result['samples']
    assert all(s['opaque'] and s['stable'] and s['neighbors'] for s in samples), [s for s in samples if not(s['opaque'] and s['stable'] and s['neighbors'])][:3]
    crossings = [s for s in samples if .52 <= s['p'] <= .58]
    assert crossings and all(s['cardBottom'] < s['carrierTop'] for s in crossings), crossings
    assert all(s['z'] == (10 if s['p'] >= .55 else 2) for s in samples)
    assert any(s['p'] == 0 for s in samples) and samples[-1]['p'] == 1
    page.get_by_role('button', name='Go to Hobbies', exact=True).click()
    page.get_by_role('button', name='Go to Tennis', exact=True).click()
    page.locator('.expanded .expanded-open').click()
    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')


def test_postcard_swap_finishes_at_original_paper_pace(browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme=postcards', wait_until='networkidle')
    result = page.evaluate('''async () => {
        const duration=window.themeEngine.currentPack().variables.board['cover-enter-duration'];
        const start=performance.now();
        window.centerOnTile('Hobbies');
        const tile=document.querySelector('[data-title="Hobbies"]');
        await new Promise(resolve => {
            const tick=()=> Number(tile.dataset.swapProgress)===1 || performance.now()-start>1500
                ? resolve() : requestAnimationFrame(tick);
            requestAnimationFrame(tick);
        });
        return {duration, elapsed:performance.now()-start, progress:tile.dataset.swapProgress};
    }''')
    assert result['duration'] == '.8s'
    assert result['progress'] == '1' and result['elapsed'] < 1000, result


def test_swap_reverses_without_reset_and_cleans_up(browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme=postcards', wait_until='networkidle')
    page.evaluate("window.centerOnTile('Hobbies')")
    page.wait_for_timeout(350)
    result=page.evaluate("""() => {
        const tile=document.querySelector('[data-title="Home"]');
        const card=tile.querySelector('[data-swap-part="card"]');
        const before=card.style.transform;
        window.centerOnTile('Home');
        return {before,after:card.style.transform,p:Number(tile.dataset.swapProgress)};
    }""")
    assert result['before']==result['after'] and 0<result['p']<1
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_timeout(50)
    assert page.locator('[data-title="Home"]').get_attribute('data-swap-progress') == '1'
    page.evaluate("window.themeEngine.activate('canonical')")
    expect(page.locator('[data-theme-swap],.theme-swap-layer')).to_have_count(0)
    expect(page.locator('.expanded-title')).to_have_count(17)
    page.evaluate("window.themeEngine.activate('postcards')")
    expect(page.locator('[data-theme-swap]')).to_have_count(17)
    page.evaluate("window.centerOnTile('Hobbies')")
    page.wait_for_timeout(50)
    expect(page.locator('[data-title="Home"]')).to_have_attribute('data-swap-progress','0')


@pytest.mark.parametrize('theme', ['botanical','workbench'])
def test_rejected_theme_is_unavailable_in_every_selection_path(theme, client, browser_page):
    from core.theme_packs import ThemePackRegistry
    registry=ThemePackRegistry.discover()
    assert theme not in {p.id for p in registry.random_candidates}
    assert registry.resolve(theme, enabled=True).id == 'canonical'
    page, origin=browser_page
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-board-theme','canonical')
    assert theme not in page.evaluate('window.themeEngine.availableThemes')
