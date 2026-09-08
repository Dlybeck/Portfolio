"""Connections express adjacency, never a one-way route."""
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_selectable_themes_use_two_arrowheads_or_none():
    for manifest_path in sorted((ROOT / 'static/themes').glob('*/theme.json')):
        manifest = json.loads(manifest_path.read_text())
        if not manifest['selection']['enabled']:
            continue
        presentation = json.loads((manifest_path.parent / manifest['presentation']).read_text())
        connectors = presentation['connectors']
        assert (connectors['headStyle'] == 'none'
                or connectors['headPosition'] in ('none', 'both')), manifest['id']


@pytest.mark.parametrize('theme', ['vinyl', 'postcards'])
@pytest.mark.parametrize('width,height', [(390, 844), (705, 863), (1440, 900)])
def test_arrowed_connections_keep_the_existing_neighbors(theme, width, height, browser_page):
    page, origin = browser_page
    page.emulate_media(reduced_motion='reduce')
    page.set_viewport_size({'width': width, 'height': height})
    page.goto(f'{origin}/?theme={theme}#ScribbleScan', wait_until='networkidle')
    rendered = page.locator('.arrows-group > g').evaluate_all('''groups => {
        const layer=document.querySelector('.tile-layer').getBoundingClientRect();
        const positions=Object.entries(window.positions).map(([title,p])=>({title,
            x:p.left/100*layer.width,y:p.top/100*layer.height}));
        function nearest(point) {
            return positions.reduce((best,p)=>Math.hypot(p.x-point.x,p.y-point.y)
                < Math.hypot(best.x-point.x,best.y-point.y) ? p : best).title;
        }
        return groups.map(group=>{
            const line=group.querySelector('path');
            return {pair:[nearest(line.getPointAtLength(0)),
                nearest(line.getPointAtLength(line.getTotalLength()))].sort(),
                paths:group.querySelectorAll('path').length};
        });
    }''')
    # Literal accepted graph; nearby screen positions are not extra edges.
    expected = {
        ('Home', 'Hobbies'), ('Home', 'Projects'), ('Home', 'Work Experience'),
        ('Home', 'Education'), ('Hobbies', '3D Printing'), ('Hobbies', 'Gaming'),
        ('Hobbies', 'Tennis'), ('3D Printing', 'Other Models'), ('3D Printing', 'Puzzles'),
        ('Projects', 'Programs'), ('Projects', 'Websites'), ('Websites', 'Digital Planner'),
        ('Websites', 'This website'), ('Websites', 'ScribbleScan'),
        ('Education', 'College'), ('Education', 'Early Education'),
    }
    assert len(rendered) == len(expected)
    assert {tuple(edge['pair']) for edge in rendered} == {tuple(sorted(pair)) for pair in expected}
    assert all(edge['paths'] == 3 for edge in rendered)  # line plus two arrowheads
