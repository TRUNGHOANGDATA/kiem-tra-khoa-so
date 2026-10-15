/** Màn "Kiểm tra khóa sổ" — 2 cột: (Bước 1 CĐPS + Bước 2 Sổ chi tiết bán hàng) | Bước 3
 * Bảng kê chứng từ + Kiểm tra. Chặn cứng khi còn chi nhánh thiếu CĐPS, hoặc có bán hàng /
 * trả lại mà thiếu sổ bán hàng (C3.2/C3.4 cần thuế từng dòng hàng). */
import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi, type KetQuaNapSbh, type KyTrongKho, type NguonKho, type ThongTinNap } from "./api";
import { cx, fso, Icon, IC, Modal, Nut, useToast } from "./ui";

interface TrangThaiCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string; thoi_diem_nap?: string }
interface ThieuCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string }
interface CdpsCu extends ThieuCdps { nap_cdps: string; xuat_bang_ke: string }
/** CĐPS nạp lại KHÁC bản đang lưu — nạp lại là ghi đè sạch nên phải báo trước. */
/** Kỳ đã có trong kho — phải hỏi trước khi đè, vì nạp lại là thay sạch cả kỳ. */
interface TrungCdps {
  chi_nhanh: string; chi_nhanh_ten?: string; ky: string; file: string; khoa: string;
  khac: boolean; so_doi: number; so_them: number; so_bot: number;
}
interface ThayDoiCdps {
  chi_nhanh: string; chi_nhanh_ten?: string; ky: string;
  so_doi: number; so_them: number; so_bot: number;
  dong: { account: string; kieu: string; cot: string }[];
}

export interface ChonFileProps {
  nap?: ThongTinNap;
  tienTrinh?: { ten: string; pct: number } | null;
  onChonFile: () => void;
  onChonNhieu: () => void;
  onQuet: () => void;
  onKiemTra: () => void;
  /** Dựng chi nhánh từ bảng kê ĐÃ LƯU trong kho (không cần chọn lại file). */
  onNapTuKho: (khoa: string[]) => void;
  /** Gỡ thanh tiến trình sau một việc chạy nền không đi qua App (nạp sổ bán hàng). */
  xoaTienTrinh: () => void;
}

function DauBuoc({ n, tieuDe, phu, xong }: { n: number; tieuDe: string; phu: string; xong?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <span className={cx("grid h-9 w-9 shrink-0 place-items-center rounded-full text-[14px] font-extrabold",
        xong ? "bg-xanh text-white" : "bg-navy text-white")}>
        {xong ? "✓" : n}
      </span>
      <div>
        <div className="text-[15px] font-bold text-ink">{tieuDe}</div>
        <div className="text-[12.5px] text-steel-500">{phu}</div>
      </div>
    </div>
  );
}

function CanhBaoNgoaiKy({ nap }: { nap: ThongTinNap }) {
  const tong = (nap.don_vi ?? []).reduce((s, d) => s + (d.ngoai_ky ?? 0), 0);
  if (!tong) return null;
  const gom = new Map<string, number>();
  (nap.don_vi ?? []).forEach((d) => (d.ngoai_ky_ct ?? []).forEach(([k, v]) => gom.set(k, (gom.get(k) ?? 0) + v)));
  const ct = [...gom.entries()].sort((a, b) => b[1] - a[1]).map(([k, v]) => `${fso(v)}× ${k}`).join(" · ");
  return (
    <div className="flex items-start gap-2 rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] leading-snug text-vang-dam">
      <Icon d={IC.warn} className="mt-0.5 h-4 w-4 shrink-0 text-vang" />
      <span><b className="tabular-nums">{fso(tong)}</b> dòng có ngày NGOÀI kỳ {nap.ky}: {ct} — kiểm tra lại có nạp nhầm file / sai khoảng xuất không.</span>
    </div>
  );
}

export default function ManChonFile(p: ChonFileProps) {
  const { nap, tienTrinh } = p;
  const toast = useToast();
  const [keo, setKeo] = useState(false);
  const [ts, setTs] = useState<TrangThaiCdps[]>([]);
  const [thieu, setThieu] = useState<ThieuCdps[]>([]);
  const [cu, setCu] = useState<CdpsCu[]>([]);
  const [dangNapCdps, setDangNapCdps] = useState(false);
  const [doi, setDoi] = useState<ThayDoiCdps[]>([]);
  const [hoi, setHoi] = useState<{ path: string; moi: TrungCdps[]; trung: TrungCdps[] } | null>(null);
  const [tick, setTick] = useState<Set<string>>(new Set());   // khóa các kỳ được chọn đè
  const [tsSbh, setTsSbh] = useState<NguonKho[]>([]);
  const [thieuSbh, setThieuSbh] = useState<ThieuCdps[]>([]);
  const [khongCanSbh, setKhongCanSbh] = useState<string[]>([]);
  const [dangNapSbh, setDangNapSbh] = useState(false);
  const [kqSbh, setKqSbh] = useState<KetQuaNapSbh | null>(null);
  const [khoKy, setKhoKy] = useState<KyTrongKho[] | null>(null);   // modal "Kiểm tra lại từ kho"
  const [chonKho, setChonKho] = useState<Set<string>>(new Set());
  const dangChay = !!tienTrinh;

  const taiTs = useCallback(async () => {
    const r = await A.goi("trang_thai_cdps");
    if (Array.isArray(r)) setTs(r as TrangThaiCdps[]);
  }, []);
  useEffect(() => { taiTs(); }, [taiTs]);
  const taiTsSbh = useCallback(async () => {
    const r = await A.goi("trang_thai_so_ban_hang");
    if (Array.isArray(r)) setTsSbh(r);
  }, []);
  useEffect(() => { taiTsSbh(); }, [taiTsSbh]);

  const taiThieuSbh = useCallback(() => {
    if (!nap || nap.loi) { setThieuSbh([]); setKhongCanSbh([]); return; }
    A.goi("thieu_so_ban_hang").then((r) => { if (Array.isArray(r)) setThieuSbh(r); });
    A.goi("khong_can_so_ban_hang").then((r) => { if (Array.isArray(r)) setKhongCanSbh(r); });
  }, [nap]);
  useEffect(() => { taiThieuSbh(); }, [taiThieuSbh]);

  // Sổ bán hàng: chọn thư mục -> nạp hết (thay sạch từng kỳ; kết quả nói rõ mới/đổi/giống).
  const napSbh = async () => {
    const r0 = await A.goi("chon_thu_muc", "");
    if (laLoi(r0)) { toast(r0.loi); return; }
    if (!r0 || (r0 as { huy?: boolean }).huy) return;
    setDangNapSbh(true);
    const r = await A.goi("nap_so_ban_hang_thu_muc", (r0 as { path: string }).path);
    setDangNapSbh(false);
    p.xoaTienTrinh();
    if (laLoi(r)) { toast(r.loi); return; }
    setKqSbh(r);
    toast(r.nap.length
      ? `Đã nạp sổ bán hàng ${r.nap.length} kỳ/chi nhánh${r.bo_qua.length ? ` · bỏ qua ${r.bo_qua.length} file` : ""}`
      : `Không thấy sổ bán hàng hợp lệ (tên “So chi tiet ban hang A01 092026 …”). Bỏ qua ${r.bo_qua.length} file.`);
    setTsSbh(r.trang_thai);
    taiThieuSbh();
  };

  const moKhoKy = async () => {
    const r = await A.goi("ky_trong_kho");
    if (!Array.isArray(r) || !r.length) { toast("Kho chưa có bảng kê nào — nạp file bảng kê một lần trước."); return; }
    setChonKho(new Set()); setKhoKy(r);
  };

  useEffect(() => {
    if (!nap || nap.loi) { setThieu([]); setCu([]); return; }
    A.goi("thieu_cdps").then((r) => { if (Array.isArray(r)) setThieu(r as ThieuCdps[]); });
    A.goi("cdps_cu").then((r) => { if (Array.isArray(r)) setCu(r as CdpsCu[]); });
  }, [nap]);

  // Chọn thư mục -> XEM TRƯỚC (chỉ đọc). Có kỳ trùng thì hỏi, không thì nạp luôn.
  const napCdps = async () => {
    const r0 = await A.goi("chon_thu_muc", "");
    if (laLoi(r0)) { toast(r0.loi); return; }
    if (!r0 || (r0 as { huy?: boolean }).huy) return;
    const path = (r0 as { path: string }).path;
    setDangNapCdps(true);
    const xt = await A.goi("xem_truoc_cdps", path);
    setDangNapCdps(false);
    if (laLoi(xt)) { toast(xt.loi); return; }
    const moi = (xt.moi as TrungCdps[]) ?? [];
    const trung = (xt.trung as TrungCdps[]) ?? [];
    const bq = (xt.bo_qua as unknown[])?.length ?? 0;
    if (!moi.length && !trung.length) {
      toast(`Không thấy file CĐPS đúng quy ước (vd “A08 082026 …”) trong thư mục. Bỏ qua ${bq} file.`);
      return;
    }
    if (!trung.length) { chayNap(path, false); return; }
    // Mặc định tick sẵn những kỳ THỰC SỰ KHÁC — đè kỳ giống hệt thì vô nghĩa.
    setTick(new Set(trung.filter((t) => t.khac).map((t) => t.khoa)));
    setHoi({ path, moi, trung });
  };

  const chayNap = async (path: string, ghiDe: boolean | string[]) => {
    setHoi(null);
    setDangNapCdps(true);
    const r = await A.goi("nap_cdps_thu_muc", path, ghiDe);
    setDangNapCdps(false);
    if (laLoi(r)) { toast(r.loi); return; }
    setDoi((r.thay_doi as ThayDoiCdps[]) ?? []);
    const nn = (r.nap as { chi_nhanh: string }[]) ?? [];
    const bqt = ((r.bo_qua_trung as unknown[]) ?? []).length;
    toast(nn.length
      ? `Đã nạp CĐPS ${nn.length} kỳ/chi nhánh${bqt ? ` · giữ nguyên ${bqt} kỳ đã có` : ""}`
      : `Không nạp kỳ nào — ${bqt} kỳ đã có trong kho được giữ nguyên.`);
    taiTs();
  };

  const coCdps = ts.length > 0;
  const dv = nap?.don_vi ?? [];
  const ky = nap?.ky ?? "";
  const thieuSet = new Set(thieu.map((t) => t.chi_nhanh));

  return (
    <div className="flex w-full flex-1 flex-col gap-4 overflow-auto p-5">
      <div>
        <h1 className="text-[20px] font-extrabold text-ink">Kiểm tra khóa sổ</h1>
        <p className="mt-0.5 text-[13px] text-steel-500">Nạp <b>Cân đối phát sinh</b> → <b>Sổ chi tiết bán hàng</b> → <b>Bảng kê chứng từ</b> → chạy kiểm tra. Cả ba được lưu vào kho.</p>
      </div>

      <div className="grid flex-1 items-start gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4">
        {/* ------------------------------ BƯỚC 1 ------------------------------ */}
        <section className="flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-5 shadow-card">
          <DauBuoc n={1} tieuDe="Cân đối phát sinh (CĐPS)" phu="Bắt buộc — để C7.6 trừ lỗ lũy kế" xong={coCdps} />

          <div className={cx("rounded-xl px-3 py-2.5 text-[12.5px]", coCdps ? "bg-xanh-nen text-xanh-dam" : "bg-vang-nen text-vang-dam")}>
            {coCdps
              ? <>Đã có CĐPS cho <b>{ts.length}</b> kỳ/chi nhánh trong kho — có thể sang Bước 2 luôn.</>
              : <>Chưa có CĐPS nào. Nạp trước khi kiểm tra (mỗi chi nhánh 1 file, tên “A08 082026 …”).</>}
          </div>

          <Nut bien={coCdps ? "phu" : "chinh"} onClick={napCdps} disabled={dangNapCdps} className="justify-center">
            <Icon d={IC.thu_muc} className="h-4 w-4" />{dangNapCdps ? "Đang nạp…" : coCdps ? "Nạp thêm / nạp lại CĐPS" : "Nạp CĐPS (chọn thư mục)"}
          </Nut>

          {doi.length > 0 && (
            <div className="rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] text-vang-dam">
              <div className="flex items-center gap-2 font-bold">
                <Icon d={IC.warn} className="h-4 w-4 shrink-0" />
                CĐPS vừa nạp KHÁC bản đang lưu ở {doi.length} kỳ/chi nhánh
              </div>
              <div className="mt-1.5 space-y-1.5">
                {doi.map((d) => (
                  <div key={d.chi_nhanh + d.ky}>
                    <b>{d.chi_nhanh_ten || d.chi_nhanh}</b> · kỳ {d.ky} —
                    {d.so_doi > 0 && <> {d.so_doi} TK đổi số</>}
                    {d.so_them > 0 && <> · thêm {d.so_them} TK</>}
                    {d.so_bot > 0 && <> · mất {d.so_bot} TK</>}
                    <div className="text-[11.5px] text-steel-500">
                      {d.dong.slice(0, 6).map((r) => `${r.account} (${r.kieu}${r.cot ? ": " + r.cot : ""})`).join(" · ")}
                      {d.dong.length > 6 && ` … +${d.dong.length - 6}`}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-1.5">Số liệu cũ đã bị thay. Kiểm tra lại kết quả của các kỳ này.</div>
            </div>
          )}

          {coCdps && (
            <div className="max-h-[220px] overflow-auto rounded-xl border border-steel-200">
              <table className="w-full text-[12.5px]">
                <thead className="sticky top-0 bg-steel-50 text-[11px] font-bold uppercase tracking-wide text-steel-400">
                  <tr><th className="px-3 py-2 text-left">Chi nhánh</th><th className="px-3 py-2 text-left">Kỳ</th></tr>
                </thead>
                <tbody>
                  {ts.map((t) => (
                    <tr key={`${t.chi_nhanh}|${t.ky}`} className="border-t border-steel-100">
                      <td className="px-3 py-1.5 font-semibold">{t.chi_nhanh_ten || t.chi_nhanh}</td>
                      <td className="px-3 py-1.5 tabular-nums text-steel-500">{t.ky}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ------------------------- BƯỚC 2 · SỔ BÁN HÀNG ------------------------- */}
        <section className="flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-5 shadow-card">
          <DauBuoc n={2} tieuDe="Sổ chi tiết bán hàng" xong={tsSbh.length > 0}
            phu="Bắt buộc khi kỳ có bán hàng / trả lại — soát thuế GTGT từng dòng hàng (C3.2, C3.4)" />
          <div className={cx("rounded-xl px-3 py-2.5 text-[12.5px]", tsSbh.length ? "bg-xanh-nen text-xanh-dam" : "bg-vang-nen text-vang-dam")}>
            {tsSbh.length
              ? <>Đã có sổ bán hàng cho <b>{tsSbh.length}</b> kỳ/chi nhánh trong kho.</>
              : <>Chưa có sổ bán hàng nào. Mỗi chi nhánh 1 file, tên “So chi tiet ban hang A01 092026”, xuất <b>cùng lúc</b> với bảng kê.</>}
          </div>
          <Nut bien={tsSbh.length ? "phu" : "chinh"} onClick={napSbh} disabled={dangNapSbh} className="justify-center">
            <Icon d={IC.thu_muc} className="h-4 w-4" />{dangNapSbh ? "Đang nạp…" : tsSbh.length ? "Nạp thêm / nạp lại sổ bán hàng" : "Nạp sổ bán hàng (chọn thư mục)"}
          </Nut>
          {kqSbh && (kqSbh.nap.some((x) => x.ket_qua === "doi") || kqSbh.bo_qua.length > 0) && (
            <div className="rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] text-vang-dam">
              {kqSbh.nap.filter((x) => x.ket_qua === "doi").map((x) => (
                <div key={x.chi_nhanh + x.ky}>▲ <b>{x.chi_nhanh_ten || x.chi_nhanh}</b> · {x.ky}: KHÁC bản cũ trong kho — đã thay.</div>
              ))}
              {kqSbh.bo_qua.map((x) => <div key={x.file}>– Bỏ qua <b>{x.file}</b>: {x.ly_do}</div>)}
            </div>
          )}
          {tsSbh.length > 0 && (
            <div className="max-h-[200px] overflow-auto rounded-xl border border-steel-200">
              <table className="w-full text-[12.5px]">
                <thead className="sticky top-0 bg-steel-50 text-[11px] font-bold uppercase tracking-wide text-steel-400">
                  <tr><th className="px-3 py-2 text-left">Chi nhánh</th><th className="px-3 py-2 text-left">Kỳ</th><th className="px-3 py-2 text-right">Số dòng</th></tr>
                </thead>
                <tbody>
                  {tsSbh.map((t) => (
                    <tr key={`${t.chi_nhanh}|${t.ky}`} className="border-t border-steel-100">
                      <td className="px-3 py-1.5 font-semibold">{t.chi_nhanh_ten || t.chi_nhanh}</td>
                      <td className="px-3 py-1.5 tabular-nums text-steel-500">{t.ky}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums text-steel-500">{fso(t.so_dong)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        </div>

        {/* ------------------------------ BƯỚC 3 ------------------------------ */}
        <section className={cx("relative flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-5 shadow-card",
          !coCdps && "opacity-60")}>
          <DauBuoc n={3} tieuDe="Bảng kê chứng từ" phu="Chọn file bảng kê (tự lưu vào kho) rồi chạy kiểm tra" />

          {!coCdps && (
            <div className="absolute inset-0 z-20 grid place-items-center rounded-2xl bg-white/40">
              <span className="rounded-xl bg-muc px-4 py-2 text-[12.5px] font-semibold text-white shadow-pop">Nạp CĐPS ở Bước 1 trước</span>
            </div>
          )}

          <div
            onDragEnter={(e) => { e.preventDefault(); setKeo(true); }}
            onDragOver={(e) => { e.preventDefault(); setKeo(true); }}
            onDragLeave={() => setKeo(false)}
            onDrop={(e) => { e.preventDefault(); setKeo(false); }}
            className={cx("flex flex-col items-center gap-2.5 rounded-xl border-2 border-dashed px-6 py-7 text-center transition",
              keo ? "border-navy bg-navy/5" : "border-steel-300 bg-steel-50/40")}
          >
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-steel-100 text-navy"><Icon d={IC.tai_len} className="h-6 w-6" /></span>
            <p className="text-[14px] font-semibold text-ink">Chọn file bảng kê chứng từ (.xlsx)</p>
            <p className="-mt-1 text-[12.5px] text-steel-500">nhiều chi nhánh thì chọn nhiều file cùng lúc</p>
            <div className="mt-1 flex flex-wrap justify-center gap-2">
              <Nut bien="phu" onClick={p.onChonFile}><Icon d={IC.file} className="h-4 w-4" />Chọn file…</Nut>
              <Nut bien="phu" onClick={p.onChonNhieu}><Icon d={IC.file} className="h-4 w-4" />Chọn nhiều file</Nut>
              <Nut bien="phu" onClick={p.onQuet}><Icon d={IC.thu_muc} className="h-4 w-4" />Nạp cả thư mục</Nut>
              <Nut bien="phu" onClick={moKhoKy}><Icon d={IC.lam_moi} className="h-4 w-4" />Kiểm tra lại từ kho…</Nut>
            </div>
          </div>

          {nap && !nap.loi && (
            <>
              <div className="flex items-center gap-3 rounded-xl border border-steel-200 bg-steel-50 px-3 py-2.5">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-navy shadow-soft"><Icon d={IC.file} className="h-4 w-4" /></span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13px] font-bold text-ink">{nap.ten}</div>
                  <div className="text-[11.5px] text-steel-500">Kỳ {nap.ky} · <span className="tabular-nums">{fso(nap.so_dong)}</span> dòng · PS <span className="tabular-nums">{fso(nap.tong_ps)}</span></div>
                </div>
              </div>
              {dv.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {dv.map((d) => {
                    const co = !thieuSet.has(d.ma);
                    return (
                      <span key={d.ma}
                        className={cx("inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-semibold",
                          co ? "bg-xanh-nen text-xanh-dam" : "bg-do-nen text-do-dam")}>
                        <Icon d={co ? IC.checkNho : IC.x} className="h-3.5 w-3.5" />{d.ten_hien || d.ma} · {co ? "có CĐPS" : "thiếu CĐPS"}
                      </span>
                    );
                  })}
                </div>
              )}
              {dv.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {dv.map((d) => {
                    const khongCan = khongCanSbh.includes(d.ma);
                    const thieuD = thieuSbh.some((t) => t.chi_nhanh === d.ma);
                    return (
                      <span key={d.ma}
                        className={cx("inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-semibold",
                          khongCan ? "bg-steel-100 text-steel-500" : thieuD ? "bg-do-nen text-do-dam" : "bg-xanh-nen text-xanh-dam")}>
                        {khongCan ? "–" : thieuD ? "✕" : "✓"} {d.ten_hien || d.ma} · {khongCan ? "không cần sổ bán hàng" : thieuD ? "thiếu sổ bán hàng" : "có sổ bán hàng"}
                      </span>
                    );
                  })}
                </div>
              )}
              {nap.loi_kho && <div className="rounded-xl border border-vang-vien bg-vang-nen px-3 py-2 text-[12.5px] text-vang-dam">▲ {nap.loi_kho}</div>}
              <CanhBaoNgoaiKy nap={nap} />
            </>
          )}
          {nap?.loi && <div className="rounded-xl border border-do-vien bg-do-nen px-4 py-3 text-[13px] font-medium text-do-dam">{nap.loi}</div>}

          {nap && !nap.loi && thieu.length > 0 && (
            <div className="flex items-start gap-2 rounded-xl border border-do-vien bg-do-nen px-3 py-2.5 text-[12.5px] leading-snug text-do-dam">
              <Icon d={IC.x} className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Còn <b>{thieu.length}</b> chi nhánh chưa có CĐPS ({thieu.map((t) => t.chi_nhanh_ten || t.chi_nhanh).join(", ")}) — nạp CĐPS ở Bước 1 rồi mới Kiểm tra.</span>
            </div>
          )}

          {nap && !nap.loi && thieuSbh.length > 0 && (
            <div className="flex items-start gap-2 rounded-xl border border-do-vien bg-do-nen px-3 py-2.5 text-[12.5px] leading-snug text-do-dam">
              <Icon d={IC.x} className="mt-0.5 h-4 w-4 shrink-0" />
              <span>Còn <b>{thieuSbh.length}</b> chi nhánh có bán hàng/trả lại mà chưa có sổ chi tiết bán hàng ({thieuSbh.map((t) => `${t.chi_nhanh_ten || t.chi_nhanh} ${t.ky}`).join(", ")}) — nạp ở Bước 2 rồi mới Kiểm tra.</span>
            </div>
          )}

          {/* CĐPS cũ hơn bảng kê: CẢNH BÁO, không chặn — vẫn kiểm tra được, chỉ là các
              con số đối chiếu hai nguồn (C9.5) chưa đáng tin. Đã dính thật 21/09: CĐPS
              nạp 17/09 vs bảng kê xuất 21/09 làm C9.5 nổ giả ở 7/8 chi nhánh. */}
          {nap && !nap.loi && cu.length > 0 && (
            <div className="flex items-start gap-2 rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] leading-snug text-vang-dam">
              <Icon d={IC.warn} className="mt-0.5 h-4 w-4 shrink-0 text-vang" />
              <span>
                <b>{cu.length}</b> chi nhánh có CĐPS <b>cũ hơn</b> bảng kê — đối chiếu bảng kê ↔ CĐPS (C9.5)
                chưa đáng tin cho tới khi nạp lại CĐPS:{" "}
                {cu.map((c) => `${c.chi_nhanh_ten || c.chi_nhanh} (CĐPS ${c.nap_cdps} · bảng kê ${c.xuat_bang_ke})`).join(" · ")}
              </span>
            </div>
          )}

          <Nut bien="chinh" disabled={!nap || !!nap.loi || dangChay || thieu.length > 0 || thieuSbh.length > 0} onClick={p.onKiemTra} className="justify-center py-3 text-[14px]">
            <Icon d={IC.soKiemTra} className="h-4 w-4" />Kiểm tra
          </Nut>

          {tienTrinh && (
            <div className="rounded-xl border border-steel-200 bg-white p-3 shadow-soft">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[13px] font-medium text-ink">{tienTrinh.ten}</span>
                <span className="text-[13px] font-bold tabular-nums text-navy">{tienTrinh.pct > 0 ? `${tienTrinh.pct}%` : ""}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-steel-100">
                <div className={cx("h-full rounded-full bg-gradient-to-r from-navy to-navy-400 transition-all", tienTrinh.pct <= 0 && "w-1/3 animate-pulse")}
                  style={tienTrinh.pct > 0 ? { width: `${tienTrinh.pct}%` } : undefined} />
              </div>
            </div>
          )}
        </section>
      </div>
      {/* Kiểm tra lại từ kho: chọn (chi nhánh × kỳ) đã lưu bảng kê, khỏi chọn lại file. */}
      <Modal mo={!!khoKy} dong={() => setKhoKy(null)} tieuDe="Kiểm tra lại từ kho" rong>
        {khoKy && (
          <div className="space-y-3 text-[13px]">
            <p className="text-steel-600">Chọn kỳ/chi nhánh có bảng kê đã lưu. Dữ liệu là bản <b>lần nạp gần nhất</b> — muốn số mới thì nạp lại file.</p>
            <div className="max-h-[45vh] overflow-auto rounded-xl border border-steel-200">
              <table className="w-full text-[12.5px]">
                <thead className="sticky top-0 bg-steel-50 text-[11px] font-bold uppercase tracking-wide text-steel-400">
                  <tr><th className="w-9 px-3 py-2" /><th className="px-3 py-2 text-left">Chi nhánh</th><th className="px-3 py-2 text-left">Kỳ</th>
                    <th className="px-3 py-2 text-right">Số dòng</th><th className="px-3 py-2 text-left">Nạp lúc</th>
                    <th className="px-3 py-2 text-left">CĐPS</th><th className="px-3 py-2 text-left">Sổ bán hàng</th></tr>
                </thead>
                <tbody>
                  {khoKy.map((k) => {
                    const chon = chonKho.has(k.khoa);
                    const doi = () => setChonKho((cu) => { const s2 = new Set(cu); if (chon) s2.delete(k.khoa); else s2.add(k.khoa); return s2; });
                    return (
                      <tr key={k.khoa} onClick={doi} className={cx("cursor-pointer border-t border-steel-100 hover:bg-steel-50", chon && "bg-navy/5")}>
                        <td className="px-3 py-1.5 text-center"><input type="checkbox" className="accent-navy" checked={chon} onChange={doi} onClick={(e) => e.stopPropagation()} /></td>
                        <td className="px-3 py-1.5 font-semibold">{k.chi_nhanh_ten || k.chi_nhanh}</td>
                        <td className="px-3 py-1.5 tabular-nums">{k.ky}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums">{fso(k.so_dong)}</td>
                        <td className="px-3 py-1.5 tabular-nums text-steel-500">{(k.thoi_diem_nap || "").replace("T", " ").slice(0, 16)}</td>
                        <td className="px-3 py-1.5">{k.co_cdps ? "✓ có" : "✕ thiếu"}</td>
                        <td className="px-3 py-1.5">{k.co_so_ban_hang ? "✓ có" : "– chưa có"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="flex justify-end gap-2">
              <Nut bien="phu" onClick={() => setKhoKy(null)}>Hủy</Nut>
              <Nut bien="chinh" disabled={!chonKho.size} onClick={() => { p.onNapTuKho([...chonKho]); setKhoKy(null); }}>
                Dùng {chonKho.size} kỳ đã chọn
              </Nut>
            </div>
          </div>
        )}
      </Modal>
      {/* Xác nhận trước khi ĐÈ: nạp lại thay sạch cả kỳ, mất số liệu cũ. */}
      <Modal mo={!!hoi} dong={() => setHoi(null)} tieuDe="Có kỳ đã nạp trước đó" rong>
        {hoi && (() => {
          const doiTick = (khoa: string) => setTick((cu) => {
            const s = new Set(cu); s.has(khoa) ? s.delete(khoa) : s.add(khoa); return s;
          });
          const tatCa = hoi.trung.every((t) => tick.has(t.khoa));
          const toggleTatCa = () => setTick(tatCa ? new Set() : new Set(hoi.trung.map((t) => t.khoa)));
          return (
          <div className="space-y-3 text-[13px]">
            <p className="text-steel-600">
              Nạp lại sẽ <b>thay sạch</b> số liệu của kỳ đó trong kho.
              Tick những kỳ muốn ghi đè (mặc định đã chọn sẵn các kỳ có thay đổi).
            </p>
            {hoi.moi.length > 0 && (
              <div className="rounded-xl border border-xanh-vien bg-xanh-nen px-3 py-2 text-xanh-dam">
                <b>{hoi.moi.length}</b> kỳ/chi nhánh <b>chưa có</b> trong kho — luôn nạp mới:{" "}
                {hoi.moi.map((m) => `${m.chi_nhanh_ten || m.chi_nhanh} ${m.ky}`).join(" · ")}
              </div>
            )}
            <div className="max-h-[38vh] overflow-auto rounded-xl border border-steel-200">
              <table className="w-full text-[12.5px]">
                <thead className="sticky top-0 bg-steel-50 text-[11px] font-bold uppercase tracking-wide text-steel-400">
                  <tr>
                    <th className="w-9 px-3 py-2 text-center">
                      <input type="checkbox" className="accent-navy" checked={tatCa} onChange={toggleTatCa} />
                    </th>
                    <th className="px-3 py-2 text-left">Chi nhánh</th>
                    <th className="px-3 py-2 text-left">Kỳ</th>
                    <th className="px-3 py-2 text-left">So với bản trong kho</th>
                  </tr>
                </thead>
                <tbody>
                  {hoi.trung.map((t) => (
                    <tr key={t.khoa} className={cx("border-t border-steel-100 cursor-pointer hover:bg-steel-50", tick.has(t.khoa) && "bg-vang-nen/40")}
                      onClick={() => doiTick(t.khoa)}>
                      <td className="px-3 py-1.5 text-center">
                        <input type="checkbox" className="accent-navy" checked={tick.has(t.khoa)}
                          onChange={() => doiTick(t.khoa)} onClick={(e) => e.stopPropagation()} />
                      </td>
                      <td className="px-3 py-1.5 font-semibold">{t.chi_nhanh_ten || t.chi_nhanh}</td>
                      <td className="px-3 py-1.5 tabular-nums">{t.ky}</td>
                      <td className="px-3 py-1.5">
                        {t.khac
                          ? <span className="font-semibold text-vang-dam">
                              ▲ Khác: {t.so_doi} TK đổi số
                              {t.so_them > 0 && ` · thêm ${t.so_them}`}
                              {t.so_bot > 0 && ` · mất ${t.so_bot}`}
                            </span>
                          : <span className="text-steel-500">✓ Giống hệt bản đang lưu</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[12px] text-steel-500">
                Đã chọn <b className="text-ink">{tick.size}</b>/{hoi.trung.length} kỳ để ghi đè
                {hoi.moi.length > 0 && ` · ${hoi.moi.length} kỳ mới`}
              </span>
              <div className="ml-auto flex gap-2">
                <Nut bien="phu" onClick={() => setHoi(null)}>Hủy</Nut>
                <Nut bien="chinh" disabled={tick.size === 0 && hoi.moi.length === 0}
                  onClick={() => chayNap(hoi.path, [...tick])}>
                  {tick.size > 0 && <Icon d={IC.warn} className="h-4 w-4" />}
                  {tick.size > 0
                    ? `Nạp ${hoi.moi.length + tick.size} kỳ (ghi đè ${tick.size})`
                    : hoi.moi.length > 0 ? `Chỉ nạp ${hoi.moi.length} kỳ mới` : "Không nạp gì"}
                </Nut>
              </div>
            </div>
          </div>
          );
        })()}
      </Modal>
    </div>

  );
}
