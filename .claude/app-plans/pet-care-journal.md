# PetCare — Nhật Ký Chăm Sóc Thú Cưng — Plan

## Trạng thái
- Bundle ID: `com.careai.petcare` (**app ĐÃ LIVE trên App Store thật** — App Store ID `6751769332` — khác với Rental/Migraine vốn chưa publish)
- Trạng thái: `MVP hoàn thành` (đại tu toàn bộ, chưa build/run thật)

## Context
App "Pet Care" đã tồn tại nhưng chỉ là bản reskin nông của template Diary/Baby dùng chung — không có hồ sơ thú cưng, không theo dõi ăn uống/vệ sinh/cân nặng có cấu trúc, không nhắc lịch tiêm phòng. Người dùng yêu cầu đại tu **tại chỗ** (giữ nguyên bundle id, không tạo app mới) nhưng **tuyệt đối không ảnh hưởng app khác** — vì đây là app ĐANG SỐNG có người dùng thật.

**Quyết định kiến trúc quan trọng**: vì app đã live, không được xoá dữ liệu người dùng cũ một cách phá hoại — chấp nhận rằng dữ liệu note/todo cũ (từ template Diary dùng chung) sẽ không còn hiển thị trong UI mới (không bị xoá khỏi storage, chỉ không dùng tới), đây là đánh đổi được người dùng ngầm chấp nhận khi yêu cầu đại tu.

## Bảng tính năng cuối cùng
5 tab: **Hôm Nay** (ghi nhanh 7 loại nhật ký) · **Nhật Ký** · **Sức Khỏe** (khám/tiêm phòng/thuốc) · **Thống Kê** (biểu đồ + cảnh báo bất thường) · **Thú Cưng** (hồ sơ + cài đặt + 8 công cụ hữu ích).

Công cụ bổ sung sau lần đầu (theo yêu cầu tiếp theo của người dùng, dạng menu `SettingList` giống các app khác trong factory): BCS calculator, tính calo, tính lượng nước, quy đổi tuổi người, danh sách thực phẩm/cây độc hại, thẻ nhận diện thú cưng (chia sẻ ảnh), checklist chuẩn bị đi khám/du lịch, nhắc lịch chải lông/tắm/cắt móng.

## Data model
`src/app/types/pet.ts`: `Pet`, `PetLogEntry` (1 type đa hình duy nhất cho 7 loại log thay vì 7 bảng riêng — quyết định có chủ đích để giữ UX "ghi nhanh" trong 1 màn hình), `VetVisit`, `PreventiveCare` (gộp vaccination+deworming+flea_tick), `Medication`, `GroomingTask`, `PetSettings`.

## Kiến trúc kỹ thuật
- Redux slice: `src/redux/pet/` — `logsByMonth` sharded theo tháng giống Rental (chưa tách history reducer riêng, xây trước khi rút ra bài học ở Migraine).
- Business logic: `src/app/common/pet/insights.ts` (anomaly detection: sụt cân, nôn nhiều, mèo không đi vệ sinh 24h — cảnh báo urgent vì có thể là tắc nghẽn đường tiết niệu), `medicationOveruse` KHÔNG áp dụng ở app này (đó là Migraine).
- Reuse: `SettingList` component (dùng chung toàn factory) cho menu công cụ, `formatVND`/`parseVNDInput` từ `common/rental/formatVND.ts` (tái dùng qua app, hợp lý vì là pure currency formatter không phụ thuộc domain).

## Wiring đặc biệt (khác Rental/Migraine vì là đại tu, không phải app mới)
- Gỡ `isPetCareApp` khỏi 3 shared tab chung (`isShowLearnStack`, `isShowDiaryStack`, `isShowFoodStack`) trong `navigation/index.js` — PetCare giờ có tab riêng hoàn toàn.
- Phát hiện và sửa 2 chỗ `isPetCareApp` bị wire nhầm hiển thị nội dung của app KHÁC (Baby vitals trong `TemperatureMonitorScreen`, Kayak trong `HomeWorkoutStack`) — bug có sẵn từ trước, dọn luôn khi đại tu.
- Xoá hẳn 3 file màn hình cũ nông (`PetFoodScreen`, `PetLearnScreen`, `PetActivitiesScreen`) sau khi xác nhận không còn nơi nào tham chiếu.

## Monetization
Free: 1 thú cưng, lịch sử 30 ngày. Premium (placeholder): không giới hạn, ẩn quảng cáo, cảnh báo/nhắc lịch không giới hạn.

## Verification đã thực hiện
- `tsc --noEmit`: 0 lỗi mới so với baseline (thời điểm build — xem cảnh báo về độ tin cậy ở mục 6.5 Playbook).
- Không có Jest test khi build lần đầu.
- **Đã audit lại bằng tsconfig cách ly** (mục 6.5 Playbook) trong lượt review sau — phát hiện bug thật, xem bảng dưới.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-07-26 | `redux/pet/saga.ts` tạo object `NotificationConfig` thiếu field bắt buộc `schedule` ở **3 chỗ** (nhắc tiêm phòng, nhắc uống thuốc, nhắc chải lông) | `tsc --noEmit` chuẩn của dự án đã âm thầm tắt kiểm tra ngữ nghĩa toàn dự án (do file lỗi cú pháp có sẵn khác) nên không báo lỗi thiếu field khi code được viết | Dùng tsconfig cách ly (loại trừ file lỗi cú pháp, tắt `allowJs`) để bắt lại lỗi ngữ nghĩa thật, thêm `schedule: 0` (field không thực sự được `createNotification()` đọc ở runtime, nhưng bắt buộc theo type) vào cả 3 chỗ | Có — mục 6.5 Playbook |
| 2026-07-26 | `CreatePetScreen`: tham số `uri` trong callback `onSave` bị implicit `any` | Tương tự — bị che bởi lỗ hổng tsc | Thêm annotation tường minh `(uri: string) =>` | Có — mục 6.5 Playbook (cùng nguyên nhân gốc) |
