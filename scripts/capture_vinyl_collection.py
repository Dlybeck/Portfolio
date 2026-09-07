"""THROWAWAY: view per-location Vinyl B details in the real phone neighborhood."""
import argparse
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
with sync_playwright() as p:
    browser = p.chromium.connect('ws://127.0.0.1:3000/')
    context = browser.new_context(viewport={'width':390,'height':844},
        is_mobile=True,has_touch=True,reduced_motion='reduce')
    page = context.new_page()
    page.goto('http://127.0.0.1:51355/?theme=vinyl&grounding=B',wait_until='networkidle')
    page.evaluate('document.fonts.ready')
    titles = page.locator('.tile-container').evaluate_all('tiles=>tiles.map(t=>t.dataset.title)')
    cards = []
    for index,title in enumerate(titles):
        page.evaluate('title=>window.centerOnTile(title)',title)
        page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
        file = args.output / f'{index:02d}.png'
        page.screenshot(path=str(file))
        cards.append((title,file))
    for offset in range(0,len(cards),6):
        gallery = browser.new_page(viewport={'width':1170,'height':1728})
        gallery.set_content('<style>body{margin:0;background:#ddd;display:grid;grid-template-columns:repeat(3,1fr);gap:4px}figure{margin:0}img{width:100%}figcaption{font:18px sans-serif}</style>'+''.join(
            '<figure><figcaption>'+name+'</figcaption><img src="data:image/png;base64,'+
            base64.b64encode(file.read_bytes()).decode()+'"></figure>' for name,file in cards[offset:offset+6]))
        gallery.screenshot(path=str(args.output/f'sheet-{offset//6}.png'),full_page=True)
        gallery.close()
    context.close()
    browser.close()
print(f'Captured {len(cards)} locations')
