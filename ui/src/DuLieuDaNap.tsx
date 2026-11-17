/** Màn "Dữ liệu đã nạp" — 3 tab: CĐPS · Sổ bán hàng · Bảng kê. Chỉ ĐỌC những gì đang nằm
 * trong kho (nạp bản nào, lúc nào, từ file nào), lọc như KTTH vẫn lọc tay rồi xuất Excel. */
import { useCallback, useEffect, useMemo, useState } from "react";
import * as A from "./api";
import { laLoi, type LoaiNguon, type NguonKho, type XemNguon } from "./api";
import { cx, fso, Icon, IC, Nut, useToast } from "./ui";
import ManCanDoi from "./CanDoi";
import BangChiTiet from "./BangChiTiet";

type Tab = "cdps" | LoaiNguon;
const TAB: { id: Tab; nhan: string }[] = [
  { id: "cdps", nhan: "Cân đối phát sinh" },
  { id: "so_ban_hang", nhan: "Sổ bán hàng" },
  { id: "bang_ke", nhan: "Bảng kê" },
];

function BangNguon({ loai }: { loai: LoaiNguon }) {
  const toast = useToast();
  const [ts, setTs] = useState<NguonKho[]>([]);
  const [chon, setChon] = useState<NguonKho | null>(null);
  const [fKy, setFKy] = useState("all");
  const [fCn, setFCn] = useState("all");
  const [locNo, setLocNo] = useState("");
  const [locCo, setLocCo] = useState("");
  const [thue0, setThue0] = useState(false);
  const [loaiCt, setLoaiCt] = useState("");
  const [dau, setDau] = useState<XemNguon | null>(null);   // ô tổng + nguồn của trang vừa tải

  useEffect(() => {
    A.goi(loai === "bang_ke" ? "trang_thai_bang_ke" : "trang_thai_so_ban_hang")
      .then((r) => { if (Array.isArray(r)) setTs(r); });
  }, [loai]);

  const kyOpts = useMemo(() => [...new Set(ts.map((t) => t.ky))].sort().reverse(), [ts]);
  const cnOpts = useMemo(() => [...new Map(ts.map((t) => [t.chi_nhanh, t.chi_nhanh_ten || t.chi_nhanh])).entries()], [ts]);
  const loc = ts.filter((t) => (fKy === "all" || t.ky === fKy) && (fCn === "all" || t.chi_nhanh === fCn));

  // Đổi lọc danh sách mà dòng đang xem không còn trong đó -> bám theo lọc.
  useEffect(() => {
    if (chon && loc.some((t) => t.chi_nhanh === chon.chi_nhanh && t.ky === chon.ky)) return;
    setChon(loc[0] ?? null);
  }, [fKy, fCn, ts]);   // eslint-disable-line react-hooks/exhaustive-deps

  const nap = useCallback(async (trang: number, kt: number, tim: string) => {
    if (!chon) return { loi: "Chưa chọn kỳ/chi nhánh" };
    const r = await A.goi("xem_nguon", loai, chon.chi_nhanh, chon.ky_nam, chon.ky_thang, trang, kt, tim,
      locNo, locCo, thue0, loaiCt);
    if (!laLoi(r)) setDau(r);
    return r;
  }, [loai, chon, locNo, locCo, thue0, loaiCt]);

  const xuat = useCallback(async (tim: string) => {
    if (!chon) return;
    const r = await A.goi("xuat_nguon", loai, chon.chi_nhanh, chon.ky_nam, chon.ky_thang, tim,
      locNo, locCo, thue0, loaiCt);
    if (laLoi(r)) { toast(r.loi); return; }
    toast("Đã xuất Excel"); A.goi("mo_file", r.path);
  }, [loai, chon, locNo, locCo, thue0, loaiCt, toast]);

  // Doanh thu ≠ 0 mà thuế = 0: nhãn chữ trung tính, KHÔNG dùng ✕ (✕ là lỗi; thuế 0 có
  // thể là hàng tặng hay giao dịch chi nhánh).
  const nhanO = useCallback((row: Record<string, unknown>, c: string) =>
    loai === "so_ban_hang" && c === "Amount3" && row.Amount3 === 0 && row.Amount2 !== 0 && row.Amount2 != null
      ? "thuế 0" : undefined, [loai]);

  const khoaBang = chon ? `${chon.chi_nhanh}|${chon.ky}|${locNo}|${locCo}|${thue0}|${loaiCt}` : "";

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden">
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
        <aside className="flex w-[196px] shrink-0 flex-col gap-2 overflow-y-auto pr-1">
          {loc.length === 0 && <div className="rounded-xl bg-steel-50 px-3 py-4 text-center text-[12.5px] text-steel-400">Kho chưa có dữ liệu này.</div>}
          {loc.map((t) => (
            <button key={`${t.chi_nhanh}|${t.ky}`} onClick={() => setChon(t)}
              className={cx("rounded-xl border bg-white p-2.5 text-left shadow-soft transition",
                chon && chon.chi_nhanh === t.chi_nhanh && chon.ky === t.ky ? "border-navy ring-1 ring-navy/30" : "border-steel-200 hover:border-steel-300")}>
              <div className="flex items-center gap-2">
                <span className="min-w-0 truncate text-[13px] font-bold text-ink">{t.chi_nhanh_ten || t.chi_nhanh}</span>
                <span className="ml-auto shrink-0 rounded-md bg-steel-100 px-1.5 py-0.5 text-[11px] font-bold text-steel-600 tabular-nums">{t.ky}</span>
              </div>
              <div className="mt-1 text-[11px] text-steel-400 tabular-nums">{fso(t.so_dong)} dòng</div>
              {t.thoi_diem_nap && <div className="truncate text-[11px] text-steel-400">Nạp: {t.thoi_diem_nap.slice(0, 16).replace("T", " ")}</div>}
            </button>
          ))}
        </aside>

        <main className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-steel-200 bg-white p-4 shadow-card">
          {!chon ? (
            <div className="grid flex-1 place-items-center text-[13px] text-steel-400">Chọn một kỳ/chi nhánh bên trái.</div>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[13.5px] font-bold text-ink">{chon.chi_nhanh_ten || chon.chi_nhanh} · kỳ {chon.ky}</span>
                {dau?.nguon_file && (
                  <span className="truncate text-[12px] text-steel-500">
                    {dau.tu_gop ? <>tách từ file gộp <b>{dau.tu_gop}</b>: </> : "file: "}{dau.nguon_file}
                  </span>
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-[12.5px]">
                <input value={locNo} onChange={(e) => setLocNo(e.target.value.trim())} placeholder="TK Nợ (vd 131)"
                  className="w-32 rounded-lg border border-steel-200 px-2 py-1 outline-none focus:border-navy-400" />
                <input value={locCo} onChange={(e) => setLocCo(e.target.value.trim())} placeholder="TK Có (vd 511)"
                  className="w-32 rounded-lg border border-steel-200 px-2 py-1 outline-none focus:border-navy-400" />
                {loai === "bang_ke" && (
                  <select value={loaiCt} onChange={(e) => setLoaiCt(e.target.value)}
                    className="rounded-lg border border-steel-200 bg-white px-2 py-1 outline-none focus:border-navy-400">
                    <option value="">Mọi loại CT</option>
                    {(dau?.loai_ct ?? []).map((k) => <option key={k} value={k}>{k}</option>)}
                  </select>
                )}
                {loai === "so_ban_hang" && (
                  <label className="inline-flex items-center gap-1.5 text-steel-600">
                    <input type="checkbox" checked={thue0} onChange={(e) => setThue0(e.target.checked)} className="accent-navy" />
                    Chỉ dòng thuế = 0
                  </label>
                )}
                {(locNo || locCo || thue0 || loaiCt) && (
                  <Nut bien="phu" className="px-2 py-1" onClick={() => { setLocNo(""); setLocCo(""); setThue0(false); setLoaiCt(""); }}>
                    <Icon d={IC.x} className="h-3.5 w-3.5" />Bỏ lọc
                  </Nut>
                )}
              </div>
              {dau && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {dau.tong_hop.map((o) => (
                    <div key={o.nhan} className="rounded-lg border border-steel-200 bg-steel-50 px-2.5 py-1.5">
                      <div className="text-[10.5px] font-bold uppercase tracking-wide text-steel-400">{o.nhan}</div>
                      <div className="text-[13px] font-bold tabular-nums text-ink">{fso(o.gia_tri)}</div>
                    </div>
                  ))}
                  <div className="self-end text-[11.5px] text-steel-400">tính trên phần đang lọc · kho có {fso(dau.tong_kho)} dòng</div>
                </div>
              )}
              <div className="flex min-h-0 flex-1 flex-col">
                <BangChiTiet key={khoaBang} nap={nap} onXuat={xuat} nhanO={nhanO} />
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default function ManDuLieuDaNap({ onQuayLai }: { onQuayLai: () => void }) {
  const [tab, setTab] = useState<Tab>("cdps");
  return (
    <div className="flex w-full flex-1 flex-col gap-4 overflow-hidden p-5">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-[18px] font-extrabold text-ink">Dữ liệu đã nạp</h2>
        <div className="flex gap-1 rounded-xl bg-steel-100 p-1">
          {TAB.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={cx("rounded-lg px-3 py-1.5 text-[12.5px] font-semibold transition",
                tab === t.id ? "bg-white text-ink shadow-soft" : "text-steel-500 hover:text-ink")}>
              {t.nhan}
            </button>
          ))}
        </div>
        <span className="text-[12px] text-steel-400">chỉ đọc · muốn đổi thì nạp lại file</span>
        <Nut bien="phu" className="ml-auto" onClick={onQuayLai}><Icon d={IC.chevL} className="h-4 w-4" />Quay lại</Nut>
      </div>
      {tab === "cdps" ? <ManCanDoi nhung onQuayLai={onQuayLai} /> : <BangNguon key={tab} loai={tab} />}
    </div>
  );
}
