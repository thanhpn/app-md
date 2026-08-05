# KidGrow / BabyGrow Journal — Plan

## Trạng thái
- Bundle ID: `com.careai.baby`
- Ngày bắt đầu: 2026-08-03
- Trạng thái: `Đang cải tiến` — M1/M2/M3 đã xong + verify test thật (2026-08-03). M4 (nhắc lịch) + M5 (iCloud sync + Premium screen) còn lại, tạm dừng theo yêu cầu người dùng để tự test trên máy trước khi làm tiếp.

## Context
App đã tồn tại (marketing tên "BabyGrow Journal", chưa publish — App Store ID rỗng trong `AppConstant.ts`) nhưng chỉ dừng ở mức log thủ công (feeding/sleep/diaper/height/weight/head/vaccination), không khác gì ghi vào Excel. Store listing (`app-asset/description/baby.md`) đã hứa sẵn: so sánh biểu đồ tăng trưởng theo chuẩn WHO, nhắc lịch ăn/tiêm chủng, chia sẻ gia đình — không cái nào có thật trong code. Khảo sát sâu (2 Explore/Plan agent + đọc trực tiếp code) còn phát hiện nhiều bug thật: field `birthday` sai (đọc field không tồn tại trong type), thiếu `updatedAt` trên mọi entity, dead code (`saveBabyActivityByMonth` ghi mà không ai đọc lại), console.log rơi rớt, và vi phạm kiến trúc nghiêm trọng — `redux/baby` bị whitelist persist nguyên khối 1 mảng time-series không giới hạn (vi phạm Playbook §4.2).

**Phát hiện quan trọng ảnh hưởng risk**: `redux/baby` không chỉ là slice riêng của KidGrow — grep xác nhận 140 file import `redux/baby/selector`, 55 dispatch site, trải khắp ~20 app family khác (PetCare, 5 app workout đo cơ thể, WaterTracker, Habits, BloodPressure, BloodSugar, Medicine, SkinCare, Pregnancy, Couple...). Mọi app đó build riêng (không chia sẻ dữ liệu runtime) nhưng chia sẻ y nguyên code này. Quyết định: tách kiến trúc lưu trữ đứng sau công tắc `isKidGrowApp` — chỉ KidGrow dùng đường mới ngay, việc bật cho 20 app còn lại là quyết định/đợt việc riêng sau, cần hồi quy riêng.

## Bảng tính năng cuối cùng (sau bước tự phản biện)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|
| Lõi (gate Premium) | WHO Growth Percentile Engine — percentile cân nặng/chiều cao/vòng đầu theo tuổi+giới tính (P3/15/50/85/97, LMS chuẩn WHO), lịch sử percentile theo thời gian | Qua đủ 4/4 bài kiểm tra sắc bén (Playbook §9.1) |
| Mồi (free, <30s) | Percentile hiện tại + đường P50 làm teaser ngay lần đo đầu; giải thích "Percentile là gì?" | |
| Hỗ trợ | Nhắc lịch ăn theo khung giờ cấu hình được | Tái dùng `redux/notification` |
| Hỗ trợ | Nhắc lịch tiêm chủng theo lịch EPI-WHO | Tái dùng `redux/notification`, mẫu `redux/kept/saga.ts` |
| Hỗ trợ | Chia sẻ ảnh memory qua Share sheet gốc | Không backend |
| Hỗ trợ | iCloud sync (marketing Premium, không code-gate) | Theo Playbook §6.3 |
| **Cắt khỏi phạm vi** | Phát hiện bất thường tiêu hoá | Không có cơ sở lâm sàng, rủi ro y tế/pháp lý |
| **Cắt khỏi phạm vi** | Chia sẻ nhiều người dùng thật (ghép thiết bị) | Cần hạ tầng ngoài phạm vi no-backend |

## Data model
```ts
// types/baby.ts — additive only
interface BabyActivity { /* ...existing... */ updatedAt?: string; }
interface UserProfile { /* ...existing... */ updatedAt?: string; }
interface Memory { /* ...existing... */ updatedAt?: string; }

type BabyPlanTier = 'free' | 'premium';
interface BabySettings {
  planTier: BabyPlanTier;
  feedingReminderEnabled: boolean;
  feedingIntervalHours: number;
  feedingWindowStart: string; // 'HH:mm'
  feedingWindowEnd: string;
  vaccinationReminderEnabled: boolean;
}

// common/baby/whoGrowthData.ts — 0 import, nguồn: WHO Child Growth Standards
type GrowthMetric = 'weight' | 'height' | 'head';
type BabySex = 'male' | 'female';
interface LmsRow { month: number; l: number; m: number; s: number; }
// WHO_LMS: Record<GrowthMetric, Record<BabySex, LmsRow[]>>; 61 tháng x 3 metric x 2 giới
```

## Kiến trúc kỹ thuật
- **Redux slice**: `src/redux/baby/` (5 file hiện có) + file mới `historyReducer.ts` (mirror `redux/migraine/historyReducer.ts`) + `migrationHelpers.ts` (pure, test được không cần mock).
- **Storage strategy**: `baby` reducer (bounded: profiles, settings, lastActivity, galleryMemories) tiếp tục whitelist persist; `babyHistory` reducer (activities time-series) KHÔNG whitelist, rehydrate từ file sharded theo tháng `BABY_ACTIVITY_LOGS_<YYYY-MM>` qua `utils/storage.ts`. Migrate 1 lần dữ liệu cũ từ `state.baby.activities` sang sharded files, guard bởi flag `activitiesMigratedAt` persist được (idempotent, an toàn khi lỗi giữa chừng).
- **Công tắc rollout**: `USE_BABY_HISTORY_STORE = isKidGrowApp` trong `redux/baby/selector.ts` + `saga.ts` — chỉ KidGrow đi qua đường mới, 20 app family khác giữ nguyên hành vi cũ 100%.
- **Business logic engine (tính năng lõi)**: `common/baby/whoGrowthCalculator.ts` — pure, không import barrel `common/index.js` (theo pattern `cloudSyncMerge.ts`/`glucoseLevels.ts`, Playbook §6.11). Công thức LMS chuẩn WHO + xử lý vùng cực trị |z|>3 + percentile qua xấp xỉ Zelen & Severo. Test: `__tests__/whoGrowth.test.ts` đối chiếu trực tiếp bảng WHO gốc tại các mốc biên.
- **Nhắc lịch**: tái dùng `redux/notification` có sẵn, không xây native mới. Mẫu tham chiếu: `redux/kept/saga.ts` (nhắc bảo hành theo ngày, "huỷ rồi tạo lại").
- **iCloud sync**: wrapper mỏng `services/babyICloudSync.ts` + `hooks/useBabyAutoSync.ts` (clone Migraine), dựa trên core dùng chung `cloudSync.ts`/`useAutoCloudSync.ts` — không đụng core.

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|
| `KidGrowHome` | Gỡ tàn dư Pregnancy (PeriodSymptoms), mount auto-sync | — |
| `BabyHeight`/`BabyWeight`/`BabyHeadSize` | Thêm id/unit khi log + card percentile | — |
| `BabyGrowthChartScreen` (mới) | Full WHO growth chart, route mới | `WhoGrowthChart` (SVG, mới) |
| `BabyVaccinationDetail` | Khối "sắp đến hạn" + toggle nhắc | `redux/kept/saga.ts` |
| `BabyUpgradePremiumScreen` (mới) | Placeholder tĩnh | `Migraine/UpgradePremiumScreen` |
| `HomeSettingScreen/KidGrowMenu.js` | Mục cài đặt nhắc ăn + Premium | — |

## Monetization
Free: unlimited logging/charts, percentile hiện tại + đường P50, nhắc lịch, iCloud sync (marketing thôi, không gate code). Premium (placeholder, chưa IAP thật): lịch sử percentile theo thời gian + đủ 5 đường P3-P97. Không gate số lượng bản ghi/lịch sử log (tránh lặp lỗi Migraine).

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Bật iCloud capability riêng cho target `com.careai.baby` qua Xcode UI (không đụng entitlements dùng chung) — code đã có fallback graceful nếu chưa bật.
- WHO LMS data cần lấy từ bảng công khai chính thức WHO lúc build (việc thật, ghi rõ nguồn+ngày lấy trong code).
- Việc bật `USE_BABY_HISTORY_STORE` cho 20 app family còn lại là quyết định/đợt việc riêng, ngoài phạm vi lần này.

## Build order
1. M1 — Bug fix nền tảng (id/updatedAt, unit, birthday, console.log, gỡ PeriodSymptoms)
2. M2 — Tách kiến trúc lưu trữ + migrate (đứng sau công tắc isKidGrowApp)
3. M3 — WHO Growth Percentile Engine
4. M4 — Nhắc lịch ăn/tiêm chủng
5. M5 — iCloud sync + màn Premium
6. Cập nhật `app-asset/description/baby.md`

## Verification đã thực hiện (M1-M3, 2026-08-03)
- `npx tsc --noEmit -p tsconfig.json`: 1077 lỗi — đúng bằng baseline trước khi sửa (đã xác nhận qua `git stash`), 0 lỗi mới trong toàn bộ file đã đụng.
- `npx jest`: **167/167 test pass** (1 suite `App.test.tsx` fail do lỗi import `react-redux` ESM có sẵn từ trước, xác nhận qua `git stash` — không liên quan thay đổi này).
  - `babyActions.test.ts` 5/5 — id/updatedAt tự sinh đúng.
  - `babyHistoryMigration.test.ts` 8/8 — pure helper group-by-month/dedupe/id tất định.
  - `babySagaMigration.test.ts` 4/4 — sequencing migrate thật (skip khi đã migrate, migrate khi rỗng, migrate khi có data, không đánh dấu migrated nếu ghi lỗi).
  - `whoGrowth.test.ts` 21/21 — đối chiếu z=0↔M tại nhiều mốc, round-trip valueAtZ/zScore, percentileFromZ tại các mốc chuẩn, classify tại đúng biên, unit conversion, ageInDays.
- `git diff --stat`: 25 file sửa + 12 file mới, toàn bộ nằm trong `redux/baby/**`, `app/containers/Baby/**`, `app/components/{Baby*,GrowthPercentileCard,WhoGrowthChart}/**`, `app/common/baby/**`, `app/types/baby.ts`, `app/utils/{storage,utils,uuid}.ts`, `app/navigation/{index.js,constants.js}` (chỉ thêm route), `redux/{rootReducer,store}.ts` + `AppInit.tsx` (chỉ thêm dòng). Không đụng file ngoài phạm vi.
- Dữ liệu WHO LMS: lấy qua `curl` trực tiếp từ `github.com/WorldHealthOrganization/anthro` (repo GitHub chính thức của WHO), không qua AI tóm tắt — đối chiếu khớp 3 mốc số liệu WHO công khai đã biết trước (3.3464kg cân nặng sơ sinh bé trai, 9.646kg lúc 12 tháng, 75.7391cm chiều cao lúc 12 tháng).

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-03 | (phát hiện lúc khảo sát, chưa phải lỗi tự gây ra) `redux/baby` dùng chung bởi ~20 app family, ước tính ban đầu chỉ "PetCare + 5 app workout" khi hỏi user — thực tế lớn hơn 3-4 lần | Chưa grep xác nhận số liệu trước khi trình bày phạm vi rủi ro cho user | Grep xác nhận 140 file/55 dispatch site trước khi chốt plan, thêm công tắc rollout `isKidGrowApp` để giảm rủi ro thay vì áp dụng ngay cho tất cả | Không cần — đã là bài học áp dụng ngay trong plan này |
| 2026-08-03 | Thiết kế saga ban đầu gate `if (!isKidGrowApp) return` NGAY TRONG từng saga function — tự phát hiện lúc viết test rằng cách này khiến không thể test độc lập logic migrate (vì `isKidGrowApp` resolve theo bundle id thật của máy chạy Jest, không phải KidGrow) | Đặt điều kiện rẽ nhánh lẫn vào logic nghiệp vụ thay vì tách riêng ở nơi wiring | Refactor: gate CHỈ nằm ở `watchBaby()` (nơi đăng ký watcher), các saga function xuất ra (`export function*`) không tự kiểm tra `isKidGrowApp` — vừa sạch hơn vừa test được trực tiếp | Có — quy tắc chung: khi 1 flag quyết định "có chạy nhánh logic không", đặt gate ở nơi wiring/đăng ký, không lặp lại bên trong từng hàm logic, để mỗi hàm logic test được độc lập không cần mock flag đó |
| 2026-08-03 | Suýt hardcode `unit: 'cm'`/`unit: 'kg'` khi thêm field unit còn thiếu ở `BabyHeight`/`BabyWeight`/`BabyHeightChart` — tự phát hiện khi thấy các màn này hiển thị giá trị kèm `heightUnit`/`weightUnit` (có thể là inch/lb tuỳ cài đặt người dùng), hardcode sẽ ghi sai nhãn đơn vị cho dữ liệu thật | Sửa nhanh theo bề mặt (giá trị trông "hợp lý" là cm/kg) mà không kiểm tra UI có cho chọn đơn vị khác không | Dùng đúng `heightUnit`/`weightUnit` từ `redux/fasting/selector` (đúng đơn vị người dùng đã chọn khi nhập), engine WHO tự convert cm/m/inch và kg/lb, trả `null` nếu đơn vị lạ thay vì đoán | Không cần — đã là bài học áp dụng ngay, tương tự tinh thần Playbook §9.2 "không đoán giá trị ảnh hưởng số liệu hiển thị" |
| 2026-08-03 | `redux/baby/selector.ts` (và giờ cả `saga.ts`) không test được dưới Jest vì import `common/baby/KidGrow.ts` → import barrel `common/index.js` → `reactotron-react-native` → `XMLHttpRequest is not defined` — lỗi có sẵn từ trước (không phải do session này gây ra), chỉ lộ ra khi viết test cho saga mới | File `KidGrow.ts` trộn lẫn hằng số thuần (Activity* type strings) với import UI/Images ngay đầu file | Tách các hằng số `Activity*` sang file mới `common/baby/babyActivityTypes.ts` (0 import), `KidGrow.ts` re-export lại (`export * from './babyActivityTypes'`) để không đổi API cũ, `redux/baby/selector.ts` import thẳng từ file mới | Không cần — đúng pattern đã ghi ở Playbook §6.11 (giống `cloudSyncMerge.ts`/`glucoseLevels.ts`), áp dụng thêm 1 lần nữa |
