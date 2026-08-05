import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { ApiError } from "../lib/api";
import { Button, ErrorText, Input, Label } from "../components/ui";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(identifier, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Đăng nhập thất bại, vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-3xl text-ink text-center mb-8">Đăng nhập</h1>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label>Email hoặc số điện thoại</Label>
          <Input size="lg" type="text" required value={identifier} onChange={(e) => setIdentifier(e.target.value)} />
        </div>
        <div>
          <Label>Mật khẩu</Label>
          <Input size="lg" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>

        {error && <ErrorText>{error}</ErrorText>}

        <Button type="submit" size="lg" disabled={submitting} className="w-full">
          {submitting ? "Đang đăng nhập…" : "Đăng nhập"}
        </Button>
      </form>

      <p className="text-center text-sm text-ink-soft mt-6">
        Chưa có tài khoản?{" "}
        <Link to="/register" className="text-brand hover:underline">
          Đăng ký ngay
        </Link>
      </p>
    </div>
  );
}
