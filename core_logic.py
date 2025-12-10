import os
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Constants
SESSIONS_DIR = os.path.join(os.path.expanduser("~"), ".config", "social-poster")
SESSIONS_FILE = os.path.join(SESSIONS_DIR, "sessions.json")

def ensure_session_dir():
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR, exist_ok=True)

def load_sessions():
    ensure_session_dir()
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sessions: {e}")
            return {}
    return {}

def save_sessions(sessions):
    ensure_session_dir()
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"Error saving sessions: {e}")

class SocialPoster:
    def __init__(self, headless=True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.sessions = load_sessions()

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

    def stop(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def get_context(self, platform):
        if not self.browser:
            self.start()

        # Create context if not exists or if we need to switch (simplified for single context usage here)
        # Ideally we reuse context or create new one per task
        if self.context:
            return self.context

        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )

        # Load session if exists
        session = self.sessions.get(platform)
        if session and 'cookies' in session:
            self.context.add_cookies(session['cookies'])

        return self.context

    def save_session(self, platform, page):
        cookies = self.context.cookies()
        # simplified session storage, just cookies for now
        self.sessions[platform] = {
            'cookies': cookies,
            'last_validated': datetime.now().isoformat()
        }
        save_sessions(self.sessions)

class XPlatform:
    def __init__(self, poster):
        self.poster = poster
        self.platform_name = 'x'
        self.base_url = 'https://x.com'
        self.login_url = 'https://x.com/i/flow/login'

    def is_logged_in(self, page):
        try:
            # Check for account switcher or profile link
            page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"]', timeout=5000)
            return True
        except:
            return False

    def login(self, username, password, two_factor_code=None):
        context = self.poster.get_context(self.platform_name)
        page = context.new_page()

        try:
            page.goto(self.login_url)

            if self.is_logged_in(page):
                self.poster.save_session(self.platform_name, page)
                return True, "Already logged in"

            # Username
            page.wait_for_selector('input[name="text"]', timeout=10000)
            page.fill('input[name="text"]', username)
            page.click('text="Next"') # Generalized text selector

            # Check for unusual activity/phone verification
            try:
                page.wait_for_selector('input[name="text"]', timeout=5000)
                # If it asks again, it might be phone/email check.
                # For simplicity, assuming standard flow or re-entering username if it's that weird dual check
                input_val = page.input_value('input[name="text"]')
                if not input_val:
                     page.fill('input[name="text"]', username) # or phone if provided
                     page.click('text="Next"')
            except:
                pass

            # Password
            page.wait_for_selector('input[name="password"]', timeout=10000)
            page.fill('input[name="password"]', password)
            page.click('[data-testid="LoginForm_Login_Button"]')

            # 2FA
            if two_factor_code:
                try:
                    page.wait_for_selector('input[name="text"]', timeout=5000)
                    page.fill('input[name="text"]', two_factor_code)
                    page.click('text="Next"')
                except:
                    pass

            page.wait_for_url('https://x.com/home', timeout=15000)

            if self.is_logged_in(page):
                self.poster.save_session(self.platform_name, page)
                return True, "Login successful"
            else:
                return False, "Login failed verification"

        except Exception as e:
            return False, f"Login error: {str(e)}"
        finally:
            page.close()

    def post(self, text, media_files=None):
        context = self.poster.get_context(self.platform_name)
        page = context.new_page()

        try:
            page.goto(self.base_url)

            if not self.is_logged_in(page):
                 return False, "Not logged in"

            # Click compose
            page.click('[data-testid="SideNav_NewTweet_Button"]')
            page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=10000)

            # Type text
            page.fill('[data-testid="tweetTextarea_0"]', text)

            # Handle media (simplified)
            if media_files:
                # Expecting paths
                with page.expect_file_chooser() as fc_info:
                    page.click('[aria-label="Add photos or video"]')
                file_chooser = fc_info.value
                file_chooser.set_files(media_files)
                # Wait for upload
                time.sleep(2) # Naive wait

            # Tweet
            page.click('[data-testid="tweetButtonInline"]')

            # Wait for success toast or post to appear
            # Simplified: wait a bit
            time.sleep(3)

            return True, "Posted successfully"

        except Exception as e:
            return False, f"Post error: {str(e)}"
        finally:
            page.close()
