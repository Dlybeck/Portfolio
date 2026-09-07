#!/usr/bin/env python3
"""Capture review evidence from an existing preview; do not alter site files."""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import quote, urlparse

from playwright.sync_api import sync_playwright

try:
    from scripts.check_grounding import source_fingerprint
except ModuleNotFoundError:
    from check_grounding import source_fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True, help='Existing private preview origin.')
    parser.add_argument('--theme', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    parsed = urlparse(args.origin)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        parser.error('Use an HTTP(S) preview origin without credentials.')
    if any(not re.fullmatch(r'[a-z][a-z0-9-]*', theme) for theme in args.theme):
        parser.error('Use theme identifiers, not paths.')
    origin = args.origin.rstrip('/')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'status': 'incomplete', 'origin': origin, 'local_source': source_fingerprint(),
                'visual_review': 'required', 'captures': [], 'page_errors': []}
    def save():
        (out / 'capture.json').write_text(json.dumps(manifest, indent=2) + '\n')
    save()
    try:
        with sync_playwright() as playwright:
            endpoint = os.environ.get('PLAYWRIGHT_WS_ENDPOINT')
            browser = playwright.chromium.connect(endpoint) if endpoint else playwright.chromium.launch()
            try:
                for theme in args.theme:
                    for width, height in ((390, 844), (1440, 900)):
                        context = browser.new_context(viewport={'width': width, 'height': height},
                            is_mobile=width == 390, has_touch=width == 390, reduced_motion='reduce')
                        page = context.new_page()
                        page.on('pageerror', lambda error: manifest['page_errors'].append(str(error)))
                        cards = []
                        def capture(label):
                            name = f'{theme}-{width}-{label}.webp'
                            page.screenshot(path=str(out / name), type='webp', quality=85)
                            manifest['captures'].append({'file': name, 'url': page.url,
                                'theme': theme, 'width': width, 'state': label})
                            cards.append((label, out / name))
                            save()
                        for label, route in (
                            ('home', '/'), ('long-copy', '/#ScribbleScan'),
                            ('reading', '/projects/programs'), ('photos', '/hobbies/tennis'),
                        ):
                            path, _, fragment = route.partition('#')
                            page.goto(f'{origin}{path}?theme={theme}' +
                                (f'#{quote(fragment)}' if fragment else ''), wait_until='networkidle')
                            page.evaluate('document.fonts.ready')
                            if page.locator('html').get_attribute('data-board-theme') != theme:
                                raise RuntimeError(f'{theme} did not activate; refusing fallback evidence.')
                            capture(label)
                        page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
                        page.emulate_media(reduced_motion='no-preference')
                        for direction, destination in (('enter', 'Hobbies'), ('exit', 'Home')):
                            page.evaluate('title=>window.centerOnTile(title)', destination)
                            started = time.monotonic()
                            for target_ms in (0, 150, 400, 900):
                                page.wait_for_timeout(max(0, target_ms - (time.monotonic()-started)*1000))
                                capture(f'{direction}-{target_ms}')
                                manifest['captures'][-1]['elapsed_ms'] = round((time.monotonic()-started)*1000)
                        gallery = browser.new_page(viewport={'width': 1440, 'height': 900})
                        html = ''.join('<figure><img src="data:image/webp;base64,' +
                            base64.b64encode(file.read_bytes()).decode() + '"><figcaption>' +
                            label + '</figcaption></figure>' for label, file in cards)
                        gallery.set_content('<style>body{background:#ddd;display:grid;grid-template-columns:'
                            'repeat(4,1fr);gap:8px;font:16px sans-serif}figure{margin:0}img{width:100%}</style>'+html)
                        gallery.screenshot(path=str(out / f'{theme}-{width}-sheet.png'), full_page=True)
                        gallery.close()
                        context.close()
            finally:
                browser.close()
        manifest['status'] = 'captured' if not manifest['page_errors'] else 'captured-with-errors'
    finally:
        save()
    print(f"{manifest['status']}: {out}; images still require visual inspection")


if __name__ == '__main__':
    main()
