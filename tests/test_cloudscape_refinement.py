"""Acceptance checks for the full composition, not just text in declared boxes."""
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('width',[320,390,1440])
def test_unfocused_cloud_titles_are_visually_centered(width,browser_page):
    page,origin=browser_page
    page.set_viewport_size({'width':width,'height':844})
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme=clouds',wait_until='networkidle')
    errors=page.locator('.tile-base').evaluate_all('''nodes=>nodes.flatMap(tile=>{
        const path=tile.querySelector('[data-visual-axis="silhouette"] path');
        const box=path.getBBox();
        let xSum=0,ySum=0,count=0;
        // Painted-area centroid approximates the visual mass of an irregular
        // cloud, unlike the transparent square viewport or its tallest lobe.
        for(let y=box.y;y<box.y+box.height;y+=3)
            for(let x=box.x;x<box.x+box.width;x+=3)
                if(path.isPointInFill(new DOMPoint(x,y))){xSum+=x;ySum+=y;count++;}
        const center=new DOMPoint(xSum/count,ySum/count).matrixTransform(path.getScreenCTM());
        const title=tile.querySelector('.scrap-title').getBoundingClientRect();
        const art=path.getBoundingClientRect();
        const dx=Math.abs(title.x+title.width/2-center.x)/art.width;
        const dy=Math.abs(title.y+title.height/2-center.y)/art.height;
        return dx>.07 || dy>.07 ? [{title:tile.getAttribute('aria-label'),dx,dy}] : [];
    })''')
    assert not errors,errors


@pytest.mark.parametrize('width',[320,390,1440])
@pytest.mark.parametrize('title',['Gaming','Hobbies','Work Experience','Education','Projects','3D Printing'])
def test_cloud_grow_starts_at_the_existing_cloud_size(width,title,browser_page):
    page,origin=browser_page
    page.set_viewport_size({'width':width,'height':844})
    page.goto(f'{origin}/?theme=clouds',wait_until='networkidle')
    measured=page.evaluate('''async title => {
        window.centerOnTile(title);
        await new Promise(requestAnimationFrame);
        const tile=document.querySelector('.expanded');
        const surface=tile.querySelector('.tile-expanded');
        const animation=surface.getAnimations().find(a=>a.animationName==='focus-grow-enter');
        animation.pause(); animation.currentTime=0;
        const selector='[data-visual-axis="silhouette"] path';
        const rect=n=>{const r=n.getBoundingClientRect();
            return {width:r.width,height:r.height,x:r.x+r.width/2,y:r.y+r.height/2};};
        return {base:rect(tile.querySelector('.tile-base '+selector)),
            start:rect(surface.querySelector(selector))};
    }''',title)
    for dimension in ('width','height','x','y'):
        assert abs(measured['base'][dimension]-measured['start'][dimension])<4,measured


def test_cloud_responsive_scale_updates_and_does_not_leak_to_other_packs(browser_page):
    page,origin=browser_page
    page.goto(f'{origin}/?theme=clouds',wait_until='networkidle')
    tile=page.locator('.expanded')
    value=lambda: tile.evaluate("t=>Number(t.style.getPropertyValue('--theme-object-size-ratio'))")
    desktop=value()
    page.set_viewport_size({'width':320,'height':844})
    page.wait_for_function('''desktop=>Number(document.querySelector('.expanded')
        .style.getPropertyValue('--theme-object-size-ratio'))>desktop''',arg=desktop)
    for theme in ('canonical','lily','planets','islands','postcards'):
        page.evaluate('theme=>window.themeEngine.activate(theme)',theme)
        assert page.locator('.tile-container').evaluate_all('''ns=>ns.every(t=>
            !t.style.getPropertyValue('--theme-object-size-ratio') &&
            !t.style.getPropertyValue('--theme-pack-cover-enter-scale') &&
            !t.style.getPropertyValue('--theme-pack-cover-exit-scale'))''')


@pytest.mark.parametrize('touch',[False,True])
def test_cloud_neighbor_document_round_trip(touch,request):
    page,origin=request.getfixturevalue('mobile_browser_page' if touch else 'browser_page')
    page.goto(f'{origin}/?theme=clouds#Hobbies',wait_until='networkidle')
    gaming=page.get_by_role('button',name='Go to Gaming',exact=True)
    if touch:
        gaming.tap()
        page.get_by_role('link',name='Open Gaming').tap()
    else:
        gaming.focus()
        page.keyboard.press('Enter')
        expect(page.get_by_role('link',name='Open Gaming')).to_be_focused()
        page.keyboard.press('Space')
    page.locator('.mini-window-container.open').wait_for()
    expect(page.frame_locator('.mini-window').locator('html')).to_have_attribute('data-board-theme','clouds')
    page.keyboard.press('Escape')
    expect(page).to_have_url(f'{origin}/?theme=clouds#Gaming')
    page.get_by_role('button',name='Go to Hobbies',exact=True).click()
    expect(page).to_have_url(f'{origin}/?theme=clouds#Hobbies')


@pytest.mark.parametrize('width',[320,390,768,1440])
def test_clouds_painted_bounds_and_neighbors_stay_usable(width,browser_page):
    page,origin=browser_page
    page.set_viewport_size({'width':width,'height':844 if width<768 else 900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(f'{origin}/?theme=clouds',wait_until='networkidle')
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)
    problems=page.evaluate('''async () => {
        const problems=[];
        for(const title of Object.keys(window.tileInfo)) {
            window.centerOnTile(title);
            await new Promise(requestAnimationFrame);
            await new Promise(requestAnimationFrame);
            const tile=document.querySelector('.tile-container.expanded');
            const path=tile.querySelector('[data-theme-size="expanded"] [data-visual-axis="silhouette"] path');
            const b=path.getBoundingClientRect();
            if(b.left<12 || b.right>innerWidth-12) problems.push(title+': cloud outside viewport gutters');
            for(const n of document.querySelectorAll('.connected .tile-base')) {
                const label=n.querySelector('.scrap-title').getBoundingClientRect();
                if(label.left<0 || label.right>innerWidth || label.top<0 || label.bottom>innerHeight)
                    problems.push(title+': neighbor label clipped: '+n.getAttribute('aria-label'));
                const r=n.getBoundingClientRect();
                const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                if(!hit || !(hit===n || n.contains(hit))) problems.push(title+': neighbor blocked');
            }
            const inverse=path.getScreenCTM().inverse();
            for(const n of tile.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector')) {
                const r=n.getBoundingClientRect();
                for(const [x,y] of [[r.left+2,r.top+2],[r.right-2,r.top+2],
                    [r.left+2,r.bottom-2],[r.right-2,r.bottom-2]]) {
                    if(!path.isPointInFill(new DOMPoint(x,y).matrixTransform(inverse)))
                        problems.push(title+': text/control leaves painted cloud: '+n.className);
                }
            }
        }
        return problems;
    }''')
    assert not problems,problems


def test_cloudscape_uses_distinct_shapes_and_existing_depth_grammar(browser_page):
    from scripts.cloudscape_art import PROFILES,sky_svg
    page,origin=browser_page
    page.goto(f'{origin}/?theme=clouds',wait_until='networkidle')
    assert len({p[1] for p in PROFILES})==6
    shapes=page.locator('[data-theme-size="base"] [data-visual-axis="silhouette"] path').evaluate_all(
        'ns=>ns.map(n=>({d:n.getAttribute("d"),aspect:n.getBBox().width/n.getBBox().height}))')
    assert len({s['d'] for s in shapes})==6
    assert max(s['aspect'] for s in shapes)-min(s['aspect'] for s in shapes)>.4
    layers=page.locator('[data-theme-background]')
    assert layers.count()==2
    assert layers.evaluate_all('ns=>ns.map(n=>Number(n.dataset.themeDepth))')==[.12,.3]
    assert layers.evaluate_all('ns=>ns.every(n=>getComputedStyle(n).pointerEvents==="none")')
    before=layers.evaluate_all('ns=>ns.map(n=>getComputedStyle(n).transform)')
    page.emulate_media(reduced_motion='reduce')
    page.get_by_role('button',name='Go to Hobbies',exact=True).click()
    after=layers.evaluate_all('ns=>ns.map(n=>getComputedStyle(n).transform)')
    assert all(a!=b for a,b in zip(before,after))
    assert (ROOT/'static/themes/clouds/assets/sky-far.svg').read_text()==sky_svg()
    assert (ROOT/'static/themes/clouds/assets/sky-near.svg').read_text()==sky_svg(near=True)
    manifest=json.loads((ROOT/'static/themes/clouds/theme.json').read_text())
    assert manifest['selection']['enabled'] and not manifest['selection']['randomEligible']
