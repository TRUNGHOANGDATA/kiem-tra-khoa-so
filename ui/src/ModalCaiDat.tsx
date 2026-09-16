/** Modal Cài đặt — chọn 3 thư mục Nguồn/Xuất/Kho (đọc/ghi qua cấu hình). */
import { useEffect, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { Icon, IC, Modal, Nut, useToast } from "./ui";

const HANG = [
  ["thu_muc_nguon", "Thư mục Nguồn"],
  ["thu_muc_xuat", "Thư mục Xuất báo cáo"],
  ["thu_muc_kho", "Thư mục Kho chốt sổ"],
] as const;

export default function ModalCaiDat({ mo, dong }: { mo: boolean; dong: () => void }) {
  const toast = useToast();
  const [gt, setGt] = useState<Record<string, string>>({ thu_muc_nguon: "", thu_muc_xuat: "", thu_muc_kho: "" });

  useEffect(() => {
    if (!mo) return;
    A.goi("lay_cau_hinh").then((r) => { if (!laLoi(r)) setGt({ ...r.tho }); else toast(r.loi); });
  }, [mo, toast]);

  const chon = async (khoa: string) => {
    const r = await A.goi("chon_thu_muc", gt[khoa] || "");
    if (laLoi(r)) { toast(r.loi); return; }
    if ("path" in r) setGt((g) => ({ ...g, [khoa]: r.path }));
  };
  const luu = async () => {
    const r = await A.goi("luu_cau_hinh", gt);
    if (laLoi(r)) { toast(r.loi); return; }
    dong(); toast("Đã lưu cài đặt thư mục");
  };

  return (
    <Modal mo={mo} dong={dong} tieuDe="Cài đặt thư mục">
      <p className="mt-1 text-[12.5px] text-steel-500">App đọc lại cấu hình mỗi lần dùng — sửa xong bấm Lưu là có hiệu lực ngay.</p>
      <div className="mt-3 space-y-3">
        {HANG.map(([khoa, nhan]) => (
          <div key={khoa}>
            <label className="block text-[12px] font-semibold text-steel-500">{nhan}</label>
            <div className="mt-1 flex gap-2">
              <input value={gt[khoa]} onChange={(e) => setGt((g) => ({ ...g, [khoa]: e.target.value }))}
                className="w-full rounded-xl border border-steel-200 px-3 py-2 text-[13px] outline-none focus:border-navy-400 focus:ring-2 focus:ring-navy/15" />
              <Nut bien="phu" onClick={() => chon(khoa)}><Icon d={IC.thu_muc} className="h-4 w-4" />Chọn…</Nut>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Nut bien="phu" onClick={dong}>Hủy</Nut>
        <Nut bien="chinh" onClick={luu}>Lưu</Nut>
      </div>
    </Modal>
  );
}
