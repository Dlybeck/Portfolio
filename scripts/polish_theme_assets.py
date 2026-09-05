"""Apply the candidate comfort pass to declarative alternate Theme Pack assets.

Idempotent authoring operation; never part of the runtime renderer.
"""
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'static/themes'
ET.register_namespace('', 'http://www.w3.org/2000/svg')

# Content bounds follow each actual silhouette, including its narrow lobes.
CONTENT_AREAS = {
    'lily': [(56,52,88,72), (52,52,96,72), (48,48,104,80), (52,52,96,72),
             (52,52,96,72), (48,52,104,72), (44,44,112,88), (56,52,88,72)],
    'islands': [(56,48,88,72), (52,56,96,72), (48,56,104,72), (52,56,96,72),
                (44,56,96,72), (48,56,104,72), (44,56,112,72), (56,56,88,72)],
}


def main():
    # New visual capabilities are represented by ordinary complete
    # presentation tokens. Legacy worlds receive their existing CSS values.
    for folder in ROOT.iterdir():
        path = folder / 'presentation.json'
        if not path.is_file():
            continue
        presentation = json.loads(path.read_text())
        presentation['board'].setdefault('content-area-space', 'box')
        presentation['document'].setdefault('title-margin', '30px 0 .83em')
        presentation['document'].setdefault('media-margin-block', '0')
        path.write_text(json.dumps(presentation, indent=2, ensure_ascii=False) + '\n')
    for theme in ('lily', 'planets', 'islands'):
        folder = ROOT / theme
        presentation_path = folder / 'presentation.json'
        presentation = json.loads(presentation_path.read_text())
        presentation['board'].update({
            'content-area-space': 'svg',
            'font-expanded-text': "'Patrick Hand', cursive",
            'font-action': "'Patrick Hand', cursive",
            'expanded-text-size': '1.125rem',
            'phone-expanded-text-size': '1rem',
            'base-title-size': '1.25rem',
            'base-title-line-height': '1.15',
            'expanded-title-size': '1.6rem',
            'expanded-title-line-height': '1.2',
            'expanded-text-line-height': '1.4',
            'text-shadow': 'none',
            'ink': {'planets': '#172547', 'lily': '#102e24', 'islands': '#001007'}[theme],
            'action-letter-spacing': '0',
            'action-size': '1.125rem',
            'expanded-width': '410px' if theme == 'planets' else '420px',
            'expanded-min-height': '390px',
            'phone-tile-size': '144px',
            'phone-expanded-width': 'min(380px, calc(100vw + 20px))',
            'phone-expanded-min-height': '400px',
            'expanded-gap': 'clamp(4px, calc(2vw - 3px), 8px)',
        })
        presentation['document'].update({
            'body-size': '1rem' if theme == 'planets' else '1.125rem',
            'panel-max-width': 'min(100%, 72ch)',
            'panel-box-sizing': 'border-box',
            'panel-padding': '12px clamp(10px, 3vw, 24px)',
            'title-margin': '24px 0 8px',
            'media-margin-block': '16px',
        })
        presentation_path.write_text(json.dumps(presentation, indent=2, ensure_ascii=False) + '\n')
        catalog_path = folder / 'tiles.json'
        catalog = json.loads(catalog_path.read_text())
        for assignment in catalog['assignments'].values():
            # Retain independent, deterministic orientation without forcing a
            # long paragraph to lean as steeply as a small neighboring object.
            base_rotation = assignment['transforms']['base']['rotationDegrees']
            assignment['transforms']['expanded']['rotationDegrees'] = round(base_rotation * .4, 2)
            if theme == 'planets' and 'typography' in assignment:
                assignment['typography'].update({
                    'baseFontFamily': "'Patrick Hand', cursive",
                    'expandedTextFontFamily': "'Patrick Hand', cursive",
                    'inkColor': '#172547',
                })
        if theme in ('lily', 'islands'):
            catalog['assignments']['Puzzles']['layout'] = {
                'expandedWidth': '420px',
                'expandedMinHeight': '390px',
                'phoneExpandedWidth': 'min(380px, calc(100vw + 40px))',
                'phoneExpandedMinHeight': '400px',
            }
        catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n')
        for path in sorted((folder / 'assets/tiles').glob('*.svg')):
            root = ET.fromstring(path.read_text())
            for element in root.iter():
                axis = element.get('data-visual-axis')
                # Veins remain visible as leaf construction, with enough tonal
                # restraint that letters remain the strongest foreground marks.
                if theme == 'lily' and axis == 'vein':
                    element.set('opacity', '.28')
                if theme == 'islands' and axis == 'elevation':
                    element.set('opacity', '.5')
                if theme == 'planets' and axis == 'surface':
                    element.set('opacity', '.6')
                if path.stem.endswith('-expanded') and element.get('data-theme-content-area'):
                    if theme in CONTENT_AREAS:
                        area = CONTENT_AREAS[theme][int(root.get('data-variant-silhouette'))]
                        element.attrib.update(zip(('x','y','width','height'), map(str, area)))
            path.write_text(ET.tostring(root, encoding='unicode') + '\n')


if __name__ == '__main__':
    main()
