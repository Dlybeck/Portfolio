#!/usr/bin/env python3
"""Compile active Postcard Swap and retain the dormant Vinyl reference."""
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_collection_themes import NS, WORLDS, axis, circle, landscape, node, path, rect


def pose(x=0, y=0, scale=1, origin_y=120, **extra):
    return dict(x=x, y=y, scale=scale, originX=120, originY=origin_y, **extra)


def vinyl(root, f, color):
    record = node(root, 'g', data_theme_part='record')
    pressing = axis(record, 'pressing', f['pressing'])
    circle(pressing, 120, 75, 74, '#242629', stroke='#111618', stroke_width=1.5,
           data_theme_record='disc')
    for r in range(50+f['pressing'], 73, 5):
        circle(pressing, 120, 75, r, 'none', stroke='#515251', stroke_width='.6')
    palette = axis(record, 'palette', f['palette'])
    circle(palette, 120, 75, 44, color)
    circle(palette, 120, 75, 2.7, '#161c1d')
    # A small registration ring and lower label bars leave a clear title above
    # the spindle. The description is printed on the jacket, not the grooves.
    circle(palette, 120, 75, 7, 'none', stroke='#655a4c', stroke_width='.5', opacity='.55')
    art = axis(record, 'artwork', f['artwork'])
    orient = axis(art, 'orientation', f['orientation'],
                  transform=f'rotate({f["orientation"]-3} 120 98)')
    for i in range(2+f['artwork']):
        path(orient, f'M{110+i*2} {91+i*4}H{130-i*2}', stroke='#5b5550', stroke_width=1)
    sleeve = node(root, 'g', data_theme_part='sleeve')
    silhouette = axis(sleeve, 'silhouette', f['silhouette'])
    edge = 45 + f['silhouette']*.3
    rect(silhouette, edge, 115, 150, 150, color, stroke='#aa9172', stroke_width=1)
    seam = axis(sleeve, 'seam', f['seam'])
    path(seam, f'M{49+f["seam"]} 124V259H187', stroke='#79654f', stroke_width='.7', opacity='.45')
    # Open mouth at the top of the jacket, where the same record emerges.
    path(seam, 'M101 115Q120 125 139 115', stroke='#79654f', stroke_width=1, opacity='.55')
    reveal = {'contentPart':'sleeve', 'titlePart':'record', 'parts':{
        'record':pose(y=48, scale=.64, origin_y=150),
        'sleeve':pose(y=-25.6, scale=.64, origin_y=150),
    }}
    return reveal, (57,133,126,116), (88,46,64,27), (79,132,82,39), '60 92 120 116'


def postcards(root, f, color):
    paper = '#fff2d9'
    back = node(root, 'g', data_theme_part='back')
    silhouette = axis(back, 'silhouette', f['silhouette'])
    rect(silhouette, 20, 25, 200+f['silhouette']*.2, 150, '#d8bc94', stroke='#a78762', stroke_width=1)
    card = node(root, 'g', data_theme_part='card')
    palette = axis(card, 'palette', f['palette'])
    rect(palette, 25, 30, 190, 140, paper, stroke=color, stroke_width=1)
    art = axis(card, 'landscape', f['landscape'], transform='translate(5 20) scale(.96 .4)')
    landscape(art, f['landscape'], color)
    front = node(root, 'g', data_theme_part='front')
    path(front, 'M20 25L120 90L220 25V175H20Z', '#ecd6b5', stroke='#ab8b66', stroke_width=1)
    path(front, 'M20 175L60 143M220 175L180 143', stroke='#c2a582', stroke_width='.7')
    # Small sealing tab, not postage on the flap side of an envelope.
    seal = axis(front, 'postage', f['postage'])
    orient = axis(seal, 'orientation', f['orientation'], transform=f'rotate({f["orientation"]-3} 120 105)')
    node(orient, 'ellipse', cx=120, cy=105, rx=5+f['postage']*.5, ry=4+f['postage']*.5, fill=color)
    flap = node(root, 'g', data_theme_part='flap')
    envelope = axis(flap, 'envelope', f['envelope'])
    path(envelope, f'M20 25L120 {-50+f["envelope"]*2}L220 25Z', '#e7cfae', stroke='#ab8b66', stroke_width=1)
    reveal = {'contentPart':'card', 'parts':{
        'back':pose(scale=.52, origin_y=100),
        'card':pose(scale=.52, origin_y=100),
        'front':pose(scale=.52, origin_y=100, foreground=True),
        'flap':pose(y=36, scale=.52, origin_y=25, flipY=-1, foreground=True),
    }}
    return reveal, (36,58,168,103), None, (86,104,68,30), '55 45 130 110'


def compile_svg(theme, factors, state):
    root = ET.Element(f'{{{NS}}}svg', {'viewBox':'0 0 240 300' if theme=='vinyl' else '0 -60 240 320',
        'preserveAspectRatio':'xMidYMid meet', 'opacity':'1', 'aria-hidden':'true', 'focusable':'false'})
    renderer = vinyl if theme == 'vinyl' else postcards
    reveal, content, title, base_content, base_view = renderer(root, factors, WORLDS[theme]['palette'][factors['palette']])
    if state == 'base':
        root.set('viewBox', base_view)
        for part in root:
            p = reveal['parts'][part.get('data-theme-part')]
            part.set('transform', f'translate({p["x"]} {p["y"]}) translate({p["originX"]} {p["originY"]}) scale({p["scale"]} {p["scale"]*p.get("flipY",1)}) translate({-p["originX"]} {-p["originY"]})')
        content = base_content
    elif title:
        rect(root, *title, 'none', data_theme_title_area='title')
    if state == 'expanded' and theme == 'postcards':
        rect(root, 55, 108, 130, 58, 'none', data_theme_carrier_title_area='title')
    rect(root, *content, 'none', data_theme_content_area='content')
    return ET.tostring(root, encoding='unicode')+'\n', reveal


def main():
    for theme in ('vinyl', 'postcards'):
        folder = ROOT/'static/themes'/theme
        tiles = json.loads((folder/'tiles.json').read_text())
        for assignment in tiles['assignments'].values():
            for state in ('base','expanded'):
                svg, reveal = compile_svg(theme, assignment['factors'], state)
                (folder/assignment[state]).write_text(svg)
            assignment['reveal'] = reveal
            if theme == 'postcards':
                assignment['swap'] = {'movingPart':'card', 'carrierPart':'front', 'liftY':-85}
        (folder/'tiles.json').write_text(json.dumps(tiles, indent=2)+'\n')
        presentation = json.loads((folder/'presentation.json').read_text())
        b = presentation['board']
        b.update({'focus-motion':'reveal', 'cover-enter-duration':'.65s', 'cover-exit-duration':'.65s',
                  'cover-enter-easing':'cubic-bezier(.22,.65,.25,1)',
                  'expanded-width':'420px', 'expanded-min-height':'430px',
                  'phone-expanded-width':'min(390px, calc(100vw + 12px))',
                  'phone-expanded-min-height':'430px', 'expanded-text-size':'1.125rem',
                  'phone-expanded-text-size':'1rem'})
        if theme == 'vinyl':
            b.update({'font-expanded-title':"'Patrick Hand', cursive", 'expanded-title-size':'1.25rem',
                      'expanded-title-line-height':'1.02'})
        else:
            b.update({'focus-motion':'swap', 'cover-enter-duration':'1.1s', 'cover-exit-duration':'1.1s'})
        (folder/'presentation.json').write_text(json.dumps(presentation, indent=2, ensure_ascii=False)+'\n')
        print(f'Compiled {b["focus-motion"]} for {theme}')


if __name__ == '__main__':
    main()
