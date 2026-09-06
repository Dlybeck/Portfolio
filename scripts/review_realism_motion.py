"""Capture real navigation transitions for every retained visual world."""
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    out=Path('/tmp/realism-motion-final'); out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.connect('ws://127.0.0.1:3000/')
        for width,height in ((390,844),(1440,900)):
            page=browser.new_page(viewport={'width':width,'height':height})
            for theme in ('canonical','lily','planets','islands','postcards'):
                page.goto(f'http://127.0.0.1:51354/?theme={theme}',wait_until='networkidle')
                page.wait_for_timeout(1300)
                frames=[]
                for destination in ('Hobbies','Home'):
                    page.evaluate('t=>window.centerOnTile(t)',destination)
                    for index,delay in enumerate((0,280,370,650)):
                        page.wait_for_timeout(delay)
                        filename=out/f'{theme}-{width}-{destination}-{index}.png'
                        page.screenshot(path=str(filename))
                        frames.append((f'{destination} — frame {index}',filename))
                gallery=browser.new_page(viewport={'width':1200,'height':900})
                cards=''.join('<figure><img src="data:image/png;base64,'+base64.b64encode(f.read_bytes()).decode()+'"><figcaption>'+label+'</figcaption></figure>' for label,f in frames)
                gallery.set_content('<style>body{background:#ddd;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font:14px sans-serif}figure{margin:0}img{width:100%}figcaption{text-align:center}</style>'+cards)
                gallery.screenshot(path=str(out/f'{theme}-{width}-sequence.png'),full_page=True)
                gallery.close()
            page.close()
        browser.close()
    print('Motion captures complete:',out)


if __name__=='__main__':
    main()
