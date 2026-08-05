import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";
import { Button, ErrorText, Input, Label } from "../components/ui";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({ email, password, full_name: fullName, phone: phone || undefined });
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Đăng ký thất bại, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-3xl text-ink text-center mb-8">Tạo tài khoản</h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label>Họ và tên</Label>
          <Input size="lg" type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div>
          <Label>Email</Label>
          <Input size="lg" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <Label>Số điện thoại (không bắt buộc)</Label>
          <Input
            size="lg"
            type="tel"
            placeholder="+84901234567"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </div>
        <div>
          <Label>Mật khẩu (tối thiểu 8 ký tự)</Label>
          <Input
            size="lg"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && <ErrorText>{error}</ErrorText>}

        <Button type="submit" size="lg" disabled={submitting} className="w-full">
          {submitting ? "Đang tạo tài khoản…" : "Đăng ký"}
        </Button>
      </form>

      <p className="text-center text-sm text-ink-soft mt-6">
        Đã có tài khoản?{" "}
        <Link to="/login" className="text-brand hover:underline">
          Đăng nhập
        </Link>
      </p>
    </div>
  );
}
