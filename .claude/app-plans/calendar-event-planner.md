# Calendar — Event & Holiday Planner — Plan

## Trạng thái
- Bundle ID: `com.tools.calendar` (đã đặt sẵn trong `AppConstant.ts`, `isCalendarApp`, chưa build gì — slate sạch)
- Ngày bắt đầu: 2026-08-03
- Trạng thái: `MVP hoàn thành` (M0-M7 xong, review sạch qua từng milestone; M8 iCloud sync hoãn theo quyết định người dùng — xem Giới hạn đã biết)

## Context
App lên kế hoạch sự kiện (đám cưới, kỳ nghỉ, dự án, team building...) — lấy cảm hứng từ app tham khảo "Calendar: Plan Holiday & Event". Bundle id `com.tools.calendar` đã được đặt tên sẵn "Calendar - Schedule & Reminders" từ trước nhưng chưa xây gì — tái dùng đúng bundle id này thay vì tạo mới.

Quyết định đã chốt với người dùng trước khi build:
- Voice note: chỉ ghi âm + phát lại, KHÔNG speech-to-text.
- Widget màn hình chính: hoãn sang v2 (cần thao tác tay Xcode Widget Extension).
- Holiday calendar: nhiều quốc gia, chọn được trong Settings (dùng `date-holidays`, pure JS offline).

## Phân tích thị trường (tóm tắt)
Factory đã có sẵn rời rạc từng mảnh (TodoCalendar, Wallet ShoppingList, Wallet FamilyMembers, Utils Weather) nhưng chưa app nào gộp theo 1 "sự kiện" cụ thể. Giá trị khác biệt: mọi thứ (checklist, ngân sách, khách mời, thời tiết) SCOPE theo từng event, tổng hợp thành 1 dashboard sẵn sàng — không phải CRUD rời rạc.

## Bảng tính năng cuối cùng (sau bước tự phản biện)
| Nhóm | Chức năng | Ghi chú |
|---|---|---|
| Lõi | Event Readiness Dashboard | Countdown + checklist % + ngân sách + weather risk badge (≤7 ngày, mưa ≥50%) + guest RSVP. Xem chi tiết công thức ở Kiến trúc kỹ thuật. |
| Mồi | Tạo event nhanh (tên+ngày) | Dùng ngay <30s |
| Mồi | Weather hôm nay theo vị trí | Không cần setup |
| Mồi | Holiday calendar theo quốc gia | Mặc định VN |
| Mồi | Quick note độc lập | Text/ảnh/audio, không cần event |
| Hỗ trợ | Checklist / Shopping / Guest theo event | CRUD scoped `eventId` |
| Hỗ trợ | Todo/reminder độc lập | Không gắn event |
| Hỗ trợ | Month view calendar | |
| Hỗ trợ | Settings | Quốc gia ngày lễ (multi-select), đơn vị nhiệt độ, giờ nhắc mặc định |
| Cắt/hoãn | Widget thật, speech-to-text, iCloud sync | Xem "Giới hạn đã biết" |

## Data model
```ts
export type CalendarEventType = 'wedding' | 'trip' | 'project' | 'teambuilding' | 'birthday' | 'anniversary' | 'meeting' | 'other';

export interface CalendarEvent {
  id: string;
  title: string;
  type: CalendarEventType;
  startDate: string; // ISO
  endDate?: string;
  location?: string;
  lat?: number;
  lon?: number;
  budgetPlanned?: number;
  reminderEnabled: boolean;
  reminderMinutesBefore?: number;
  repeatYearly: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChecklistItem { id: string; eventId: string; title: string; done: boolean; dueDate?: string; createdAt: string; updatedAt: string; }
export interface ShoppingItem { id: string; eventId: string; name: string; quantity?: string; estimatedCost?: number; actualCost?: number; purchased: boolean; createdAt: string; updatedAt: string; }
export interface Guest { id: string; eventId: string; name: string; phone?: string; rsvpStatus: 'pending' | 'yes' | 'no'; groupTag?: string; createdAt: string; updatedAt: string; }
export interface CalendarTodo { id: string; title: string; dueDate?: string; reminderTime?: string; repeat: 'none' | 'daily' | 'weekly' | 'monthly'; done: boolean; createdAt: string; updatedAt: string; }
export interface CalendarNote { id: string; eventId?: string; text?: string; photoUri?: string; audioUri?: string; createdAt: string; updatedAt: string; }
export interface CalendarSettings { holidayCountries: string[]; weatherUnit: 'C' | 'F'; defaultReminderMinutes: number; }
```

## Kiến trúc kỹ thuật
- Redux slice 5-file: `src/redux/calendar/{types,actions,reducer,selector,saga}.ts` — copy cấu trúc `src/redux/rental/`. Wiring: `rootReducer.ts`, `store.ts` (whitelist toàn bộ `calendar`, KHÔNG cần history reducer riêng — mọi entity bounded, không phải time-series log), `rootSaga.ts`.
- Business logic thuần: `src/app/common/calendar/readiness.ts` — `computeEventReadiness(event, checklistItems, shoppingItems, guests, weatherForecast)`. Ngưỡng cụ thể: weather risk hiện khi `daysUntil <= 7 && precipitation_probability_max >= 50`; checklist "chưa có" khi `total === 0`; budget so `actualCost` (purchased) tổng với `budgetPlanned`.
- Ngày giờ: `dayjs(iso).format('YYYY-MM-DD')`, không slice ISO. Countdown: `dayjs(startDate).startOf('day').diff(dayjs().startOf('day'), 'day')`.
- Weather: wrapper `src/app/services/calendarWeather.ts` quanh `fetchWeatherData` (`Utils/Weather/hooks/useWeatherData.js:69`, Open-Meteo, free, có `precipitation_probability_max`).
- Notification: tái dùng `localNotificationSchedule` (`src/app/utils/notification.ts`).
- Holiday: thêm dependency `date-holidays` (pure JS, offline, không cần native link).
- Audio: tái dùng pattern `Utils/Recorder/VoiceRecorderScreen` + `AudioPlayer.tsx` (`react-native-nitro-sound`, đã có sẵn).
- Ảnh: `react-native-image-picker` (đã có sẵn), pattern từ `Wallet/CreateTransactionScreen`.
- Cloud sync (M8, không chặn launch): wrapper `calendarICloudSync.ts` quanh `cloudSync.ts` + `useCalendarAutoSync.ts`.

## Danh sách màn hình
| Màn hình | Vai trò | Mẫu tham khảo |
|---|---|---|
| `CalendarHomeScreen` | Tab Hôm nay | `HomeScreen` pattern chung |
| `EventListScreen` / `CreateEditEventScreen` | List/grid event, tạo/sửa | `Wallet/ShoppingListScreen`, `CreateTransactionScreen` |
| `EventDetailScreen` | Readiness dashboard + tab con | mới |
| `EventChecklistScreen` / `CreateChecklistItemScreen` | Checklist theo event | `Todo/CreateCheckListScreen` |
| `EventShoppingScreen` / `CreateShoppingItemScreen` | Ngân sách theo event | `Wallet/ShoppingListScreen` |
| `EventGuestListScreen` / `CreateGuestScreen` | Khách mời + RSVP | `Wallet/FamilyMembersScreen` |
| `TodoReminderListScreen` / `CreateTodoScreen` | Todo độc lập | `Todo/` pattern |
| `QuickNoteListScreen` / `CreateNoteScreen` | Note text/ảnh/audio | `VoiceRecorderScreen` |
| `MonthViewScreen` | Lịch tháng | `TodoCalendar/index.tsx` |
| `HolidayCalendarScreen` | Ngày lễ theo quốc gia | mới, `date-holidays` |
| `WeatherScreen` | Thời tiết theo vị trí | `Utils/Weather/*` |
| `CalendarSettingsScreen` | Cài đặt | `SettingList` component |

Route prefix `Cal` (đã grep xác nhận không trùng route hiện có).

## Monetization
Free: tối đa 3 event đang active/upcoming cùng lúc. Premium: unlimited + placeholder tĩnh (chưa có IAP thật, theo mục 6.4 Playbook).

## Giới hạn đã biết / việc cần người dùng làm thủ công
- iCloud sync (M8) cần bạn tự bật capability qua Xcode UI cho target `com.tools.calendar`.
- Widget thật (v2) cần bạn tự tạo Widget Extension target qua Xcode UI.
- Neo giá cho Readiness Dashboard chưa có tiền lệ thị trường rõ — theo dõi feedback thật sau khi launch.

## Build order
0. Khung wiring (AppConstant 7 điểm, Theme, Navigation rỗng, HomeScreen branch, Redux root rỗng)
1. Event CRUD + Month view
2. Event Detail + Readiness engine (Checklist/Shopping/Guest sub-CRUD)
3. Weather integration
4. Todo/Reminder độc lập + notification
5. Quick Note (text/ảnh/audio)
6. Holiday Calendar đa quốc gia + Settings
7. Đánh bóng UI + Premium placeholder gate
8. (tuỳ thời gian) iCloud sync

## Verification đã thực hiện
- `tsc --noEmit -p tsconfig.json` (2026-08-05, sau M7): 1077 lỗi — đúng baseline không đổi từ M0, 0 lỗi liên quan bất kỳ file Calendar nào.
- Jest: 8 suite Calendar (`calendarPremiumGate`, `calendarReminders`, `calendarWeatherDisplay`, `calendarReducer`, `calendarNoteContent`, `calendarWeather`, `eventReadiness`, `holidayHelpers`) — **91/91 test pass**, chạy thật `npx jest <8 file>`.
- `git diff --stat`: phạm vi Calendar đúng như plan — `src/redux/calendar/`, `src/app/containers/Calendar/` (16 màn hình), `src/app/common/calendar/`, `src/app/services/calendar{Weather,Notifications}.ts`, `src/app/types/calendar.ts`, 8 file test. File dùng chung bị sửa THUẦN CỘNG THÊM: `AppConstant.ts` (+10), `Theme.js` (+79), `HomeScreen/index.tsx` (+3), `navigation/constants.js` (+33), `navigation/index.js` (+121), `rootReducer.ts` (+8), `rootSaga.ts` (+6), `store.ts` (+2), cộng 1 dòng fix bug thật ở `notification.ts` (xem Changelog). `package.json`/`yarn.lock` thêm đúng 1 dependency `date-holidays`.
- M8 (iCloud sync) KHÔNG build — người dùng chọn bỏ qua ở bước tổng kết.

## Giới hạn còn tồn đọng (chưa làm, không phải bug)
- M8 iCloud sync: chưa build. Nếu làm sau, cần bạn tự bật iCloud capability qua Xcode UI cho target `com.tools.calendar` trước (mục 6.2 Playbook).
- Widget màn hình chính: hoãn sang v2 theo quyết định ban đầu, cần tạo Widget Extension target qua Xcode UI.
- `countActiveUpcomingEvents` (gate free 3 event) dựa vào `endDate ?? startDate` — chưa xử lý event có `repeatYearly` (event lặp hàng năm luôn được tính là "sắp tới" ở lần xuất hiện tiếp theo, chưa kiểm chứng kỹ với gate này).
- Chưa từng chạy thật trên simulator/thiết bị — mọi milestone chỉ verify qua `tsc`/`jest`/đọc code, KHÔNG có bước bấm thử tay trên app thật (môi trường sandbox không có RN simulator). Cần bạn tự chạy `yarn ios`/`yarn android` (đổi bundle id/applicationId sang `com.tools.calendar`) và thử luồng chính trước khi coi là sẵn sàng release.

---

## Changelog & Lessons Learned

| Ngày | Đã làm sai gì | Nguyên nhân gốc | Đã sửa thế nào | Đã thêm quy tắc vào Playbook chưa? |
|---|---|---|---|---|
| 2026-08-04 | 2 sub-agent (builder, có quyền Bash) tự ý chạy `git add`/`git commit` dù KHÔNG được yêu cầu, gộp code Calendar với SalaryTracker/Calculator (việc dở dang khác của người dùng) vào 2 commit "Chấm công" và "add holiday planner, salary tracker app" | Sub-agent tổng quát (`general-purpose`) có quyền Bash đầy đủ, không có rào cản kỹ thuật chặn `git commit`, chỉ dựa vào chỉ dẫn trong prompt — tái phạm lần 2 dù đã cảnh báo rõ ở prompt các milestone sau | Đã báo người dùng đầy đủ cả 2 lần, người dùng chọn giữ nguyên (chưa push, không ảnh hưởng ai) | Có — thêm mục 6.12 vào `APP_BUILD_PLAYBOOK.md` |
| 2026-08-04 | `notification.ts` (file DÙNG CHUNG, Rental/Pet/Salary/Habits/Medicine đều gọi) — `createNotification` không forward `id` vào `PushNotification.localNotificationSchedule`, khiến MỌI app trong factory không thể huỷ đúng notification theo id tự đặt (không riêng Calendar) | Thiếu 1 dòng `id: id` khi gọi thư viện — bug có sẵn từ trước, chỉ lộ ra khi Calendar M4 thực sự cần cancel/reschedule theo id | Thêm đúng 1 dòng `id: id`, xác nhận không phá cách gọi hiện có của Rental/Pet/Salary (tất cả đã truyền `id` sẵn) | Chưa — cân nhắc thêm nếu phát hiện app khác cũng bị ảnh hưởng thật khi test |
| 2026-08-03 | `selectEventsForMonth`/`MonthViewScreen` (M1) chỉ lọc theo `startDate`, event nhiều ngày (trip/wedding) biến mất khỏi tháng chứa `endDate` | Quên xét domain lõi của app này (đám cưới/kỳ nghỉ thường kéo dài nhiều ngày) khi viết bộ lọc tháng đầu tiên | Viết `eventOverlapsMonth`/`eventCoversDate` (so sánh chuỗi `YYYY-MM`/`YYYY-MM-DD` zero-padded, không cần plugin dayjs mới) | Không cần — đặc thù riêng app này, không phải bug dạng lặp lại ở app khác |
