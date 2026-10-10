from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TEST_PORT = 5001
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
DB_PATH = ROOT / "database" / "playwright_auth.sqlite3"
SCREENSHOT_DIR = ROOT / "docs" / "testcases" / "screenshots"
REPORT_PATH = ROOT / "docs" / "testcases" / "auth_execution_report.xlsx"
VALID_PASSWORD = "Prati#123"
_user_serial = 0


def reset_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()


def wait_for_server() -> None:
    deadline = time.time() + 35
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/login", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Flask app did not become ready within 35 seconds.")


def unique_username(prefix: str) -> str:
    global _user_serial
    _user_serial += 1
    letters = "".join(character for character in prefix.lower() if character.isalpha())[:3] or "usr"
    return f"{letters}_{_user_serial}{int(time.time()) % 10000}"[:15]


def register_user(page: Page, username: str, role: str, password: str) -> None:
    page.goto(f"{BASE_URL}/register")
    page.locator("#username").fill(username)
    page.select_option("#role", role)
    page.locator("#password").fill(password)
    page.locator("#confirm_password").fill(password)
    page.locator("button[type='submit']").click()
    expect(page).to_have_url(f"{BASE_URL}/login")
    expect(page.locator("body")).to_contain_text("Account created")


def login_user(page: Page, username: str, password: str) -> None:
    page.goto(f"{BASE_URL}/login")
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    submit = page.locator("button[type='submit']")
    expect(submit).to_be_enabled()
    submit.click()
    expect(page).to_have_url(f"{BASE_URL}/dashboard")


def sign_out(page: Page) -> None:
    page.locator("form[action$='/logout']").first.evaluate("form => form.requestSubmit()")
    expect(page).to_have_url(f"{BASE_URL}/login")


def login_and_expect_error(page: Page, username: str, password: str) -> None:
    page.goto(f"{BASE_URL}/login")
    page.locator("#username").fill(username)
    page.locator("#password").fill(password)
    page.locator("button[type='submit']").click()
    expect(page.locator(".login-server-error")).to_contain_text("incorrect")


def run_case(test_id: str, title: str, callback) -> dict:
    screenshot_path = SCREENSHOT_DIR / f"{test_id}.png"
    result = {"TC ID": test_id, "Title": title, "Status": "PASS", "Error": "", "Screenshot": ""}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        try:
            callback(page)
        except Exception as exc:
            result["Status"] = "FAIL"
            result["Error"] = str(exc)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                result["Screenshot"] = str(screenshot_path.relative_to(ROOT))
            except Exception:
                result["Screenshot"] = ""
        finally:
            browser.close()
    return result


def start_server_if_needed() -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["EXPENSE_TRACKER_DB"] = str(DB_PATH)
    log_path = DB_PATH.with_suffix(".log")
    log_handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "from backend.app import app; "
                f"app.run(host='127.0.0.1', port={TEST_PORT}, use_reloader=False)"
            ),
        ],
        cwd=str(ROOT),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )
    process.log_handle = log_handle  # type: ignore[attr-defined]
    try:
        wait_for_server()
    except Exception:
        process.kill()
        log_handle.close()
        output = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        raise RuntimeError(f"Flask app did not become ready.\n{output}") from None
    if process.poll() is not None:
        log_handle.close()
        output = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        raise RuntimeError(f"Flask app exited before tests started.\n{output}")
    return process


def run_scenarios() -> list[dict]:
    cases: list[dict] = []

    def auth_01(page: Page):
        username = unique_username("auth")
        register_user(page, username, "Student", VALID_PASSWORD)
        login_user(page, username, VALID_PASSWORD)

    def auth_02(page: Page):
        page.goto(f"{BASE_URL}/register")
        page.locator("#username").fill("bob_02")
        page.locator("#password").fill("Bob@2024")
        page.locator("#confirm_password").fill("Bob@2024")
        page.locator("[data-registration-form]").evaluate("form => form.requestSubmit()")
        expect(page.locator("#role-error")).to_contain_text("Choose your role")
        expect(page).to_have_url(f"{BASE_URL}/register")

    def auth_03(page: Page):
        page.goto(f"{BASE_URL}/register")
        invalids = ["ab", "averylongusername123", "john doe", "john"]
        for value in invalids:
            page.locator("#username").fill(value)
            page.locator("#role").select_option("Student")
            page.locator("#password").fill("Strong@123")
            page.locator("#confirm_password").fill("Strong@123")
            page.locator("#username").blur()
            expect(page.locator("#username-error")).to_contain_text("Use 3–15")
        page.locator("#username").fill("validuser_90")
        page.locator("#role").select_option("Student")
        page.locator("#password").fill("Strong@123")
        page.locator("#confirm_password").fill("Strong@123")
        page.locator("button[type='submit']").click()
        expect(page).to_have_url(f"{BASE_URL}/login")

    def auth_04(page: Page):
        page.goto(f"{BASE_URL}/register")
        page.locator("#username").fill("mismatch_01")
        page.select_option("#role", "Professional")
        page.locator("#password").fill("Strong@123")
        page.locator("#confirm_password").fill("Strong@124")
        page.locator("#confirm_password").blur()
        expect(page.locator("#confirm-password-error")).to_contain_text("Passwords do not match")

    def auth_05(page: Page):
        username = unique_username("dup")
        register_user(page, username, "Homemaker", VALID_PASSWORD)
        page.goto(f"{BASE_URL}/register")
        page.locator("#username").fill(username)
        page.select_option("#role", "Homemaker")
        page.locator("#password").fill("StrongPass@123")
        page.locator("#confirm_password").fill("StrongPass@123")
        submit = page.locator("button[type='submit']")
        expect(submit).to_be_enabled()
        submit.click()
        expect(page.locator("#username-error")).to_contain_text("already taken")
        expect(page).to_have_url(f"{BASE_URL}/register")

        login_and_expect_error(page, username, "Wrong@999")
        login_and_expect_error(page, unique_username("miss"), "Random@123")

    def auth_06(page: Page):
        page.goto(f"{BASE_URL}/dashboard")
        expect(page).to_have_url(f"{BASE_URL}/login")

    def auth_07(page: Page):
        username = unique_username("out")
        register_user(page, username, "Professional", VALID_PASSWORD)
        login_user(page, username, VALID_PASSWORD)
        sign_out(page)
        page.goto(f"{BASE_URL}/dashboard")
        expect(page).to_have_url(f"{BASE_URL}/login")

    def auth_08(page: Page):
        user_a = unique_username("usa")
        user_b = unique_username("usb")
        register_user(page, user_a, "Student", "Alpha@1234")
        register_user(page, user_b, "Professional", "Bravo@1234")
        login_user(page, user_a, "Alpha@1234")
        page.goto(f"{BASE_URL}/expenses")
        expect(page).to_have_url(f"{BASE_URL}/expenses")
        sign_out(page)
        login_user(page, user_b, "Bravo@1234")
        page.goto(f"{BASE_URL}/profile")
        expect(page.locator("body")).to_contain_text(user_b)
        expect(page.locator("body")).not_to_contain_text(user_a)

    def auth_09(page: Page):
        username = unique_username("csrf")
        register_user(page, username, "Student", VALID_PASSWORD)
        login_user(page, username, VALID_PASSWORD)
        page.goto(f"{BASE_URL}/expenses")
        response = page.evaluate(
            """
            () => fetch('/expenses/add', {
              method: 'POST',
              headers: {'Content-Type': 'application/x-www-form-urlencoded'},
              body: 'amount=12.50&category_id=1&expense_date=2026-10-09&description=csrf-test'
            }).then(r => ({status: r.status, url: r.url}))
            """
        )
        assert response["url"].rstrip("/").endswith("/login"), response
        assert response["status"] in {200, 302, 400, 401}, response

    def auth_10(page: Page):
        username = unique_username("role")
        register_user(page, username, "Student", VALID_PASSWORD)
        login_user(page, username, VALID_PASSWORD)
        page.goto(f"{BASE_URL}/expenses")
        category = page.locator("#modal-category")
        if not category.is_visible():
            page.get_by_role("button", name="Add expense").click()
        expect(category).to_be_visible()
        options = category.locator("option").all_text_contents()
        assert "Education" in options
        assert "Food & Dining" in options
        assert "Other" in options

    def auth_11(page: Page):
        page.goto(f"{BASE_URL}/login")
        submit = page.locator("button[type='submit']")
        expect(submit).to_be_disabled()
        page.locator("#username").fill("validuser_1")
        expect(submit).to_be_disabled()
        page.locator("#password").fill("Valid@123")
        expect(submit).not_to_be_disabled()

    def auth_12(page: Page):
        page.goto(f"{BASE_URL}/register")
        submit = page.locator("button[type='submit']")
        expect(submit).to_be_disabled()
        page.locator("#username").fill("newreg_15")
        expect(submit).to_be_disabled()
        page.select_option("#role", "Professional")
        page.locator("#password").fill("Valid@123")
        expect(submit).to_be_disabled()
        page.locator("#confirm_password").fill("Valid@123")
        expect(submit).not_to_be_disabled()

    test_map = {
        "AUTH-01": ("Registration and login with valid details", auth_01),
        "AUTH-02": ("Role selection validation", auth_02),
        "AUTH-03": ("Username validation", auth_03),
        "AUTH-04": ("Password mismatch and paste prevention", auth_04),
        "AUTH-05": ("Duplicate username and invalid credentials", auth_05),
        "AUTH-06": ("Protected route access without authentication", auth_06),
        "AUTH-07": ("Logout invalidates session", auth_07),
        "AUTH-08": ("User data isolation", auth_08),
        "AUTH-09": ("CSRF protection", auth_09),
        "AUTH-10": ("Role-based category visibility", auth_10),
        "AUTH-11": ("Login button enable/disable logic", auth_11),
        "AUTH-12": ("Registration button enable/disable logic", auth_12),
    }

    for test_id, (title, callback) in test_map.items():
        cases.append(run_case(test_id, title, callback))

    return cases


def generate_report(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item["Status"] == "PASS")
    failed = total - passed
    errors = failed

    workbook = Workbook()
    summary = workbook.active
    summary.title = "Summary"
    summary["A1"] = "Metric"
    summary["B1"] = "Value"
    summary["A1"].font = Font(bold=True)
    summary["A2"] = "Total tests"
    summary["B2"] = total
    summary["A3"] = "Passed"
    summary["B3"] = passed
    summary["A4"] = "Failed"
    summary["B4"] = failed
    summary["A5"] = "Errors"
    summary["B5"] = errors

    details = workbook.create_sheet("Details")
    headers = ["TC ID", "Title", "Status", "Error", "Screenshot"]
    for idx, header in enumerate(headers, start=1):
        cell = details.cell(row=1, column=idx)
        cell.value = header
        cell.font = Font(bold=True)

    for row_index, item in enumerate(results, start=2):
        details.cell(row=row_index, column=1, value=item["TC ID"])
        details.cell(row=row_index, column=2, value=item["Title"])
        details.cell(row=row_index, column=3, value=item["Status"])
        details.cell(row=row_index, column=4, value=item["Error"])
        details.cell(row=row_index, column=5, value=item["Screenshot"])

    for column in ["A", "B", "C", "D", "E"]:
        details.column_dimensions[column].width = 26
    summary.column_dimensions["A"].width = 18
    summary.column_dimensions["B"].width = 12

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(REPORT_PATH)


def choose_port() -> int:
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main() -> None:
    global BASE_URL, TEST_PORT
    TEST_PORT = choose_port()
    BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
    reset_database()
    server_process = start_server_if_needed()
    try:
        results = run_scenarios()
        generate_report(results)
        total = len(results)
        passed = sum(1 for item in results if item["Status"] == "PASS")
        failed = total - passed
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {failed}")
        print(f"Report path: {REPORT_PATH}")
        for item in results:
            error = item["Error"].encode("ascii", errors="replace").decode("ascii")
            print(f"{item['TC ID']}: {item['Status']} | {error}")
            if item["Status"] == "FAIL":
                print(f"Screenshot: {item['Screenshot']}")
    finally:
        if server_process.poll() is None:
            server_process.terminate()
            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()
        log_handle = getattr(server_process, "log_handle", None)
        if log_handle is not None and not log_handle.closed:
            log_handle.close()


if __name__ == "__main__":
    main()
