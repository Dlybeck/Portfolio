"""The focused collection must leave visible paths to its neighbors."""
import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize('width,height', [
    (705, 863), (390, 844), (1440, 900), (320, 568), (844, 390),
    (600, 800), (601, 800), (600, 400),
])
def test_vinyl_home_leaves_visible_connector_runs(width, height, browser_page):
    page, origin = browser_page
    page.emulate_media(reduced_motion='reduce')
    page.set_viewport_size({'width': width, 'height': height})
    page.goto(f'{origin}/?theme=vinyl', wait_until='networkidle')
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)
    disc = page.locator('.expanded [data-swap-part="record"] [data-theme-record="disc"]')
    bounds = disc.bounding_box()
    assert abs(bounds['width'] - bounds['height']) < 1
    # Relationship groups follow tilesData's edge order. Sample the real paths,
    # counting uninterrupted pixels outside every tile's painted SVG shapes.
    runs = page.evaluate('''() => {
        const edges=Object.entries(window.tilesData).flatMap(([parent,children]) =>
            children.map(child=>({parent,child})));
        const shapes=[...document.querySelectorAll('.tile-container svg *')]
            .filter(n=>typeof n.isPointInFill==='function' && getComputedStyle(n).fill!=='none'
                && getComputedStyle(n).visibility!=='hidden'
                && !n.closest('defs,clipPath,mask')
                && !n.closest('[aria-hidden="true"].tile-base'));
        function painted(n,point) {
            for(let a=n;a && !a.classList.contains('tile-container');a=a.parentElement) {
                const s=getComputedStyle(a);
                if(s.display==='none' || Number(s.opacity)===0) return false;
            }
            const matrix=n.getScreenCTM();
            return matrix && n.isPointInFill(point.matrixTransform(matrix.inverse()));
        }
        return [...document.querySelectorAll('.arrows-group > g')].flatMap((group,i)=>{
            if(edges[i].parent!=='Home')return [];
            const path=group.querySelector('path'), length=path.getTotalLength();
            let run=0,longest=0;
            for(let d=0;d<=length;d+=2) {
                const point=path.getPointAtLength(d).matrixTransform(path.getScreenCTM());
                const visible=point.x>=0 && point.x<innerWidth && point.y>=0 && point.y<innerHeight
                    && !shapes.some(n=>painted(n,point));
                run=visible ? run+2 : 0;
                longest=Math.max(longest,run);
            }
            return [{neighbor:edges[i].child,visibleRun:longest}];
        });
    }''')
    assert len(runs) == 4
    assert all(edge['visibleRun'] >= 24 for edge in runs), runs
