"""THROWAWAY: verify the private corrected-B preview, not production approval."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
origin = 'http://127.0.0.1:51355'
root = Path(__file__).resolve().parents[1]
source = (root / 'static/prototypes/theme-grounding.js').read_bytes()
assert urlopen(origin + '/static/prototypes/theme-grounding.js').read() == source
receipt = {'source_sha256': hashlib.sha256(source).hexdigest(), 'views': [], 'status': 'running'}
try:
    with sync_playwright() as p:
        browser = p.chromium.connect('ws://127.0.0.1:3000/')
        for width, height in ((320, 740), (390, 844), (1440, 900)):
            context = browser.new_context(viewport={'width': width, 'height': height},
                is_mobile=width < 500, has_touch=width < 500, reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            def assert_paper(expected_variant='B'):
                expected = (page.locator('.expanded [data-prototype-inner-sleeve]').first.evaluate(
                    'paper => getComputedStyle(paper).fill') if expected_variant == 'B'
                    else 'rgb(244, 232, 206)')
                expect(page.locator('.mini-window-container')).to_have_css('background-color', expected)
                edge = (page.locator('.expanded .tile-base [data-theme-part="sleeve"] [data-visual-axis="silhouette"] rect').evaluate(
                    'jacket => getComputedStyle(jacket).fill') if expected_variant == 'B'
                    else 'rgb(155, 69, 55)')
                for side in ('top', 'right', 'bottom', 'left'):
                    expect(page.locator('.mini-window-container')).to_have_css(f'border-{side}-color', edge)
                    expect(page.locator('.mini-window-container')).to_have_css(f'border-{side}-width', '8px')
                if expected_variant == 'B':
                    assert edge != expected, 'Jacket surround disappears into the inner paper'
                for tag in ('html', 'body'):
                    expect(page.frame_locator('.mini-window').locator(tag)).to_have_css('background-color', expected)
                expect(page.locator('.loading-scrap')).to_have_count(0)
                return expected

            page.goto(origin + '/?theme=vinyl&grounding=A', wait_until='networkidle')
            expect(page.locator('html')).to_have_attribute('data-grounding', 'B')
            assert 'grounding=B' in page.url
            expect(page.locator('[data-prototype-disc]')).to_have_count(17)
            collection = page.locator('.tile-container').evaluate_all('''tiles => tiles.map(tile => ({
                cover: [...tile.querySelectorAll('.tile-base [data-theme-part="sleeve"] path')]
                    .filter(n => n.hasAttribute('fill') && n.getAttribute('fill') !== 'none').map(n => n.getAttribute('d')).join('|'),
                pressing: tile.querySelector('[data-prototype-disc] circle').getAttribute('fill'),
                paper: tile.querySelector('[data-prototype-inner-sleeve]').getAttribute('fill')
            }))''')
            assert len({c['cover'] for c in collection}) >= 5, 'Covers still repeat the same illustration'
            assert len({c['pressing'] for c in collection}) >= 4, 'Records need visible pressing variety'
            assert len({c['paper'] for c in collection}) >= 3, 'Inner sleeves need paper variety'
            def artwork():
                return page.locator('.tile-container').evaluate_all('''tiles => tiles.map(tile => ({
                    covers:[...tile.querySelectorAll('[data-theme-part="sleeve"]')].map(n => n.innerHTML),
                    disc:tile.querySelector('[data-prototype-disc]')?.innerHTML,
                    paper:tile.querySelector('[data-prototype-inner-sleeve]')?.outerHTML
                }))''')
            initial_art = artwork()
            assert all(len(set(a['covers'])) == 1 for a in initial_art), 'Jacket artwork changes between states'
            titles = page.locator('.tile-container').evaluate_all('tiles => tiles.map(t => t.dataset.title)')
            states = []
            for title in titles:
                page.evaluate('title => window.centerOnTile(title)', title)
                page.wait_for_function('title => document.querySelector(".tile-container.expanded")?.dataset.title === title', arg=title)
                page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                state = page.locator('.tile-container.expanded').evaluate('''tile => {
                    const moving = tile.querySelector('[data-swap-part="record"]');
                    const nodes = [...moving.querySelectorAll('.expanded-title,.expanded-text,.expanded-open')];
                    const art = moving.querySelector('[data-theme-part="record"]').getBoundingClientRect();
                    const neighbors = [...document.querySelectorAll('.connected .tile-base')].map(n => {
                        const b = n.getBoundingClientRect();
                        const x = Math.max(12, Math.min(innerWidth-12, b.x+b.width/2));
                        const y = Math.max(60, Math.min(innerHeight-12, b.y+b.height/2));
                        const hit = document.elementFromPoint(x,y);
                        return {title:n.closest('.tile-container').dataset.title, usable: n.contains(hit)};
                    });
                    return {title:tile.dataset.title, fit:tile.dataset.themeContentFit, progress:tile.dataset.swapProgress,
                        peek:tile.querySelector('[data-prototype-disc]').getAttribute('transform'),
                        fonts:nodes.map(n => ({kind:n.className, size:parseFloat(getComputedStyle(n).fontSize)})),
                        // Handwritten glyphs can extend past their line box without
                        // clipping. Reject horizontal overflow or clipped vertical ink.
                        overflow:nodes.some(n => n.scrollWidth > n.clientWidth+1 ||
                            (getComputedStyle(n).overflowY !== 'visible' && n.scrollHeight > n.clientHeight+1)),
                        bounds:art.toJSON(), neighbors};
                }''')
                states.append(state)
                assert state['fit'] == 'true' and state['progress'] == '1', state
                assert state['peek'] == 'translate(0 -66)' and not state['overflow'], state
                assert all(n['size'] >= (20 if 'expanded-title' in n['kind'] else 18 if 'expanded-open' in n['kind'] else 14) for n in state['fonts']), state
                assert state['bounds']['left'] >= 0 and state['bounds']['right'] <= width, state
                assert all(n['usable'] for n in state['neighbors']), state
            page.evaluate("window.centerOnTile('Home')")
            page.get_by_role('button', name='Go to Hobbies', exact=True).click()
            page.get_by_role('button', name='Go to Tennis', exact=True).click()
            page.locator('.expanded .expanded-open').click()
            expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')
            assert_paper()
            page.screenshot(path=str(args.output / f'vinyl-page-{width}.png'))
            for expected in ('C', 'B'):
                page.get_by_role('button', name='Next prototype', exact=True).click()
                expect(page.locator('html')).to_have_attribute('data-grounding', expected)
                assert '/hobbies/tennis' in page.url
                assert_paper(expected)
            assert artwork() == initial_art, 'Detail identity changed during navigation/comparison'
            paper_pages = []
            for slug, route in (('work', '/jobs'), ('gaming', '/hobbies/gaming'),
                                ('website', '/projects/websites/this_website'), ('tennis', '/hobbies/tennis'),
                                ('puzzles', '/hobbies/3d_printing/puzzles')):
                # Keep the viewer open to catch a stale color on document-to-document navigation.
                page.evaluate('route => window.openPage(route)', route)
                page.wait_for_function('route => document.querySelector(".mini-window").contentWindow.location.pathname === "/_documents" + route', arg=route)
                paper_pages.append({'route': route, 'color': assert_paper()})
                page.screenshot(path=str(args.output / f'vinyl-paper-{slug}-{width}.png'))
            assert len({item['color'] for item in paper_pages}) == 4, paper_pages
            page.keyboard.press('Escape')
            expect(page.locator('body')).not_to_have_class(re.compile(r'\bpage-open\b'))
            page.evaluate("window.centerOnTile('Home')")
            assert page.locator('[data-title="Tennis"] [data-prototype-disc]').get_attribute('transform') == 'translate(0 0)'
            # Switching packs must tear down the nested peek and preserve controls.
            page.evaluate("window.themeEngine.activate('canonical')")
            expect(page.locator('html')).to_have_attribute('data-board-theme', 'canonical')
            expect(page.locator('[data-prototype-disc], .prototype-flow, #prototype-cloud-surface')).to_have_count(0)
            page.get_by_role('button', name='Go to Hobbies', exact=True).click()
            page.get_by_role('button', name='Go to Tennis', exact=True).click()
            page.locator('.expanded .expanded-open').click()
            expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Tennis')
            assert page.frame_locator('.mini-window').locator('#prototype-reading-style').count() == 0
            assert page.locator('html').evaluate("n => n.style.getPropertyValue('--prototype-vinyl-paper')") == ''
            assert page.locator('html').evaluate("n => n.style.getPropertyValue('--prototype-vinyl-jacket')") == ''
            page.screenshot(path=str(args.output / f'canonical-page-{width}.png'))
            page.keyboard.press('Escape')
            page.evaluate("window.themeEngine.activate('vinyl')")
            expect(page.locator('[data-prototype-disc]')).to_have_count(17)
            assert artwork() == initial_art, 'Details changed after reactivating Vinyl'
            page.evaluate("window.centerOnTile('Home')")
            page.screenshot(path=str(args.output / f'vinyl-home-{width}.png'))
            assert page.locator('.prototype-flow').count() == 0
            assert errors == [], errors
            receipt['views'].append({'width': width, 'states': states, 'page_errors': errors, 'controls': 'passed',
                'distinct_covers':len({c['cover'] for c in collection}),
                'distinct_pressings':len({c['pressing'] for c in collection}),
                'distinct_papers':len({c['paper'] for c in collection}), 'identity':'stable',
                'opened_papers':paper_pages})
            context.close()
        browser.close()
    receipt['status'] = 'passed'
except Exception as error:
    receipt['status'] = 'failed'
    receipt['error'] = str(error)
    raise
finally:
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'completed_widths': [v['width'] for v in receipt['views']]}))
