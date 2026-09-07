"""Cloudscape's drawn silhouette families and deterministic distant sky art."""
import random
from xml.etree import ElementTree as ET
from scripts.build_collection_themes import NS, axis, node, path, rect

# Independent outlines, shaded contours, and measured readable interiors.
PROFILES = [
    ('billow',
     'M43 236C14 230 4 205 17 182C-2 156 10 116 40 110C29 74 58 49 87 58'
     'C88 25 122 10 149 28C173 9 210 30 208 58C243 43 277 64 274 99'
     'C310 102 327 134 307 164C327 192 304 230 279 234Q162 249 43 236Z',
     'M17 192Q36 220 77 222Q145 230 191 218Q244 230 305 197C301 225 280 237 254 239'
     'Q139 251 43 236C20 230 10 210 17 192Z', (40,78,240,148)),
    ('bank',
     'M30 231C2 222 -2 192 19 176C3 150 28 124 54 130C59 91 99 80 125 101'
     'C141 65 185 68 205 101C235 82 274 107 269 138C300 128 325 155 309 182'
     'C331 207 300 237 275 237Q160 246 30 231Z',
     'M13 202Q47 222 99 220Q140 232 180 221Q257 232 311 205C303 229 280 238 250 239'
     'Q120 246 30 231Q10 222 13 202Z', (38,133,244,92)),
    ('tower',
     'M47 238C16 236 3 210 14 184C-1 165 5 134 31 126C18 99 36 70 63 69'
     'C51 41 76 16 101 26C116 -1 152 12 158 39C191 29 215 55 202 84'
     'C237 67 273 88 271 120C307 116 327 146 309 172C328 204 301 235 273 240'
     'Q147 247 47 238Z',
     'M13 193Q48 219 90 219Q132 238 176 222Q245 232 310 197C298 227 280 240 244 242'
     'Q130 250 47 238C23 234 10 213 13 193Z', (39,78,241,150)),
    ('windbank',
     'M10 221Q27 204 48 201C35 179 54 159 79 163C66 131 91 106 119 114'
     'C117 78 153 53 183 72C212 48 251 72 245 106C280 94 307 119 295 148'
     'C326 166 318 207 291 220Q259 241 199 235L139 231Q72 239 10 221Z',
     'M10 221Q64 221 103 213Q151 229 195 221Q256 231 301 200Q282 234 235 236'
     'L139 231Q72 239 10 221Z', (82,113,199,113)),
    ('cluster',
     'M32 231C10 222 4 205 18 185C-5 164 8 132 36 128C27 99 47 76 74 85'
     'C75 50 115 39 138 66C157 29 198 39 210 75C244 58 274 79 272 109'
     'C303 106 322 133 306 158C328 176 315 204 294 211C286 237 260 244 236 233'
     'C207 252 177 240 163 235C132 251 102 240 90 233Q57 245 32 231Z',
     'M17 196Q47 220 86 218Q126 233 157 218Q193 233 225 218Q270 229 309 192'
     'Q305 207 294 211C286 237 260 244 236 233C207 252 177 240 163 235'
     'C132 251 102 240 90 233Q57 245 32 231Q12 218 17 196Z', (40,80,239,147)),
    ('swell',
     'M40 239C8 234 -1 200 19 179C-2 144 13 101 49 97C35 58 70 26 103 42'
     'C123 8 168 14 184 47C213 21 252 44 252 76C287 65 315 96 300 126'
     'C326 148 322 180 305 195C318 219 289 244 263 242Q146 252 40 239Z',
     'M16 196Q54 220 91 220Q140 234 188 221Q257 235 307 201C313 229 283 244 258 243'
     'Q136 252 40 239C18 234 10 212 16 196Z', (38,74,244,158)),
]

# Short summaries can occupy flatter banks; long copy gets roomier clouds.
# These are authoring assignments, never runtime exceptions.
FAMILIES = {'Home':0, 'Hobbies':1, 'Projects':4, 'Work Experience':2,
    'Education':3, '3D Printing':5, 'Gaming':0, 'Tennis':4, 'Other Models':2,
    'Puzzles':5, 'Programs':2, 'Websites':4, 'Digital Planner':0,
    'This website':5, 'ScribbleScan':0, 'College':4, 'Early Education':3}

# Optical centers follow each silhouette's painted mass, not the shared
# transparent viewBox. The tapered bank has a narrower, right-shifted interior
# so its title centers on the billow without clipping phone neighbors.
BASE_AREAS = [(64,94,192,100), (66,119,192,100), (58,98,192,100),
              (101,112,154,100), (64,104,192,100), (65,96,192,100)]


def cloud_svg(f, state):
    root = ET.Element(f'{{{NS}}}svg', {'viewBox':'0 0 320 270',
        'preserveAspectRatio':'xMidYMid meet','opacity':'.98'})
    family, shape, shade, safe = PROFILES[f['silhouette'] % len(PROFILES)]
    palette=axis(root,'palette',f['palette'])
    fill=['#fff8e9','#f5fbff','#ffffff','#edf5fc','#fffdf3'][f['palette']]
    silhouette=axis(palette,'silhouette',f['silhouette'])
    path(silhouette,shape,fill)
    underside=axis(palette,'underside',f['underside'])
    path(underside,shade,['#d4e3ee','#dce7ed','#cfdfea'][f['underside']%3],opacity='.45')
    density=axis(palette,'density',f['density'])
    path(density,f'M{57+f["density"]*9} 236Q137 240 {215-f["density"]*8} 236',
         stroke='#eef5f8',stroke_width='.7',opacity='.4')
    wisp=axis(palette,'wisp',f['wisp'])
    orient=axis(wisp,'orientation',f['orientation'],transform=f'rotate({f["orientation"]-2} 160 232)')
    path(orient,f'M{44+f["wisp"]*5} 235Q76 237 {110+f["wisp"]*8} 234',
         stroke='#d4e3ec',stroke_width=1,opacity='.45')
    x,y,w,h=safe
    rect(root,*(safe if state=='expanded' else BASE_AREAS[f['silhouette'] % len(PROFILES)]),
         'none',data_theme_content_area='content')
    # Base and focus share the actual drawing; semantic markers differ.
    return ET.tostring(root,encoding='unicode')+'\n'


def sky_svg(near=False):
    root=ET.Element(f'{{{NS}}}svg',{'viewBox':'0 0 3000 3000',
        'preserveAspectRatio':'none','aria-hidden':'true','focusable':'false'})
    rng=random.Random(174 if near else 53)
    for i in range(42 if near else 32):
        x,y=rng.uniform(-180,3000),rng.uniform(-100,3000)
        width,height=rng.uniform(230,560),rng.uniform(22,50)
        g=node(root,'g',transform=f'translate({x:.1f} {y:.1f}) scale({width/320:.3f} {height/100:.3f})',
               opacity='.23' if near else '.3')
        if near:
            path(g,'M0 79Q32 55 64 61Q77 22 106 43Q124 6 152 38Q181 22 201 50'
                 'Q224 36 244 59Q279 51 320 81Q223 91 175 84Q79 94 0 79Z','#f7fbff')
        else:
            path(g,'M0 56Q88 21 151 40Q221 22 320 36Q260 33 200 48Q109 36 0 56Z','#f4f8ef')
            path(g,'M47 73Q113 54 170 64Q218 55 274 58Q219 67 170 72Q106 66 47 73Z','#f4f8ef')
    return ET.tostring(root,encoding='unicode')+'\n'
