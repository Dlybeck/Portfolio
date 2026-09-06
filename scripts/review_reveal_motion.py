"""Bounded visual evidence for opening and reversing the shared Reveal preset."""
import base64
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    output = Path('/tmp/reveal-motion-review')
    output.mkdir(exist_ok=True)
    measurements = []
    with sync_playwright() as p:
        browser = p.chromium.connect(os.environ.get('PLAYWRIGHT_WS_ENDPOINT', 'ws://127.0.0.1:3000/'))
        for width, height in [(1440, 900), (390, 844)]:
            page = browser.new_page(viewport={'width': width, 'height': height})
            for theme in ('vinyl', 'postcards'):
                page.goto(f'http://127.0.0.1:51354/?theme={theme}', wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.wait_for_timeout(800)
                page.screenshot(path=str(output/f'{theme}-{width}-board.png'))
                # Keep the camera fixed to inspect the actual object's CSS
                # transitions, not a mockup or a separate animation renderer.
                frames = []
                for opening in (False, True):
                    page.evaluate('''opening => {
                        const tile = document.querySelector('[data-title="Home"]');
                        tile.classList.toggle('expanded', opening);
                        getComputedStyle(tile).transform;
                    }''', opening)
                    page.wait_for_timeout(30)
                    page.evaluate('''() => {
                        window.reviewAnimations = document.querySelector('[data-title="Home"]')
                            .getAnimations({subtree:true});
                        window.reviewAnimations.forEach(a => a.pause());
                    }''')
                    for time in (0, 160, 350, 650):
                        page.evaluate('t => window.reviewAnimations.forEach(a => a.currentTime = t)', time)
                        page.evaluate('() => new Promise(requestAnimationFrame)')
                        frame = output/f'{theme}-{width}-{opening}-{time}.png'
                        clip = {'x':max(0,width/2-235), 'y':max(0,height/2-255),
                                'width':min(width,470), 'height':510}
                        page.screenshot(path=str(frame), clip=clip)
                        frames.append((('opening' if opening else 'closing')+f' {time}ms', frame))
                    page.evaluate('window.reviewAnimations.forEach(a => a.finish())')
                measurements.append(page.locator('[data-title="Home"] .tile-expanded').evaluate('''n => ({
                    theme:document.documentElement.dataset.boardTheme, width:innerWidth,
                    parts:[...n.querySelectorAll('[data-theme-size="expanded"] > [data-theme-part]')].map(p => ({
                        name:p.dataset.themePart, matrix:getComputedStyle(p).transform
                    }))})'''))
                gallery = browser.new_page(viewport={'width':1200,'height':1000})
                cards = ''.join('<figure><img src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"><figcaption>'+label+'</figcaption></figure>' for label,path in frames)
                gallery.set_content('<style>body{margin:0;background:#eee;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;font:16px sans-serif}figure{margin:0}img{width:100%}figcaption{text-align:center}</style>'+cards)
                gallery.screenshot(path=str(output/f'{theme}-{width}-motion.png'), full_page=True)
                gallery.close()
            page.close()
        browser.close()
    (output/'measurements.json').write_text(json.dumps(measurements, indent=2))
    print(output)


if __name__ == '__main__':
    main()
