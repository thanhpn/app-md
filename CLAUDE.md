# careai/ — workspace gốc

Thư mục này chứa 5 project độc lập (mỗi project 1 git repo riêng, xem `ARCHITECTURE.md` để biết chi tiết quan hệ): `CareAi/`, `dvc-api/`, `salon-web/`, `beverage-web/`, `velox-web/`.

- **`.claude/CODING_GUIDELINES.md`** — quy tắc hành vi coding chung (suy nghĩ trước khi code, đơn giản trước tiên, thay đổi có phẫu thuật, thực thi hướng-mục-tiêu). Áp dụng nền cho MỌI project ở đây, kết hợp thêm rule riêng từng project. Nội dung này cũng đã nhúng trực tiếp vào `CLAUDE.md` của từng project con để vẫn áp dụng khi project đó được mở độc lập (không mở chung workspace này) — sửa `CODING_GUIDELINES.md` thì nhớ đồng bộ lại các bản nhúng đó (danh sách ở cuối file `CODING_GUIDELINES.md`).
- **`.claude/APP_BUILD_PLAYBOOK.md`** — quy tắc RIÊNG cho factory app **CareAi** (React Native, ~90+ app qua bundle-id switching). Không áp dụng cho 4 project còn lại.
- **`ARCHITECTURE.md`** — tổng quan quan hệ giữa 5 project, khi nào project nào độc lập/liên quan tới nhau.
