#!/usr/bin/env python3
"""
Automated Visual Testing for Dev Dashboard Mobile Interface
Tests all mobile functionality and captures screenshots for analysis
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime
import json

# Test configuration
BASE_URL = "http://localhost:8080"
TEST_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
TEST_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "your_password_here")  # Replace with actual password
TEST_TOTP = "000000"  # Replace with actual 2FA code when running

# Screenshot directory
SCREENSHOT_DIR = Path(__file__).parent.parent / "test_screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Test results
test_results = []


class TestResult:
    def __init__(self, name: str, passed: bool, message: str, screenshot: str = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.screenshot = screenshot
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "screenshot": self.screenshot,
            "timestamp": self.timestamp
        }


async def take_screenshot(page: Page, name: str) -> str:
    """Take a screenshot and return the filepath"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = SCREENSHOT_DIR / filename
    await page.screenshot(path=str(filepath), full_page=True)
    print(f"📸 Screenshot saved: {filepath}")
    return str(filepath)


async def login(page: Page) -> bool:
    """Login to the dev dashboard"""
    try:
        print("\n🔐 Logging in...")
        await page.goto(f"{BASE_URL}/dev/login")
        await page.wait_for_load_state("networkidle")

        # Take screenshot of login page
        await take_screenshot(page, "01_login_page")

        # Fill login form
        await page.fill("#username", TEST_USERNAME)
        await page.fill("#password", TEST_PASSWORD)
        await page.fill("#totp", TEST_TOTP)

        await take_screenshot(page, "02_login_filled")

        # Submit
        await page.click("#loginBtn")

        # Wait for redirect (either to project selector or dashboard)
        await page.wait_for_url(f"{BASE_URL}/dev**", timeout=10000)

        await take_screenshot(page, "03_after_login")

        # Check if we're logged in
        token = await page.evaluate("localStorage.getItem('access_token')")

        if token:
            print("✅ Login successful")
            return True
        else:
            print("❌ Login failed - no token")
            return False

    except Exception as e:
        print(f"❌ Login error: {e}")
        await take_screenshot(page, "ERROR_login")
        return False


async def test_mobile_viewport(page: Page):
    """Test 1: Mobile viewport and initial render"""
    test_name = "Mobile Viewport & Initial Render"
    print(f"\n🧪 Test: {test_name}")

    try:
        # Set mobile viewport (iPhone 14 Pro)
        await page.set_viewport_size({"width": 393, "height": 852})
        await page.goto(f"{BASE_URL}/dev/terminal", wait_until="networkidle")

        screenshot = await take_screenshot(page, "04_mobile_initial")

        # Check if terminal is visible
        terminal = await page.query_selector("#terminal")
        is_visible = await terminal.is_visible() if terminal else False

        # Check if content is cut off (should not scroll vertically)
        has_vertical_scroll = await page.evaluate("""
            () => document.body.scrollHeight > window.innerHeight
        """)

        # Check navbar width
        navbar_width = await page.evaluate("""
            () => document.querySelector('.header')?.offsetWidth
        """)
        viewport_width = await page.evaluate("() => window.innerWidth")

        issues = []
        if not is_visible:
            issues.append("❌ Terminal not visible on mobile")
        if has_vertical_scroll:
            issues.append("❌ Page has vertical scroll (content cut off at bottom)")
        if navbar_width and navbar_width > viewport_width:
            issues.append(f"❌ Navbar too wide ({navbar_width}px > {viewport_width}px)")

        if not issues:
            test_results.append(TestResult(test_name, True, "All viewport tests passed", screenshot))
            print("✅ Viewport tests passed")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def test_swipe_gestures(page: Page):
    """Test 2: Swipe gestures between terminal and preview"""
    test_name = "Swipe Gestures"
    print(f"\n🧪 Test: {test_name}")

    try:
        await page.set_viewport_size({"width": 393, "height": 852})

        # Initial state
        screenshot1 = await take_screenshot(page, "05_before_swipe")

        # Check initial visibility
        terminal_visible_before = await page.evaluate("""
            () => {
                const terminal = document.querySelector('.terminal-section');
                const style = window.getComputedStyle(terminal);
                return style.display !== 'none';
            }
        """)

        # Perform swipe left (should show preview)
        await page.evaluate("""
            () => {
                const touch = {
                    clientX: 300,
                    clientY: 400
                };

                document.dispatchEvent(new TouchEvent('touchstart', {
                    touches: [touch],
                    bubbles: true
                }));

                const endTouch = {
                    clientX: 50,
                    clientY: 400
                };

                document.dispatchEvent(new TouchEvent('touchend', {
                    changedTouches: [endTouch],
                    bubbles: true
                }));
            }
        """)

        await page.wait_for_timeout(500)  # Wait for animation
        screenshot2 = await take_screenshot(page, "06_after_swipe_left")

        # Check if preview is visible
        preview_visible = await page.evaluate("""
            () => {
                const preview = document.querySelector('.preview-section');
                const style = window.getComputedStyle(preview);
                return style.display !== 'none';
            }
        """)

        # Swipe right (should show terminal again)
        await page.evaluate("""
            () => {
                const touch = {
                    clientX: 50,
                    clientY: 400
                };

                document.dispatchEvent(new TouchEvent('touchstart', {
                    touches: [touch],
                    bubbles: true
                }));

                const endTouch = {
                    clientX: 300,
                    clientY: 400
                };

                document.dispatchEvent(new TouchEvent('touchend', {
                    changedTouches: [endTouch],
                    bubbles: true
                }));
            }
        """)

        await page.wait_for_timeout(500)
        screenshot3 = await take_screenshot(page, "07_after_swipe_right")

        terminal_visible_after = await page.evaluate("""
            () => {
                const terminal = document.querySelector('.terminal-section');
                const style = window.getComputedStyle(terminal);
                return style.display !== 'none';
            }
        """)

        issues = []
        if not terminal_visible_before:
            issues.append("❌ Terminal not visible initially")
        if not preview_visible:
            issues.append("❌ Swipe left did not show preview")
        if not terminal_visible_after:
            issues.append("❌ Swipe right did not show terminal")

        if not issues:
            test_results.append(TestResult(test_name, True, "Swipe gestures work correctly", screenshot2))
            print("✅ Swipe gestures work")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot2))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def test_keyboard_shortcuts(page: Page):
    """Test 3: Keyboard shortcuts (arrow keys, tab, etc.)"""
    test_name = "Keyboard Shortcuts"
    print(f"\n🧪 Test: {test_name}")

    try:
        await page.set_viewport_size({"width": 393, "height": 852})

        screenshot = await take_screenshot(page, "08_keyboard_test")

        # Click Tab button
        tab_btn = await page.query_selector('button[onclick*="sendKey(\'\\\\t\')"]')
        if tab_btn:
            await tab_btn.click()
            await page.wait_for_timeout(100)

        # Click Up Arrow button
        up_btn = await page.query_selector('button[onclick*="sendKey(\'\\\\x1b[A\')"]')
        if up_btn:
            await up_btn.click()
            await page.wait_for_timeout(100)

        # Check if escape sequences are showing in terminal (they shouldn't)
        terminal_content = await page.evaluate("""
            () => {
                const terminal = document.querySelector('#terminal');
                return terminal ? terminal.textContent : '';
            }
        """)

        issues = []
        if '\\x1b[' in terminal_content:
            issues.append("❌ Escape sequences visible in terminal (should be executed)")
        if '\\t' in terminal_content:
            issues.append("❌ Tab character visible in terminal (should be executed)")

        if not tab_btn:
            issues.append("❌ Tab button not found")
        if not up_btn:
            issues.append("❌ Arrow key button not found")

        if not issues:
            test_results.append(TestResult(test_name, True, "Keyboard shortcuts work", screenshot))
            print("✅ Keyboard shortcuts work")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def test_text_selection(page: Page):
    """Test 4: Text selection on mobile"""
    test_name = "Text Selection on Mobile"
    print(f"\n🧪 Test: {test_name}")

    try:
        await page.set_viewport_size({"width": 393, "height": 852})

        # Check if user-select is enabled
        user_select = await page.evaluate("""
            () => {
                const terminal = document.querySelector('#terminal');
                const style = window.getComputedStyle(terminal);
                return style.userSelect || style.webkitUserSelect;
            }
        """)

        screenshot = await take_screenshot(page, "09_text_selection")

        issues = []
        if user_select == 'none':
            issues.append("❌ Text selection disabled (user-select: none)")

        if not issues:
            test_results.append(TestResult(test_name, True, f"Text selection enabled ({user_select})", screenshot))
            print(f"✅ Text selection enabled ({user_select})")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def test_claude_autostart(page: Page):
    """Test 5: Claude Code auto-start"""
    test_name = "Claude Auto-Start"
    print(f"\n🧪 Test: {test_name}")

    try:
        await page.set_viewport_size({"width": 393, "height": 852})

        # Wait for WebSocket connection
        await page.wait_for_timeout(3000)  # Give Claude time to start

        screenshot = await take_screenshot(page, "10_claude_autostart")

        # Check terminal content for Claude prompt or path
        terminal_content = await page.evaluate("""
            () => {
                const terminal = document.querySelector('#terminal');
                return terminal ? terminal.textContent : '';
            }
        """)

        issues = []
        if '/opt/homebrew/bin/claude' in terminal_content:
            issues.append("❌ Claude path visible in terminal (should use exec)")
        if 'claude' not in terminal_content.lower():
            issues.append("❌ Claude might not have started (no 'claude' text found)")

        if not issues:
            test_results.append(TestResult(test_name, True, "Claude auto-started correctly", screenshot))
            print("✅ Claude auto-started")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def test_keyboard_sizing(page: Page):
    """Test 6: Layout with mobile keyboard"""
    test_name = "Mobile Keyboard Layout"
    print(f"\n🧪 Test: {test_name}")

    try:
        await page.set_viewport_size({"width": 393, "height": 852})

        screenshot1 = await take_screenshot(page, "11_before_keyboard")

        # Simulate keyboard appearing (reduce viewport height)
        await page.set_viewport_size({"width": 393, "height": 500})  # Keyboard takes ~350px

        await page.wait_for_timeout(500)
        screenshot2 = await take_screenshot(page, "12_with_keyboard")

        # Check if content is still visible
        terminal_visible = await page.evaluate("""
            () => {
                const terminal = document.querySelector('#terminal');
                if (!terminal) return false;
                const rect = terminal.getBoundingClientRect();
                return rect.height > 0 && rect.top < window.innerHeight;
            }
        """)

        # Check if there's vertical scroll
        has_scroll = await page.evaluate("""
            () => document.body.scrollHeight > window.innerHeight
        """)

        issues = []
        if not terminal_visible:
            issues.append("❌ Terminal not visible with keyboard open")
        if has_scroll:
            issues.append("⚠️ Page scrolls with keyboard (might be expected)")

        if not issues:
            test_results.append(TestResult(test_name, True, "Layout adapts to keyboard", screenshot2))
            print("✅ Keyboard layout works")
        else:
            msg = "\n".join(issues)
            test_results.append(TestResult(test_name, False, msg, screenshot2))
            print(f"❌ Issues found:\n{msg}")

    except Exception as e:
        test_results.append(TestResult(test_name, False, f"Error: {e}", None))
        print(f"❌ Test failed: {e}")


async def generate_report():
    """Generate HTML test report"""
    print("\n" + "="*60)
    print("📊 TEST REPORT")
    print("="*60)

    passed = sum(1 for r in test_results if r.passed)
    failed = sum(1 for r in test_results if not r.passed)
    total = len(test_results)

    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    print(f"\n📸 Screenshots saved to: {SCREENSHOT_DIR}")

    # Generate HTML report
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Dev Dashboard Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
        .header {{ background: linear-gradient(135deg, #006699, #005588); padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .test {{ background: #2d2d2d; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #666; }}
        .test.passed {{ border-left-color: #00ff00; }}
        .test.failed {{ border-left-color: #ff5555; }}
        .screenshot {{ max-width: 100%; border-radius: 8px; margin-top: 10px; }}
        .stats {{ display: flex; gap: 20px; margin-top: 20px; }}
        .stat {{ background: #383838; padding: 15px; border-radius: 8px; flex: 1; text-align: center; }}
        .stat .value {{ font-size: 2em; font-weight: bold; }}
        .stat.passed .value {{ color: #00ff00; }}
        .stat.failed .value {{ color: #ff5555; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Dev Dashboard Mobile Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="label">Total Tests</div>
            <div class="value">{total}</div>
        </div>
        <div class="stat passed">
            <div class="label">Passed</div>
            <div class="value">{passed}</div>
        </div>
        <div class="stat failed">
            <div class="label">Failed</div>
            <div class="value">{failed}</div>
        </div>
    </div>

    <h2>Test Results</h2>
"""

    for result in test_results:
        status = "passed" if result.passed else "failed"
        icon = "✅" if result.passed else "❌"
        screenshot_html = f'<img src="{Path(result.screenshot).name}" class="screenshot" />' if result.screenshot else ""

        html += f"""
    <div class="test {status}">
        <h3>{icon} {result.name}</h3>
        <p><strong>Status:</strong> {'PASSED' if result.passed else 'FAILED'}</p>
        <p><strong>Message:</strong> {result.message.replace(chr(10), '<br>')}</p>
        <p><strong>Time:</strong> {result.timestamp}</p>
        {screenshot_html}
    </div>
"""

    html += """
</body>
</html>
"""

    report_path = SCREENSHOT_DIR / "test_report.html"
    report_path.write_text(html)
    print(f"\n📄 HTML Report: {report_path}")

    # Also save JSON
    json_path = SCREENSHOT_DIR / "test_results.json"
    json_path.write_text(json.dumps([r.to_dict() for r in test_results], indent=2))
    print(f"📄 JSON Report: {json_path}")

    # Print issues found
    print("\n" + "="*60)
    print("🔍 ISSUES FOUND:")
    print("="*60)
    for result in test_results:
        if not result.passed:
            print(f"\n❌ {result.name}:")
            print(f"   {result.message}")

    return failed == 0


async def main():
    """Run all tests"""
    print("🚀 Starting Automated Visual Testing Platform")
    print(f"📍 Base URL: {BASE_URL}")
    print(f"📁 Screenshots: {SCREENSHOT_DIR}")

    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Login first
            if not await login(page):
                print("❌ Cannot proceed without login")
                await browser.close()
                sys.exit(1)

            # Run all tests
            await test_mobile_viewport(page)
            await test_swipe_gestures(page)
            await test_keyboard_shortcuts(page)
            await test_text_selection(page)
            await test_claude_autostart(page)
            await test_keyboard_sizing(page)

            # Generate report
            all_passed = await generate_report()

            await browser.close()

            # Exit with appropriate code
            sys.exit(0 if all_passed else 1)

        except Exception as e:
            print(f"❌ Fatal error: {e}")
            await take_screenshot(page, "FATAL_ERROR")
            await browser.close()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
