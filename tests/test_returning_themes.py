import json
from pathlib import Path
import shutil
import pytest
from playwright.sync_api import expect

from core.theme_packs import load_theme_pack, InvalidThemeAsset
from scripts.audit_theme_variants import audit_world

ROOT=Path(__file__).resolve().parents[1]


def test_independent_swap_can_split_print_around_a_physical_feature(tmp_path):
    folder=tmp_path/'independent-disc'
    shutil.copytree(ROOT/'static/themes/vinyl',folder)
    manifest=json.loads((folder/'theme.json').read_text())
    manifest['id']='independent-disc'
    (folder/'theme.json').write_text(json.dumps(manifest))
    pack=load_theme_pack(folder)
    assert pack.id=='independent-disc'
    assert all(tile.reveal.title_part==tile.swap.moving_part for _,tile in pack.tiles)
    data=json.loads((folder/'tiles.json').read_text())
    data['assignments']['Home']['reveal']['titlePart']='sleeve'
    (folder/'tiles.json').write_text(json.dumps(data))
    with pytest.raises(InvalidThemeAsset): load_theme_pack(folder)


@pytest.mark.parametrize('width',[320,390,1440])
def test_sleeve_print_stays_on_its_paper_and_cleans_up_on_switch(width,browser_page):
    page,origin=browser_page
    page.set_viewport_size({'width':width,'height':844})
    page.goto(f'{origin}/?theme=vinyl',wait_until='networkidle')
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)
    problems=page.locator('.tile-container').evaluate_all('''tiles => tiles.flatMap(tile=>{
        const layer=tile.querySelector('[data-swap-part="record"]');
        // The accepted design prints on a full inner sleeve, not on the disc.
        // Its paper can correctly cover the hidden spindle hole beneath it.
        const paper=layer.querySelector('[data-theme-material="paper"]').getBoundingClientRect();
        return [...layer.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector')]
            .filter(n=> {const b=n.getBoundingClientRect();
                return b.left<paper.left-2 || b.right>paper.right+2 || b.top<paper.top-2 || b.bottom>paper.bottom+2;
            }).map(n=>tile.dataset.title+':'+n.className);
    })''')
    assert not problems,problems
    page.evaluate("window.themeEngine.activate('canonical')")
    expect(page.locator('[data-swap-title],.theme-swap-layer')).to_have_count(0)
    expect(page.locator('.expanded-title')).to_have_count(17)
    assert page.locator('.expanded .expanded-title').evaluate("n=>n.style.left")==''
    page.evaluate("window.themeEngine.activate('vinyl')")
    expect(page.locator('[data-swap-title]')).to_have_count(17)


def test_cloud_variants_remain_visible(browser_page):
    page,origin=browser_page
    result=audit_world(page,origin,'clouds')
    assert result['passed'],result


def test_cloud_assets_match_authoring_recipe():
    from scripts.revisit_cloudscape import cloud_svg
    tiles=json.loads((ROOT/'static/themes/clouds/tiles.json').read_text())
    for tile in tiles['assignments'].values():
        for state in ('base','expanded'):
            assert (ROOT/'static/themes/clouds'/tile[state]).read_text()==cloud_svg(tile['factors'],state)
