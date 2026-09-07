"""One-shot preservation of owner-approved B prototypes before integration.

Exports inert artwork and screenshots, never executable runtime theme code.
Use a fresh output directory. The comparison runner remains private.
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--origin', default='http://127.0.0.1:51355')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with sync_playwright() as p:
        browser = p.chromium.connect('ws://127.0.0.1:3000/')
        for width, height in ((390, 844), (1440, 900)):
            context = browser.new_context(viewport={'width': width, 'height': height},
                reduced_motion='reduce', is_mobile=width == 390, has_touch=width == 390)
            page = context.new_page()
            for theme in ('vinyl', 'clouds', 'lily', 'canonical'):
                for name, route in (('home', '/'), ('long', '/#ScribbleScan'),
                                    ('page', '/hobbies/tennis')):
                    path, _, fragment = route.partition('#')
                    page.goto(f'{args.origin}{path}?theme={theme}&grounding=B#{fragment}',
                              wait_until='networkidle')
                    page.evaluate('document.fonts.ready')
                    page.wait_for_function("document.documentElement.dataset.grounding === 'B'")
                    page.screenshot(path=str(args.output / f'{theme}-{width}-{name}.png'))
                    if width == 1440 and theme == 'vinyl' and name == 'home':
                        data = page.locator('.tile-container').evaluate_all('''tiles => Object.fromEntries(tiles.map(tile => {
                            const base = tile.querySelector('.tile-base [data-theme-size="base"]').cloneNode(true);
                            const expanded = tile.querySelector('.tile-expanded [data-theme-size="expanded"]').cloneNode(true);
                            const record = tile.querySelector('[data-swap-part="record"] [data-theme-part="record"]').cloneNode(true);
                            const sleeve = tile.querySelector('.tile-base [data-theme-part="sleeve"]').cloneNode(true);
                            expanded.querySelector('[data-theme-part="record"]').replaceWith(record);
                            expanded.querySelector('[data-theme-part="sleeve"]').replaceWith(sleeve);
                            const paper = record.querySelector('[data-prototype-inner-sleeve]').getAttribute('fill');
                            const surround = sleeve.querySelector('[data-visual-axis="silhouette"] rect').getAttribute('fill');
                            for (const svg of [base,expanded]) {
                                for (const el of [svg,...svg.querySelectorAll('*')]) {
                                    for (const attr of [...el.attributes]) {
                                        if (attr.name === 'style' || attr.name === 'class' || attr.name.startsWith('data-prototype-')) el.removeAttribute(attr.name);
                                    }
                                }
                            }
                            record.children[1].setAttribute('data-theme-detail', 'disc');
                            record.children[1].removeAttribute('transform');
                            record.children[1].querySelector('circle[r="3"]').setAttribute('data-theme-spindle', 'true');
                            record.children[2].setAttribute('data-theme-material', 'paper');
                            return [tile.dataset.title,{base:base.outerHTML,expanded:expanded.outerHTML,
                                readingSurface:{pageColor:paper,surroundColor:surround}}];
                        }))''')
                        (args.output / 'vinyl-artwork.json').write_text(json.dumps(data, indent=2) + '\n')
                    if width == 1440 and theme == 'clouds' and name == 'page':
                        svg = page.locator('#prototype-cloud-surface').evaluate('''svg => {
                            const copy=svg.cloneNode(true); copy.removeAttribute('id');
                            copy.setAttribute('xmlns','http://www.w3.org/2000/svg'); return copy.outerHTML;
                        }''')
                        (args.output / 'mist-bank.svg').write_text(svg + '\n')
            context.close()
        browser.close()
    print(f'Approved baseline and inert art exported to {args.output}', flush=True)


if __name__ == '__main__':
    main()
