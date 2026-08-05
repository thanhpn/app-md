# [Tên app/feature] — Plan

> Dùng bởi skill `.claude/skills/build-app/SKILL.md` (nhánh B/C — ngoài CareAi factory, xem `_TEMPLATE.md` cho nhánh CareAi).
> Copy thành `.claude/app-plans/<slug>.md` khi bắt đầu. Điền ngay sau khi plan được duyệt qua `ExitPlanMode` — file plan tạm ở `~/.claude/plans/` bị ghi đè ở lần plan-mode kế tiếp.

## Trạng thái
- Project: (dvc-api / salon-web / beverage-web / reviews-web / velox-web / dvc-worker / mới)
- Ngày bắt đầu:
- Trạng thái: `Đang xây` / `Hoàn thành` / `Đang cải tiến`

## Context
Vì sao xây, vấn đề gì giải quyết.

## Bảng tính năng (mỗi tính năng đã qua bài kiểm tra sắc bén — xem `APP_BUILD_PLAYBOOK.md` mục 9.1)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|

## Data model
```ts
// các interface/schema chính
```

## Kiến trúc kỹ thuật
Convention/pattern có sẵn đang tái dùng (nếu nhánh B), storage/DB, API contract nếu có.

## Danh sách màn hình/route
| Màn hình/Route | Vai trò | Mẫu tham khảo |
|---|---|---|

## Milestone (mỗi milestone phải cho ra thứ verify được ngay khi xong)
| # | Milestone | Tiêu chí verify cụ thể | Trạng thái |
|---|---|---|---|

## Giới hạn đã biết / việc cần người dùng làm thủ công

## Verification đã thực hiện
- Lệnh đã chạy + output thật (không phải lời hứa)
- `git diff --stat`: phạm vi thay đổi

---

## Changelog & Lessons Learned
| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào |
|---|---|---|---|
