/** Bộ UI dùng chung: tiện ích, biểu tượng inline (một họ nét), toast, modal. */
import { createContext, useCallback, useContext, useEffect, useState } from "react";

export const cx = (...xs: (string | false | null | undefined)[]) => xs.filter(Boolean).join(" ");
export const nf = new Intl.NumberFormat("vi-VN");
export const fso = (n: number | undefined | null) => nf.format(Math.round(Number(n ?? 0)));

/* --------------------------------- icon ---------------------------------- */
export const IC = {
  x: <><circle cx="12" cy="12" r="9" /><path d="m15 9-6 6M9 9l6 6" /></>,
  warn: <path d="M10.3 4.3 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z M12 9.5v4.2 M12 17.2h.01" />,
  check: <><circle cx="12" cy="12" r="9" /><path d="m8.4 12.3 2.5 2.5 4.7-5.1" /></>,
  checkNho: <path d="m5 13 4 4L19 7" />,
  lock: <><path d="M7 11V8a5 5 0 0 1 10 0v3" /><rect x="5" y="11" width="14" height="9" rx="2" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  gear: <><circle cx="12" cy="12" r="3.2" /><path d="M19.4 12a7.4 7.4 0 0 0-.1-1.3l2-1.6-2-3.4-2.4 1a7.3 7.3 0 0 0-2.2-1.3L14.3 2h-4l-.4 2.4A7.3 7.3 0 0 0 7.7 5.7l-2.4-1-2 3.4 2 1.6a7.4 7.4 0 0 0 0 2.6l-2 1.6 2 3.4 2.4-1a7.3 7.3 0 0 0 2.2 1.3l.4 2.4h4l.4-2.4a7.3 7.3 0 0 0 2.2-1.3l2.4 1 2-3.4-2-1.6a7.4 7.4 0 0 0 .1-1.3Z" /></>,
  chevR: <path d="m9 6 6 6-6 6" />,
  chevL: <path d="m15 6-6 6 6 6" />,
  chevDown: <path d="m6 9 6 6 6-6" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.9-3.9" /></>,
  taiXuong: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" /></>,
  lam_moi: <><path d="M21 12a9 9 0 0 1-15.4 6.4L3 16" /><path d="M3 12a9 9 0 0 1 15.4-6.4L21 8" /><path d="M21 3v5h-5" /><path d="M3 21v-5h5" /></>,
  file: <><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v5h5" /></>,
  thu_muc: <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9L9.6 3.9A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />,
  tai_len: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m17 8-5-5-5 5" /><path d="M12 3v12" /></>,
  bar: <><path d="M3 3v18h18" /><path d="M8 17v-6.5M13 17V6.5M18 17v-3.5" /></>,
  chep: <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" /></>,
};

export function Icon({ d, className = "h-4 w-4" }: { d: React.ReactNode; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      {d}
    </svg>
  );
}

/* --------------------------------- nút ------------------------------------ */
type NutProps = React.ButtonHTMLAttributes<HTMLButtonElement> & { bien?: "chinh" | "phu" | "header" };
export function Nut({ bien = "phu", className, children, ...rest }: NutProps) {
  const base = "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-[13px] font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed";
  const bienCls = {
    chinh: "bg-gradient-to-br from-navy-dark to-navy text-white shadow-soft hover:from-navy hover:to-navy-400",
    phu: "border border-steel-200 bg-white text-navy shadow-soft hover:border-steel-300",
    header: "border border-white/25 bg-white/10 text-white hover:bg-white/20",
  }[bien];
  return <button className={cx(base, bienCls, className)} {...rest}>{children}</button>;
}

/* -------------------------------- toast ----------------------------------- */
type ToastFn = (msg: string) => void;
const ToastCtx = createContext<ToastFn>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const toast = useCallback((m: string) => setMsg(m), []);
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 3200);
    return () => clearTimeout(t);
  }, [msg]);
  return (
    <ToastCtx.Provider value={toast}>
      {children}
      {msg && (
        <div className="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 rounded-xl bg-ink px-4 py-2.5 text-[13px] font-medium text-white shadow-pop">
          {msg}
        </div>
      )}
    </ToastCtx.Provider>
  );
}

/* -------------------------------- modal ----------------------------------- */
export function Modal({ mo, dong, tieuDe, children, rong }: {
  mo: boolean; dong: () => void; tieuDe: string; children: React.ReactNode; rong?: boolean;
}) {
  useEffect(() => {
    if (!mo) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && dong();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [mo, dong]);
  if (!mo) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/45 p-6" onMouseDown={dong}>
      <div
        className={cx("w-full rounded-2xl bg-white p-5 shadow-pop", rong ? "max-w-[70vw]" : "max-w-[440px]")}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 className="mb-1 text-[16px] font-extrabold text-ink">{tieuDe}</h3>
        {children}
      </div>
    </div>
  );
}

/* ----------------------------- nhãn trạng thái ---------------------------- */
export const MAU_KL: Record<string, MucKL> = {
  chua_san_sang: "do", can_ra_soat: "vang", san_sang: "xanh",
};
export type MucKL = "do" | "vang" | "xanh";
export const khoaKL = (m?: string): "chua_san_sang" | "can_ra_soat" | "san_sang" =>
  m === "san_sang" || m === "SAN_SANG" ? "san_sang"
  : m === "can_ra_soat" || m === "CAN_RA_SOAT" ? "can_ra_soat"
  : "chua_san_sang";
