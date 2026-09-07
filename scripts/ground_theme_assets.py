#!/usr/bin/env python3
"""Compile bounded physical-coherence corrections into installed SVG assets.

Run after historical export/refinement scripts. No runtime dependency.
"""
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'static/themes'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
RADII = (54, 47, 56, 53, 52, 57, 49, 55)


def tag(name):
    return f'{{{NS}}}{name}'


def ground_limb_and_rings(root):
    body = root.find(".//*[@data-visual-axis='silhouette']")
    radius = float(body.get('rx'))
    atmosphere = root.find(".//*[@data-visual-axis='atmosphere']")
    for ellipse in atmosphere.iter(tag('ellipse')):
        halo_radius = radius + min(5, float(ellipse.get('rx')) - radius)
        ellipse.set('rx', str(halo_radius))
        ellipse.set('ry', str(halo_radius))
    for limb in atmosphere.iter(tag('path')):
        r = radius + 3
        x, y = round(r * .866, 2), round(83 - r * .5, 2)
        limb.set('d', f'M{100-x} {y}A{r} {r} 0 0 1 {100+x} {y}')
    # Separate halves avoid double-painted/translucent seams outside the globe.
    for rear in root.findall(".//*[@data-theme-ring-half='rear']"):
        if rear.tag != tag('ellipse'):
            continue
        rx, ry = float(rear.get('rx')), float(rear.get('ry'))
        rear.tag = tag('path')
        for attribute in ('cx', 'cy', 'rx', 'ry'):
            rear.attrib.pop(attribute, None)
        rear.set('d', f'M{100-rx} 83A{rx} {ry} 0 0 1 {100+rx} 83')


def ground_planet(root):
    if root.get('data-theme-grounding') == 'spherical-v1':
        ground_limb_and_rings(root)
        return
    palette = root.find(".//*[@data-visual-axis='palette']")
    body = palette.find("./*[@data-visual-axis='silhouette']")
    radius = RADII[int(body.get('data-visual-value'))]
    old_rx, old_ry = float(body.get('rx')), float(body.get('ry'))
    body.set('rx', str(radius))
    body.set('ry', str(radius))
    atmosphere = palette.find("./*[@data-visual-axis='atmosphere']")
    for ellipse in atmosphere.iter(tag('ellipse')):
        gap = max(float(ellipse.get('rx')) - old_rx,
                  float(ellipse.get('ry')) - old_ry)
        ellipse.set('rx', str(radius + gap))
        ellipse.set('ry', str(radius + gap))
    defs = ET.Element(tag('defs'))
    clip = ET.SubElement(defs, tag('clipPath'), {'id': 'planet-surface'})
    ET.SubElement(clip, tag('circle'), {'cx': '100', 'cy': '83', 'r': str(radius)})
    root.insert(0, defs)
    # Surface features belong to the globe, unlike its moons or ring system.
    for child in list(palette):
        if child.get('data-visual-axis') == 'surface' or child.tag == tag('path'):
            child.set('clip-path', 'url(#planet-surface)')
    companions = palette.find("./*[@data-visual-axis='companion']")
    for ring in companions.findall(tag('ellipse')):
        if ring.get('fill') != 'none':
            continue
        rx = float(ring.get('rx'))
        ry = round(radius * .72, 2)
        ring.set('ry', str(ry))
        ring.set('data-theme-ring-half', 'rear')
        front = deepcopy(ring)
        front.tag = tag('path')
        for attribute in ('cx', 'cy', 'rx', 'ry'):
            front.attrib.pop(attribute, None)
        front.set('d', f'M{100-rx} 83A{rx} {ry} 0 0 0 {100+rx} 83')
        front.set('data-theme-ring-half', 'front')
        palette.append(front)
    root.set('data-theme-grounding', 'spherical-v1')
    ground_limb_and_rings(root)


def ground_lily(root):
    palette = root.find(".//*[@data-visual-axis='palette']")
    accent = palette.find("./*[@data-visual-axis='accent']")
    if accent is None:
        return
    if accent.get('data-visual-value') == '2':
        # Keep the same bloom on the upper leaf edge in both states, outside
        # the writing area. This also covers the long-copy ScribbleScan leaf.
        accent.find(tag('g')).set('transform', 'translate(112 38)')
        return
    if accent.get('data-visual-value') != '3':
        return
    # Water ripples can peek from behind the leaf, never lie on its surface.
    detail = accent.find(tag('g'))
    detail.set('transform', 'translate(28 27)')
    detail.set('stroke', '#bde7df')
    palette.remove(accent)
    palette.insert(0, accent)
    accent.set('data-theme-grounding', 'water-behind-leaf')


def main():
    for theme, ground in (('planets', ground_planet), ('lily', ground_lily)):
        for path in sorted((ROOT / theme / 'assets/tiles').glob('*.svg')):
            root = ET.fromstring(path.read_text())
            ground(root)
            path.write_text(ET.tostring(root, encoding='unicode') + '\n')


if __name__ == '__main__':
    main()
