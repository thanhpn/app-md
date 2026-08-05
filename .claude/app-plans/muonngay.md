# Mượn Ngay — nền tảng cho thuê/mượn đồ & chia sẻ đồ từ thiện — Plan

> Xây bằng skill `.claude/skills/build-app/SKILL.md` (nhánh A — CareAi factory). Dự án 2 repo: CareAi (mobile client) + dvc-api (`apps/lending`, backend mới). Phần backend còn có SRS riêng tại `dvc-api/docs/srs/lending-platform.md` (viết ở milestone B1) — file này chỉ giữ trọng tâm sản phẩm/plan tổng, không lặp lại chi tiết kỹ thuật backend đã có ở đó.

## Trạng thái
- Bundle ID (CareAi): `com.careai.muonngay` (đề xuất, chưa publish — tên hiển thị "Mượn Ngay", có thể đổi lúc build)
- Backend: `dvc-api/apps/lending` — **B1-B5 Done** (2026-08-03), đã seed dữ liệu thật (28 item/10 tài khoản/14 quan tâm/17 rating, xem `dvc-api/apps/lending/seed/`)
- Web: `lending-web` (mới, W1-W4, xem mục "Web frontend" bên dưới) — client web song song với mobile CareAi, gọi cùng backend
- Mobile CareAi (M6-M8): chưa build, giữ nguyên trong todo, chưa huỷ
- Ngày bắt đầu: 2026-08-03
- Trạng thái: `Đang xây` — backend xong, web đang bắt đầu W1

## Web frontend (`lending-web`) — sàn web thuê/mượn/tặng đồ

Web app mới, độc lập với mobile CareAi, tham khảo phong cách thị giác `rentzy.vn` (KHÔNG vay cơ chế giao dịch — không giỏ hàng/thanh toán/order-tracking, thay bằng nút "Quan tâm" hiện liên hệ đúng backend B4). Tech stack: Vite+React+TS+Tailwind, copy convention `reviews-web` (api client/design system) + `salon-web` (auth). Chi tiết đầy đủ (kiến trúc, thiết kế từng màn, cấu trúc thư mục) xem plan đã duyệt lúc build — tóm tắt milestone:

| # | Milestone | Trạng thái |
|---|---|---|
| W1 | Scaffold + design system + api client + auth (login/register/navbar) | Done (2026-08-03) |
| W2 | Home (hero+danh mục) + Search (filter bar+grid+phân trang) | Done (2026-08-03) |
| W3 | Item detail (Quan tâm/rating) + Đăng đồ + Đồ của tôi | Done (2026-08-03) |
| W4 | Hồ sơ/rating cá nhân + polish UI | Done (2026-08-03) |

**Verification thật đã chạy**: mỗi milestone build→review→fix (W2: mất vị trí khi bấm danh mục + race condition geolocation; W3: rating bị khoá vĩnh viễn nếu người quan tâm đổi thiết bị/xoá localStorage — chuyển sang để backend là nguồn sự thật thay vì đoán ở client; W4: 3 màu badge chưa migrate token). `npm run build`/`npm run lint` sạch sau mỗi milestone. Chạy dev bằng `cd lending-web && npm run dev` (cần `.env.local` đã có sẵn app-key tenant lending đã seed).

**Việc chưa làm / giới hạn đã biết**: chưa upload ảnh thật qua `platform/fileupload` (PostItem chưa có UI chọn ảnh), chưa git-init `lending-web` (giữ như beverage-web/reviews-web).

## Context
Thay thế cách cho/thuê/mượn đồ dùng cá nhân hiện đang sống rải rác trong nhóm Facebook/Zalo (không biết ai giữ đồ gì, không tìm được đồ gần mình, không có lịch sử/uy tín). Quyết định kiến trúc lớn nhất: đây là **nền tảng thật kết nối nhiều người dùng lạ** (không phải sổ tay cá nhân) — xác nhận qua `AskUserQuestion` — nên cần backend directory mới, khác no-backend mặc định của CareAi. Đây là app factory thứ 2 (sau Rental) có backend thật.

## Tính năng lõi (đã qua bài kiểm tra sắc bén mục 9.1)
Tìm đồ cần thuê/mượn/xin **gần bạn** + liên hệ trực tiếp người đăng. (3/4 — neo giá yếu, thị trường VN chưa có tiền lệ trả phí rõ ràng cho việc này, nhưng Fat Llama là bằng chứng ở thị trường khác; chấp nhận rủi ro monetize, xem Monetization bên dưới).

## Quyết định thu hẹp scope (để khả thi 1 dev solo)
- Không xử lý thanh toán trong app — chỉ là directory/matching, giao dịch tiền/đặt cọc offline giữa 2 bên.
- Không chat realtime — MVP chỉ "Quan tâm" → hiện SĐT/Zalo người đăng.
- Không dùng `react-native-maps` (chưa có trong CareAi, tránh đụng pbxproj/Gradle dùng chung) — hiển thị kết quả dạng list sắp theo khoảng cách, dùng `@react-native-community/geolocation` đã có sẵn.
- Không PostGIS — Haversine SQL thuần trên cột `lat/lng` phẳng (tiền lệ `apps/beverage`).

## Bảng tính năng cuối cùng
| Nhóm | Chức năng | Ghi chú |
|---|---|---|
| Lõi | Tìm đồ gần bạn (bán kính, lọc loại/danh mục) | Haversine, không map |
| Lõi | Liên hệ người đăng ("Quan tâm" → hiện contact) | Không chat realtime |
| Mồi | Feed đồ từ thiện gần bạn ngay khi mở app | Dùng được <30s, không cần đăng gì |
| Mồi | Đăng nhanh 1 món đồ (3 field + ảnh) | Viral/shareable |
| Hỗ trợ | Đăng ký/đăng nhập (bắt buộc) | Copy pattern Salon |
| Hỗ trợ | Quản lý "Đồ của tôi" (sửa/xoá/đánh dấu đã cho) | |
| Hỗ trợ | Rating sau giao dịch | Chỉ khi item đã `given_out` |
| Hỗ trợ | Cài đặt (bán kính tìm kiếm, đăng xuất) | |

## Data model
Backend (`apps/lending`, Postgres — chi tiết SQL đầy đủ trong SRS doc):
```
items(id, owner_user_id, title, description, category, type[lend_free|rent_paid|donate],
      rental_price_note?, lat, lng, address_label, photo_keys[], status[available|reserved|given_out],
      created_at, updated_at)
interests(id, item_id, interested_user_id, contact_revealed_at, created_at)
ratings(id, item_id, rater_user_id, rated_user_id, score 1-5, comment?, created_at)
```
Mobile: mirror trực tiếp response backend (không tách history/persist reducer như Rental — dữ liệu thuộc server, local chỉ cache trang hiện tại).

## Kiến trúc kỹ thuật
- Backend: skeleton copy `apps/rental` (Postgres, JWT verify-only qua `platform/iam`, gateway 1-dòng, `platform/fileupload` cho ảnh).
- Mobile: HTTP client copy hình dạng `rentalApiClient.ts`/`rentalAuth.ts` (Keychain service riêng `lending_auth`), UI đăng nhập/gating copy pattern **Salon** (`SalonRegisterScreen`/`getSalonIsLoggedIn`) — không phải Rental (Rental's auth UI chưa từng wire).
- 7 điểm `AppConstant.ts` copy mẫu `RENTAL_BUNDLE_ID`.

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|
| Đăng ký/Đăng nhập | Bắt buộc trước khi dùng | `SalonRegisterScreen` |
| Home (feed gần bạn + feed từ thiện) | Tính năng mồi, entry chính | — |
| Tìm kiếm/bộ lọc | Tính năng lõi | — |
| Đăng đồ | Tính năng mồi | — |
| Đồ của tôi | Hỗ trợ, quản lý | — |
| Chi tiết đồ + Quan tâm | Tính năng lõi (liên hệ) | — |
| Rating | Hỗ trợ | — |
| Hồ sơ/Lịch sử | Hỗ trợ | — |
| Cài đặt | Hỗ trợ | — |

## Monetization
Chưa monetize ở MVP (rủi ro market chưa kiểm chứng — xem tính năng lõi). Nếu sau này thêm, khả năng: phí niêm yết nổi bật hoặc hoa hồng khi có bằng chứng người dùng thật sẵn sàng trả — không giả vờ có trước khi kiểm chứng.

## Giới hạn đã biết / việc cần làm thủ công
- Base URL API cần tự sửa theo platform (giống Rental).
- Cần `make up` trong `dvc-api` (Postgres + fileupload/MinIO) trước khi test mobile.
- Chưa xây thanh toán, chat realtime, bản đồ — xem quyết định scope.

## Build order (= milestone, xem trạng thái từng cái ở bảng dưới)
1. B1 — SRS + schema + skeleton service + gateway + health check
2. B2 — CRUD món đồ + ảnh (fileupload)
3. B3 — Tìm kiếm bán kính (Haversine) + lọc + phân trang
4. B4 — "Quan tâm" → contact + ghi nhận
5. B5 — Rating sau giao dịch
6. M6 — CareAi scaffold + auth bắt buộc + Home feed
7. M7 — Đăng đồ + Đồ của tôi
8. M8 — Chi tiết + Quan tâm + Rating + Hồ sơ + Cài đặt

## Verification đã thực hiện
(chưa có — chưa build milestone nào)

---

## Changelog & Lessons Learned
| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| | | | | |
