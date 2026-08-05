import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import * as api from "../lib/api";
import type { ItemType } from "../lib/api";
import { CATEGORIES, RADIUS_OPTIONS_KM, DEFAULT_RADIUS_KM, DEFAULT_LOCATION, TYPE_LABELS } from "../lib/constants";
import { ItemCard } from "../components/ItemCard";
import { Button, Input, Select } from "../components/ui";

type TypeFilter = ItemType | "all";
type SortMode = "distance" | "newest";

const TYPE_OPTIONS: { value: TypeFilter; label: string }[] = [
  { value: "all", label: "Tất cả" },
  { value: "lend_free", label: TYPE_LABELS.lend_free },
  { value: "rent_paid", label: TYPE_LABELS.rent_paid },
  { value: "donate", label: TYPE_LABELS.donate },
];

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();

  const lat = Number(searchParams.get("lat")) || DEFAULT_LOCATION.lat;
  const lng = Number(searchParams.get("lng")) || DEFAULT_LOCATION.lng;
  const radius = Number(searchParams.get("radius")) || DEFAULT_RADIUS_KM;
  const type = (searchParams.get("type") as TypeFilter) || "all";
  const category = searchParams.get("category") || "all";
  const sort = (searchParams.get("sort") as SortMode) || "distance";

  const [results, setResults] = useState<api.ItemSearchResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [manualLat, setManualLat] = useState(String(lat));
  const [manualLng, setManualLng] = useState(String(lng));

  // Keep the manual inputs in sync when lat/lng change from elsewhere
  // (geolocation button, or arriving from Home's "Tìm quanh đây" with
  // lat/lng already in the URL).
  useEffect(() => {
    setManualLat(String(lat));
    setManualLng(String(lng));
  }, [lat, lng]);

  // Functional update — reads the CURRENT params at the moment setSearchParams
  // actually applies the change, not whatever `searchParams` this closure was
  // created with. Matters because updateParams is passed into async callbacks
  // (geolocation) that can fire well after a render where the user has since
  // changed another filter; building `next` from a captured `searchParams`
  // would silently revert that other filter back to its stale value.
  function updateParams(patch: Record<string, string | null>) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      for (const [key, value] of Object.entries(patch)) {
        if (value === null || value === "") next.delete(key);
        else next.set(key, value);
      }
      return next;
    });
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => updateParams({ lat: String(pos.coords.latitude), lng: String(pos.coords.longitude) }),
      () => {
        // denied/unavailable — leave current lat/lng as-is.
      },
      { timeout: 5000 },
    );
  }

  function applyManualLocation() {
    const parsedLat = Number(manualLat);
    const parsedLng = Number(manualLng);
    if (Number.isNaN(parsedLat) || Number.isNaN(parsedLng)) return;
    updateParams({ lat: String(parsedLat), lng: String(parsedLng) });
  }

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .searchItems({
        lat,
        lng,
        radius_km: radius,
        category: category !== "all" ? category : undefined,
        type: type !== "all" ? type : undefined,
        limit: 48,
      })
      .then((data) => {
        if (!cancelled) {
          setResults(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setResults([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng, radius, type, category]);

  const sorted =
    sort === "newest" && results
      ? [...results].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      : results;

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-display text-ink mb-6">Tìm đồ quanh bạn</h1>

      <div className="space-y-5 mb-8">
        {/* Location */}
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="secondary" size="sm" onClick={useCurrentLocation}>
            Dùng vị trí hiện tại
          </Button>
          <span className="text-xs text-ink-faint">hoặc nhập toạ độ:</span>
          <Input
            size="sm"
            className="w-28"
            type="number"
            step="any"
            value={manualLat}
            onChange={(e) => setManualLat(e.target.value)}
            onBlur={applyManualLocation}
            aria-label="Vĩ độ"
          />
          <Input
            size="sm"
            className="w-28"
            type="number"
            step="any"
            value={manualLng}
            onChange={(e) => setManualLng(e.target.value)}
            onBlur={applyManualLocation}
            aria-label="Kinh độ"
          />
        </div>

        {/* Radius */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-ink-soft mr-1">Bán kính:</span>
          {RADIUS_OPTIONS_KM.map((km) => (
            <button
              key={km}
              onClick={() => updateParams({ radius: String(km) })}
              className={`rounded-full px-3.5 py-1.5 text-sm border transition-colors ${
                radius === km ? "bg-brand text-white border-brand" : "border-line text-ink-soft hover:border-brand hover:text-brand"
              }`}
            >
              {km}km
            </button>
          ))}
        </div>

        {/* Type */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-ink-soft mr-1">Loại:</span>
          {TYPE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => updateParams({ type: opt.value === "all" ? null : opt.value })}
              className={`rounded-full px-3.5 py-1.5 text-sm border transition-colors ${
                type === opt.value ? "bg-accent text-white border-accent" : "border-line text-ink-soft hover:border-accent hover:text-accent"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Category */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-ink-soft mr-1">Danh mục:</span>
          <button
            onClick={() => updateParams({ category: null })}
            className={`rounded-full px-3.5 py-1.5 text-sm border transition-colors ${
              category === "all" ? "bg-brand text-white border-brand" : "border-line text-ink-soft hover:border-brand hover:text-brand"
            }`}
          >
            Tất cả
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => updateParams({ category: category === cat ? null : cat })}
              className={`rounded-full px-3.5 py-1.5 text-sm border transition-colors ${
                category === cat ? "bg-brand text-white border-brand" : "border-line text-ink-soft hover:border-brand hover:text-brand"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-ink-soft">Sắp xếp:</span>
          <Select size="sm" value={sort} onChange={(e) => updateParams({ sort: e.target.value === "distance" ? null : e.target.value })}>
            <option value="distance">Gần nhất</option>
            <option value="newest">Mới đăng</option>
          </Select>
        </div>
      </div>

      {loading ? (
        <ResultsSkeleton />
      ) : !sorted || sorted.length === 0 ? (
        <div className="py-24 text-center text-ink-soft">
          <p className="mb-2">Chưa tìm thấy đồ nào trong phạm vi này.</p>
          <p className="text-sm">Thử mở rộng bán kính tìm kiếm hoặc bỏ bớt bộ lọc.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {sorted.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}

function ResultsSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-line overflow-hidden animate-pulse">
          <div className="aspect-[4/3] bg-line" />
          <div className="p-3.5 space-y-2">
            <div className="h-3 w-full bg-line rounded" />
            <div className="h-3 w-2/3 bg-line rounded" />
            <div className="h-4 w-1/2 bg-line rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}
