import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import * as api from "../lib/api";
import { CATEGORIES, DEFAULT_LOCATION } from "../lib/constants";
import { ItemCard } from "../components/ItemCard";
import { Button } from "../components/ui";

// Home = "mồi" per the plan: prove the app is useful in <30s without login —
// hero CTA + category chips + a nearby-items preview feed. Full filter UI
// lives in Search.tsx (W2's other page); Home only needs a fast entry point.
export default function Home() {
  const navigate = useNavigate();
  const [coords, setCoords] = useState(DEFAULT_LOCATION);
  const [items, setItems] = useState<api.ItemSearchResult[] | null>(null);
  const [loading, setLoading] = useState(true);

  // Best-effort geolocation on mount — never blocks the page (starts with
  // the Hồ Gươm fallback immediately, upgrades silently if/when granted).
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => {
        // denied/unavailable — keep the fallback, no error UI needed.
      },
      { timeout: 5000 },
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .searchItems({ lat: coords.lat, lng: coords.lng, limit: 8 })
      .then((data) => {
        if (!cancelled) {
          setItems(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setItems([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [coords]);

  // Every outbound link to /search reuses whatever `coords` ended up being
  // (real geolocation once resolved, Hồ Gươm fallback until then/if denied) —
  // so category chips and "Xem tất cả" don't silently drop the user's real
  // location back to the hardcoded default the way a bare `/search` link would.
  function searchLink(params: Record<string, string> = {}) {
    const qs = new URLSearchParams({ lat: String(coords.lat), lng: String(coords.lng), ...params });
    return `/search?${qs.toString()}`;
  }

  function handleFindNearby() {
    if (!navigator.geolocation) {
      navigate(`/search?lat=${DEFAULT_LOCATION.lat}&lng=${DEFAULT_LOCATION.lng}`);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => navigate(`/search?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`),
      () => navigate(`/search?lat=${DEFAULT_LOCATION.lat}&lng=${DEFAULT_LOCATION.lng}`),
      { timeout: 5000 },
    );
  }

  return (
    <div>
      <section className="mx-auto max-w-6xl px-6 py-20 text-center">
        <h1 className="text-4xl sm:text-5xl text-ink mb-4 font-display">Mượn đồ quanh bạn — không cần mua</h1>
        <p className="text-ink-soft text-lg mb-8">Tìm, mượn, thuê hoặc xin đồ từ những người ở gần bạn — không cần mua mới.</p>
        <Button size="lg" onClick={handleFindNearby}>
          Tìm quanh đây
        </Button>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-10">
        <div className="flex flex-wrap gap-2 justify-center">
          {CATEGORIES.map((cat) => (
            <Link
              key={cat}
              to={searchLink({ category: cat })}
              className="rounded-full border border-line bg-surface px-4 py-2 text-sm text-ink-soft hover:border-brand hover:text-brand transition-colors"
            >
              {cat}
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="flex items-end justify-between mb-6">
          <h2 className="text-2xl text-ink font-display">Đồ gần bạn</h2>
          <Link to={searchLink()} className="text-sm font-semibold text-brand hover:text-brand-dark">
            Xem tất cả →
          </Link>
        </div>

        {loading ? (
          <PreviewSkeleton />
        ) : !items || items.length === 0 ? (
          <div className="py-16 text-center text-ink-soft">
            <p>Chưa tìm thấy đồ nào gần bạn. Thử mở rộng bán kính ở trang tìm kiếm.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function PreviewSkeleton() {
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
