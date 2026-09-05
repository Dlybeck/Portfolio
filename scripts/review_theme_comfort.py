"""Capture actual Board and Document layouts for a bounded visual review.

Usage: python scripts/review_theme_comfort.py --output /tmp/theme-review
Screenshots and measurements are review evidence, not a visual quality score.
"""
import argparse
import base64
import html
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', default='http://127.0.0.1:51353')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    measurements = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect(
            os.environ.get('PLAYWRIGHT_WS_ENDPOINT', 'ws://127.0.0.1:3000/')
        )
        for size, width, height in [('desktop', 1440, 900), ('phone', 390, 844)]:
            context = browser.new_context(
                viewport={'width': width, 'height': height}, reduced_motion='reduce'
            )
            page = context.new_page()
            for theme in ('canonical', 'lily', 'planets', 'islands'):
                page.goto(f'{args.origin}/?theme={theme}', wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.wait_for_function("document.querySelectorAll('[data-theme-content-fit]').length === 17")
                titles = page.evaluate('Object.keys(window.tileInfo)')
                for title in titles:
                    page.evaluate('title => window.centerOnTile(title)', title)
                    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                    tile = page.locator('.tile-container.expanded .tile-expanded')
                    # Locator screenshots scroll transformed map elements into
                    # view, moving the camera. Capture the visible viewport crop
                    # without touching scroll position or navigation instead.
                    bounds = tile.bounding_box()
                    left, top = max(0, bounds['x']), max(0, bounds['y'])
                    clip = {'x': left, 'y': top,
                            'width': min(width, bounds['x'] + bounds['width']) - left,
                            'height': min(height, bounds['y'] + bounds['height']) - top}
                    page.screenshot(path=str(args.output / f'{theme}-{size}-{title}.png'), clip=clip)
                    metrics = tile.evaluate('''node => ({
                        title: node.closest('[data-title]').dataset.title,
                        fit: node.closest('[data-title]').dataset.themeContentFit,
                        text: [...node.querySelectorAll('.expanded-title,.expanded-text,.expanded-open')].map(el => ({
                            role: el.className, size: parseFloat(getComputedStyle(el).fontSize),
                            width: el.clientWidth, height: el.clientHeight,
                            scrollWidth: el.scrollWidth, scrollHeight: el.scrollHeight
                        }))
                    })''')
                    measurements.append({'theme': theme, 'size': size, **metrics})
                    if title in ('Home', 'Work Experience', 'ScribbleScan'):
                        page.screenshot(path=str(args.output / f'{theme}-{size}-{title}-board.png'))
                for name, route in [('tennis','/hobbies/tennis'), ('programs','/projects/programs'), ('models','/hobbies/3d_printing/puzzles')]:
                    page.goto(f'{args.origin}{route}?theme={theme}', wait_until='networkidle')
                    document = page.frame_locator('.mini-window')
                    document.locator('#location').wait_for()
                    document.locator('body').evaluate('() => document.fonts.ready')
                    page.screenshot(path=str(args.output / f'{theme}-{size}-doc-{name}.png'))
            context.close()
        # Contact sheets complement the unmodified individual screenshots.
        gallery = browser.new_page(viewport={'width': 1280, 'height': 900})
        for theme in ('lily', 'planets', 'islands'):
            for size in ('desktop', 'phone'):
                cards = []
                for path in sorted(args.output.glob(f'{theme}-{size}-*.png')):
                    if path.stem.endswith('-board') or '-doc-' in path.stem:
                        continue
                    encoded = base64.b64encode(path.read_bytes()).decode()
                    cards.append(f'<figure><img src="data:image/png;base64,{encoded}"><figcaption>{html.escape(path.stem)}</figcaption></figure>')
                gallery.set_content('<style>body{margin:0;background:#eee;font:14px sans-serif;display:grid;grid-template-columns:repeat(4,1fr);gap:8px}figure{margin:0}img{width:100%;height:300px;object-fit:contain}figcaption{text-align:center;padding:4px}</style>' + ''.join(cards))
                gallery.screenshot(path=str(args.output / f'review-{theme}-{size}.png'), full_page=True)
        gallery.close()
        browser.close()
    (args.output / 'measurements.json').write_text(json.dumps(measurements, indent=2))
    print(f'Review captured at {args.output}')
    for item in measurements:
        if item['fit'] != 'true' or any(t['size'] < 15 and t['role'].startswith('expanded-text') for t in item['text']):
            print(json.dumps(item))


if __name__ == '__main__':
    main()
