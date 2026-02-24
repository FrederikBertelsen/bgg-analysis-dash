from playwright.sync_api import ElementHandle

from scraping.camoufox_wrapper import CamoufoxWrapper
from scraping.page_wrapper import PageWrapper


def test_fingerprint_dot_com_evasion(page: PageWrapper) -> float:
    print("Testing evasion on https://demo.fingerprint.com/playground:")
    page.goto("https://demo.fingerprint.com/playground")
    page.wait_for_selector("td[class^='SignalTable_green']")
    pass_count = page.locator("td[class^='SignalTable_green']").count()
    fail_count = page.locator("td[class^='SignalTable_red']").count()
    evasion_score = round(
        (
            pass_count / (pass_count + fail_count)
            if (pass_count + fail_count) > 0
            else 0
        ),
        2,
    )
    print(
        f"    Passed: {pass_count}, Failed: {fail_count}",
        f"    Evasion score: {evasion_score*100}%",
    )
    return evasion_score


def test_pixelscan_evasion(page: PageWrapper) -> float:
    print("Testing evasion on https://pixelscan.net/bot-check:")
    page.goto("https://pixelscan.net/bot-check")
    page.wait_for_selector("#tabs > li > button")
    page.sleep(1000)
    tabs = page.locator("#tabs > li > button")
    test_results = {}
    for tab in tabs.element_handles():
        tab_name = tab.inner_text()
        tab.click()

        page.sleep(1000)

        tests = page.locator(
            "div[id$='accordion-collapse-navigator-details'] > div > div"
        )

        for test in tests.element_handles():
            test_key_elm = test.query_selector("span")
            test_value_elm = test.query_selector("div")

            if test_key_elm is not None and test_value_elm is not None:
                test_key = test_key_elm.inner_text()
                test_value = test_value_elm.inner_text()

                passed = "normal" in test_value.lower()

                test_results[f"{tab_name} - {test_key}"] = passed

    evasion_score = round(
        sum(test_results.values()) / len(test_results) if len(test_results) > 0 else 0,
        2,
    )
    print(
        f"    Passed: {sum(test_results.values())}, Failed: {len(test_results) - sum(test_results.values())}",
        f"    Evasion score: {evasion_score*100}%",
    )
    if not all(test_results.values()):
        print("     Failed tests:")
        for test_name, passed in test_results.items():
            if not passed:
                print(f"        {test_name}")

    return evasion_score


def test_browser_scan_evasion(page: PageWrapper) -> float:
    print("Testing evasion on https://www.browserscan.net/bot-detection:")
    page.goto("https://www.browserscan.net/bot-detection")
    page.sleep(2000)

    test_results = {}
    test_elms: list[ElementHandle] = []
    for query in [
        "div._11xj7yu._1yv4nu8",
        "div._11xj7yu._w1b9c6",
        "div._11xj7yu._f6qr8l",
    ]:
        page.wait_for_selector(query)
        test_elms.extend(page.locator(query).element_handles())

    for elm in test_elms:
        passed = elm.query_selector('svg[style="fill: rgb(74, 255, 189);"]') is not None
        test_name_elm = elm.query_selector("h3")
        test_name = (
            test_name_elm.inner_text() if test_name_elm is not None else "Unknown test"
        )
        test_results[test_name] = passed

    evasion_score = round(
        sum(test_results.values()) / len(test_results) if len(test_results) > 0 else 0,
        2,
    )
    print(
        f"    Passed: {sum(test_results.values())}, Failed: {len(test_results) - sum(test_results.values())}",
        f"    Evasion score: {evasion_score*100}%",
    )
    if not all(test_results.values()):
        print("     Failed tests:")
        for test_name, passed in test_results.items():
            if not passed:
                print(f"        {test_name}")

    return evasion_score


def test_brotector_captcha_evasion(page: PageWrapper) -> float:
    print("Testing evasion on https://seleniumbase.github.io/apps/brotector:")
    page.goto("https://seleniumbase.github.io/apps/brotector")

    page.wait_for_selector("label#pText")

    page.sleep(2000)

    page.click("button#myButton")

    page.sleep(2000)

    text = page.get_text("label#pText")
    passed = "SUCCESS" in text if text is not None else False

    print(f"    Brotector CAPTCHA test result: {'Passed' if passed else 'Failed'}")

    return 1 if passed else 0


def test_simple_cloudflare_captcha_evasion(page: PageWrapper) -> float:
    print(
        "Testing evasion on https://2captcha.com/demo/cloudflare-turnstile (simple Cloudflare CAPTCHA):"
    )
    page.goto("https://2captcha.com/demo/cloudflare-turnstile")
    page.sleep(5000)

    clicked_captcha = False
    turnstile = page.locator("div#cf-turnstile").first.element_handle()
    if turnstile:
        print("    Found Cloudflare Turnstile CAPTCHA.")
        bounding_box = turnstile.bounding_box()
        if bounding_box:
            click_x = bounding_box["x"] + bounding_box["width"] / 15
            click_y = bounding_box["y"] + bounding_box["height"] / 2
            print(f"    Clicking CAPTCHA at coordinates ({click_x}, {click_y}).")
            page.click_coordinates(click_x, click_y)
            clicked_captcha = True
            page.sleep(2000)
        else:
            print("    Failed to get bounding box for CAPTCHA.")
            return 0
    else:
        print("    Failed to find Cloudflare Turnstile CAPTCHA.")
        return 0

    if not clicked_captcha:
        print("    Failed to click CAPTCHA.")
        return 0

    page.click('button[data-action="demo_action"]')
    page.sleep(2000)

    result_text = page.get_text("p", has_text="Captcha is passed successfully!")

    if result_text:
        print("    CAPTCHA test result: Passed")
        return 1
    else:
        print("    CAPTCHA test result: Failed")
        return 0


def test_cloudflare_challenge_evasion(page: PageWrapper) -> float:
    print(
        "Testing evasion on https://2captcha.com/demo/cloudflare-turnstile-challenge (Cloudflare challenge)"
    )
    page.goto("https://2captcha.com/demo/cloudflare-turnstile-challenge")
    page.sleep(5000)

    result_text = page.get_text("p", has_text="Captcha is passed successfully!")

    if result_text:
        print("    Cloudflare challenge test result: Passed")
        return 1
    else:
        print("    Cloudflare challenge test result: Failed")
        return 0


with CamoufoxWrapper().start_browser(
    headless=False, humanize=True, enable_cache=False
) as browser:
    page = browser.new_page()

    evasion_scores = []

    evasion_scores.append(test_fingerprint_dot_com_evasion(page))
    page.sleep(2000)
    evasion_scores.append(test_pixelscan_evasion(page))
    page.sleep(2000)
    evasion_scores.append(test_browser_scan_evasion(page))
    page.sleep(2000)
    evasion_scores.append(test_brotector_captcha_evasion(page))
    page.sleep(2000)
    evasion_scores.append(test_simple_cloudflare_captcha_evasion(page))
    page.sleep(2000)
    evasion_scores.append(test_cloudflare_challenge_evasion(page))

    # https://overpoweredjs.com/
    # https://bot.sannysoft.com/
    # https://browserleaks.com/javascript
    # https://abrahamjuliot.github.io/creepjs/
    # https://fingerprint-scan.com/

    print("FINISHED TESTING EVASION")
    print(f"Overall evasion scores: {evasion_scores}")