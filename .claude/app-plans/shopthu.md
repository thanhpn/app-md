# ShopThử — Mock Shopping / Order Simulator — Plan

## Trạng thái
- Bundle ID: `com.careai.shopthu`
- Ngày bắt đầu: 2026-07-27
- Trạng thái: `MVP hoàn thành` (chưa build/run thật trên simulator — người dùng tự tạo target Xcode + gán bundle id)

## Lưu ý triển khai khác với plan ban đầu
- **Free/Premium**: bảng tính năng gắn nhãn vòng lặp đặt hàng là "Lõi (Premium, 4/4)" nhưng mục Free/Premium lại liệt kê toàn bộ luồng đặt hàng là free — đã triển khai theo mục Free/Premium (đúng hơn về sản phẩm: khoá cả core loop sẽ giết chết giá trị app cho free user). Premium chỉ gate bộ sưu tập độc quyền/Flash Sale không giới hạn/export PDF.
- **Tab "Trang chủ"**: KHÔNG tạo `SHOPTHU_HOME_STACK` riêng — dùng đúng tab `HOME_STACK` dùng chung toàn factory (gate `isShopThuApp` trong `HomeScreen/index.tsx`, giống hệt pattern `KeptHomeScreen`). ShopThu chỉ thêm 2 tab riêng: Đơn hàng (`SHOPTHU_ORDERS_STACK`) + Cài đặt (`SHOPTHU_SETTINGS_STACK`).
- **Ảnh sản phẩm**: dùng LoremFlickr (`loremflickr.com/{w}/{h}/{keyword}?lock=N`) — CDN thật, không cần API key, ảnh khớp theo từ khoá danh mục (skincare/gadget/pet...), khác với đề xuất Unsplash/Pexels ban đầu vì Unsplash Source (endpoint không cần key) đã bị khai tử — LoremFlickr là lựa chọn tương đương còn hoạt động.

## Context
Người dùng muốn 1 app "thương mại điện tử" đầy đủ như Shopee (duyệt sản phẩm, đặt hàng, nhận hàng) nhưng **không có giao dịch thật** — mục đích là xả cơn thèm bấm "Mua ngay" mà không tốn tiền. Đây là app mới trong CareAi App Factory, theo đúng quy trình `.claude/APP_BUILD_PLAYBOOK.md`. Đã hoàn thành Bước 1-3 của Playbook (nghiên cứu, tự phản biện, trình bày + 2 câu hỏi lớn qua `AskUserQuestion`), người dùng đã chọn:
- **Ảnh sản phẩm**: ảnh minh hoạ miễn phí bản quyền (Unsplash/Pexels), chọn khớp danh mục — không hotlink ảnh thật từ sàn TMĐT (rủi ro bản quyền/nhãn hiệu + hotlink có thể bị chặn), không dùng emoji-only (mất cảm giác "lướt Shopee thật").
- **Định vị/giọng điệu**: giải trí nhẹ nhàng "xả cơn thèm mua sắm" — KHÔNG dùng ngôn ngữ y tế ("nghiện", "rối loạn mua sắm", "cai nghiện").

Đã nghiên cứu xu hướng sản phẩm thật (TikTok Shop, Amazon Most Wished For 2026) để làm nền catalog: dụng cụ làm đẹp/skincare, gadget nhà thông minh, phụ kiện thú cưng, pin sạc/loa mini, đồ chơi/novelty — đúng nhóm hàng "mua theo cảm hứng".

## Phân tích thị trường (tóm tắt)
Shopee/TikTok Shop/Temu là nguyên nhân gây thèm mua, không phải đối thủ. App wishlist (Pinterest, Keep) chỉ dừng ở "lưu lại" — không tái tạo vòng cảm xúc chờ đợi → nhận hàng → unbox. Khoảng trống: kỹ thuật trị liệu thật ("bỏ giỏ, chờ 24-48h") cho thấy chính **nghi thức mua sắm** (ritual) mới gây nghiện, không phải quyền sở hữu — app này tái tạo trọn nghi thức đó miễn phí, an toàn.

## Bảng tính năng cuối cùng (đã qua tự phản biện, mục 9.1 Playbook)
| Nhóm | Tính năng | Ghi chú |
|---|---|---|
| **Lõi (Premium, 4/4)** | **Vòng lặp đặt hàng trọn vẹn**: Duyệt → Giỏ → "Thanh toán" giả → timeline giao hàng nhiều mốc (local notification thật) → Unbox/ăn mừng → tự vào "Đã nhận" | JTBD: *"Khi tôi thèm bấm Mua Ngay, tôi muốn trải qua trọn vòng đặt-chờ-nhận mà không tốn tiền, để cơn thèm được thoả mãn."* Rủi ro tự nhận: chưa có tiền lệ giá thị trường cho đúng loại trải nghiệm này (giống canh bạc định vị OCD của Kept) — chấp nhận, không đầu tư quá tay ngoài MVP tới khi có dữ liệu retention |
| Mồi (free, <30s) | **Lướt Ngay** — swipe kiểu Tinder qua sản phẩm trending, like = lưu wishlist | Dùng ngay lần mở đầu tiên, không cần dữ liệu |
| Mồi (free, <30s) | **Săn Sale Chớp Nhoáng** — carousel đếm ngược giả lập trên Home | Cảm giác khẩn cấp tức thì |
| Hỗ trợ | Catalog: danh mục, tìm kiếm, lọc (giá/sao/danh mục), sort (Phổ biến/Mới/Bán chạy/Giá) | Client-side filter thuần trên mảng tĩnh |
| Hỗ trợ | Chi tiết sản phẩm: ảnh, mô tả, review giả seed sẵn, biến thể màu/size | |
| Hỗ trợ | Giỏ hàng, "Thanh toán" (chọn địa chỉ/phương thức giả, không có SDK thanh toán thật) | |
| Hỗ trợ | Theo dõi đơn (danh sách + timeline trạng thái từng đơn) | |
| Hỗ trợ | "Đã nhận" — gallery các đơn đã unbox | |
| Hỗ trợ | Wishlist board + thẻ chia sẻ (snapshot) | Tái dùng `react-native-view-shot`+`react-native-share` đã có trong Rental/Kept |
| Hỗ trợ | Bộ đếm "Tiền đã không tiêu" | Đóng khung tích cực, không phán xét |
| Hỗ trợ (Premium placeholder) | Bộ sưu tập độc quyền, không giới hạn lượt xem Flash Sale/ngày, export báo cáo "đã không tiêu" | Placeholder tĩnh — KHÔNG IAP thật (mục 6.4 Playbook) |

**Free/Premium**: Free = toàn bộ CRUD/duyệt/giỏ/đặt hàng/timeline/2 tính năng mồi + counter. Premium (placeholder tĩnh, nút "Sắp ra mắt") = bộ sưu tập độc quyền + Flash Sale không giới hạn + export PDF.

## Data model
```ts
// src/app/types/shopthu.ts
type ProductCategory = 'beauty'|'home_gadget'|'fashion'|'electronics'|'pet'|'kitchen'|'toys'|'sports';

interface ProductReview { id: string; author: string; rating: 1|2|3|4|5; comment: string; createdAt: string; }
interface ProductVariant { id: string; label: string; }
interface Product {
  id: string; name: string; category: ProductCategory; tags: ('trending'|'new'|'bestseller')[];
  price: number; originalPrice?: number; currency: 'VND';
  rating: number; soldCount: number; imageUrl: string; images: string[];
  description: string; variants?: ProductVariant[]; reviews: ProductReview[];
}

interface CartItem { productId: string; variantId?: string; quantity: number; addedAt: string; updatedAt: string; }

type OrderStatus = 'confirmed'|'shipped'|'out_for_delivery'|'delivered'|'cancelled';
interface OrderStatusEvent { status: OrderStatus; at: string; }
interface OrderLine { productId: string; variantId?: string; quantity: number; priceAtOrder: number; }
interface Order {
  id: string; lines: OrderLine[]; totalAmount: number;
  fakeAddress: string; fakePaymentMethod: 'cod'|'card_demo'|'ewallet_demo';
  statusHistory: OrderStatusEvent[]; currentStatus: OrderStatus;
  shippedAt: string; outForDeliveryAt: string; deliveredAt: string; // mốc precompute lúc tạo đơn
  unboxed: boolean; createdAt: string; updatedAt: string;
}

interface WishlistItem { productId: string; savedAt: string; }
interface ShopThuSettings { planTier: 'free'|'premium'; notificationsEnabled: boolean; moneyNotSpentTotal: number; }
```

## Kiến trúc kỹ thuật

**Catalog sản phẩm — JSON tĩnh, KHÔNG qua Redux/AsyncStorage** (đúng yêu cầu người dùng "dữ liệu lưu JSON, update được về sau"):
- `src/app/common/shopthu/data/{beauty,home_gadget,fashion,electronics,pet,kitchen,toys,sports}.json` — mỗi file 1 mảng `Product[]` theo đúng category, ~15-20 sản phẩm/file (tổng ~120-140 sản phẩm), seed từ xu hướng thật đã research (TikTok Shop/Amazon Most Wished For 2026) + review giả hợp lý.
- `src/app/common/shopthu/catalog.ts` — `import beauty from './data/beauty.json'; ...; export const ALL_PRODUCTS: Product[] = [...beauty, ...homeGadget, ...];` — copy đúng convention "1 domain file → 1 exported const array, import thẳng vào screen" đã dùng cho `PetArticles.ts`/`WorkoutArticles.ts` (khác ở chỗ dùng `.json` thay vì `.ts` literal vì người dùng cần sửa nội dung không đụng code). `tsconfig.json` kế thừa `@react-native/typescript-config` — cần xác nhận `resolveJsonModule` bật sẵn (verify ở Milestone 1, nếu chưa thì thêm vào `tsconfig.json` — additive, an toàn).
- Ảnh: mỗi category có 8-12 URL ảnh Unsplash/Pexels thật (CDN trực tiếp, không cần API key) chọn khớp chủ đề, cycle qua các sản phẩm cùng category để đa dạng — chốt danh sách URL cụ thể lúc build Milestone 1.

**Redux — 5-file slice, tách reducer đúng pattern Kept/Migraine** (`src/redux/shopthu/{types,actions,reducer,selector,saga}.ts`):
- `shopthuReducer` (whitelist trong `store.ts`): `cart: CartItem[]`, `wishlist: WishlistItem[]`, `activeOrders: Order[]` (đơn chưa `delivered`/`cancelled` — số lượng nhỏ, bounded), `settings: ShopThuSettings`.
- `shopthuHistoryReducer` (KHÔNG whitelist — pattern mục 4.2 Playbook, vì đơn hàng tích luỹ nhiều năm giống attack log): `ordersByMonth: Record<string, Order[]>` cho đơn đã `delivered`/`cancelled`, rehydrate qua `loadAllShopThuHistorySaga` dùng `AsyncStorage.getAllKeys()` + prefix `shopthu_orders_` (copy đúng `getAllKeptMonths`/`getAllMigraineMonths` trong `src/app/utils/storage.ts`).
- Khi đơn chuyển sang `delivered`/`cancelled`: saga di chuyển record từ `activeOrders` sang file tháng tương ứng (`localMonthOf(order.createdAt)` từ `dateHelpers.ts`, KHÔNG slice ISO string — mục 4.4).

**Order timeline engine (thuần, test Jest)** — `src/app/common/shopthu/orderTimelineEngine.ts`:
```ts
export const SHIPPED_OFFSET_HOURS = 3;
export const OUT_FOR_DELIVERY_OFFSET_HOURS = 20;
export const DELIVERED_OFFSET_HOURS = 28;
export function computeOrderTimestamps(createdAt: string) { /* trả về shippedAt/outForDeliveryAt/deliveredAt bằng dayjs(createdAt).add(...) */ }
export function computeCurrentStatus(order: Order, now: string): OrderStatus { /* so sánh now với 3 mốc, pure function */ }
```
Tại thời điểm tạo đơn: precompute 3 mốc, lưu vào `Order`, schedule 2 local notification thật qua `createNotification()` (pattern `pet/saga.ts`): 1 lúc `shippedAt` ("Đơn đã giao cho vận chuyển 📦"), 1 lúc `deliveredAt` ("Đơn đã đến — bấm để unbox 🎉"). Nếu huỷ đơn: `cancelNotification()` cả 2 id (id dạng `shopthu-order-${orderId}-shipped`/`-delivered`). Mỗi lần mở `OrderTrackingListScreen`/app foreground: gọi `computeCurrentStatus` cho từng active order để hiển thị đúng trạng thái ngay cả khi notification bị miss.

**Money-not-spent counter**: `settings.moneyNotSpentTotal` cộng dồn `totalAmount` mỗi khi đơn chuyển `delivered` (không cộng khi `cancelled`) — tính trong saga, 1 nơi duy nhất.

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|
| `ShopThuHomeScreen` | Flash sale carousel + entry Lướt Ngay + danh mục + grid trending | `KeptHomeScreen` pattern, render trong `HomeScreen/index.tsx` qua `isShopThuApp` |
| `ShopThuCategoryScreen`/`ShopThuSearchScreen` | Duyệt theo danh mục + tìm kiếm/lọc/sort | List→Detail chuẩn |
| `ShopThuProductDetailScreen` | Ảnh, mô tả, review, chọn biến thể, "Thêm giỏ"/"Mua ngay" | — |
| `ShopThuCartScreen` | Giỏ hàng, chỉnh số lượng | — |
| `ShopThuCheckoutScreen` | Chọn địa chỉ/phương thức giả, xác nhận | — |
| `ShopThuOrderTrackingListScreen`/`ShopThuOrderDetailScreen` | Danh sách đơn + timeline trạng thái | `KeptDormantItemsScreen` (list+trạng thái) |
| `ShopThuUnboxingScreen` | Ăn mừng khi đơn `delivered`, CTA "Cất vào Đã nhận" | — |
| `ShopThuReceivedGalleryScreen` | Gallery đơn đã unbox | — |
| `ShopThuSwipeDeckScreen` | Tính năng mồi "Lướt Ngay" | — |
| `ShopThuWishlistScreen`/`ShopThuSnapshotShareScreen` | Wishlist board + thẻ chia sẻ | `KeptSnapshotCardScreen` |
| `ShopThuSettingsScreen` | Thông báo, "Tiền đã không tiêu", backup/restore | `KeptSettingsScreen` |
| `ShopThuUpgradePremiumScreen` | Placeholder tĩnh | `KeptUpgradePremiumScreen` |

## Wiring vào app-factory (7 điểm AppConstant + navigation + theme + home + redux — mục 5 Playbook)
- `AppConstant.ts`: thêm `SHOPTHU_BUNDLE_ID = 'com.careai.shopthu'`, `getAppId/getAppName/getHomeIcon` case, `isShopThuApp` export — copy đúng vị trí/pattern của `KEPT_BUNDLE_ID` (L78, L175, L341, L662, L1167 theo báo cáo Explore).
- `navigation/index.js` + `constants.js`: 3 tab-stack (Trang chủ/Đơn hàng/Cài đặt) theo pattern `KeptItemsStack`/`KeptInsightsStack`/`KeptSettingsStack`; toàn bộ route đặt tiền tố `ShopThu`/`SHOPTHU_` (grep trùng tên trước khi thêm).
- `Theme.js`: thêm `shopthuThemes` (màu cam/hồng ấm áp — tâm lý học phù hợp "vui vẻ, xả stress", không dùng lại palette app khác), thêm case đầu `getTheme()`.
- `HomeScreen/index.tsx`: thêm `{isShopThuApp && <ShopThuHomeScreen theme={theme} />}`.
- `rootReducer.ts`/`store.ts`/`rootSaga.ts`: thêm `shopthu`+`shopthuHistory` reducer, whitelist chỉ `shopthu`, fork `watchShopThu()`.

## Giới hạn đã biết / việc cần người dùng làm thủ công
- Người dùng tự tạo target Xcode + gán bundle id + build (không cần native module mới, MVP không đụng pbxproj/entitlements).
- Chưa xác nhận `resolveJsonModule` trong tsconfig — verify + bật ở Milestone 1 nếu thiếu.
- Danh sách URL ảnh Unsplash/Pexels cụ thể cho từng danh mục sẽ chốt lúc code Milestone 1 (cần vài phút chọn ảnh thật khớp chủ đề, không tự bịa URL).
- Core loop chưa có tiền lệ giá thị trường (rủi ro monetize) — theo dõi sau khi có dữ liệu dùng thật, giống cảnh báo đã ghi ở Kept.

## Build order
1. Data model (`types/shopthu.ts`) + catalog JSON (8 file category, ~120-140 sản phẩm thật từ research trend) + `catalog.ts` — verify `resolveJsonModule`.
2. Redux 2-reducer (`shopthu`/`shopthuHistory`) + storage sharding (`storage.ts` thêm `shopthu_orders_` prefix) + `orderTimelineEngine.ts` — viết Jest test trước khi làm UI (biên chính xác 3 mốc giờ, huỷ đơn, chuyển sang history đúng tháng theo `localMonthOf`).
3. Core loop UI: Home → Category/Search → ProductDetail → Cart → Checkout → OrderTracking → Unboxing → ReceivedGallery — chạy bài kiểm tra hoàn hảo mục 3.2 Playbook (giỏ rỗng, 1 đơn, nhiều đơn cùng lúc, đơn huỷ, catalog lớn scroll) trước khi sang phần khác.
4. 2 tính năng mồi: Swipe Deck, Flash Sale carousel trên Home.
5. Wishlist board + Snapshot share.
6. Settings (notification thật + counter "Tiền đã không tiêu" + backup/restore) + Premium placeholder.
7. Wiring `AppConstant.ts`/`Theme.js`/navigation/`HomeScreen` + `git diff --stat` xác nhận additive-only trên file dùng chung.

## Verification đã thực hiện (sau build)
- **Jest**: `__tests__/orderTimelineEngine.test.ts` — 11/11 test pass thật (3 mốc giờ chính xác, biên inclusive tại từng mốc, ở lại `delivered` mãi mãi kể cả mở app 30 ngày sau, `cancelled` không bao giờ đổi trạng thái dù qua mốc delivered). Toàn bộ suite dự án: 87/87 test logic pass (`App.test.tsx` fail vì lỗi babel/ESM có sẵn từ trước — đúng lỗi đã ghi nhận trong `kept-belongings-tracker.md`, không liên quan ShopThu, không đụng `App.tsx`).
- **`tsc --noEmit -p tsconfig.json`**: 1077 dòng, KHÔNG đổi so với baseline, 0 dòng nhắc tới "shopthu" — chạy lại sau mỗi milestone (1,2,3,4,5,6,7), luôn sạch.
- **Xác minh thêm bằng tsconfig cách ly** (mục 6.5 Playbook, `allowJs:false` + loại `YogaPlanPro1/2/3.ts`): phát hiện lỗi `navigation.navigate(...)` "not assignable to type never" trên toàn bộ file ShopThu — nhưng đối chiếu chéo với `KeptItemListScreen.tsx` (code đã ship, đã duyệt) dưới CÙNG cấu hình cách ly cho thấy Kept cũng bị lỗi y hệt → xác nhận đây là artefact của việc loại bỏ hết `.js` (làm mất `RootParamList` suy ra từ `navigation/index.js`), không phải bug thật trong code ShopThu. Bài học này áp dụng đúng cảnh báo ở mục 6.5 Playbook, không cần thêm quy tắc mới.
- **`git diff --stat`** trên 9 file dùng chung đã sửa (`AppConstant.ts`, `Theme.js`, `HomeScreen/index.tsx`, `navigation/constants.js`, `navigation/index.js`, `utils/storage.ts`, `rootReducer.ts`, `rootSaga.ts`, `store.ts`): **306 insertions, 0 deletions** — đúng additive-only theo mục 5 Playbook.
- Đã tự rà lại 5 kịch bản cho vòng lặp đặt hàng: giỏ rỗng (EmptyState + CTA về Home), 1 đơn đang giao, nhiều đơn cùng lúc (Order Tracking List), đơn bị huỷ (giữ nguyên trạng thái `cancelled` vĩnh viễn qua `computeCurrentStatus`), và mở app sau khi đơn đã "đến" nhiều ngày (status vẫn đúng nhờ pure function, không phụ thuộc notification có bắn hay không).
- **Chưa test trên simulator/device thật** (môi trường này không chạy được Metro/Xcode) — toàn bộ verification ở trên là static (typecheck + unit test), KHÔNG phải xác nhận UI thật chạy đúng. Người dùng cần tự build thử trên simulator trước khi coi màn hình là "đã đánh bóng xong" theo mục 3.2 Playbook.

---

## Changelog & Lessons Learned
| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| | | | | |
