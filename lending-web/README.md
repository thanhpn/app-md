# lending-web

Frontend web "Mượn Ngay" — sàn thuê/mượn/xin đồ dùng cá nhân giữa những người dùng gần nhau (không mua bán, không giỏ hàng/thanh toán). Gọi thật backend `dvc-api/apps/lending` qua gateway. Vite + React 19 + TypeScript + Tailwind v4, copy convention `reviews-web` (api client/design system) + `salon-web` (auth).

Xem `.claude/app-plans/muonngay.md` (mục "Web frontend (`lending-web`)") và `dvc-api/docs/srs/lending-platform.md` (FR-1..FR-21) ở workspace gốc để biết đầy đủ bối cảnh sản phẩm/API.

## Chạy local

1. `dvc-api` phải đang chạy (`make up` trong thư mục đó) — tenant `lending` đã được seed sẵn, `app_key` đã có trong `.env.local`:
   ```
   VITE_API_BASE_URL=http://localhost:8080
   VITE_APP_KEY=dgRvUqBeXBeF8PiDBxRaVUvtgP8ktDF7O4A_p0_VZio
   ```
2. `npm install`
3. `npm run dev` — mở `http://localhost:5173`

## Cấu trúc

- `src/lib/api.ts` — fetch client, unwrap envelope `{success,data,error}`, endpoint `platform/iam` (register/login/refresh/logout/getMe) + stub types `Item`/`Interest`/`Rating` (CRUD thật cho `apps/lending` đến W2/W3).
- `src/lib/auth.tsx` — `AuthProvider`/`useAuth`, localStorage `lending_access_token`/`lending_refresh_token`, `withFreshToken` retry-1-lần-khi-401.
- `src/components/ui/` — design system dùng chung (Button/Card/Input/Select/Textarea/Label/Badge), palette: `--color-brand` (cam đất/terracotta) + `--color-accent` (teal, phụ) — xem `src/index.css`.
- `src/pages/` — Home (placeholder W1), Login, Register.

## Trạng thái

**W1 done**: scaffold + design system + api client + auth (login/register/navbar) hoạt động thật với backend đang chạy. Home/Search/ItemDetail/PostItem là W2/W3, chưa xây.

Chưa git-track — tạo repo khi sẵn sàng, theo đúng pattern `reviews-web`/`beverage-web`.
