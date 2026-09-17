/** Màn KẾT QUẢ — sidebar chi nhánh + banner kết luận + bảng bước/lỗi. Nối dữ liệu thật. */
import { useMemo, useState } from "react";
import type { Buoc, Check, DonVi, KetQua, Nhom } from "./api";
import { cx, Dau, fso, Icon, IC, khoaKL, KY_HIEU, Nut } from "./ui";

const MUC = { chua_san_sang: "do", can_ra_soat: "vang", san_sang: "xanh" } as const;
const mucDonVi = (d: DonVi) => MUC[khoaKL(d.muc_do_ket_luan)];

/* --------------------------- 4 thẻ thống kê ------------------------------- */
export function TheThongKe({ soDo, soVang, dat, soChiNhanh, onXemLoi }:
  { soDo: number; soVang: number; dat: number; soChiNhanh: number; onXemLoi?: () => void }) {
  const cards = [
    { ic: IC.x, nhan: "Nghiêm trọng", so: soDo, phu: "cần xử lý ngay", nen: "bg-do-nen", vien: "border-do-vien", ico: "bg-do/15 text-do", chu: "text-do-dam", nhay: true },
    { ic: IC.warn, nhan: "Cảnh báo", so: soVang, phu: "cần kiểm tra thêm", nen: "bg-vang-nen", vien: "border-vang-vien", ico: "bg-vang/15 text-vang", chu: "text-vang-dam", nhay: true },
    { ic: IC.check, nhan: "Đạt", so: dat, phu: "đã hoàn thành", nen: "bg-xanh-nen", vien: "border-xanh-vien", ico: "bg-xanh/15 text-xanh", chu: "text-xanh-dam", nhay: false },
    { ic: IC.toanha, nhan: "Tổng chi nhánh", so: soChiNhanh, phu: "trong kỳ này", nen: "bg-steel-50", vien: "border-steel-200", ico: "bg-steel-200/70 text-steel-700", chu: "text-steel-700", nhay: false },
  ];
  return (
    <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
      {cards.map((c) => {
        const bam = !!onXemLoi && c.nhay && c.so > 0;
        return (
          <button key={c.nhan} type="button" disabled={!bam} onClick={bam ? onXemLoi : undefined}
            className={cx("flex items-center gap-3 rounded-xl border px-3.5 py-2.5 text-left shadow-soft transition", c.nen, c.vien,
              bam ? "cursor-pointer hover:shadow-card" : "cursor-default")}>
            <span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-full", c.ico)}><Icon d={c.ic} className="h-[18px] w-[18px]" /></span>
            <div className="min-w-0">
              <div className={cx("text-[12px] font-bold leading-tight", c.chu)}>{c.nhan}</div>
              <div className="flex items-baseline gap-1.5">
                <span className={cx("text-[22px] font-extrabold leading-tight tabular-nums", c.chu)}>{fso(c.so)}</span>
                <span className="truncate text-[11px] text-steel-500">{c.phu}</span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

/* --------------------- khu mục theo mức độ (đỏ / vàng) -------------------- */
function KhuMuc({ mau, tieuDe, ds, onCheck }: { mau: "do" | "vang"; tieuDe: string; ds: Check[]; onCheck: (c: Check) => void }) {
  const s = mau === "do"
    ? { vien: "border-do-vien", nen: "bg-do-nen", chu: "text-do-dam", ic: IC.x }
    : { vien: "border-vang-vien", nen: "bg-vang-nen", chu: "text-vang-dam", ic: IC.warn };
  return (
    <section className={cx("overflow-hidden rounded-xl border-2", s.vien)}>
      <div className={cx("flex items-center gap-2 px-4 py-2.5", s.nen)}>
        <Icon d={s.ic} className={cx("h-4 w-4", s.chu)} />
        <span className={cx("text-[13.5px] font-extrabold uppercase tracking-wide", s.chu)}>{tieuDe}</span>
        <span className={cx("ml-auto rounded-full bg-white/80 px-2.5 py-0.5 text-[12px] font-extrabold tabular-nums", s.chu)}>{ds.length}</span>
      </div>
      <div className="divide-y divide-steel-100 bg-white">
        {ds.map((c) => (
          <button key={c.ma} onClick={() => onCheck(c)}
            className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition hover:bg-steel-50">
            <Dau muc={mau} />
            <span className="shrink-0 text-[12px] font-bold text-steel-400">{c.ma}</span>
            <span className="min-w-0 flex-1 truncate text-[13px] text-ink">{c.ten}{c.ghi_chu ? <span className="text-steel-400"> — {c.ghi_chu}</span> : null}</span>
            <span className={cx("shrink-0 text-[12px] font-extrabold tabular-nums", s.chu)}>{fso(c.so_loi)}</span>
            <Icon d={IC.chevR} className="h-4 w-4 shrink-0 text-steel-300" />
          </button>
        ))}
      </div>
    </section>
  );
}

function DongSo({ mau, nhan, so }: { mau: "do" | "vang" | "xanh"; nhan: string; so: number }) {
  const t = { do: "text-do-dam", vang: "text-vang-dam", xanh: "text-xanh-dam" }[mau];
  return (
    <div className="flex items-center gap-2 rounded-md bg-steel-50 px-2 py-1">
      <Dau muc={mau} className="h-[15px] w-[15px] text-[9px]" />
      <span className={cx("flex-1 text-[11.5px] font-semibold", t)}>{nhan}</span>
      <span className={cx("text-[13px] font-extrabold tabular-nums", t)}>{fso(so)}</span>
    </div>
  );
}

function ChotChip({ chot }: { chot?: DonVi["chot"] }) {
  if (!chot || chot.trang_thai !== "DA_CHOT")
    return <span className="rounded-full bg-steel-100 px-2 py-0.5 text-[11px] font-semibold text-steel-500">Chưa chốt</span>;
  if (chot.doi_chieu === "LECH")
    return <span className="inline-flex items-center gap-1 rounded-full bg-vang-nen px-2 py-0.5 text-[11px] font-semibold text-vang-dam"><Icon d={IC.warn} className="h-3 w-3" />Dữ liệu đổi</span>;
  return <span className="inline-flex items-center gap-1 rounded-full bg-xanh-nen px-2 py-0.5 text-[11px] font-semibold text-xanh-dam"><Icon d={IC.lock} className="h-3 w-3" />Đã chốt</span>;
}

function TheChiNhanh({ d, tongCheck, chon, onClick }: { d: DonVi; tongCheck: number; chon: boolean; onClick: () => void }) {
  const dat = Math.max(0, tongCheck - (d.so_do ?? 0) - (d.so_vang ?? 0));
  return (
    <button
      onClick={onClick}
      className={cx(
        "w-full rounded-xl border bg-white p-2.5 text-left shadow-soft transition",
        chon ? "border-navy ring-1 ring-navy/30" : "border-steel-200 hover:border-steel-300 hover:shadow-card",
      )}
      style={chon ? { boxShadow: "inset 3px 0 0 #1B4B7A" } : undefined}
    >
      <div className="mb-2 flex items-center gap-2">
        <Dau muc={mucDonVi(d)} className="h-[19px] w-[19px] text-[11px]" />
        <span className="min-w-0 truncate text-[14px] font-bold text-ink">{d.ten_hien || d.ma}</span>
        {d.ten_hien && d.ten_hien !== d.ma && <span className="shrink-0 text-[11px] font-semibold text-steel-400">{d.ma}</span>}
        <span className="ml-auto shrink-0"><ChotChip chot={d.chot} /></span>
      </div>
      <div className="space-y-1">
        <DongSo mau="do" nhan="Nghiêm trọng" so={d.so_do ?? 0} />
        <DongSo mau="vang" nhan="Cảnh báo" so={d.so_vang ?? 0} />
        <DongSo mau="xanh" nhan="Đạt" so={dat} />
      </div>
    </button>
  );
}

/* -------------------------------- bảng bước ------------------------------- */
const CFG_BUOC = {
  // Mù màu: mỗi trạng thái một NÉT icon riêng — trước đây 3 trạng thái dùng chung
  // IC.checkNho và chỉ phân biệt bằng màu pill.
  DA_LAM: { pill: "bg-xanh-nen text-xanh-dam", nhan: "Đã làm", ic: IC.check, ring: "border-xanh-vien text-xanh" },
  CAN_RA: { pill: "bg-vang-nen text-vang-dam", nhan: "Cần rà", ic: IC.warn, ring: "border-vang-vien text-vang" },
  CHUA_LAM: { pill: "bg-do-nen text-do-dam", nhan: "Chưa làm", ic: IC.x, ring: "border-do-vien text-do" },
  TU_XAC_NHAN: { pill: "bg-steel-100 text-steel-500", nhan: "Tự xác nhận", ic: IC.oTick, ring: "border-steel-200 text-steel-400" },
  KHONG_AP_DUNG: { pill: "bg-steel-100 text-steel-400", nhan: "Không áp dụng", ic: IC.khongApDung, ring: "border-steel-200 text-steel-300" },
} as const;
function cfgBuoc(tt: string) {
  // Backend gửi trạng thái bước dạng CHỮ THƯỜNG (da_lam, can_ra, chua_lam,
  // tu_xac_nhan, khong_ap_dung — xem app/trang_thai.py); khoá CFG_BUOC là CHỮ HOA.
  // Không chuẩn hoá thì mọi bước đều rơi vào nhánh mặc định "Không áp dụng".
  return CFG_BUOC[String(tt).toUpperCase() as keyof typeof CFG_BUOC] ?? CFG_BUOC.KHONG_AP_DUNG;
}

function DongBuoc({ b, stt, onClick }: { b: Buoc; stt: number; onClick?: () => void }) {
  const c = cfgBuoc(b.trang_thai);
  return (
    <button
      onClick={onClick}
      disabled={!b.co_chung_cu}
      className="flex w-full items-center gap-4 px-5 py-3.5 text-left transition enabled:hover:bg-steel-50 disabled:cursor-default"
    >
      <span className="w-6 shrink-0 text-right text-[13px] font-semibold tabular-nums text-steel-400">{stt}</span>
      <span className={cx("grid h-7 w-7 shrink-0 place-items-center rounded-full border", c.ring)}>
        <Icon d={c.ic} className="h-4 w-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[14px] font-semibold text-ink">{b.buoc}</span>
        <span className="block truncate text-[12.5px] text-steel-500">{b.tom_tat}</span>
      </span>
      <span className={cx("inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[12px] font-semibold", c.pill)}>
        <Icon d={c.ic} className="h-3.5 w-3.5" />{c.nhan}
      </span>
      {b.co_chung_cu ? <Icon d={IC.chevR} className="h-4 w-4 shrink-0 text-steel-300" /> : <span className="w-4" />}
    </button>
  );
}

/* --------------------------------- lỗi (nhóm) ----------------------------- */
function TheNhom({ n, onCheck }: { n: Nhom; onCheck: (c: Check) => void }) {
  const [mo, setMo] = useState(true);
  const muc = n.checks.some((c) => !c.la_thong_ke && c.so_loi > 0 && c.muc_do === "do")
    ? "do" : n.checks.some((c) => !c.la_thong_ke && c.so_loi > 0) ? "vang" : "xanh";
  return (
    <div className="overflow-hidden rounded-xl border border-steel-200">
      <button onClick={() => setMo((v) => !v)} className="flex w-full items-center gap-3 bg-steel-50 px-4 py-2.5 text-left">
        <Dau muc={muc} />
        <span className="rounded-md bg-white px-2 py-0.5 text-[12px] font-bold text-steel-500 ring-1 ring-steel-200">{n.ma}</span>
        <span className="text-[13.5px] font-semibold text-ink">{n.ten}</span>
        <span className="ml-auto text-[12px] font-semibold text-steel-400 tabular-nums">{fso(n.so_loi)} lỗi</span>
        <Icon d={IC.chevDown} className={cx("h-4 w-4 text-steel-400 transition", mo && "rotate-180")} />
      </button>
      {mo && (
        <div className="divide-y divide-steel-100">
          {n.checks.map((c) => {
            const md = c.la_thong_ke ? "xam" : c.so_loi === 0 ? "xanh" : c.muc_do;
            return (
              <button key={c.ma} onClick={() => onCheck(c)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition hover:bg-steel-50">
                <Dau muc={md} className="h-[15px] w-[15px] text-[9px]" />
                <span className="text-[12px] font-bold text-steel-400">{c.ma}</span>
                <span className="min-w-0 flex-1 truncate text-[13px] text-ink">{c.ten}{c.ghi_chu ? <span className="text-steel-400"> — {c.ghi_chu}</span> : null}</span>
                {!c.la_thong_ke && c.so_loi > 0 && <span className="text-[12px] font-bold tabular-nums text-do-dam">{fso(c.so_loi)}</span>}
                <Icon d={IC.chevR} className="h-4 w-4 shrink-0 text-steel-300" />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* --------------------------------- màn ------------------------------------ */
export interface KetQuaProps {
  kq: KetQua;
  nhieu: boolean;
  onChonDonVi: (i: number) => void;
  onChot: () => void;
  onMoLai: () => void;
  onChotLai: () => void;
  onCapNhatChotLai: () => void;
  onXemChiTiet: (maCheck: string, tieuDe: string) => void;
  onXemThayDoi: () => void;
  onXuat: () => void;
  onXuatTongHop: () => void;
  onKiemTraLai: () => void;
  onFileKhac: () => void;
}

export default function ManKetQua(p: KetQuaProps) {
  const { kq } = p;
  const t = kq.tomtat;
  const muc = khoaKL(t.muc_do_ket_luan);
  const mauKL = MUC[muc];
  const [tab, setTab] = useState<"trangthai" | "loi">("trangthai");

  const tongCheck = useMemo(
    () => kq.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke).length,
    [kq.nhom],
  );
  const dat = Math.max(0, tongCheck - t.so_do - t.so_vang);
  const dsSap = useMemo(
    () => [...kq.don_vi].sort((a, b) => ({ do: 0, vang: 1, xanh: 2 })[mucDonVi(a)] - ({ do: 0, vang: 1, xanh: 2 })[mucDonVi(b)]),
    [kq.don_vi],
  );
  const dsLoi = useMemo(
    () => kq.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke && c.so_loi > 0),
    [kq.nhom],
  );
  const dsDo = dsLoi.filter((c) => c.muc_do === "do");
  const dsVang = dsLoi.filter((c) => c.muc_do === "vang");
  const demMuc = { do: 0, vang: 0, xanh: 0 };
  kq.don_vi.forEach((d) => (demMuc[mucDonVi(d)] += 1));

  const bVien = { do: "bg-do", vang: "bg-vang", xanh: "bg-xanh" }[mauKL];
  const bNen = { do: "bg-do-nen text-do", vang: "bg-vang-nen text-vang", xanh: "bg-xanh-nen text-xanh" }[mauKL];
  const bChu = { do: "text-do-dam", vang: "text-vang-dam", xanh: "text-xanh-dam" }[mauKL];
  const bIcon = { do: IC.x, vang: IC.warn, xanh: IC.check }[mauKL];
  const chot = t.chot;
  const daChot = chot?.trang_thai === "DA_CHOT";
  const lech = daChot && chot.doi_chieu === "LECH";

  return (
    <div className="flex w-full flex-1 flex-col gap-4 overflow-hidden p-5">
      {/* 4 thẻ thống kê — full width trên cùng (theo mockup dashboard) */}
      <TheThongKe soDo={t.so_do} soVang={t.so_vang} dat={dat} soChiNhanh={kq.don_vi.length} onXemLoi={() => setTab("loi")} />

      {/* Hàng: danh sách chi nhánh | khu chính */}
      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
      {/* Sidebar */}
      {p.nhieu && (
        <aside className="flex w-[260px] shrink-0 flex-col gap-3 overflow-hidden">
          <div className="flex items-baseline justify-between px-1">
            <h2 className="text-[13px] font-bold text-ink">Danh sách chi nhánh</h2>
            <span className="text-[12px] font-semibold text-steel-400 tabular-nums">{kq.don_vi.length}</span>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 px-1 text-[11.5px] font-semibold">
            {demMuc.do > 0 && <span className="text-do-dam">{KY_HIEU.do} {demMuc.do} chưa sẵn sàng</span>}
            {demMuc.vang > 0 && <span className="text-vang-dam">{KY_HIEU.vang} {demMuc.vang} cần rà</span>}
            {demMuc.xanh > 0 && <span className="text-xanh-dam">{KY_HIEU.xanh} {demMuc.xanh} sẵn sàng</span>}
          </div>
          <div className="-mr-1 flex flex-col gap-2 overflow-y-auto pr-1">
            {dsSap.map((d) => (
              <TheChiNhanh key={d.i} d={d} tongCheck={tongCheck} chon={d.i === kq.dang_xem} onClick={() => p.onChonDonVi(d.i)} />
            ))}
          </div>
        </aside>
      )}

      {/* Khu chính */}
      <main className="flex min-w-0 flex-1 flex-col gap-3 overflow-hidden">
        {/* Banner */}
        <section className="relative overflow-hidden rounded-2xl border border-steel-200 bg-white p-4 shadow-card">
          <span className={cx("absolute inset-y-0 left-0 w-[5px]", bVien)} />
          <div className="flex flex-wrap items-center gap-4 pl-1">
            <span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-full", bNen)}>
              <Icon d={bIcon} className="h-5 w-5" />
            </span>
            <div className="min-w-0 flex-1">
              <h2 className={cx("text-[16px] font-extrabold", bChu)}>{t.cau_ket_luan}</h2>
              <p className="mt-0.5 truncate text-[12.5px] text-steel-500">
                {p.nhieu && <>Chi nhánh {t.chi_nhanh_ten || t.chi_nhanh}{t.chi_nhanh_ten && t.chi_nhanh_ten !== t.chi_nhanh ? ` (${t.chi_nhanh})` : ""} · </>}Kỳ {t.ky} · {t.ten} · <span className="tabular-nums">{fso(t.so_dong)}</span> dòng
              </p>
            </div>
            {/* Hành động chốt */}
            {daChot ? (
              <div className="flex flex-col gap-1.5">
                <div className={cx("flex items-center gap-1.5 text-[13px] font-semibold", lech ? "text-vang-dam" : "text-xanh-dam")}>
                  <Icon d={IC.lock} className="h-4 w-4" />Đã chốt {(chot!.ngay_chot ?? "").slice(0, 10).split("-").reverse().join("/")}
                </div>
                <div className="flex gap-1.5">
                  <Nut bien="phu" className="px-3 py-1.5 text-[12px]" onClick={p.onMoLai}>Mở lại</Nut>
                  <Nut bien="phu" className="px-3 py-1.5 text-[12px]" onClick={p.onChotLai}>Chốt lại</Nut>
                </div>
              </div>
            ) : (
              <Nut bien="chinh" className="px-5 py-3 text-[14px]" onClick={p.onChot}>
                <Icon d={IC.lock} className="h-4 w-4" />Chốt sổ kỳ này
              </Nut>
            )}
          </div>
        </section>

        {/* Băng drift khi LỆCH */}
        {lech && (
          <section className="rounded-xl border border-vang-vien bg-vang-nen px-4 py-3">
            <div className="flex items-center gap-2 text-[14px] font-bold text-vang-dam">
              <Icon d={IC.warn} className="h-4 w-4" />Kỳ đã chốt nhưng dữ liệu nguồn đã thay đổi
            </div>
            <div className="mt-1 text-[13px] text-vang-dam">
              Δ dòng: <b className="tabular-nums text-ink">{chot!.tom_tat_lech!.delta_dong > 0 ? "+" : ""}{fso(chot!.tom_tat_lech!.delta_dong)}</b> ·
              Δ tổng phát sinh: <b className="tabular-nums text-ink">{fso(chot!.tom_tat_lech!.delta_ps)}</b> ·
              <b className="tabular-nums text-ink"> {fso(chot!.tom_tat_lech!.so_ct_anh_huong)}</b> chứng từ ảnh hưởng
            </div>
            <div className="mt-2 flex gap-2">
              <Nut bien="phu" className="px-3 py-1.5 text-[12px]" onClick={p.onXemThayDoi}>Xem thay đổi</Nut>
              <Nut bien="chinh" className="px-3 py-1.5 text-[12px]" onClick={p.onCapNhatChotLai}>Cập nhật & chốt lại</Nut>
            </div>
          </section>
        )}

        {/* Tabs + nội dung */}
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-steel-200 bg-white shadow-card">
          <div className="flex items-center gap-1 border-b border-steel-200 px-3">
            {(["trangthai", "loi"] as const).map((k) => (
              <button key={k} onClick={() => setTab(k)}
                className={cx("relative flex items-center gap-1.5 px-4 py-3 text-[13.5px] font-semibold transition", tab === k ? "text-navy" : "text-steel-500 hover:text-ink")}>
                {k === "trangthai" ? "Trạng thái khóa sổ" : "Lỗi & cảnh báo"}
                {k === "loi" && dsDo.length > 0 && (
                  <span className="rounded-full bg-do-nen px-1.5 py-0.5 text-[11px] font-bold text-do-dam tabular-nums">{KY_HIEU.do} {dsDo.length}</span>
                )}
                {k === "loi" && dsVang.length > 0 && (
                  <span className="rounded-full bg-vang-nen px-1.5 py-0.5 text-[11px] font-bold text-vang-dam tabular-nums">{KY_HIEU.vang} {dsVang.length}</span>
                )}
                {tab === k && <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-navy" />}
              </button>
            ))}
          </div>

          {tab === "trangthai" ? (
            <>
              {/* Dải hòa giải: 16 bước ≠ kết luận. Lỗi chặn (C1.5/C5.x/C3.2…) là kiểm tra
                  dữ liệu, KHÔNG nằm trong 16 bước — nhắc để không hiểu nhầm "đã xong". */}
              {dsDo.length > 0 || dsVang.length > 0 ? (
                <button onClick={() => setTab("loi")}
                  className={cx("flex items-center gap-2.5 border-b px-5 py-2.5 text-left text-[13px] font-semibold transition",
                    dsDo.length > 0 ? "border-do-vien bg-do-nen text-do-dam hover:brightness-95" : "border-vang-vien bg-vang-nen text-vang-dam hover:brightness-95")}>
                  <Icon d={dsDo.length > 0 ? IC.x : IC.warn} className="h-4 w-4 shrink-0" />
                  <span>Ngoài 16 bước, phần soát dữ liệu còn
                    {dsDo.length > 0 && <> <b>{dsDo.length} nghiêm trọng</b></>}
                    {dsDo.length > 0 && dsVang.length > 0 && " ·"}
                    {dsVang.length > 0 && <> <b>{dsVang.length} cảnh báo</b></>} cần xử lý.</span>
                  <span className="ml-auto shrink-0 whitespace-nowrap underline">Xem Lỗi &amp; cảnh báo →</span>
                </button>
              ) : (
                <div className="flex items-center gap-2.5 border-b border-xanh-vien bg-xanh-nen px-5 py-2.5 text-[13px] font-semibold text-xanh-dam">
                  <Icon d={IC.check} className="h-4 w-4 shrink-0" />
                  <span>Không còn lỗi hay cảnh báo — sẵn sàng khóa sổ.</span>
                </div>
              )}
              <div className="flex items-center gap-4 border-b border-steel-100 px-5 py-2.5 text-[11.5px] font-bold uppercase tracking-wide text-steel-400">
                <span className="w-6 text-right">#</span><span className="w-7" />
                <span className="flex-1">Nội dung kiểm tra</span><span className="pr-6">Trạng thái</span>
              </div>
              <div className="min-h-0 flex-1 divide-y divide-steel-100 overflow-y-auto">
                {kq.trang_thai.map((b, i) => (
                  <DongBuoc key={i} b={b} stt={i + 1}
                    onClick={b.co_chung_cu ? () => p.onXemChiTiet(b.ma_check, `${b.buoc} — chứng minh (${b.ma_check})`) : undefined} />
                ))}
              </div>
            </>
          ) : (
            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
              {dsDo.length === 0 && dsVang.length === 0 && (
                <div className="rounded-xl border-2 border-xanh-vien bg-xanh-nen px-4 py-6 text-center text-[13px] font-bold text-xanh-dam">
                  Không có lỗi hay cảnh báo nào.
                </div>
              )}
              {dsDo.length > 0 && (
                <KhuMuc mau="do" tieuDe="Nghiêm trọng — phải xử lý" ds={dsDo}
                  onCheck={(c) => p.onXemChiTiet(c.ma, `${c.ma} · ${c.ten}`)} />
              )}
              {dsVang.length > 0 && (
                <KhuMuc mau="vang" tieuDe="Cảnh báo — nên rà soát" ds={dsVang}
                  onCheck={(c) => p.onXemChiTiet(c.ma, `${c.ma} · ${c.ten}`)} />
              )}
              {/* Chi tiết đầy đủ theo nhóm (gồm mục thống kê & đã đạt) — thu gọn */}
              <details className="overflow-hidden rounded-xl border border-steel-200">
                <summary className="cursor-pointer select-none px-4 py-2.5 text-[13px] font-semibold text-steel-500 hover:bg-steel-50">
                  Xem tất cả theo nhóm (gồm mục thống kê &amp; đã đạt)
                </summary>
                <div className="space-y-2.5 border-t border-steel-100 p-3">
                  {kq.nhom.map((n) => (
                    <TheNhom key={n.ma} n={n} onCheck={(c) => p.onXemChiTiet(c.ma, `${c.ma} · ${c.ten}`)} />
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="flex flex-wrap items-center gap-2 border-t border-steel-200 pt-3">
          <Nut bien="chinh" onClick={p.onXuat}><Icon d={IC.taiXuong} className="h-4 w-4" />Xuất báo cáo Excel</Nut>
          {p.nhieu && <Nut onClick={p.onXuatTongHop}><Icon d={IC.bar} className="h-4 w-4" />Xuất tổng hợp chi nhánh</Nut>}
          <Nut onClick={p.onKiemTraLai}><Icon d={IC.lam_moi} className="h-4 w-4" />Kiểm tra lại</Nut>
          <Nut className="ml-auto" onClick={p.onFileKhac}><Icon d={IC.file} className="h-4 w-4" />Kiểm tra file khác</Nut>
        </footer>
      </main>
      </div>
    </div>
  );
}
