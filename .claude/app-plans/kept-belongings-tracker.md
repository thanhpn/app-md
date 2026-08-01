# Kept — Personal Belongings & Closet Tracker — Plan

## Trạng thái
- Bundle ID: `com.careai.kept`
- Ngày bắt đầu: 2026-07-26
- Trạng thái: `v1.1 hoàn thành` (chưa build/run thật trên simulator — người dùng tự cấu hình bundle/target qua Xcode)

## Context
App quản lý đồ dùng cá nhân (quần áo, giày, đồ chơi, tài sản chung) — định vị **OCD/kiểm soát trước** (theo quyết định người dùng qua `AskUserQuestion`, không theo đề xuất "tài sản/tiết kiệm trước" của agent tổng hợp). Xây theo quy trình đầy đủ của Playbook: 3 agent (nghiên cứu thị trường, ý tưởng theo góc OCD/tài sản, tổng hợp+phản biện chéo) → tự phản biện → 2 câu hỏi lớn qua `AskUserQuestion` → Plan Mode → duyệt.

**Căng thẳng đã biết, cố ý chấp nhận**: nghiên cứu thị trường không tìm thấy bằng chứng giá nào cho định vị OCD (chỉ có bằng chứng giá cho hướng tài chính — Stylebook $4.99). Đây là 1 canh bạc định vị có chủ đích của người dùng, không phải phát hiện đã kiểm chứng — không đầu tư quá tay vào tính năng riêng cho OCD (VD: animation "hoàn thành" riêng) ngoài mức MVP bình thường cần, chờ dữ liệu retention thật xác nhận.

## Phân tích thị trường (tóm tắt)
Thị trường phân mảnh, "tổn thương lòng tin" chứ không bão hòa: Sortly (dẫn đầu inventory tổng quát) bị review 1 sao vì tăng giá ~300%, mất dữ liệu sau update; CLZ bắt subscribe riêng từng loại sưu tầm (phim/sách/game), không hỗ trợ đồ chơi/collectible chung; app tủ đồ chia phe đẹp-nông-miễn phí (Acloset/Whering, bị chê glitchy) vs sâu-cũ-trả 1 lần (Stylebook, được khen đúng vì KHÔNG subscription/cloud). Khoảng trống: bắt ảnh nhanh, chạy hoàn toàn trên máy, đa danh mục, không ép tài khoản.

## Bảng tính năng cuối cùng (sau bước tự phản biện + pivot OCD)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|
| **Lõi (Premium, 4/4)** | **Daily Check-In** (ledger dùng/mặc đồ) | Chạm để log <5s → trạng thái active/dormant + cờ "đồ bị lãng quên" (>90 ngày). Cùng engine với hướng "cost-per-wear" nhưng đóng khung lại theo chắc chắn/hoàn chỉnh thay vì tiết kiệm |
| Mồi (free, <30s) | Instant Outfit Randomizer | Random phối đồ từ đồ đã có |
| Mồi (free, cần vài món) | Inventory Snapshot Card | Thẻ chia sẻ: số món, breakdown danh mục, "100% đã phân loại" — flex về trật tự, KHÔNG phải flex tiền |
| Hỗ trợ | CRUD món đồ, tìm kiếm theo danh mục/phòng/tag | Chuẩn List→Detail→Create/Edit |
| Hỗ trợ | **Set-Completeness Check** (bộ nhiều món: vest, giày đôi, bộ đồ chơi) | Được thêm lại sau khi chọn định vị OCD — phục vụ đúng nhu cầu đối xứng/hoàn chỉnh, dù tần suất thấp |
| Hỗ trợ | Nhắc bảo hành/bảo hiểm | Local notification THẬT qua `createNotification()` (pattern PetCare) — không phải setting chết |
| Hỗ trợ (Premium nhẹ) | Export CSV (free) / PDF (Premium) | Cho hồ sơ bảo hiểm |
| **Cắt khỏi MVP** | Duplicate-detector | Quyết định người dùng: chưa có bằng chứng giá, cần logic so ảnh — để sau |
| **Hoãn** | OCR/quét mã vạch | Cần native module mới → rủi ro Xcode Compile Sources (mục 6.1 Playbook) |

**Định vị**: "Biết chính xác mình có gì — không món nào bị quên, hoàn toàn trên máy bạn." Giọng điệu: điềm tĩnh, chính xác, không phán xét — tránh mọi ngôn ngữ mang tính "shaming" về đồ đạc/bừa bộn.

**Free/Premium**: Free = CRUD đầy đủ + tìm kiếm + 2 tính năng mồi + Set-Completeness Check + CSV export. Premium (placeholder tĩnh) = engine Daily Check-In (cờ dormant + cost-per-use) + PDF export.

## Data model
```ts
type ItemCategory = 'clothing_top'|'clothing_bottom'|'clothing_outerwear'|'shoes'|'accessory'|'toy_collectible'|'electronics'|'other';

interface Item {
  id: string; name: string; category: ItemCategory; photoUri?: string;
  brand?: string; size?: string; color?: string; room?: string;
  purchasePrice?: number; purchaseDate?: string;
  warrantyExpiresAt?: string; insuranceValue?: number;
  setId?: string; archived?: boolean;
  createdAt: string; updatedAt: string;
}
interface ItemSet { id: string; name: string; expectedItemIds: string[]; createdAt: string; updatedAt: string; }
interface UseEvent { id: string; itemId: string; usedAt: string; createdAt: string; } // 1 record/lần chạm, KHÔNG phải 1/ngày
interface KeptSettings { planTier: 'free'|'premium'; dormantThresholdDays: 90; warrantyReminderEnabled: boolean; }
```

## Kiến trúc kỹ thuật
- Redux slice: `src/redux/kept/` (5 file chuẩn). **Áp dụng pattern tách reducer NGAY TỪ ĐẦU** (bài học rút ra từ Migraine, đã ghi trong `migraine-diary.md` là "nên áp dụng ngược lại cho Rental/PetCare khi có dịp" — app này áp dụng đúng từ ngày đầu): `keptReducer` (items/itemSets/settings, whitelist) + `keptHistoryReducer` (useEventsByMonth, KHÔNG whitelist, rehydrate từ file tháng).
- Storage: `kept_useevents_${YYYY-MM}.json` sharded theo tháng, `loadAllHistorySaga` dùng `AsyncStorage.getAllKeys()` + filter prefix (pattern Migraine).
- Business logic: `src/app/common/kept/checkInEngine.ts` (`computeItemStatus`, `computeCostPerUse` — pure function, Jest test), `setCompleteness.ts`. Tái dùng `localDateOf` từ `src/app/common/migraine/dateHelpers.ts` (đã generic, không có logic riêng của Migraine).

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|
| `KeptHomeScreen` | Today — Daily Check-In + cảnh báo dormant | `MigraineHomeScreen` |
| `LogUseScreen` | Multi-select món đã dùng hôm nay | — |
| `ItemListScreen`/`ItemDetailScreen`/`CreateItemScreen` | Catalog CRUD | Pattern List→Detail→Create/Edit chuẩn |
| `DormantItemsScreen` | Đồ bị lãng quên + cost-per-use | — |
| `ItemSetsScreen`/`CreateItemSetScreen` | Set-Completeness | — |
| `OutfitRandomizerScreen` | Tính năng mồi | — |
| `SnapshotCardScreen` | Tính năng mồi (share card) | `react-native-view-shot`+`react-native-share` — tái dùng, không cần dependency mới (đã dùng ở Rental invoice-share) |
| `KeptStatsScreen` | Insights | — |
| `ExportScreen` | CSV/PDF | `buildReportHtml.ts` pattern của Migraine nếu áp dụng được |
| `KeptSettingsScreen` | Nhắc bảo hành (schedule thật), backup/restore | Pattern PetCare |
| `KeptUpgradePremiumScreen` | Placeholder tĩnh | Pattern Rental/PetCare/Migraine |

## Monetization
Free: CRUD + tìm kiếm + 2 mồi + Set-Completeness + CSV. Premium (placeholder): Daily Check-In engine + PDF export.

## v1.1 — sắc bén hơn, bớt thao tác, đồng bộ iCloud tự động (2026-07-26)

Người dùng phản hồi bản MVP "chưa đủ wow", quá nhiều thao tác tay, thiếu đồng bộ. Tự phản biện lại theo mục 2.3/3.2/9.1 Playbook (không phải làm đẹp chung chung) → 7 hạng mục cụ thể:

| # | Đã thêm | Vì sao (bám đúng gap tìm được, không phải trang trí) |
|---|---|---|
| 1 | **Quick check-in chip** trên Home — 8 món gần dùng/thêm nhất, chạm 1 lần là log ngay, không cần mở `LogKeptUseScreen` | Trước đó MỌI lần check-in đều phải mở màn hình riêng dù chỉ 1 món — phá vỡ đúng lời hứa "5 giây" |
| 2 | `CheckInBurst` (component dùng chung, `Animated`+`Vibration`, KHÔNG thêm dependency mới) — phản hồi tức thời cho mọi hành động check-in (chip Home, `LogKeptUseScreen`, `KeptItemDetailScreen`) | Mục 2.3 Playbook: "mọi hành động lưu phải có phản hồi tức thời" — trước đó không có gì |
| 3 | "Ready to let go" bundle trên `KeptDormantItemsScreen` — chọn nhiều món dormant → tạo thẻ chia sẻ (tái dùng pattern `captureRef`+`Share` của Snapshot Card) | Trước đó màn hình dormant chỉ hiển thị, không có hành động khép vòng lặp — thiếu "aha moment" mục 3.2 #5 |
| 4 | `BatchAddKeptItemsScreen` — chọn nhiều ảnh cùng lúc (`ImageCropPicker multiple:true`) → review list đặt tên/danh mục hàng loạt | Sửa đúng khiếm khuyết Stylebook mà chính nghiên cứu thị trường của tôi tìm ra ("cumbersome bulk photo entry") — không phải tính năng bịa ra |
| 5 | Nhớ category/room lần trước (`KEPT_LAST_CATEGORY_KEY`/`KEPT_LAST_ROOM_KEY` trong `types/kept.ts`, dùng chung giữa Create và Batch) | Giảm thao tác lặp lại |
| 6 | `MilestoneCelebration` — hiệu ứng confetti-dot tự vẽ (không dùng lottie dù đã có sẵn — không có asset local, không tự bịa URL) khi streak chạm mốc cố định 7/30/100/365 | Wow-factor thật, gắn với dữ liệu thật (streak), không phải hiệu ứng vô nghĩa |
| 7 | **Đồng bộ iCloud tự động** — `keptICloudSync.ts` (nhại chính xác `iCloudSync.ts` của Migraine, KHÔNG refactor file đó) + `useKeptAutoSync()` hook: tự sync lúc mount + mỗi lần app quay lại foreground (throttle 60s) — không cần bấm nút | Yêu cầu rõ của người dùng; Settings vẫn giữ nút "Sync now" làm phương án dự phòng/xác nhận, không phải cơ chế chính |

**Quyết định kỹ thuật đáng chú ý**: `keptICloudSync.ts` viết riêng, không trích xuất module dùng chung với Migraine dù phần lõi (`mergeById`, container path, device id) giống hệt nhau — ưu tiên không đụng code Migraine đang chạy tốt, đúng tinh thần "mỗi app viết business logic riêng" đã áp dụng nhất quán trong factory này. Cân nhắc lại nếu có app thứ 3 cần iCloud sync.

**Việc thủ công người dùng cần làm thêm** (giống hệt bước Migraine đã làm): thêm `UbiquityContainer.swift`/`.m` vào Compile Sources của target Kept, tạo entitlements riêng, bật capability iCloud Documents qua Xcode UI.

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Người dùng tự tạo target Xcode + gán bundle id + build — **không cần** thao tác native module nào từ Claude (MVP không có native module mới, khác Migraine).
- Duplicate-detector và OCR/barcode đã hoãn khỏi MVP có chủ đích (xem bảng tính năng).
- Định vị OCD chưa có bằng chứng giá — rủi ro monetize cần theo dõi sau launch.

## Build order
1. Data model + redux (2 reducer) + storage + `loadAllHistorySaga`.
2. `checkInEngine.ts` + `setCompleteness.ts` + Jest test — chạy thật trước khi làm UI.
3. Core loop: `KeptHomeScreen`/`LogUseScreen`/`DormantItemsScreen` → chạy qua bài kiểm tra hoàn hảo mục 3.2 (5 kịch bản) trước khi sang phần khác.
4. Catalog CRUD.
5. 2 tính năng mồi.
6. `KeptStatsScreen`, `ExportScreen`.
7. `KeptSettingsScreen` (notification thật) + Premium placeholder.
8. Wiring `AppConstant.ts`/theme/navigation, `tsc` diff, `git diff --stat`.

## Verification đã thực hiện
- Jest: `__tests__/checkInEngine.test.ts` — 14/14 test pass thật (computeItemStatus qua 5 kịch bản gồm biên chính xác 90 ngày, computeCostPerUse graceful degradation NaN/Infinity, computeCheckInStreak, computeSetStatus). Toàn bộ suite dự án: 30/30 test logic pass (App.test.tsx fail vì lỗi babel/ESM có sẵn từ trước, không liên quan Kept, không đụng `App.tsx`).
- `tsc --noEmit` chuẩn dự án: 1077 dòng, không đổi so với baseline, 0 dòng nhắc tới "kept". **Đã xác minh thêm bằng tsconfig cách ly** (loại `YogaPlanPro2.ts`/`YogaPlanPro3.ts`, theo mục 6.5 Playbook) — ra 1065 dòng (khác baseline, xác nhận tsc cách ly đang kiểm tra ngữ nghĩa thật), grep "kept" + toàn bộ file dùng chung đã sửa (Theme.js, navigation/index.js, AppConstant.ts, HomeScreen, storage.ts, rootReducer/rootSaga/store) → 0 kết quả, không có lỗi nào liên quan.
- `git diff --stat` trên đúng danh sách file dùng chung đã sửa: chỉ có dòng cộng thêm (317 insertions, 0 deletions) trên 9 file — đúng phạm vi additive theo mục 5 Playbook. (Ghi chú: `ios/project.pbxproj`/`Info.plist` cũng đổi trong lúc làm việc nhưng đó là Xcode tự ghi do người dùng đang thao tác song song, không phải do Claude sửa — không đụng tới các file này.)
- Đã tự chạy qua bài kiểm tra hoàn hảo 5 kịch bản (mục 3.2) cho Daily Check-In: rỗng, dữ liệu tối thiểu (1 món chưa dùng), biên 90 ngày chính xác, món không có giá mua, catalog lớn (FlatList virtualized). Bắt và sửa 1 lỗi tự phát hiện: KeptHomeScreen ban đầu tính "Active" = tổng món trừ dormant — gộp nhầm trạng thái "chưa từng dùng" vào "active", đã sửa dùng `computeItemStatus` tính đúng 3 trạng thái.
- Notification bảo hành: đã wire thật vào `createNotification()`/`cancelNotification()` qua saga (`saveItemNotificationSaga`, `deleteItemNotificationSaga`, `updateSettingsNotificationSaga`) — không phải setting chết, toggle bật/tắt reschedule lại toàn bộ item có `warrantyExpiresAt`.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-07-26 | `KeptHomeScreen` tính số món "Active" = tổng món − dormant, gộp nhầm trạng thái "chưa từng check-in" (`never_used`) vào "active" | Chưa nghĩ tới trạng thái thứ 3 khi viết UI, chỉ nghĩ nhị phân active/dormant dù engine đã có 3 trạng thái | Tính lại bằng `computeItemStatus` cho từng món, đếm đúng status === 'active' | Không cần thêm quy tắc riêng — đã được mục 3.2 (bài kiểm tra hoàn hảo, tự đóng vai người dùng) bắt trước khi bàn giao, không phải bug người dùng phát hiện |
