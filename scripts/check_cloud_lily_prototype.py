"""Targeted browser checks for private candidate continuity, not aesthetic approval."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    origin = 'http://127.0.0.1:51355'
    source = Path(__file__).resolve().parents[1] / 'static/prototypes/theme-grounding.js'
    served = urlopen(origin + '/static/prototypes/theme-grounding.js', timeout=10).read()
    assert served == source.read_bytes()
    receipt = {'source_sha256': hashlib.sha256(served).hexdigest(), 'status': 'running', 'views': []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect('ws://127.0.0.1:3000/')
            try:
                for width, height in ((320, 740), (390, 844), (1440, 900)):
                    context = browser.new_context(viewport={'width': width, 'height': height},
                        is_mobile=width < 500, has_touch=width < 500, reduced_motion='reduce')
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(origin + '/hobbies/gaming?theme=clouds&grounding=C', wait_until='networkidle')
                    expect(page.locator('html')).to_have_attribute('data-board-theme', 'clouds')
                    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Gaming')
                    expect(page.locator('.loading-scrap')).to_have_count(0)
                    page.emulate_media(reduced_motion='no-preference')
                    # Observe both states in the same frame: the reading background
                    # must not vanish while its content is still exiting.
                    state = page.evaluate('''() => {
                        const wash = () => ({content:getComputedStyle(document.body,'::after').content,
                            background:getComputedStyle(document.body,'::after').backgroundImage,
                            clouds:getComputedStyle(document.querySelector('#prototype-cloud-surface')).display});
                        const before = wash(); closePage();
                        return {before, after:wash(), closing:document.querySelector('.mini-window-container').classList.contains('closing')};
                    }''')
                    page.screenshot(path=str(args.output / f'clouds-C-{width}-closing.png'))
                    assert state['closing'] and state['before']['content'] != 'none', state
                    assert state['after'] == state['before'], 'Reading backdrop disappears before content: ' + str(state)
                    page.wait_for_timeout(500)
                    assert page.evaluate("getComputedStyle(document.body,'::after').content === 'none'")
                    assert page.locator('#prototype-cloud-surface').evaluate("el => getComputedStyle(el).display") == 'none'
                    page.evaluate("openPage('/hobbies/gaming')")
                    page.wait_for_timeout(100)
                    page.evaluate('closePage()')
                    page.wait_for_timeout(80)
                    page.evaluate("openPage('/hobbies/gaming')")
                    page.wait_for_timeout(500)
                    expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Gaming')
                    expect(page.locator('.mini-window-container')).to_have_class('mini-window-container open')
                    page.get_by_role('button', name='Next prototype', exact=True).click()
                    expect(page.locator('html')).to_have_attribute('data-grounding', 'A')
                    assert page.evaluate("getComputedStyle(document.body,'::after').content === 'none'")
                    for variant in ('B', 'C'):
                        page.get_by_role('button', name='Next prototype', exact=True).click()
                        expect(page.locator('html')).to_have_attribute('data-grounding', variant)
                        expect(page.frame_locator('.mini-window').locator('#location')).to_have_text('Gaming')
                    page.emulate_media(reduced_motion='reduce')
                    page.keyboard.press('Escape')
                    page.wait_for_timeout(30)
                    assert page.evaluate("getComputedStyle(document.body,'::after').content === 'none'")
                    page.evaluate("window.themeEngine.activate('canonical')")
                    expect(page.locator('html')).to_have_attribute('data-board-theme', 'canonical')
                    expect(page.locator('#prototype-cloud-surface')).to_have_count(0)
                    page.evaluate("window.themeEngine.activate('lily')")
                    expect(page.locator('html')).to_have_attribute('data-board-theme', 'lily')
                    flowers = []
                    for title in ('Gaming', 'ScribbleScan'):
                        page.evaluate('title => centerOnTile(title)', title)
                        page.wait_for_timeout(40)
                        flower = page.locator('.expanded .tile-expanded').evaluate('''surface => {
                            const bloom=surface.querySelector('[data-visual-axis="accent"][data-visual-value="2"]');
                            const a=bloom.getBoundingClientRect();
                            const writing=[...surface.querySelectorAll('.expanded-title,.expanded-text,.expanded-open')]
                                .map(node => node.getBoundingClientRect()).filter(b => b.width && b.height);
                            return {bloom:a.toJSON(), writing:writing.map(b => b.toJSON()),
                                clear:writing.length>0 && writing.every(b =>
                                    a.right+2<=b.left || a.left>=b.right+2 || a.bottom+2<=b.top || a.top>=b.bottom+2)};
                        }''')
                        assert flower['clear'], (title, flower)
                        flowers.append({'title': title, **flower})
                        page.screenshot(path=str(args.output / f'lily-{width}-{title.lower()}.png'))
                    assert errors == [], errors
                    receipt['views'].append({'width': width, 'exit': state, 'flowers': flowers, 'errors': errors})
                    context.close()
                    print(f'{width}: cloud exit/reopen/comparison/teardown and lily writing clearance passed', flush=True)
            finally:
                browser.close()
        receipt['status'] = 'passed'
    except Exception as error:
        receipt['status'] = 'failed'
        receipt['error'] = str(error)
        raise
    finally:
        (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()
