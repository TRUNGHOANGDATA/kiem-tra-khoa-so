/** Modal xác nhận chốt sổ (dùng chung cho "Chốt sổ kỳ này" & "Chốt lại").
 *  Khi kỳ đã chốt -> hiện cảnh báo chốt đè (bản cũ thành hết hiệu lực). */
import { useEffect, useState } from "react";
import type { TomTat } from "./api";
import { fso, Icon, IC, Modal, Nut } from "./ui";

export default function ModalChot({ mo, chotLai, tomtat, dong, onChot }: {
  mo: boolean; chotLai: boolean; tomtat?: TomTat; dong: () => void; onChot: (ghiChu: string) => void;
}) {
  const [ghiChu, setGhiChu] = useState("");
  useEffect(() => { if (mo) setGhiChu(""); }, [mo]);
  if (!tomtat) return null;
  const chot = tomtat.chot;
  const daChot = chot?.trang_thai === "DA_CHOT";
  const ngay = chot?.ngay_chot ? new Date(chot.ngay_chot).toLocaleString("vi-VN") : "";

  return (
    <Modal mo={mo} dong={dong} tieuDe={chotLai ? "Chốt lại kỳ này" : "Chốt sổ kỳ này"}>
      <div className="mt-3 space-y-1.5 text-[13px] leading-relaxed text-steel-500">
        <div>Kỳ <b className="text-ink">{tomtat.ky}</b> · Chi nhánh <b className="text-ink">{tomtat.chi_nhanh_ten || tomtat.chi_nhanh}</b></div>
        <div>Số dòng: <b className="tabular-nums text-ink">{fso(tomtat.so_dong)}</b> · Tổng phát sinh: <b className="tabular-nums text-ink">{fso(tomtat.tong_ps)}</b></div>
        <div>Kết luận: <b className="text-ink">{tomtat.cau_ket_luan}</b></div>
      </div>

      {daChot && (
        <div className="mt-3 flex items-start gap-2 rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] leading-snug text-vang-dam">
          <Icon d={IC.warn} className="mt-0.5 h-4 w-4 shrink-0 text-vang" />
          <span>Kỳ này <b>đã chốt</b>{ngay ? ` ngày ${ngay}` : ""}. Chốt lại sẽ tạo bản mới; bản đang có chuyển thành <b>hết hiệu lực</b> (vẫn xem được ở tab Lịch sử chốt sổ).</span>
        </div>
      )}

      <label className="mt-4 block text-[12px] font-semibold text-steel-500">Ghi chú (tùy chọn)</label>
      <input value={ghiChu} onChange={(e) => setGhiChu(e.target.value)} autoFocus
        placeholder="VD: Đã đối chiếu sổ phụ ngân hàng"
        className="mt-1 w-full rounded-xl border border-steel-200 px-3 py-2 text-[13px] outline-none focus:border-navy-400 focus:ring-2 focus:ring-navy/15" />

      <div className="mt-4 flex justify-end gap-2">
        <Nut bien="phu" onClick={dong}>Hủy</Nut>
        <Nut bien="chinh" onClick={() => onChot(ghiChu.trim())}><Icon d={IC.lock} className="h-4 w-4" />Chốt sổ</Nut>
      </div>
    </Modal>
  );
}
