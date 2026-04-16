from abc import ABC, abstractmethod

from aiohttp import ClientSession



class AbstractPtitCrawler(ABC):
    def __init__(self, session: ClientSession):
        self.session = session
        self.user = None
        self.current_token = ""

    @abstractmethod
    async def get_main_page_session_id(self, *args, **kwargs) -> str:
        """Fetch the main page ID."""
        pass

    @abstractmethod
    async def get_user_login(self) -> any:
        """Fetch credentials."""
        pass

    @abstractmethod
    async def extract_in_progress_courses(self) -> list:
        """Scrape the course list."""
        pass

    @abstractmethod
    async def view_courses(self,  course_id: str, course_name: str) -> None:
        """Process and display courses."""
        pass

    @abstractmethod
    async def view_lessons(self, course_id):
        """access the lesson to show that you viewed."""
        pass

    async def _run(self) -> None:
        """
        The orchestrator: Checks for existing sessions before
        starting manual login flow.
        """
        print("🚀 Bắt đầu tiến trình crawler...")

        # 1. Attempt to login (this checks local file first internally)
        # The get_user_login method we built handles the logic:
        # Try Local -> If Fail -> Fetch Token -> Prompt User -> Save Local
        login_result = await self.get_user_login()

        if login_result:
            print("📖 Đang lấy danh sách khóa học...")

            # 2. Extract and View courses
            # You might want to store the courses in a variable if needed later
            await self.view_courses()

            print("\n✅ Hoàn thành tiến trình.")
        else:
            print("❌ Không thể tiếp tục do đăng nhập thất bại.")