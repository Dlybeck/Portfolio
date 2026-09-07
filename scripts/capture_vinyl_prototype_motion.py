"""THROWAWAY: controlled Swap frames, narrow-phone fit and control restoration."""
from pathlib import Path
import argparse
import base64
import json
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--variant', choices=['B', 'C'])
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
receipt = []
with sync_playwright() as p:
    browser = p.chromium.connect('ws://127.0.0.1:3000/')
    for width, height in ((320,740), (390,844), (1440,900)):
        for variant in (args.variant or 'BC'):
            context = browser.new_context(viewport={'width':width,'height':height},
                is_mobile=width<500,has_touch=width<500,reduced_motion='reduce')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'http://127.0.0.1:51355/?theme=vinyl&grounding={variant}',wait_until='networkidle')
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(100)
            cards = []

            def capture(name):
                file = args.output / f'{width}-{variant}-{name}.png'
                page.screenshot(path=str(file))
                cards.append((name,file))

            capture('home-reduced')
            page.emulate_media(reduced_motion='no-preference')
            page.clock.install()
            page.evaluate("window.centerOnTile('Hobbies')")
            for name, step in (('extract',230),('clear',150),('place',160),('focused',400)):
                page.clock.run_for(step)
                capture(name)
            # Reverse before Home finishes extracting, then settle back on Hobbies.
            page.evaluate("window.centerOnTile('Home')")
            page.clock.run_for(280)
            capture('return-interrupted')
            page.evaluate("window.centerOnTile('Hobbies')")
            page.clock.run_for(200)
            capture('reverse')
            page.clock.run_for(1000)
            capture('settled')
            receipt.append({'width':width,'variant':variant,'errors':errors,
                'state':page.evaluate("""() => ({current:window.currentTileTitle,
                  tiles:[...document.querySelectorAll('[data-theme-swap]')].filter(t=>t.classList.contains('expanded')).map(t=>({
                    title:t.dataset.title,progress:t.dataset.swapProgress,fit:t.dataset.themeContentFit,
                    bounds:t.querySelector('.tile-expanded').getBoundingClientRect().toJSON()}))})""")})
            gallery = browser.new_page(viewport={'width':1440,'height':900})
            markup = ''.join('<figure><figcaption>'+name+'</figcaption><img src="data:image/png;base64,'+
                base64.b64encode(file.read_bytes()).decode()+'"></figure>' for name,file in cards)
            gallery.set_content('<style>body{margin:0;background:#ddd;display:grid;grid-template-columns:'
                'repeat(4,1fr);gap:6px}figure{margin:0}img{width:100%}figcaption{font:18px sans-serif}</style>'+markup)
            gallery.screenshot(path=str(args.output/f'{width}-{variant}-sheet.png'),full_page=True)
            gallery.close()
            context.close()
    browser.close()
print(json.dumps(receipt,indent=2))
(args.output / 'receipt.json').write_text(json.dumps(receipt,indent=2) + '\n')
