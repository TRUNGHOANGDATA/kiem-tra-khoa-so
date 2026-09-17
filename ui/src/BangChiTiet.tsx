/** Bảng chi tiết dùng chung: lay_chi_tiet (chứng minh 1 check) & lay_diff_chot
 *  (dòng thêm/bớt). Tìm kiếm + phân trang; cột số căn phải theo cot_so. */
import { useEffect, useMemo, useState } from "react";
import type { ChiTiet, Loi } from "./api";
import { laLoi } from "./api";
import { cx, fso, Icon, IC, Nut } from "./ui";

const KICH_THUOC = 100;

export default function BangChiTiet({ nap }: { nap: (trang: number, kt: number, tim: string) => Promise<ChiTiet | Loi> }) {
  const [d, setD] = useState<ChiTiet | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [trang, setTrang] = useState(1);
  const [tim, setTim] = useState("");
  const [dangTim, setDangTim] = useState("");

  useEffect(() => {
    let huy = false;
    nap(trang, KICH_THUOC, dangTim).then((r) => {
      if (huy) return;
      if (laLoi(r)) { setLoi(r.loi); setD(null); }
      else { setLoi(null); setD(r); }
    });
    return () => { huy = true; };
  }, [trang, dangTim, nap]);

  // debounce ô tìm
  useEffect(() => {
    const t = setTimeout(() => { setDangTim(tim); setTrang(1); }, 280);
    return () => clearTimeout(t);
  }, [tim]);

  const soSet = useMemo(() => new Set(d?.cot_so ?? []), [d]);
  const soTrang = d ? Math.max(1, Math.ceil(d.tong / KICH_THUOC)) : 1;

  return (
    <div className="mt-2 flex max-h-[72vh] flex-col">
      {/* thanh công cụ */}
      <div className="mb-2 flex items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-steel-200 bg-white px-3 py-2">
          <Icon d={IC.search} className="h-4 w-4 text-steel-400" />
          <input value={tim} onChange={(e) => setTim(e.target.value)} placeholder="Tìm trong kết quả…"
            className="w-full bg-transparent text-[13px] outline-none placeholder:text-steel-400" />
        </div>
        {d?.tom_tat && (
          <span className="text-[12.5px] font-semibold text-vang-dam">
            Thêm {fso(d.tom_tat.so_them)} · Bớt {fso(d.tom_tat.so_bot)} · {fso(d.tom_tat.so_ct_anh_huong)} chứng từ
          </span>
        )}
      </div>

      {loi && <div className="rounded-xl border border-do-vien bg-do-nen px-4 py-3 text-[13px] text-do-dam">{loi}</div>}

      {d && (
        <>
          <div className="min-h-0 flex-1 overflow-auto rounded-xl border border-steel-200">
            <table className="w-full border-collapse text-[12.5px]">
              <thead className="sticky top-0 z-10 bg-steel-50">
                <tr>
                  {d.cot.map((c, i) => (
                    <th key={c} className={cx("whitespace-nowrap border-b border-steel-200 px-3 py-2 font-semibold text-steel-500",
                      soSet.has(c) ? "text-right" : "text-left")}>
                      {d.nhan[i] ?? c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {d.dong.length === 0 && (
                  <tr><td colSpan={d.cot.length} className="px-3 py-8 text-center text-steel-400">Không có dòng nào.</td></tr>
                )}
                {d.dong.map((row, ri) => (
                  <tr key={ri} className="odd:bg-white even:bg-steel-50/60 hover:bg-navy/5">
                    {d.cot.map((c) => {
                      const v = row[c];
                      const so = soSet.has(c);
                      const hien = v == null || v === "" ? "" : so && typeof v === "number" ? fso(v) : String(v);
                      // Cột CHỮ phải xuống dòng: "Diễn giải" dài cả dòng làm bảng tràn
                      // ngang, người dùng phải kéo mới đọc được. Cột SỐ thì không bao
                      // giờ ngắt — số tiền bị bẻ đôi là đọc sai.
                      return (
                        <td key={c} className={cx("border-b border-steel-100 px-3 py-1.5",
                          so ? "whitespace-nowrap text-right tabular-nums" : "whitespace-normal break-words text-left")}>
                          {hien}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* phân trang */}
          <div className="mt-2 flex items-center justify-between text-[12.5px] text-steel-500">
            <span><b className="tabular-nums text-ink">{fso(d.tong)}</b> dòng · bấm ô để bôi đen rồi Ctrl+C</span>
            <div className="flex items-center gap-2">
              <Nut bien="phu" className="px-2.5 py-1.5" disabled={trang <= 1} onClick={() => setTrang((t) => t - 1)}><Icon d={IC.chevL} className="h-4 w-4" /></Nut>
              <span className="tabular-nums">Trang {trang}/{soTrang}</span>
              <Nut bien="phu" className="px-2.5 py-1.5" disabled={trang >= soTrang} onClick={() => setTrang((t) => t + 1)}><Icon d={IC.chevR} className="h-4 w-4" /></Nut>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
