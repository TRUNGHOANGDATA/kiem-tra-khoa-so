import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { cx, fso, Icon, IC, Modal, Nut, ToastProvider, useToast } from "./ui";
import ManChonFile from "./ChonFile";
import ManKetQua from "./KetQua";
import BangChiTiet from "./BangChiTiet";
import ModalChot from "./ModalChot";
import ModalCaiDat from "./ModalCaiDat";
import ManLichSu from "./LichSu";

type ManHinh = "chon" | "ketqua" | "lichsu";
type TienTrinh = { ten: string; pct: number } | null;

function NutHeader({ children, icon, onClick }: { children: React.ReactNode; icon: React.ReactNode; onClick?: () => void }) {
  return (
    <button onClick={onClick} className="inline-flex items-center gap-2 rounded-xl border border-white/25 bg-white/10 px-3.5 py-2 text-[13px] font-semibold text-white transition hover:bg-white/20">
      <Icon d={icon} className="h-4 w-4" />{children}
    </button>
  );
}

function Noi() {
  const toast = useToast();
  const [man, setMan] = useState<ManHinh>("chon");
  const [nap, setNap] = useState<A.ThongTinNap | undefined>();
  const [kq, setKq] = useState<A.KetQua | undefined>();
  const [tt, setTt] = useState<TienTrinh>(null);
  const [chay, setChay] = useState(false);
  const [modalChot, setModalChot] = useState<{ mo: boolean; chotLai: boolean }>({ mo: false, chotLai: false });
  const [modalCaiDat, setModalCaiDat] = useState(false);
  const [bang, setBang] = useState<{ tieuDe: string; nguon: "chi_tiet" | "diff"; ma?: string } | null>(null);

  // Python đập nhịp tiến trình qua window.onTienTrinh.
  useEffect(() => {
    window.onTienTrinh = (ten, pct) => setTt({ ten, pct });
    return () => { window.onTienTrinh = undefined; };
  }, []);

  const nhieu = (kq?.don_vi.length ?? 0) > 1;

  /* ------------------------------ nạp file ------------------------------- */
  const xuLyNap = (kq: A.ThongTinNap | A.Loi | null) => {
    if (!kq) return;
    if (laLoi(kq)) { toast(kq.loi); return; }
    setNap(kq); setKq(undefined); setMan("chon");
  };
  const chonFile = async () => xuLyNap(await A.goi("chon_file", false));
  const chonNhieu = async () => xuLyNap(await A.goi("chon_nhieu_file"));
  const quet = async () => xuLyNap(await A.goi("quet_thu_muc"));

  /* ----------------------------- kiểm tra -------------------------------- */
  const kiemTra = useCallback(async () => {
    if (!nap) return;
    setChay(true); setTt({ ten: "Đang chuẩn bị…", pct: 0 });
    const r = await A.goi("chay_kiem_tra", nap.cac_path);
    setChay(false); setTt(null);
    if (laLoi(r)) { toast(r.loi); return; }
    setKq(r); setMan("ketqua");
  }, [nap, toast]);

  const chonDonVi = async (i: number) => {
    const r = await A.goi("chon_don_vi", i);
    if (laLoi(r)) { toast(r.loi); return; }
    setKq(r);
  };
  const lamMoi = async () => {
    const r = await A.goi("chon_don_vi", kq?.dang_xem ?? 0);
    if (!laLoi(r)) setKq(r);
  };

  /* ------------------------------- chốt ---------------------------------- */
  const xacNhanChot = async (ghiChu: string) => {
    const r = await A.goi("chot_so", ghiChu);
    setModalChot({ mo: false, chotLai: false });
    if (laLoi(r)) { toast(r.loi); return; }
    await lamMoi(); toast("Đã chốt sổ kỳ này");
  };
  const moLai = async () => {
    if (!confirm("Mở lại kỳ này? Bản đã chốt vẫn được giữ trong lịch sử.")) return;
    const r = await A.goi("mo_lai_ky");
    if (laLoi(r)) { toast(r.loi); return; }
    await lamMoi(); toast("Đã mở lại kỳ");
  };
  const capNhatChotLai = async () => {
    if (!confirm("Đóng băng dữ liệu MỚI làm bản chốt hiện hành? Bản cũ vẫn được giữ trong lịch sử.")) return;
    const r = await A.goi("chot_so", "Cập nhật dữ liệu mới");
    if (laLoi(r)) { toast(r.loi); return; }
    await lamMoi(); toast("Đã cập nhật và chốt lại kỳ này");
  };

  /* ------------------------------ xuất ----------------------------------- */
  const xuat = async () => {
    const r = await A.goi("xuat_bao_cao");
    if (laLoi(r)) { toast(r.loi); return; }
    toast("Đã xuất báo cáo"); A.goi("mo_file", r.path);
  };
  const xuatTongHop = async () => {
    const r = await A.goi("xuat_tong_hop");
    if (laLoi(r)) { toast(r.loi); return; }
    toast("Đã xuất tổng hợp"); A.goi("mo_file", r.path);
  };

  /* --------------------------- Esc quay lại ------------------------------ */
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (bang) setBang(null);
      else if (modalChot.mo) setModalChot({ mo: false, chotLai: false });
      else if (modalCaiDat) setModalCaiDat(false);
      else if (man === "lichsu") setMan("ketqua");
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [bang, modalChot.mo, modalCaiDat, man]);

  return (
    <div className="flex h-full flex-col bg-steel-100 font-sans text-ink">
      {/* Header */}
      <header className="flex items-center gap-4 bg-gradient-to-br from-navy-dark via-navy to-navy-400 px-6 py-3 text-white shadow-header">
        <div className="grid h-10 w-10 place-items-center rounded-xl border border-white/25 bg-white/15 text-[15px] font-extrabold tracking-wide">KS</div>
        <div>
          <h1 className="text-[17px] font-bold leading-tight">Kiểm tra khóa sổ cuối kỳ</h1>
          <p className="text-[12px] text-steel-200">Doanh nghiệp sản xuất · Thông tư 200</p>
        </div>
        <div className="ml-auto flex items-center gap-2.5">
          {kq && <span className="hidden items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-3.5 py-2 text-[13px] font-semibold md:inline-flex">{nhieu ? `${kq.don_vi.length} chi nhánh · ` : ""}kỳ {kq.tomtat.ky}</span>}
          <NutHeader icon={IC.clock} onClick={() => setMan("lichsu")}>Lịch sử chốt sổ</NutHeader>
          <NutHeader icon={IC.gear} onClick={() => setModalCaiDat(true)}>Cài đặt</NutHeader>
        </div>
      </header>

      {/* Thân */}
      {man === "chon" && (
        <ManChonFile nap={nap} tienTrinh={tt} onChonFile={chonFile} onChonNhieu={chonNhieu} onQuet={quet} onKiemTra={kiemTra} />
      )}
      {man === "ketqua" && kq && (
        <ManKetQua kq={kq} nhieu={nhieu}
          onChonDonVi={chonDonVi}
          onChot={() => setModalChot({ mo: true, chotLai: false })}
          onChotLai={() => setModalChot({ mo: true, chotLai: true })}
          onMoLai={moLai}
          onCapNhatChotLai={capNhatChotLai}
          onXemThayDoi={() => setBang({ tieuDe: "Thay đổi so với bản đã chốt", nguon: "diff" })}
          onXemChiTiet={(ma, td) => setBang({ tieuDe: td, nguon: "chi_tiet", ma })}
          onXuat={xuat} onXuatTongHop={xuatTongHop}
          onKiemTraLai={kiemTra} onFileKhac={() => { setMan("chon"); }} />
      )}
      {man === "lichsu" && <ManLichSu onQuayLai={() => setMan(kq ? "ketqua" : "chon")} />}

      {/* Modals */}
      <ModalChot
        mo={modalChot.mo} chotLai={modalChot.chotLai} tomtat={kq?.tomtat}
        dong={() => setModalChot({ mo: false, chotLai: false })} onChot={xacNhanChot} />
      <ModalCaiDat mo={modalCaiDat} dong={() => setModalCaiDat(false)} />
      {bang && (
        <Modal mo dong={() => setBang(null)} tieuDe={bang.tieuDe} rong>
          <BangChiTiet
            nap={(trang, kt, tim) =>
              bang.nguon === "diff"
                ? A.goi("lay_diff_chot", trang, kt, tim)
                : A.goi("lay_chi_tiet", bang.ma!, trang, kt, tim)} />
        </Modal>
      )}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Noi />
    </ToastProvider>
  );
}
