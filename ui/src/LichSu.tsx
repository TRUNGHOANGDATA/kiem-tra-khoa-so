/** Màn Lịch sử chốt sổ + thanh công cụ kho (sao lưu/phục hồi/nhập/mở thư mục). */
import { useCallback, useEffect, useMemo, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { cx, Icon, IC, Nut, useToast } from "./ui";

const NHAN_KL: Record<string, string> = { san_sang: "Sẵn sàng", can_ra_soat: "Cần rà soát", chua_san_sang: "Chưa sẵn sàng", SAN_SANG: "Sẵn sàng", CAN_RA_SOAT: "Cần rà soát", CHUA_SAN_SANG: "Chưa sẵn sàng" };
const mauKL = (m: string) => (m.toLowerCase().includes("san_sang") && !m.toLowerCase().includes("chua") ? "text-xanh-dam" : m.toLowerCase().includes("can_ra") ? "text-vang-dam" : "text-do-dam");

function moTaKho(s: { so_ban: number; so_ban_hieu_luc: number; so_ky: number; so_chi_nhanh: number; ky_dau: string; ky_cuoi: string }) {
  const khoang = s.ky_dau && s.ky_cuoi ? (s.ky_dau === s.ky_cuoi ? s.ky_dau : `${s.ky_dau} → ${s.ky_cuoi}`) : "—";
  return `• ${s.so_ban} bản chốt (${s.so_ban_hieu_luc} còn hiệu lực)\n• ${s.so_ky} kỳ · ${s.so_chi_nhanh} chi nhánh · kỳ ${khoang}`;
}

export default function ManLichSu({ onQuayLai }: { onQuayLai: () => void }) {
  const toast = useToast();
  const [dong, setDong] = useState<A.BanChot[]>([]);
  const [fKy, setFKy] = useState("all");
  const [fCn, setFCn] = useState("all");
  const [fHl, setFHl] = useState(false);

  const tai = useCallback(async () => {
    const r = await A.goi("lich_su_chot", null);
    if (laLoi(r)) { toast(r.loi); return; }
    setDong(r.dong);
  }, [toast]);
  useEffect(() => { tai(); }, [tai]);

  const ky = (r: A.BanChot) => `${String(r.ky_thang).padStart(2, "0")}/${r.ky_nam}`;
  const kyOpts = useMemo(() => [...new Set(dong.map(ky))].sort().reverse(), [dong]);
  const cnOpts = useMemo(() => [...new Map(dong.map((r) => [r.chi_nhanh, r.chi_nhanh_ten || r.chi_nhanh])).entries()], [dong]);
  const loc = dong.filter((r) =>
    (fKy === "all" || ky(r) === fKy) && (fCn === "all" || r.chi_nhanh === fCn) && (!fHl || r.con_hieu_luc));

  const saoLuu = async () => { const k = await A.goi("sao_luu_kho"); toast(laLoi(k) ? k.loi : "Đã sao lưu kho: " + k.path); };
  const chonKho = async () => { const f = await A.goi("chon_file_sqlite"); return laLoi(f) ? (toast(f.loi), null) : "huy" in f ? null : f.path; };
  const phucHoi = async () => {
    const p = await chonKho(); if (!p) return;
    const s = await A.goi("tom_tat_kho", p); if (laLoi(s)) { toast(s.loi); return; }
    if (!confirm(`File kho được chọn:\n${moTaKho(s)}\n\nPhục hồi sẽ THAY kho hiện tại bằng file này (bản cũ tự sao lưu trước). Tiếp tục?`)) return;
    const k = await A.goi("phuc_hoi_kho", p); toast(laLoi(k) ? k.loi : "Đã phục hồi. Backup: " + k.da_sao_luu); tai();
  };
  const nhapGop = async () => {
    const p = await chonKho(); if (!p) return;
    const s = await A.goi("tom_tat_kho", p); if (laLoi(s)) { toast(s.loi); return; }
    if (!confirm(`File kho được chọn:\n${moTaKho(s)}\n\nNhập & gộp sẽ THÊM các bản chưa có vào kho hiện tại (không xóa gì). Tiếp tục?`)) return;
    const k = await A.goi("nhap_gop_kho", p); toast(laLoi(k) ? k.loi : `Đã thêm ${k.da_them}, bỏ qua ${k.bo_qua_trung} bản trùng.`); tai();
  };

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-1 flex-col gap-4 overflow-hidden p-4">
      <div className="flex items-center gap-3">
        <h2 className="text-[18px] font-extrabold text-ink">Lịch sử chốt sổ</h2>
        <Nut bien="phu" className="ml-auto" onClick={onQuayLai}><Icon d={IC.chevL} className="h-4 w-4" />Quay lại</Nut>
      </div>
      <div className="flex flex-wrap gap-2">
        <Nut bien="phu" onClick={saoLuu}>Sao lưu kho</Nut>
        <Nut bien="phu" onClick={phucHoi}>Phục hồi từ file…</Nut>
        <Nut bien="phu" onClick={nhapGop}>Nhập & gộp từ file…</Nut>
        <Nut bien="phu" onClick={() => A.goi("mo_thu_muc_kho")}>Mở thư mục kho</Nut>
      </div>

      {/* Bộ lọc */}
      <div className="flex flex-wrap items-center gap-2 text-[13px]">
        <span className="font-semibold text-steel-500">Lọc:</span>
        <select value={fKy} onChange={(e) => setFKy(e.target.value)}
          className="rounded-lg border border-steel-200 bg-white px-2.5 py-1.5 text-[13px] outline-none focus:border-navy-400">
          <option value="all">Mọi kỳ</option>
          {kyOpts.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <select value={fCn} onChange={(e) => setFCn(e.target.value)}
          className="rounded-lg border border-steel-200 bg-white px-2.5 py-1.5 text-[13px] outline-none focus:border-navy-400">
          <option value="all">Mọi chi nhánh</option>
          {cnOpts.map(([ma, ten]) => <option key={ma} value={ma}>{ten}</option>)}
        </select>
        <label className="ml-1 inline-flex items-center gap-1.5 text-steel-600">
          <input type="checkbox" checked={fHl} onChange={(e) => setFHl(e.target.checked)} className="accent-navy" />
          Chỉ còn hiệu lực
        </label>
        <span className="ml-auto text-[12px] font-semibold text-steel-400 tabular-nums">{loc.length}/{dong.length} bản</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto rounded-2xl border border-steel-200 bg-white shadow-card">
        <table className="w-full border-collapse text-[13px]">
          <thead className="sticky top-0 bg-steel-50">
            <tr className="text-left text-[12px] font-bold uppercase tracking-wide text-steel-400">
              {["Kỳ", "Chi nhánh", "Ngày chốt", "Kết luận", "Trạng thái", "Ghi chú"].map((h) => (
                <th key={h} className="border-b border-steel-200 px-4 py-2.5">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loc.length === 0 && <tr><td colSpan={6} className="px-4 py-10 text-center text-steel-400">{dong.length ? "Không có bản chốt khớp bộ lọc." : "Chưa có kỳ nào được chốt."}</td></tr>}
            {loc.map((r) => (
              <tr key={r.id} className={cx("border-b border-steel-100", !r.con_hieu_luc && "opacity-50")}>
                <td className="px-4 py-2.5 font-semibold tabular-nums">{String(r.ky_thang).padStart(2, "0")}/{r.ky_nam}</td>
                <td className="px-4 py-2.5 font-semibold">
                  {r.chi_nhanh_ten || r.chi_nhanh}
                  {r.chi_nhanh_ten && r.chi_nhanh_ten !== r.chi_nhanh && <span className="ml-1.5 text-[11px] font-medium text-steel-400">{r.chi_nhanh}</span>}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-steel-500">{r.thoi_diem_chot}</td>
                <td className={cx("px-4 py-2.5 font-semibold", mauKL(r.ket_luan_ma))}>{NHAN_KL[r.ket_luan_ma] ?? r.ket_luan_ma}</td>
                <td className="px-4 py-2.5">{r.con_hieu_luc ? <span className="text-xanh-dam">Hiệu lực</span> : <span className="text-steel-400">Đã thay</span>}</td>
                <td className="px-4 py-2.5 text-steel-500">{r.ghi_chu}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
