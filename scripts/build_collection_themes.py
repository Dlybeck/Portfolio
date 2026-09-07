#!/usr/bin/env python3
"""Compile four grounded collection worlds into declarative Theme Packs.

Authoring only: the application consumes the resulting SVG and JSON files.
Run from any directory; reruns replace only these four generated packs.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.theme_packs import BOARD_LOCATIONS
from scripts.scaffold_theme_pack import slug, write_json

PACKS = ROOT / 'static/themes'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
WORLDS = {
    'vinyl': dict(label='Vinyl Collection', paper='#f4e8ce', ink='#282528',
                  accent='#9b4537', muted='#8d755f', background='#514239',
                  palette=['#efbe83', '#dbacaa', '#adc1c0', '#ddd19f', '#bcb4cc'],
                  artifact='none', motion='cover'),
    'botanical': dict(label='Botanical Collection', paper='#f6f0d9', ink='#293d2c',
                      accent='#456b43', muted='#8b9876', background='#64705b',
                      palette=['#71874c', '#7c9366', '#4e796a', '#a09548', '#866d7e'],
                      artifact='field-notebook', motion='settle'),
    'workbench': dict(label="Maker’s Workbench", paper='#e9f1ec', ink='#214e65',
                      accent='#9a4424', muted='#669496', background='#224f50',
                      palette=['#306585', '#496f83', '#386f69', '#596c8c', '#6c697b'],
                      artifact='field-notebook', motion='cover'),
    'postcards': dict(label='Postcards & Letters', paper='#fff2d9', ink='#594038',
                      accent='#9c493d', muted='#b29774', background='#b28c66',
                      palette=['#719dad', '#c38162', '#83936b', '#9986a1', '#688c94'],
                      artifact='none', motion='cover'),
}


def node(parent, tag, **attrs):
    return ET.SubElement(parent, f'{{{NS}}}{tag}',
                         {key.replace('_', '-'): str(value) for key, value in attrs.items()})


def axis(parent, name, value, **attrs):
    return node(parent, 'g', data_visual_axis=name, data_visual_value=value, **attrs)


def path(parent, d, fill='none', **attrs):
    return node(parent, 'path', d=d, fill=fill, **attrs)


def rect(parent, x, y, width, height, fill, **attrs):
    return node(parent, 'rect', x=x, y=y, width=width, height=height, fill=fill, **attrs)


def circle(parent, cx, cy, r, fill, **attrs):
    return node(parent, 'circle', cx=cx, cy=cy, r=r, fill=fill, **attrs)


def mark(parent, name, value, **attrs):
    return dict(data_visual_axis=name, data_visual_value=value,
                data_visual_scope='self', **attrs)


def seed(theme, title, channel):
    return int.from_bytes(hashlib.sha256(f'{theme}:{title}:{channel}'.encode()).digest()[:4], 'big')


def mount(parent, f, kind='tape'):
    g = axis(parent, 'mount', f['mount'])
    x = 39 + f['mount'] * 27
    a = axis(g, 'orientation', f['orientation'],
             transform=f"rotate({(f['orientation']-3)*3} {x+14} 19)")
    if kind == 'clip':
        rect(a, x, 7, 24, 18, '#3e484a', rx=2)
        path(a, f'M{x+5} 16V4Q{x+12} -2 {x+19} 4V16', stroke='#bbc8c5', stroke_width=2)
    else:
        path(a, f'M{x} 11L{x+31} 9L{x+29} 25L{x-1} 26Z',
             '#d8caa0', opacity='.72', stroke='#b2a57f', stroke_width='.6')
    return g


def vinyl(root, f, color, state):
    palette = axis(root, 'palette', f['palette'])
    radius = 72 + f['pressing'] * 2
    pressing = axis(palette, 'pressing', f['pressing'])
    circle(pressing, 161, 99, radius, '#242629', stroke='#111618', stroke_width=2,
           data_theme_record='disc')
    for r in range(32, int(radius)-5, 9):
        circle(pressing, 161, 99, r, 'none', stroke='#454849', stroke_width='.7')
    circle(pressing, 161, 99, 25, color)
    circle(pressing, 161, 99, 4, '#514239')
    cut = f['silhouette']
    # A record jacket is square, with enough clearance for the circular disc.
    shape = f'M13 {18+cut}H{176-cut}V181H13Z'
    path(palette, shape, color, stroke='#c6ac87', stroke_width=1.4,
         **mark(root, 'silhouette', cut))
    # Jacket art is printed in the upper band; the lower area is its liner label.
    art = axis(palette, 'artwork', f['artwork'])
    orientation = axis(art, 'orientation', f['orientation'],
                       transform=f"rotate({(f['orientation']-3)*2} 94 43)")
    if f['artwork'] == 0:
        for i in range(3):
            path(orientation, f'M{56+i*10} 57V48Q{56+i*10} {28+i*7} 94 {28+i*7}'
                 f'Q{132-i*10} {28+i*7} {132-i*10} 48V57',
                 stroke='#604b45', stroke_width=2.2, opacity='.75')
    elif f['artwork'] == 1:
        for i in range(3):
            circle(orientation, 69+i*25, 43, 12-i*2, ['#694d49','#f8ead1','#345b60'][i])
    else:
        path(orientation, 'M48 54L72 31L96 54L119 31L143 54Z', '#4d6261')
    seam = axis(palette, 'seam', f['seam'])
    path(seam, f'M{16+f["seam"]} 27V173H166', stroke='#705b47', stroke_width='.7', opacity='.5')
    # The sleeve mouth belongs on the record-facing edge.
    edge = 176-cut
    path(seam, f'M{edge} {78+f["seam"]*3}Q{edge-12} 99 {edge} {120-f["seam"]*3}',
         stroke='#705b47', stroke_width=1, opacity='.55')
    return (26, 68, 136, 65) if state == 'base' else (24, 68, 140, 102)


def specimen(parent, species, color):
    g = node(parent, 'g', transform='translate(114 58)')
    if species % 4 == 0:  # a fern frond
        path(g, 'M-40 5Q0 -23 39 -5', stroke='#536243', stroke_width=1.6)
        for i in range(7):
            x = -34 + i*10
            y = -8 - (1-abs(i-3)/3)*9
            path(g, f'M{x} {y}Q{x-13} {y-21} {x-3} {y-20}Q{x+3} {y-9} {x} {y}Z', color)
            path(g, f'M{x} {y}Q{x-12} {y+11} {x-12} {y+16}Q{x} {y+13} {x} {y}Z', color)
    elif species % 4 == 1:  # rounded paired leaves
        path(g, 'M-35 4Q0 -9 41 -31', stroke='#69724f', stroke_width=1.5)
        for i in range(4):
            x = -26+i*18
            node(g, 'ellipse', cx=x, cy=-7-i*5, rx=12, ry=7, fill=color,
                 transform=f'rotate(-26 {x} {-7-i*5})')
            node(g, 'ellipse', cx=x+5, cy=5-i*5, rx=10, ry=6, fill=color,
                 transform=f'rotate(25 {x+5} {5-i*5})')
    elif species % 4 == 2:  # pressed wildflower sprig
        path(g, 'M-31 7Q-9 -8 26 -26M-9 -5L-16 -30', stroke='#6c8250', stroke_width=2)
        for x,y in [(26,-26),(-16,-30)]:
            for dx,dy in [(0,-7),(7,-2),(4,6),(-5,6),(-7,-3)]:
                node(g, 'ellipse', cx=x+dx, cy=y+dy, rx=5, ry=7, fill=color)
            circle(g, x, y, 3, '#caaa52')
        path(g, 'M-17 -2Q-28 -21 -35 -14Q-30 0 -17 -2Z', '#879763')
    else:  # broad lobed leaf
        path(g, 'M-7 7L-4 -3M-4 -3L-32 -12L-23 -20L-33 -30L-14 -30L-10 -47L1 -38L15 -47L19 -29L34 -26L22 -15L24 -5L-4 -3Z', color)
        path(g, 'M-4 -3L2 -32M-4 -3L-21 -23M-4 -3L22 -24', stroke='#f1e8c4', stroke_width='1', opacity='.5')


def botanical(root, f, color, state):
    palette = axis(root, 'palette', f['palette'])
    inset = f['silhouette']
    path(palette, f'M{16+inset} 16H224V{183-inset}H16Z', '#f6f0d9',
         stroke='#c5bea0', stroke_width=1.3, **mark(root,'silhouette',inset))
    art = axis(palette, 'specimen', f['specimen'])
    specimen(art, f['specimen'], color)
    mount(palette, f)
    # Mounting strips secure stems; they are not generic decoration over text.
    strip = axis(palette, 'strip', f['strip'])
    t = .2 + f['strip']*.16
    if f['specimen'] == 3:
        x, y = 114-7+3*t, 58+7-10*t
    else:
        start, control, end = {
            0: ((-40,5),(0,-23),(39,-5)),
            1: ((-35,4),(0,-9),(41,-31)),
            2: ((-31,7),(-9,-8),(26,-26)),
        }[f['specimen']]
        x, y = (offset+(1-t)**2*a+2*(1-t)*t*b+t*t*c
                for offset,a,b,c in zip((114,58),start,control,end))
    rect(strip, round(x-2,2), round(y-5,2), 4, 10, '#e4dab7', opacity='.8',
         transform=f'rotate(-20 {x:.2f} {y:.2f})')
    return (34, 80, 172, 63) if state == 'base' else (34, 74, 172, 101)


def diagram(parent, kind, ink):
    g = node(parent, 'g', stroke=ink, stroke_width=1.4, stroke_linejoin='round')
    if kind % 4 == 0:
        path(g, 'M93 31L119 18L146 32L146 55L119 69L93 55ZM93 31L119 45L146 32M119 45V69')
        path(g, 'M87 32V57M90 59L116 73', stroke_width='.7')
    elif kind % 4 == 1:
        circle(g, 120, 43, 21, 'none')
        circle(g, 120, 43, 9, 'none')
        path(g, 'M89 43H151M120 14V72', stroke_width='.7', stroke_dasharray='3 3')
        for dx,dy in [(-12,-12),(12,-12),(12,12),(-12,12)]:
            circle(g,120+dx,43+dy,2,'none')
    elif kind % 4 == 2:
        path(g,'M79 58H105V30H134V58H160M85 24H99M140 24H154M91 24V58M148 24V58')
        path(g,'M79 64H160M82 62L79 64L82 66M157 62L160 64L157 66',stroke_width='.7')
    else:
        path(g,'M83 30H105V20H136V37H158V59H131V69H103V53H83Z')
        for x,y in [(92,42),(119,31),(144,47),(117,58)]:
            circle(g,x,y,3,'none')


def workbench(root,f,color,state):
    palette = axis(root,'palette',f['palette'])
    shape = f'M17 16H{224-f["silhouette"]}V182H17Z'
    path(palette,shape,'#e9f1ec',stroke='#9bb7b6',stroke_width=1.5,
         **mark(root,'silhouette',f['silhouette']))
    grid = axis(palette,'grid',f['grid'])
    spacing = 8+f['grid']*2
    for x in range(27,217,spacing):
        path(grid,f'M{x} 22V72',stroke='#80a8b7',stroke_width='.45',opacity='.5')
    for y in range(22,73,spacing):
        path(grid,f'M27 {y}H217',stroke='#80a8b7',stroke_width='.45',opacity='.5')
    art = axis(palette,'drawing',f['drawing'])
    diagram(art,f['drawing'],color)
    mount(palette,f,'clip')
    return (30,82,180,60) if state=='base' else (30,77,180,101)


def landscape(parent, kind, color):
    rect(parent,26,29,188,45,color)
    if kind%4==0:  # coast
        circle(parent,174,40,7,'#f8d18b')
        path(parent,'M26 57Q77 46 128 59T214 56V74H26Z','#a4c5c3')
        path(parent,'M26 65Q56 56 96 74H26Z','#ecd098')
    elif kind%4==1:  # mountains
        circle(parent,180,42,8,'#f1d2a2')
        path(parent,'M26 74L74 37L120 74M76 74L137 32L192 74Z','#697b74')
        path(parent,'M119 48L137 32L154 46L141 43L133 49Z','#f1ead9')
    elif kind%4==2:  # rolling fields
        path(parent,'M26 63Q68 34 130 65Q171 43 214 57V74H26Z','#526c51')
        path(parent,'M26 73Q89 47 150 71Q185 55 214 69V74H26Z','#b9b679')
    else:  # evening shore
        circle(parent,125,43,10,'#f0c298')
        path(parent,'M26 60H214V74H26Z','#556f86')
        path(parent,'M106 66H144M111 70H139',stroke='#efd1a6',stroke_width='1.5')


def postcards(root,f,color,state):
    palette=axis(root,'palette',f['palette'])
    # Envelope is behind the illustrated face; stamp belongs to the envelope.
    envelope=axis(palette,'envelope',f['envelope'])
    dx=f['envelope']*2
    path(envelope,f'M{10-dx} 9L225 13L231 178L10 187Z','#e3cfaf',stroke='#ba9a78',stroke_width=1)
    # This is the addressed face, not the flap side: the stamp belongs here.
    mount_group=axis(envelope,'postage',f['postage'])
    stamp=axis(mount_group,'orientation',f['orientation'],transform=f"rotate({f['orientation']-3} 219 23)")
    rect(stamp,208,3,23,31,'#f8edcf',stroke='#9c493d',stroke_width='1.5',stroke_dasharray='2 2')
    rect(stamp,212,7,15,22,color)
    circle(stamp,219,15,3+f['postage'],'#f7ddb1')
    cut=f['silhouette']
    path(palette,f'M19 {21+cut}H220V182H19Z','#fff2d9',stroke='#c1a783',stroke_width=1,
         **mark(root,'silhouette',cut))
    art=axis(palette,'landscape',f['landscape'])
    landscape(art,f['landscape'],color)
    # A handwritten caption sits in the postcard's unprinted margin.
    return (30,87,180,58) if state=='base' else (30,82,180,94)


RENDERERS={'vinyl':vinyl,'botanical':botanical,'workbench':workbench,'postcards':postcards}
AXES={
    'vinyl':dict(silhouette=4,palette=5,orientation=7,pressing=4,artwork=3,seam=4),
    'botanical':dict(silhouette=4,palette=5,orientation=7,specimen=4,mount=5,strip=4),
    'workbench':dict(silhouette=4,palette=5,orientation=7,drawing=4,mount=5,grid=4),
    'postcards':dict(silhouette=4,palette=5,orientation=7,landscape=4,envelope=4,postage=4),
}


def tile(theme,title,state,f):
    root=ET.Element(f'{{{NS}}}svg',{'viewBox':'0 0 240 200','preserveAspectRatio':'xMidYMid meet',
        'aria-hidden':'true','focusable':'false','class':'theme-object','opacity':'1'})
    area=RENDERERS[theme](root,f,WORLDS[theme]['palette'][f['palette']],state)
    rect(root,*area,'none',stroke='none',data_theme_content_area='content')
    return ET.tostring(root,encoding='unicode')+'\n'


def background(theme,c):
    root=ET.Element(f'{{{NS}}}svg',{'viewBox':'0 0 1600 1200','preserveAspectRatio':'xMidYMid slice'})
    rect(root,0,0,1600,1200,c['background'])
    if theme=='workbench':
        # A cutting mat's measured grid is purposefully regular, unlike water/stars.
        for x in range(0,1601,40):
            path(root,f'M{x} 0V1200',stroke='#6b9390',stroke_width=1,opacity='.19')
        for y in range(0,1201,40):
            path(root,f'M0 {y}H1600',stroke='#6b9390',stroke_width=1,opacity='.19')
        for x in range(0,1601,200):
            path(root,f'M{x} 0V1200',stroke='#81aba4',stroke_width=1,opacity='.17')
    elif theme in ('vinyl','postcards'):
        # Quiet long wood-grain contours, not high-frequency photographic noise.
        for i in range(12):
            y=70+i*103
            path(root,f'M-40 {y}C390 {y-29} 740 {y+34} 1640 {y-14}',
                 stroke='#291f1d' if theme=='vinyl' else '#7c593e',stroke_width=1.4,opacity='.16')
    else:
        # Plain cloth specimen table; only widely spaced weave hints.
        for i in range(10):
            x=85+i*174
            path(root,f'M{x} 0L{x+30} 1200',stroke='#a1ab8b',stroke_width=1,opacity='.1')
    return ET.tostring(root,encoding='unicode')+'\n'


def presentation(theme,c):
    data=deepcopy(json.loads((PACKS/'islands/presentation.json').read_text()))
    b,d=data['board'],data['document']
    ink,paper,accent,muted=c['ink'],c['paper'],c['accent'],c['muted']
    # Replace inherited palette references, then assign material-specific slots.
    replacements={'#23534d':ink,'#173c38':ink,'#001007':ink,'#426b61':muted,
                  '#267487':accent,'#226f73':accent,'#17657a':accent,'#0e5365':ink,
                  '#3b867c':muted,'#68a69a':muted,'#6b9c83':muted,'#f2e3b4':paper,
                  '#f2e3b8':paper,'#fff8d6':paper,'#fffbed':paper,'#fff9df':paper,
                  '#e6d9aa':paper,'#e1d19a':paper,'#287f9d':c['background']}
    for group in (b,d):
        for key,value in group.items():
            if isinstance(value,str):
                for old,new in replacements.items(): value=value.replace(old,new)
                group[key]=value
    b.update({'ambient-display':'none','board-bg-image':'none','board-bg-color':c['background'],
      'shell-bg':c['background'],'nav-radius':'3px','control-radius':'4px','selector-radius':'3px',
      'nav-logo-filter':'none','control-icon-filter':'none','action-radius':'4px',
      'action-border':f'1px solid {muted}','link':ink,'link-bg':paper,'focus':paper,
      'control-hover-bg':paper,'control-hover-shadow':'0 4px 8px rgba(0,0,0,.2)',
      'nav-border':muted,'control-border':muted,'nav-border-width':'1px','control-border-width':'1px',
      'tile-shadow':'drop-shadow(3px 5px 3px rgba(0,0,0,.22))',
      'tile-hover-shadow':'drop-shadow(5px 8px 6px rgba(0,0,0,.25))',
      'viewer-artifact':c['artifact'],'viewer-artifact-label':{'vinyl':'LINER NOTES','botanical':'FIELD COLLECTION',
      'workbench':'PROJECT NOTEBOOK','postcards':'CORRESPONDENCE'}[theme],
      'viewer-artifact-ink':paper,'viewer-artifact-accent':accent,'viewer-artifact-detail':muted,
      'viewer-bg':paper,'viewer-bg-image':'none','viewer-border':muted,'viewer-border-width':'1px',
      'viewer-radius':'2px','viewer-shadow':'4px 12px 24px rgba(0,0,0,.28)',
      'viewer-padding':'32px 30px 38px','phone-viewer-padding':'24px 16px 30px',
      'viewer-rotation':'-.2deg','focus-motion':c['motion'],'tile-size':'180px','phone-tile-size':'154px',
      'expanded-width':'420px','expanded-min-height':'390px',
      'phone-expanded-width':'min(390px, calc(100vw + 12px))','phone-expanded-min-height':'380px',
      'base-title-size':'1.3rem','base-title-line-height':'1.15','expanded-title-size':'1.6rem',
      'expanded-text-size':'1.125rem','phone-expanded-text-size':'1rem','expanded-gap':'6px',
      'cover-enter-duration':'.4s','cover-exit-duration':'.28s','cover-enter-offset':'-48vh',
      'cover-enter-rotation':'-5deg','cover-enter-scale':'.94','cover-exit-offset':'-48vh',
      'cover-exit-rotation':'3deg','cover-exit-scale':'.94',
      'hover-lift':'-3px','hover-scale':'1.035','loading-bg':paper,'loading-ink':ink,
      'loading-radius':'3px','loading-shadow':'2px 4px 8px rgba(0,0,0,.2)'})
    d.update({'page-bg':paper,'page-bg-image':'none','page-bg-size':'auto',
       'secondary-ink':ink,'caption-ink':ink,
       'panel-bg':'transparent','panel-border':'transparent','panel-border-width':'0',
       'button-bg':accent,'button-ink':paper,'button-border':accent,'button-hover-bg':ink,
       'button-radius':'3px','form-button-radius':'3px','field-radius':'3px',
       'result-radius':'3px','model-radius':'3px','model-bg':paper,'model-border':muted,
       'model-shadow':'0 3px 8px rgba(0,0,0,.15)','code-radius':'3px','header-radius':'3px',
       'link-hover-decoration':'underline','action-hover-text-decoration':'underline',
       'separator-display':'block','separator-height':'1px','separator-opacity':'.3',
       'focus':accent,'bullet-marker':"'• '", 'panel-max-width':'min(100%, 72ch)'})
    if theme in ('botanical','workbench'):
        b.update({'viewer-padding':'32px 28px 42px 54px','phone-viewer-padding':'24px 16px 34px 30px',
                  'viewer-artifact-detail':'#f8f3df','viewer-artifact-accent':muted})
    if theme=='workbench':
        d['page-bg-image']='repeating-linear-gradient(0deg, transparent 0 27px, rgba(50,110,135,.10) 27px 28px)'
        d['page-bg-size']='auto'
        b['font-expanded-title']="'Architects Daughter', cursive"
        d['font-title']=d['font-heading']="'Architects Daughter', cursive"
    if theme=='vinyl':
        b['font-navbar']=b['font-expanded-title']="Georgia, serif"
        b['font-navbar-weight']='700'
        d['font-title']=d['font-heading']='Georgia, serif'
        d['font-body']=d['font-link']='Arial, sans-serif'
        d['body-size']='1rem'
        b['viewer-border-width']='8px'
        b['viewer-border']=accent
    if theme=='postcards':
        b['viewer-bg']='#e3cfaf'
        b['viewer-bg-image']='repeating-linear-gradient(130deg, #af5147 0 8px, #f4e8ce 8px 16px, #577f9a 16px 24px, #f4e8ce 24px 32px)'
        b['viewer-padding']='24px'
        b['phone-viewer-padding']='16px 12px'
        b['viewer-shadow']='3px 8px 18px rgba(64,43,28,.28)'
    connectors=data['connectors']
    connectors.update({'color':{'vinyl':'#c5b199','botanical':'#dfdfbf','workbench':'#b7cebf','postcards':'#695241'}[theme],
        'strokeWidth':2.3,'opacity':.62,'dashPattern':'short' if theme in ('postcards','workbench') else 'none',
        'headStyle':'open','headPosition':'end','headLen':14,'headHalf':5,
        'wobble':.08,'haloWidth':1,'haloOpacity':0,'insetFactor':9})
    return data


def main():
    for theme,c in WORLDS.items():
        if theme == 'vinyl':
            # Owner-approved packaging is authored directly in its pack; this
            # historical sketch generator must not overwrite it.
            continue
        folder=PACKS/theme
        assets=folder/'assets/tiles'
        assets.mkdir(parents=True,exist_ok=True)
        assignments={}
        for title in sorted(BOARD_LOCATIONS):
            factors={axis:seed(theme,title,axis)%count for axis,count in AXES[theme].items()}
            name=slug(title)
            for state in ('base','expanded'):
                (assets/f'{name}-{state}.svg').write_text(tile(theme,title,state,factors))
            rotation=(seed(theme,title,'placement')%81-40)/10
            assignments[title]={'base':f'assets/tiles/{name}-base.svg',
              'expanded':f'assets/tiles/{name}-expanded.svg','factors':factors,
              'transforms':{'base':{'rotationDegrees':rotation,'offsetXPixels':0,'offsetYPixels':0},
                            'expanded':{'rotationDegrees':round(rotation*.35,2),'offsetXPixels':0,'offsetYPixels':0},
                            'detailRotationDegrees':0},
              'motion':{'durationOffsetMilliseconds':seed(theme,title,'duration')%31-15,
                        'rotationOffsetDegrees':0,'offsetXPixels':0,'offsetYPixels':0,'scaleOffset':0}}
        (folder/'assets/background.svg').write_text(background(theme,c))
        write_json(folder/'tiles.json',{'assignments':assignments})
        write_json(folder/'presentation.json',presentation(theme,c))
        write_json(folder/'theme.json',{'$schema':'portfolio-theme-pack/v1','id':theme,'label':c['label'],
          'version':1,'tiles':'tiles.json','presentation':'presentation.json',
          'background':[{'asset':'assets/background.svg','depth':1.0}],
          'selection':{'enabled':theme in ('postcards','vinyl'),'randomEligible':theme == 'postcards','randomWeight':1}})
        print(f'Built {theme}: {len(assignments)} locations')

    # Keep the single authoring command reproducible: the two selected worlds
    # use physical assemblies instead of the initial cover-style sketches.
    from scripts.refine_collection_reveals import main as refine_reveals
    refine_reveals()


if __name__=='__main__':
    main()
