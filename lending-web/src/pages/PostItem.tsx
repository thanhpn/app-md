import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import * as api from "../lib/api";
import { useAuth } from "../lib/auth";
import { CATEGORIES, TYPE_LABELS } from "../lib/constants";
import { Button, ErrorText, Input, Label, Select, Textarea } from "../components/ui";

type Coords = { lat: number; lng: number } | null;

export default function PostItem() {
  const { account, loading, withFreshToken } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [type, setType] = useState<api.ItemType>("lend_free");
  const [rentalPriceNote, setRentalPriceNote] = useState("");
  const [addressLabel, setAddressLabel] = useState("");
  const [coords, setCoords] = useState<Coords>(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return <p className="text-center py-20 text-ink-soft">Đang tải…</p>;
  }
  if (!account) {
    return <Navigate to="/login" replace />;
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationError("Trình duyệt không hỗ trợ định vị.");
      return;
    }
    setLocating(true);
    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocationError("Không lấy được vị trí — vui lòng cho phép truy cập vị trí rồi thử lại.");
        setLocating(false);
      },
      { timeout: 5000 },
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim() || !category || !addressLabel.trim()) {
      setError("Vui lòng điền đầy đủ tiêu đề, danh mục và địa chỉ.");
      return;
    }
    if (type === "rent_paid" && !rentalPriceNote.trim()) {
      setError("Vui lòng nhập giá thuê.");
      return;
    }
    if (!coords) {
      setLocationError("Vui lòng bấm 'Dùng vị trí hiện tại' trước khi đăng — vị trí là bắt buộc.");
      return;
    }

    setSubmitting(true);
    try {
      const item = await withFreshToken((token) =>
        api.createItem(token, {
          title: title.trim(),
          description: description.trim() || undefined,
          category,
          type,
          rental_price_note: type === "rent_paid" ? rentalPriceNote.trim() : undefined,
          lat: coords.lat,
          lng: coords.lng,
          address_label: addressLabel.trim(),
        }),
      );
      navigate(`/items/${item.id}`);
    } catch {
      setError("Không đăng được đồ — vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-display text-ink mb-6">Đăng đồ</h1>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <Label htmlFor="title">Tiêu đề</Label>
          <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>

        <div>
          <Label htmlFor="description">Mô tả</Label>
          <Textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <div>
          <Label htmlFor="category">Danh mục</Label>
          <Select id="category" value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label>Loại</Label>
          <div className="flex flex-wrap gap-4">
            {(Object.keys(TYPE_LABELS) as api.ItemType[]).map((t) => (
              <label key={t} className="flex items-center gap-1.5 text-sm text-ink-soft">
                <input type="radio" name="type" value={t} checked={type === t} onChange={() => setType(t)} />
                {TYPE_LABELS[t]}
              </label>
            ))}
          </div>
        </div>

        {type === "rent_paid" && (
          <div>
            <Label htmlFor="price">Giá thuê</Label>
            <Input
              id="price"
              value={rentalPriceNote}
              onChange={(e) => setRentalPriceNote(e.target.value)}
              placeholder="VD: 50.000đ/ngày"
              required
            />
          </div>
        )}

        <div>
          <Label htmlFor="address">Địa chỉ</Label>
          <Input id="address" value={addressLabel} onChange={(e) => setAddressLabel(e.target.value)} required />
        </div>

        <div>
          <Label>Vị trí</Label>
          <div className="flex items-center gap-3">
            <Button type="button" variant="secondary" size="sm" onClick={useCurrentLocation} disabled={locating}>
              {locating ? "Đang lấy vị trí…" : coords ? "Đã lấy vị trí ✓" : "Dùng vị trí hiện tại"}
            </Button>
            {coords && (
              <span className="text-xs text-ink-faint">
                {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
              </span>
            )}
          </div>
          {locationError && <ErrorText className="mt-1">{locationError}</ErrorText>}
        </div>

        {error && <ErrorText>{error}</ErrorText>}

        <Button type="submit" disabled={submitting}>
          {submitting ? "Đang đăng…" : "Đăng đồ"}
        </Button>
      </form>
    </div>
  );
}
