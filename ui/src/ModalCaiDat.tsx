/** Modal Cài đặt — thư mục Nguồn/Xuất/Kho + bảng quy đổi chi nhánh (mã → tên hiển thị). */
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
  const [ma, setMa] = useState<string[]>([]);              // các mã chi nhánh (gợi ý từ file + đã quy đổi)
  const [ten, setTen] = useState<Record<string, string>>({}); // mã -> tên hiển thị
  const [maMoi, setMaMoi] = useState("");                  // ô thêm mã thủ công
  const [tab, setTab] = useState<"thu_muc" | "quy_doi">("thu_muc");

  useEffect(() => {
    if (!mo) return;
    A.goi("lay_cau_hinh").then((r) => {
      if (laLoi(r)) { toast(r.loi); return; }
      setGt({ ...r.tho });
      setMa(r.ma_goi_y ?? []);
      setTen({ ...(r.quy_doi ?? {}) });
      setMaMoi("");
      setTab("thu_muc");
    });
  }, [mo, toast]);

  const chon = async (khoa: string) => {
    const r = await A.goi("chon_thu_muc", gt[khoa] || "");
    if (laLoi(r)) { toast(r.loi); return; }
    if ("path" in r) setGt((g) => ({ ...g, [khoa]: r.path }));
  };

  const themMa = () => {
    const m = maMoi.trim();
    if (!m) return;
    if (!ma.includes(m)) setMa((xs) => [...xs, m]);
    setMaMoi("");
  };

  const xoaMa = (m: string) => {
    setMa((xs) => xs.filter((x) => x !== m));       // bỏ khỏi danh sách -> Lưu là xóa hẳn trong kho
    setTen((t) => { const { [m]: _bo, ...con } = t; return con; });
  };

  const luu = async () => {
    // Chỉ gửi cặp có tên; backend tự lọc lần nữa và giữ nguyên mã gốc làm danh tính.
    const quy_doi: Record<string, string> = {};
    for (const m of ma) { const t = (ten[m] ?? "").trim(); if (t) quy_doi[m] = t; }
    const r = await A.goi("luu_cau_hinh", { ...gt, quy_doi_chi_nhanh: quy_doi });
    if (laLoi(r)) { toast(r.loi); return; }
    dong(); toast("Đã lưu cài đặt");
  };

  const TAB: [typeof tab, string][] = [["thu_muc", "Thư mục"], ["quy_doi", "Quy đổi chi nhánh"]];

  return (
    <Modal mo={mo} dong={dong} tieuDe="Cài đặt">
      {/* Thanh tab — mỗi mục một khu riêng, không dồn hết vào một trang cuộn dài */}
      <div className="mt-1 flex gap-1 border-b border-steel-200">
        {TAB.map(([k, nhan]) => (
          <button key={k} type="button" onClick={() => setTab(k)}
            className={
              "-mb-px rounded-t-lg px-4 py-2 text-[13px] font-semibold transition " +
              (tab === k
                ? "border-b-2 border-navy text-navy"
                : "border-b-2 border-transparent text-steel-400 hover:text-steel-600")
            }>
            {nhan}
          </button>
        ))}
      </div>

      <div className="mt-4 max-h-[60vh] overflow-auto pr-1">
        {tab === "thu_muc" && (
          <section className="space-y-3">
            <p className="text-[12.5px] text-steel-500">App đọc lại cấu hình mỗi lần dùng — lưu xong là có hiệu lực ngay.</p>
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
          </section>
        )}

        {tab === "quy_doi" && (
          <section className="space-y-2.5">
            <p className="text-[12.5px] text-steel-500">
              Đặt tên dễ nhớ cho từng mã (A01 = “Nhà máy Hải Phòng”); bấm 🗑 để xóa một mã. Lưu vào kho SQLite.
              Tên hiển thị khắp nơi và trong file Excel; <b>mã gốc vẫn là danh tính khi chốt sổ</b> nên đổi tên/xóa tên không ảnh hưởng đối chiếu kỳ cũ.
            </p>

            {ma.length === 0 && (
              <p className="rounded-xl bg-steel-50 px-3 py-2.5 text-[12.5px] text-steel-500">
                Chưa có mã nào. Nạp một file bảng kê để hiện sẵn danh sách mã, hoặc thêm mã thủ công bên dưới.
              </p>
            )}

            <div className="space-y-2">
              {ma.map((m) => (
                <div key={m} className="flex items-center gap-2">
                  <span className="w-16 shrink-0 rounded-lg bg-steel-100 px-2 py-1.5 text-center text-[12.5px] font-bold text-steel-700">{m}</span>
                  <span className="shrink-0 text-steel-300">→</span>
                  <input
                    value={ten[m] ?? ""}
                    placeholder="Tên hiển thị…"
                    onChange={(e) => setTen((t) => ({ ...t, [m]: e.target.value }))}
                    className="w-full rounded-xl border border-steel-200 px-3 py-2 text-[13px] outline-none focus:border-navy-400 focus:ring-2 focus:ring-navy/15" />
                  <button type="button" onClick={() => xoaMa(m)} title="Xóa mã này"
                    className="shrink-0 rounded-lg p-2 text-steel-400 transition hover:bg-rose-50 hover:text-rose-500">
                    <Icon d={IC.thung} className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Thêm mã thủ công */}
            <div className="flex items-center gap-2 pt-0.5">
              <input
                value={maMoi}
                placeholder="Thêm mã khác…"
                onChange={(e) => setMaMoi(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), themMa())}
                className="w-28 rounded-xl border border-steel-200 px-3 py-2 text-[13px] outline-none focus:border-navy-400 focus:ring-2 focus:ring-navy/15" />
              <Nut bien="phu" onClick={themMa}>Thêm mã</Nut>
            </div>
          </section>
        )}
      </div>

      <div className="mt-5 flex justify-end gap-2 border-t border-steel-200 pt-3">
        <Nut bien="phu" onClick={dong}>Hủy</Nut>
        <Nut bien="chinh" onClick={luu}>Lưu</Nut>
      </div>
    </Modal>
  );
}
