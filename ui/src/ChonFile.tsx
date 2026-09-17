/** Màn "Kiểm tra khóa sổ" — trải rộng 2 cột: Bước 1 Cân đối phát sinh (CĐPS, bắt buộc)
 * | Bước 2 Bảng kê chứng từ + Kiểm tra (chặn cứng nếu còn chi nhánh thiếu CĐPS). */
import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi, type ThongTinNap } from "./api";
import { cx, fso, Icon, IC, Modal, Nut, useToast } from "./ui";

interface TrangThaiCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string; thoi_diem_nap?: string }
interface ThieuCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string }
/** CĐPS nạp lại KHÁC bản đang lưu — nạp lại là ghi đè sạch nên phải báo trước. */
/** Kỳ đã có trong kho — phải hỏi trước khi đè, vì nạp lại là thay sạch cả kỳ. */
interface TrungCdps {
  chi_nhanh: string; chi_nhanh_ten?: string; ky: string; file: string;
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
  const [dangNapCdps, setDangNapCdps] = useState(false);
  const [doi, setDoi] = useState<ThayDoiCdps[]>([]);
  const [hoi, setHoi] = useState<{ path: string; moi: TrungCdps[]; trung: TrungCdps[] } | null>(null);
  const dangChay = !!tienTrinh;

  const taiTs = useCallback(async () => {
    const r = await A.goi("trang_thai_cdps");
    if (Array.isArray(r)) setTs(r as TrangThaiCdps[]);
  }, []);
  useEffect(() => { taiTs(); }, [taiTs]);

  useEffect(() => {
    if (!nap || nap.loi) { setThieu([]); return; }
    A.goi("thieu_cdps").then((r) => { if (Array.isArray(r)) setThieu(r as ThieuCdps[]); });
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
    setHoi({ path, moi, trung });
  };

  const chayNap = async (path: string, ghiDe: boolean) => {
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
        <p className="mt-0.5 text-[13px] text-steel-500">Nạp <b>Cân đối phát sinh</b> (bắt buộc) → nạp <b>Bảng kê chứng từ</b> → chạy kiểm tra.</p>
      </div>

      <div className="grid flex-1 items-start gap-4 lg:grid-cols-2">
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

        {/* ------------------------------ BƯỚC 2 ------------------------------ */}
        <section className={cx("relative flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-5 shadow-card",
          !coCdps && "opacity-60")}>
          <DauBuoc n={2} tieuDe="Bảng kê chứng từ" phu="Chọn file bảng kê rồi chạy kiểm tra" />

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

          <Nut bien="chinh" disabled={!nap || !!nap.loi || dangChay || thieu.length > 0} onClick={p.onKiemTra} className="justify-center py-3 text-[14px]">
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
      {/* Xác nhận trước khi ĐÈ: nạp lại thay sạch cả kỳ, mất số liệu cũ. */}
      <Modal mo={!!hoi} dong={() => setHoi(null)} tieuDe="Có kỳ đã nạp trước đó" rong>
        {hoi && (
          <div className="space-y-3 text-[13px]">
            <p className="text-steel-600">
              Nạp lại sẽ <b>thay sạch</b> số liệu của kỳ đó trong kho. Chọn cách xử lý:
            </p>
            {hoi.moi.length > 0 && (
              <div className="rounded-xl border border-steel-200 bg-steel-50 px-3 py-2">
                <b>{hoi.moi.length}</b> kỳ/chi nhánh <b>chưa có</b> trong kho — sẽ nạp mới:{" "}
                <span className="text-steel-500">
                  {hoi.moi.map((m) => `${m.chi_nhanh_ten || m.chi_nhanh} ${m.ky}`).join(" · ")}
                </span>
              </div>
            )}
            <div className="max-h-[38vh] overflow-auto rounded-xl border border-steel-200">
              <table className="w-full text-[12.5px]">
                <thead className="sticky top-0 bg-steel-50 text-[11px] font-bold uppercase tracking-wide text-steel-400">
                  <tr>
                    <th className="px-3 py-2 text-left">Chi nhánh</th>
                    <th className="px-3 py-2 text-left">Kỳ</th>
                    <th className="px-3 py-2 text-left">So với bản trong kho</th>
                  </tr>
                </thead>
                <tbody>
                  {hoi.trung.map((t) => (
                    <tr key={t.chi_nhanh + t.ky} className="border-t border-steel-100">
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
            <div className="flex flex-wrap justify-end gap-2 pt-1">
              <Nut bien="phu" onClick={() => setHoi(null)}>Hủy</Nut>
              {/* Không có kỳ nào mới thì nút này trùng nghĩa với Hủy — ẩn đi. */}
              {hoi.moi.length > 0 && (
                <Nut bien="phu" onClick={() => chayNap(hoi.path, false)}>
                  Chỉ nạp {hoi.moi.length} kỳ mới, giữ nguyên kỳ đã có
                </Nut>
              )}
              <Nut bien="chinh" onClick={() => chayNap(hoi.path, true)}>
                <Icon d={IC.warn} className="h-4 w-4" />Ghi đè {hoi.trung.length} kỳ đã có
              </Nut>
            </div>
          </div>
        )}
      </Modal>
    </div>

  );
}
