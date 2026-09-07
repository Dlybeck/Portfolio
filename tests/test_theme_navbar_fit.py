import pytest


@pytest.mark.parametrize('theme', ['lily', 'planets', 'islands', 'postcards', 'vinyl', 'clouds'])
@pytest.mark.parametrize('width', [320, 390])
def test_phone_header_shows_full_name_without_crowding_document_controls(browser_page, theme, width):
    page, origin = browser_page
    page.set_viewport_size({'width': width, 'height': 844})
    page.goto(f'{origin}/hobbies/tennis?theme={theme}', wait_until='networkidle')
    page.evaluate('document.fonts.ready')
    assert page.locator('html').get_attribute('data-board-theme') == theme
    measurements = page.locator('.navbar-title').evaluate('''title => {
        const navbar = document.querySelector('.navbar').getBoundingClientRect();
        const close = document.querySelector('.close-button').getBoundingClientRect();
        const home = document.querySelector('.home-button').getBoundingClientRect();
        return {text:title.textContent.trim(), clipped:title.scrollWidth > title.clientWidth + 1,
            right:navbar.right, left:navbar.left, closeLeft:close.left,
            homeRight:home.right, homeLeft:home.left, titleRight:title.getBoundingClientRect().right};
    }''')
    assert measurements['text'] == 'David Lybeck'
    assert not measurements['clipped']
    assert measurements['left'] >= 0
    assert measurements['right'] <= measurements['closeLeft'] - 4
    assert measurements['homeLeft'] >= measurements['titleRight']
    assert measurements['homeRight'] <= measurements['right']
