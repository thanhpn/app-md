# [Tên App] — Plan

> Copy file này thành `.claude/app-plans/<app-slug>.md` khi bắt đầu 1 app mới.
> Điền vào ngay sau khi plan được duyệt qua `ExitPlanMode` — đừng để trống quá lâu vì file plan tạm ở `~/.claude/plans/` sẽ bị ghi đè ở lần plan-mode kế tiếp.

## Trạng thái
- Bundle ID: `com.careai.xxx`
- Ngày bắt đầu:
- Trạng thái: `Đang xây` / `MVP hoàn thành` / `Đang cải tiến`

## Context
Vì sao xây app này, vấn đề gì nó giải quyết, bằng chứng thị trường (nếu có).

## Phân tích thị trường (tóm tắt)
Đối thủ chính, điểm yếu của họ, khoảng trống.

## Bảng tính năng cuối cùng (sau bước tự phản biện)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|

## Data model
```ts
// các interface chính
```

## Kiến trúc kỹ thuật
- Redux slice: `src/redux/<app>/`
- Storage strategy: (sharding theo tháng? whitelist gì, không whitelist gì?)
- Business logic engine đặc biệt (nếu có): file, thuật toán, cách test

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|

## Monetization
Free tier gồm gì, Premium gate vào đâu.

## Giới hạn đã biết / việc cần người dùng làm thủ công
(VD: bước Xcode thủ công, tài khoản Apple Developer, v.v.)

## Build order
1.
2.

## Verification đã thực hiện
- `tsc --noEmit`: ...
- Jest test: file nào, kết quả thật (không phải lời hứa)
- `git diff --stat`: phạm vi thay đổi

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| | | | | |
