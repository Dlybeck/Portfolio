from playwright.sync_api import expect


def test_unpinned_load_keeps_original_even_with_old_rotation_cookie(client):
    client.cookies.set('portfolio_theme', 'canonical')
    for route in ('/', '/', '/hobbies/tennis'):
        response = client.get(route)
        assert 'data-board-theme="canonical"' in response.text
        assert 'portfolio_theme=' not in response.headers.get('set-cookie', '')
    assert 'data-board-theme="vinyl"' in client.get('/?theme=vinyl').text


def test_dial_steps_both_directions_and_preserves_manual_choice_on_reload(browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme=vinyl', wait_until='networkidle')
    page.get_by_role('button', name='Next theme', exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'canonical')
    expect(page.locator('[data-theme-name]')).to_have_text('Original')
    page.get_by_role('button', name='Previous theme', exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'vinyl')
    expect(page.locator('[data-theme-name]')).to_have_text('Vinyl Collection')
    page.reload(wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'vinyl')
    expect(page.locator('.cp-comparison')).to_have_count(0)


def test_rapid_dial_steps_count_pending_choices_without_moving_home(browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme=vinyl', wait_until='networkidle')
    page.get_by_role('button', name='Next theme', exact=True).evaluate(
        'button => { button.click(); button.click(); button.click(); }'
    )
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'islands')
    expect(page.locator('[data-theme-name]')).to_have_text('Island Chain')
    expect(page).to_have_url(f'{origin}/?theme=islands')
    expect(page.get_by_role('button', name='Go to Hobbies')).to_be_visible()


def test_rejected_dial_pack_restores_original_and_can_step_again(browser_page):
    page, origin = browser_page
    page.goto(f'{origin}/?theme=canonical', wait_until='networkidle')
    page.route('**/_theme-packs/clouds.json', lambda route: route.fulfill(status=503))
    page.get_by_role('button', name='Next theme', exact=True).click()
    expect(page).to_have_url(f'{origin}/?theme=canonical')
    expect(page.locator('[data-theme-name]')).to_have_text('Original')
    page.get_by_role('button', name='Previous theme', exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-board-theme', 'vinyl')
