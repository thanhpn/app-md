# Migraine Diary — Trigger Tracker — Plan

## Trạng thái
- Bundle ID: `com.careai.migraine`
- Trạng thái: `MVP hoàn thành`, đã qua 1 vòng review logic nghiệp vụ nghiêm túc + sửa bug thật

## Context
Bằng chứng thị trường: Health & Fitness dẫn đầu review tiêu cực (5.395 review phê phán), cộng đồng đau mãn tính than phiền app hiện có (Migraine Buddy, Bearable, Manage My Pain) bắt tạo tài khoản + đẩy dữ liệu bệnh lên cloud hãng. Định vị: log cơn đau ~10 giây, phân tích tương quan trigger **chạy hoàn toàn trên máy** (không server nào thấy dữ liệu), minh bạch về độ tin cậy thống kê thay vì tuyên bố mơ hồ, xuất PDF cho bác sĩ, đồng bộ qua **iCloud của chính người dùng** (không phải cloud hãng — trả lời đúng khiếu nại của cộng đồng thay vì lặp lại nó).

**Đối tượng mục tiêu quốc tế/tiếng Anh** (khác Rental/PetCare vốn nhắm thị trường Việt) — vì bằng chứng nghiên cứu đọc như từ App Store quốc tế, và thuật ngữ y khoa (photophobia, phonophobia, aura...) cần chuẩn ICHD-3 để có độ tin cậy với cả bệnh nhân lẫn bác sĩ họ đưa PDF cho xem.

## Bảng tính năng cuối cùng
5 tab: **Today** (log nhanh + cảnh báo lạm dụng thuốc MOH) · **Journal** · **Analysis** (biểu đồ + correlation cards, gate Premium) · **Profile** (thuốc + export) · **Settings** (iCloud sync + backup).

**Monetization cố ý khác 2 app trước**: Free = logging + journal + lịch sử 60 ngày. Premium = **chính engine phân tích tương quan** (giá trị lõi) + PDF export + iCloud sync — gate vào tính năng tạo giá trị thật, không phải giới hạn số lượng vô nghĩa.

## Data model
`src/app/types/migraine.ts`: `Attack` (intensity 0-10 NRS, locations đa chọn, symptoms theo ICHD-3, medicationsTaken), `DailyContext` (**bắt buộc log cả ngày KHÔNG đau** — đây là nhóm đối chứng thống kê, không tuỳ chọn), `Medication` (category acute/preventive + drugClass để tính MOH), `CustomTrigger`, `MigraineSettings`.

## Kiến trúc kỹ thuật — engine thống kê (điểm khác biệt hoá chính)
`src/app/common/migraine/correlationEngine.ts`:
1. `buildDayIndex()` — 1 record/ngày từ ngày log đầu tiên tới hôm nay, gồm cả ngày không đau.
2. Với mỗi factor (ngủ <6h, stress cao, rượu, bỏ bữa, thời tiết, hành kinh, trigger tuỳ chỉnh...) — dựng bảng 2×2, tính **Fisher's exact test** (p-value chính xác, không xấp xỉ — phù hợp cỡ mẫu nhỏ của dữ liệu cá nhân).
3. Ngưỡng mẫu tối thiểu (`MIN_SAMPLE_SIZE = 14`) trước khi hiển thị bất kỳ pattern nào. Luôn hiện số liệu gốc ("12/15 ngày"), không chỉ phần trăm. Ngôn ngữ luôn "liên quan đến", không bao giờ "gây ra".
4. `medicationOveruse.ts` — đếm số **ngày** (không phải liều) dùng thuốc cắt cơn/30 ngày, cảnh báo theo ngưỡng ICHD-3 thật (>10 ngày/tháng triptan/opioid, >15 ngày giảm đau thường).

**Đã viết Jest test thật, đã CHẠY THẬT** — `__tests__/correlationEngine.test.ts` + `__tests__/dateHelpers.test.ts`, 16/16 pass, đối chiếu với ví dụ thống kê kinh điển đã công bố (bài toán "Lady Tasting Tea" của Fisher, bảng [[3,1],[1,3]] → p=0.4857 khớp tài liệu thống kê chuẩn).

## Đồng bộ iCloud
Tách rõ: phần JS (`src/app/services/iCloudSync.ts`, merge record-level theo `updatedAt`) + source native mới (`ios/CareAi/UbiquityContainer.swift`/`.m`) do Claude viết, nhưng **việc wire vào Xcode target (Compile Sources, entitlements riêng, bật capability) để người dùng tự làm qua Xcode UI** — không tự sửa `project.pbxproj`/entitlements dùng chung (xem mục 6.1-6.2 Playbook — bài học rút ra chính từ app này).

## Verification đã thực hiện
- 16/16 Jest test pass thật (không chỉ tuyên bố).
- Xác nhận bằng tsconfig cách ly rằng `tsc --noEmit` chuẩn của dự án đã mất khả năng kiểm tra ngữ nghĩa (xem Changelog).
- `git diff --stat`: phạm vi đúng như plan.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-07-26 | `checkMedicationOveruse()` so `takenAt` với `dayjs(referenceDate)` (= nửa đêm) bằng `.isAfter()` trực tiếp → mọi liều thuốc uống **sau đó cùng ngày tham chiếu** (trường hợp phổ biến nhất — uống thuốc rồi mới mở app) bị loại nhầm là "trong tương lai" | Không so theo **toàn bộ ngày** (`startOf('day')`/`endOf('day')`), so trực tiếp timestamp với mốc nửa đêm | Đổi sang so với `windowEnd = dayjs(referenceDate).endOf('day')` | Có — mục 4.4 Playbook |
| 2026-07-26 | 8 chỗ dùng `isoString.slice(0, 10)` / `.slice(0, 7)` để suy ra ngày/tháng — cho ra ngày **UTC**, không phải ngày địa phương người dùng. Không nhất quán với `buildDayIndex()` (dùng `dayjs().format()` đúng theo local) | Thói quen cắt chuỗi nhanh thay vì đi qua dayjs; không nhận ra ISO string lưu là UTC | Tạo `dateHelpers.ts` (`localDateOf`/`localMonthOf`), thay thế toàn bộ 8 chỗ | Có — mục 4.4 Playbook (quy tắc trung tâm, áp dụng mọi app) |
| 2026-07-26 | Viết test regression cho bug ngày UTC bằng timestamp UTC hardcode — **chính test đó lại sai** vì môi trường sandbox chạy ở múi giờ Asia/Saigon (UTC+7), khiến mốc giờ hardcode rơi sang ngày khác so với giả định | Không nhận ra timezone của môi trường chạy test ảnh hưởng tới `dayjs()` không có đối số | Viết lại test dùng `dayjs(referenceDate).hour(20)` (tương đối, không hardcode UTC) — test đúng ở MỌI múi giờ | Nên thêm: viết test ngày-giờ luôn tương đối theo `dayjs(...)`, không hardcode chuỗi ISO UTC tuyệt đối |
| 2026-07-26 | `Medication` thiếu `updatedAt` → logic merge iCloud (`mergeById`, "ai `updatedAt` mới hơn thắng") không thể phân biệt bản nào mới hơn khi sửa thuốc trên 2 máy khác nhau | Thiết kế type ban đầu chỉ nghĩ tới `createdAt` | Thêm `updatedAt: string` bắt buộc vào type, set lại ở `CreateMedicationScreen` mỗi lần lưu (kể cả edit) | Có — mục 4.5 Playbook |
| 2026-07-26 | PDF report: mục "Trigger Correlations" tính trên TOÀN BỘ lịch sử nhưng không ghi rõ — trong khi header PDF ghi "Period: Last 30 days" (áp dụng cho bảng attack log, không áp dụng cho correlation) → bác sĩ đọc dễ hiểu nhầm phạm vi dữ liệu | Cố ý dùng toàn bộ lịch sử cho correlation (đúng về mặt thống kê — cắt ngắn sẽ làm giảm độ tin cậy) nhưng quên ghi rõ trong UI | Thêm dòng chú thích ngay dưới heading "Trigger Correlations" trong `buildReportHtml.ts` | Chưa — cân nhắc thêm quy tắc chung "mọi số liệu tổng hợp trong export phải ghi rõ phạm vi dữ liệu dùng để tính" nếu gặp lại ở app khác |
| 2026-07-26 | `redux/migraine/saga.ts`: ban đầu để `attacksByMonth`/`contextsByMonth`/`allAttacks`/`allDailyContexts` chung 1 reducer với `medications`/`settings`, rồi whitelist cả reducer đó → dữ liệu time-series bị nhân đôi vào blob `redux-persist`, phình to vô hạn theo năm sử dụng | Thiết kế ban đầu không tách riêng "state nhỏ cần persist" khỏi "cache lớn chỉ nên rehydrate" | Tách thành 2 reducer: `migraine` (whitelist) + `migraineHistory` (KHÔNG whitelist, rebuild từ file tháng lúc mở app) | Có — mục 4.2 Playbook (viết ngay từ đầu khi thiết kế app này, trước khi kịp mắc lỗi ở Rental/PetCare — nên áp dụng ngược lại cho 2 app đó khi có dịp) |
| 2026-07-26 | Môi trường: `tsc --noEmit` chuẩn dự án báo "0 lỗi mới" nhưng thực ra **không còn kiểm tra ngữ nghĩa** cho toàn dự án (do file cú pháp lỗi có sẵn: `YogaPlanPro2/3.ts`, nhiều `.js` Flow-annotation dưới `allowJs`) | Phát hiện khi cố tình chèn 1 lỗi rõ ràng (thiếu property bắt buộc) vào code và thấy `tsc` không báo gì | Dựng tsconfig cách ly (`allowJs:false`, loại trừ file lỗi cú pháp đã biết) để kiểm tra ngữ nghĩa thật — phát hiện thêm 3 bug PetCare (xem `pet-care-journal.md`) | Có — mục 6.5 Playbook |
| 2026-07-26 | Môi trường: chạy Jest báo `clearMocksOnScope is not a function` | `react-native` mang theo `jest-environment-node`/`jest-mock` phiên bản riêng lồng trong `node_modules/react-native/node_modules/`, lệch version với `jest` top-level; `resolutions` không ép được version cho dependency khai báo trực tiếp trong `package.json` | Đặt `jest` khớp chính xác version mà `react-native` mong đợi (`^29.7.0`), `rm -rf node_modules && yarn install` | Có — mục 6.6 Playbook |
| 2026-07-26 | Sau khi sửa lỗi jest ở trên (2 lần `rm -rf node_modules`), gây ra **2 bản React song song** (`19.2.7` top-level vs `19.1.1` lồng trong hầu hết package con) → crash runtime `Cannot read property 'useMemo' of null` khi người dùng chạy app thật | `resolutions: {"react": "19.1.1"}` có sẵn nhưng không ép được version cho `react` vì nó cũng là dependency khai báo trực tiếp (`^19.1.1`, dạng dải) trong `package.json` — cùng nguyên nhân gốc như bug jest ở trên, chỉ khác package | Đổi `"react": "^19.1.1"` → `"react": "19.1.1"` (cố định, khớp ý định của `resolutions`), `rm -rf node_modules && yarn install` lại | Có — mục 6.6 Playbook (đúc kết thành quy tắc chung: dependency khai báo trực tiếp bị lồng đôi → sửa version cố định, đừng chỉ trông cậy `resolutions`) |

**Việc còn cần người dùng làm thủ công**: 3 bước Xcode cho iCloud (xem mục 6.1-6.3 Playbook) — thêm `UbiquityContainer.swift`/`.m` vào Compile Sources của target Migraine, tạo entitlements riêng, bật capability iCloud Documents qua UI Xcode. Setting "giờ nhắc nhật ký hàng ngày" hiện lưu được nhưng **chưa có gì thực sự lên lịch thông báo** — đã hỏi người dùng có muốn nối vào `createNotification()` (pattern PetCare đã dùng) không, đang chờ phản hồi.
