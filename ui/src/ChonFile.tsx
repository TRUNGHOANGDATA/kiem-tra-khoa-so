/** Màn 1 — chọn/quét file bảng kê, xem thẻ file + cảnh báo ngoài kỳ, bấm Kiểm tra. */
import { useState } from "react";
import type { ThongTinNap } from "./api";
import { cx, fso, Icon, IC, Nut } from "./ui";

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

export default function ManChonFile(p: ChonFileProps) {
  const { nap, tienTrinh } = p;
  const [keo, setKeo] = useState(false);
  const dangChay = !!tienTrinh;

  return (
    <div className="flex flex-1 items-center justify-center overflow-auto p-8">
      <div className="flex w-full max-w-[560px] flex-col gap-4">
        {/* Vùng kéo thả */}
        <section
          onDragEnter={(e) => { e.preventDefault(); setKeo(true); }}
          onDragOver={(e) => { e.preventDefault(); setKeo(true); }}
          onDragLeave={() => setKeo(false)}
          onDrop={(e) => { e.preventDefault(); setKeo(false); /* kéo-thả path thật do pywebview xử lý riêng; ở đây vẫn cho chọn qua nút */ }}
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
            {(nap.don_vi?.length ?? 0) > 1 && (
              <div className="flex flex-wrap gap-1.5">
                {nap.don_vi.map((d) => (
                  <span key={d.ma} className="rounded-lg bg-steel-100 px-2 py-1 text-[12px] font-semibold text-steel-700">
                    {d.ma} <span className="text-steel-400 tabular-nums">· {fso(d.so_dong)}</span>
                  </span>
                ))}
              </div>
            )}
            <CanhBaoNgoaiKy nap={nap} />
          </section>
        )}
        {nap?.loi && (
          <div className="rounded-xl border border-do-vien bg-do-nen px-4 py-3 text-[13px] font-medium text-do-dam">{nap.loi}</div>
        )}

        {/* Nút kiểm tra */}
        <Nut bien="chinh" disabled={!nap || !!nap.loi || dangChay} onClick={p.onKiemTra} className="py-3.5 text-[15px]">
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
      </div>
    </div>
  );
}
