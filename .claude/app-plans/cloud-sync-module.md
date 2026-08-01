# Module iCloud Sync dùng chung (cross-app infra) — Plan

> Không phải 1 app tiêu dùng — đây là 1 module hạ tầng dùng chung cho nhiều app trong factory (Migraine, Kept, và mọi app tương lai có dữ liệu đáng giữ lâu dài). Áp dụng khuôn `_TEMPLATE.md` có lược bớt phần không liên quan (market analysis, monetization, danh sách màn hình).

## Trạng thái
- Ngày bắt đầu: 2026-08-01
- Trạng thái: Đang xây (refactor Migraine + Kept dùng chung module, chưa test native thật)

## Context
Mọi app trong factory chỉ lưu dữ liệu AsyncStorage cục bộ — mất dữ liệu khi đổi máy/xoá app. Đã có 2 implementation iCloud sync trùng lặp gần như y hệt (Migraine: `src/app/services/iCloudSync.ts`, Kept: `src/app/services/keptICloudSync.ts`), cùng dựa trên native bridge dùng chung `ios/CareAi/UbiquityContainer.swift` (đã generic, nhưng CHƯA add vào Compile Sources của bất kỳ target nào — tính năng chưa chạy thật cho ai). Mục tiêu: gộp phần logic không phụ thuộc app cụ thể thành 1 module lõi generic, để (a) Migraine/Kept dùng chung không trùng lặp code, (b) mọi app tương lai wire vào chỉ trong vài dòng thay vì copy-paste ~150 dòng mỗi lần.

Quyết định đã hỏi & được duyệt (xem hội thoại 2026-08-01):
1. Refactor Migraine + Kept dùng chung module ngay (an toàn vì native chưa live cho ai — rủi ro hồi quy = 0).
2. Nâng Migraine lên auto-sync giống Kept (thay đổi hành vi thật đã duyệt).
3. Đưa việc wire cloud-sync thành bước MẶC ĐỊNH cho app mới có dữ liệu người dùng đáng giữ (cập nhật Playbook mục 5).

## Data model
Không có type mới — module hoạt động generic trên `{id: string}[]` bất kỳ do app truyền vào, kèm hàm `timeOf(item)` để biết field nào là mốc thời gian merge (`updatedAt ?? createdAt`).

## Kiến trúc kỹ thuật
- **Module lõi** (mới): `src/app/services/cloudSync.ts` — `isCloudSyncAvailable()`, `getOrCreateDeviceId(storageKey)`, `mergeById<T>(local, remote, timeOf)`, `syncCollections<TSnapshot>(appKey, local)`. Dùng lại native `UbiquityContainer` (không đổi) + `saveToStorage`/`loadFromStorage` (`src/app/utils/storage.ts`, không đổi).
- **Wrapper mỏng giữ nguyên API cũ**: `iCloudSync.ts` (Migraine), `keptICloudSync.ts` (Kept) — gọi `syncCollections` bên trong, export lại đúng tên/shape cũ (`isICloudAvailable`, `syncNow`, `SyncOutcome`, `isKeptICloudAvailable`, `syncKeptNow`, `KeptSyncOutcome`). Không nơi gọi nào cần sửa.
- **Hook generic** (mới): `src/app/hooks/useAutoCloudSync.ts` — trích từ `useKeptAutoSync.ts` (throttle 60s module-level, ref latest state, chạy lúc mount + AppState active). `useKeptAutoSync.ts` refactor thành wrapper của hook này (giữ tên/cách gọi). **File mới** `useMigraineAutoSync.ts` cùng factory, mount vào `MigraineHomeScreen/index.tsx` (mirror `KeptHomeScreen`).
- **Cố ý không đụng**: `MigraineSettings.icloudSyncEnabled` là field chết (khai báo, mặc định `false`, không nơi nào đọc để gate sync) — giữ nguyên hành vi hiện tại (không gate), ghi vào Changelog làm known issue.

## Giới hạn đã biết / việc cần người dùng làm thủ công
Với MỖI app muốn bật thật: add `UbiquityContainer.swift` vào Compile Sources của target đó + tạo entitlements riêng + bật capability "iCloud > iCloud Documents" qua Xcode UI (không tự động hoá được — mục 6.1/6.2 Playbook). Chưa test sync thật giữa 2 thiết bị (cần bước Xcode ở trên trước).

## Build order
1. `src/app/services/cloudSync.ts` (module lõi) + Jest test cho `mergeById`.
2. Refactor `iCloudSync.ts`, `keptICloudSync.ts` thành wrapper — verify export/shape không đổi.
3. `useAutoCloudSync.ts` + refactor `useKeptAutoSync.ts`.
4. `useMigraineAutoSync.ts` + mount vào `MigraineHomeScreen`.
5. Cập nhật `APP_BUILD_PLAYBOOK.md` mục 5/6.3/7.
6. `tsc --noEmit` + `yarn jest` + `git diff --stat`.

## Verification đã thực hiện
- **Jest**: `npx jest cloudSync.test.ts` — 5/5 test pass thật (`mergeById`: local-only giữ nguyên, remote-only được thêm, local mới hơn thắng, remote mới hơn thắng, merge độc lập nhiều id cùng lúc). `mergeById` được tách sang file thuần riêng `cloudSyncMerge.ts` (không import `react-native`/`react-native-fs`) vì import RNFS ở module-scope khiến Jest fail parse (`react-native-fs/FS.common.js` dùng cú pháp Flow không được transform theo `jest.config.js` hiện tại của repo — phát hiện thật khi chạy, không phải suy đoán).
- **`tsc --noEmit -p tsconfig.json`**: 0 lỗi mới ở mọi file đã sửa/tạo (`cloudSync.ts`, `cloudSyncMerge.ts`, `useAutoCloudSync.ts`, `useMigraineAutoSync.ts`, `iCloudSync.ts`, `keptICloudSync.ts`, `useKeptAutoSync.ts`, `MigraineHomeScreen/index.tsx`) — xác nhận bằng `grep` tên các file này trong output, không xuất hiện. Toàn bộ ~1077 dòng lỗi còn lại trong output thuộc file hỏng cú pháp có sẵn từ trước (`app-asset/description/diary.ts`, `YogaPlanPro2/3.ts`, các `.js` Flow-annotation dưới `HomeSettingScreen/`) — đúng giới hạn đã ghi ở Playbook mục 6.5, không phải lỗi do thay đổi lần này.
- **Đối chiếu API cũ/mới bằng mắt**: `isICloudAvailable`, `syncNow`, `SyncOutcome`, `isKeptICloudAvailable`, `syncKeptNow`, `KeptSyncOutcome` giữ nguyên tên + shape — `MigraineSettingsScreen/index.tsx` (nút "Sync now" thủ công) và `KeptHomeScreen/index.tsx` không cần sửa gì.
- **`git diff --stat`**: đúng phạm vi kế hoạch — 4 file sửa (`MigraineHomeScreen/index.tsx` +3 dòng mount hook, `useKeptAutoSync.ts`/`iCloudSync.ts`/`keptICloudSync.ts` co gọn thành wrapper), 5 file mới (`cloudSync.ts`, `cloudSyncMerge.ts`, `useAutoCloudSync.ts`, `useMigraineAutoSync.ts`, `__tests__/cloudSync.test.ts`). Không đụng `project.pbxproj`/entitlements (2 file này có thay đổi trong working tree nhưng là việc dở dang có sẵn từ trước phiên này, không phải do task này).
- **Chưa test được**: sync thật giữa 2 thiết bị — cần người dùng tự làm bước Xcode thủ công trước (xem mục "Giới hạn đã biết" bên dưới), chưa thể verify tự động.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-01 | `MigraineSettings.icloudSyncEnabled` là field chết, không gate gì | Khai báo lúc thiết kế type ban đầu nhưng chưa từng wire vào logic sync | Chưa sửa — cố ý giữ nguyên trong lần refactor này (out of scope), ghi lại làm known issue | Chưa — cần quyết định xoá field hay wire thật thành toggle trước khi thêm rule |
