import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import * as api from "../lib/api";
import { useAuth } from "../lib/auth";
import { CATEGORIES, NEXT_STATUSES, STATUS_LABELS, TYPE_LABELS } from "../lib/constants";
import { Badge, Button, ErrorText, Input, Select, Textarea } from "../components/ui";
import type { BadgeTone } from "../components/ui/Badge";

type WithFreshToken = ReturnType<typeof useAuth>["withFreshToken"];

const STATUS_TONE: Record<api.ItemStatus, BadgeTone> = {
  available: "success",
  reserved: "warning",
  given_out: "neutral",
};

export default function MyItems() {
  const { account, loading, withFreshToken } = useAuth();
  const [items, setItems] = useState<api.Item[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!account) return;
    withFreshToken((token) => api.listMyItems(token))
      .then(setItems)
      .catch(() => setItems([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account]);

  if (loading) {
    return <p className="text-center py-20 text-ink-soft">Đang tải…</p>;
  }
  if (!account) {
    return <Navigate to="/login" replace />;
  }

  function updateLocal(updated: api.Item) {
    setItems((prev) => prev?.map((it) => (it.id === updated.id ? updated : it)) ?? prev);
  }
  function removeLocal(id: string) {
    setItems((prev) => prev?.filter((it) => it.id !== id) ?? prev);
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-display text-ink">Đồ của tôi</h1>
        <Link to="/post">
          <Button size="sm">+ Đăng đồ mới</Button>
        </Link>
      </div>

      {error && <ErrorText className="mb-4">{error}</ErrorText>}
      {items === null && <MyItemsSkeleton />}
      {items?.length === 0 && (
        <div className="rounded-2xl border border-line bg-canvas py-16 text-center">
          <p className="text-ink-soft mb-2">Bạn chưa đăng đồ nào cả.</p>
          <p className="text-sm text-ink-faint mb-5">Đăng món đồ đầu tiên để bắt đầu cho mượn, cho thuê hoặc tặng đồ quanh bạn nhé!</p>
          <Link to="/post">
            <Button size="sm">+ Đăng đồ ngay</Button>
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {items?.map((item) => (
          <ItemRow
            key={item.id}
            item={item}
            withFreshToken={withFreshToken}
            onUpdate={updateLocal}
            onDelete={removeLocal}
            onError={setError}
          />
        ))}
      </div>
    </div>
  );
}

function MyItemsSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-line bg-surface p-4 flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex-1 min-w-0 space-y-2">
            <div className="h-5 w-16 bg-line rounded-full" />
            <div className="h-4 w-2/3 bg-line rounded" />
            <div className="h-3 w-1/3 bg-line rounded" />
          </div>
          <div className="h-8 w-24 bg-line rounded-lg" />
        </div>
      ))}
    </div>
  );
}

function ItemRow({
  item,
  withFreshToken,
  onUpdate,
  onDelete,
  onError,
}: {
  item: api.Item;
  withFreshToken: WithFreshToken;
  onUpdate: (item: api.Item) => void;
  onDelete: (id: string) => void;
  onError: (msg: string | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  async function changeStatus(next: api.ItemStatus) {
    setBusy(true);
    onError(null);
    try {
      const updated = await withFreshToken((token) => api.updateItemStatus(token, item.id, next));
      onUpdate(updated);
    } catch {
      onError("Không đổi được trạng thái, thử lại sau.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setBusy(true);
    onError(null);
    try {
      await withFreshToken((token) => api.deleteItem(token, item.id));
      onDelete(item.id);
    } catch {
      onError("Không xoá được, thử lại sau.");
      setBusy(false);
    }
  }

  if (editing) {
    return (
      <EditForm
        item={item}
        withFreshToken={withFreshToken}
        onSaved={(updated) => {
          onUpdate(updated);
          setEditing(false);
        }}
        onCancel={() => setEditing(false)}
        onError={onError}
      />
    );
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-4 flex flex-col sm:flex-row sm:items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Badge tone={STATUS_TONE[item.status]}>{STATUS_LABELS[item.status]}</Badge>
          <Badge tone="neutral">{TYPE_LABELS[item.type]}</Badge>
        </div>
        <Link to={`/items/${item.id}`} className="font-semibold text-ink hover:text-brand">
          {item.title}
        </Link>
        <p className="text-xs text-ink-faint truncate">{item.address_label}</p>
      </div>

      <div className="flex flex-col items-start sm:items-end gap-2">
        <div className="flex flex-wrap gap-2">
          {NEXT_STATUSES[item.status].map((next) => (
            <Button key={next} size="sm" variant="secondary" disabled={busy} onClick={() => changeStatus(next)}>
              → {STATUS_LABELS[next]}
            </Button>
          ))}
        </div>
        {confirmingDelete ? (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-ink-soft">Xoá "{item.title}"?</span>
            <Button size="sm" variant="danger" disabled={busy} onClick={handleDelete}>
              Xác nhận
            </Button>
            <Button size="sm" variant="ghost" disabled={busy} onClick={() => setConfirmingDelete(false)}>
              Huỷ
            </Button>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" disabled={busy} onClick={() => setEditing(true)}>
              Sửa
            </Button>
            <Button size="sm" variant="danger" disabled={busy} onClick={() => setConfirmingDelete(true)}>
              Xoá
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function EditForm({
  item,
  withFreshToken,
  onSaved,
  onCancel,
  onError,
}: {
  item: api.Item;
  withFreshToken: WithFreshToken;
  onSaved: (item: api.Item) => void;
  onCancel: () => void;
  onError: (msg: string | null) => void;
}) {
  const [title, setTitle] = useState(item.title);
  const [description, setDescription] = useState(item.description ?? "");
  const [category, setCategory] = useState(item.category);
  const [rentalPriceNote, setRentalPriceNote] = useState(item.rental_price_note ?? "");
  const [addressLabel, setAddressLabel] = useState(item.address_label);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const updated = await withFreshToken((token) =>
        api.updateItem(token, item.id, {
          title: title.trim(),
          description: description.trim(),
          category,
          rental_price_note: item.type === "rent_paid" ? rentalPriceNote.trim() : undefined,
          address_label: addressLabel.trim(),
        }),
      );
      onSaved(updated);
    } catch {
      onError("Không lưu được, thử lại sau.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface p-4 space-y-3">
      <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Tiêu đề" />
      <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Mô tả" />
      <Select value={category} onChange={(e) => setCategory(e.target.value)}>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </Select>
      {item.type === "rent_paid" && (
        <Input value={rentalPriceNote} onChange={(e) => setRentalPriceNote(e.target.value)} placeholder="Giá thuê" />
      )}
      <Input value={addressLabel} onChange={(e) => setAddressLabel(e.target.value)} placeholder="Địa chỉ" />
      <div className="flex gap-2">
        <Button size="sm" disabled={saving} onClick={handleSave}>
          Lưu
        </Button>
        <Button size="sm" variant="secondary" disabled={saving} onClick={onCancel}>
          Huỷ
        </Button>
      </div>
    </div>
  );
}
