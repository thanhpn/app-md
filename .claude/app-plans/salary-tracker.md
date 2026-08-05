# Salary Tracker — Plan

## Trạng thái
- Bundle ID: `com.careai.salary.tracker`
- App đã build (1 commit `b2104c7`, ngoài quy trình Playbook, chưa từng có file plan) trước khi file này được tạo.
- Ngày tạo file plan: 2026-08-03
- Trạng thái: `Đang cải tiến` — vòng 1: Tier 0 (nền tảng) + Tier 1 (tự động hoá) xong. Vòng 2 (2026-08-03): badge so sánh tháng + "Quyết toán thuế TNCN" xong. Vòng 3 (2026-08-04): chấm công chuyên nghiệp — ảnh + GPS + calendar + xuất thẻ ảnh cho HR — xong. Vòng 4 (2026-08-05): onboarding lần đầu + streak chấm công liên tục — xem mục "Vòng 4" bên dưới. Tier 2 đầy đủ (báo cáo năm dạng biểu đồ, CSV backup, gate Premium) và Home Screen Widget (cần native target ngoài RN, không tự làm được) vẫn để sau.

## Context
App chấm công + tính lương, có sẵn engine tính Net/Gross khá đầy đủ (OT 3 mức, thuế VN/flat/custom, thưởng, phép năm). Người dùng yêu cầu tiếp tục phát triển: nghiên cứu thêm tính năng người dùng mong muốn, tự động hoá xử lý/tính toán cho thuận tiện nhất. Research + tự phản biện + chốt với người dùng qua `AskUserQuestion`, 3 quyết định lớn:
1. Tự động nhận diện ngày Lễ **chỉ** dương lịch cố định (Tết/Giỗ Tổ là âm lịch, cần bảng bảo trì hàng năm — người dùng chọn bỏ qua).
2. Tier 2 (báo cáo năm/xuất bảng lương/CSV backup) → gate Premium (placeholder tĩnh, mẫu `Rental/UpgradePremiumScreen`), nhưng để sau.
3. Vòng này chỉ Tier 0 + Tier 1.

Trong lúc research phát hiện 2 vấn đề kỹ thuật cần sửa trước tính năng mới:
- Bug: `LeaveConfig.year` không tự cập nhật → từ 1/1 năm sau, "phép còn lại" tính sai vĩnh viễn.
- Vi phạm Playbook §4.2: `attendance` (time-series, tăng vô hạn) nằm chung reducer whitelist persist với `config` (state nhỏ).
- Vi phạm Playbook §2: chưa có theme riêng, fallback theme mặc định.

## Bảng tính năng (đã qua tự phản biện + sharpness test §9.1)

| Tier | Chức năng | Ghi chú |
|---|---|---|
| 0 | Sửa bug `LeaveConfig.year` (auto-rollover) | Bug thật, không phải feature |
| 0 | Tách `attendance` khỏi reducer persist, shard theo tháng | Playbook §4.2, retrofit an toàn theo mẫu `baby/saga.ts` |
| 0 | Theme riêng (navy + gold) | Playbook §2 |
| 1 | Tự nhận diện ngày Lễ dương lịch cố định (4 ngày) | Sửa lỗi con người quên toggle → tính sai OT = mất tiền thật |
| 1 | Nhắc "quên chấm công ra" | Tái dùng `notification.ts` có sẵn |
| 1 | Đồng hồ "tiền đang chảy vào túi" real-time | Mồi feature, dùng ngay <30s |
| 1 | Nhắc ngày trả lương (cấu hình `payday`) | Reminder chung chung, không chèn số dự báo (tránh lệch) |
| 1 | So sánh lương Net tháng này/tháng trước (badge +/-X% trên Dashboard) | Rẻ, tận dụng dữ liệu sẵn có, không cần màn hình riêng |
| 1 | Ước tính quyết toán thuế TNCN cuối năm (`taxProfile === 'vn'`) | Nhu cầu thật thị trường VN, tái dùng đúng công thức `computeMonthNet` đã kiểm chứng, không tạo nguồn thuế thứ 2 |
| 2 (sau) | Báo cáo thu nhập năm dạng biểu đồ, xuất bảng lương, CSV backup | Gate Premium placeholder |
| Cắt | Lịch ca làm cố định, nhiều nguồn thu nhập | Scope creep, để sau nếu cần |

## Data model
```ts
// constant.ts — thêm
interface AttendanceRecord { /* ... */ updatedAt: string }
interface LeaveRecord { /* ... */ updatedAt: string }
interface BonusRecord { /* ... */ updatedAt: string }
interface SalaryConfig { /* ... */ payday: number } // 1-28, clamp ở UI
const VN_FIXED_HOLIDAYS: string[] = ['01-01', '04-30', '05-01', '09-02']; // MM-DD, Điều 112 BLLĐ, không gồm Tết/Giỗ Tổ (âm lịch)

// redux/salary/historyReducer.ts — mới, KHÔNG whitelist
interface SalaryHistoryState {
  allAttendance: AttendanceRecord[];
  isHistoryLoaded: boolean;
  isHistoryLoading: boolean;
}

// redux/salary/reducer.ts — giữ nguyên `attendance` (không xoá field, xem lý do migration bên dưới)
interface SalaryState {
  /* ...existing... */
  attendanceMigratedAt: string | null;
}
```

## Kiến trúc kỹ thuật

**Retrofit tách attendance** (mirror chính xác `src/redux/baby/saga.ts` + `reducer.ts` — Baby app đã làm y hệt việc này sau khi ship, khác Kept/Migraine vốn tách từ đầu):
- KHÔNG xoá field `attendance` khỏi `SalaryState` (giữ type-safe lúc rehydrate). Thêm `attendanceMigratedAt: string | null`.
- 4 case `CHECK_OUT`/`ADD_ATTENDANCE`/`UPDATE_ATTENDANCE`/`DELETE_ATTENDANCE` guard `if (state.attendanceMigratedAt) return state;` → no-op vĩnh viễn sau migrate, đồng thời là lưới an toàn nếu migration lỗi.
- `saga.ts` (file mới — salary trước đây chưa có saga nào): `migrateLegacyAttendanceIfNeeded()` (mirror `migrateLegacyActivitiesIfNeeded`, baby/saga.ts:69-99) — đọc legacy `attendance`, group theo `localMonthOf(record.date)` (`src/app/common/migraine/dateHelpers.ts`), ghi shard qua `storage.ts` (`readSalaryAttendanceByMonth`/`writeSalaryAttendanceByMonth`/`getAllSalaryAttendanceMonths`, mirror `readKeptUseEventsByMonth` block), set `MARK_ATTENDANCE_MIGRATED` chỉ khi ghi thành công (retry nếu lỗi).
- `ensureHydrated()` + `loadAllHistorySaga()` + `checkOutSaga`/`addAttendanceSaga`/`updateAttendanceSaga`/`deleteAttendanceSaga` (write-through) + `watchSalary()` — mirror `kept/saga.ts`.
- `rootReducer.ts` thêm `salaryHistory`, **không** thêm vào whitelist `store.ts`. `rootSaga.ts` fork `watchSalary()`.
- Mount dispatch `loadAllAttendanceHistory()` ở cả `SalaryDashboardScreen.tsx` và `AttendanceHistoryScreen.tsx` (2 nơi đọc `getAttendance` độc lập).

**Rollover phép năm**: `rolloverLeaveConfigIfNeeded(leaveConfig, leaves, now = dayjs())` trong `salaryCalc.ts` — lặp tăng năm, carry-over cap = `annualDays` hiện tại (tái dùng field có sẵn, không bịa hằng số). Xử lý bằng `useEffect` đồng bộ trong `SalaryDashboardScreen.tsx` (không cần saga, state đã resident).

**Theme**: `salaryTrackerThemes` trong `Theme.js`, copy đầy đủ bộ key như `keptThemes` (không chỉ 6 key tự dùng — chrome dùng chung có thể đọc key khác). Navy + gold, khác tông `walletThemes`.

**Ngày Lễ tự động**: `classifyDayType()` check `VN_FIXED_HOLIDAYS` trước (ưu tiên hơn cuối tuần), fallback logic cũ. Lan toả tự động tới `AttendanceEditModal`/`SalaryDashboardScreen` vì cả 2 đã gọi hàm này.

**So sánh tháng này/tháng trước**: `computeMonthOverMonthDelta(currentNet, previousNet)` (thuần, `salaryCalc.ts`) — trả `null` nếu cả 2 tháng đều 0 (ẩn badge), trả `{label: 'Mới', positive: true}` nếu tháng trước = 0 (tránh chia cho 0), còn lại tính % làm tròn. `SummaryCard` thêm prop `deltaLabel`/`deltaPositive` (badge màu `correctText`/`errorText` theo theme), chỉ gắn vào card Net trên Dashboard — không đụng CSV/report Tier 2.

**Quyết toán thuế TNCN cuối năm**: `computeYearPitFinalization(attendance, bonuses, config, year, now)` (thuần, `salaryCalc.ts`) — cộng dồn `computeMonthGross`/`computeMonthNet` (2 hàm đã có, đã kiểm chứng) qua từng tháng Jan→(tháng hiện tại nếu `year` là năm nay, else Dec), rồi áp bảng thuế **năm** suy ra bằng cách nhân 12 trực tiếp từ `VN_PIT_BRACKETS` (bảng tháng đã có) — không hardcode bảng năm riêng để tránh lệch (Playbook §6.10). Không tự chế logic "tháng nào tính" — dùng đúng công thức tháng hiện có (VD lương tháng luôn tính đủ base dù thiếu chấm công, giống Dashboard đang làm). Màn hình mới `PitFinalizationScreen.tsx` (route `SalaryPitFinalization`, nút trong "Công cụ" ở Dashboard): year switcher, chặn xem năm tương lai; nếu `config.taxProfile !== 'vn'` hiện empty-state có CTA sang Config đổi hồ sơ thuế (không tính thuế mù mờ cho hồ sơ khác).

**Reminder** (tái dùng `src/app/utils/notification.ts`, format `date:'YYYY-MM-DD'`/`time:'HH:mm:ss'`, không phải ISO — mirror style `syncWarrantyNotificationForItem` trong `kept/saga.ts`, cancel-rồi-maybe-tạo-lại):
- Quên check-out: schedule lúc `CHECK_IN` (giờ vào + `standardHoursPerDay`), cancel lúc `CHECK_OUT`/`CANCEL_CHECK_IN`.
- Ngày lương: `syncPaydayReminder(config)` lúc `SET_SALARY_CONFIG` + mount, `repeat:'month'` (lần đầu dùng trong factory — bắt buộc smoke test tay), nội dung chung chung không chèn số dự báo.

**Đồng hồ tiền real-time**: `LiveEarningsTicker.tsx` mirror `CheckInTimer.tsx` (tự `setInterval` riêng), dùng `hourlyRateFromConfig()` có sẵn (đã xác nhận an toàn cả 4 `payType`).

## Danh sách màn hình
Vòng 1: không có màn hình mới. Sửa: `SalaryDashboardScreen` (mount dispatch + rollover + ticker), `AttendanceHistoryScreen` (mount dispatch), `SalaryConfigScreen` (field `payday`), `AttendanceEditModal` (`updatedAt`), `LeaveScreen` (chú thích carry-over cap).

Vòng 2: thêm `PitFinalizationScreen.tsx` (route `SalaryPitFinalization`, mẫu tham khảo: `SalaryCalculatorScreen` cho result card + `AttendanceHistoryScreen` cho pattern switcher). `SummaryCard` thêm badge delta (tuỳ chọn, không phá component cũ).

## Monetization
Không đổi vòng này (không gate gì thêm). Tier 2 (sau) sẽ gate Premium placeholder giống `Rental/UpgradePremiumScreen`.

## Giới hạn đã biết
- `repeat:'month'` chưa từng dùng trong factory — cần smoke test tay kỹ.
- Android `channelId` dùng id của chính notification (kế thừa từ `notification.ts`, không sửa trong plan này).
- Carry-over phép năm bị cắt ở `annualDays` là chủ đích, không phải bug.

## Build order
1. Milestone 1 — Tier 0 (data model + migration + rollover + theme).
2. Milestone 2 — Tier 1 (ngày Lễ tự động + reminder + ticker + payday).
3. Milestone 3 (vòng 2) — badge so sánh tháng + màn quyết toán thuế TNCN.

## Verification đã thực hiện
- Jest: `__tests__/salaryCalc.test.ts` — **21/21 pass**: `rolloverLeaveConfigIfNeeded` (4 case), `classifyDayType` (7 case), `computeMonthOverMonthDelta` (5 case: cả 2 tháng=0 → null, tháng trước=0 → "Mới", tăng/giảm/0%), `computeYearPitFinalization` (5 case, đáng chú ý: case lương cố định cả năm → `diff` đúng bằng 0 tuyệt đối — chứng minh bảng thuế năm suy ra ×12 khớp chính xác với bảng tháng; case thưởng cục bộ 1 tháng → `diff` âm/được hoàn thuế, đúng thực tế thuế luỹ tiến VN; case năm tương lai → 0 tháng tính, không NaN; case hồ sơ thuế không phải 'vn' → không crash). Số liệu test được tính tay trước (bậc thuế, bảo hiểm, giảm trừ) rồi đối chiếu, khớp chính xác (chỉ lệch dấu phẩy động rất nhỏ, dùng `toBeCloseTo`).
- Trong lúc viết test (vòng 1), gặp đúng lỗi đã biết ở Playbook §6.11 (`constant.ts` kéo theo `SelectCurrencyModal` → `react-native-modalbox`, Jest báo `SyntaxError: Cannot use import statement outside a module`) — đã sửa bằng cách tách phần type/constant thuần sang `src/app/containers/SalaryTracker/types.ts` (0 side-effect import), `constant.ts` giờ chỉ còn `export * from './types'` + `getCurrencyFormatByCode`. `salaryCalc.ts` import trực tiếp từ `types.ts`.
- `npx tsc --noEmit -p tsconfig.json`: không có lỗi mới liên quan salary (dự án có baseline lỗi cú pháp cũ ở nơi khác — xem Playbook §6.5). Tự dựng tsconfig cách ly tạm thời (loại trừ file lỗi cú pháp đã biết) để kiểm tra ngữ nghĩa thật ở cả 2 vòng — vòng 1 so sánh bằng `git stash` (baseline 7773 dòng lỗi → sau đổi 7782, chênh lệch toàn bộ là `TS7016` đã có sẵn); vòng 2 diff trực tiếp danh sách lỗi trước/sau bằng `diff`, xác nhận chỉ thêm đúng 2 dòng `TS7016` cùng loại cho `PitFinalizationScreen.tsx` (thiếu `@types` cho Ionicons/barrel `common`, y hệt mọi màn hình khác), không có lỗi mới nào khác. File tsconfig tạm đã xoá sau khi verify xong ở cả 2 vòng.
- `git diff --stat` (chỉ phạm vi salary): vòng 1 17 file, vòng 2 thêm 15 file (đè lên nhau 1 phần) — không đụng file ngoài phạm vi ở cả 2 vòng. **Lưu ý minh bạch**: working tree của `CareAi` có sẵn 1 thay đổi KHÔNG liên quan (xoá `src/app/containers/Calculator/*`, thêm `src/app/containers/BodySizeDetailScreen/Calculator/`) — đã tồn tại trong working tree TRƯỚC vòng 1, không phải do plan này gây ra.
- **Chưa làm được** (cần thiết bị/simulator thật, không tự động hoá được): smoke test notification (quên check-out, payday `repeat:'month'`), thử ticker tiền với cả 4 `payType`, xác nhận migration không mất dữ liệu chấm công cũ, tự bấm qua màn "Quyết toán thuế TNCN" trên simulator để kiểm tra layout/số liệu hiển thị đúng với dữ liệu thật (chỉ mới verify logic tính toán qua Jest, chưa tự mắt xem UI).

---

## Vòng 3 (2026-08-04) — Chấm công chuyên nghiệp: ảnh + GPS + calendar + xuất HR

**Context**: người dùng muốn chấm công kèm ảnh+GPS+giờ như app chuyên nghiệp, log đúng ngày để gửi HR, xem qua calendar tháng. Research xác nhận mọi năng lực cần (camera `react-native-vision-camera`, GPS `@react-native-community/geolocation`, lưu file `react-native-fs`, composite+share `react-native-view-shot`+`react-native-share`, calendar `react-native-calendars`) đã có sẵn trong factory, mirror trực tiếp từ `GeoStampCameraScreen`/`Calendar/MonthViewScreen`/`PetIdCardScreen` — không thêm dependency mới. Chốt qua `AskUserQuestion`: capture tùy chọn mặc định bật; **không gate Premium** (gate kiểu factory = khóa cứng thật tới khi có IAP, không phù hợp vì người dùng muốn tự dùng ngay); xuất "thẻ ảnh từng ngày" trước; làm cả 3 phần trong 1 plan nhiều milestone.

**Quyết định kỹ thuật quan trọng** (đã qua 1 vòng Plan agent stress-test trước khi code):
- `AttendanceProof {photoPath, latitude?, longitude?, address?, capturedAt}` — lat/lng optional vì GPS fail độc lập với quyền camera.
- `capturedAt` (giờ thật lúc chụp) ghi đè giờ chấm công chính thức khi chụp thành công — giờ bấm nút chỉ là fallback khi bấm "Bỏ qua" (tránh giờ trên ảnh và giờ tính lương lệch nhau, nhìn như bug).
- Chuyển proof từ màn camera về Dashboard qua field tạm trong `salary` reducer (`pendingCheckOutProof`), KHÔNG dùng nav-params-back (không có tiền lệ trong codebase — Plan agent xác nhận, dùng lại đúng cơ chế `activeCheckIn` đã có).
- `GeoStampOverlay.tsx` (dùng chung với app khác) chỉ sửa cộng thêm 2 điểm (prop `brandLabel` có default giữ nguyên, fallback text khi `editable=false`) — không fork.
- `AttendanceEditModal.handleSave` không spread `record` prop → phải tường minh giữ `checkInProof`/`checkOutProof` khi lưu, nếu không mất ảnh mỗi lần lưu.
- `deleteAttendanceSaga` phải dọn file ảnh mồ côi qua `deleteFile` (`src/app/utils/file.ts`, có sẵn) khi xoá record.
- Camera-only, KHÔNG cho chọn ảnh từ thư viện (giữ tính "bằng chứng" — ảnh cũ có thể giả mạo).

**Milestone**: 1) data model + màn chụp `AttendanceProofCameraScreen` + wiring check-in/out + dọn file mồ côi; 2) toggle List/Calendar vào `AttendanceHistoryScreen` (`classifyAttendanceDayStatus` mới trong `salaryCalc.ts`); 3) `AttendanceDayShareCard` xuất thẻ ảnh cho HR (mirror `PetIdCardScreen`).

Plan chi tiết đầy đủ (kiến trúc từng phần, route/redux exact edit points) — xem lịch sử session.

**Verification đã thực hiện**:
- Jest `__tests__/salaryCalc.test.ts`: **26/26 pass** (thêm 5 test cho `classifyAttendanceDayStatus`: rỗng→none, chỉ checkIn→partial, đủ cả 2→complete, nhiều record cùng ngày ưu tiên complete, record không có checkIn/checkOut nào→none).
- `npx tsc --noEmit` isolated-check: **lưu ý quan trọng** — trong lúc làm vòng này, phát hiện có 1 phiên làm việc/tiến trình KHÁC đang đồng thời sửa đổi cùng working tree (tính năng "Calendar" — nhắc lịch/thời tiết/todo, hoàn toàn không liên quan, đụng `src/redux/calendar/*`, `navigation/*`, `package.json`) khiến việc so sánh baseline bằng `git stash` không an toàn (thử 1 lần bị lỗi "not uptodate", đã dừng ngay không ép buộc). Chuyển sang verify bằng cách `grep` lỗi tsc theo ĐÚNG từng đường dẫn file mình sửa — toàn bộ chỉ còn lỗi `TS7016` baseline đã biết (thiếu `@types` cho Ionicons/barrel `common`, giống mọi file khác), không có lỗi mới nào của riêng mình, kể cả 2 file mới (`AttendanceProofCameraScreen.tsx`, `AttendanceDayShareCard.tsx`).
- `git diff --stat` scoped đúng path salary/GeoStamp/test: 16 file sửa + 2 file mới, đúng phạm vi plan, không đụng file của tiến trình Calendar đang chạy song song.
- **Chưa làm được** (cần thiết bị thật — camera/GPS/permission/share sheet không giả lập được): toàn bộ luồng chụp ảnh check-in/out thật, xác nhận file ảnh lưu đúng thư mục và bị xoá khi huỷ check-in/xoá record, chạm ngày trên calendar mở đúng bottom sheet, bấm "Chia sẻ cho HR" ra đúng ảnh thẻ.

---

## Vòng 4 (2026-08-05) — Onboarding lần đầu + streak chấm công liên tục

**Context**: người dùng muốn phát triển thêm tính năng "cao cấp" để tăng ưu tiên cài đặt/giữ chân người dùng. Research trước: factory KHÔNG có sẵn thư viện rating-prompt/quick-actions/widget, và `isSalaryTrackerApp` chưa wire vào `getAppId()` (app chưa publish) → loại bỏ ngay ý tưởng nút đánh giá/link chia sẻ App Store (link sẽ chết). Home Screen Widget/Quick Actions cần thêm native target ngoài RN (Playbook §6.1 cấm tự sửa pbxproj) — đã hỏi và người dùng chọn **bỏ qua vòng này**, không chuẩn bị data layer trước. Còn lại 3 đề xuất, người dùng chọn 2: onboarding + streak (bỏ hoàn thiện Tier 2).

**Quyết định kỹ thuật**:
- `SalaryConfig` thêm `hasOnboarded: boolean` (default `false`). `SalaryTracker/index.tsx` gate: nếu chưa onboard, render thẳng `OnboardingScreen` (không qua `Stack.Navigator`, vì đây là luồng tuyến tính không cần back-navigation) thay vì Dashboard; xong thì dispatch `setSalaryConfig({...hasOnboarded:true})`, component tự re-render vào Stack bình thường.
- Onboarding 3 bước (hình thức lương → lương cơ bản → hồ sơ thuế) — export `PAY_TYPE_LABEL`/`TAX_PROFILE_LABEL` từ `SalaryConfigScreen.tsx` (trước đó local) để dùng chung, tránh 2 nguồn nhãn có thể lệch nhau.
- Streak: đặt tên lại là **"chuỗi ngày chấm công liên tục"** (đo tính đều đặn — có đủ checkIn+checkOut mỗi ngày làm việc), KHÔNG dùng chữ "đúng giờ" như đề xuất ban đầu — vì `SalaryConfig` không có khái niệm "giờ vào ca chuẩn" để so sánh trễ/đúng giờ, gắn nhãn "đúng giờ" sẽ sai với thứ thực sự đo được (tự sửa lại cho trung thực, không hỏi lại vì không phải quyết định lớn).
- `computeAttendanceStreak`: bỏ qua cuối tuần/Lễ (không phá chuỗi, không tính), hôm nay chưa xong ca không phá chuỗi (chỉ không tính), 1 ngày làm việc TRONG QUÁ KHỨ bị bỏ lỡ thì chuỗi dừng ngay tại đó. Vòng lặp bounded (10 năm) để không bao giờ treo.

**Files**: `types.ts` (field mới), `salaryCalc.ts` (`computeAttendanceStreak`), `screens/OnboardingScreen.tsx` (mới), `index.tsx` (gate), `components/AttendanceStreakBanner.tsx` (mới, mirror phong cách `DiaryStreak` có sẵn trong factory nhưng tính streak đúng thay vì cửa sổ 7 ngày cố định), `SalaryDashboardScreen.tsx` (render banner), `SalaryConfigScreen.tsx` (export 2 label map).

**Verification đã thực hiện**:
- Jest: **31/31 pass** (thêm 5 test cho `computeAttendanceStreak`: 0 record, chuỗi đủ tuần bỏ qua cuối tuần không phá, hôm nay dang dở không phá chuỗi, thiếu 1 ngày làm việc trong quá khứ thì dừng chuỗi ngay, bỏ qua đúng 1 ngày Lễ cố định giống cuối tuần). Ngày thứ trong tuần dùng để dựng test đã xác nhận bằng lệnh `date` thật trước khi viết, không đoán.
- `npx tsc --noEmit` isolated-check, lọc theo đúng path từng file đã sửa (vẫn có tiến trình Calendar khác chạy song song trong repo) — chỉ còn lỗi `TS7016` baseline đã biết, không có lỗi mới, kể cả 2 file mới (`OnboardingScreen.tsx`, `AttendanceStreakBanner.tsx`).
- `git diff --stat` scoped: 6 file sửa + 2 file mới, đúng phạm vi.
- **Chưa làm được** (cần thiết bị/simulator thật): tự bấm qua luồng onboarding 3 bước, xác nhận banner streak hiện đúng/ẩn đúng khi chưa có dữ liệu, xác nhận banner không hiện khi streak=0 và 7 ngày gần nhất không có complete nào.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-03 | App được build (`b2104c7`) hoàn toàn ngoài quy trình Playbook: không plan file, `attendance` (time-series) whitelist chung reducer nhỏ (vi phạm §4.2), không có theme riêng (vi phạm §2), `LeaveConfig.year` không rollover (bug thật) | Xây 1-shot, không qua bước tự phản biện/plan trước khi code | Retrofit theo plan này (Tier 0) | Không cần thêm quy tắc mới — đã có sẵn §4.2/§2, chỉ là ví dụ thực tế của việc bỏ qua quy trình |
