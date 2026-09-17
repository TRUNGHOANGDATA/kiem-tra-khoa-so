/** Màn xem Cân đối số phát sinh (CĐPS) đã nhập: chọn (chi nhánh × kỳ) -> chi tiết tài khoản. */
import { useCallback, useEffect, useMemo, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { cx, fso, Icon, IC, Nut, useToast } from "./ui";

interface TrangThai { chi_nhanh: string; chi_nhanh_ten?: string; ky: string; thoi_diem_nap?: string }
interface DongCdps {
  account: string; ten: string; du_dau_no: number; du_dau_co: number;
  ps_no: number; ps_co: number; du_cuoi_no: number; du_cuoi_co: number; is_group: number | boolean; level: number;
}

const n0 = (v: number) => (v ? fso(v) : "");

export default function ManCanDoi({ onQuayLai }: { onQuayLai: () => void }) {
  const toast = useToast();
  const [ts, setTs] = useState<TrangThai[]>([]);
  const [chon, setChon] = useState<TrangThai | null>(null);
  const [dong, setDong] = useState<DongCdps[]>([]);
  const [fKy, setFKy] = useState("all");
  const [fCn, setFCn] = useState("all");
  const [tim, setTim] = useState("");
  const [anNhom, setAnNhom] = useState(false);
  // Chọn xong chi nhánh thì tự thu danh sách: 6 cột số của CĐPS cần gần hết
  // bề ngang, để cả hai thì lần nào cũng phải kéo ngang mới đọc được.
  const [thuGon, setThuGon] = useState(false);

  useEffect(() => {
    A.goi("trang_thai_cdps").then((r) => { if (Array.isArray(r)) setTs(r as TrangThai[]); });
  }, []);

  const kyOpts = useMemo(() => [...new Set(ts.map((t) => t.ky))].sort().reverse(), [ts]);
  const cnOpts = useMemo(() => [...new Map(ts.map((t) => [t.chi_nhanh, t.chi_nhanh_ten || t.chi_nhanh])).entries()], [ts]);
  const loc = ts.filter((t) => (fKy === "all" || t.ky === fKy) && (fCn === "all" || t.chi_nhanh === fCn));

  const xemChiTiet = useCallback(async (t: TrangThai) => {
    setChon(t); setDong([]); setThuGon(true);
    const [thang, nam] = t.ky.split("/");
    const r = await A.goi("chi_tiet_cdps", t.chi_nhanh, Number(nam), Number(thang));
    if (laLoi(r)) { toast(r.loi); return; }
    setDong((r.dong as DongCdps[]) ?? []);
  }, [toast]);

  const dongLoc = dong.filter((d) => {
    if (anNhom && (d.is_group === 1 || d.is_group === true)) return false;
    const q = tim.trim().toLowerCase();
    return !q || d.account.toLowerCase().includes(q) || (d.ten || "").toLowerCase().includes(q);
  });

  return (
    <div className="flex w-full flex-1 flex-col gap-4 overflow-hidden p-5">
      <div className="flex items-center gap-3">
        <h2 className="text-[18px] font-extrabold text-ink">Cân đối số phát sinh</h2>
        <Nut bien="phu" className="ml-auto" onClick={onQuayLai}><Icon d={IC.chevL} className="h-4 w-4" />Quay lại</Nut>
      </div>

      {/* Bộ lọc danh sách */}
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        <span className="font-semibold text-steel-500">Lọc:</span>
        <select value={fKy} onChange={(e) => setFKy(e.target.value)}
          className="rounded-lg border border-steel-200 bg-white px-2.5 py-1.5 outline-none focus:border-navy-400">
          <option value="all">Mọi kỳ</option>
          {kyOpts.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <select value={fCn} onChange={(e) => setFCn(e.target.value)}
          className="rounded-lg border border-steel-200 bg-white px-2.5 py-1.5 outline-none focus:border-navy-400">
          <option value="all">Mọi chi nhánh</option>
          {cnOpts.map(([ma, ten]) => <option key={ma} value={ma}>{ten}</option>)}
        </select>
        <span className="ml-auto text-[12px] font-semibold text-steel-400 tabular-nums">{loc.length} kỳ/chi nhánh</span>
      </div>

      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
        {/* Danh sách (chi nhánh × kỳ) */}
        {!thuGon && (
        <aside className="flex w-[196px] shrink-0 flex-col gap-2 overflow-y-auto pr-1">
          {loc.length === 0 && <div className="rounded-xl bg-steel-50 px-3 py-4 text-center text-[12.5px] text-steel-400">Chưa nhập CĐPS nào.</div>}
          {loc.map((t) => (
            <button key={`${t.chi_nhanh}|${t.ky}`} onClick={() => xemChiTiet(t)}
              className={cx("rounded-xl border bg-white p-2.5 text-left shadow-soft transition",
                chon && chon.chi_nhanh === t.chi_nhanh && chon.ky === t.ky ? "border-navy ring-1 ring-navy/30" : "border-steel-200 hover:border-steel-300")}>
              <div className="flex items-center gap-2">
                <span className="min-w-0 truncate text-[13px] font-bold text-ink">{t.chi_nhanh_ten || t.chi_nhanh}</span>
                <span className="ml-auto shrink-0 rounded-md bg-steel-100 px-1.5 py-0.5 text-[11px] font-bold text-steel-600 tabular-nums">{t.ky}</span>
              </div>
              {t.thoi_diem_nap && <div className="mt-1 truncate text-[11px] text-steel-400">Nạp: {t.thoi_diem_nap.slice(0, 10).split("-").reverse().join("/")}</div>}
            </button>
          ))}
        </aside>
        )}

        {/* Chi tiết tài khoản */}
        <main className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-steel-200 bg-white shadow-card">
          {!chon ? (
            <div className="grid flex-1 place-items-center text-[13px] text-steel-400">Chọn một kỳ/chi nhánh bên trái để xem chi tiết.</div>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2 border-b border-steel-200 px-4 py-2.5">
                <button onClick={() => setThuGon((v) => !v)} title={thuGon ? "Hiện danh sách chi nhánh" : "Ẩn danh sách để bảng rộng hơn"}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-steel-200 px-2 py-1 text-[12px] font-semibold text-steel-600 hover:border-steel-300">
                  <Icon d={thuGon ? IC.chevR : IC.chevL} className="h-3.5 w-3.5" />{thuGon ? "Hiện danh sách" : "Ẩn danh sách"}
                </button>
                <span className="text-[13.5px] font-bold text-ink">{chon.chi_nhanh_ten || chon.chi_nhanh} · kỳ {chon.ky}</span>
                <div className="ml-auto flex items-center gap-2">
                  <div className="flex items-center gap-1.5 rounded-lg border border-steel-200 px-2 py-1">
                    <Icon d={IC.search} className="h-3.5 w-3.5 text-steel-400" />
                    <input value={tim} onChange={(e) => setTim(e.target.value)} placeholder="Tìm số hiệu / tên TK…"
                      className="w-44 text-[12.5px] outline-none" />
                  </div>
                  <label className="inline-flex items-center gap-1.5 text-[12.5px] text-steel-600">
                    <input type="checkbox" checked={anNhom} onChange={(e) => setAnNhom(e.target.checked)} className="accent-navy" />
                    Ẩn dòng nhóm
                  </label>
                </div>
              </div>
              <div className="min-h-0 flex-1 overflow-auto">
                <table className="w-full border-collapse text-[11.5px]">
                  <thead className="sticky top-0 z-10 bg-steel-50 text-steel-400">
                    <tr className="text-left text-[11px] font-bold uppercase tracking-wide">
                      <th rowSpan={2} className="w-[54px] border-b border-steel-200 px-2 py-2">TK</th>
                      <th rowSpan={2} className="w-full border-b border-steel-200 px-2 py-2 text-left">Tên tài khoản</th>
                      <th colSpan={2} className="border-b border-l border-steel-200 px-2 py-1.5 text-center">Dư đầu</th>
                      <th colSpan={2} className="border-b border-l border-steel-200 px-2 py-1.5 text-center">Phát sinh</th>
                      <th colSpan={2} className="border-b border-l border-steel-200 px-2 py-1.5 text-center">Dư cuối</th>
                    </tr>
                    <tr className="text-right text-[10.5px]">
                      {["Nợ", "Có", "Nợ", "Có", "Nợ", "Có"].map((h, i) => (
                        <th key={i} className={cx("border-b border-steel-200 px-2 py-1", i % 2 === 0 && "border-l")}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dongLoc.length === 0 && <tr><td colSpan={8} className="px-3 py-8 text-center text-steel-400">Không có dòng khớp.</td></tr>}
                    {dongLoc.map((d, i) => {
                      const nhom = d.is_group === 1 || d.is_group === true;
                      return (
                        <tr key={`${d.account}-${i}`} className={cx("border-b border-steel-100", nhom && "bg-steel-50 font-semibold")}>
                          <td className="px-2 py-1.5 font-bold tabular-nums text-steel-700">{d.account}</td>
                          <td className="break-words px-2 py-1.5 leading-snug" style={{ paddingLeft: `${8 + Math.max(0, d.level) * 10}px` }}>{d.ten}</td>
                          <td className="whitespace-nowrap border-l border-steel-100 px-2 py-1.5 text-right tabular-nums">{n0(d.du_dau_no)}</td>
                          <td className="whitespace-nowrap px-2 py-1.5 text-right tabular-nums">{n0(d.du_dau_co)}</td>
                          <td className="whitespace-nowrap border-l border-steel-100 px-2 py-1.5 text-right tabular-nums">{n0(d.ps_no)}</td>
                          <td className="whitespace-nowrap px-2 py-1.5 text-right tabular-nums">{n0(d.ps_co)}</td>
                          <td className="whitespace-nowrap border-l border-steel-100 px-2 py-1.5 text-right tabular-nums">{n0(d.du_cuoi_no)}</td>
                          <td className="whitespace-nowrap px-2 py-1.5 text-right tabular-nums">{n0(d.du_cuoi_co)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
