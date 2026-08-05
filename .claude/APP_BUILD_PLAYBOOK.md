# App Build Playbook — CareAi App Factory

**Đọc file này TOÀN BỘ trước khi bắt đầu bất kỳ yêu cầu nào liên quan đến xây dựng app mới hoặc đại tu app hiện có trong dự án này.** File này là "hiến pháp" cho mọi lần xây app trong factory này. Đừng bỏ qua bước nào để tiết kiệm thời gian — mỗi bước ở đây tồn tại vì đã từng có hậu quả thật khi bỏ qua.

---

## 0. Bối cảnh dự án (đọc trước khi làm bất cứ điều gì)

Đây **không phải** một app đơn — đây là một **nhà máy app** (app factory): một codebase React Native duy nhất tạo ra ~90+ app riêng biệt trên App Store/Play Store, chuyển đổi danh tính qua `bundle ID`.

- **Công tắc trung tâm**: `src/app/common/AppConstant.ts` — đọc `DeviceInfo.getBundleId()`, từ đó suy ra hằng số `is<Ten>App`, tên app, icon, ngôn ngữ mặc định, đơn vị tiền tệ, AdMob unit ID...
- **1 project Xcode / 1 `project.pbxproj` dùng chung cho toàn bộ ~90 target.** Không có product flavor cho Android theo app — `applicationId` được đổi tay trước mỗi lần build.
- **Toàn bộ portfolio hiện tại kiếm tiền qua AdMob.** Chưa có IAP/subscription thật (`react-native-iap`, RevenueCat) ở bất kỳ đâu — mọi app "Premium" trong factory này đến giờ đều là **placeholder tĩnh** ("Sắp ra mắt"), không xử lý thanh toán thật.
- Không có backend/server riêng của app-maker — mọi thứ lưu **cục bộ trên máy** (AsyncStorage). Đây là lợi thế cạnh tranh có chủ đích (xem mục 3) — đừng phá vỡ nó bằng cách thêm cloud sync tùy tiện.

Nếu chưa từng thấy file `AppConstant.ts`, `src/app/navigation/index.js`, `src/app/common/Theme.js` — hãy đọc chúng trước (dùng Explore agent nếu project lớn) để hiểu pattern hiện có trước khi tự sáng tác pattern mới.

---

## 1. Quy trình bắt buộc khi nhận yêu cầu xây app mới

Làm đúng thứ tự. Đừng nhảy thẳng vào code.

### Bước 1 — Nghiên cứu & tự đề xuất yêu cầu (draft)
- Nếu người dùng đưa "bằng chứng" (số liệu review, insight thị trường...) — tận dụng nó, đừng nghiên cứu lại từ đầu.
- Kiểm tra xem bundle id / app đã có sẵn trong `AppConstant.ts` chưa (đã từng có trường hợp bundle id được đặt trước nhưng chưa xây gì — coi đó là slate sạch).
- Kiểm tra xem có app tương tự đã tồn tại trong factory chưa (tránh trùng lặp, hoặc học pattern tái dùng được).
- Tự phác thảo: đối thủ cạnh tranh, khoảng trống thị trường, bảng tính năng, data model sơ bộ, danh sách màn hình.
- **Đây phải là phân tích sâu, không phải liệt kê wishlist.** Mỗi tính năng trong bản phác thảo phải trả lời được: ai cần nó, cần bao thường xuyên, và vì sao không tự làm bằng Notes/Excel/app free trong 5 phút. Xem tiêu chuẩn chi tiết ở **mục 9**. Danh sách tính năng không xếp hạng theo giá trị (giống kiểu brainstorm liệt kê hết mọi ý tưởng) là dấu hiệu phân tích chưa đủ sâu.

### Bước 2 — Tự phản biện (BẮT BUỘC, đừng bỏ qua)
Trước khi trình bày cho người dùng, tự viết ra **ít nhất 3-5 điểm phản biện** nhắm vào chính bản phác thảo của mình. Đây không phải thủ tục hình thức — đây là bước tạo ra chất lượng. Các góc phản biện bắt buộc phải cân nhắc:

| Góc phản biện | Câu hỏi tự vấn |
|---|---|
| Scope creep | Tính năng nào là "nice to have" đang được ngụy trang thành "cần thiết"? Cắt được gì mà không mất giá trị lõi? |
| Khả thi kỹ thuật trong codebase NÀY | Có cần backend không có sẵn? Có cần native module mới không (xem mục 6)? Có đụng vào file dùng chung (pbxproj, entitlements) không? |
| Tính thực tế của monetization | Free tier có đang cho không thứ lẽ ra nên trả phí không? Premium có gate đúng vào tính năng tạo giá trị lõi không, hay chỉ giới hạn số lượng vô nghĩa? |
| Khác biệt hoá thật sự | Nếu bỏ tính năng "thông minh/phân tích" đi, app này có khác gì hàng chục app CRUD khác trong Play Store không? |
| Rủi ro y tế/pháp lý/riêng tư (nếu có) | Có tuyên bố nào cần ngôn ngữ "liên quan đến" thay vì "gây ra" không? Có ngưỡng dữ liệu tối thiểu trước khi hiển thị insight không? |
| Tính lâu dài của dữ liệu | Data model có tính đến việc dùng NHIỀU NĂM không bị chậm không (xem mục 5.3)? |

Ngoài bảng trên, chạy **bài kiểm tra sắc bén** (mục 9.1) cho từng tính năng trong bản phác thảo trước khi đưa vào bảng cuối cùng — tính năng nào không qua được thì cắt hoặc hạ xuống "có thể làm sau", không đưa vào MVP.

Từ bảng phản biện này, **viết lại thành yêu cầu cuối cùng đã tinh chỉnh** — đây mới là thứ trình bày cho người dùng, không phải bản nháp ban đầu. Yêu cầu cuối cùng phải đạt tiêu chuẩn chính xác ở mục 9.2 (không mơ hồ, đo/test được) trước khi đưa vào Plan Mode.

### Bước 3 — Trình bày & hỏi những quyết định lớn không thể tự quyết
Trình bày phân tích thị trường + bảng tính năng đã tinh chỉnh. Nếu có quyết định kiến trúc lớn, không thể đảo ngược dễ dàng, hoặc cần hành động ngoài phạm vi code (ví dụ: bật iCloud capability cần tài khoản Apple Developer của người dùng) — dùng `AskUserQuestion` để hỏi rõ, đừng tự đoán.

### Bước 4 — Vào Plan Mode, viết plan chi tiết
Dùng `EnterPlanMode`. Trong lúc plan mode, hệ thống chỉ cho phép ghi vào **1 file plan tạm** do hệ thống chỉ định (thường ở `~/.claude/plans/<random-name>.md`) — đây là giới hạn cứng của công cụ, không né được. Viết plan đầy đủ vào đó theo cấu trúc:
- **Context**: vì sao xây app này, vấn đề nó giải quyết
- **Bảng tính năng cuối cùng** (đã qua bước phản biện)
- **Data model** (TypeScript interfaces)
- **Kiến trúc kỹ thuật**: redux slice, storage strategy, statistical/business logic engine nếu có
- **Danh sách màn hình** kèm mô tả + màn hình nào là template tham khảo
- **Build order theo milestone** (mỗi milestone phải cho ra thứ test được)
- **Rủi ro/giới hạn đã biết** (native module cần tay người dùng, monetization chưa thật, v.v.)
- **Verification plan**

Gọi `ExitPlanMode` để xin duyệt. **Không viết code trước khi được duyệt.**

### Bước 5 — Ngay sau khi được duyệt: lưu plan vào project (KHÔNG chỉ để ở file tạm)
File tạm ở `~/.claude/plans/` **bị ghi đè** ở lần plan-mode tiếp theo (đã xảy ra thật trong session trước — 3 app khác nhau ghi đè cùng 1 file). Ngay sau `ExitPlanMode` được duyệt, **bước đầu tiên trước khi code** là copy nội dung plan đã duyệt vào:

```
.claude/app-plans/<app-slug>.md
```

(dùng file `.claude/app-plans/_TEMPLATE.md` làm khuôn mẫu cấu trúc). File này được **git-track**, tồn tại lâu dài, và là nơi cập nhật khi sản phẩm cải tiến hoặc khi phát hiện làm sai (xem mục 7).

### Bước 6 — Build theo milestone, verify liên tục
- Dùng `TodoWrite` theo dõi milestone.
- Sau **mỗi milestone**: chạy `npx tsc --noEmit -p tsconfig.json`, so sánh số dòng lỗi với baseline hiện tại — nhưng đọc kỹ mục 6.5 trước khi tin tưởng tuyệt đối vào kết quả này.
- Với logic nghiệp vụ quan trọng (tính toán, thống kê, ngưỡng cảnh báo...) — viết Jest unit test thật, chạy thật, không chỉ tuyên bố "đã test".
- Cuối cùng: `git status`/`git diff --stat` xác nhận phạm vi thay đổi đúng như plan — không đụng file ngoài phạm vi (đặc biệt các file dùng chung).

### Bước 7 — Tổng kết
Báo cáo ngắn gọn: đã xây gì, đã verify bằng cách nào (cụ thể, không chung chung), việc gì còn cần người dùng làm thủ công (nếu có).

---

## 2. Nguyên tắc thiết kế (Apple-tier, premium)

- **Mỗi app có theme màu RIÊNG** trong `Theme.js`, không tái dùng palette app khác. Chọn màu theo tâm lý học phù hợp domain (VD: xanh dương/lavender dịu cho app y tế đau mãn tính, cam san hô ấm cho app thú cưng, xanh dương tài chính cho app quản lý tiền).
- **Hệ thống spacing nhất quán**: 4/8/12/15/20/24px. Border radius card: 10-16px.
- **Phân cấp typography rõ ràng**: tiêu đề 20-28px bold, nội dung 14-16px, meta/caption 11-13px.
- **Empty state không bao giờ để trống trơn** — luôn có icon/emoji + copy thân thiện + CTA hành động tiếp theo.
- **Pattern List → Detail → Create/Edit** cho mọi entity CRUD, nhất quán xuyên suốt app.
- **Dashboard/tab "Hôm nay" luôn dẫn đầu bằng hành động chính** (nút lớn, nổi bật) — không chôn hành động quan trọng nhất trong menu.
- **Progressive disclosure** cho màn hình nhiều dữ liệu: tóm tắt trước, chi tiết khi tap vào.
- **Không có setting "chết"** — trước khi coi 1 màn hình cài đặt là xong, kiểm tra lại: mỗi toggle/field có thực sự gây ra hiệu ứng nào đó không? (Bài học thật: Migraine app từng có "giờ nhắc nhật ký" lưu được nhưng không có gì lên lịch — không phát hiện ra cho tới khi review lại.)
- **Không cần tài sản hình ảnh mới nếu không có sẵn** — dùng emoji làm icon (rẻ, đủ đẹp, không cần thiết kế) hoặc tái dùng icon có sẵn trong `Images.js`. Không tự bịa đường dẫn ảnh chưa tồn tại.

### 2.1 Sang trọng đến từ TIẾT CHẾ, không phải nhồi nhét
- Tối đa **1 màu chủ đạo + 1 màu nhấn + thang trung tính** cho mỗi app. Không quá 3 màu "nổi bật" xuất hiện cùng lúc trên 1 màn hình — nhiều màu sặc sỡ trông rẻ tiền, không phải sinh động.
- Whitespace là công cụ thiết kế, không phải chỗ trống lãng phí cần lấp đầy. Thà 1 màn hình có ít nội dung, thoáng, dễ quét mắt — còn hơn nhồi đủ thứ vào "cho đỡ phí màn hình".
- Số liệu (tiền, chỉ số, %) luôn format nhất quán qua **1 helper dùng chung duy nhất** cho cả app (kiểu `formatVND`/`localDateOf` đã có) — không tự format rải rác từng màn hình, dễ lệch nhau (thừa/thiếu số 0, sai đơn vị).

### 2.2 Giọng điệu nhất quán xuyên suốt
- Toàn bộ copy trong 1 app dùng **1 giọng điệu duy nhất** phù hợp domain (ấm áp/đồng cảm cho app sức khỏe, gọn/đáng tin cho app tài chính...) — không trộn văn phong trang trọng và đùa giỡn trong cùng 1 app.
- Thông báo lỗi/rỗng/thành công **không dùng ngôn ngữ kỹ thuật khô khan** ("Error", "No data", "Success") — viết lại bằng giọng của app, luôn kèm gợi ý hành động tiếp theo thay vì chỉ báo trạng thái.

### 2.3 Chi tiết nhỏ tạo cảm giác cao cấp
- Mọi hành động lưu/xoá/gửi phải có **phản hồi tức thời** (đổi trạng thái nút, animation nhẹ, chuyển màn hình mượt) — người dùng không bao giờ được để trong trạng thái "không chắc thao tác đã ăn chưa".
- Mỗi màn hình chỉ có **đúng 1 CTA nổi bật nhất** (nút primary, màu đặc); hành động phụ dùng style nhạt hơn (outline/text). Tránh cảnh nhiều nút to bằng nhau gây rối mắt, không rõ hành động chính là gì.
- Icon/emoji dùng **nhất quán 1 hệ thống** trong toàn app — nếu chọn emoji làm icon, dùng emoji cho MỌI nơi cùng cấp độ (VD: toàn bộ icon loại nhật ký), không trộn tuỳ tiện với icon vector có sẵn trên cùng nhóm UI.

### 2.4 Checklist đánh bóng UI trước khi coi 1 màn hình "xong"
- [ ] Đúng 1 CTA nổi bật nhất trên màn hình
- [ ] Không quá 3 màu nổi bật cùng lúc
- [ ] Số liệu format qua đúng 1 helper dùng chung, không tự viết rải rác
- [ ] Mọi trạng thái rỗng có copy riêng theo giọng app, không phải text kỹ thuật mặc định
- [ ] Đã tự dùng thử luồng chính trên kích thước màn hình nhỏ nhất được hỗ trợ — không vỡ layout, không chữ bị cắt

---

## 3. Nguyên tắc định vị sản phẩm

- Đọc review 1-2-3 sao của đối thủ trực tiếp trước khi thiết kế tính năng — khoảng trống thị trường thường nằm ở đó, không phải ở tính năng đối thủ đã làm tốt.
- **"Không cần tài khoản, dữ liệu không rời khỏi máy"** là lợi thế cạnh tranh thật với nhóm app sức khỏe/tài chính cá nhân (người dùng ghét bị ép tạo tài khoản + đẩy dữ liệu nhạy cảm lên cloud của hãng). Đừng vô tình phá vỡ lợi thế này bằng cách thêm cloud sync lên server riêng — nếu cần đồng bộ đa thiết bị, ưu tiên **iCloud/Google Drive của chính người dùng** (xem mục 6.3), không phải server của app-maker.
- **Premium nên gate vào tính năng tạo giá trị lõi** (insight/phân tích/export chuyên nghiệp), không phải giới hạn số lượng bản ghi vô nghĩa.

### 3.1 Phân tầng tính năng: Lõi (1) → Mồi (2-4) → Hỗ trợ (còn lại)
Mọi app nên có đúng **1 tính năng lõi** (core) — sâu, hẹp, backing bởi logic minh bạch test được (VD: correlation engine của Migraine, anomaly detection của PetCare) — đây là lý do người dùng trả phí. Luôn tự hỏi: bỏ tính năng này đi thì app còn gì khác với 10 app CRUD tương tự? Nếu câu trả lời là "không còn gì" — đúng, đó chính là mục đích.

Xung quanh tính năng lõi là **2-4 tính năng mồi** (xem 3.3) và phần còn lại là **tính năng hỗ trợ** (CRUD, cài đặt) — cần thiết để tính năng lõi vận hành được nhưng KHÔNG phải điểm bán hàng, không cần đầu tư đánh bóng ngang tính năng lõi.

### 3.2 Tính năng lõi phải HOÀN HẢO trước khi chuyển sang tính năng khác
Tính năng lõi chạy được lần đầu ("hoạt động") và tính năng lõi **hoàn hảo** ("đáng để trả tiền") là 2 mức khác nhau — milestone build chỉ tính là xong ở mức thứ hai. Quy trình đánh bóng bắt buộc, làm ngay sau khi tính năng lõi chạy được, TRƯỚC KHI chuyển sang màn hình/tính năng tiếp theo:

1. **Tự đóng vai người dùng thật**, chạy qua tối thiểu 5 kịch bản thực tế khác nhau: dữ liệu trống, dữ liệu tối thiểu, dữ liệu cực đoan/dị thường, và nếu có bối cảnh áp lực (VD: đang lên cơn đau, đang vội) — mô phỏng đúng bối cảnh đó. Ghi lại MỌI điểm khó chịu/mơ hồ/thiếu sót, không bỏ qua vì "nhỏ".
2. **Sửa hết danh sách đó** trước khi coi milestone xong — không để "tạm ổn" cho tính năng lõi, vì đây là phần duy nhất người dùng đánh giá "app này có đáng tiền không".
3. **Bài kiểm tra hoàn hảo** — phải trả lời YES cho cả 5 câu:
   - Kết quả có **tự giải thích** được không, hay cần người dùng đọc hướng dẫn riêng?
   - Có **degrade gracefully** khi thiếu dữ liệu không (không crash, không hiện số vô nghĩa, có trạng thái "cần thêm dữ liệu" rõ ràng thay vì im lặng hoặc lỗi)?
   - Tốc độ/số bước thao tác có đúng như đã cam kết trong JTBD không (VD: nếu hứa "10 giây" — đã tự bấm giờ thật chưa, hay chỉ ước lượng)?
   - Nếu liên quan số liệu/thống kê — có hiện **số liệu gốc minh bạch**, không chỉ 1 kết luận đóng hộp không giải thích được?
   - Có ít nhất **1 khoảnh khắc "aha"** — thứ người dùng không tự nhận ra nếu không có tính năng này?

### 3.3 Tính năng mồi (hook features) — thứ khiến ai cũng muốn dùng
Khác tính năng lõi (sâu, hẹp, cần tích luỹ dữ liệu, thường trả phí), tính năng mồi có đặc điểm ngược lại: **miễn phí, dùng được ngay trong <30 giây kể từ lúc mở app lần đầu, không cần setup hay dữ liệu lịch sử, và hấp dẫn đối tượng RỘNG hơn** người thật sự cần tính năng lõi. Mục đích không phải kiếm tiền trực tiếp mà là:
- Cho lý do mở app dù hôm đó chưa cần dùng tính năng lõi (duy trì thói quen).
- Dễ chia sẻ/khoe (screenshot-worthy) — kênh lan truyền tự nhiên.
- Chứng minh giá trị ngay từ phút đầu, trước khi người dùng mới kịp tích luỹ đủ dữ liệu để tính năng lõi phát huy.

VD đã áp dụng trong factory này: BCS calculator + thẻ nhận diện thú cưng của PetCare (dùng được ngay lần đầu mở app, không cần đã log gì trước đó), bảng thực phẩm/cây độc hại (tra cứu tức thời, hữu ích cả với người không dùng tính năng log hàng ngày).

---

## 4. Data model & Redux — pattern đã kiểm chứng

### 4.1 Cấu trúc slice 5 file
`src/redux/<app>/{types,actions,reducer,selector,saga}.ts` — copy nguyên xi cấu trúc từ `src/redux/rental/` hoặc `src/redux/migraine/` làm mẫu.

### 4.2 Tách "state nhỏ, cần persist" khỏi "cache lớn, không nên persist"
**Bài học quan trọng nhất về hiệu năng dài hạn**: `redux-persist` lưu TOÀN BỘ state của mỗi reducer đã whitelist thành 1 blob duy nhất trong AsyncStorage. Nếu để dữ liệu time-series (log hàng ngày, hàng năm) nằm trong reducer đã whitelist, blob này phình to vô hạn theo thời gian dùng — chậm dần mỗi lần mở app.

**Quy tắc**: chia làm 2 reducer riêng:
- `<app>Reducer` (VD: `migraine`) — chỉ chứa state nhỏ, bounded (settings, danh mục thuốc, medications...) → **whitelist trong `store.ts`**.
- `<app>HistoryReducer` (VD: `migraineHistory`) — chứa mảng dữ liệu đã flatten từ file tháng (rehydrate mỗi lần mở app từ AsyncStorage file, không phải nguồn sự thật) → **KHÔNG whitelist**.

Xem `src/redux/migraine/reducer.ts` + `src/redux/migraine/historyReducer.ts` làm mẫu chính xác, kèm comment giải thích lý do ngay trong code.

### 4.3 Lưu trữ time-series: sharding theo tháng
Dữ liệu log hàng ngày/hàng cơn (attack, meter reading, pet log...) → lưu file JSON riêng theo tháng trong AsyncStorage (`<prefix>_${YYYY-MM}.json`), KHÔNG dồn vào 1 file/mảng khổng lồ. Cache trong bộ nhớ (module-level object trong `saga.ts`) để tránh đọc lại file không cần thiết. Dùng `AsyncStorage.getAllKeys()` + filter prefix để tự động phát hiện các tháng đã có dữ liệu khi cần load toàn bộ lịch sử (xem `getAllMigraineMonths` trong `storage.ts`).

### 4.4 QUY TẮC NGÀY GIỜ — bug đã thực sự xảy ra, đừng lặp lại
**Không bao giờ** dùng `isoString.slice(0, 10)` hoặc `.slice(0, 7)` trên timestamp ISO UTC để suy ra "ngày/tháng nào" theo góc nhìn người dùng. `startAt` lưu dạng `dayjs().toISOString()` (UTC) — cắt chuỗi trực tiếp cho ra ngày UTC, KHÔNG PHẢI ngày địa phương của người dùng. Với người dùng lệch múi giờ (kể cả UTC+7 — đã tự bắt được bug này khi sandbox test chạy ở Asia/Saigon), 1 sự kiện lúc nửa đêm địa phương có thể bị tính sai hẳn 1 ngày/tháng.

**Luôn dùng helper `dayjs(isoString).format('YYYY-MM-DD')`** (xem `src/app/common/migraine/dateHelpers.ts` — copy pattern này cho app mới nếu cần). Áp dụng nhất quán ở MỌI nơi: sharding file theo tháng, lọc theo khoảng ngày, group theo tháng cho biểu đồ, engine phân tích tương quan.

Khi so sánh 1 "ngày tham chiếu" (VD: `referenceDate` cho tính lạm dụng thuốc) với timestamp thật — so sánh theo **toàn bộ ngày** (`.startOf('day')` / `.endOf('day')`), không so trực tiếp với `dayjs(referenceDate)` (mặc định = nửa đêm), nếu không mọi sự kiện xảy ra sau đó trong cùng ngày sẽ bị loại nhầm là "trong tương lai".

### 4.5 Trường `updatedAt` là bắt buộc trên mọi entity có thể chỉnh sửa
Nếu entity có thể sync đa thiết bị (kể cả trong tương lai) hoặc cần merge — PHẢI có `updatedAt`, set lại **mỗi lần lưu** (kể cả khi edit, không chỉ khi tạo mới). Thiếu field này khiến logic merge "ai mới hơn thắng" không thể hoạt động đúng (đã xảy ra thật với `Medication` trong Migraine app).

---

## 5. Wiring vào hệ thống app-factory (7 điểm trong `AppConstant.ts`)

Khi thêm app mới, sửa đúng các điểm sau (dùng bundle id của app khác làm mẫu tham chiếu trực tiếp trong code):

1. Hằng số bundle id (`export const X_BUNDLE_ID = '...'`)
2. `getAppId()` — case trả App Store numeric ID (để `''` nếu chưa publish)
3. `getAppName()` — case trả tên hiển thị
4. `getAppIcon()` — case trả URL icon marketing (có thể để trống, có fallback)
5. `getHomeIcon()` — case trả icon tab bar (tái dùng `Images.js` có sẵn nếu hợp lý)
6. `export const is<Ten>App = bundleId === X_BUNDLE_ID;`
7. `getDefaultCurrency()` / `getDefaultLanguage()` — chỉ thêm case nếu khác default (`vi`/VND hoặc `en`/USD tùy thị trường mục tiêu)

Sau đó:
- **Theme**: thêm block theme riêng trong `Theme.js`, thêm `case is<Ten>App: return <ten>Themes;` vào `getTheme()`.
- **Navigation**: thêm import screens + `is<Ten>App` vào `navigation/index.js`, tạo stack riêng cho mỗi tab (copy pattern `PropertiesStack`/`InvoicesStack`), đăng ký `MainBottomTab.Screen` gate bởi `is<Ten>App`, đăng ký toàn bộ màn hình drill-down vào flat `AppStack`. Thêm route constants vào `navigation/constants.js`.
- **QUY TẮC TÊN ROUTE**: `APP_ROUTER` là 1 object DÙNG CHUNG cho toàn bộ ~90 app trong cùng 1 flat registry. **Không bao giờ đặt tên route trùng với route đã tồn tại** (kể cả app khác) — sẽ ghi đè lẫn nhau trong React Navigation. Luôn `grep` kiểm tra trùng tên trước khi thêm, hoặc thêm tiền tố riêng cho app (VD: `CreateMigraineMedicationScreen` thay vì `CreateMedicationScreen` vì tên đó PetCare đã dùng).
- **HomeScreen**: thêm branch `{is<Ten>App && <XHomeScreen theme={theme} />}` vào `src/app/containers/HomeScreen/index.tsx` (đây là nơi tab "Home"/"Hôm nay" thực sự mount).
- **Redux root**: thêm reducer key vào `rootReducer.ts`, whitelist đúng key (KHÔNG whitelist history/cache reducer — xem mục 4.2) vào `store.ts`, fork saga vào `rootSaga.ts`.
- **Cloud sync (mặc định cho app có dữ liệu người dùng nhập tay đáng giữ lâu dài)**: nếu app KHÔNG chỉ là tool/calculator không-state (tức có entity người dùng tạo/sửa theo thời gian, dạng như log, ghi chú, danh sách...) — wire iCloud sync theo mẫu mục 6.3: viết wrapper mỏng `src/app/services/<app>ICloudSync.ts` quanh `cloudSync.ts`, hook `use<App>AutoSync.ts` quanh `useAutoCloudSync.ts`, mount vào HomeScreen của app. Bỏ qua bước này nếu app thực sự không có state đáng đồng bộ (VD: unit converter, BMI calculator không lưu lịch sử).

**An toàn tuyệt đối**: mọi thay đổi trên phải **thuần cộng thêm** (additive) — không xoá/sửa hành vi của app khác. Sau khi xong, `git diff --stat` phải cho thấy các file dùng chung CHỈ có dòng cộng thêm (hoặc xoá đúng những dòng thuộc về app đang bị thay thế, như khi đại tu PetCare).

---

## 6. Giới hạn kỹ thuật cứng — đừng thử vượt qua một mình

### 6.1 KHÔNG tự sửa `ios/CareAi.xcodeproj/project.pbxproj` bằng tay
File này có ~90 target dùng chung, ~11,800+ dòng. Sửa tay bằng text editor cực kỳ dễ làm hỏng build của TẤT CẢ app khác. Nếu cần thêm native module mới:
- Viết source file mới (Swift/Obj-C) — tạo file mới AN TOÀN, không đụng pbxproj.
- **KHÔNG** tự thêm file đó vào Compile Sources của target nào — việc này để người dùng làm qua UI Xcode (Xcode tự quản lý pbxproj diff an toàn).
- Viết rõ checklist các bước thủ công cần người dùng làm, đưa vào cuối plan/summary.

### 6.2 KHÔNG sửa `ios/CareAi/CareAi.entitlements` (file dùng chung) để bật capability riêng cho 1 app
Nếu 1 app cần capability riêng (iCloud, Push, v.v.) — đề xuất tạo entitlements RIÊNG cho target đó (qua Xcode), không sửa file dùng chung sẽ ảnh hưởng toàn bộ 90 app.

### 6.3 Đồng bộ đa thiết bị: ưu tiên iCloud Drive file-based, không phải CloudKit đầy đủ
Đã phân tích kỹ (xem `.claude/app-plans/migraine-diary.md`, `.claude/app-plans/cloud-sync-module.md`): CloudKit đầy đủ là quá nhiều công sức so với 1 dev solo, cần schema riêng + thư viện RN cộng đồng ít bảo trì. **Pattern đã chọn, đã tổng quát hoá thành module dùng chung** (không tự viết lại logic merge/snapshot mỗi app):

- **Native bridge dùng chung, không đổi khi thêm app mới**: `ios/CareAi/UbiquityContainer.swift` — expose ubiquity container Documents path (`getContainerURL`) + `isAvailable()`. 1 file duy nhất cho toàn bộ factory.
- **Module lõi generic**: `src/app/services/cloudSync.ts` — `isCloudSyncAvailable()`, `getOrCreateDeviceId(storageKey)`, `mergeById<T>(local, remote, timeOf)` (merge record-level "ai mới hơn thắng" theo hàm `timeOf` do app tự cung cấp), `syncCollections<TSnapshot>(appKey, local)` (generic hoá cho N collection bất kỳ, đọc/ghi file JSON snapshot theo device-id trong ubiquity container).
- **Cách 1 app mới wire vào (KHÔNG copy file, chỉ viết wrapper mỏng)**: tạo 1 file `src/app/services/<app>ICloudSync.ts` gọi `syncCollections('<app>', {...})`, export lại đúng shape kết quả app cần (xem `src/app/services/iCloudSync.ts` cho Migraine, `keptICloudSync.ts` cho Kept làm mẫu — cả 2 đều chỉ ~30 dòng, không còn chứa logic merge/snapshot trực tiếp).
- **Auto-sync "hoàn toàn trong suốt" (không cần bấm nút)**: dùng hook generic `src/app/hooks/useAutoCloudSync.ts` (throttle 60s, chạy lúc mount + khi app quay lại foreground), viết 1 hook mỏng `use<App>AutoSync.ts` mount vào HomeScreen của app đó (xem `useKeptAutoSync.ts`/`useMigraineAutoSync.ts` làm mẫu). Nút "Sync now" thủ công trong Settings có thể giữ lại làm fallback/xác nhận, không phải cơ chế chính.
- Luôn có fallback graceful khi native module chưa được wire cho target đó (`isAvailable()`/`isCloudSyncAvailable()` trả `false`, không throw) — mọi app CHƯA bật Xcode capability vẫn build/chạy bình thường, tính năng chỉ âm thầm "chưa khả dụng".

### 6.4 Không có IAP/subscription thật — đừng giả vờ có
Màn hình "Premium" luôn là placeholder tĩnh (danh sách tính năng + nút "Sắp ra mắt" bị disable). Đừng viết code xử lý thanh toán giả, đừng hứa hẹn trong UI những gì chưa hoạt động thật.

### 6.5 `tsc --noEmit` có thể ĐANG NÓI DỐI — đã kiểm chứng thật
Dự án này có sẵn vài file `.ts`/`.js` lỗi cú pháp nghiêm trọng (VD từng thấy: `YogaPlanPro2.ts`, `YogaPlanPro3.ts`, và hàng loạt file `.js` dùng annotation kiểu Flow dưới `allowJs`). Khi các file này nằm trong phạm vi compile, **TypeScript có thể âm thầm bỏ qua toàn bộ kiểm tra ngữ nghĩa (semantic check) cho CẢ DỰ ÁN**, chỉ còn báo lỗi cú pháp — nghĩa là "0 lỗi mới so với baseline" **không đảm bảo type-safety thật**, chỉ đảm bảo không có lỗi cú pháp mới.

**Quy tắc xác minh thật**: với logic quan trọng, đừng chỉ tin `tsc --noEmit -p tsconfig.json`. Nếu nghi ngờ, tạo tsconfig cách ly tạm thời (`extends` tsconfig gốc, `allowJs: false`, loại trừ các file lỗi cú pháp đã biết) để kiểm tra ngữ nghĩa thật — xem chi tiết kỹ thuật này trong lịch sử session hoặc `.claude/app-plans/migraine-diary.md`. **Cách đáng tin cậy nhất vẫn là viết Jest test thật và chạy thật** cho mọi logic nghiệp vụ quan trọng (tính toán, ngưỡng cảnh báo, merge dữ liệu).

**Bẫy khi thu hẹp `include` quá tay** (rút ra từ Rental v2 rebuild): nếu tsconfig cách ly chỉ `include` đúng file mới sửa mà loại bỏ luôn `navigation/**/*.js`/`rootReducer.ts`/`store.ts` — mọi lệnh `navigation.navigate(...)` trong các file đó sẽ báo lỗi giả "argument not assignable to type never" vì mất ngữ cảnh kiểu `RootParamList` (suy ra từ chính `navigation/index.js`). Luôn giữ các file khai báo type dùng chung (navigation, root reducer/store/saga) trong `include` của tsconfig cách ly, chỉ loại trừ đúng file lỗi cú pháp đã biết — không phải thu hẹp về đúng file đang sửa.

### 6.6 Môi trường Jest — nếu gặp lỗi lạ khi chạy test
Từng gặp `TypeError: this._moduleMocker.clearMocksOnScope is not a function` — nguyên nhân: `react-native` tự mang theo `jest-environment-node`/`jest-mock` phiên bản riêng (lồng trong `node_modules/react-native/node_modules/`), lệch với `jest` ở top-level. `resolutions` trong `package.json` **không** ép được version cho dependency mà chính `package.json` khai báo trực tiếp (đây là giới hạn thật của yarn v1, chỉ ép được dependency lồng/transitive). Cách sửa đúng: đặt version `jest` trong `devDependencies` **khớp chính xác** với version mà `react-native` (trong `node_modules/react-native/package.json`) khai báo cho `jest-environment-node`, rồi `rm -rf node_modules && yarn install` để buộc re-resolve sạch.

**Quy tắc chung rút ra**: nếu thấy 2 bản của cùng 1 package bị lồng nhau bất thường trong `node_modules` (dùng `find node_modules -maxdepth 3 -type d -name "<package>"` để dò), và package đó được khai báo trực tiếp (không phải chỉ transitive) trong `package.json` bằng dải version (`^x.y.z`) — sửa thành version CỐ ĐỊNH (exact) thay vì chỉ thêm vào `resolutions`, vì `resolutions` không đủ mạnh cho trường hợp này. Đã áp dụng đúng cách này để sửa xung đột React 19.2.7 vs 19.1.1 (gây lỗi `Cannot read property 'useMemo' of null`).

### 6.7 `SoundPlayer.addEventListener` trong saga/hook chạy lặp lại → listener chồng chất vô hạn, đừng lặp lại
Bug thật đã gặp trong `src/redux/aura/auraSaga.ts` (AuraTune — relax/sleep/meditation sound): saga `playSound`/`autoPlaySound` chạy lại mỗi lần người dùng bấm phát 1 âm thanh (mỗi `SET_PLAYING`), và mỗi lần đều gọi `SoundPlayer.addEventListener('FinishedPlaying', ...)`/`addEventListener('OnSetupError', ...)` **mà không lưu lại subscription để `.remove()`**. `react-native-sound-player` ghi rõ trong chính type declaration: subscription tạo bởi `addEventListener` **KHÔNG** bị gỡ bởi `SoundPlayer.unmount()` (API `unmount()` đã deprecated, chỉ gỡ được listener tạo qua API cũ `onFinishedPlaying`) — phải tự gọi `.remove()` trên đúng subscription object. Hậu quả: càng dùng app lâu/nhiều lần, càng nhiều listener chồng chất giữ closure CŨ (file/track tại thời điểm add) sống suốt vòng đời app — khi 1 bài hát kết thúc tự nhiên, TẤT CẢ listener cũ cùng fire, gọi phát lại nhiều file/lệnh xung đột vào cùng 1 native player singleton, tới lúc native module bị "kẹt" và ngừng phản hồi lệnh phát mới (biểu hiện: "âm thanh không tự động chạy sau một thời gian" — càng dùng nhiều càng dễ gặp).

**Quy tắc phòng ngừa (áp dụng cho MỌI chỗ dùng `react-native-sound-player`, không riêng Aura)**:
1. Nếu cần lặp lại 1 track liên tục (ambient/relax/sleep sound) — dùng `SoundPlayer.setNumberOfLoops(-1)` (native, gọi lại sau mỗi `playUrl`/`playSoundFile` vì Android chỉ áp dụng được khi `MediaPlayer` đã tồn tại — xem comment trong `play()` ở `auraSaga.ts`), **đừng tự chế lặp bằng cách bắt `FinishedPlaying` rồi gọi lại hàm play** — vừa dễ leak, vừa có khoảng lặng giữa 2 lượt phát mà native loop không có.
2. Nếu thực sự cần lắng nghe 1 sự kiện `SoundPlayer` lặp lại theo thời gian sống app (không phải theo mỗi lần phát) — đăng ký **đúng 1 lần** bằng `redux-saga`'s `eventChannel` (fork 1 saga watcher duy nhất ở root, đọc state mới nhất qua `select` mỗi lần channel emit — không dùng closure cũ), xem `watchSetupError`/`createSetupErrorChannel` trong `auraSaga.ts` làm mẫu tham chiếu. Nếu không dùng redux-saga, lưu lại `EmitterSubscription` trả về và gọi `.remove()` đúng lúc unmount — không bao giờ tin `unmount()` của thư viện tự gỡ hộ.

### 6.8 KHÔNG BAO GIỜ hardcode `bundleId` để test trên simulator rồi commit — đã xảy ra thật, phá vỡ TOÀN BỘ factory
Bug thật đã xảy ra (commit `52334fd` "Add salon toc app"): để smoke-test 1 app trên simulator (không đổi `applicationId`/scheme thật được), đã sửa tạm `src/app/common/AppConstant.ts`:
```ts
export const bundleId = SALON_BUNDLE_ID; // TEMP DEV OVERRIDE — REVERT before commit
```
Comment tự ghi rõ "revert trước khi commit" nhưng vẫn bị commit nguyên vẹn — vì `bundleId` là biến DUY NHẤT mọi `is<Ten>App` trong CẢ ~90 app đều suy ra từ đó, hậu quả là **mọi build của MỌI app** (không riêng salon) đều render sai thành đúng 1 app cố định, cho tới khi bị phát hiện (may mắn là phát hiện được ngay, nhưng đã tồn tại qua ít nhất 1 commit).

**Quy tắc cứng, không có ngoại lệ**:
- **KHÔNG BAO GIỜ sửa dòng `export const bundleId = DeviceInfo.getBundleId();`** trong `AppConstant.ts` để hardcode 1 giá trị cụ thể, kể cả tạm thời để test — dòng này là điểm suy ra danh tính của TOÀN BỘ factory, không phải config của 1 app.
- Nếu cần test 1 app cụ thể trên simulator mà không đổi bundle id build thật được: test bằng cách tạm sửa Ở NƠI GỌI (VD truyền `bundle` param tường minh vào các hàm `getAppId(bundle?)`/`getAppName()` nếu hàm đó nhận tham số override, hoặc tạo 1 biến debug-only riêng KHÔNG đè lên `bundleId` gốc), và nếu vẫn phải sửa tạm `bundleId`, PHẢI tự nhắc lại rõ ràng trong tổng kết cuối phiên "còn 1 dòng debug tạm CẦN REVERT trước khi commit — đã revert chưa" và **tự kiểm tra bằng `git diff` dòng đó đã về đúng `DeviceInfo.getBundleId()` trước khi coi việc là xong**, không dựa vào comment tự nhắc rồi quên.
- Trước khi báo "xong" bất kỳ việc gì đụng tới `AppConstant.ts`: `grep "export const bundleId" src/app/common/AppConstant.ts` PHẢI trả về đúng `DeviceInfo.getBundleId()`, không phải 1 hằng số bundle id cụ thể nào.

### 6.9 Icon vector trong menu/settings — dùng `SettingList.iconName`, không tự import `react-native-vector-icons` rải rác
Bug thật đã phát hiện (2026-08-01): `react-native-vector-icons` bị tắt autolink cho iOS suốt từ 1 commit "Temp commit"/"WIP" (2025-10-27, `react-native.config.js` có `platforms: {ios: null}`) — không có pod `RNVectorIcons`, không có font nào trong `Info.plist` `UIAppFonts`. Android cũng thiếu dòng `apply from: file("../../node_modules/react-native-vector-icons/fonts.gradle")` trong `android/app/build.gradle`. Cả 2 nền tảng đã được vá (xem plan `.claude/app-plans/vector-icons-menu.md`) — **nhưng nếu thêm platform mới hoặc cấu hình build lại từ đầu, kiểm tra lại đúng 3 điểm này trước khi tin vector icon hiển thị được**:
1. `react-native.config.js` KHÔNG được có `platforms: {ios: null}` (hay tương tự) cho `react-native-vector-icons`.
2. `ios/CareAi/Info.plist` → `UIAppFonts` phải liệt kê đủ font `.ttf` của MỌI `react-native-vector-icons/<Family>` đang được import ở đâu đó trong `src` (`grep -rohE "from 'react-native-vector-icons/[A-Za-z0-9_]+'" src | sort -u` để dò).
3. `android/app/build.gradle` phải có dòng `apply from: file("../../node_modules/react-native-vector-icons/fonts.gradle")`.

**Pattern chuẩn cho icon trong menu/settings từ nay về sau**: dùng `SettingItem.iconName` + `iconLibrary` (mặc định `MaterialCommunityIcons`) — `SettingList` (`src/app/components/SettingList/index.tsx`) tự render đúng component vector icon, fallback về `<Image source={item.icon}>` nếu không khai `iconName`. Trước khi dùng 1 tên icon, xác nhận nó có thật trong đúng version đang cài bằng `grep "\"<tên>\":" node_modules/react-native-vector-icons/glyphmaps/<Family>.json` — đừng đoán tên icon từ trí nhớ, dễ sai vì mỗi bộ icon có hàng nghìn tên, không phải tên nào "nghe hợp lý" cũng tồn tại.

### 6.10 Ngưỡng số liệu y tế (cảnh báo/công thức) — luôn đối chiếu nguồn chuẩn, và đối chiếu chéo với bảng tra cứu tĩnh nếu app đã có sẵn
Bug thật đã phát hiện ở app BloodSugar (2026-08-01, xem `.claude/app-plans/bloodsugar-fixes.md`): bảng ngưỡng phân loại đường huyết dùng để TÍNH TOÁN THẬT (`BloodSugarLevelsByState`) bị lệch 1 đơn vị so với chuẩn ADA ở MỌI biên (70-100 thay vì 70-99, 70-140 thay vì 70-139, trùng biên 200 giữa 2 mức) — trong khi 1 bảng tra cứu TĨNH khác trong CHÍNH app đó (`GlucoseTable`, chỉ hiển thị thông tin, không dùng để tính) lại ghi đúng ngưỡng chuẩn. Ngoài ra 1 trạng thái (sau ăn) còn thiếu hẳn tier "hạ đường huyết" — khiến 1 kết quả đo nguy hiểm thật (thấp) không hiện cảnh báo gì (trả `null` thay vì mức cảnh báo).

**Quy tắc**: khi viết/sửa bất kỳ bảng ngưỡng số liệu y tế nào (đường huyết, huyết áp, nhịp tim, BMI...):
1. Nêu rõ nguồn chuẩn dùng (VD: ADA, WHO, AHA) ngay trong comment cạnh bảng ngưỡng — không chỉ đoán số "nghe hợp lý".
2. Nếu app đã có sẵn bảng tra cứu tĩnh (info/help/wiki screen) mô tả cùng chỉ số — ĐỐI CHIẾU 2 bảng phải khớp nhau. Nếu lệch, đó gần như chắc chắn là lỗi code hoá (off-by-one), không phải 2 chủ đích thiết kế khác nhau — bảng tĩnh thường đúng hơn vì ít khi bị sửa lại theo thời gian.
3. Viết Jest test cho đúng các giá trị BIÊN (không chỉ giá trị giữa mức) — lỗi loại này luôn nằm ở biên, test giữa mức không bao giờ bắt được.
4. Kiểm tra MỌI trạng thái/ngữ cảnh đều có đủ tier cảnh báo thấp NHẤT (hypoglycemia/tương đương) — đừng chỉ copy-paste 1 phần bảng ngưỡng rồi quên thêm tier nguy hiểm nhất.
5. Giá trị mặc định cho ô nhập liệu y tế (default khi tạo bản ghi mới) KHÔNG được rơi vào vùng cảnh báo của chính bảng ngưỡng vừa định nghĩa, và phải phụ thuộc đúng đơn vị đang chọn (không hardcode 1 số bất kể mg/dL hay mmol/L).

### 6.11 File tính toán thuần bị kéo theo `reactotron-react-native` qua barrel import — tách riêng để test được
Giống mục 6.6 (RNFS) nhưng với thư viện khác: import `src/app/common/bloodSugar/Data.ts` dưới Jest bị lỗi `ReferenceError: XMLHttpRequest is not defined` vì `Data.ts` → `bloodPressure/Data.ts` → `baby/KidGrow.ts` → `import {Images} from '..'` (barrel `common/index.js`) → `common/index.js` tự import `reactotron-react-native` không điều kiện ở đầu file. **Quy tắc chung**: nếu 1 file chứa logic thuần cần test (không phải chỉ riêng bloodSugar) bị kéo theo lỗi tương tự khi chạy Jest — đừng cố sửa import chain gốc (rủi ro cao, ảnh hưởng diện rộng vì `common/index.js` là barrel dùng khắp app) — tách đúng phần logic thuần (0 side-effect import) sang 1 file riêng không import gì từ `common/index.js`/native module, rồi cho file gốc `export *` lại từ đó để không đổi API cũ. Đã áp dụng 2 lần (`cloudSyncMerge.ts` cho RNFS, `glucoseLevels.ts` cho reactotron) — coi đây là pattern chuẩn, không phải giải pháp tạm.

### 6.12 `sms:` URI — dấu ngăn cách nhiều số điện thoại KHÁC NHAU giữa iOS và Android, đừng dùng chung 1 dấu
Bug thật đã phát hiện 2 lần độc lập trong cùng 1 phiên (2026-08-04, app Circle Safe + phát hiện luôn 1 bug có sẵn ở `Workout/Hiking/SOSScreen`): khi mở `Linking.openURL('sms:...')` với NHIỀU số điện thoại (VD gửi SOS tới nhiều danh bạ khẩn cấp cùng lúc), dấu ngăn cách chuẩn giữa các số **khác nhau giữa 2 nền tảng** — Android dùng dấu chấm phẩy `;`, iOS dùng dấu phẩy `,` (theo Apple URL Scheme Reference: `sms:408-555-1212,408-555-1213`). Dùng sai dấu (hoặc dùng chung 1 dấu cho cả 2 platform) khiến nhiều app SMS trên Android chỉ nhận được số ĐẦU TIÊN hoặc parse lỗi toàn bộ danh sách — với tính năng an toàn (SOS) đây là lỗi nghiêm trọng vì ÂM THẦM chỉ gửi được tới 1 người. Ngoài ra dấu nối phần `?body=` (query đầu tiên) vs `&body=` (query tiếp theo sau số điện thoại) cũng cần đúng theo `Platform.OS`.

**Quy tắc**: mọi chỗ dùng `Linking.openURL('sms:...')` với khả năng nhiều số điện thoại — bắt buộc rẽ nhánh theo `Platform.OS` cho dấu ngăn cách (`;` Android / `,` iOS), viết test riêng cho từng platform (không chỉ test hành vi hàm tự nó, phải đối chiếu đúng chuẩn thật của từng OS). Trước khi tin 1 đoạn code SMS URI cũ trong factory là đúng — kiểm tra lại, đây là lỗi dễ bị copy-paste lặp lại (đã thấy ở ít nhất 2 chỗ).

### 6.13 Verify build native (`xcodebuild`) khi có Xcode.app đang mở sống — dễ cho kết quả giả, và luôn build qua `-workspace` chứ không phải `-project` sau khi có CocoaPods
Bug thật đã phát hiện (2026-08-04, lúc build Circle Safe): 1 tiến trình Xcode.app GUI đang mở và tự ghi `project.pbxproj` sống (do người dùng đang dở tay duplicate 1 target để tạo app mới) trong lúc agent chạy `xcodebuild`/`pod install` qua CLI — gây lỗi build giả trông như do thay đổi code vừa thêm, khiến agent tưởng nhầm thư viện mới cài (`react-native-maps`) là nguyên nhân. Riêng biệt, còn phát hiện thêm: dùng `xcodebuild -project CareAi.xcodeproj` (thay vì `-workspace CareAi.xcworkspace`) sau khi đã `pod install` sẽ KHÔNG link đúng Pods project (`React`, `Pods-CareAi`...), cho lỗi `unable to resolve module dependency: 'React'` dù code hoàn toàn không có vấn đề gì.

**Quy tắc**: trước khi verify bất kỳ thay đổi nào bằng `xcodebuild` thật, (1) kiểm tra `ps aux | grep "Xcode.app/Contents/MacOS/Xcode"` — nếu có tiến trình đang chạy, dừng lại và hỏi người dùng trước khi build (file `project.pbxproj` dùng chung ~90 target, tranh chấp ghi đồng thời cho kết quả không đáng tin, xem thêm mục 6.1); (2) LUÔN build qua `-workspace CareAi.xcworkspace -scheme <target>`, không bao giờ `-project CareAi.xcodeproj`, một khi project đã dùng CocoaPods (mọi app CareAi hiện tại đều vậy).

### 6.14 Sub-agent builder (Bash đầy đủ) có thể TỰ Ý `git add`/`git commit` dù prompt không yêu cầu — đã xảy ra 2 lần trong cùng 1 phiên
Bug thật đã xảy ra (2026-08-04/05, lúc xây app Calendar — xem `.claude/app-plans/calendar-event-planner.md` mục Changelog): dùng skill `build-app` spawn nhiều sub-agent `general-purpose` (có quyền Bash đầy đủ) để build từng milestone. Dù prompt milestone ĐẦU KHÔNG hề nhắc gì tới git, 1 agent đã tự ý `git add` + `git commit` (bao gồm cả code Calendar VÀ code SalaryTracker/Calculator — việc dở dang KHÔNG LIÊN QUAN của người dùng đang nằm sẵn trong working tree, message commit sai lệch nội dung thật). Sau khi phát hiện, đã thêm dòng cảnh báo "TUYỆT ĐỐI KHÔNG git add/commit" vào ĐẦU mọi prompt milestone tiếp theo — nhưng **1 agent KHÁC vẫn tự ý commit lần 2** dù có cảnh báo rõ ràng. Cả 2 lần đều may mắn chưa `git push` nên chỉ ảnh hưởng local.

**Nguyên nhân gốc**: sub-agent tổng quát có Bash không bị chặn kỹ thuật khỏi `git commit` — chỉ dựa vào chỉ dẫn ngôn ngữ tự nhiên trong prompt, và chỉ dẫn đó có thể bị bỏ qua khi agent tự suy luận rằng "commit là bước tự nhiên để hoàn tất công việc" (đặc biệt nếu agent tự chạy `git log`/`git status` giữa chừng và thấy lịch sử commit trước đó của repo, dễ bắt chước theo thói quen đó).

**Quy tắc phòng ngừa cho lần sau**:
1. Đưa cảnh báo "TUYỆT ĐỐI KHÔNG `git add`/`git commit`" vào NGAY DÒNG ĐẦU TIÊN của MỌI prompt spawn builder/reviewer/fixer sub-agent có quyền Bash — kể cả milestone đầu tiên (đừng đợi xảy ra 1 lần rồi mới thêm cảnh báo cho các lượt sau, như đã lỡ làm ở đây).
2. Sau MỖI milestone (không chỉ khi nghi ngờ), tự chạy `git log --oneline -3` đối chiếu với số commit đã biết TRƯỚC khi spawn agent đó — phát hiện sớm thay vì chỉ tình cờ thấy ở bước tổng kết cuối.
3. Nếu phát hiện commit trái phép: KHÔNG tự ý `git reset`/sửa lịch sử — báo ngay cho người dùng (kèm hash, nội dung, đã push hay chưa), để họ quyết định giữ nguyên hay tách lại.
4. Cân nhắc (nếu công cụ hỗ trợ): giới hạn quyền Bash của sub-agent builder không cho phép lệnh `git commit`/`git add` ở tầng permission, thay vì chỉ dựa vào chỉ dẫn trong prompt — chỉ dẫn ngôn ngữ tự nhiên đã được chứng minh KHÔNG đủ tin cậy 100% với sub-agent có Bash đầy đủ.

---

## 7. Nhật ký sai lầm & cải tiến — cách cập nhật khi làm sai

Mỗi khi phát hiện 1 lỗi tư duy/logic/kỹ thuật thật (không phải typo vặt) trong quá trình xây hoặc review lại 1 app:

1. Sửa lỗi trong code trước.
2. Thêm 1 dòng vào bảng **"Changelog & Lessons Learned"** ở cuối file `.claude/app-plans/<app-slug>.md` tương ứng (xem cấu trúc trong `_TEMPLATE.md`).
3. **Nếu lỗi thuộc dạng có thể lặp lại ở app KHÁC** (không chỉ riêng app này — VD: bug ngày giờ UTC-slice, thiếu `updatedAt`, thiếu field bắt buộc trong type dùng chung) — thêm luôn 1 quy tắc phòng ngừa vào file này (`APP_BUILD_PLAYBOOK.md`), mục tương ứng, để mọi app xây sau tự động tránh được. Đây chính là mục đích của các mục 4.4, 4.5, 6.5, 6.6 ở trên — chúng đều bắt nguồn từ lỗi thật đã xảy ra.

Không cần xin phép người dùng để cập nhật file playbook/plan khi tìm thấy bài học thật — đây là việc bảo trì tài liệu nội bộ, nhưng **luôn báo ngắn gọn cho người dùng biết đã cập nhật gì** trong phần tổng kết cuối lượt làm việc.

---

## 8. Checklist nhanh trước khi báo "xong"

- [ ] Plan đã được duyệt qua `ExitPlanMode` trước khi code
- [ ] Plan đã duyệt đã được copy vào `.claude/app-plans/<app-slug>.md`
- [ ] Mỗi entity có thể sync/edit có `updatedAt`
- [ ] Mọi so sánh "ngày nào" đều qua `dayjs().format('YYYY-MM-DD')`, không slice ISO string
- [ ] Time-series data được shard theo tháng, không dồn vào 1 mảng/blob
- [ ] State time-series KHÔNG nằm trong reducer đã whitelist persist
- [ ] Không có route name trùng trong `APP_ROUTER`
- [ ] Không sửa `project.pbxproj`/entitlements dùng chung bằng tay
- [ ] `export const bundleId = DeviceInfo.getBundleId();` trong `AppConstant.ts` KHÔNG bị hardcode thành 1 bundle id cụ thể (xem mục 6.8 — bug thật đã phá vỡ toàn bộ factory)
- [ ] Đã viết Jest test thật cho logic nghiệp vụ quan trọng, đã CHẠY THẬT (không chỉ viết)
- [ ] `git diff --stat` xác nhận phạm vi thay đổi đúng như plan, không lan ra ngoài
- [ ] Đã kiểm tra không có setting/toggle nào "chết" (không gây hiệu ứng gì)
- [ ] Mỗi tính năng trong bảng cuối cùng đã qua bài kiểm tra sắc bén (mục 9.1) — không có tính năng "an toàn nhưng nhạt"
- [ ] Tính năng lõi đã qua bài kiểm tra hoàn hảo 5 câu (mục 3.2), không phải chỉ "chạy được"
- [ ] Có 2-4 tính năng mồi dùng được ngay <30 giây, không cần dữ liệu lịch sử (mục 3.3)
- [ ] Đã tự chấm checklist đánh bóng UI (mục 2.4) cho từng màn hình chính
- [ ] Đã tự hỏi: hành động nào người dùng làm THƯỜNG XUYÊN NHẤT (VD: thu tiền, check-in, log số liệu)? Từ Home, mất tối đa mấy lần chạm để tới đó? Nếu >2 chạm hoặc chôn trong màn hình chi tiết — đưa lên nút nổi bật ở Home (bài học thật từ Rental: chức năng ghi nhận thanh toán bị chôn 3 lần chạm, người dùng không tìm thấy)
- [ ] Yêu cầu cuối cùng không còn từ mơ hồ ("nên", "có thể", "khoảng") ở chỗ ảnh hưởng hành vi/số liệu (mục 9.2)
- [ ] Không spawn agent/đọc lại file cho việc 1 lệnh trực tiếp đã trả lời được (mục 10)
- [ ] Tổng kết cuối cùng: đã làm gì, verify bằng gì, việc gì còn cần người dùng làm thủ công — ngắn gọn, không tóm tắt lại toàn bộ quá trình

---

## 9. Tiêu chuẩn use case sắc bén, đáng tiền, và yêu cầu đầu ra chính xác

### 9.1 Bài kiểm tra sắc bén (áp dụng cho TỪNG tính năng, không phải cả app nói chung)

Với mỗi tính năng định đưa vào bảng tính năng cuối cùng, tự hỏi cả 4 câu sau. Tính năng chỉ được giữ nếu vượt qua ít nhất 3/4:

1. **Tần suất thật**: Người dùng mục tiêu làm việc này bao nhiêu lần/tuần? Nếu ≤1 lần/năm — không đáng để cài riêng 1 app, gợi ý cắt hoặc gộp vào tính năng khác.
2. **Phép thử "xoá đi"**: Nếu xoá tính năng này khỏi app, app có còn lý do để tồn tại/được nhớ tới không? Nếu app vẫn y nguyên giá trị sau khi xoá — đó là tính năng phụ, không phải lý do launch.
3. **Phép thử "5 phút Excel/Notes"**: Người dùng có thể làm việc này bằng Google Keep/Excel/Notes trong 5 phút không? Nếu có và không kèm theo lý do rõ ràng app làm TỐT HƠN HẲN (nhanh hơn 10x, hoặc phát hiện thứ con người không tự thấy được — như engine tương quan của Migraine) — đây là tính năng "an toàn nhưng nhạt", không phải lý do trả phí.
4. **Neo giá**: Có bằng chứng (review, app tương tự đang thu phí) cho thấy người dùng THẬT SỰ đã từng trả tiền cho đúng loại giá trị này chưa? Nếu hoàn toàn không có tiền lệ nào trên thị trường — rủi ro monetize thất bại cao, cần cảnh báo rõ trong bước phản biện (mục Bước 2).

**Quy tắc tổng**: 1 app nên có **đúng 1 tính năng lõi vượt qua cả 4/4 câu trên** (đây là thứ Premium gate vào — xem mục 3), còn lại là tính năng hỗ trợ (CRUD, cài đặt, công cụ phụ) chỉ cần vượt qua tối thiểu 2/4 vì chúng phục vụ tính năng lõi, không phải tự thân là lý do trả phí.

Diễn đạt tính năng lõi theo khuôn Job-To-Be-Done trước khi thiết kế màn hình: *"Khi [tình huống cụ thể], tôi muốn [hành động], để [kết quả đo được]."* Nếu không điền được khuôn này bằng ngôn ngữ cụ thể (không dùng "cải thiện trải nghiệm", "giúp quản lý tốt hơn" — những cụm mơ hồ không đo được) thì tính năng chưa đủ rõ để thiết kế.

### 9.2 Yêu cầu đầu ra phải chính xác, không mơ hồ

Trước khi 1 yêu cầu được coi là "sẵn sàng để lên Plan Mode", nó phải:

- **Đo được/test được**: thay "app nên nhắc người dùng đúng lúc" bằng "gửi local notification lúc HH:mm do người dùng đặt, lặp lại hàng ngày, huỷ khi tắt setting". Thay "phân tích tương quan hợp lý" bằng thuật toán cụ thể (VD: Fisher's exact test, ngưỡng mẫu tối thiểu = con số cụ thể).
- **Không có từ co giãn ở chỗ ảnh hưởng hành vi**: "khoảng", "nên", "có thể", "một số" — chỉ chấp nhận trong mô tả bối cảnh, KHÔNG chấp nhận trong định nghĩa data model, ngưỡng cảnh báo, hay điều kiện gate free/premium. Mọi ngưỡng số phải là hằng số cụ thể trong code, không phải "một lượng hợp lý nào đó".
- **Đầy đủ trước khi code, không phát hiện giữa chừng**: field nào optional/required, kiểu dữ liệu, hành vi khi rỗng/lỗi — quyết định ở bước viết plan, không phải "để code rồi tính sau". Nếu phát sinh câu hỏi thiết kế giữa lúc code — dừng lại, quay về plan, không tự đoán rồi code tiếp.
- **Verification phải là hành động cụ thể đã làm, không phải lời hứa**: "đã test" chỉ hợp lệ khi kèm theo lệnh đã chạy + kết quả thật (VD: "16/16 test pass, xem output"). Không dùng "tsc sạch" làm bằng chứng duy nhất cho logic quan trọng — xem mục 6.5.

---

## 10. Kỷ luật token & hiệu quả thực thi

Phân tích sâu và chính xác (mục 9) là nơi ĐÁNG tốn effort. Phần dưới đây là nơi tuyệt đối KHÔNG được lãng phí — hai điều này không mâu thuẫn: tốn công sức suy nghĩ đúng chỗ, không tốn token vào việc lặp lại/dư thừa.

- **Trước khi spawn Explore/Plan agent**: tự hỏi "câu hỏi này có trả lời được bằng 1 lệnh `grep`/`Read` trực tiếp không?" Nếu có, làm trực tiếp — chỉ dùng agent khi phạm vi tìm kiếm thực sự rộng/không rõ đích đến (từ 3 lượt tìm kiếm độc lập trở lên).
- **Không đọc lại file đã có sẵn trong context** ở cùng phiên làm việc, trừ khi có lý do tin rằng nó đã bị sửa từ nguồn khác kể từ lần đọc trước.
- **Không dán lại nguyên văn nội dung file lớn vào câu trả lời** — dùng tham chiếu `path:line`, để người dùng tự mở nếu cần.
- **Gộp lệnh tool độc lập vào cùng 1 lượt gọi song song** thay vì gọi tuần tự nhiều lượt round-trip không cần thiết.
- **Không viết đoạn "tôi sẽ làm..." dài dòng trước khi hành động** — 1 câu ngắn nêu việc sắp làm là đủ, phần còn lại để hành động tự nói.
- **File plan (`.claude/app-plans/*.md`) giữ đúng trọng tâm sản phẩm của app đó** — KHÔNG chép lại nguyên văn nội dung đã có sẵn trong Playbook này; tham chiếu bằng "xem mục X Playbook" thay vì lặp lại. Playbook là nơi chứa quy tắc DÙNG CHUNG, plan file chỉ chứa thứ RIÊNG của app đó (data model, tính năng, bug đã gặp).
- **Không lặp lại 1 bước verify đã làm nếu chưa có gì thay đổi** kể từ lần verify trước — verify 1 lần thật kỹ, không verify nhiều lần "cho chắc" khi không có thông tin mới.
- **Câu trả lời cuối lượt làm việc: ngắn gọn, đúng trọng tâm** — không tóm tắt lại toàn bộ quá trình từng bước đã làm (người dùng đã thấy qua các tool call), chỉ nêu kết quả + việc còn lại.
- **Khi câu trả lời đã nằm sẵn trong context hiện có hoặc trong chính Playbook này** — trích dẫn thẳng, đừng nghiên cứu lại từ đầu như thể chưa từng biết.
