# careai workspace — tổng quan kiến trúc

> File này là **nguồn sự thật cấp workspace** — mô tả các project độc lập nằm trong thư mục này, quan hệ giữa chúng, và trỏ tới tài liệu chi tiết của từng project. Đây KHÔNG phải chỗ lặp lại nội dung đã có ở tài liệu riêng của từng app — chỉ tóm tắt + tham chiếu.
>
> Thư mục này (`careai/`) không phải 1 git repo duy nhất chứa toàn bộ code — mỗi project bên dưới là **1 git repo độc lập, có remote riêng**. Repo git bọc ngoài (nơi file này sống) chỉ chứa metadata dùng chung: `.claude/` (quy tắc AI dùng chung) + file này. Xem `.claude/APP_BUILD_PLAYBOOK.md` để biết lý do và cách dùng.

## Sơ đồ quan hệ

```
careai/                              ← repo git riêng (chỉ chứa .claude/ + ARCHITECTURE.md), remote: thanhpn/app-md
├── .claude/                         ← quy tắc/kế hoạch dùng chung cho AI khi phát triển bất kỳ project nào ở đây
│   ├── APP_BUILD_PLAYBOOK.md        ← "hiến pháp" riêng cho CareAi (factory app RN) — xem mục 1
│   └── app-plans/                   ← 1 file plan dài hạn / app con trong CareAi factory
│
├── CareAi/                          ← [ĐỘC LẬP] repo riêng: 1MobileApp/CareAi.git
│                                       React Native, ~90+ app di động phát hành qua bundle-id switching
│                                       Không liên quan tới 3 project web bên dưới.
│
├── dvc-api/                         ← [HỆ THỐNG BACKEND] repo riêng: 1MobileApp/app-api.git
│   └── apps/{salon,beverage}/          Backend Go monorepo (microservices), phục vụ salon-web + beverage-web
│                                       Xem dvc-api/docs/ARCHITECTURE.md (chi tiết: iam, gateway, payment...)
│
├── salon-web/     ─┐  [ĐỘC LẬP repo] gọi API qua dvc-api/apps/salon
├── beverage-web/  ─┤  [CHƯA CÓ git]  gọi API qua dvc-api/apps/beverage
├── reviews-web/   ─┘  [CHƯA CÓ git]  gọi API qua dvc-api/apps/reviews
│                    └─ cả 3 đều: Vite + React + TS + Tailwind, VITE_API_BASE_URL trỏ vào dvc-api gateway (localhost:8080 local)
│
├── dvc-worker/                      ← [CHƯA CÓ git] repo riêng dự kiến, độc lập ngôn ngữ với dvc-api (Python/FastAPI, không phải Go)
│                                       Crawler đa nguồn (TMĐT/blog-review/YouTube) sinh dữ liệu + bài viết cho reviews-web.
│                                       Có trang admin quản lý nguồn tin riêng (port 8090 local). Đẩy dữ liệu đã xử lý sang
│                                       dvc-api/apps/reviews qua admin API (chưa build ở milestone đầu — xem dvc-worker/README.md).
│
└── velox-web/                       ← [ĐỘC LẬP, không liên quan gì tới các project trên]
                                        repo riêng: 1MobileApp/velox-web.git
                                        Website giới thiệu công ty phần mềm outsource, tĩnh, không gọi backend nào ở đây
```

## 1. CareAi — App factory di động

- **Repo**: `git@github.com:1MobileApp/CareAi.git` (nhánh `master`)
- **Là gì**: 1 codebase React Native duy nhất tạo ra ~90+ app riêng biệt trên App Store/Play Store, chuyển đổi danh tính qua `bundle ID` (`src/app/common/AppConstant.ts`). Không có backend riêng — mọi dữ liệu lưu cục bộ (AsyncStorage). Kiếm tiền qua AdMob, chưa có IAP thật.
- **Tài liệu chi tiết**: `CareAi/CLAUDE.md` (quy ước code trong repo) + **`.claude/APP_BUILD_PLAYBOOK.md`** ở workspace này (quy trình bắt buộc khi xây/đại tu 1 app trong factory — đọc TOÀN BỘ trước khi động vào CareAi) + `.claude/app-plans/<app-slug>.md` (plan riêng từng app con đã xây).
- Không liên quan kỹ thuật gì tới `dvc-api`/`salon-web`/`beverage-web`/`velox-web`.

## 2. dvc-api + salon-web + beverage-web — Hệ thống backend đa ứng dụng

Đây là **1 hệ thống 3 phần** phối hợp với nhau, không phải 3 project rời rạc:

- **`dvc-api`** (`git@github.com:1MobileApp/app-api.git`, nhánh `main`): backend Golang monorepo (Go workspace), kiến trúc microservices thật — `platform/gateway` (reverse-proxy + rate-limit + CORS, cửa ngõ public duy nhất), `platform/iam` (auth, MongoDB, JWT RS256), `platform/payment`, `platform/fileupload`, `platform/shipping`, và `apps/salon` + `apps/beverage` (business logic riêng từng app, tự khai DB). Chạy qua Docker Compose, public qua Cloudflare Tunnel. **Xem `dvc-api/docs/ARCHITECTURE.md` để biết chi tiết đầy đủ** (data model, token flow, bài học CORS đã gặp, changelog).
- **`salon-web`** (`git@github.com:1MobileApp/salon-web.git`, nhánh `main`): frontend Vite + React + TS + Tailwind cho "Aurée Salon" — demo đặt lịch salon, gọi thật `dvc-api/apps/salon` qua gateway. Xem `salon-web/TASKS.md` cho trạng thái từng tính năng + cách verify.
- **`beverage-web`** (chưa có git repo riêng): frontend Vite + React + TS + Tailwind cho app đặt đồ uống, gọi `dvc-api/apps/beverage` qua gateway.
- **`reviews-web`** (chưa có git repo riêng): frontend Vite + React + TS + Tailwind cho "SoSánhGiá" — website review/so sánh giá sản phẩm + blog + trang quản trị, gọi `dvc-api/apps/reviews` qua gateway. 7 trang công khai (trang chủ, tìm kiếm, danh sách/chi tiết sản phẩm, so sánh, danh sách/chi tiết blog) + admin CRUD 9 loại nội dung. Xem `dvc-api/docs/apps/reviews.md` cho backend, `.env.local` của `reviews-web` cho `VITE_APP_KEY` (tenant riêng, seed qua `platform/iam/cmd/seed-tenant`).
- Cả 3 frontend đọc backend URL qua `.env.local` → `VITE_API_BASE_URL=http://localhost:8080` (local, cần `make up` trong `dvc-api` trước). Production URL còn trống — chờ `dvc-api` xong Cloudflare Tunnel + domain public.

## 3. dvc-worker — Crawler đa nguồn cho reviews-web

- **Repo**: `dvc-worker/` (chưa git-track — tạo repo riêng khi sẵn sàng, giống `beverage-web`/`reviews-web`).
- **Là gì**: service Python/FastAPI hoàn toàn độc lập với `dvc-api` (khác ngôn ngữ, khác DB Postgres riêng port 5433) — crawl dữ liệu sản phẩm/giá (TMĐT), bài viết/review (blog/site so sánh), video (YouTube transcript) để làm nguyên liệu cho `reviews-web`. Kiến trúc generic-first: thêm 1 site nguồn mới là thêm 1 `Source` (cấu hình JSON qua trang admin), không phải viết code mới — trừ khi cần 1 "chiến lược fetch" hoàn toàn mới (xem `dvc-worker/README.md`).
- Có trang quản trị riêng (Jinja2, không phải SPA — cố ý giữ đơn giản) ở `/admin`, port 8090 local, tách biệt hoàn toàn với các trang admin của `salon-web`/`reviews-web`.
- **Trạng thái hiện tại**: crawl + lưu dữ liệu gốc (có đủ quan hệ để sau này ghép "sản phẩm giống nhau giữa nhiều nguồn"/gợi ý tương tự) — ĐÃ nối xong bước đẩy dữ liệu sang `dvc-api/apps/reviews` (nút "Đẩy sang Review" trong trang admin, gọi admin API reviews bằng 1 tài khoản admin riêng seed cho `dvc-worker`, ghi `Offer.source='crawler'`). Job "xào nấu" nội dung bằng LLM (viết lại/tổng hợp bài đánh giá) vẫn CHƯA build — milestone sau. Xem `dvc-worker/README.md`.
- Không chia sẻ code/DB với `dvc-api` — ranh giới service-to-service, sẽ chỉ giao tiếp qua HTTP khi bước đẩy dữ liệu được build.

## 4. velox-web — Website công ty (độc lập)

- **Repo**: `git@github.com:1MobileApp/velox-web.git` (nhánh `main`)
- **Là gì**: website giới thiệu công ty phát triển phần mềm outsource. Vite + React + TS, tĩnh, không gọi API nào trong workspace này. Không chia sẻ code/hạ tầng với 4 project còn lại.

## Cách dùng file `.claude/` dùng chung khi phát triển từng project

- Khi mở **toàn bộ thư mục `careai/`** làm workspace: Claude Code đọc `.claude/` ở đây tự động (hook `UserPromptSubmit` nhắc đọc playbook khi liên quan tới CareAi factory).
- Khi mở **riêng 1 project con** (VD: chỉ mở `dvc-api/` hoặc `salon-web/` trong VSCode/terminal): project đó có 1 `CLAUDE.md` ngắn ở gốc, trỏ tham chiếu tương đối về `../ARCHITECTURE.md` (file này) và — với CareAi — về `../.claude/APP_BUILD_PLAYBOOK.md`, để dev/AI vẫn biết bối cảnh tổng dù không mở workspace cha.
- `.claude/` được git-track riêng (remote `thanhpn/app-md.git`), tách khỏi 5 repo project — sửa quy tắc dùng chung ở đây không ảnh hưởng lịch sử git của từng app, và có thể `git pull` file này về máy khác để đồng bộ quy tắc.

## Changelog

| Ngày | Thay đổi |
|---|---|
| 2026-08-01 | Khởi tạo `ARCHITECTURE.md` + git hoá `.claude/` (remote `thanhpn/app-md.git`), thêm `CLAUDE.md` stub tham chiếu vào từng project con. |
| 2026-08-02 | Thêm `dvc-worker/` (project thứ 6) — crawler đa nguồn Python/FastAPI cho `reviews-web`, độc lập ngôn ngữ với `dvc-api`. |
