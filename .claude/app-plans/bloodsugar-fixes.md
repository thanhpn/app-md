# BloodSugar (AuraTune/CareAi family) — Fix công thức/cảnh báo/thống kê — Plan

> App con dùng module `redux/baby` + `BabyActivity` dùng chung. Áp dụng khuôn `_TEMPLATE.md` có lược phần market analysis (đây là fix + nâng cấp app đã xây, không phải app mới).

## Trạng thái
- Ngày bắt đầu: 2026-08-01
- Trạng thái: Đang xây

## Context
Review theo yêu cầu người dùng phát hiện 4 lỗi nghiêm trọng trong engine phân loại đường huyết (`src/app/common/bloodSugar/Data.ts`) và cách nó được dùng ở `BloodSugarGauge`/`BloodGlucoseAddNewScreen`: sai biên phân loại (off-by-one so với ADA), thiếu hẳn cảnh báo hạ đường huyết cho mọi lần đo sau ăn, gauge chính hiện cảnh báo sai khi chưa có dữ liệu, giá trị mặc định khi thêm bản ghi mới nằm trong vùng nguy hiểm. Đã duyệt sửa hết + thêm Time in Range (TIR) — chỉ số chuẩn ATTD/ADA hiện đại thay thế cách chỉ nhìn trung bình cộng.

**Bằng chứng chính**: `GlucoseTable` (bảng tra cứu tĩnh) ghi đúng ranh giới ADA — dùng làm nguồn đối chiếu xác nhận `BloodSugarLevelsByState` (engine thật) bị lệch 1 đơn vị.

## Data model
Không có type mới ngoài kiểu trả về của `computeTimeInRange`: `{veryLow, low, inRange, high, veryHigh, totalCount}` (percentages + count), định nghĩa trong `Data.ts`.

## Kiến trúc kỹ thuật — xem chi tiết đầy đủ ở plan đã duyệt (hội thoại 2026-08-01), tóm tắt:
1. `Data.ts`: sửa biên `BeforeBreakfast.normal→[70,99]`, `diabetes→[126,199]`; `AfterBreakfast.normal→[70,139]` + thêm tier `low:[0,69]`. Thêm `GenericGlucoseRanges` (veryLow<54, low 54-69, normal 70-180, high 181-250, veryHigh>250) + `getGenericGlucoseLevel(mgValue)` + `computeTimeInRange(readings)`. Sửa `convertBloodSugar` hệ số 18→18.0182.
2. `BloodSugarGauge` + `BloodSugarHome`: guard "chưa có dữ liệu" (không chấm điểm khi `bloodSugar<=0`), dùng `getGenericGlucoseLevel` thay vì ép `'BeforeBreakfast'` cho số trung bình trộn lẫn trước/sau ăn.
3. `BloodGlucoseAddNewScreen`: default glucose an toàn theo unit (`90`/`5.0`), ruler mmol/L range `1.1–33.3`, chặn hba1c nhập vào `[3,20]`.
4. `BloodSugarHbA1cChart`: `parseInt`→`parseFloat`, lọc NaN.
5. `GlucoseTable`: thêm dòng hypoglycemia vào `postMealLevels`.
6. Mới: `BloodSugarTimeInRangeCard` (component) — mount vào `BloodSugarAnalyticScreen`.

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Không tự chạy app để xem UI thật — chỉ verify bằng Jest test + đọc code.

## Build order
1. `Data.ts` (biên + generic ranges + TIR + hệ số quy đổi).
2. `BloodSugarGauge` + `BloodSugarHome`.
3. `BloodGlucoseAddNewScreen`.
4. `BloodSugarHbA1cChart` + `GlucoseTable`.
5. `BloodSugarTimeInRangeCard` mới + mount vào `BloodSugarAnalyticScreen`.
6. Jest test + `tsc` + `git diff --stat`.

## Verification đã thực hiện
- **Jest**: `npx jest bloodSugarData.test.ts` — 16/16 test pass thật, gồm test hồi quy cho đúng từng bug đã sửa (99 vs 100 mg/dL, 139 vs 140 mg/dL, 199/200 không trùng biên, 65 mg/dL sau ăn trả về `low` thay vì `null`, hệ số quy đổi chính xác 18.0182, `computeTimeInRange` bucket đúng %).
- Logic phân loại/quy đổi được tách sang file thuần `glucoseLevels.ts` (0 import) vì import `Data.ts` gốc kéo theo `reactotron-react-native` qua chuỗi `bloodPressure/Data → baby/KidGrow → common/index.js`, khiến Jest lỗi `XMLHttpRequest is not defined` — phát hiện thật khi chạy, không phải suy đoán. `Data.ts` `export *` lại từ file này nên mọi nơi import cũ (`BloodSugarGauge`, `BloodSugarStateCard`, `GlucoseTable`...) không cần sửa gì.
- `tsc --noEmit`: 0 lỗi mới ở mọi file đã sửa/tạo — lỗi baseline có sẵn (1077 dòng, file `.js` Flow-annotation) không đổi số lượng.
- `git diff --stat`: đúng phạm vi kế hoạch. Không đụng `project.pbxproj`/`Podfile.lock`/scheme files — đang có thay đổi dở dang song song từ phiên làm việc khác của bạn (có vẻ đang chạy `pod install`), đã cẩn thận chỉ stage đúng file BloodSugar.
- **Chưa test được**: hiển thị UI thật (Gauge, TimeInRangeCard, ruler picker) trên simulator/thiết bị — chỉ verify được bằng test + đọc lại code.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-01 | Ngưỡng phân loại đường huyết lệch 1 đơn vị so với ADA (100/140/200 thay vì 99/139/199); thiếu tier hạ đường huyết cho mọi trạng thái sau ăn | Off-by-one khi code hoá bảng ngưỡng — bảng tra cứu tĩnh `GlucoseTable` ghi đúng nhưng logic thật `BloodSugarLevelsByState` lệch, không đối chiếu chéo lúc viết | Sửa lại đúng biên ADA, thêm tier `low` cho mọi trạng thái sau ăn | Có — sẽ cân nhắc thêm rule chung "khi có bảng ngưỡng y tế, đối chiếu với nguồn chuẩn + bảng tra cứu tĩnh nếu có sẵn trong cùng app" |
| 2026-08-01 | Giá trị mặc định glucose khi thêm bản ghi mới (`'60'`) nằm trong vùng hạ đường huyết, và không phụ thuộc đơn vị đang chọn | Chọn số mặc định không đối chiếu với chính bảng ngưỡng của app | Đổi thành mặc định theo đúng unit, nằm giữa vùng Normal (90 mg/dL / 5.0 mmol/L) | Chưa — cân nhắc thêm rule "giá trị mặc định cho input y tế không được rơi vào vùng cảnh báo" vào Playbook nếu gặp lại ở app khác |
