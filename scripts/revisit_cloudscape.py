#!/usr/bin/env python3
"""Author Cloudscape's cumulus study and weather notebook as inert pack data."""
from copy import deepcopy
import json
from pathlib import Path
from scripts.build_collection_themes import seed
from scripts.cloudscape_art import cloud_svg, sky_svg, FAMILIES

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'static/themes/clouds'


def main():
    tiles = json.loads((FOLDER/'tiles.json').read_text())
    for title, assignment in tiles['assignments'].items():
        assignment['factors']['silhouette'] = FAMILIES[title]
        for state in ('base', 'expanded'):
            (FOLDER/assignment[state]).write_text(cloud_svg(assignment['factors'], state))
            assignment['transforms'][state]['rotationDegrees'] = (seed('clouds',title,'tilt')%21-10)/10
        assignment['motion']['durationOffsetMilliseconds'] = seed('clouds',title,'pace')%41-20
    (FOLDER/'tiles.json').write_text(json.dumps(tiles,indent=2)+'\n')
    # Start from the already accepted notebook grammar, not rounded blue panels.
    presentation = deepcopy(json.loads((ROOT/'static/themes/lily/presentation.json').read_text()))
    replacements = {'#173f35':'#263d50','#315f50':'#40576a','#2f7254':'#476981',
        '#6c9c70':'#8a9da7','#f7ffe9':'#fffdf5','#dcecc5':'#e8edf0',
        '#245e45':'#2f4c61','#4b8763':'#637e90','#83aa70':'#8a9da7',
        '#d5e9bd':'#e8edf0','#d9ebc5':'#e8edf0','#f5ffe8':'#fffdf5'}
    for section in ('board','document'):
        for key, value in presentation[section].items():
            for old,new in replacements.items(): value = value.replace(old,new)
            presentation[section][key] = value
    b,d = presentation['board'],presentation['document']
    for role in ('font-navbar','font-base-title','font-expanded-title','font-expanded-text','font-action','control-font'):
        b[role] = "'Patrick Hand', cursive"
    b.update({'ink':'#263d50','link':'#263d50','link-bg':'#fffdf5',
        'text-shadow':'none','board-bg-color':'#80b6d2',
        'board-bg-image':'linear-gradient(180deg, #6fa9ca, #bbd9e4)', 'board-bg-size':'auto',
        'ambient-display':'none','shell-bg':'#80b6d2',
        'tile-shadow':'drop-shadow(0 4px 2px rgba(49,79,95,.12))',
        'tile-hover-shadow':'drop-shadow(0 5px 3px rgba(49,79,95,.17))',
        'nav-bg':'#f7f8f2','nav-border':'#819aab','nav-ink':'#263d50','nav-radius':'5px',
        'nav-logo-filter':'none','control-icon-filter':'none','control-bg':'#f7f8f2',
        'control-border':'#819aab','control-ink':'#263d50','control-radius':'5px',
        'action-border':'1px solid #849cad','action-shadow':'0 2px 0 rgba(49,79,95,.16)',
        'action-radius':'4px','selector-bg':'#fffdf5','selector-ink':'#263d50','selector-border':'#849cad',
        'focus-motion':'grow','cover-enter-scale':'var(--theme-object-size-ratio, .43)',
        'cover-exit-scale':'var(--theme-object-size-ratio, .43)',
        'cover-enter-duration':'.38s','cover-exit-duration':'.24s',
        'hover-lift':'-2px','hover-scale':'1.025',
        'content-area-space':'svg','tile-size':'180px','phone-tile-size':'142px',
        'expanded-width':'420px','expanded-min-height':'380px',
        'phone-expanded-width':'min(338px, calc(87vw - 32px))','phone-expanded-min-height':'340px',
        'expanded-title-size':'1.5rem','expanded-text-size':'1.125rem',
        'phone-expanded-text-size':'1rem','expanded-text-line-height':'1.2',
        'expanded-gap':'6px','base-title-size':'1.18rem',
        'viewer-artifact':'field-notebook','viewer-artifact-label':'SKY OBSERVATIONS',
        'viewer-artifact-accent':'#6f8798','viewer-artifact-ink':'#263d50',
        'viewer-artifact-detail':'#f7f4e8','viewer-bg':'#d1dce0',
        'viewer-bg-image':'none','viewer-border':'#6f8798','viewer-radius':'8px',
        'viewer-rotation':'0deg','loading-bg':'#fffdf5','loading-ink':'#263d50'})
    d.update({'page-bg':'#faf7ec','page-bg-image':'none','page-bg-size':'auto',
        'ink':'#263d50','secondary-ink':'#40576a','caption-ink':'#40576a','title-ink':'#263d50',
        'link':'#365c78','panel-bg':'transparent','panel-radius':'0','panel-shadow':'none',
        'media-bg':'#fffdf5','media-border':'#fffdf5','media-radius':'2px',
        'code-bg':'#e8edf0','header-bg':'#476981','header-border':'1px solid #819aab',
        'field-radius':'3px','result-radius':'3px','model-radius':'3px','code-radius':'3px',
        'body-line-height':'1.5','paragraph-line-height':'1.5','paragraph-margin':'16px 0'})
    presentation['connectors'].update({'color':'#f3f7f5','strokeWidth':1.9,'opacity':.58,
        'wobble':.025,'curveStyle':'varied','dashPattern':'short','haloWidth':1,'haloOpacity':0,
        'variation':{'strokeWidth':.2,'wobble':.02,'dash':.25,'opacity':.12,'markerScale':0}})
    (FOLDER/'presentation.json').write_text(json.dumps(presentation,indent=2)+'\n')
    manifest=json.loads((FOLDER/'theme.json').read_text())
    manifest['background'] = [{'asset':'assets/sky-far.svg','depth':.12},
                              {'asset':'assets/sky-near.svg','depth':.3}]
    (FOLDER/'assets/sky-far.svg').write_text(sky_svg())
    (FOLDER/'assets/sky-near.svg').write_text(sky_svg(near=True))
    manifest['selection'].update(enabled=True,randomEligible=False)
    (FOLDER/'theme.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Compiled Cloudscape: cumulus study + weather notebook')


if __name__=='__main__': main()
