import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import * as api from "../lib/api";
import { useAuth } from "../lib/auth";
import { Button, Card, ErrorText } from "../components/ui";

export default function Profile() {
  const { account, loading } = useAuth();
  const [ratings, setRatings] = useState<api.UserRatingsResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!account) return;
    let cancelled = false;
    api
      .getUserRatings(account.id)
      .then((r) => {
        if (!cancelled) setRatings(r);
      })
      .catch(() => {
        if (!cancelled) setError("Không tải được đánh giá của bạn, thử lại sau.");
      });
    return () => {
      cancelled = true;
    };
  }, [account]);

  if (loading) {
    return <p className="text-center py-20 text-ink-soft">Đang tải…</p>;
  }
  if (!account) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <h1 className="text-2xl font-display text-ink">Hồ sơ của tôi</h1>
          <p className="text-ink-soft text-sm mt-1">{account.full_name || account.email}</p>
        </div>
        <Link to="/my-items">
          <Button variant="secondary" size="sm">
            Đồ của tôi
          </Button>
        </Link>
      </div>

      <Card padding="md" className="mb-6">
        <h2 className="font-semibold text-ink mb-3">Thông tin tài khoản</h2>
        <dl className="text-sm space-y-1.5">
          <div className="flex gap-2">
            <dt className="text-ink-faint w-28 shrink-0">Email</dt>
            <dd className="text-ink-soft break-all">{account.email}</dd>
          </div>
          {account.phone && (
            <div className="flex gap-2">
              <dt className="text-ink-faint w-28 shrink-0">Số điện thoại</dt>
              <dd className="text-ink-soft">{account.phone}</dd>
            </div>
          )}
        </dl>
      </Card>

      <Card padding="md">
        <h2 className="font-semibold text-ink mb-4">Đánh giá từ cộng đồng</h2>

        {error && <ErrorText className="mb-4">{error}</ErrorText>}

        {!ratings && !error ? (
          <RatingsSkeleton />
        ) : ratings && ratings.count > 0 ? (
          <>
            <p className="mb-5">
              <span className="text-xl font-semibold text-star">★ {ratings.avg_score.toFixed(1)}</span>{" "}
              <span className="text-sm text-ink-soft">({ratings.count} đánh giá)</span>
            </p>
            <ul className="space-y-4">
              {ratings.ratings.map((r) => (
                <li key={r.id} className="border-t border-line pt-4 first:border-t-0 first:pt-0">
                  <p className="text-star text-sm mb-1">
                    {"★".repeat(r.score)}
                    <span className="text-ink-faint">{"★".repeat(5 - r.score)}</span>
                  </p>
                  {r.comment ? (
                    <p className="text-sm text-ink-soft">{r.comment}</p>
                  ) : (
                    <p className="text-sm text-ink-faint italic">Không có nhận xét kèm theo.</p>
                  )}
                  <p className="text-xs text-ink-faint mt-1">{new Date(r.created_at).toLocaleDateString("vi-VN")}</p>
                </li>
              ))}
            </ul>
          </>
        ) : (
          !error && (
            <div className="py-8 text-center">
              <p className="text-ink-soft mb-2">Bạn chưa nhận được đánh giá nào cả.</p>
              <p className="text-sm text-ink-faint mb-5">
                Cho mượn, cho thuê hoặc tặng một món đồ để bắt đầu xây dựng uy tín của bạn với cộng đồng nhé!
              </p>
              <Link to="/post">
                <Button size="sm">Đăng đồ đầu tiên</Button>
              </Link>
            </div>
          )
        )}
      </Card>
    </div>
  );
}

function RatingsSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-6 w-32 bg-line rounded" />
      <div className="h-4 w-full bg-line rounded" />
      <div className="h-4 w-2/3 bg-line rounded" />
    </div>
  );
}
