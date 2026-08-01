# Aurée Salon (mobile) — Plan

> Copy từ plan đã duyệt qua Plan Mode ngày 2026-07-28. Xem `.claude/APP_BUILD_PLAYBOOK.md` cho quy tắc dùng chung — file này chỉ ghi thứ riêng của app này.

## Trạng thái
- Bundle ID: `com.careai.salon`
- Ngày bắt đầu: 2026-07-28
- Trạng thái: `Đang xây`

## Context
App mobile cho hệ thống đặt lịch salon tóc đã có backend (`dvc-api`) + web (`salon-web`) ở dự án riêng `/Users/thanhpn/Documents/careai/dvc-api` và `/Users/thanhpn/Documents/careai/salon-web`. Đây là **ngoại lệ có chủ đích** với triết lý "không backend, chỉ local" của CareAi — người dùng đã được hỏi rõ về xung đột này (qua `AskUserQuestion`) và chọn vẫn tích hợp vào CareAi. Không phải app phát hành đại trà kiếm tiền qua AdMob — là business tool thật cho khách hàng salon, chỉ làm phần khách hàng (không có dashboard quản trị trên mobile).

## Bảng tính năng cuối cùng (đã qua bước phản biện)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|
| Lõi | Đặt lịch chọn nhân viên + xem slot trống thật | JTBD: "muốn xem đúng giờ trống thật của nhân viên tôi thích và đặt ngay, không phải gọi điện hay bị trùng lịch" — backend đã chứng minh (conflict-check thật, verify ở M9 `dvc-api`) |
| Mồi (<30s, không cần tài khoản) | Xem danh sách dịch vụ + giá | Gọi thẳng `GET /api/v1/salon/services` (public) |
| Hỗ trợ | Đăng nhập/Đăng ký | `SalonLoginScreen`/`SalonRegisterScreen` riêng, KHÔNG tái dùng `AuthLoginScreen`/`redux/user` (đang trỏ backend khác của app khác) |
| Hỗ trợ | Tài khoản + lịch sử booking + trạng thái thanh toán | `SalonAccountScreen` |

## Data model
```ts
// src/app/containers/Salon/types.ts — khớp response backend, xem salon-web/src/lib/api.ts đối chiếu
export type SalonService = { id: string; name: string; description?: string; duration_min: number; price_cents: number; currency: string; image_url?: string };
export type Staff = { id: string; full_name: string; phone?: string; email?: string; avatar_url?: string; active: boolean };
export type TimeSlot = { start: string; end: string };
export type Booking = {
  id: string; service_id: string; staff_id?: string; duration_min: number;
  price_cents: number; currency: string; scheduled_at: string; status: string; note?: string;
  payment_status: 'unpaid' | 'paid'; payment_method?: string; paid_amount_cents?: number; paid_at?: string;
  created_at: string;
};
export type SalonAccount = { id: string; email: string; phone?: string; full_name?: string; roles: string[]; status: string };
export type TokenPair = { access_token: string; refresh_token: string; expires_in: number; token_type: string };
```

## Kiến trúc kỹ thuật
- **Network**: `fetch` thuần (không thêm axios/react-query — chưa có tiền lệ trong CareAi). `src/app/services/SalonAPI.ts` — service module mirror `ArticleAPI.ts`/`LotteryAPI.ts`, 1 hàm `request()` helper base URL + parse envelope `{success,data,error}`.
- **Redux slice**: `src/redux/salon/` (types/actions/reducer/selector/saga) — pattern REQUEST/SUCCESS/FAILURE + `isLoading`, copy khuôn `redux/lottery/`. KHÔNG có `historyReducer.ts` (server là nguồn sự thật, không cần shard local time-series như rental/migraine — xem lý do đầy đủ trong plan đã duyệt).
- **Whitelist persist**: chỉ `token`/`refreshToken`/`isLoggedIn`/`account` trong `redux/salon` — KHÔNG whitelist cache services/staff/bookings (refetch khi mở app).
- **Base URL**: hằng số 1 chỗ trong `SalonAPI.ts`, tự đổi tay theo môi trường test (simulator/emulator/máy thật).
- **Route naming**: tiền tố `Salon*` để tránh trùng `APP_ROUTER` (Rental đã chiếm `BookingsScreen`/`CreateBookingScreen`/`RecordPaymentScreen`).

## Danh sách màn hình
| Màn hình | Vai trò | Cần đăng nhập | Mẫu tham khảo |
|---|---|---|---|
| `SalonHomeScreen` | Hero + CTA, mount tab Trang chủ | Không | `RentalHomeScreen` |
| `SalonServicesScreen` | Danh sách dịch vụ + giá | Không | style theo `salon-web/Services.tsx` |
| `SalonLoginScreen`/`SalonRegisterScreen` | Đăng nhập/đăng ký | — | `AuthLoginScreen`/`AuthSignup` (copy layout, không copy backend URL) |
| `SalonBookingScreen` | Chọn dịch vụ → nhân viên (optional) → ngày → slot trống thật → xác nhận | Có | `salon-web/Booking.tsx` |
| `SalonAccountScreen` | Tài khoản + lịch sử + trạng thái thanh toán | Có | `salon-web/Account.tsx` |

Tab bar: Trang chủ / Dịch vụ / Đặt lịch / Tài khoản.

## Monetization
Không áp dụng — không phải app AdMob/Premium giả của factory, là business tool thật.

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Base URL API phải tự đổi tay theo môi trường test (không có `.env` kiểu Vite trong RN).
- Cần `docker compose up` (dvc-api) chạy trước khi test mobile.
- Không có dashboard quản trị trên mobile (chỉ phía khách hàng).
- Token lưu qua `redux-persist` thường (giống `redux/user`), chưa dùng `react-native-keychain` dù đã có sẵn trong deps.

## Build order
1. Wiring nền tảng (7 điểm `AppConstant.ts`, `salonThemes`, route constants, `redux/salon` skeleton chỉ auth, root wiring, `SalonAPI.ts` auth functions) — verify: build simulator không crash.
2. Auth thật (Login/Register gọi `dvc-api` thật) — verify: tạo tài khoản thật, thấy trong Mongo.
3. Dịch vụ + Trang chủ thật — verify: hiện đúng 6 dịch vụ seed.
4. Đặt lịch chọn nhân viên + slot trống thật — verify: booking thật trong Mongo, trùng giờ bị chặn đúng.
5. Tài khoản + lịch sử — verify: booking mới hiện đúng.
6. Đánh bóng theo checklist §2.4 playbook.

## Verification đã thực hiện
(Cập nhật sau mỗi milestone thật.)

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| | | | | |
