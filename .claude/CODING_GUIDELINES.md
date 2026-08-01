# Coding Guidelines — quy tắc hành vi coding chung cho mọi project trong workspace này

> Nguồn gốc: quy tắc hành vi tổng quát để giảm lỗi thường gặp của LLM khi code — áp dụng cho MỌI project trong `careai/` (CareAi, dvc-api, salon-web, beverage-web, velox-web), **kết hợp thêm** (không thay thế) rule riêng từng project (`CareAi/.claude/APP_BUILD_PLAYBOOK.md` cho CareAi, `dvc-api/docs/ENGINEERING_STANDARDS.md`+`SRS_PROCESS.md` cho dvc-api...). Khi 2 bộ rule mâu thuẫn cụ thể, rule RIÊNG của project thắng (vì nó phản ánh bài học/quyết định đã kiểm chứng thật trong chính project đó) — file này là baseline áp dụng khi rule riêng không nói gì khác.
>
> File này là **canonical source** — nội dung được nhúng trực tiếp (embed) vào `CLAUDE.md` của từng project con để đảm bảo luôn được nạp tự động dù project đó được mở độc lập hay mở chung cả workspace (không dựa vào việc AI có tự quyết định đọc file cha hay không). **Khi sửa file này, phải đồng bộ lại đúng y hệt vào từng `CLAUDE.md` đã nhúng** (xem danh sách ở cuối file) — không sửa 1 nơi rồi để các nơi khác lệch.

**Tradeoff:** Các quy tắc này thiên về thận trọng hơn tốc độ. Với việc nhỏ/tầm thường, dùng phán đoán hợp lý thay vì áp dụng máy móc.

## 1. Suy nghĩ trước khi code

**Đừng giả định. Đừng giấu sự mơ hồ. Nêu rõ trade-off.**

Trước khi implement:
- Nêu rõ giả định của bạn. Nếu không chắc, hỏi.
- Nếu có nhiều cách hiểu, trình bày cả — đừng tự chọn 1 cách âm thầm.
- Nếu có cách đơn giản hơn, nói ra. Phản biện khi cần thiết.
- Nếu có gì không rõ, dừng lại. Gọi tên đúng chỗ đang mơ hồ. Hỏi.

## 2. Đơn giản trước tiên

**Code tối thiểu để giải quyết đúng vấn đề. Không có gì mang tính suy đoán.**

- Không thêm tính năng ngoài những gì đã yêu cầu.
- Không tạo abstraction cho code chỉ dùng 1 lần.
- Không thêm "tính linh hoạt"/"khả năng cấu hình" nếu không ai yêu cầu.
- Không viết error handling cho tình huống không thể xảy ra.
- Nếu viết 200 dòng mà có thể rút còn 50 — viết lại.

Tự hỏi: "1 senior engineer có thấy cái này bị overcomplicated không?" Nếu có — đơn giản hoá.

## 3. Thay đổi có phẫu thuật (surgical)

**Chỉ đụng vào đúng chỗ cần. Chỉ dọn dẹp phần mình gây ra.**

Khi sửa code có sẵn:
- Đừng "cải thiện" code/comment/format ở chỗ lân cận không liên quan.
- Đừng refactor những gì không hỏng.
- Giữ đúng style hiện có, kể cả khi bạn sẽ làm khác đi nếu viết mới.
- Nếu thấy dead code không liên quan — nêu ra, đừng tự xoá.

Khi thay đổi của bạn tạo ra phần thừa (orphan):
- Xoá import/biến/hàm mà CHÍNH thay đổi của bạn làm chúng không còn dùng.
- Đừng xoá dead code có sẵn từ trước trừ khi được yêu cầu.

Phép thử: mỗi dòng thay đổi phải truy ngược được thẳng tới yêu cầu của người dùng.

## 4. Thực thi hướng-mục-tiêu (goal-driven)

**Định nghĩa tiêu chí thành công. Lặp lại tới khi verify được.**

Biến task thành mục tiêu verify được:
- "Thêm validation" → "Viết test cho input không hợp lệ, rồi làm cho test pass"
- "Sửa bug" → "Viết 1 test tái hiện đúng bug, rồi làm cho test pass"
- "Refactor X" → "Đảm bảo test pass cả trước và sau khi refactor"

Với task nhiều bước, nêu ngắn gọn 1 kế hoạch:
```
1. [Bước] → verify: [cách kiểm tra]
2. [Bước] → verify: [cách kiểm tra]
3. [Bước] → verify: [cách kiểm tra]
```

Tiêu chí thành công rõ ràng giúp bạn tự lặp độc lập. Tiêu chí mơ hồ ("làm cho nó chạy") đòi hỏi phải hỏi lại liên tục.

---

**Các quy tắc này đang có tác dụng nếu:** diff có ít thay đổi không cần thiết hơn, ít phải viết lại do overcomplicated hơn, và câu hỏi làm rõ xuất hiện TRƯỚC khi implement thay vì sau khi đã mắc lỗi.

---

## Danh sách nơi đã nhúng nội dung file này (cập nhật khi thêm project mới)

- `CareAi/CLAUDE.md`
- `dvc-api/CLAUDE.md`
- `salon-web/CLAUDE.md`
- `beverage-web/CLAUDE.md`
- `velox-web/CLAUDE.md`
