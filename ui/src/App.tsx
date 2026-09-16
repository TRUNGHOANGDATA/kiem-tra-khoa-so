/**
 * Màn KẾT QUẢ (bản dựng look đầu tiên) — React + Tailwind, bản sắc "Thép & Sổ cái".
 * Hiện dùng dữ liệu mẫu để xem giao diện; chặng sau nối vào pywebview.api thật.
 */
import { useState } from "react";

/* ----------------------------- dữ liệu mẫu ------------------------------ */
type ChiNhanh = { ma: string; do: number; vang: number; dat: number; chot: "chua" | "khop" | "lech" };
const TONG = 40;
const CHI_NHANH: ChiNhanh[] = [
  { ma: "A01", do: 3, vang: 10, dat: 27, chot: "chua" },
  { ma: "A02", do: 5, vang: 9, dat: 26, chot: "chua" },
  { ma: "A06", do: 1, vang: 6, dat: 20, chot: "chua" },
  { ma: "A04", do: 1, vang: 3, dat: 23, chot: "chua" },
  { ma: "A08", do: 1, vang: 4, dat: 22, chot: "khop" },
  { ma: "A05", do: 0, vang: 1, dat: 24, chot: "chua" },
  { ma: "A07", do: 0, vang: 3, dat: 23, chot: "chua" },
  { ma: "A03", do: 0, vang: 0, dat: 40, chot: "khop" },
];
type Buoc = { i: number; ten: string; mo: string; trangThai: "da" | "ra" | "chua" | "tu" };
const BUOC: Buoc[] = [
  { i: 11, ten: "Kết chuyển chi phí 635/641/642/811 → 911", mo: "Đã kết chuyển: 641, 642, 811", trangThai: "da" },
  { i: 12, ten: "Đánh giá chênh lệch tỷ giá cuối kỳ (413)", mo: "Không có số dư gốc ngoại tệ cần đánh giá", trangThai: "tu" },
  { i: 13, ten: "Kết chuyển chi phí thuế TNDN 8211 → 911", mo: "Đã có 8211, hoặc kỳ không phát sinh lãi", trangThai: "da" },
  { i: 14, ten: "Khấu trừ thuế GTGT 3331 ↔ 1331", mo: "Thuế vào 41.338.913 / thuế ra 741.884.731 — đã khấu trừ", trangThai: "da" },
  { i: 15, ten: "Kết chuyển lãi/lỗ 911 ↔ 421", mo: "Đã có bút toán 911 ↔ 421", trangThai: "da" },
  { i: 16, ten: "TK đầu 5/6/7/8 đã về 0 (kết chuyển hết)", mo: "Còn 2 tài khoản có nợ ≠ 0", trangThai: "ra" },
];

/* ------------------------------- tiện ích -------------------------------- */
const nf = new Intl.NumberFormat("vi-VN");
const mucCua = (c: ChiNhanh) => (c.do > 0 ? "do" : c.vang > 0 ? "vang" : "xanh");

/* ------------------------------ biểu tượng ------------------------------- */
const I = {
  x: <path d="M15 9l-6 6M9 9l6 6" />,
  warn: <path d="M10.3 4.3 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z M12 9.5v4.2 M12 17.2h.01" />,
  check: <path d="m8.4 12.3 2.5 2.5 4.7-5.1" />,
  lock: <path d="M7 11V8a5 5 0 0 1 10 0v3 M5 11h14v9H5z" />,
  clock: <path d="M12 7v5l3 2" />,
  gear: <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" />,
  chevR: <path d="m9 6 6 6-6 6" />,
  search: <path d="M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14ZM20 20l-3.9-3.9" />,
};
function Svg({ d, cls = "h-4 w-4" }: { d: React.ReactNode; cls?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75}
      strokeLinecap="round" strokeLinejoin="round" className={cls} aria-hidden>
      {d}
    </svg>
  );
}

/* ------------------------------- thành phần ------------------------------ */
function StatPill({ mau, nhan, so }: { mau: "do" | "vang" | "xanh"; nhan: string; so: number }) {
  const c = {
    do: "border-do-vien bg-do-nen text-do-dam",
    vang: "border-vang-vien bg-vang-nen text-vang-dam",
    xanh: "border-xanh-vien bg-xanh-nen text-xanh-dam",
  }[mau];
  const ic = { do: I.x, vang: I.warn, xanh: I.check }[mau];
  return (
    <div className={`flex items-center gap-2.5 rounded-xl border px-3.5 py-2 ${c}`}>
      <Svg d={ic} cls="h-4 w-4" />
      <div className="leading-none">
        <div className="text-[11px] font-semibold opacity-80">{nhan}</div>
        <div className="mt-1 text-xl font-extrabold tnum">{nf.format(so)}</div>
      </div>
    </div>
  );
}

function ChotChip({ chot }: { chot: ChiNhanh["chot"] }) {
  if (chot === "khop")
    return <span className="inline-flex items-center gap-1 rounded-full bg-xanh-nen px-2 py-0.5 text-[11px] font-semibold text-xanh-dam"><Svg d={I.lock} cls="h-3 w-3" />Đã chốt</span>;
  if (chot === "lech")
    return <span className="inline-flex items-center gap-1 rounded-full bg-vang-nen px-2 py-0.5 text-[11px] font-semibold text-vang-dam"><Svg d={I.warn} cls="h-3 w-3" />Dữ liệu đổi</span>;
  return <span className="rounded-full bg-steel-100 px-2 py-0.5 text-[11px] font-semibold text-steel-500">Chưa chốt</span>;
}

function DongSo({ mau, nhan, so }: { mau: "do" | "vang" | "xanh"; nhan: string; so: number }) {
  const t = { do: "text-do-dam", vang: "text-vang-dam", xanh: "text-xanh-dam" }[mau];
  const dot = { do: "bg-do", vang: "bg-vang", xanh: "bg-xanh" }[mau];
  return (
    <div className="flex items-center gap-2 rounded-md bg-steel-50 px-2 py-1">
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      <span className={`flex-1 text-[11.5px] font-semibold ${t}`}>{nhan}</span>
      <span className={`text-[13px] font-extrabold tnum ${t}`}>{nf.format(so)}</span>
    </div>
  );
}

function TheChiNhanh({ c, chon, onClick }: { c: ChiNhanh; chon: boolean; onClick: () => void }) {
  const dot = { do: "bg-do", vang: "bg-vang", xanh: "bg-xanh" }[mucCua(c)];
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-xl border bg-white p-2.5 text-left shadow-soft transition
        ${chon ? "border-navy ring-1 ring-navy/30 [box-shadow:inset_3px_0_0_theme(colors.navy.DEFAULT)]" : "border-steel-200 hover:border-steel-300 hover:shadow-card"}`}
    >
      <div className="mb-2 flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${dot} ring-2 ring-steel-100`} />
        <span className="text-[14px] font-bold text-ink">{c.ma}</span>
        <span className="ml-auto"><ChotChip chot={c.chot} /></span>
      </div>
      <div className="space-y-1">
        <DongSo mau="do" nhan="Nghiêm trọng" so={c.do} />
        <DongSo mau="vang" nhan="Cảnh báo" so={c.vang} />
        <DongSo mau="xanh" nhan="Đạt" so={c.dat} />
      </div>
    </button>
  );
}

function DongBuoc({ b }: { b: Buoc }) {
  const cfg = {
    da: { pill: "bg-xanh-nen text-xanh-dam", nhan: "Đã làm", ic: I.check, ring: "border-xanh-vien text-xanh" },
    ra: { pill: "bg-vang-nen text-vang-dam", nhan: "Cần rà", ic: I.warn, ring: "border-vang-vien text-vang" },
    chua: { pill: "bg-do-nen text-do-dam", nhan: "Chưa làm", ic: I.x, ring: "border-do-vien text-do" },
    tu: { pill: "bg-steel-100 text-steel-500", nhan: "Tự xác nhận", ic: I.check, ring: "border-steel-200 text-steel-400" },
  }[b.trangThai];
  return (
    <button className="flex w-full items-center gap-4 px-5 py-3.5 text-left transition hover:bg-steel-50">
      <span className="w-6 shrink-0 text-right text-[13px] font-semibold tnum text-steel-400">{b.i}</span>
      <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border ${cfg.ring}`}>
        <Svg d={cfg.ic} cls="h-4 w-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[14px] font-semibold text-ink">{b.ten}</span>
        <span className="block truncate text-[12.5px] text-steel-500">{b.mo}</span>
      </span>
      <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold ${cfg.pill}`}>
        <Svg d={cfg.ic} cls="h-3.5 w-3.5" />{cfg.nhan}
      </span>
      <Svg d={I.chevR} cls="h-4 w-4 shrink-0 text-steel-300" />
    </button>
  );
}

function NutHeader({ children, icon }: { children: React.ReactNode; icon: React.ReactNode }) {
  return (
    <button className="inline-flex items-center gap-2 rounded-xl border border-white/25 bg-white/10 px-3.5 py-2 text-[13px] font-semibold text-white transition hover:bg-white/20">
      <Svg d={icon} cls="h-4 w-4" />{children}
    </button>
  );
}

/* --------------------------------- App ---------------------------------- */
export default function App() {
  const [xem, setXem] = useState(0);
  const [tab, setTab] = useState<"trangthai" | "loi">("trangthai");
  const dsSap = [...CHI_NHANH].sort(
    (a, b) => ({ do: 0, vang: 1, xanh: 2 })[mucCua(a)] - ({ do: 0, vang: 1, xanh: 2 })[mucCua(b)],
  );
  const cn = CHI_NHANH[xem];
  const demMuc = { do: 0, vang: 0, xanh: 0 };
  CHI_NHANH.forEach((c) => (demMuc[mucCua(c) as "do" | "vang" | "xanh"] += 1));

  return (
    <div className="flex h-full flex-col bg-steel-100 font-sans text-ink">
      {/* ---------------- Header ---------------- */}
      <header className="flex items-center gap-4 bg-gradient-to-br from-navy-dark via-navy to-navy-400 px-6 py-3 text-white shadow-header">
        <div className="grid h-10 w-10 place-items-center rounded-xl border border-white/25 bg-white/15 text-[15px] font-extrabold tracking-wide shadow-inner">
          KS
        </div>
        <div>
          <h1 className="text-[17px] font-bold leading-tight">Kiểm tra khóa sổ cuối kỳ</h1>
          <p className="text-[12px] text-steel-200">Doanh nghiệp sản xuất · Thông tư 200</p>
        </div>
        <div className="ml-auto flex items-center gap-2.5">
          <span className="hidden items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-3.5 py-2 text-[13px] font-semibold text-white md:inline-flex">
            8 chi nhánh · kỳ 08/2026
          </span>
          <NutHeader icon={I.clock}>Lịch sử chốt sổ</NutHeader>
          <NutHeader icon={I.gear}>Cài đặt</NutHeader>
        </div>
      </header>

      {/* ---------------- Thân: 2 cột ---------------- */}
      <div className="mx-auto flex w-full max-w-[1240px] flex-1 gap-4 overflow-hidden p-4">
        {/* Sidebar chi nhánh */}
        <aside className="flex w-[260px] shrink-0 flex-col gap-3 overflow-hidden">
          <div className="flex items-baseline justify-between px-1">
            <h2 className="text-[13px] font-bold text-ink">Danh sách chi nhánh</h2>
            <span className="text-[12px] font-semibold text-steel-400 tnum">{CHI_NHANH.length}</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-steel-200 bg-white px-3 py-2 shadow-soft">
            <Svg d={I.search} cls="h-4 w-4 text-steel-400" />
            <input placeholder="Tìm chi nhánh…" className="w-full bg-transparent text-[13px] outline-none placeholder:text-steel-400" />
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 px-1 text-[11.5px] font-semibold">
            {demMuc.do > 0 && <span className="text-do-dam">● {demMuc.do} chưa sẵn sàng</span>}
            {demMuc.vang > 0 && <span className="text-vang-dam">● {demMuc.vang} cần rà</span>}
            {demMuc.xanh > 0 && <span className="text-xanh-dam">● {demMuc.xanh} sẵn sàng</span>}
          </div>
          <div className="-mr-1 flex flex-col gap-2 overflow-y-auto pr-1">
            {dsSap.map((c) => (
              <TheChiNhanh key={c.ma} c={c} chon={c.ma === cn.ma} onClick={() => setXem(CHI_NHANH.indexOf(c))} />
            ))}
          </div>
        </aside>

        {/* Khu chính */}
        <main className="flex min-w-0 flex-1 flex-col gap-3 overflow-hidden">
          {/* Banner kết luận */}
          <section className="relative overflow-hidden rounded-2xl border border-steel-200 bg-white p-4 shadow-card">
            <span className="absolute inset-y-0 left-0 w-[5px] bg-do" />
            <div className="flex flex-wrap items-center gap-4 pl-1">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-do-nen text-do">
                <Svg d={I.x} cls="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-[16px] font-extrabold text-do-dam">
                  CHƯA SẴN SÀNG KHÓA SỔ — còn {cn.do + cn.vang} việc phải xử lý
                </h2>
                <p className="mt-0.5 truncate text-[12.5px] text-steel-500">
                  Chi nhánh {cn.ma} · Kỳ 08/2026 · Bảng kê 082026 · <span className="tnum">80.868</span> dòng
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StatPill mau="do" nhan="Nghiêm trọng" so={cn.do} />
                <StatPill mau="vang" nhan="Cảnh báo" so={cn.vang} />
                <StatPill mau="xanh" nhan="Đạt" so={cn.dat} />
              </div>
              <button className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-navy-dark to-navy px-5 py-3 text-[14px] font-bold text-white shadow-card transition hover:from-navy hover:to-navy-400">
                <Svg d={I.lock} cls="h-4 w-4" />Chốt sổ kỳ này
              </button>
            </div>
          </section>

          {/* Tabs + bảng bước */}
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-steel-200 bg-white shadow-card">
            <div className="flex items-center gap-1 border-b border-steel-200 px-3">
              {([["trangthai", "Trạng thái khóa sổ"], ["loi", "Lỗi & cảnh báo"]] as const).map(([k, ten]) => (
                <button
                  key={k}
                  onClick={() => setTab(k)}
                  className={`relative px-4 py-3 text-[13.5px] font-semibold transition
                    ${tab === k ? "text-navy" : "text-steel-500 hover:text-ink"}`}
                >
                  {ten}
                  {tab === k && <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-navy" />}
                </button>
              ))}
              <span className="ml-auto pr-3 text-[12px] text-steel-400">
                Cập nhật lần cuối: <span className="tnum">26/08/2026 10:24</span>
              </span>
            </div>
            <div className="flex items-center gap-4 border-b border-steel-100 px-5 py-2.5 text-[12px] font-bold uppercase tracking-wide text-steel-400">
              <span className="w-6 text-right">#</span>
              <span className="w-7" />
              <span className="flex-1">Nội dung kiểm tra</span>
              <span className="pr-6">Trạng thái</span>
            </div>
            <div className="min-h-0 flex-1 divide-y divide-steel-100 overflow-y-auto">
              {BUOC.map((b) => <DongBuoc key={b.i} b={b} />)}
            </div>
          </div>

          {/* Footer hành động */}
          <footer className="flex flex-wrap items-center gap-2 border-t border-steel-200 pt-3">
            <button className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-navy-dark to-navy px-4 py-2.5 text-[13px] font-bold text-white shadow-soft transition hover:from-navy hover:to-navy-400">
              Xuất báo cáo Excel
            </button>
            <button className="rounded-xl border border-steel-200 bg-white px-4 py-2.5 text-[13px] font-semibold text-navy shadow-soft transition hover:border-steel-300">Xuất tổng hợp chi nhánh</button>
            <button className="rounded-xl border border-steel-200 bg-white px-4 py-2.5 text-[13px] font-semibold text-navy shadow-soft transition hover:border-steel-300">Kiểm tra lại</button>
            <button className="ml-auto rounded-xl border border-steel-200 bg-white px-4 py-2.5 text-[13px] font-semibold text-navy shadow-soft transition hover:border-steel-300">Kiểm tra file khác</button>
          </footer>
        </main>
      </div>
    </div>
  );
}
