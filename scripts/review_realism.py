"""Capture the complete installed catalog and record material-fit evidence."""
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path('/tmp/portfolio-realism-baseline')
THEMES = ('canonical', 'lily', 'planets', 'islands', 'vinyl', 'postcards', 'botanical', 'workbench')


def main():
    OUT.mkdir(exist_ok=True)
    label_checks = []
    rendered = {}
    with sync_playwright() as p:
        browser = p.chromium.connect('ws://127.0.0.1:3000/')
        for width, height in ((1440,900), (390,844)):
            page = browser.new_page(viewport={'width':width,'height':height}, reduced_motion='reduce')
            for theme in THEMES:
                for name, route in (('home','/'), ('long-copy','/?unused=1#ScribbleScan'), ('document','/hobbies/tennis')):
                    path, _, fragment = route.partition('#')
                    separator = '&' if '?' in path else '?'
                    page.goto(f'http://127.0.0.1:51354{path}{separator}theme={theme}'+('#'+fragment if fragment else ''), wait_until='networkidle')
                    page.evaluate('document.fonts.ready')
                    rendered[f'{theme}-{width}-{name}'] = page.locator('html').get_attribute('data-board-theme')
                    if name == 'document':
                        page.frame_locator('.mini-window').locator('#location').wait_for()
                        page.frame_locator('.mini-window').locator('body').evaluate('() => document.fonts.ready')
                    page.screenshot(path=str(OUT/f'{theme}-{width}-{name}.png'))
                    if theme == 'vinyl' and name != 'document' and rendered[f'{theme}-{width}-{name}'] == 'vinyl':
                        label_checks.append(page.evaluate('''() => {
                            const tile=document.querySelector('.tile-container.expanded');
                            const label=tile.querySelector('[data-theme-size="expanded"] [data-theme-part="record"] [data-visual-axis="palette"] circle');
                            const roles=[...tile.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector')];
                            return {width:innerWidth,title:tile.dataset.title,labelDiameter:label.getBoundingClientRect().width,
                                optimisticRequiredHeight:roles.reduce((sum,n)=>sum+n.clientHeight,0),
                                roles:roles.map(n=>({role:n.className,width:n.clientWidth,height:n.clientHeight,font:getComputedStyle(n).fontSize}))};
                        }'''))
            page.close()
        gallery = browser.new_page(viewport={'width':1200,'height':900})
        for width in (1440,390):
            for name in ('home','long-copy','document'):
                cards=''.join('<figure><img src="data:image/png;base64,'+base64.b64encode((OUT/f'{t}-{width}-{name}.png').read_bytes()).decode()+'"><figcaption>'+t+(' (disabled; fallback)' if rendered[f'{t}-{width}-{name}'] != t else '')+'</figcaption></figure>' for t in THEMES)
                gallery.set_content('<style>body{background:#ddd;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font:16px sans-serif}figure{margin:0}img{width:100%}figcaption{text-align:center}</style>'+cards)
                gallery.screenshot(path=str(OUT/f'catalog-{width}-{name}.png'),full_page=True)
        gallery.close(); browser.close()
    (OUT/'vinyl-label-capacity.json').write_text(json.dumps(label_checks,indent=2))
    (OUT/'rendered-catalog.json').write_text(json.dumps(rendered,indent=2))
    print(json.dumps(label_checks,indent=2))
    print('Capture complete:', OUT)


if __name__ == '__main__':
    main()
