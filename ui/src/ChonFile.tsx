/** Màn 1 — nhập theo 2 BƯỚC: (1) Cân đối phát sinh (CĐPS, bắt buộc — bỏ qua được nếu đã
 * có trong kho) → (2) Bảng kê chứng từ + Kiểm tra (chặn cứng nếu còn chi nhánh thiếu CĐPS). */
import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi, type ThongTinNap } from "./api";
import { cx, fso, Icon, IC, Nut, useToast } from "./ui";

interface TrangThaiCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string; thoi_diem_nap?: string }
interface ThieuCdps { chi_nhanh: string; chi_nhanh_ten?: string; ky: string }

export interface ChonFileProps {
  nap?: ThongTinNap;
  tienTrinh?: { ten: string; pct: number } | null;
  onChonFile: () => void;
  onChonNhieu: () => void;
  onQuet: () => void;
  onKiemTra: () => void;
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

function ChiSoBuoc({ buoc }: { buoc: 1 | 2 }) {
  const B = [[1, "Cân đối phát sinh"], [2, "Bảng kê chứng từ"]] as const;
  return (
    <div className="flex items-center gap-2">
      {B.map(([n, ten], i) => (
        <div key={n} className="flex items-center gap-2">
          <span className={cx("grid h-6 w-6 place-items-center rounded-full text-[12px] font-bold",
            buoc === n ? "bg-navy text-white" : buoc > n ? "bg-xanh text-white" : "bg-steel-200 text-steel-500")}>
            {buoc > n ? "✓" : n}
          </span>
          <span className={cx("text-[12.5px] font-semibold", buoc >= n ? "text-ink" : "text-steel-400")}>Bước {n} · {ten}</span>
          {i === 0 && <span className="mx-1 h-px w-6 bg-steel-300" />}
        </div>
      ))}
    </div>
  );
}

export default function ManChonFile(p: ChonFileProps) {
  const { nap, tienTrinh } = p;
  const toast = useToast();
  const [keo, setKeo] = useState(false);
  const [buoc, setBuoc] = useState<1 | 2>(1);
  const [ts, setTs] = useState<TrangThaiCdps[]>([]);
  const [thieu, setThieu] = useState<ThieuCdps[]>([]);
  const [dangNapCdps, setDangNapCdps] = useState(false);
  const dangChay = !!tienTrinh;

  const taiTs = useCallback(async () => {
    const r = await A.goi("trang_thai_cdps");
    if (Array.isArray(r)) setTs(r as TrangThaiCdps[]);
  }, []);
  useEffect(() => { taiTs(); }, [taiTs]);

  // Bảng kê đổi -> tính chi nhánh còn thiếu CĐPS (để chặn Kiểm tra)
  useEffect(() => {
    if (!nap || nap.loi) { setThieu([]); return; }
    A.goi("thieu_cdps").then((r) => { if (Array.isArray(r)) setThieu(r as ThieuCdps[]); });
  }, [nap]);

  const napCdps = async () => {
    const r0 = await A.goi("chon_thu_muc", "");
    if (laLoi(r0)) { toast(r0.loi); return; }
    if (!r0 || (r0 as { huy?: boolean }).huy) return;
    setDangNapCdps(true);
    const r = await A.goi("nap_cdps_thu_muc", (r0 as { path: string }).path);
    setDangNapCdps(false);
    if (laLoi(r)) { toast(r.loi); return; }
    const nn = (r.nap as { chi_nhanh: string }[]) ?? [];
    const bq = (r.bo_qua as unknown[])?.length ?? 0;
    toast(nn.length
      ? `Đã nạp CĐPS ${nn.length} file: ${nn.map((x) => x.chi_nhanh).join(", ")}`
      : `Không thấy file CĐPS đúng quy ước (vd “A08 082026 …”) trong thư mục. Bỏ qua ${bq} file.`);
    taiTs();
  };

  const coCdps = ts.length > 0;
  const dv = nap?.don_vi ?? [];
  const ky = nap?.ky ?? "";
  const thieuSet = new Set(thieu.map((t) => t.chi_nhanh));

  return (
    <div className="flex flex-1 items-center justify-center overflow-auto p-8">
      <div className="flex w-full max-w-[560px] flex-col gap-4">
        <ChiSoBuoc buoc={buoc} />

        {/* ------------------------------ BƯỚC 1: CĐPS ------------------------------ */}
        {buoc === 1 && (
          <section className="flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-5 shadow-card">
            <div className="flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-steel-100 text-navy"><Icon d={IC.bar} className="h-5 w-5" /></span>
              <div>
                <div className="text-[15px] font-bold text-ink">Cân đối số phát sinh (CĐPS)</div>
                <div className="text-[12.5px] text-steel-500">Bắt buộc — để C7.6 trừ lỗ lũy kế. Mỗi chi nhánh 1 file, tên “A08 082026 …”.</div>
              </div>
            </div>

            <div className={cx("rounded-xl px-3 py-2.5 text-[12.5px]", coCdps ? "bg-xanh-nen text-xanh-dam" : "bg-vang-nen text-vang-dam")}>
              {coCdps
                ? <>Đã có CĐPS cho <b>{ts.length}</b> kỳ/chi nhánh trong kho — có thể bỏ qua bước nạp.</>
                : <>Chưa có CĐPS nào trong kho. Hãy nạp trước khi sang bước 2.</>}
            </div>

            <Nut bien="phu" onClick={napCdps} disabled={dangNapCdps} className="justify-center">
              <Icon d={IC.thu_muc} className="h-4 w-4" />{dangNapCdps ? "Đang nạp…" : "Nạp CĐPS (chọn thư mục)"}
            </Nut>

            <Nut bien="chinh" disabled={!coCdps} onClick={() => setBuoc(2)} className="justify-center py-3">
              {coCdps ? "Bỏ qua / Tiếp tục →" : "Cần nạp CĐPS để tiếp tục"}
            </Nut>
          </section>
        )}

        {/* ---------------------------- BƯỚC 2: BẢNG KÊ ---------------------------- */}
        {buoc === 2 && (
          <>
            <button onClick={() => setBuoc(1)} className="self-start text-[13px] font-semibold text-navy hover:underline">
              ← Quay lại bước 1 (CĐPS)
            </button>

            <section
              onDragEnter={(e) => { e.preventDefault(); setKeo(true); }}
              onDragOver={(e) => { e.preventDefault(); setKeo(true); }}
              onDragLeave={() => setKeo(false)}
              onDrop={(e) => { e.preventDefault(); setKeo(false); }}
              className={cx(
                "flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed bg-white px-8 py-10 text-center shadow-card transition",
                keo ? "border-navy bg-navy/5" : "border-steel-300",
              )}
            >
              <span className="grid h-14 w-14 place-items-center rounded-2xl bg-steel-100 text-navy">
                <Icon d={IC.tai_len} className="h-7 w-7" />
              </span>
              <p className="text-[15px] font-semibold text-ink">Chọn file bảng kê chứng từ (.xlsx)</p>
              <p className="-mt-1 text-[13px] text-steel-500">nhiều chi nhánh thì chọn nhiều file cùng lúc — hoặc</p>
              <div className="flex flex-wrap justify-center gap-2">
                <Nut bien="phu" onClick={p.onChonFile}><Icon d={IC.file} className="h-4 w-4" />Chọn file…</Nut>
                <Nut bien="phu" onClick={p.onChonNhieu}><Icon d={IC.file} className="h-4 w-4" />Chọn nhiều file</Nut>
                <Nut bien="phu" onClick={p.onQuet} title="Nạp mọi bảng kê trong thư mục nguồn"><Icon d={IC.thu_muc} className="h-4 w-4" />Nạp cả thư mục</Nut>
              </div>
            </section>

            {/* Thẻ file đã nạp */}
            {nap && !nap.loi && (
              <section className="flex flex-col gap-3 rounded-2xl border border-steel-200 bg-white p-4 shadow-card">
                <div className="flex items-center gap-3">
                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-steel-100 text-navy"><Icon d={IC.file} className="h-5 w-5" /></span>
                  <div className="min-w-0">
                    <div className="text-[11px] font-semibold uppercase tracking-wide text-steel-400">File</div>
                    <div className="truncate text-[14px] font-bold text-ink">{nap.ten}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[["Kỳ", nap.ky], ["Số dòng", fso(nap.so_dong)], ["Tổng phát sinh", fso(nap.tong_ps)]].map(([k, v]) => (
                    <div key={k} className="rounded-xl bg-steel-50 px-3 py-2">
                      <div className="text-[11px] font-semibold text-steel-400">{k}</div>
                      <div className="mt-0.5 text-[15px] font-bold tabular-nums text-ink">{v}</div>
                    </div>
                  ))}
                </div>
                {/* Trạng thái CĐPS theo chi nhánh của kỳ đang nạp */}
                {dv.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {dv.map((d) => {
                      const co = !thieuSet.has(d.ma);
                      return (
                        <span key={d.ma}
                          className={cx("inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] font-semibold",
                            co ? "bg-xanh-nen text-xanh-dam" : "bg-do-nen text-do-dam")}>
                          <Icon d={co ? IC.checkNho : IC.x} className="h-3.5 w-3.5" />
                          {d.ten_hien || d.ma} · {co ? "có CĐPS" : "thiếu CĐPS"}
                        </span>
                      );
                    })}
                  </div>
                )}
                <CanhBaoNgoaiKy nap={nap} />
              </section>
            )}
            {nap?.loi && (
              <div className="rounded-xl border border-do-vien bg-do-nen px-4 py-3 text-[13px] font-medium text-do-dam">{nap.loi}</div>
            )}

            {/* Chặn cứng khi thiếu CĐPS */}
            {nap && !nap.loi && thieu.length > 0 && (
              <div className="flex items-start gap-2 rounded-xl border border-do-vien bg-do-nen px-3 py-2.5 text-[12.5px] leading-snug text-do-dam">
                <Icon d={IC.x} className="mt-0.5 h-4 w-4 shrink-0" />
                <span>Còn <b>{thieu.length}</b> chi nhánh chưa có CĐPS ({thieu.map((t) => t.chi_nhanh_ten || t.chi_nhanh).join(", ")}) —
                  quay lại <b>bước 1</b> nạp CĐPS rồi mới Kiểm tra.</span>
              </div>
            )}

            {/* Nút kiểm tra — chặn nếu thiếu CĐPS */}
            <Nut bien="chinh" disabled={!nap || !!nap.loi || dangChay || thieu.length > 0} onClick={p.onKiemTra} className="py-3.5 text-[15px]">
              Kiểm tra
            </Nut>

            {/* Tiến trình */}
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
          </>
        )}
      </div>
    </div>
  );
}
