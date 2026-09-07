"""THROWAWAY capture of A/B/C in their real board/document context."""
from pathlib import Path
import argparse
import base64
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--vinyl', action='store_true')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
with sync_playwright() as p:
    browser = p.chromium.connect('ws://127.0.0.1:3000/')
    for width, height in ((390,844),(1440,900)):
        context = browser.new_context(viewport={'width':width,'height':height},
            is_mobile=width==390,has_touch=width==390,reduced_motion='reduce')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        scenes = (('vinyl','/','vinyl-home'), ('vinyl','/#ScribbleScan','vinyl-long')) if args.vinyl else (
            ('clouds','/','cloud-board'), ('clouds','/hobbies/gaming','cloud-page'), ('lily','/','pond-board'))
        for theme, route, label in scenes:
            captures = []
            for variant in ('BC' if theme == 'vinyl' else 'ABC'):
                path, _, fragment = route.partition('#')
                page.goto(f'http://127.0.0.1:51355{path}?theme={theme}&grounding={variant}#{fragment}',
                    wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.locator('#grounding-prototype').wait_for()
                page.wait_for_timeout(150)
                file = args.output / f'{label}-{width}-{variant}.png'
                page.screenshot(path=str(file))
                captures.append((variant,file))
            gallery = browser.new_page(viewport={'width':min(1440,width*len(captures)),'height':height})
            markup = ''.join('<figure><figcaption>'+v+'</figcaption><img src="data:image/png;base64,'+
                base64.b64encode(file.read_bytes()).decode()+'"></figure>' for v,file in captures)
            gallery.set_content('<style>body{margin:0;background:#ddd;display:grid;grid-template-columns:'
                f'repeat({len(captures)},1fr);gap:6px' + '}figure{margin:0}img{width:100%}figcaption{font:20px sans-serif}</style>'+markup)
            gallery.screenshot(path=str(args.output/f'{label}-{width}-comparison.png'),full_page=True)
            gallery.close()
        print(f'{width}px: {errors or "no page errors"}',flush=True)
        context.close()
    browser.close()
