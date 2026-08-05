import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "../lib/api";
import { useAuth } from "../lib/auth";
import { NEXT_STATUSES, STATUS_LABELS, TYPE_LABELS } from "../lib/constants";
import { Badge, Button, ErrorText, Select, Textarea } from "../components/ui";
import type { BadgeTone } from "../components/ui/Badge";

type WithFreshToken = ReturnType<typeof useAuth>["withFreshToken"];

const STATUS_TONE: Record<api.ItemStatus, BadgeTone> = {
  available: "success",
  reserved: "warning",
  given_out: "neutral",
};

function priceNote(item: api.Item): string {
  if (item.type === "rent_paid") return item.rental_price_note || "Thuê trả phí";
  if (item.type === "donate") return "Tặng";
  return "Miễn phí";
}

export default function ItemDetail() {
  const { id } = useParams<{ id: string }>();
  const { account, withFreshToken } = useAuth();
  const [item, setItem] = useState<api.Item | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  // Fetched once here (not inside OwnerRatingSummary/RatingSection) so the
  // non-owner rating gate below can reuse it for a backend-truth "did I
  // already rate the owner for this item" check instead of only session
  // state — see RatingSection's comment for why the owner-side check can't
  // get the same treatment as cheaply.
  const [ownerRatings, setOwnerRatings] = useState<api.UserRatingsResult | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    api
      .getItem(id)
      .then((data) => {
        if (!cancelled) {
          setItem(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNotFound(true);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!item) return;
    let cancelled = false;
    api
      .getUserRatings(item.owner_user_id)
      .then((r) => {
        if (!cancelled) setOwnerRatings(r);
      })
      .catch(() => {
        if (!cancelled) setOwnerRatings(null);
      });
    return () => {
      cancelled = true;
    };
  }, [item?.owner_user_id]);

  if (loading) {
    return <ItemDetailSkeleton />;
  }
  if (notFound || !item) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-20 text-center">
        <p className="text-ink-soft mb-2">Không tìm thấy đồ này — có thể đã bị xoá hoặc cho đi rồi.</p>
        <p className="text-sm text-ink-faint mb-5">Thử quay lại tìm những món đồ khác quanh bạn.</p>
        <Link to="/search">
          <Button size="sm">Tìm đồ khác</Button>
        </Link>
      </div>
    );
  }

  const isOwner = account?.id === item.owner_user_id;
  const alreadyRatedOwner =
    !!account && !!ownerRatings && ownerRatings.ratings.some((r) => r.item_id === item.id && r.rater_user_id === account.id);

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <ItemHeader item={item} />
      <OwnerRatingSummary ratings={ownerRatings} />

      <div className="mt-6 space-y-6">
        {!account && <NotLoggedInCta />}

        {account && !isOwner && (
          <>
            <InterestSection item={item} withFreshToken={withFreshToken} />
            {item.status === "given_out" && (
              <RatingSection item={item} isOwner={false} interests={null} alreadyRated={alreadyRatedOwner} withFreshToken={withFreshToken} />
            )}
          </>
        )}

        {account && isOwner && <OwnerSection item={item} onUpdate={setItem} withFreshToken={withFreshToken} />}
      </div>
    </div>
  );
}

function ItemDetailSkeleton() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 animate-pulse">
      <div className="rounded-2xl bg-line aspect-video mb-4" />
      <div className="flex gap-2 mb-3">
        <div className="h-6 w-20 bg-line rounded-full" />
        <div className="h-6 w-24 bg-line rounded-full" />
        <div className="h-6 w-16 bg-line rounded-full" />
      </div>
      <div className="h-7 w-2/3 bg-line rounded mb-3" />
      <div className="h-5 w-1/3 bg-line rounded mb-4" />
      <div className="h-4 w-1/2 bg-line rounded" />
    </div>
  );
}

function ItemHeader({ item }: { item: api.Item }) {
  return (
    <div>
      <div className="rounded-2xl overflow-hidden bg-canvas mb-4">
        {item.photo_keys?.[0] ? (
          <img src={item.photo_keys[0]} alt={item.title} className="w-full aspect-[16/9] object-cover" />
        ) : (
          <div className="w-full aspect-[16/9] flex items-center justify-center bg-gradient-to-br from-brand-light to-accent-light">
            <span className="text-6xl font-display font-extrabold text-brand/40">{item.title.charAt(0).toUpperCase()}</span>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 mb-2">
        <Badge tone={STATUS_TONE[item.status]}>{STATUS_LABELS[item.status]}</Badge>
        <Badge tone="brand">{TYPE_LABELS[item.type]}</Badge>
        <Badge tone="neutral">{item.category}</Badge>
      </div>
      <h1 className="text-2xl font-display text-ink mb-2">{item.title}</h1>
      <p className="text-lg font-semibold text-brand mb-3">{priceNote(item)}</p>
      {item.description && <p className="text-ink-soft mb-3 whitespace-pre-wrap">{item.description}</p>}
      <p className="text-sm text-ink-faint">{item.address_label}</p>
    </div>
  );
}

function OwnerRatingSummary({ ratings }: { ratings: api.UserRatingsResult | null }) {
  return (
    <p className="text-sm text-ink-soft mt-1">
      Chủ đồ:{" "}
      {ratings && ratings.count > 0 ? `★ ${ratings.avg_score.toFixed(1)} (${ratings.count} đánh giá)` : "chưa có đánh giá"}
    </p>
  );
}

function NotLoggedInCta() {
  return (
    <div className="rounded-2xl border border-line bg-canvas p-5 text-center">
      <p className="text-ink-soft mb-3">Đăng nhập để xem thông tin liên hệ và quan tâm đến đồ này.</p>
      <Link to="/login">
        <Button>Đăng nhập để xem liên hệ</Button>
      </Link>
    </div>
  );
}

function InterestSection({ item, withFreshToken }: { item: api.Item; withFreshToken: WithFreshToken }) {
  const [contact, setContact] = useState<api.ContactInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (item.status === "given_out") {
    return <StatusNotice text="Đã có người nhận." />;
  }
  if (item.status === "reserved") {
    return <StatusNotice text="Đang được giữ chỗ." />;
  }

  async function handleInterest() {
    setLoading(true);
    setError(null);
    try {
      const result = await withFreshToken((token) => api.expressInterest(token, item.id));
      setContact(result.contact);
    } catch {
      setError("Không gửi được yêu cầu quan tâm, thử lại sau.");
    } finally {
      setLoading(false);
    }
  }

  if (contact) {
    return (
      <div className="rounded-2xl border border-success/30 bg-success-light p-5">
        <p className="font-semibold text-success mb-2">Đã gửi yêu cầu quan tâm! Liên hệ với chủ đồ:</p>
        <p className="text-ink">{contact.full_name}</p>
        <p className="text-ink-soft text-sm">{contact.email}</p>
        <p className="text-ink-soft text-sm">{contact.phone}</p>
      </div>
    );
  }

  return (
    <div>
      <Button size="lg" onClick={handleInterest} disabled={loading}>
        {loading ? "Đang gửi…" : "Quan tâm — Xem liên hệ"}
      </Button>
      {error && <ErrorText className="mt-2">{error}</ErrorText>}
    </div>
  );
}

function StatusNotice({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-line bg-canvas p-4 text-center text-ink-soft">
      <Button disabled className="mb-2">
        Quan tâm — Xem liên hệ
      </Button>
      <p className="text-sm">{text}</p>
    </div>
  );
}

function OwnerSection({
  item,
  onUpdate,
  withFreshToken,
}: {
  item: api.Item;
  onUpdate: (item: api.Item) => void;
  withFreshToken: WithFreshToken;
}) {
  const [interests, setInterests] = useState<api.Interest[] | null>(null);
  const [changing, setChanging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    withFreshToken((token) => api.listInterests(token, item.id))
      .then((data) => {
        if (!cancelled) setInterests(data);
      })
      .catch(() => {
        if (!cancelled) setInterests([]);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.id]);

  async function changeStatus(next: api.ItemStatus) {
    setChanging(true);
    setError(null);
    try {
      const updated = await withFreshToken((token) => api.updateItemStatus(token, item.id, next));
      onUpdate(updated);
    } catch {
      setError("Không đổi được trạng thái, thử lại sau.");
    } finally {
      setChanging(false);
    }
  }

  const nextStatuses = NEXT_STATUSES[item.status];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-line bg-surface p-5">
        <h2 className="font-semibold text-ink mb-3">Quản lý đồ của bạn</h2>
        {nextStatuses.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {nextStatuses.map((next) => (
              <Button key={next} size="sm" variant="secondary" disabled={changing} onClick={() => changeStatus(next)}>
                Chuyển sang "{STATUS_LABELS[next]}"
              </Button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-ink-soft">Đồ này đã cho đi — không thể đổi trạng thái nữa.</p>
        )}
        {error && <ErrorText className="mt-2">{error}</ErrorText>}

        <h3 className="text-sm font-semibold text-ink mt-5 mb-2">Người quan tâm ({interests?.length ?? 0})</h3>
        {interests === null && <p className="text-sm text-ink-faint">Đang tải…</p>}
        {interests?.length === 0 && <p className="text-sm text-ink-faint">Chưa có ai quan tâm.</p>}
        {interests && interests.length > 0 && (
          <ul className="space-y-1">
            {interests.map((i) => (
              <li key={i.id} className="text-sm text-ink-soft">
                Tài khoản {i.interested_user_id.slice(0, 8)}… — quan tâm lúc{" "}
                {new Date(i.created_at).toLocaleString("vi-VN")}
              </li>
            ))}
          </ul>
        )}
      </div>

      {item.status === "given_out" && (
        <RatingSection item={item} isOwner interests={interests ?? []} withFreshToken={withFreshToken} />
      )}
    </div>
  );
}

function StarPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          className={`text-2xl leading-none transition-colors ${n <= value ? "text-star" : "text-ink-faint hover:text-star/60"}`}
          aria-label={`${n} sao`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

// Rating prompt (FR-18/19/20) — only shown once item is given_out. For the
// owner, target is picked from the real interests list (any of them is a
// legitimate rating target per FR-18); "already rated" for the owner side is
// tracked per-session only (no cheap backend check for "did I rate THIS
// specific interested_user_id" without an extra call per person) — a genuine
// repeat after a reload is still caught server-side (FR-18a ALREADY_RATED)
// and shown as an inline error, not silently ignored.
//
// For a non-owner, the only legitimate target is the owner. There is NO
// client-side way to know for certain whether this account actually has an
// `interests` row on this item — GET /items/:id/interests (FR-17) is
// owner-only, so we can't read that back. Earlier this section gated
// visibility behind a localStorage marker set at expressInterest time, but
// that's a real bug: the marker is lost on a different device/session or if
// storage is cleared, and once given_out, InterestSection no longer offers a
// way to re-set it (the "Quan tâm" button is replaced by a status message) —
// a legitimate interested party could permanently lose the ability to rate
// through the UI, silently, with zero indication why. The server already
// knows the real answer (checkValidRatingTarget in SubmitRating), so the fix
// is to always show the form to a logged-in non-owner and let the backend be
// the source of truth: a genuinely ineligible account gets a friendly
// message from the INVALID_RATING_TARGET rejection instead of a missing
// button. "already rated" for the non-owner path IS backend-truth (the
// alreadyRated prop, derived from getUserRatings in the parent) since that
// data was already being fetched for the rating summary anyway.
function RatingSection({
  item,
  isOwner,
  interests,
  alreadyRated = false,
  withFreshToken,
}: {
  item: api.Item;
  isOwner: boolean;
  interests: api.Interest[] | null;
  alreadyRated?: boolean;
  withFreshToken: WithFreshToken;
}) {
  const [ratedIds, setRatedIds] = useState<string[]>([]);
  const [target, setTarget] = useState("");
  const [score, setScore] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const candidates = isOwner
    ? (interests ?? []).map((i) => i.interested_user_id).filter((id) => !ratedIds.includes(id))
    : !alreadyRated && !ratedIds.includes(item.owner_user_id)
      ? [item.owner_user_id]
      : [];

  if (isOwner && (interests?.length ?? 0) === 0) {
    return null;
  }
  if (candidates.length === 0) {
    return (
      <div className="rounded-2xl border border-line bg-canvas p-5 text-center text-sm text-ink-soft">
        {done ? "Cảm ơn bạn đã đánh giá!" : "Bạn đã đánh giá xong."}
      </div>
    );
  }

  const effectiveTarget = isOwner ? target || candidates[0] : candidates[0];

  async function submit() {
    if (!effectiveTarget || score < 1) {
      setError("Vui lòng chọn số sao đánh giá.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await withFreshToken((token) =>
        api.submitRating(token, item.id, { rated_user_id: effectiveTarget, score, comment: comment.trim() || undefined }),
      );
      setRatedIds((prev) => [...prev, effectiveTarget]);
      setScore(0);
      setComment("");
      setTarget("");
      setDone(true);
    } catch (err) {
      let message = "Không gửi được đánh giá, thử lại sau.";
      if (err instanceof api.ApiError) {
        if (err.code === "ALREADY_RATED") message = "Bạn đã đánh giá người này rồi.";
        else if (err.code === "INVALID_RATING_TARGET") message = "Chỉ người đã quan tâm món đồ này mới có thể đánh giá.";
      }
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <h2 className="font-semibold text-ink mb-3">Đánh giá {isOwner ? "người quan tâm" : "chủ đồ"}</h2>

      {isOwner && candidates.length > 1 && (
        <Select className="mb-3" size="sm" value={effectiveTarget} onChange={(e) => setTarget(e.target.value)}>
          {candidates.map((id) => (
            <option key={id} value={id}>
              Tài khoản {id.slice(0, 8)}…
            </option>
          ))}
        </Select>
      )}

      <StarPicker value={score} onChange={setScore} />
      <Textarea
        className="mt-3"
        placeholder="Nhận xét (tuỳ chọn)"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      {error && <ErrorText className="mt-2">{error}</ErrorText>}
      <Button className="mt-3" size="sm" disabled={submitting} onClick={submit}>
        {submitting ? "Đang gửi…" : "Gửi đánh giá"}
      </Button>
    </div>
  );
}
