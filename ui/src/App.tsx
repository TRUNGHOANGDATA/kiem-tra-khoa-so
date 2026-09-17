import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { cx, Icon, IC, Modal, Nut, ToastProvider, useToast } from "./ui";
import ManChonFile from "./ChonFile";
import ManKetQua, { TheThongKe } from "./KetQua";
import BangChiTiet from "./BangChiTiet";
import ModalChot from "./ModalChot";
import ModalCaiDat from "./ModalCaiDat";
import ManLichSu from "./LichSu";
import ManCanDoi from "./CanDoi";
import nen from "./assets/nen.png";
import logo from "./assets/logo.png";

type ManHinh = "tongquan" | "kiemtra" | "candoi" | "lichsu";
type TienTrinh = { ten: string; pct: number } | null;

const NAV: { id: ManHinh; nhan: string; icon: React.ReactNode }[] = [
  { id: "tongquan", nhan: "Tổng quan", icon: IC.home },
  { id: "kiemtra", nhan: "Kiểm tra khóa sổ", icon: IC.soKiemTra },
  { id: "candoi", nhan: "Cân đối phát sinh", icon: IC.bar },
  { id: "lichsu", nhan: "Lịch sử", icon: IC.clock },
];

function Noi() {
  const toast = useToast();
  const [man, setMan] = useState<ManHinh>("tongquan");
  const [nap, setNap] = useState<A.ThongTinNap | undefined>();
  const [kq, setKq] = useState<A.KetQua | undefined>();
  const [tt, setTt] = useState<TienTrinh>(null);
  const [, setChay] = useState(false);
  const [modalChot, setModalChot] = useState<{ mo: boolean; chotLai: boolean }>({ mo: false, chotLai: false });
  const [modalCaiDat, setModalCaiDat] = useState(false);
  const [bang, setBang] = useState<{ tieuDe: string; nguon: "chi_tiet" | "diff"; ma?: string } | null>(null);

  useEffect(() => {
    window.onTienTrinh = (ten, pct) => setTt({ ten, pct });
    return () => { window.onTienTrinh = undefined; };
  }, []);

  const nhieu = (kq?.don_vi.length ?? 0) > 1;
  const ky = kq?.tomtat.ky ?? nap?.ky ?? "—";
  const soChiNhanh = kq?.don_vi.length ?? nap?.don_vi?.length ?? 0;

  /* ------------------------------ nạp file ------------------------------- */
  const xuLyNap = (r: A.ThongTinNap | A.Loi | null) => {
    if (!r) return;
    if (laLoi(r)) { toast(r.loi); return; }
    setNap(r); setKq(undefined); setTt(null); setMan("kiemtra");
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
    setKq(r); setMan("tongquan");
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
      else if (man === "lichsu" || man === "candoi") setMan(kq ? "tongquan" : "kiemtra");
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [bang, modalChot.mo, modalCaiDat, man, kq]);

  return (
    <div className="flex h-full bg-[#F3F5F8] font-sans text-ink">
      {/* ------------------------------- Sidebar ------------------------------- */}
      <aside className="flex w-[240px] shrink-0 flex-col bg-[#0E3B2E] text-white">
        <div className="flex items-center gap-3 px-5 py-5">
          <img src={logo} alt="Logo" className="h-11 w-11 shrink-0 rounded-xl object-cover shadow-soft ring-1 ring-white/15" />
          <div className="min-w-0">
            <div className="text-[14px] font-extrabold leading-tight">Kiểm tra<br />khóa sổ cuối kỳ</div>
            <div className="mt-0.5 text-[11px] text-white/50">Doanh nghiệp sản xuất</div>
          </div>
        </div>

        <nav className="flex flex-col gap-0.5 px-3">
          {NAV.map((m) => {
            const active = man === m.id;
            return (
              <button key={m.id} onClick={() => setMan(m.id)}
                className={cx("relative flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-[13.5px] font-semibold transition",
                  active ? "bg-white/10 text-white" : "text-white/60 hover:bg-white/5 hover:text-white")}>
                {active && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-brass-300" />}
                <Icon d={m.icon} className="h-[18px] w-[18px]" />{m.nhan}
              </button>
            );
          })}
          <button onClick={() => setModalCaiDat(true)}
            className="flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-[13.5px] font-semibold text-white/60 transition hover:bg-white/5 hover:text-white">
            <Icon d={IC.gear} className="h-[18px] w-[18px]" />Cài đặt
          </button>
        </nav>

        <div className="mt-auto p-4">
          <div className="rounded-2xl bg-white/5 p-4 ring-1 ring-white/10">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-brass/25 text-brass-300"><Icon d={IC.lock} className="h-5 w-5" /></div>
            <p className="mt-2.5 text-[12.5px] font-semibold leading-snug text-white/85">“Số liệu minh bạch<br />Doanh nghiệp vững mạnh”</p>
          </div>
          <div className="mt-3 px-1 text-[11px] text-white/35">Phiên bản 1.0.0</div>
        </div>
      </aside>

      {/* ------------------------------ Nội dung ------------------------------ */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar */}
        {/* Thanh trên chỉ mô tả FILE ĐANG KIỂM TRA, nên chỉ hiện ở hai màn dùng file đó.
            Màn CĐPS và Lịch sử có bộ lọc kỳ riêng — để nhãn "Kỳ 08/2026" đứng chết trên
            đầu khiến người dùng tưởng nó là ô chọn kỳ mà bấm không được. */}
        {(man === "tongquan" || man === "kiemtra") && (
          <header className="flex items-center gap-4 border-b border-steel-200 bg-white px-6 py-3">
            <div title="Kỳ đọc tự động từ dữ liệu trong file đang kiểm tra — muốn xem kỳ khác thì nạp file khác"
              className="inline-flex cursor-default select-none items-center gap-2 text-[13px] font-semibold text-ink">
              <Icon d={IC.lich} className="h-4 w-4 text-navy" />Kỳ {ky} <span className="font-normal text-steel-400">(theo file đang kiểm tra)</span>
            </div>
            {soChiNhanh > 0 && (
              <div className="inline-flex items-center gap-2 text-[13px] font-medium text-steel-500">
                <Icon d={IC.toanha} className="h-4 w-4 text-steel-400" />{soChiNhanh} chi nhánh được kiểm tra
              </div>
            )}
          </header>
        )}

        <main className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
          {/* Ảnh nền phủ toàn vùng nội dung + lớp phủ trắng mỏng cho dễ đọc */}
          <div className="pointer-events-none absolute inset-0 bg-cover bg-bottom" style={{ backgroundImage: `url(${nen})` }} />
          <div className="pointer-events-none absolute inset-0 bg-white/25" />
          <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden">
          {man === "tongquan" && (
            kq ? (
              <ManKetQua kq={kq} nhieu={nhieu}
                onChonDonVi={chonDonVi}
                onChot={() => setModalChot({ mo: true, chotLai: false })}
                onChotLai={() => setModalChot({ mo: true, chotLai: true })}
                onMoLai={moLai}
                onCapNhatChotLai={capNhatChotLai}
                onXemThayDoi={() => setBang({ tieuDe: "Thay đổi so với bản đã chốt", nguon: "diff" })}
                onXemChiTiet={(ma, td) => setBang({ tieuDe: td, nguon: "chi_tiet", ma })}
                onXuat={xuat} onXuatTongHop={xuatTongHop}
                onKiemTraLai={kiemTra} onFileKhac={() => setMan("kiemtra")} />
            ) : (
              <div className="w-full flex-1 overflow-auto p-6">
                {/* Hero — chữ nổi trên ảnh nền của main */}
                <section className="relative min-h-[150px] px-2 pt-2">
                  <div className="relative z-10 max-w-[560px]">
                    <h1 className="text-[28px] font-extrabold text-ink">Xin chào! <span className="align-middle">👋</span></h1>
                    <p className="mt-2 max-w-[440px] text-[14px] font-medium leading-relaxed text-steel-700">
                      Cùng kiểm tra khóa sổ để đảm bảo dữ liệu chính xác và đầy đủ cho kỳ {ky}.
                    </p>
                    <Nut bien="chinh" className="mt-5 px-6 py-3 text-[14px]" onClick={() => setMan("kiemtra")}>
                      <Icon d={IC.soKiemTra} className="h-4 w-4" />Bắt đầu kiểm tra khóa sổ
                    </Nut>
                  </div>
                  <div className="pointer-events-none absolute right-4 top-1 z-10 hidden text-right text-[16px] font-semibold italic leading-snug text-navy/70 md:block">
                    Kiểm tra hôm nay,<br />An tâm ngày mai
                  </div>
                </section>
                <div className="mt-3"><TheThongKe soDo={0} soVang={0} dat={0} soChiNhanh={soChiNhanh} /></div>
              </div>
            )
          )}
          {man === "kiemtra" && (
            <ManChonFile nap={nap} tienTrinh={tt} onChonFile={chonFile} onChonNhieu={chonNhieu} onQuet={quet} onKiemTra={kiemTra} />
          )}
          {man === "lichsu" && <ManLichSu onQuayLai={() => setMan(kq ? "tongquan" : "kiemtra")} />}
          {man === "candoi" && <ManCanDoi onQuayLai={() => setMan(kq ? "tongquan" : "kiemtra")} />}
          </div>
        </main>
      </div>

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
