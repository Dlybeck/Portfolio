#!/usr/bin/env python3
"""Compile Postcard swaps. Vinyl's accepted SVGs are now authored pack assets.

The historical picture-disc renderer below is not the approved sleeve design;
do not run it over the authored Vinyl pack.
"""
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
    circle(pressing, 120, 120, 113, '#242629', stroke='#111618', stroke_width=1.5,
           data_theme_record='disc')
    palette = axis(record, 'palette', f['palette'])
    # Picture-disc print beneath a clear grooved face, not an oversized label.
    circle(palette, 120, 120, 101, '#f6edda')
    for r in range(103+f['pressing'], 113, 3):
        circle(pressing, 120, 120, r, 'none', stroke='#696761', stroke_width='.55')
    circle(palette, 120, 120, 3, '#282528', data_theme_spindle='hole')
    circle(palette, 120, 120, 6, 'none', stroke='#b3a792', stroke_width='.7')
    art = axis(palette, 'artwork', f['artwork'])
    orient = axis(art, 'orientation', f['orientation'],
                  transform=f'rotate({(f["orientation"]-3)*2} 120 120)')
    # Small album-cover landscape, printed into the face above the title.
    path(orient, 'M65 46Q120 -2 175 46Z', color)
    path(orient, f'M68 46L{94+f["artwork"]*7} {23+f["artwork"]*3}L129 46Z', '#626f69')
    path(orient, f'M104 46L{141-f["artwork"]*4} 27L172 46Z', '#a1a899')
    sleeve = node(root, 'g', data_theme_part='sleeve')
    silhouette = axis(sleeve, 'silhouette', f['silhouette'])
    edge = 3 + f['silhouette']*.15
    rect(silhouette, edge, 3, 234, 234, color, stroke='#aa9172', stroke_width=1)
    seam = axis(sleeve, 'seam', f['seam'])
    path(seam, f'M{8+f["seam"]} 13V231H228', stroke='#79654f', stroke_width='.7', opacity='.45')
    # Open mouth at the top of the jacket, where the same record emerges.
    path(seam, 'M99 3Q120 11 141 3', stroke='#79654f', stroke_width=1, opacity='.55')
    # Printed sleeve graphic stays with the sleeve throughout the exchange.
    rect(seam, 38, 25, 164, 63, '#f6edda')
    circle(seam, 168, 43, 10, color)
    path(seam, f'M38 88L{82+f["artwork"]*7} 38L137 88Z', '#626f69')
    path(seam, f'M96 88L{153-f["artwork"]*4} 47L202 88Z', '#a1a899')
    reveal = {'contentPart':'record', 'titlePart':'record', 'parts':{
        'record':pose(scale=.5),
        'sleeve':pose(scale=.5, foreground=True),
    }}
    return reveal, (53,132,134,79), (53,56,134,45), (78,106,84,38), '59 59 122 122'


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
    root = ET.Element(f'{{{NS}}}svg', {'viewBox':'0 0 240 240' if theme=='vinyl' else '0 -60 240 320',
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
    if state == 'expanded' and theme == 'vinyl':
        rect(root, 41, 103, 158, 80, 'none', data_theme_carrier_title_area='title')
    rect(root, *content, 'none', data_theme_content_area='content')
    return ET.tostring(root, encoding='unicode')+'\n', reveal


def main():
    for theme in ('postcards',):
        folder = ROOT/'static/themes'/theme
        tiles = json.loads((folder/'tiles.json').read_text())
        for assignment in tiles['assignments'].values():
            for state in ('base','expanded'):
                svg, reveal = compile_svg(theme, assignment['factors'], state)
                (folder/assignment[state]).write_text(svg)
            assignment['reveal'] = reveal
            if theme == 'postcards':
                assignment['swap'] = {'movingPart':'card', 'carrierPart':'front', 'liftY':-85}
            else:
                assignment['swap'] = {'movingPart':'record', 'carrierPart':'sleeve', 'liftY':-122}
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
                      'expanded-title-line-height':'1.1', 'focus-motion':'swap',
                      'cover-enter-duration':'.8s', 'cover-exit-duration':'.8s',
                      'expanded-width':'440px', 'expanded-min-height':'440px',
                      'phone-expanded-width':'min(410px, calc(100vw + 12px))',
                      'phone-expanded-min-height':'410px', 'expanded-text-line-height':'1.2',
                      'expanded-gap':'5px', 'action-treatment':'annotation',
                      'action-border':'0', 'action-shadow':'none', 'link-bg':'transparent',
                      'action-text-decoration':'underline', 'action-radius':'0'})
        else:
            b.update({'focus-motion':'swap', 'cover-enter-duration':'.8s', 'cover-exit-duration':'.8s'})
        (folder/'presentation.json').write_text(json.dumps(presentation, indent=2, ensure_ascii=False)+'\n')
        print(f'Compiled {b["focus-motion"]} for {theme}')


if __name__ == '__main__':
    main()
