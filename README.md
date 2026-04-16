# PTIT LMS Auto Complete

Công cụ hỗ trợ truy cập và xem tự động các bài học trên hệ thống LMS.


## ✨ Tính năng nổi bật

- **Xử lý bất đồng bộ (Asyncio):** Sử dụng `aiohttp` để truy cập nhiều khóa học cùng lúc mà không làm treo chương trình.
- **Cơ chế Mở khóa thông minh:** Tự động làm mới trạng thái khóa học sau mỗi chương để nhận diện và truy cập các bài học vừa được mở khóa (unlocked).
- **Quản lý Session thông minh:** - Lưu Cookie vào file cục bộ (`session_cookies.json`).
    - Tự động kiểm tra và tái sử dụng Session cũ, chỉ yêu cầu đăng nhập thủ công khi Session hết hạn.
- **Trích xuất dữ liệu AJAX:** Sử dụng trực tiếp các endpoint API của Moodle (`core_courseformat_get_state`) giúp dữ liệu chính xác và ổn định hơn.

## 🛠 Cấu trúc dự án

- `PtitCrawlerProtocol`: Định nghĩa giao thức chuẩn cho Crawler.
- `AbstractPtitCrawler`: Lớp trừu tượng quản lý session, đăng nhập và lưu trữ.
- `UserCredentials`: Dataclass lưu trữ thông tin tài khoản và `sesskey`.

## 🚀 Hướng dẫn sử dụng
Cài python 3.9 trở lên rồi vào thư mục paste:
```bash
python3 -m pip install -r requirements.txt
```
Sau đó chạy: 
```bash
python3 main.py
```

Nếu cần đăng nhập thì đăng nhập bằng MSV.
