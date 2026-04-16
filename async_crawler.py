import asyncio
import json
import os

import re
from base import AbstractPtitCrawler
from entities import  UserCredentials
from aiohttp import ClientSession

from lxml.html import fromstring

COOKIE_FILE = "session_cookies.json"

class MyPtitCrawler(AbstractPtitCrawler):
    def __init__(self, session: ClientSession):
        super().__init__(session)
        self.current_token = ""
        self.sesskey = ""

    def save_cookies(self):
        """Save session cookies to a local JSON file."""
        cookies = {}
        for cookie in self.session.cookie_jar:
            cookies[cookie.key] = cookie.value

        with open(COOKIE_FILE, "w") as f:
            json.dump(cookies, f)
        print("💾 Đã lưu session vào file cục bộ.")

    def load_cookies(self):
        """Load cookies from the local JSON file into the session."""
        if os.path.exists(COOKIE_FILE):
            try:
                with open(COOKIE_FILE, "r") as f:
                    cookies = json.load(f)
                    self.session.cookie_jar.update_cookies(cookies)
                print("📂 Đã tải session cũ từ file.")
                return True
            except Exception as e:
                print(f"⚠️ Không thể tải session cũ: {e}")
        return False

    async def check_session_valid(self) -> bool:
        """Check if the current session is still logged in."""
        try:
            async with self.session.get("https://lms.pttc1.edu.vn/my/", allow_redirects=False) as resp:
                if resp.status == 200:
                    # Session is alive, try to grab the sesskey while we're here
                    html = await resp.text()
                    match = re.search(r'"sesskey":"([^"]+)"', html)
                    if match:
                        self.sesskey = match.group(1)
                    return True
        except:
            pass
        return False

    async def get_user_login(self) -> dict:
        # 1. Try to use existing session first
        if self.load_cookies():
            if await self.check_session_valid():
                print("✅ Session vẫn còn hiệu lực. Bỏ qua đăng nhập thủ công.")

                # --- CRITICAL: CREATE USER OBJECT FROM SAVED DATA ---
                # If you don't save the username to a file, you can just use "Cached User"
                self.user = UserCredentials(
                    username="Cached User",
                    password="HIDDEN",
                    logintoken=self.sesskey
                )
                return {"status": "reused", "sesskey": self.sesskey}
            else:
                print("❌ Session hết hạn hoặc không hợp lệ.")

        # 2. Manual login flow
        print("\n--- XÁC THỰC NGƯỜI DÙNG THỦ CÔNG ---")

        if not self.current_token:
            # Note: Make sure get_main_page_session_id sets self.current_token
            await self.get_main_page_session_id()

        loop = asyncio.get_event_loop()
        username = await loop.run_in_executor(None, input, "Tên đăng nhập: ")
        password = await loop.run_in_executor(None, input, "Mật khẩu: ")

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://lms.pttc1.edu.vn/login/index.php',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }

        data = {
            'logintoken': self.current_token,
            'username': username,
            'password': password,
        }

        try:
            async with self.session.post(
                    'https://lms.pttc1.edu.vn/login/index.php',
                    headers=headers,
                    data=data,
                    allow_redirects=True
            ) as response:
                final_html = await response.text()

                if response.status == 200 and "login" not in str(response.url):
                    match = re.search(r'"sesskey":"([^"]+)"', final_html)
                    if match:
                        self.sesskey = match.group(1)

                    print(f"✅ Đăng nhập thành công.")

                    # --- CRITICAL: CREATE USER OBJECT HERE ---
                    self.user = UserCredentials(
                        username=username,
                        password=password,
                        logintoken=self.sesskey
                    )

                    self.save_cookies()
                    return {"username": username, "sesskey": self.sesskey}
                else:
                    print("❌ Đăng nhập thất bại.")
        except Exception as e:
            print(f"❌ Lỗi: {e}")

        return {}

    async def get_main_page_session_id(self) -> str:
        print("Đang vào trang chủ....")

        try:
            # Use self.session from the abstract class
            async with self.session.get("https://lms.pttc1.edu.vn/login/index.php") as response:
                if response.status != 200:
                    print(f"Lỗi kết nối: {response.status}")
                    return ""

                html_content = await response.text()

                # The regex we built earlier
                match = re.search(r'name="logintoken"\s+value="([^"]+)"', html_content)

                if match:
                    token = match.group(1)
                    self.current_token = token
                    print(f"Đã tìm thấy token: {token}")
                    return token
                else:
                    print("Không tìm thấy logintoken trong HTML")
                    return ""

        except Exception as e:
            print(f"Đã xảy ra lỗi khi lấy token: {e}")
            return ""



    async def extract_in_progress_courses(self) -> list:
        """
        Extracts courses marked as 'inprogress' using the Moodle AJAX service.
        """
        print("--- ĐANG TRÍCH XUẤT KHÓA HỌC ĐANG DIỄN RA ---")

        # 1. Ensure we have the sesskey from the login step
        # If self.user.logintoken stores your sesskey as we set up before:
        current_sesskey = getattr(self.user, 'logintoken', '')

        if not current_sesskey:
            print("❌ Lỗi: Không có sesskey. Không thể lấy danh sách khóa học.")
            return []

        url = 'https://lms.pttc1.edu.vn/lib/ajax/service.php'

        params = {
            'sesskey': current_sesskey,
            'info': 'theme_remui_get_myoverviewcourses',
        }

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Origin': 'https://lms.pttc1.edu.vn',
            'Referer': 'https://lms.pttc1.edu.vn/my/courses.php',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

        # Moodle AJAX service expects a list of method calls
        json_data = [
            {
                'index': 0,
                'methodname': 'theme_remui_get_myoverviewcourses',
                'args': {
                    'offset': 0,
                    'limit': 0,  # 0 usually means fetch all
                    'classification': 'inprogress',
                    'sort': 'fullname',
                    'customfieldname': '',
                    'customfieldvalue': '',
                },
            },
        ]

        try:
            # Using self.session.post (Async)
            async with self.session.post(
                    url,
                    params=params,
                    headers=headers,
                    json=json_data
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    # Moodle AJAX returns a list corresponding to the json_data input list
                    # We want the 'data' field inside the first element's result
                    if data and not data[0].get('error'):
                        courses = data[0].get('data', [])
                        print(f"✅ Tìm thấy {len(courses)} khóa học đang diễn ra.")
                        return courses
                    else:
                        error_msg = data[0].get('exception', 'Unknown error')
                        print(f"❌ Lỗi từ Server: {error_msg}")
                else:
                    print(f"❌ Lỗi HTTP: {response.status}")

        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách khóa học: {e}")

        return []

    async def view_courses(self) -> None:
        """
        Orchestrates all courses concurrently.
        """
        courses_response = await self.extract_in_progress_courses()

        try:
            # Assuming the structure is data[0]['data']['courses']
            course_list = courses_response['courses']
        except (IndexError, KeyError, TypeError):
            print("❌ Không thể lấy danh sách khóa học.")
            return

        print(f"🚀 Khởi chạy trình xem {len(course_list)} khóa học song song...")

        # Run each course as a separate concurrent task
        await asyncio.gather(*(self.view_lessons(str(c['id']), c['fullname']) for c in course_list))

        print("\n✨ Hoàn thành tất cả các khóa học.")

    async def view_lessons(self, course_id: str, course_name: str) -> None:
        """
        Handles a single course: visits lessons, checks for unlocks, and repeats.
        """
        processed_cm_ids = set()

        while True:
            print(f"🔄 [{course_name}] Đang kiểm tra trạng thái mới...")
            state = await self._get_course_state(course_id)
            state = json.loads(state)

            if not state:
                break

            sections = state.get('section', [])
            # Create a map for quick lookup: { "46289": {module_data} }
            all_modules = {str(m['id']): m for m in state.get('cm', [])}

            new_content_found_in_loop = False

            for section in sections:
                section_title = section.get('title', 'General')
                cm_ids = section.get('cmlist', [])

                # Find modules in this section we haven't touched yet
                to_process = [str(cid) for cid in cm_ids if str(cid) not in processed_cm_ids]

                if not to_process:
                    continue

                print(f"📖 [{course_name}] -> Chương: {section_title}")

                for cm_id in to_process:
                    module = all_modules.get(cm_id)

                    # Check if it's visible (not locked by a previous requirement)
                    if module and module.get('uservisible'):
                        url = module.get('url')
                        await self._visit_lesson(url, course_name)
                        processed_cm_ids.add(cm_id)
                        new_content_found_in_loop = True
                    else:
                        # If the first unprocessed item in a section is locked,
                        # we usually can't see the rest of the section.
                        print(f"   🔒 [{course_name}] Bài {cm_id} đang bị khóa.")
                        break

                        # If we processed new content, we break the section loop
                # to refresh the state and see if the NEXT section unlocked.
                if new_content_found_in_loop:
                    break

            # If we went through all sections and found nothing new to do, the course is finished
            if not new_content_found_in_loop:
                print(f"✅ [{course_name}] Đã xử lý xong tất cả bài học hiện có.")
                break

    async def _visit_lesson(self, url: str, course_name: str) -> None:
        """Visits the URL to trigger the 'viewed' status in Moodle."""
        if not url:
            return
        try:
            async with self.session.get(url, timeout=15) as resp:
                status = "✅" if resp.status == 200 else f"❌ ({resp.status})"
                # Extracting ID from URL for cleaner logging
                html_data = await resp.text()
                lesson_id = url.split('id=')[-1] if 'id=' in url else "unknown"
                print(f"      {status} [{course_name}] Truy cập bài: {lesson_id}")
                # Human-like pacing per lesson
                await asyncio.sleep(0.8)
        except Exception as e:
            print(f"      ⚠️ [{course_name}] Lỗi kết nối bài {url}: {e}")

    async def _get_course_state(self, course_id: str) -> dict:
        """Helper to fetch the current JSON state of the course."""
        url = 'https://lms.pttc1.edu.vn/lib/ajax/service.php'
        sesskey = getattr(self.user, 'logintoken', '')

        params = {'sesskey': sesskey, 'info': 'core_courseformat_get_state'}
        json_data = [{
            'index': 0,
            'methodname': 'core_courseformat_get_state',
            'args': {'courseid': int(course_id)},
        }]

        try:
            async with self.session.post(url, params=params, json=json_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0].get('data', {})
        except Exception as e:
            print(f"❌ Lỗi tải trạng thái: {e}")
        return {}


