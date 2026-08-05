---
name: build-app
description: Xây 1 app/feature hoàn chỉnh từ 1 câu mô tả, qua chu trình đa-agent phân tích → thiết kế → (build → test → review) lặp theo milestone. User-invoked — gõ /build-app kèm mô tả app.
disable-model-invocation: true
---

# build-app

Biến 1 mô tả app thành app hoàn chỉnh, đã verify thật — qua sub-agent tách theo giai đoạn để giữ context của main thread nhỏ gọn, tránh nổ token khi app có nhiều milestone.

## Nguyên lý (áp dụng xuyên suốt, không chỉ đọc 1 lần)

1. **Phân tích + thiết kế chỉ chạy 1 LẦN, ở đầu.** "Lặp" trong skill này là **vòng milestone** (build→test→review), không phải lặp lại cả 5 giai đoạn mỗi lần. Đây là điểm tiết kiệm token lớn nhất — phân tích/thiết kế là chỗ đáng tốn suy nghĩ, chỉ nên trả giá đúng 1 lần.
2. **Mỗi giai đoạn nặng = 1 sub-agent qua `Agent` tool.** Sub-agent tự đọc/ghi file, chỉ trả báo cáo <200 từ. Main thread KHÔNG đọc lại nguyên văn file sub-agent đã xử lý — tin báo cáo, chỉ tự xác nhận bằng lệnh trực tiếp (`git diff --stat`, chạy test) khi cần.
3. **Artifact thay hội thoại.** Spec/plan/milestone sống trong 1 file (`plan file`, dưới `.claude/app-plans/`). Prompt cho sub-agent trỏ `path:section`, không dán lại nội dung.
4. **Cổng phê duyệt trước build.** Plan phải qua `ExitPlanMode` được duyệt trước khi bất kỳ builder sub-agent nào chạy — build sai kế hoạch là chỗ tốn token nhất để sửa lại.
5. **Trần vòng fix = 2.** Mỗi milestone tối đa 2 vòng build→review-fix. Còn CONFIRMED finding sau vòng 2 → dừng, hỏi người dùng quyết định — đừng tự lặp vô hạn.
6. **Tái dùng, không phát minh lại.** Nếu target là CareAi factory, phân tích+thiết kế giao thẳng cho `.claude/APP_BUILD_PLAYBOOK.md` mục 1 Bước 1-5 (đã kiểm chứng bằng thực chiến — đừng viết lại). Milestone tầm thường (đổi copy, config nhỏ, 1-2 dòng) → làm trực tiếp ở main thread, đừng spawn agent chỉ để tiết kiệm 1 lệnh `Edit`.
7. **`/code-review` là `disable-model-invocation` — KHÔNG gọi được qua `Skill` tool, kể cả từ trong skill này** (đã tự kiểm chứng: gọi thẳng bị lỗi "cannot be used with Skill tool due to disable-model-invocation"). Bước review ở Giai đoạn 2 phải spawn 1 sub-agent review trực tiếp (Agent tool, đóng vai reviewer nghiêm khắc, dùng `ReportFindings`-style output CONFIRMED/PLAUSIBLE) — không phải gọi skill.

## Bước 0 — Xác định nhánh

Từ mô tả app + thư mục hiện tại, xác định:
- **Nhánh A**: app mới trong CareAi factory (React Native, bundle-id switching) — xem `ARCHITECTURE.md` mục 1.
- **Nhánh B**: app/feature mới trong 1 project sẵn có ngoài CareAi (`dvc-api`, `salon-web`, `beverage-web`, `reviews-web`, `velox-web`, `dvc-worker`).
- **Nhánh C**: app hoàn toàn mới, chưa thuộc project nào trong workspace này.

Nếu không rõ, hỏi bằng `AskUserQuestion` — đừng đoán, vì mỗi nhánh có nghi thức phân tích khác hẳn nhau.

## Giai đoạn 1 — PHÂN TÍCH + THIẾT KẾ (chạy đúng 1 lần)

### Nhánh A (CareAi)
Làm đúng Bước 1→5 của `.claude/APP_BUILD_PLAYBOOK.md` mục 1 (nghiên cứu, tự phản biện, trình bày, Plan Mode, lưu plan vào `.claude/app-plans/<app-slug>.md`). Không lặp lại nội dung các bước đó ở đây — đọc thẳng playbook, coi nó là nguồn sự thật duy nhất cho nhánh này.

### Nhánh B/C
1. Spawn 1 sub-agent (`Explore` nếu chỉ cần định vị pattern có sẵn; `general-purpose` nếu cần vừa nghiên cứu vừa phác thảo) để: định vị convention/pattern hiện có trong project đích (nhánh B), phác thảo bảng tính năng, data model sơ bộ, danh sách màn hình/route. Áp dụng **bài kiểm tra sắc bén** cho từng tính năng (tần suất thật / phép thử "xoá đi" / phép thử "5 phút Excel-Notes" / neo giá — xem `.claude/APP_BUILD_PLAYBOOK.md` mục 9.1, tiêu chuẩn này dùng chung được, không riêng CareAi). Agent tự viết kết quả vào `.claude/app-plans/<slug>.md` (copy từ `.claude/app-plans/_TEMPLATE_GENERIC.md`), KHÔNG trả nội dung dài về main thread — chỉ báo "đã viết plan nháp vào path X" + tóm tắt 3 dòng.
2. Đọc lại đúng file plan đó (1 lần).
3. `EnterPlanMode` dựa trên plan draft đó, tinh chỉnh + chốt danh sách milestone. Mỗi milestone phải cho ra thứ **verify được ngay khi xong** — không milestone nào là "nửa chức năng". `ExitPlanMode` xin duyệt.
4. Sau khi duyệt: cập nhật `.claude/app-plans/<slug>.md` với plan CHÍNH THỨC (ghi đè bản nháp — file tạm plan-mode bị ghi đè ở lần sau, xem playbook mục 5 để hiểu lý do). `TodoWrite` tạo 1 todo/milestone.

**Hoàn thành giai đoạn khi**: có 1 file plan đã duyệt, git-track được, liệt kê milestone theo đúng thứ tự build kèm tiêu chí verify cụ thể cho từng milestone (không phải "làm cho nó chạy").

## Giai đoạn 2 — VÒNG LẶP MILESTONE (build → test → review) × N

Với mỗi milestone theo đúng thứ tự trong plan:

1. `TodoWrite` đánh dấu `in_progress`.
2. **Milestone tầm thường** (1-2 file, không cần explore) → làm trực tiếp bằng `Edit`/`Write` ở main thread, bỏ qua bước 3, sang bước 4.
   **Milestone cần build nhiều file/logic** → spawn 1 **builder sub-agent** (foreground — bước sau phụ thuộc kết quả). Prompt tự chứa: mô tả milestone (trỏ `plan-file:section`, không dán lại), file pattern mẫu cụ thể nếu có, lệnh verify chính xác cần chạy (`tsc --noEmit`, `jest <file>`, `npm run build`...). Yêu cầu: nếu milestone có business logic quan trọng (tính toán, ngưỡng, merge dữ liệu) → viết + CHẠY THẬT test tương ứng ngay trong cùng lượt (không tách thêm sub-agent test riêng — gộp lại đỡ 1 round-trip không cần thiết). Báo cáo cuối <200 từ: file đã đổi, lệnh verify đã chạy + kết quả thật.
3. **Spawn reviewer** — 1 sub-agent (`general-purpose`) đóng vai reviewer nghiêm khắc, giới hạn đúng diff của milestone này (`git diff --stat` trước để xác nhận phạm vi khớp milestone, không review lan ra cả repo). Yêu cầu agent dùng `ReportFindings` (verdict CONFIRMED/PLAUSIBLE, đã tự chạy lệnh xác minh chứ không đoán). KHÔNG gọi skill `/code-review` qua `Skill` tool — nó bị chặn (`disable-model-invocation`, chỉ chạy khi người dùng tự gõ).
4. Còn CONFIRMED finding → quay lại bước 2, gửi tiếp cho ĐÚNG builder sub-agent đó qua `SendMessage` (dùng `agentId` đã spawn ở bước 2, không tạo agent mới — giữ nguyên context, không phân tích lại từ đầu) kèm danh sách finding cụ thể. Đếm vòng — sau vòng thứ 2 vẫn còn CONFIRMED → dừng vòng lặp milestone này, báo người dùng rõ finding còn lại để họ quyết định (không tự ý bỏ qua, không tự lặp vòng 3).
5. Sạch (hoặc chỉ còn finding không phải CONFIRMED) → `TodoWrite` đánh dấu `completed`, sang milestone kế tiếp.

**Hoàn thành giai đoạn khi**: mọi milestone ở trạng thái `completed`, hoặc đã dừng chờ người dùng quyết định 1 finding cụ thể.

## Giai đoạn 3 — TỔNG KẾT (đúng 1 lần, ở cuối)

1. Chạy verify toàn cục ĐÚNG 1 LẦN (test suite đầy đủ / `tsc --noEmit` toàn project) — không chạy lại verify của milestone đã pass trước đó.
2. `git diff --stat` xác nhận phạm vi thay đổi khớp plan, không lan ra file ngoài phạm vi (đặc biệt file dùng chung nếu Nhánh A — xem playbook mục 5 đoạn cuối, mục 6).
3. Cập nhật plan file: trạng thái → hoàn thành, mục Verification ghi kết quả THẬT (lệnh + output), thêm dòng Changelog nếu phát hiện bài học mới (nhánh A: cân nhắc thêm luôn vào playbook nếu bài học có thể lặp ở app khác — xem playbook mục 7).
4. Báo cáo ngắn cho người dùng: đã xây gì, verify bằng gì (cụ thể), việc gì còn cần làm thủ công. Không tóm tắt lại từng bước đã đi qua.

## Khi nào KHÔNG dùng skill này

- Sửa 1 bug/1 tính năng nhỏ trong app đã có → sửa trực tiếp rồi dùng `/code-review`, không cần cả chu trình này (chi phí spawn sub-agent không đáng cho việc nhỏ).
- Mô tả app chưa đủ để phác thảo bảng tính năng → hỏi lại người dùng trước khi vào Giai đoạn 1, đừng tự bịa cho có cái để chạy.
