import { Link } from "react-router-dom";
import type { ItemSearchResult, ItemType } from "../lib/api";
import { TYPE_LABELS } from "../lib/constants";
import { Card } from "./ui/Card";
import { Badge, type BadgeTone } from "./ui/Badge";

// Three distinct but harmonious tones from the existing theme (terracotta
// brand / teal accent / green success) rather than three arbitrary colors —
// see index.css's theme tokens.
const TYPE_TONE: Record<ItemType, BadgeTone> = {
  lend_free: "brand",
  rent_paid: "accent",
  donate: "success",
};

function formatDistance(km: number): string {
  if (km < 1) return `${Math.round(km * 1000)}m`;
  return `${km.toFixed(1)}km`;
}

function ItemImage({ item }: { item: Pick<ItemSearchResult, "photo_keys" | "title"> }) {
  const src = item.photo_keys?.[0];
  if (src) {
    return <img src={src} alt={item.title} className="aspect-[4/3] w-full object-cover" loading="lazy" />;
  }
  return (
    <div className="aspect-[4/3] w-full flex items-center justify-center bg-gradient-to-br from-brand-light to-accent-light">
      <span className="text-3xl font-display font-extrabold text-brand/40">{item.title.charAt(0).toUpperCase()}</span>
    </div>
  );
}

function priceNote(item: ItemSearchResult): string {
  if (item.type === "rent_paid") return item.rental_price_note || "Thuê trả phí";
  if (item.type === "donate") return "Tặng";
  return "Miễn phí";
}

export function ItemCard({ item }: { item: ItemSearchResult }) {
  return (
    <Link to={`/items/${item.id}`} className="group block h-full">
      <Card hover padding="sm" className="h-full flex flex-col overflow-hidden !p-0 group-hover:-translate-y-0.5 transition-transform">
        <div className="relative overflow-hidden rounded-t-2xl bg-canvas">
          <ItemImage item={item} />
          <Badge tone="neutral" className="absolute top-2.5 left-2.5 shadow-sm bg-white/95">
            {formatDistance(item.distance_km)}
          </Badge>
          <Badge tone={TYPE_TONE[item.type]} className="absolute top-2.5 right-2.5 shadow-sm">
            {TYPE_LABELS[item.type]}
          </Badge>
        </div>
        <div className="p-3.5 flex flex-col gap-1 flex-1">
          <h3 className="text-sm font-semibold text-ink line-clamp-2 leading-snug min-h-[2.5em]">{item.title}</h3>
          <p className="text-xs text-ink-faint truncate">{item.address_label}</p>
          <div className="mt-auto pt-2 text-sm font-semibold text-brand">{priceNote(item)}</div>
        </div>
      </Card>
    </Link>
  );
}
