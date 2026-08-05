# Quản Lý Nhà Trọ - Thu Tiền Phòng — Plan

## Trạng thái
- Bundle ID: `com.careai.rental.manager`
- Trạng thái: `Đại tu toàn bộ (v2)` — xây lại từ đầu theo tài liệu yêu cầu chức năng 18 module do người dùng cung cấp (chưa build/run thật trên simulator)

## Context
Bản v1 (MVP đầu tiên trong factory thử subscription thật) chỉ tính điện/nước theo đơn giá **cố định**, không có bậc thang — đúng lỗ hổng pháp lý mà tài liệu 18-module (do người dùng cung cấp, dựa trên khó khăn thực tế của chủ trọ + quy định pháp luật hiện hành + tiêu chuẩn thị trường) cảnh báo, và hoàn toàn thiếu module đối soát lãi/lỗ điện nước — điểm khác biệt cốt lõi mà chính tài liệu chỉ ra. Người dùng yêu cầu xây lại toàn bộ, **chỉ cho chủ trọ** (không xây cổng người thuê).

Quyết định kiến trúc lớn (qua `AskUserQuestion`):
- **1 chủ trọ, 1 thiết bị** — không multi-user/phân quyền thật qua nhiều thiết bị. Giữ đúng kiến trúc no-backend đã chứng minh của factory, thay vì đi theo gợi ý Firebase/Supabase của tài liệu (mục 8.1) — đó sẽ là app đầu tiên cần backend trong factory, một quyết định lớn bị từ chối.
- **Xây tại chỗ**, giữ nguyên bundle id (chưa publish, an toàn để thay toàn bộ data model).

## Phạm vi (tự phản biện theo giới hạn thật của factory)

**Tính năng lõi**: **Đối soát điện/nước tổng tòa nhà — Lãi/Lỗ** (module M8 trong tài liệu gốc). Chính tài liệu gọi đây là khác biệt cốt lõi; cũng là phép tính chủ trọ không tự làm được bằng Excel nếu không ghi chỉ số tổng + cộng dồn chỉ số từng phòng — đúng tiêu chí "human không tự thấy được" (mục 9.1 Playbook).

**MVP** (map từ tài liệu, bỏ phần cần backend): M1 (tòa nhà/nhóm phòng, bỏ M1.4 multi-user thật, M1.5 nhân bản cấu hình), M2 (phòng, bỏ M2.6 booking giữ chỗ), M3 (người thuê/CCCD/ở ghép), M4 (hợp đồng/cọc, bỏ M4.3 ký điện tử), M5 (cấu hình bậc thang — input cho M7/M8), M6 (ghi chỉ số **gồm cả chỉ số đồng hồ tổng tòa nhà** — mới hoàn toàn, bỏ M6.6 OCR), M7 (tính hóa đơn theo bậc thang thật), **M8 đầy đủ**, M9 (chi phí sửa chữa/vận hành), M10 (thu tiền thủ công + **VietQR tĩnh**, không đối soát ngân hàng tự động), M11 (công nợ/tuổi nợ), M12 (**chỉ local notification**), M13 (tạm trú), M14 (liên hệ khẩn cấp), M15 (thanh lý/chuyển phòng), M16 (báo cáo, xuất CSV thay Excel), M18 (cài đặt, audit log, backup/restore JSON).

**Hoãn (Phase 2)**: M1.5, M2.6, M4.3, M6.6 (cần ML native module mới), M8.5, M9.6, M12.5, M16.5/M16.7.

**Cắt hẳn, không phải "để sau"**:
- M10.3 (đối soát tự động qua SMS Banking) — iOS không cho app thứ 3 đọc SMS, rào cản kỹ thuật thật, không phải lựa chọn lịch trình.
- M12 kênh Zalo OA/SMS/email — cần backend + API bên thứ 3 trả phí; chỉ còn local push (`createNotification()`, đã dùng ở PetCare/Migraine/Kept).
- M17 (cổng người thuê) — theo yêu cầu rõ của người dùng.
- M18.1 phân quyền thật qua nhiều thiết bị — xem quyết định kiến trúc; chỉ còn ghi chú "ai phụ trách", không phải kiểm soát truy cập thật.
- M18.4 Excel thật — dùng CSV (mở được bằng Excel, không cần thêm thư viện `xlsx`).
- Mã hóa AES thật cho ảnh CCCD — ảnh lưu file local như mọi app khác trong factory, không mã hóa đặc biệt; phải nói rõ trong copy app, không được tuyên bố "đã mã hóa" nếu không làm thật.
- Bảng bậc thang 6 bậc: seed theo cấu trúc tài liệu mô tả, nhưng **không thể tự lấy biểu giá EVN hiện hành thật** — UI Settings phải ghi rõ "tự đối chiếu với hóa đơn điện thật của bạn", không tuyên bố tự động cập nhật.

## Data model
```ts
interface Property { id; name; address; roomGroupIds: string[]; electricityPricingOverrideId?; defaultFees: FeeItem[]; createdAt; updatedAt; }
interface RoomGroup { id; propertyId; name; roomIds: string[]; createdAt; updatedAt; }
interface Room { id; propertyId; roomGroupIds: string[]; name; area?; monthlyRent; status: 'vacant'|'occupied'|'repairing'|'inactive'; assetChecklist?; electricityPricingOverrideId?; fees?; createdAt; updatedAt; }
interface Tenant { id; name; phone; idPhotoFrontUri?; idPhotoBackUri?; emergencyContactName?; emergencyContactPhone?; emergencyContactRelation?; notes?; createdAt; updatedAt; }
interface Contract { id; roomId; primaryTenantId; memberTenantIds: string[]; startDate; endDate?; depositAmount; dueDayOfMonth; lateFeePercentPerDay?; status: 'active'|'ended'; endedAt?; createdAt; updatedAt; }
interface TieredPriceTable { id; name; tiers: {maxKwh; pricePerKwh}[]; updatedAt; }
interface MeterReading { id; roomId; month; previousElectricity; currentElectricity; previousWater; currentWater; electricityPhotoUri?; waterPhotoUri?; createdAt; }
interface BuildingMeterReading { id; propertyId; month; electricityTotalKwh; waterTotalM3; electricityBillAmount; waterBillAmount; createdAt; } // input bắt buộc cho M8
interface Invoice { id; roomId; propertyId; month; rentAmount; electricityUnits; electricityAmount; electricityTierBreakdown: TierBreakdownRow[]; waterUnits; waterAmount; fees; feesTotal; carriedOverDebt; lateFeeAmount; total; dueDate; status; paidAmount; payments: Payment[]; splitMode: 'whole_room'|'even_split'; createdAt; updatedAt; }
interface Payment { id; invoiceId; amount; date; method?; note?; }
interface Expense { id; propertyId; roomId?; category: 'repair'|'operating'; description; amount; payer: 'owner'|'tenant'|'split'; date; photoUri?; createdAt; }
interface TemporaryResidenceRecord { id; tenantId; registeredAt?; expiresAt?; status; attachmentUri?; updatedAt; }
interface AuditLogEntry { id; action; entityType; entityId; note; at; }
interface RentalSettings { defaultTieredPriceTableId; defaultWaterUnitPrice; reminderDaysBeforeDue; tempResidenceReminderDaysBefore; planTier; freeTierPropertyLimit; freeTierRoomLimit; bankAccountForQr?; }
```
`Invoice.electricityTierBreakdown` hiển thị ngay trên hóa đơn — bằng chứng minh bạch cách tính bậc thang (mục 3.2 Playbook), không chỉ đưa ra số cuối cùng.

## Kiến trúc kỹ thuật
- **Áp dụng tách reducer NGAY TỪ ĐẦU** (bài học rút ra chính từ v1, ghi trong changelog dưới — đây là dịp áp dụng): `rentalReducer` (properties/roomGroups/rooms/tenants/contracts/settings/tieredPriceTables, whitelist) + `rentalHistoryReducer` (invoicesByMonth/meterReadingsByMonth/buildingMeterByMonth/expensesByMonth/paymentsByMonth, KHÔNG whitelist, rehydrate từ file tháng).
- Engine cốt lõi `src/app/common/rental/`: `tieredPricing.ts` (tính bậc thang, pure, test), `calculateInvoice.ts` (viết lại, dùng tieredPricing + phí trễ hạn + nợ cộng dồn), `reconciliation.ts` (engine tính năng lõi M8, pure, test), `debtAging.ts` (pure, test), `vietQr.ts` (sinh chuỗi VietQR tĩnh cho `react-native-qrcode-svg` đã có sẵn, không gọi mạng).
- Tái dùng `localDateOf`/`localMonthOf` từ `src/app/common/migraine/dateHelpers.ts`.

## Danh sách màn hình
Giữ khái niệm, viết lại logic: `PropertiesScreen`/`PropertyDetailScreen`/`CreatePropertyScreen`, `RoomDetailScreen`/`CreateRoomScreen`, `InvoiceListScreen`/`InvoiceDetailScreen` (thêm tier breakdown + VietQR), `RecordPaymentScreen`, `RentalSettingsScreen` (thêm editor bảng bậc thang), `UpgradePremiumScreen`.

Mới: `RoomGroupsScreen`/`CreateRoomGroupScreen`, `ContractDetailScreen`/`CreateContractScreen` (thay `AssignTenantScreen` cũ, quản lý ở ghép), `BuildingMeterReadingScreen`, **`ReconciliationScreen`** (màn hình nhà của tính năng lõi, biểu đồ xu hướng qua `react-native-chart-kit`), `ExpensesScreen`/`CreateExpenseScreen`, `DebtScreen`, `TemporaryResidenceScreen`/`CreateTemporaryResidenceScreen`, `TerminationScreen`, `ReportsScreen`, `AuditLogScreen`.

## Bổ sung sau v2: đối soát tài sản bàn giao + quản lý phòng ở ghép (2026-07-27)

Hai lỗ hổng thật phát hiện sau khi v2 chạy: (1) `Room.assetChecklist` có trong type từ đầu nhưng chưa có màn hình nào đọc/ghi — `TerminationScreen` chỉ có 1 số "chi phí sửa chữa" tự do, không có bằng chứng nào phía sau, trong khi tranh chấp tiền cọc là điểm xung đột #1 giữa chủ trọ - người thuê theo chính tài liệu gốc. (2) M2.1 "số người ở tối đa" chưa từng được thêm vào `Room` — không có cách nào biết phòng ở ghép nào đang thiếu người.

**Đã thêm**:
- `Room.maxOccupancy`, `Contract.moveInAssetSnapshot`/`settlementAssetReport`/`moveOutPhotoUri`, type `AssetSettlementItem`.
- `CreateRoomScreen`: editor danh mục tài sản (tên + tình trạng) + trường số người ở tối đa.
- `CreateContractScreen`: tự động snapshot `Room.assetChecklist` vào `Contract.moveInAssetSnapshot` lúc tạo hợp đồng (đóng băng tình trạng lúc vào ở), có preview trước khi lưu.
- `TerminationScreen`: viết lại — đối chiếu từng tài sản (Còn tốt/Hư hỏng/Mất + chi phí riêng từng món) thay vì 1 số tự do, tự cộng vào quyết toán cùng "chi phí khác" và 1 ảnh hiện trạng tổng thể.
- `ContractDetailScreen`: hiển thị lại báo cáo đối chiếu tài sản + ảnh cho hợp đồng đã kết thúc.
- Sức chứa ở ghép tính TỰ ĐỘNG (không lưu cờ riêng, tránh lệch dữ liệu): `1 + memberTenantIds.length` so với `maxOccupancy`. `RoomDetailScreen` hiện badge "Cần tìm thêm N người"; `SharedRoomsScreen` (mới) gom toàn bộ phòng đang thiếu người kèm SĐT người thuê hiện tại (để chủ trọ nhờ giới thiệu) — chỉ tính phòng ĐÃ CÓ người ở nhưng chưa đầy, không tính phòng trống hoàn toàn (đã tự sửa 1 lần trong lúc review). Có quick-action nổi bật trên Home khi có phòng cần tìm người.

## Bổ sung: chi phí tổng hợp + ước tính thuế + bảng cân đối lãi/lỗ (2026-07-27)

Yêu cầu: chủ trọ cần thấy tổng chi phí (theo tòa nhà/phòng/chi phí chung), ước tính thuế phải đóng, và bảng cân đối lãi/lỗ theo tháng/năm (tổng hoặc từng tòa nhà). Hai lỗ hổng thật phát hiện lúc scope: **`ExpensesScreen` tồn tại trong code/navigation nhưng KHÔNG có màn hình nào dẫn tới nó** (cùng loại lỗi "chôn hành động quan trọng" như M10.1 — xem hàng changelog 2026-07-26 bên dưới, lần này là *unreachable* chứ không phải *khó tìm*); và `Expense.propertyId` trước đó bắt buộc nên không thể ghi nhận chi phí thật sự chung (kế toán, giấy phép kinh doanh) mà không gán ép vào 1 tòa nhà.

**Đã thêm**:
- `Expense.propertyId` chuyển thành optional (`undefined` = chi phí chung công ty, không thuộc tòa nhà nào); `deleteExpense` action bỏ tham số `propertyId` (xác nhận qua đọc `deleteExpenseSaga` — chỉ dùng `date` để tính key tháng, `propertyId` chưa từng được dùng, không cần giữ optional làm gì).
- `RentalSettings` thêm `taxEnabled`/`annualRevenueTaxThreshold`/`vatRatePercent`/`personalIncomeTaxRatePercent` — giá trị seed (100 triệu/năm, 5% GTGT + 5% TNCN theo mô hình cá nhân/hộ cho thuê, không phải pháp nhân), luôn có thể sửa trong `RentalSettingsScreen`, có disclaimer rõ không phải số liệu chính thức.
- 2 engine thuần mới có Jest test: `common/rental/taxEstimate.ts` (`computeTaxEstimate` — dưới/đúng ngưỡng = 0 thuế, trên ngưỡng = % cố định trên doanh thu tiền phòng), `common/rental/profitLoss.ts` (`computeProfitLoss` — cộng doanh thu theo thành phần hóa đơn trừ tổng chi phí, không NaN khi rỗng, âm đúng khi chi > thu).
- `ExpensesScreen`/`CreateExpenseScreen` viết lại: `propertyId` route param thành optional — khi vào từ 1 tòa nhà cụ thể (`PropertyDetailScreen`) thì khoá lại như cũ; khi vào từ Home (aggregate) thì hiện hàng chip lọc "Tất cả/Chung/từng tòa nhà" (giống pattern `InvoiceListScreen`) và picker chọn tòa nhà lúc tạo mới.
- **Sửa lỗi unreachable**: thêm quick-action "Chi phí" trên `RentalHomeScreen` (vào chế độ tổng hợp) + entry "Chi phí"/"Lãi/lỗ" trên `PropertyDetailScreen` (khoá theo tòa nhà đó).
- `TaxEstimateScreen` (mới): chọn năm, tổng tiền phòng thực thu trong năm từ hóa đơn thật, so ngưỡng, breakdown GTGT/TNCN, disclaimer, link sang mục thuế trong Cài đặt.
- `ProfitLossScreen` (mới): chuyển đổi theo tháng/năm + điều hướng kỳ trước/sau, hàng chip chọn tòa nhà (Tất cả + từng tòa nhà), breakdown doanh thu theo thành phần (tiền phòng/điện/nước/phí) trừ tổng chi phí ra lãi/lỗ ròng. Vào từ `ReportsScreen` (không khoá tòa nhà) và `PropertyDetailScreen` (khoá theo tòa nhà đó nhưng vẫn đổi được về "Tất cả").
- `ReportsScreen`: thêm link sang `ProfitLossScreen` và `TaxEstimateScreen` (giữ nguyên phần tổng quan tháng này + xuất CSV + link Đối soát/Công nợ cũ).

## Bổ sung: vòng đời tài sản — tình trạng, hao mòn, chi phí thay thế, nhắc bảo dưỡng (2026-07-27)

Yêu cầu: theo dõi tình trạng phòng/đồ đạc liên tục (không chỉ lúc bàn giao như `AssetSettlementItem` đã có), ước tính mức hao mòn, chi phí thay thế, nhắc lịch bảo dưỡng, và chuẩn hoá dữ liệu để sẵn sàng sync khi có backend (chưa xây sync thật — mục 6.1/6.3 Playbook, đây là chủ đích không phải thiếu sót).

**Quyết định thiết kế chính**:
- Hao mòn = ước tính theo thời gian (`số tháng đã dùng / tuổi thọ kỳ vọng`), không có cảm biến thật — luôn ghi rõ là ước tính trong UI (mục 9.2 Playbook).
- Không tạo entity lịch sử sửa chữa riêng — tái dùng `Expense` đã có (thêm `Expense.assetId?`) để tránh trùng lặp storage.
- Không thêm field `Room`-level cho tình trạng — suy ra từ tổng hợp asset, tránh 2 nguồn sự thật.
- "Chuẩn hoá sync tương lai" chỉ là thêm `updatedAt` bắt buộc cho `AssetItem` (đang thiếu, đúng mục 4.5 Playbook) — không thêm field tenant-facing giả định, không viết code đồng bộ/API (chưa có backend).
- Nhắc bảo dưỡng tái dùng nguyên pattern `createNotification`/`cancelNotification` + `RentalSettings.reminderDaysBeforeDue` đã có (xem `saveContractNotificationSaga`), không thêm setting mới.

**Data model**: `AssetItem` thêm `conditionStatus` (enum 4 trạng thái), `purchaseDate`, `purchaseCost`, `expectedLifespanMonths`, `replacementCost`, `maintenanceIntervalMonths`, `lastMaintenanceDate`, `updatedAt` (bắt buộc). `Expense` thêm `assetId?`.

**Engine mới** `common/rental/assetLifecycle.ts`: `computeAssetWear` (ngưỡng cụ thể `AGING_THRESHOLD_PERCENT = 70`, `<70% good / 70–<100% aging / >=100% end_of_life`), `computeNextMaintenanceDate`.

**Saga mới**: watcher thứ 2 cho `SAVE_ROOM` (`saveRoomMaintenanceNotificationsSaga`) — diff asset cũ/mới để cancel notification của asset đã xoá, tạo/huỷ lại theo `maintenanceIntervalMonths` hiện tại, cùng pattern `saveContractNotificationSaga`.

**Màn hình mới**: `AssetDetailScreen` (view+edit 1 asset, hiện wear%/lịch bảo dưỡng read-only, danh sách chi phí gắn `assetId`, nút ghi nhận sửa chữa mở `CreateExpenseScreen` pre-fill), `MaintenanceScreen` (aggregate toàn portfolio, sort theo hạn gần nhất). Entry point: quick-action `RentalHomeScreen` + `PropertyDetailScreen` (rút kinh nghiệm lỗi unreachable đã gặp 2 lần trước — xây entry point ngay từ đầu, không để phát hiện sau).

**Verification đã thực hiện**: Jest thật cho `computeAssetWear`/`computeNextMaintenanceDate` — 8 test (thiếu dữ liệu không NaN, biên chính xác 70%/100%, 3 mốc fallback khác nhau cho `computeNextMaintenanceDate`, case không set interval trả `undefined`) — tổng `__tests__/rentalEngines.test.ts` 37/37 pass. `tsc` qua tsconfig cách ly đã kiểm chứng — 0 lỗi mới trong mọi file Rental/navigation/store liên quan (45 lỗi TS8010 còn lại là noise có sẵn từ app khác, không đổi so với trước). `git diff --stat` xác nhận thay đổi chỉ trong file Rental + `navigation/*` (thuần cộng thêm) + test + doc này.

**Giới hạn đã biết** (ghi rõ, không cố sửa vì hiếm gặp — mục 9.2 Playbook không được đóng hộp giả sử "ổn"): `saveRoomMaintenanceNotificationsSaga` dùng cache trong bộ nhớ (`ROOM_ASSET_NOTIFICATION_IDS`, reset khi mở lại app) để biết asset nào vừa bị xoá và cần huỷ nhắc — nếu người dùng xoá 1 asset đang có lịch nhắc NGAY LẦN LƯU ĐẦU TIÊN sau khi mở lại app, thông báo cũ (đặt lịch từ phiên trước) sẽ không bị huỷ đúng lúc đó (tự hết tác dụng ở lần sửa phòng tiếp theo). Chưa bấm thử notification thật trên thiết bị trong phiên này — xác minh qua đọc lại code, không phải quan sát trực tiếp.

## Bổ sung: cho thuê ngắn hạn kiểu Airbnb — đặt phòng, lịch, nhập iCal, doanh thu/thuế hợp nhất (2026-07-27)

Yêu cầu: kết hợp quản lý cho thuê dài hạn hiện có với cho thuê ngắn hạn kiểu Airbnb. Đã hỏi 1 quyết định kiến trúc lớn (AskUserQuestion): có cần nhập lịch từ Airbnb qua iCal để tránh trùng lịch không — người dùng chọn CÓ.

**Giới hạn kỹ thuật thật, minh bạch trong UI**: app không có backend/API riêng, không phải đối tác API Airbnb → chỉ đồng bộ 1 chiều (đọc busy-dates từ link iCal Airbnb xuất ra), không đẩy ngược lịch/giá lên Airbnb được. Feed iCal công khai của Airbnb/Booking.com chủ động ẩn tên khách + giá (hành vi chuẩn của nền tảng, không phải giới hạn app) — bản ghi nhập từ iCal chỉ có khoảng ngày, chủ trọ tự bổ sung tên khách/giá nếu cần.

**Quyết định thiết kế chính**:
- `Booking` là entity MỚI tách khỏi `Contract` (ngữ nghĩa khác hẳn: theo đêm vs theo tháng) — nằm trong `rentalHistoryReducer` (không whitelist) + sharded theo tháng trong AsyncStorage, giống hệt `Expense`/`Invoice` (mục 4.2/4.3 Playbook, quyết định từ đầu).
- Không thêm dependency iCal ngoài — viết parser thuần nhỏ tự test (`icalParser.ts`), tránh rủi ro thư viện ngoài không kiểm soát chất lượng. Không cần native module — `fetch()` có sẵn, `react-native-calendars` đã có sẵn trong `package.json`.
- Fetch iCal là GET công khai TỚI Airbnb (đọc dữ liệu công khai từ URL người dùng cung cấp), không phải đẩy dữ liệu riêng tư ra ngoài — không vi phạm nguyên tắc "không cloud sync tuỳ tiện" (mục 3 Playbook).
- Bản ghi từ iCal đánh dấu `source: 'ical_import'`, khớp theo `icalUid` ở lần đồng bộ sau để không tạo trùng; chủ trọ bổ sung thông tin ngay trên bản ghi đó thay vì tạo bản ghi song song.
- Doanh thu ngắn hạn nối vào `computeProfitLoss` (tham số `bookingsInPeriod`, default `[]`, không phá test cũ) và vào doanh thu chịu thuế ở `TaxEstimateScreen`.
- Tái dùng tính năng tình trạng tài sản/phòng vừa xây (mục trên) làm bước kiểm tra bàn giao nhanh giữa 2 lượt khách — không xây luồng settlement riêng.

**Data model**: `Booking` (roomId, propertyId, checkInDate/checkOutDate, guestName?/guestPhone?, platform, nightlyRate?/cleaningFee?/totalAmount?, paymentStatus, paidAmount, source, icalUid?, notes?, createdAt, updatedAt bắt buộc). `Room` thêm `icalFeeds?: ICalFeedConfig[]` (nhỏ, gọn, ở reducer đã whitelist như `assetChecklist`).

**Engine mới**: `common/rental/icalParser.ts` (`parseICalBusyDates` — tách VEVENT, đọc UID/DTSTART/DTEND, bỏ qua block thiếu field an toàn). `profitLoss.ts` mở rộng thêm `bookingsInPeriod` param.

**Màn hình mới**: `BookingCalendarScreen` (dùng `react-native-calendars` có sẵn), `CreateBookingScreen` (validate trùng ngày cùng phòng, cảnh báo mềm nếu phòng đang có hợp đồng dài hạn), `BookingsScreen` (aggregate, entry Home + PropertyDetailScreen ngay từ đầu). `RoomDetailScreen` thêm mục "Cho thuê ngắn hạn (Airbnb)" + quản lý feed iCal (thêm/xoá URL, nút đồng bộ thủ công — không tự chạy nền). `ProfitLossScreen`/`TaxEstimateScreen` cộng doanh thu ngắn hạn, tách dòng rõ ràng trước khi gộp tổng.

**Verification đã thực hiện**: Jest thật — thêm `parseICalBusyDates` (5 test: mẫu VEVENT đúng cấu trúc Airbnb tính tay đúng UID/ngày, block thiếu UID/DTEND bị bỏ qua an toàn không throw, text rỗng không crash, CRLF cho kết quả giống LF, line-folding RFC 5545 unfold đúng) và `computeProfitLoss` mở rộng (2 test mới: cộng đúng `shortTermBooking` vào tổng, booking chưa có `totalAmount` tính là 0 không NaN) + cập nhật 3 test cũ để khớp field `shortTermBooking` mới trong `toEqual` — tổng `__tests__/rentalEngines.test.ts` 44/44 pass. `tsc` qua tsconfig cách ly đã kiểm chứng — 0 lỗi mới trong mọi file Rental/navigation/store liên quan (vẫn đúng 45 lỗi TS8010 noise có sẵn, không tăng). `git diff --stat` xác nhận thay đổi chỉ trong file Rental + `navigation/*`/`storage.ts` (thuần cộng thêm) + test + doc này — không đụng `package.json` (đúng kế hoạch, không thêm dependency iCal ngoài).

**Giới hạn đã biết**: đồng bộ iCal là thủ công (người dùng bấm "Đồng bộ ngay"), không tự chạy nền — đúng chủ đích minh bạch, không phải thiếu sót. Bản ghi nhập từ iCal không có tên khách/giá (nền tảng không xuất công khai) — chủ trọ cần tự bổ sung nếu muốn theo dõi đầy đủ. Chưa test với 1 link iCal Airbnb thật (chỉ test bằng mẫu `.ics` dựng tay đúng cấu trúc đã biết) — nên tự thử với link thật trước khi coi là hoàn thiện, vì Airbnb có thể thay đổi định dạng xuất theo thời gian. Chưa bấm thử trên simulator/thiết bị thật trong phiên này.

## Bổ sung: màn hình tổng quan phòng (Rooms Overview) — search + bộ lọc nâng cao (2026-08-02)

Yêu cầu: 1 màn hình cho chủ trọ thấy TOÀN BỘ danh mục phòng (mọi tòa nhà) trong 1 lần nhìn — trạng thái, số người ở, nợ cước, vấn đề bảo trì (điện/nước) — kèm search mặc định theo tên, bộ lọc nâng cao ẩn/hiện khi bấm. Không cần backend — toàn bộ dữ liệu (Room.status, Contract cho occupancy, Invoice cho nợ, Room.assetChecklist cho vấn đề bảo trì) đã có sẵn local, chỉ chưa có nơi nào gộp lại thành 1 view.

**Kiến trúc**: 1 hàm thuần mới `common/rental/roomOverview.ts` (`buildRoomOverviewRows`, `RoomOverviewRow`, `RoomSeverity`), KHÔNG thêm selector redux mới — component tự gọi các selector đã có (`getRooms`/`getProperties`/`getContracts`/`getTenants`/`getAllInvoices`) rồi tính trong `useMemo`, đúng cách `RentalHomeScreen` đã làm với `underFilledCount`. Tái dùng nguyên `computeDebtAging` (nợ quá hạn) và pattern `computeNextMaintenanceDate` (bảo dưỡng quá hạn) đã có, không viết lại logic. `severity` (`ok`/`warning`/`critical`) suy ra từ: status=repairing hoặc asset `broken` hoặc nợ quá hạn → critical; có nợ chưa tới hạn hoặc asset `needs_repair` hoặc sắp tới hạn bảo dưỡng → warning.

**Màn hình**: `containers/Rental/RoomsOverviewScreen` — search bar luôn hiện (mặc định, lọc theo tên phòng/tòa nhà/tên người thuê), nút "Bộ lọc nâng cao ▾" ẩn mặc định (chip tòa nhà, chip trạng thái, toggle "chỉ có nợ"/"chỉ có vấn đề"). Card mỗi phòng: border-trái màu theo severity, badge trạng thái, occupancy/nợ/vấn đề bảo trì bằng icon emoji nhất quán với style Rental hiện có. Tap → `RoomDetailScreen`.

**Entry point**: quick-action tile mới trên `RentalHomeScreen`, đặt ở hàng action đầu tiên (cạnh "Nhà trọ"/"Hóa đơn") — chủ đích tránh lặp lại lỗi "chôn hành động quan trọng" đã ghi ở 2 hàng changelog 2026-07-26/2026-07-27 bên dưới.

**Không liên quan** tới backend ticket sửa chữa vừa build trong `dvc-api` (`docs/srs/rental-tenant-tickets.md`, cho vai trò Tenant qua app riêng chưa xây) — "vấn đề bảo trì" ở màn này lấy từ `Room.assetChecklist` local, không gọi API.

**Verification đã thực hiện**: Jest thật — 8 test case mới cho `buildRoomOverviewRows` (phòng trống không vấn đề → ok; đang sửa → critical bất kể debt/maintenance; nợ quá hạn → critical; nợ chưa tới hạn → warning; asset broken → critical; asset needs_repair → warning; occupancy phòng ở ghép tính đúng `1 + memberTenantIds.length`; nhiều tòa nhà không lẫn dữ liệu) — `__tests__/rentalEngines.test.ts` 52/52 pass. `tsc` qua tsconfig cách ly đúng phạm vi (Rental + `navigation/**/*.js` + rootReducer/store/rootSaga/storage, theo đúng bài học mục 6.5 Playbook) — 0 lỗi trong file Rental/mới, 45 lỗi TS8010 noise có sẵn không đổi. `git diff --stat`: CareAi chỉ đụng 4 file có sẵn (test, RentalHomeScreen, navigation constants+index, thuần cộng thêm) + 2 file mới (`roomOverview.ts`, `RoomsOverviewScreen/`). **Chưa bấm thử trên simulator/thiết bị thật trong phiên này** (không có công cụ tương tác UI) — verify dựa trên đọc lại logic từng nhánh (search, filter, severity color, empty state) + Jest chạy thật cho phần logic, không phải quan sát trực tiếp trên app; nên tự tay bấm qua trước khi phát hành. Lúc wiring quick-action Home phát hiện tile "Phòng ở ghép" từng bị lặp 2 lần khi chèn tile mới — đã dọn lại, xác nhận qua đọc lại JSX cân bằng thẻ đóng/mở.

## Bổ sung lớn: Owner sync client + app Tenant mới hoàn toàn (2026-08-02)

Yêu cầu người dùng: app Tenant cần đủ 5 nhóm chức năng — xem thông tin, chi phí hàng tháng, báo lỗi, thông báo, liên hệ chủ nhà. Backend đã build xong (`dvc-api apps/rental`: auth qua `platform/iam`, phân quyền Owner/Manager/Tenant, sync generic, ticket 18 FR, `GET /me/room`/`GET /me/invoices` FR-19..FR-23 — xem `dvc-api/docs/srs/rental-tenant-tickets.md`), nhưng **chưa có mobile client nào gọi tới** — CareAi 100% local-only tới thời điểm này.

**Quyết định lớn đã chốt qua AskUserQuestion**:
1. "Liên hệ chủ nhà" chỉ qua thread tin nhắn gắn với ticket (không xây kênh chat tự do).
2. Liên kết Tenant↔Room qua `room_id` thật (Owner chọn từ picker lúc mời), không phải `unit_label` gõ tay.
3. Xây luôn client sync HTTP cho app Owner (giải quyết gốc việc Owner app chưa từng đồng bộ gì lên server) — không nhập tay tạm.

**Quyết định kiến trúc quan trọng** (chi tiết đầy đủ trong plan đã duyệt, xem lịch sử trò chuyện hoặc `~/.claude/plans/harmonic-jumping-lamport.md` nếu còn):
- Đăng nhập TÙY CHỌN — app Owner giữ nguyên local-only nếu không đăng nhập, "Đồng bộ đám mây" là mục mới trong Settings, không ép buộc.
- `Property.id` local (client-generated) khác `id` server trả về (Postgres-generated) — khi bật cloud cho 1 tòa nhà, rewrite 1 lần: đổi `Property.id` + cascade toàn bộ `propertyId` tham chiếu (Room/Contract/Invoice/...) sang ID server, không giữ bảng mapping riêng.
- Cơ chế sync: "đẩy toàn bộ, để server LWW tự loại trùng" (`sync_records.UpsertIfNewer` đã lọc theo `updated_at` ở tầng SQL) — không xây outbox/dirty-queue.
- Quy ước `entity_type` khi push PHẢI khớp tên interface TypeScript (`"Room"`, `"Contract"`, `"Invoice"`...), payload nguyên object theo `src/app/types/rental.ts`.
- Tái dùng hạ tầng có sẵn: `react-native-keychain` (lưu JWT, đã dùng cho `LockProvider`/`PasswordManager`), `generateUUIDv4()` (`src/app/utils/utils.ts:205`), `createNotification`/`cancelNotification` (`src/app/utils/notification.ts`), `react-native-qrcode-svg` + `react-native-vision-camera`/`@mgcrea/vision-camera-barcode-scanner` (đã cài, đủ cho QR mời 2 chiều), cấu trúc `useAutoCloudSync.ts` làm mẫu cho hook tự động sync HTTP.

**8 milestone đã lên kế hoạch** (mỗi milestone ra 1 thứ test được):
M1 nền tảng dùng chung (HTTP client + auth + Keychain) → M2 Owner bật đồng bộ đám mây/rewrite ID/push-pull → M3 Owner mời Manager/Tenant qua tài khoản thật (QR/email, chọn Room thật) → M4 Owner dashboard ticket → M5 app Tenant mới (bundle id `com.careai.rental.tenant`, scaffold + đăng nhập + liên kết nhà trọ) → M6 app Tenant Home (thông tin + chi phí, tính năng LÕI) → M7 app Tenant ticket + thông báo polling + liên hệ chủ nhà → M8 app Tenant cài đặt/đăng xuất.

**Trạng thái**: M1 Done. Các milestone sau (M2..M8) build tuần tự sau khi được duyệt tiếp.

**M1 đã build**: `src/app/services/rentalApiClient.ts` (`request<T>` thuần, envelope `{success,data,error}`, `RentalApiError`, `X-App-Key` chỉ gắn khi `appKey:true`), `src/app/services/rentalAuth.ts` (`register`/`login`/`logout`/`authRequest` với đúng 1 lần refresh-and-retry khi 401, lưu token qua `react-native-keychain` — KHÔNG AsyncStorage, đúng pattern đã dùng ở `LockProvider`/`PasswordManager`). Đăng nhập vẫn hoàn toàn tùy chọn — chưa có màn hình nào gọi tới các hàm này, app Owner không đổi hành vi.

**Verification đã thực hiện**: Jest thật — 13 test case (`rentalApiClient.test.ts`: envelope thành công/lỗi, HTTP status không ok dù envelope success, 204 không đọc body, gắn đúng Authorization/X-App-Key có điều kiện; `rentalAuth.test.ts`: round-trip Keychain mock đúng API thật (`setGenericPassword`/`getGenericPassword`/`resetGenericPassword` với `service`), refresh-and-retry đúng 1 lần khi 401, KHÔNG retry lỗi domain khác như 403, xoá token + báo `RentalSessionExpiredError` khi refresh cũng thất bại) — toàn dự án 129/129 test logic pass (`App.test.tsx` fail vì lỗi babel/ESM có sẵn từ trước, không liên quan). `tsc` qua tsconfig cách ly (Rental + service mới + `navigation/**/*.js` + rootReducer/store/rootSaga/storage) — 0 lỗi mới, đúng 45 lỗi TS8010 noise có sẵn không đổi. **Verify hợp đồng dữ liệu thật với backend sống**: viết 1 script Node độc lập (`/tmp/verify_rentalauth_contract.js`, không giữ lại trong repo) gọi thật `register`→`login`→`GET /properties` (có token)→`refresh`→gọi lại `GET /properties` (token mới)→`logout`→gọi với token rác xác nhận đúng `401 UNAUTHORIZED` (chính là điều kiện `authRequest` dựa vào để quyết định có refresh-retry hay không) — toàn bộ khớp đúng type `TokenPair`/`RentalAccount` đã định nghĩa. Riêng phần đọc/ghi Keychain thật (native runtime) chưa test trên simulator/thiết bị thật trong phiên này (không có công cụ tương tác UI) — dựa trên unit test mock đúng API thật + đối chiếu cách dùng thật đã có ở `LockProvider`/`PasswordManager`, chưa phải quan sát trực tiếp.

## Monetization
Giữ mô hình Free/Premium placeholder tĩnh như v1 (chưa có IAP thật, mục 6.4 Playbook).

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Không multi-user/đa thiết bị thật cho nhân viên (quyết định kiến trúc đã chọn).
- Bảng bậc thang seed sẵn, người dùng cần tự đối chiếu với hóa đơn điện thật.
- Ảnh CCCD không mã hóa đặc biệt, chỉ lưu file local như các app khác.
- Không đối soát ngân hàng tự động, không kênh Zalo/SMS/email (cần backend).

## Build order
1. Data model + redux (2 reducer) + storage helpers cho toàn bộ entity mới.
2. 4 engine lõi (`tieredPricing`/`reconciliation`/`debtAging`/`vietQr`) + Jest test — chạy thật trước UI.
3. M1/M2: Properties/RoomGroups/Rooms.
4. M3/M4: Tenants/Contracts (thay Tenant+AssignTenant cũ).
5. M5/M6/M7: cấu hình bậc thang, ghi chỉ số phòng + tổng tòa nhà, tính hóa đơn có tier breakdown.
6. **M8 (tính năng lõi)**: `ReconciliationScreen` + biểu đồ — chạy bài kiểm tra hoàn hảo mục 3.2 riêng cho màn này.
7. M9/M10/M11: chi phí, thanh toán + VietQR + biên nhận, công nợ/tuổi nợ.
8. M12/M13/M14: nhắc nhở local, tạm trú, liên hệ khẩn cấp.
9. M15/M16/M18: thanh lý, báo cáo + CSV, cài đặt (bậc thang editor), audit log, backup/restore.
10. Wiring route mới, `tsc` diff (chuẩn + cách ly), `git diff --stat`.

## Verification đã thực hiện
- Jest: `__tests__/rentalEngines.test.ts` — 22/22 test pass thật, gồm biên chính xác bậc thang điện (3 bậc, ranh giới chính xác 50/100 kWh), `computeCarryOver` (nợ + phạt trễ hạn tính tay), `computeBuildingReconciliation` (hao hụt %, lãi/lỗ, ca hasEnoughData=false không NaN, ca thu vượt không bị gắn cờ sai), `computeDebtAging` (ranh giới chính xác 15/16 ngày), và đặc biệt `crc16ccitt` đối chiếu với test vector CRC-16/CCITT-FALSE đã công bố ("123456789" → 0x29B1) — xác nhận thuật toán VietQR đúng theo chuẩn thật, không chỉ tự nhất quán nội bộ. Toàn dự án: 54/54 test logic pass (App.test.tsx fail vì lỗi babel/ESM có sẵn từ trước, không liên quan).
- **Phát hiện lại lỗ hổng tsc dự án** (mục 6.5 Playbook) — `tsc` chuẩn báo "1077 dòng, không đổi" dù đã xóa hàng loạt action/type cũ mà nhiều màn hình cũ còn tham chiếu (phải là lỗi thật). Tsconfig cách ly cũ (chỉ loại 2 file Yoga) cũng KHÔNG bắt được — nghĩa là có thêm file lỗi cú pháp khác gây tắt kiểm tra ngữ nghĩa toàn dự án, chưa xác định được file cụ thể. **Kỹ thuật xác minh mới, đáng tin cậy hơn**: tsconfig cách ly thu hẹp `include` chỉ tới đúng phạm vi file liên quan (containers/Rental, redux/rental, common/rental, types/rental.ts + các file dùng chung đã sửa) thay vì toàn dự án — cách này bắt được đầy đủ lỗi thật ngay lập tức (45+ lỗi ở các file cũ chưa migrate), rồi sau khi sửa hết, xác nhận 0 lỗi. Nên dùng cách thu hẹp phạm vi này cho các lần sau thay vì chỉ loại trừ file lỗi đã biết.
- `git diff --stat`: chỉ 4 file dùng chung bị sửa (`navigation/index.js`, `navigation/constants.js`, `utils/storage.ts`, `rootReducer.ts`) — 223 dòng cộng thêm, 5 dòng xóa (đúng 4 dòng xóa `AssignTenantScreen` cũ đã bị thay thế bởi Contract, xác nhận bằng grep không có xóa nào khác ngoài dự kiến).
- Đã tự chạy qua bài kiểm tra hoàn hảo 5 kịch bản (mục 3.2) cho `ReconciliationScreen`: chưa có dữ liệu (empty state + CTA), 1 tháng, nhiều tháng (biểu đồ xu hướng), hao hụt >15% (badge đỏ "bất thường"), thu vượt/hao hụt âm (badge xanh "Thu vượt", không gắn cờ sai).
- (2026-07-27) Jest: thêm `computeTaxEstimate` (4 test: dưới ngưỡng, đúng ngưỡng không tính là vượt, trên ngưỡng tính tay đúng %, tắt tính năng luôn = 0) và `computeProfitLoss` (3 test: rỗng không NaN, cộng đúng từng thành phần tính tay, âm đúng khi chỉ có chi phí không có doanh thu) vào `__tests__/rentalEngines.test.ts` — 29/29 pass. `tsc` qua tsconfig cách ly đúng phạm vi đã kiểm chứng (Rental + `navigation/**/*.js` + `rootReducer`/`store`/`rootSaga`/`storage`) — 0 lỗi trong mọi file Rental/navigation/store liên quan (các lỗi TS8010 còn lại là noise có sẵn từ file `.js` app khác được kéo vào gián tiếp qua `navigation/index.js`, không liên quan tới thay đổi này). `git diff --stat` xác nhận thay đổi chỉ nằm trong file Rental + `navigation/index.js`/`navigation/constants.js` (thêm route thuần, không sửa route cũ) + file test + doc này. **Chưa chạy được bằng tay trên simulator/thiết bị thật trong phiên này** (không có công cụ tương tác UI) — việc xác minh dựa trên Jest chạy thật + đọc lại logic từng nhánh (chip lọc, optional propertyId, breakdown theo kỳ) chứ không phải quan sát trực tiếp trên app; nên tự tay bấm qua trước khi phát hành.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-07-26 | Chưa audit lại bằng tsconfig cách ly (mục 6.5) hay viết Jest test cho `calculateInvoice.ts`; tính điện/nước theo đơn giá cố định, không bậc thang — sai với quy định pháp luật thật | App v1 được xây trước khi phát hiện ra lỗ hổng `tsc` và trước khi hình thành quy tắc "phải test logic quan trọng"; không có bằng chứng thị trường/pháp lý chi tiết lúc xây v1 | Xây lại toàn bộ v2 theo tài liệu yêu cầu 18 module người dùng cung cấp — bậc thang thật, có Jest test cho mọi engine tính toán | Có — mục 6.5 và mục 8 (checklist) của Playbook áp dụng cho mọi app từ nay về sau |
| 2026-07-26 | v1 không tách reducer persist/history riêng — `invoicesByMonth`/`meterReadingsByMonth` nằm chung reducer đã whitelist | Xây trước khi rút ra bài học tách reducer từ Migraine | v2 áp dụng tách reducer ngay từ đầu (xem Kiến trúc kỹ thuật) | Có — mục 4.2 Playbook |
| 2026-07-26 | Xây xong v2 nhưng chức năng "Ghi nhận thanh toán" (M10.1) chỉ có 1 đường vào duy nhất: Home → tab Hóa đơn → mở chi tiết hóa đơn → mới thấy nút. Người dùng test thử và không tìm thấy — đúng lỗi "chôn hành động quan trọng nhất trong menu" mà mục 2 Playbook cảnh báo | Tập trung làm đúng/đủ 18 module trong lúc build mà không tự hỏi "hành động nào chủ trọ làm THƯỜNG XUYÊN NHẤT có dễ tìm không" — thu tiền hàng tháng chắc chắn là 1 trong số đó | Thêm banner nổi bật trên Home khi có hóa đơn chưa thu tháng này (đếm số lượng, 1 chạm đến danh sách đã lọc sẵn "Chưa thu"); thêm nút "Thu tiền" trực tiếp trên từng dòng ở `InvoiceListScreen` (bỏ qua bước vào chi tiết) | Nên thêm: sau khi xây xong 1 tính năng CRUD, tự hỏi tính năng nào trong đó là hành động lặp lại thường xuyên nhất và kiểm tra số lần chạm cần thiết để tới đó — cân nhắc thêm vào mục 3.2 (bài kiểm tra hoàn hảo) như 1 câu hỏi bổ sung |
| 2026-07-26 | Kỹ thuật tsconfig cách ly (mục 6.5) thu hẹp phạm vi quá tay — loại bỏ `navigation/**/*.js` khỏi `include` làm mất ngữ cảnh kiểu `RootParamList`, khiến MỌI lệnh `navigation.navigate(...)` trong toàn bộ Rental (kể cả code không hề đổi) báo lỗi giả "argument of type X is not assignable to parameter of type never" | Hiểu sai phạm vi "thu hẹp" — tưởng chỉ cần include đúng file mình sửa, nhưng quên rằng kiểu dùng chung (RootParamList) được khai báo/suy ra từ chính `navigation/index.js` | Chạy lại với `navigation/**/*.js` + `rootReducer`/`store`/`rootSaga`/`storage` trong `include` — xác nhận lại 0 lỗi thật | Có — bổ sung vào mục 6.5 Playbook: tsconfig cách ly thu hẹp phải giữ đủ file cung cấp type ambient/dùng chung (navigation, rootReducer...), không chỉ file mình sửa, nếu không sẽ tạo báo động giả |
| 2026-07-27 | `Room.assetChecklist` được khai báo trong type từ lúc xây v2 nhưng KHÔNG có màn hình nào đọc/ghi nó — field "chết" đúng kiểu Playbook mục 2 cảnh báo (dead setting), chỉ khác là dead *data field* thay vì dead *toggle*. `Room.maxOccupancy` (M2.1 gốc) bị bỏ sót hoàn toàn khi rebuild | Khi rebuild v2, tập trung vào luồng tính hóa đơn/đối soát (tính năng lõi) và bỏ sót các field nhỏ hơn trong cùng model — không có bước rà soát "field nào trong type đã khai báo nhưng chưa có UI dùng tới" trước khi coi 1 module là xong | Thêm editor tài sản + max occupancy vào `CreateRoomScreen`, snapshot vào `Contract` lúc tạo hợp đồng, đối chiếu itemized lúc thanh lý | Nên thêm: bổ sung vào checklist mục 8 — sau khi hoàn thành 1 type/interface, grep chính field đó trong toàn bộ `containers/` để xác nhận có ít nhất 1 nơi đọc VÀ 1 nơi ghi, không chỉ khai báo suông |
| 2026-07-27 | Bản đầu của `SharedRoomsScreen` tính "phòng thiếu người" chỉ dựa trên `occupancyCount < maxOccupancy`, gộp luôn phòng trống hoàn toàn (0 người) vào danh sách "ở ghép cần tìm người" — tự phát hiện khi tự đóng vai người dùng đi qua kịch bản (mục 3.2) | Không phân biệt "phòng trống hoàn toàn, cần tìm người thuê đầu tiên" (đã có sẵn ở danh sách phòng trống) với "phòng đã có người, ở ghép chưa đủ" (ý nghĩa thật của tính năng) | Thêm điều kiện `occupancyCount > 0` vào bộ lọc ở cả `SharedRoomsScreen` và banner đếm số trên Home | Không cần thêm quy tắc riêng — đã được mục 3.2 (tự đóng vai người dùng qua kịch bản) bắt trước khi bàn giao |
| 2026-07-27 | `ExpensesScreen`/`CreateExpenseScreen` được xây từ M9 nhưng KHÔNG có bất kỳ màn hình nào (Home, PropertyDetail, tab nào) dẫn tới chúng — grep xác nhận 0 điểm vào, phát hiện lúc scope yêu cầu chi phí tổng hợp mới, không phải khi build M9 ban đầu | Cùng nguyên nhân gốc với hàng "M10.1 Ghi nhận thanh toán" (2026-07-26): build xong 1 CRUD/module rồi coi là xong mà không tự hỏi "từ Home cần mấy chạm để tới đây" — lần này còn nặng hơn (0 chạm khả dĩ, không phải chỉ 3 chạm) vì màn hình bị bỏ sót hoàn toàn khỏi mọi action row | Thêm quick-action "Chi phí" trên `RentalHomeScreen` + entry trên `PropertyDetailScreen` | Không cần thêm quy tắc mới — quy tắc mục 8 (đếm số chạm từ Home sau khi xây xong CRUD) đã có sẵn từ lần trước, lần này là do CHƯA áp dụng nó cho `ExpensesScreen` khi build M9, không phải do thiếu quy tắc |
| 2026-07-27 | `Expense.propertyId` được khai báo bắt buộc từ v2, khiến không thể ghi nhận chi phí chung thật sự (kế toán, giấy phép) mà không gán ép vào 1 tòa nhà bất kỳ — phát hiện khi scope yêu cầu "chi phí chung" | Lúc rebuild v2 mặc định mọi entity đều thuộc về 1 `Property` mà không xét trường hợp chi phí ở cấp công ty, không gắn với tòa nhà cụ thể nào | Đổi `propertyId` thành optional trên type, cập nhật `deleteExpense` action (bỏ tham số thừa `propertyId` sau khi xác nhận saga không dùng), thêm chế độ "Chung" ở cả 2 màn hình chi phí | Không cần thêm quy tắc riêng — đã được nhắc ở mục 8 (grep field mới để xác nhận có đọc/ghi) áp dụng khi review lại type |
