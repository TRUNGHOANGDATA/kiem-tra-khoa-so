/**
 * Cầu nối React ↔ pywebview (window.pywebview.api). Toàn bộ phương thức của JsApi
 * (app/api.py) được gói kiểu ở đây. API chỉ sẵn sàng sau sự kiện 'pywebviewready';
 * sanApi() trả Promise chờ đúng lúc đó.
 */

/* ------------------------------- kiểu dữ liệu ------------------------------ */
export type MucDo = "do" | "vang" | "xanh";
export type KetLuanMa = "chua_san_sang" | "can_ra_soat" | "san_sang";

export interface Chot {
  trang_thai: "DA_CHOT" | "CHUA_CHOT";
  doi_chieu: "KHOP" | "LECH" | "CHUA_CHOT";
  ngay_chot?: string;
  ghi_chu?: string;
  ket_luan_ma?: string;
  loi_kho?: string;
  tom_tat_lech?: { delta_dong: number; delta_ps: number; so_ct_anh_huong: number };
}

export interface DonVi {
  i: number;
  ma: string;
  ten_hien?: string;
  ky: string;
  so_dong: number;
  tong_ps: number;
  nguon?: string;
  da_chay?: boolean;
  muc_do_ket_luan?: KetLuanMa;
  cau_ket_luan?: string;
  san_sang?: boolean;
  so_do?: number;
  so_vang?: number;
  so_chua_lam?: number;
  so_can_ra?: number;
  con_viec?: number;
  chot?: Chot;
}

export interface Buoc {
  buoc: string;
  trang_thai: string; // DA_LAM / CAN_RA / CHUA_LAM / TU_XAC_NHAN / KHONG_AP_DUNG
  tom_tat: string;
  ma_check: string;
  co_chung_cu: boolean;
}

export interface Check {
  ma: string;
  ten: string;
  muc_do: MucDo;
  so_loi: number;
  la_thong_ke: boolean;
  ghi_chu: string;
}
export interface Nhom {
  ma: string;
  ten: string;
  so_loi: number;
  muc_do: MucDo;
  checks: Check[];
}

export interface TomTat {
  ky: string;
  ten: string;
  so_dong: number;
  tong_ps: number;
  chi_nhanh: string;
  chi_nhanh_ten?: string;
  cau_ket_luan: string;
  muc_do_ket_luan: KetLuanMa;
  so_do: number;
  so_vang: number;
  so_chua_lam: number;
  so_can_ra: number;
  con_viec: number;
  san_sang: boolean;
  chot: Chot;
}

export interface KetQua {
  tomtat: TomTat;
  trang_thai: Buoc[];
  nhom: Nhom[];
  don_vi: DonVi[];
  dang_xem: number;
  loi?: string;
}

export interface DonViNap {
  ma: string;
  ten_hien?: string;
  ky: string;
  so_dong: number;
  tong_ps: number;
  nguon?: string;
  ngoai_ky?: number;
  ngoai_ky_ct?: [string, number][];
}
export interface ThongTinNap {
  path: string;
  cac_path: string[];
  so_file: number;
  ten: string;
  ky: string;
  so_dong: number;
  tong_ps: number;
  don_vi: DonViNap[];
  loi?: string;
}

export interface ChiTiet {
  tong: number;
  trang: number;
  cot: string[];
  nhan: string[];
  cot_so: string[];
  cot_so_le: string[];
  tom_tat?: { so_them: number; so_bot: number; so_ct_anh_huong: number };
  dong: Record<string, unknown>[];
  loi?: string;
}

export interface BanChot {
  id: number;
  ky_nam: number;
  ky_thang: number;
  chi_nhanh: string;
  chi_nhanh_ten?: string;
  thoi_diem_chot: string;
  ghi_chu: string;
  ket_luan_ma: string;
  con_hieu_luc: number;
  so_do: number;
  so_vang: number;
}

export interface CauHinh {
  tho: { thu_muc_nguon: string; thu_muc_xuat: string; thu_muc_kho: string };
  giai: { thu_muc_nguon: string; thu_muc_xuat: string; thu_muc_kho: string };
  quy_doi: Record<string, string>;
  ma_goi_y: string[];
  loi?: string;
}

type Loi = { loi: string };
export const laLoi = (x: unknown): x is Loi =>
  !!x && typeof x === "object" && typeof (x as Loi).loi === "string";

/* ------------------------------- cầu nối ---------------------------------- */
interface PyApi {
  chon_file(nhieu?: boolean): Promise<ThongTinNap | Loi | null>;
  chon_nhieu_file(): Promise<ThongTinNap | Loi | null>;
  quet_thu_muc(): Promise<ThongTinNap | Loi>;
  nap_nhieu_file(paths: string[]): Promise<ThongTinNap | Loi>;
  chay_kiem_tra(path: string | string[] | null): Promise<KetQua | Loi>;
  chon_don_vi(i: number): Promise<KetQua | Loi>;
  lay_chi_tiet(ma: string, trang?: number, kich_thuoc?: number, tim?: string): Promise<ChiTiet | Loi>;
  xuat_bao_cao(): Promise<{ path: string } | Loi>;
  xuat_tong_hop(): Promise<{ path: string } | Loi>;
  mo_file(path: string): Promise<boolean | Loi>;
  mo_thu_muc(path: string): Promise<boolean | Loi>;
  chot_so(ghi_chu?: string): Promise<{ chot: Chot } | Loi>;
  mo_lai_ky(): Promise<{ chot: Chot } | Loi>;
  lich_su_chot(chi_nhanh?: string | null): Promise<{ dong: BanChot[] } | Loi>;
  lay_diff_chot(trang?: number, kich_thuoc?: number, tim?: string): Promise<ChiTiet | Loi>;
  sao_luu_kho(): Promise<{ path: string } | Loi>;
  phuc_hoi_kho(path: string): Promise<{ da_sao_luu: string } | Loi>;
  nhap_gop_kho(path: string): Promise<{ da_them: number; bo_qua_trung: number } | Loi>;
  tom_tat_kho(path: string): Promise<{ so_ban: number; so_ban_hieu_luc: number; so_ky: number; so_chi_nhanh: number; ky_dau: string; ky_cuoi: string } | Loi>;
  chon_file_sqlite(): Promise<{ path: string } | { huy: true } | Loi>;
  chon_thu_muc(directory?: string): Promise<{ path: string } | { huy: true } | Loi>;
  lay_cau_hinh(): Promise<CauHinh | Loi>;
  luu_cau_hinh(cfg: { thu_muc_nguon?: string; thu_muc_xuat?: string; thu_muc_kho?: string;
                      quy_doi_chi_nhanh?: Record<string, string> }): Promise<{ ok: true } | Loi>;
  mo_thu_muc_kho(): Promise<boolean | Loi>;
}

declare global {
  interface Window {
    pywebview?: { api: PyApi };
    onTienTrinh?: (ten: string, pct: number) => void;
  }
}

let sanSang: Promise<PyApi> | null = null;
export function sanApi(): Promise<PyApi> {
  if (window.pywebview?.api) return Promise.resolve(window.pywebview.api);
  if (!sanSang) {
    sanSang = new Promise<PyApi>((resolve) => {
      window.addEventListener("pywebviewready", () => resolve(window.pywebview!.api), { once: true });
    });
  }
  return sanSang;
}

/** Gọi một phương thức api sau khi bridge sẵn sàng. */
export async function goi<K extends keyof PyApi>(ten: K, ...args: Parameters<PyApi[K]>): Promise<ReturnType<PyApi[K]>> {
  const api = await sanApi();
  // @ts-expect-error spread vào phương thức động
  return api[ten](...args);
}
