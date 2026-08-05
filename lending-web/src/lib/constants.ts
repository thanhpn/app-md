import type { ItemStatus, ItemType } from "./api";

// Hardcoded per W2 scope — no categories-list endpoint exists (see api.ts's
// searchItems comment), these are the 8 real categories from the seed data
// (dvc-api/apps/lending/seed/fixtures.json).
export const CATEGORIES = [
  "dụng cụ sửa nhà",
  "điện tử",
  "đồ nhà bếp",
  "đồ cắm trại",
  "thời trang & dạ hội",
  "sách",
  "đồ trẻ em",
  "thể thao",
] as const;

export const TYPE_LABELS: Record<ItemType, string> = {
  lend_free: "Miễn phí mượn",
  rent_paid: "Thuê trả phí",
  donate: "Tặng",
};

// FR-7's exact state machine: available<->reserved, reserved->given_out.
// Nothing transitions out of given_out, nothing jumps available->given_out
// directly — see dvc-api/apps/lending/internal/domain/item.go.
export const STATUS_LABELS: Record<ItemStatus, string> = {
  available: "Còn sẵn",
  reserved: "Đang giữ chỗ",
  given_out: "Đã cho đi",
};

export const NEXT_STATUSES: Record<ItemStatus, ItemStatus[]> = {
  available: ["reserved"],
  reserved: ["available", "given_out"],
  given_out: [],
};

export const RADIUS_OPTIONS_KM = [1, 3, 5, 10, 25, 50] as const;
export const DEFAULT_RADIUS_KM = 5;

// Hồ Gươm — graceful fallback when geolocation is denied/unavailable.
export const DEFAULT_LOCATION = { lat: 21.0285, lng: 105.8542 };
