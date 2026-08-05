import { Link, NavLink } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../lib/auth";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm tracking-wide transition-colors ${
    isActive ? "text-brand font-medium" : "text-ink-soft hover:text-ink"
  }`;

const mobileNavLinkClass = ({ isActive }: { isActive: boolean }) =>
  `block py-2.5 text-base tracking-wide transition-colors ${
    isActive ? "text-brand font-medium" : "text-ink-soft"
  }`;

export default function Navbar() {
  const { account, logout } = useAuth();
  // Below `md` the desktop nav (Trang chủ/Tìm kiếm/Đăng đồ/Đồ của tôi/Hồ sơ)
  // has nowhere to go — it used to just disappear entirely at 375px with no
  // replacement, silently cutting off Search/Post/MyItems/Profile on mobile.
  // This panel is the fix.
  const [menuOpen, setMenuOpen] = useState(false);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <header className="border-b border-line bg-surface/95 backdrop-blur sticky top-0 z-20">
      <div className="mx-auto max-w-6xl px-6 h-20 flex items-center justify-between">
        <Link to="/" className="font-display text-2xl tracking-wide text-ink" onClick={closeMenu}>
          Mượn <span className="text-brand">Ngay</span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          <NavLink to="/" end className={navLinkClass}>
            Trang chủ
          </NavLink>
          <NavLink to="/search" className={navLinkClass}>
            Tìm kiếm
          </NavLink>
          {account && (
            <>
              <NavLink to="/post" className={navLinkClass}>
                Đăng đồ
              </NavLink>
              <NavLink to="/my-items" className={navLinkClass}>
                Đồ của tôi
              </NavLink>
              <NavLink to="/profile" className={navLinkClass}>
                Hồ sơ
              </NavLink>
            </>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {account ? (
            <>
              <span className="hidden lg:inline text-sm text-ink-soft">
                Xin chào, {account.full_name || account.email}
              </span>
              <button
                onClick={() => logout()}
                className="hidden md:inline-block text-sm border border-line rounded-full px-4 py-2 hover:border-brand hover:text-brand transition-colors"
              >
                Đăng xuất
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hidden md:inline text-sm text-ink-soft hover:text-ink">
                Đăng nhập
              </Link>
              <Link
                to="/register"
                className="hidden md:inline-block text-sm bg-brand text-white rounded-full px-5 py-2 hover:bg-brand-dark transition-colors"
              >
                Đăng ký
              </Link>
            </>
          )}

          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center w-10 h-10 -mr-2 rounded-lg text-ink-soft hover:bg-brand-light hover:text-brand transition-colors"
            aria-label={menuOpen ? "Đóng menu" : "Mở menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            {menuOpen ? (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            ) : (
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {menuOpen && (
        <nav className="md:hidden border-t border-line px-6 py-3 bg-surface">
          <NavLink to="/" end className={mobileNavLinkClass} onClick={closeMenu}>
            Trang chủ
          </NavLink>
          <NavLink to="/search" className={mobileNavLinkClass} onClick={closeMenu}>
            Tìm kiếm
          </NavLink>
          {account && (
            <>
              <NavLink to="/post" className={mobileNavLinkClass} onClick={closeMenu}>
                Đăng đồ
              </NavLink>
              <NavLink to="/my-items" className={mobileNavLinkClass} onClick={closeMenu}>
                Đồ của tôi
              </NavLink>
              <NavLink to="/profile" className={mobileNavLinkClass} onClick={closeMenu}>
                Hồ sơ
              </NavLink>
            </>
          )}

          <div className="border-t border-line mt-2 pt-2">
            {account ? (
              <button
                onClick={() => {
                  logout();
                  closeMenu();
                }}
                className="block w-full text-left py-2.5 text-base text-ink-soft"
              >
                Đăng xuất
              </button>
            ) : (
              <>
                <Link to="/login" className="block py-2.5 text-base text-ink-soft" onClick={closeMenu}>
                  Đăng nhập
                </Link>
                <Link to="/register" className="block py-2.5 text-base text-brand font-medium" onClick={closeMenu}>
                  Đăng ký
                </Link>
              </>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
