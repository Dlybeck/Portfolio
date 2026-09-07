"""One-time migration of inert, owner-approved comparison artwork into packs.

Input is the preserved export from capture_approved_theme_baseline.py. Normal
theme authoring uses the resulting JSON/SVGs, not the prototype or this script.
"""
import argparse
import json
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'static/themes'


def update_json(path, modify):
    data = json.loads(path.read_text())
    modify(data)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    args = parser.parse_args()
    for theme, profiles, color in (
        ('clouds', [(4.5, 0, .6), (1.8, 10, .38)], '#eef7f9'),
        ('lily', [(1.5, -5, .5), (.8, 6, .32)], '#c3e8e4'),
    ):
        update_json(ROOT / theme / 'presentation.json', lambda p: p['connectors'].update({
            'ribbons': [dict(width=w, offset=o, opacity=a, color=color) for w, o, a in profiles]}))

    (ROOT / 'clouds/assets/mist-bank.svg').write_text((args.baseline / 'mist-bank.svg').read_text())
    update_json(ROOT / 'clouds/theme.json', lambda p: p.update({
        'viewerSurface': {'asset': 'assets/mist-bank.svg', 'outsetX': 18, 'outsetY': 12}}))
    update_json(ROOT / 'clouds/presentation.json', lambda p: p['board'].update({
        'viewer-artifact': 'none', 'viewer-bg': 'transparent', 'viewer-bg-image': 'none',
        'viewer-border-width': '0', 'viewer-radius': '0', 'viewer-shadow': 'none',
        'viewer-rotation': '0deg', 'viewer-padding': '36px 40px 44px',
        'phone-viewer-padding': '28px 18px 32px', 'viewer-enter-offset': '35vw',
        'viewer-enter-rotation': '0deg', 'viewer-exit-offset': '-45vw',
        'viewer-exit-rotation': '0deg', 'viewer-enter-duration': '.38s',
        'viewer-exit-duration': '.24s'}))
    update_json(ROOT / 'clouds/presentation.json', lambda p: p['document'].update({
        'page-bg': '#f4f8f8', 'page-bg-image': 'none', 'ink': '#243e51',
        'title-ink': '#243e51', 'secondary-ink': '#36546a', 'button-bg': '#315f79',
        'button-radius': '6px', 'font-title': "'Patrick Hand', cursive",
        'font-heading': "'Patrick Hand', cursive", 'title-size': '1.65rem',
        'title-margin': '16px 0 12px', 'media-bg': '#f6fafb', 'media-border': '#f6fafb',
        'media-shadow': 'none', 'media-border-width': '3px', 'body-size': '1.125rem',
        'body-line-height': '1.5'}))

    approved = json.loads((args.baseline / 'vinyl-artwork.json').read_text())
    tiles_path = ROOT / 'vinyl/tiles.json'
    tiles = json.loads(tiles_path.read_text())
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    covers, pressings = {}, {}
    for title, tile in tiles['assignments'].items():
        art = approved[title]
        expanded = ET.fromstring(art['expanded'])
        parts = {n.get('data-theme-part'): n for n in expanded if n.get('data-theme-part')}
        record = parts['record']
        disc = record.find('.//*[@data-theme-detail="disc"]')
        disc.attrib.pop('data-theme-detail', None)
        disc.set('data-theme-swap-detail', 'disc')
        disc[0].set('data-theme-record', 'disc')
        jacket = parts['sleeve']
        jacket.attrib.pop('transform', None)
        seam = jacket.find('.//*[@data-visual-axis="seam"]')
        picture = ET.Element('{http://www.w3.org/2000/svg}g')
        for node in list(seam)[2:]:
            seam.remove(node)
            picture.append(node)
        cover_key = tuple(n.get('d', n.tag) for n in picture)
        pressing_key = ET.tostring(disc, encoding='unicode')
        tile['factors']['artwork'] = covers.setdefault(cover_key, len(covers))
        tile['factors']['pressing'] = pressings.setdefault(pressing_key, len(pressings))
        tile['factors']['orientation'] = round(tile['transforms']['base']['rotationDegrees'] * 10)
        picture.set('data-visual-axis', 'artwork')
        picture.set('data-visual-value', str(tile['factors']['artwork']))
        seam.append(picture)
        disc.set('data-visual-axis', 'pressing')
        disc.set('data-visual-value', str(tile['factors']['pressing']))
        silhouette = jacket.find('.//*[@data-visual-axis="silhouette"]')
        palette = ET.Element('{http://www.w3.org/2000/svg}g', {
            'data-visual-axis': 'palette', 'data-visual-value': str(tile['factors']['palette'])})
        for node in list(silhouette):
            silhouette.remove(node)
            palette.append(node)
        silhouette.append(palette)
        for state in ('base', 'expanded'):
            svg = ET.fromstring(art[state])
            for old in list(svg):
                name = old.get('data-theme-part')
                if name not in parts:
                    continue
                replacement = deepcopy(parts[name])
                replacement.attrib.pop('transform', None)
                if state == 'base' and old.get('transform'):
                    replacement.set('transform', old.get('transform'))
                index = list(svg).index(old)
                svg.remove(old)
                svg.insert(index, replacement)
            # Export only shape data; runtime instance identifiers are not art.
            for attr in ('data-theme-object', 'data-theme-size', 'data-theme-identity'):
                svg.attrib.pop(attr, None)
            if 'xmlns' not in svg.attrib and not svg.tag.startswith('{'):
                svg.set('xmlns', 'http://www.w3.org/2000/svg')
            markup = ET.tostring(svg, encoding='unicode')
            (ROOT / 'vinyl' / tile[state]).write_text('\n'.join(line.rstrip() for line in markup.splitlines()) + '\n')
        tile['readingSurface'] = art['readingSurface']
        tile['swap']['details'] = [{'part': 'record', 'element': 'disc', 'x': 0, 'y': -66, 'start': .72}]
    tiles_path.write_text(json.dumps(tiles, indent=2, ensure_ascii=False) + '\n')
    update_json(ROOT / 'vinyl/presentation.json', lambda p: p['board'].update({
        'expanded-width': '380px', 'expanded-min-height': '380px',
        'phone-expanded-width': 'min(300px, calc(100vw - 70px))',
        'phone-expanded-min-height': 'min(300px, calc(100vw - 70px))',
        'expanded-title-size': '1.4rem', 'expanded-text-size': '1.125rem',
        'phone-expanded-text-size': '1rem', 'expanded-text-line-height': '1.35'}))
    print('Approved Clouds B, Lily B and Vinyl B assets adopted; no prototype runtime required.')


if __name__ == '__main__':
    main()
