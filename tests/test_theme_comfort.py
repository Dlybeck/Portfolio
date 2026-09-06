import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize('theme', ['lily', 'planets', 'islands', 'vinyl', 'botanical', 'workbench', 'postcards'])
@pytest.mark.parametrize('width', [320, 390, 768, 1440])
def test_content_fits_the_rendered_svg_at_readable_sizes(browser_page, theme, width):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 900 if width > 600 else 844})
    page.goto(f'{origin}/?theme={theme}', wait_until='networkidle')
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)
    # Remove rotations only for this geometry assertion so DOM rectangles can
    # be compared directly with the browser's own rendered SVG marker bounds.
    page.add_style_tag(content='''
        .tile-base { transform: none !important; }
        .tile-expanded { animation: none !important;
            transform: translate(-50%, -50%) !important; }
        .theme-reveal-part,
        [data-theme-reveal] .tile-expanded :is(.expanded-title,.expanded-text,.expanded-open) {
            transform: none !important; transition: none !important;
        }
    ''')
    issues = page.locator('.tile-container').evaluate_all('''tiles => tiles.flatMap(tile => {
        const problems = [];
        for (const state of ['base', 'expanded']) {
            const body = tile.querySelector(`.tile-${state} .paper-body`);
            const selectors = state === 'base' ? '.scrap-title'
                : '.expanded-title,.expanded-text,.expanded-open';
            for (const node of body.querySelectorAll(selectors)) {
                const marker = body.querySelector(node.dataset.revealTitle
                    ? '[data-theme-title-area]' : '[data-theme-content-area]').getBoundingClientRect();
                const rect = node.getBoundingClientRect();
                if (rect.left < marker.left - 2 || rect.right > marker.right + 2
                    || rect.top < marker.top - 2 || rect.bottom > marker.bottom + 2) {
                    problems.push(`${tile.dataset.title} ${state}: outside rendered SVG content area`);
                }
                const minimum = state === 'base' ? 14
                    : node.matches('.expanded-text') ? (innerWidth < 360 ? 14 : 15)
                    : node.matches('.expanded-title') ? 20 : 18;
                if (parseFloat(getComputedStyle(node).fontSize) < minimum) {
                    problems.push(`${tile.dataset.title} ${state}: text below ${minimum}px`);
                }
            }
        }
        return problems;
    })''')
    assert issues == []


@pytest.mark.parametrize('theme', ['lily', 'planets', 'islands', 'vinyl', 'botanical', 'workbench', 'postcards'])
def test_phone_document_uses_reading_width_and_separates_photos(browser_page, theme):
    page, origin = browser_page
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(f'{origin}/hobbies/tennis?theme={theme}', wait_until='networkidle')
    document = page.frame_locator('.mini-window')
    measurements = document.locator('.section').first.evaluate('''section => {
        const paragraph = section.querySelector('p');
        const style = getComputedStyle(paragraph);
        const photos = [...section.querySelectorAll('img')].map(n => n.getBoundingClientRect());
        return {
            font: parseFloat(style.fontSize),
            readingWidth: paragraph.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
            viewport: innerWidth,
            photoGap: photos[1].top - photos[0].bottom,
            overflow: document.documentElement.scrollWidth > innerWidth + 1
        };
    }''')
    assert measurements['font'] >= 16
    assert measurements['readingWidth'] >= measurements['viewport'] * .78
    assert measurements['photoGap'] >= 12
    assert not measurements['overflow']
