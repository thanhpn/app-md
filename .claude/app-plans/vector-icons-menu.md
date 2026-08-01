# Chuyển icon menu/settings (HomeSettingScreen) sang vector icon — Plan

> Cross-cutting infra/UI change, không phải 1 app riêng — áp dụng khuôn `_TEMPLATE.md` có lược bớt phần market analysis/monetization.

## Trạng thái
- Ngày bắt đầu: 2026-08-01
- Trạng thái: Đang xây

## Context
36 file `src/app/containers/HomeSettingScreen/*.js` (menu tính năng dùng chung nhiều app) hiển thị icon qua `<Image source={item.icon}>` (component `SettingList`) — icon PNG gom từ nhiều nguồn, độ đồng đều kém. Mục tiêu: chuyển sang vector icon (MaterialCommunityIcons) để nét đều, cùng 1 bộ.

**Phát hiện quan trọng**: `react-native-vector-icons` (đã dùng ở 22 file khác) hiện KHÔNG được link cho iOS — `react-native.config.js` có `platforms: {ios: null}` từ 1 commit "Temp commit"/"WIP" (2025-10-27) chưa từng revert. Xác nhận: `Podfile.lock` không có pod `RNVectorIcons`, `Info.plist` `UIAppFonts` thiếu mọi font icon. Phải sửa trước.

## Data model
Không có type nghiệp vụ mới. Mở rộng `SettingItem` (`src/app/types/index.ts`) thêm 2 field optional: `iconName?: string`, `iconLibrary?: 'MaterialCommunityIcons' | 'Ionicons' | 'FontAwesome5' | 'MaterialIcons' | 'Entypo'`.

## Kiến trúc kỹ thuật
- **Linking iOS**: xoá `platforms: {ios: null}` khỏi `react-native.config.js`; thêm 10 font (`Entypo.ttf`, `EvilIcons.ttf`, `FontAwesome.ttf`, `FontAwesome5_Brands/Regular/Solid.ttf`, `Ionicons.ttf`, `MaterialCommunityIcons.ttf`, `MaterialIcons.ttf`, `SimpleLineIcons.ttf`) vào `ios/CareAi/Info.plist` `UIAppFonts` — sửa luôn bug cho 22 file cũ, không chỉ 36 file mới. Việc bạn tự làm: `cd ios && pod install`.
- **`SettingList`** (`src/app/components/SettingList/index.tsx`): nếu `item.iconName` có → render `Icon` (chọn component theo `iconLibrary`, mặc định MaterialCommunityIcons) thay `<Image>`; không có → giữ nguyên `<Image>` cũ (additive, item chưa migrate không đổi gì).
- **Bảng mapping 42 icon → tên MaterialCommunityIcons**: đã xác thực từng tên tồn tại thật trong `node_modules/react-native-vector-icons/glyphmaps/MaterialCommunityIcons.json` (xem plan file tạm đã duyệt, hoặc `git show` commit này để xem bảng đầy đủ).
- **36 file Menu.js**: chỉ THÊM `iconName: '<tên>'` vào mỗi `SettingItem`, giữ nguyên `icon: Images.xxx` cũ (không xoá — rollback dễ, `Images.xxx` có thể dùng nơi khác).

## Giới hạn đã biết / việc cần người dùng làm thủ công
- `pod install` (không có CocoaPods trong môi trường build này).
- Không thể tự test hiển thị thực tế trên simulator/thiết bị — cần bạn tự xem sau khi `pod install` + rebuild.

## Build order
1. Fix `react-native.config.js` + `Info.plist`.
2. Mở rộng `SettingItem` + `SettingList`.
3. Áp `iconName` vào 36 file theo bảng mapping.
4. `tsc --noEmit`, `git diff --stat`.
5. Cập nhật `APP_BUILD_PLAYBOOK.md`.

## Verification đã thực hiện
- Script Node đối chiếu 118/118 dòng `icon: Images.x` đang hoạt động (loại 3 dòng đã comment) đều có `iconName` đi kèm đúng — chạy thật, không phải lời hứa.
- Toàn bộ 42 tên icon dùng trong bảng mapping đã `grep` xác nhận tồn tại thật trong `node_modules/react-native-vector-icons/glyphmaps/MaterialCommunityIcons.json` của đúng version đang cài trước khi dùng.
- `npx tsc --noEmit -p tsconfig.json`: 0 lỗi mới ở `SettingList/index.tsx`/`types/index.ts`; các lỗi baseline có sẵn ở `HomeSettingScreen/*.js` (Flow-annotation, mục 6.5 Playbook) chỉ lệch số dòng do chèn thêm `iconName`, không phải lỗi mới — xác nhận bằng `diff` giữa tsc output trước/sau, chỉ khác số dòng, không khác nội dung/số lượng lỗi.
- `git diff --stat`: đúng phạm vi kế hoạch (7 file config/component, 28/36 Menu.js có thay đổi thật — 8 file còn lại không có icon nào để đổi).
- **Chưa test được**: hiển thị icon thật trên simulator/thiết bị — cần `pod install` (không có CocoaPods ở môi trường này) rồi rebuild mới xem được.

## Việc còn lại (bạn tự làm)
- `cd ios && pod install` để pod `RNVectorIcons` thực sự được thêm vào project + copy font.
- Rebuild app, tự xem icon hiển thị đúng trên cả iOS/Android trước khi coi là hoàn tất — 1 vài tên icon trong bảng mapping là lựa chọn tốt nhất theo ngữ nghĩa (VD `CapBottle` → `bottle-tonic-outline`) nhưng chưa được xác nhận bằng mắt, có thể cần đổi nếu nhìn không đúng ý.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-01 | `react-native-vector-icons` không link cho iOS, tồn tại từ 2025-10-27 | Commit "Temp commit"/"WIP" tắt autolink iOS để debug tạm, không revert | Xoá override + thêm UIAppFonts | Có — mục 6.9 Playbook (sẽ thêm) |
