# dvc-worker

Crawler + nội dung nguồn cho hệ sinh thái `careai/` — thu thập dữ liệu sản phẩm/giá/bài đánh giá/video từ các trang TMĐT, blog/so sánh, và YouTube, lưu lại có cấu trúc + có quan hệ (để sau này gợi ý sản phẩm tương tự / so sánh giá đa nguồn), rồi **đẩy sang `dvc-api/apps/reviews`** (nút "Đẩy sang Review" trong trang admin) để lên thẳng `reviews-web`. Repo hoàn toàn độc lập với `dvc-api` (khác ngôn ngữ: Python/FastAPI thay vì Go), giao tiếp qua HTTP admin API — không đụng DB của `dvc-api`.

## Vì sao Python (không phải Go như dvc-api)

Quyết định của người dùng: hệ sinh thái crawling/scraping + gọi LLM của Python (httpx, BeautifulSoup, trafilatura, yt-dlp, SDK các LLM) phong phú hơn hẳn Go cho loại việc này. Đây là service độc lập, không chia sẻ code với `dvc-api` — chỉ liên lạc qua HTTP sau này.

## Kiến trúc: generic-first, thêm nguồn = thêm cấu hình

Ý tưởng cốt lõi: **thêm 1 trang web mới không cần code mới**, chỉ cần tạo 1 `Source` (qua trang admin) với `adapter_key` phù hợp + `config` JSON (URL, CSS selector...). Chỉ 3 "chiến lược fetch" khác nhau cần code (`app/adapters/`):

| `adapter_key` | Dùng cho | Cách hoạt động |
|---|---|---|
| `generic_html_product` | Trang sản phẩm TMĐT (chỉ site KHÔNG chặn bot/không cấm crawl trong ToS) | Fetch HTML tĩnh (httpx, không chạy JS) + trích xuất theo CSS selector khai trong `config.selectors` |
| `generic_article` | Blog/trang so sánh/review | Dùng `trafilatura` (thư viện trích xuất nội dung generic, kiểu Readability) — hầu hết layout blog chạy được luôn không cần selector riêng |
| `youtube_channel` | Kênh YouTube | `yt-dlp` liệt kê video gần nhất + `youtube-transcript-api` lấy transcript |
| `shopee_affiliate` | Sản phẩm Shopee (qua kênh chính thức) | Gọi **Shopee Affiliate Open API** (GraphQL, có ký HMAC) — KHÔNG scrape HTML Shopee. Cần tài khoản Shopee Affiliate đã duyệt, xem mục riêng bên dưới. |

**Vì sao không scrape thẳng Shopee**: Shopee chặn bot chủ động và cấm scraping trong Điều khoản dịch vụ — vòng qua biện pháp chặn đó là vấn đề pháp lý/ToS, không phải kỹ thuật, nên `dvc-worker` không có adapter nào làm việc đó. `shopee_affiliate` dùng đúng kênh Shopee cung cấp sẵn cho mục đích so sánh giá/affiliate.

### Ví dụ config từng adapter

**`generic_html_product`** (xem chi tiết + toàn bộ field trong docstring `app/adapters/generic_html_product.py`):
```json
{
  "seed_urls": ["https://shop.example.com/category/dien-thoai"],
  "product_link_selector": "a.product-card",
  "max_items": 50,
  "selectors": {
    "name": "h1.product-title",
    "price": ".price",
    "brand": ".brand",
    "images": "img.gallery-img::attr(src)",
    "category_path": ".breadcrumb"
  },
  "specs_selector": ".specs-table tr"
}
```
`::attr(x)` là cú pháp riêng để lấy attribute thay vì text (VD lấy `src` của `<img>`). Có thể dùng `product_urls: [...]` thay cho `seed_urls`+`product_link_selector` nếu đã biết sẵn danh sách URL sản phẩm.

**`generic_article`**:
```json
{ "seed_urls": ["https://blog.example.com/category/reviews"], "article_link_selector": "a.post-title", "max_items": 30 }
```

**`youtube_channel`**:
```json
{ "channel_url": "https://www.youtube.com/@somechannel/videos", "max_items": 20, "languages": ["vi", "en"] }
```

**`shopee_affiliate`** (chỉ 1 trong 3 field scope bên dưới là bắt buộc):
```json
{ "keyword": "điều hòa", "max_items": 100, "page_size": 20 }
```
```json
{ "shop_id": 123456, "max_items": 50 }
```
App ID/Secret KHÔNG nằm trong config này — xem mục "Shopee Affiliate" bên dưới.

## Shopee Affiliate — kênh dữ liệu Shopee hợp lệ (không scrape)

1. Đăng ký + được duyệt tài khoản tại [Shopee Affiliate Program](https://affiliate.shopee.vn) (Việt Nam) — mỗi thị trường Shopee có chương trình affiliate riêng.
2. Lấy `app_id`/`secret` trong dashboard (mục Open API), điền vào `.env`: `SHOPEE_AFFILIATE_APP_ID`, `SHOPEE_AFFILIATE_SECRET`.
3. Tạo Source với `adapter_key=shopee_affiliate`, config theo ví dụ trên (tìm theo từ khoá hoặc theo shop).
4. Đẩy sang `reviews-web` như bình thường — `Offer.affiliate_url` sẽ dùng đúng `offerLink` (link có gắn theo dõi hoa hồng) chứ không phải link sản phẩm trần, nên click "Tới nơi bán" tính hoa hồng đúng.

**Quan trọng — chưa verify E2E thật**: adapter này dựng theo tài liệu công khai về Shopee Affiliate Open API (schema `productOfferV2`, cách ký `Authorization: SHA256 Credential=...`) vì chưa có tài khoản Shopee Affiliate thật để test. Trước khi bật lịch tự động, hãy tự chạy thử 1 lần qua "Chạy ngay" và đối chiếu field trả về với Open API Explorer trong dashboard Shopee của bạn — tên field/enum (`sortType`, `listType`) Shopee không công bố spec chính thức, có thể lệch giữa các thị trường.

## Đẩy dữ liệu sang reviews-web

Nút **"Đẩy sang Review"** ở mỗi Source kiểu `ecommerce_product` trong trang admin (`/admin/sources`) — nhập tên danh mục đích trên `reviews-web` (tự tạo nếu chưa có), rồi:

1. Get-or-create 1 `Category` (theo tên bạn nhập) và 1 `Retailer` (theo tên Source) bên `apps/reviews`, cache lại `id` vào `sources.reviews_category_id`/`reviews_retailer_id` — lần đẩy sau dùng lại, không tạo trùng.
2. Với mỗi `crawled_products` có giá: tạo mới (lần đầu, set `status=published` ngay) hoặc cập nhật (lần sau, nhận diện qua `pushed_product_id` đã lưu cục bộ) 1 `Product` bên reviews — tên/ảnh/specs/brand.
3. Tạo/cập nhật 1 `Offer` (giá, link gốc = `crawled_products.url`, `source="crawler"`) gắn với retailer ở bước 1.
4. Sản phẩm không có giá bị bỏ qua (báo lỗi rõ ràng trong kết quả, không crash cả lượt đẩy).

Cần seed 1 tài khoản admin RIÊNG cho `dvc-worker` bên `dvc-api` trước (không dùng chung tài khoản người thật):
```bash
# chạy từ thư mục dvc-api, container postgres/mongo của dvc-api đang lên
IAM_MONGO_URI="mongodb://<user>:<pass>@localhost:27017/?authSource=admin" \
IAM_MONGO_DB="iam" \
IAM_JWT_PRIVATE_KEY_PATH="./deploy/secrets/iam/private.pem" \
IAM_JWT_PUBLIC_KEY_PATH="./deploy/secrets/iam/public.pem" \
go run ./platform/iam/cmd/seed-admin --config ./platform/iam/config.yaml \
  --tenant-id <tenant id của reviews, xem GET /api/v1/tenants/resolve?app_key=...> \
  --email worker@dvcworker.local --password '<mật khẩu>' --name "dvc-worker service"
```
Rồi điền `REVIEWS_API_BASE_URL`/`REVIEWS_APP_KEY`/`REVIEWS_ADMIN_EMAIL`/`REVIEWS_ADMIN_PASSWORD` vào `.env` (xem `.env.example`). `REVIEWS_API_BASE_URL` trỏ qua gateway của `dvc-api` giống `reviews-web`, ví dụ `http://host.docker.internal:8080/api/v1/reviews` khi `dvc-worker` chạy trong Docker còn `dvc-api` chạy trên host (macOS/Windows Docker Desktop — Linux cần `--add-host` thay vì `host.docker.internal`).

**Rate limit**: gateway của `dvc-api` giới hạn theo IP (mặc định 240 req/phút, burst 60) — đẩy nhiều sản phẩm cùng lúc tốn tới 4 request/sản phẩm nên `push_service.py` tự giãn cách (~0.8s/sản phẩm) + `ReviewsClient` tự retry-backoff khi gặp `429`. Đẩy lại (re-push) luôn an toàn — idempotent qua `pushed_product_id`, không tạo trùng.

## Chạy local

```bash
docker compose up -d --build   # postgres (port 5433) + worker (port 8090), tự chạy alembic migration lúc start
```
Copy `.env.example` → `.env`, đổi `ADMIN_USERNAME`/`ADMIN_PASSWORD`/`SESSION_SECRET_KEY` trước khi chạy thật (mặc định chỉ để dev).

Trang quản trị: http://localhost:8090/admin (đăng nhập bằng `ADMIN_USERNAME`/`ADMIN_PASSWORD`) — quản lý Nguồn tin (CRUD + "Chạy ngay"), xem Lịch sử crawl, Sản phẩm/Bài viết đã thu thập.

JSON API (`/api/v1/*`, bảo vệ bằng HTTP Basic Auth cùng tài khoản admin) dùng cho script/tích hợp sau này — xem `app/api/*.py`.

## Chạy test

```bash
docker build -t dvc-worker:dev .
docker run --rm dvc-worker:dev pytest -q
```
(Máy host nếu Python 3.12 cài qua Homebrew bị lỗi link `libexpat` — dùng Docker để test/chạy thay vì venv local là cách né vấn đề môi trường đó.)

## Dữ liệu & quan hệ (đã build sẵn cho việc "gợi ý sản phẩm tương tự" sau này)

Theo đúng yêu cầu: bản này **chỉ crawl + lưu dữ liệu gốc**, chưa sinh bài viết ("xào nấu") — nhưng schema đã lưu đủ quan hệ để làm việc đó sau mà không phải đổi cấu trúc:

- `raw_items` — snapshot HTML/transcript gốc mới nhất mỗi URL (để reprocess nếu sửa bug parser mà không cần crawl lại).
- `crawled_products` — sản phẩm đã parse, có `canonical_product_id` (nullable) trỏ tới `canonical_products` — nhóm "đây là cùng 1 sản phẩm thật" giữa nhiều nguồn, gán sau (tay hoặc job matching tự động sau này).
- `crawled_price_history` — 1 dòng mỗi lần giá THỰC SỰ đổi (không phải mỗi lần crawl), giống pattern `apps/reviews.PriceHistory`.
- `related_product_links` — đồ thị quan hệ generic giữa 2 `crawled_products` (`same_product`/`similar`/`accessory`/`alternative`) — nền cho gợi ý sản phẩm tương tự.
- `crawled_content` — review/bài viết/transcript video gốc, có `related_product_id` best-effort nếu adapter xác định được nội dung nói về sản phẩm nào.
- `content_drafts` — hàng đợi rỗng cho job "xào nấu" (LLM rewrite) sau này — `subject_id` trỏ tới `crawled_products`/`canonical_products` (polymorphic, không có FK cứng vì job đó chưa build).

## Phạm vi chưa làm (cố ý, theo đúng yêu cầu build lần này)

- **Job "xào nấu" nội dung bằng LLM** — chỉ có bảng `content_drafts` làm hàng đợi, chưa gọi LLM nào. Khi làm: đọc `crawled_content`/`crawled_products` liên quan qua `related_product_id`/`canonical_product_id`, ghi kết quả vào `content_drafts`.
- **Trang JS nặng (SPA/React storefront)** — `generic_html_product` chỉ fetch HTML tĩnh qua httpx, không chạy JS. Nếu gặp site cần render JS, thêm 1 adapter mới dùng Playwright (chưa cài — cần thêm dependency + browser binary, cố ý bỏ ngoài bản đầu để giữ image nhẹ).
- **Tự động khớp sản phẩm cùng 1 mặt hàng giữa nhiều nguồn** (`related_product_links`/`canonical_product_id`) — bảng đã sẵn, nhưng chưa có job tự động gán (mới gán tay được qua API/DB trực tiếp).
- **Nhận diện currency tự động** — `ParsedProduct.currency` mặc định `"VND"`; nếu 1 site bán bằng ngoại tệ, tạm thời phải sửa tay sau khi crawl hoặc mở rộng selector config (chưa làm, vì mọi nguồn dự kiến ban đầu đều VND).
- **Rate-limit/lịch sự khi CRAWL site nguồn** — chưa có delay giữa các request trong 1 lần crawl (khác với rate-limit khi PUSH sang reviews, đã có — xem mục trên); cần thêm nếu crawl nhiều trang cùng lúc để tránh bị site nguồn chặn IP.
- **1 Source ↔ 1 Category cố định khi đẩy** — chưa hỗ trợ 1 Source có sản phẩm thuộc nhiều category khác nhau bên reviews dù `crawled_products.category_path` đã lưu đủ thông tin phân cấp gốc; hiện toàn bộ sản phẩm của 1 Source đẩy vào cùng 1 Category do admin chọn lúc đẩy.
- **`shopee_affiliate` chưa verify E2E thật** — chưa có tài khoản Shopee Affiliate đã duyệt để test; adapter dựng đúng theo tài liệu công khai (schema `productOfferV2`, cách ký request) nhưng field/enum name (`sortType`/`listType`) Shopee không công bố spec chính thức nên có thể lệch — xem mục "Shopee Affiliate" phía trên trước khi bật chạy tự động.
- Đã verify thật cả 3 adapter đầu + bước đẩy sang reviews, toàn bộ với dữ liệu thật (không mock):
  - `generic_html_product` trỏ vào `books.toscrape.com` (site luyện scraping) và **websosanh.vn/dien-lanh/cat-1867.htm thật** — 44/44 sản phẩm crawl thành công sau khi thêm `product_link_url_pattern` lọc bỏ link quảng cáo (`direct.htm?adsid=...` lẫn trong danh sách, cùng selector với link sản phẩm thật nhưng khác layout trang đích).
  - `generic_article` trỏ vào 1 bài Wikipedia thật, trích xuất đúng tiêu đề + ~26k ký tự nội dung sạch.
  - `youtube_channel` trỏ vào 1 kênh YouTube thật, lấy đúng 2 video + transcript (6.7k–42k ký tự). Trong lúc verify phát hiện + sửa 2 bug thật do 2 dependency đã lỗi thời (`yt-dlp==2024.12.13` không đọc được layout kênh mới của YouTube; `youtube-transcript-api==0.6.3` gọi API cũ đã đổi — cả 2 nâng lên bản mới nhất, `youtube_channel.py` sửa theo API instance-based mới của `youtube-transcript-api` v1.x) — 2 thư viện này đổi theo tốc độ YouTube đổi frontend, cần bump định kỳ nếu adapter đột nhiên trả 0 kết quả.
  - **Đẩy sang reviews**: 44/44 sản phẩm điện lạnh websosanh.vn lên `reviews-web` thật, published, hiện đúng tên/giá/ảnh/specs/"1 nhà bán"/link "Tới nơi bán" — xác nhận qua cả API lẫn Playwright trên frontend thật.
  - Admin UI (login, danh sách nguồn, sản phẩm, lịch sử crawl, form thêm nguồn) verify qua Playwright thật, 0 lỗi console.

## Bài học (đọc trước khi crawl site thật/đẩy số lượng lớn)
- **Selector danh sách có thể khớp cả link quảng cáo** — nhiều site TMĐT chèn sản phẩm tài trợ vào cùng vị trí/class CSS với sản phẩm thật nhưng trỏ URL khác layout (VD `direct.htm` thay vì trang sản phẩm thật). Dùng `product_link_url_pattern` (regex) để lọc, đừng giả định mọi link từ 1 selector đều parse được — adapter đã thiết kế để lỗi từng link không làm hỏng cả lượt chạy, nhưng lọc trước vẫn sạch hơn.
- **"674.547 sản phẩm" hiển thị trên trang không có nghĩa là có 674.547 kết quả thật crawl được** — nhiều site TMĐT phóng đại số đếm cho SEO; số sản phẩm thật load được (kể cả qua API phân trang ẩn phía sau) có thể chỉ bằng số item render sẵn trong HTML tĩnh ban đầu. Xác minh bằng cách thử cuộn/gọi API phân trang thật trước khi giả định "còn nhiều trang nữa".
- **`yt-dlp`/`youtube-transcript-api` lỗi thời rất dễ trả về "thành công nhưng 0 kết quả" thay vì lỗi rõ ràng** — YouTube đổi cấu trúc frontend thường xuyên hơn tốc độ release của các thư viện community. Nếu 1 nguồn YouTube tự nhiên trả `items_found=0, errors_count=0`, nghi ngờ đầu tiên là bump 2 package này lên bản mới nhất trước khi nghi ngờ config sai.
- **`Source.config` rỗng (`{}`) không tự báo lỗi lúc tạo, chỉ báo khi chạy** — form thêm nguồn không validate config theo adapter đã chọn; nếu để trống, lượt chạy đầu tiên sẽ fail với lỗi rõ ràng (`"config has neither ..."`) nhưng chỉ phát hiện được sau khi bấm "Chạy ngay", không phải lúc lưu. Luôn xem `/admin/runs` sau lần chạy đầu của 1 nguồn mới.
- **Selector rộng kiểu `a[href*="/xxx/"]` dễ vơ luôn link chuyên mục lẫn link bài viết thật** nếu 2 loại dùng chung tiền tố URL (VD websosanh: bài viết `/tin-tuc/<slug>-cNN-<id 16 số>.htm`, còn trang chuyên mục chỉ `/tin-tuc/<slug>-cNN.htm`, không có phần ID dài). Luôn kiểm tra mẫu link thật (`curl` + `grep`) trước khi chốt `article_link_url_pattern`/`product_link_url_pattern`, đừng chỉ dựa vào tiền tố path.
