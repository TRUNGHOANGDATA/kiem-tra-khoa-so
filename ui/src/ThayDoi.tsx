/** Màn "Thay đổi từ khi chốt": chứng từ (thêm/bớt/SỬA) + chỉ số CĐPS đã đổi so với bản
 *  chốt — để kiểm soát bút toán phát sinh sau khi đã khóa sổ.
 *
 *  Người dùng MÙ MÀU: mọi mức độ phải mang KÝ HIỆU đứng trước (＋ － ✎ –), màu chỉ là
 *  lớp phụ. Không bao giờ phân biệt chỉ bằng màu. */
import { useCallback, useEffect, useState } from "react";
import * as A from "./api";
import { laLoi } from "./api";
import { cx, fso, Icon, IC, Nut, useToast } from "./ui";

type Dong = Record<string, unknown>;
interface Sua { so_ct: string; dong_cu: Dong[]; dong_moi: Dong[] }
interface ChungTu {
  tom_tat: { ct_them: number; ct_bot: number; ct_sua: number };
  them: Dong[]; bot: Dong[]; sua: Sua[];
}
interface CdpsDoi {
  so_doi: number; so_them: number; so_bot: number;
  dong: { account: string; kieu: string; cot?: string; [k: string]: unknown }[];
}
interface DonVi {
  chi_nhanh: string; chi_nhanh_ten: string; ky: string;
  thoi_diem_chot: string; ghi_chu_chot?: string;
  co_cdps_chot: boolean; chung_tu: ChungTu; cdps: CdpsDoi | null;
}
interface KetQua {
  pham_vi: string; don_vi: DonVi[];
  tom_tat: { ct_them: number; ct_bot: number; ct_sua: number; tk_doi: number; so_chi_nhanh: number };
}

/** Cột đáng hiện của một dòng bảng kê — bỏ cột rỗng cho đỡ ngợp. */
const COT = ["DocCode", "DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description"];
const NHAN: Record<string, string> = {
  DocCode: "Loại CT", DocNo: "Số CT", DocDate: "Ngày CT", DebitAccount: "TK Nợ",
  CreditAccount: "TK Có", Amount: "Số tiền", Description: "Diễn giải",
};

function BangDong({ dong, vien }: { dong: Dong[]; vien?: string }) {
  if (!dong.length) return <div className="px-3 py-2 text-[12.5px] italic text-steel-500">(không có dòng nào)</div>;
  const cot = COT.filter((c) => dong.some((d) => d[c] !== null && d[c] !== undefined && d[c] !== ""));
  return (
    <div className={cx("overflow-x-auto rounded-lg border", vien || "border-steel-200")}>
      <table className="w-full text-[12.5px]">
        <thead className="bg-steel-50 text-left text-steel-600">
          <tr>{cot.map((c) => <th key={c} className="px-2.5 py-1.5 font-semibold">{NHAN[c] || c}</th>)}</tr>
        </thead>
        <tbody>
          {dong.map((d, i) => (
            <tr key={i} className="border-t border-steel-100">
              {cot.map((c) => (
                <td key={c} className={cx("px-2.5 py-1.5", c === "Amount" && "text-right tabular-nums")}>
                  {c === "Amount" ? fso(Number(d[c])) : String(d[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function O({ ky_hieu, nhan, so, mau }: { ky_hieu: string; nhan: string; so: number; mau: string }) {
  return (
    <div className={cx("rounded-xl border px-3 py-2", mau)}>
      <div className="text-[12px] font-medium opacity-80">{ky_hieu} {nhan}</div>
      <div className="text-[19px] font-bold tabular-nums">{so}</div>
    </div>
  );
}

export default function ManThayDoi({ onQuayLai }: { onQuayLai: () => void }) {
  const toast = useToast();
  const [pv, setPv] = useState<"dang_xem" | "tat_ca">("dang_xem");
  const [kq, setKq] = useState<KetQua | null>(null);
  const [loi, setLoi] = useState("");
  const [dangChay, setDangChay] = useState(false);
  const [bung, setBung] = useState<Record<string, boolean>>({});

  const tai = useCallback(async (phamVi: string) => {
    setDangChay(true); setLoi(""); setKq(null);
    const r = await A.goi("thay_doi_tu_khi_chot", phamVi);
    setDangChay(false);
    if (laLoi(r)) { setLoi(r.loi); return; }
    setKq(r as unknown as KetQua);
  }, []);
  useEffect(() => { tai(pv); }, [tai, pv]);

  const xuat = async () => {
    const r = await A.goi("xuat_thay_doi", pv);
    toast(laLoi(r) ? r.loi : "Đã xuất: " + r.path);
  };

  const t = kq?.tom_tat;
  return (
    <div className="mx-auto w-full max-w-[1400px] px-5 py-4">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Nut bien="phu" onClick={onQuayLai}><Icon d={IC.chevL} className="h-4 w-4" />Quay lại</Nut>
        <h2 className="ml-1 text-[17px] font-bold text-ink">Thay đổi từ khi chốt</h2>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex overflow-hidden rounded-lg border border-steel-300">
            {([["dang_xem", "Chi nhánh đang xem"], ["tat_ca", "Tất cả chi nhánh"]] as const).map(([id, nhan]) => (
              <button key={id} onClick={() => setPv(id)}
                className={cx("px-3 py-1.5 text-[12.5px] font-medium",
                  pv === id ? "bg-navy text-white" : "bg-white text-steel-600 hover:bg-steel-50")}>
                {nhan}
              </button>
            ))}
          </div>
          <Nut onClick={() => tai(pv)} disabled={dangChay}>
            <Icon d={IC.clock} className="h-4 w-4" />Làm mới
          </Nut>
          <Nut bien="chinh" onClick={xuat} disabled={!kq}>
            <Icon d={IC.taiXuong} className="h-4 w-4" />Xuất Excel
          </Nut>
        </div>
      </div>

      {dangChay && <div className="rounded-xl border border-steel-200 bg-white px-4 py-3 text-[13px]">Đang đối chiếu…</div>}

      {loi && (
        <div className="flex items-start gap-2 rounded-xl border border-vang-vien bg-vang-nen px-3 py-2.5 text-[12.5px] text-vang-dam">
          <Icon d={IC.warn} className="mt-0.5 h-4 w-4 shrink-0 text-vang" /><span>{loi}</span>
        </div>
      )}

      {t && (
        <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <O ky_hieu="＋" nhan="Chứng từ thêm" so={t.ct_them} mau="border-vang-vien bg-vang-nen text-vang-dam" />
          <O ky_hieu="－" nhan="Chứng từ bớt" so={t.ct_bot} mau="border-do-vien bg-do-nen text-do-dam" />
          <O ky_hieu="✎" nhan="Chứng từ bị sửa" so={t.ct_sua} mau="border-vang-vien bg-vang-nen text-vang-dam" />
          <O ky_hieu="◆" nhan="Tài khoản CĐPS đổi" so={t.tk_doi} mau="border-steel-300 bg-white text-ink" />
        </div>
      )}

      {kq?.don_vi.map((d) => {
        const c = d.chung_tu;
        const sach = !c.tom_tat.ct_them && !c.tom_tat.ct_bot && !c.tom_tat.ct_sua && !d.cdps;
        return (
          <section key={d.chi_nhanh} className="mb-4 rounded-xl border border-steel-200 bg-white p-4 shadow-soft">
            <div className="mb-3 flex flex-wrap items-baseline gap-2">
              <h3 className="text-[15px] font-bold text-ink">{d.chi_nhanh_ten}</h3>
              <span className="text-[12.5px] text-steel-500">
                kỳ {d.ky} · chốt lúc {String(d.thoi_diem_chot).replace("T", " ")}
              </span>
              {sach && (
                <span className="ml-auto rounded-full bg-xanh-nen px-2.5 py-0.5 text-[12px] font-semibold text-xanh-dam">
                  ✓ Không có gì đổi kể từ khi chốt
                </span>
              )}
            </div>

            {!!c.tom_tat.ct_sua && (
              <div className="mb-3">
                <div className="mb-1.5 text-[13px] font-semibold text-ink">✎ Chứng từ bị sửa ({c.tom_tat.ct_sua})</div>
                {c.sua.map((s) => {
                  const mo = bung[d.chi_nhanh + s.so_ct];
                  return (
                    <div key={s.so_ct} className="mb-1.5 rounded-lg border border-vang-vien bg-vang-nen/40">
                      <button onClick={() => setBung((b) => ({ ...b, [d.chi_nhanh + s.so_ct]: !mo }))}
                        className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] font-medium text-vang-dam">
                        <span className="tabular-nums">{mo ? "▾" : "▸"}</span>
                        <span>{s.so_ct}</span>
                        <span className="ml-auto text-[12px] opacity-75">
                          {s.dong_cu.length} dòng trước · {s.dong_moi.length} dòng sau
                        </span>
                      </button>
                      {mo && (
                        <div className="space-y-2 px-3 pb-3">
                          <div>
                            <div className="mb-1 text-[12px] font-semibold text-steel-600">Trước khi sửa</div>
                            <BangDong dong={s.dong_cu} vien="border-do-vien" />
                          </div>
                          <div>
                            <div className="mb-1 text-[12px] font-semibold text-steel-600">Sau khi sửa</div>
                            <BangDong dong={s.dong_moi} vien="border-vang-vien" />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {!!c.tom_tat.ct_them && (
              <div className="mb-3">
                <div className="mb-1.5 text-[13px] font-semibold text-ink">＋ Chứng từ thêm mới ({c.tom_tat.ct_them})</div>
                <BangDong dong={c.them} vien="border-vang-vien" />
              </div>
            )}
            {!!c.tom_tat.ct_bot && (
              <div className="mb-3">
                <div className="mb-1.5 text-[13px] font-semibold text-ink">－ Chứng từ đã mất ({c.tom_tat.ct_bot})</div>
                <BangDong dong={c.bot} vien="border-do-vien" />
              </div>
            )}

            <div>
              <div className="mb-1.5 text-[13px] font-semibold text-ink">◆ Chỉ số CĐPS</div>
              {!d.co_cdps_chot ? (
                <div className="rounded-lg border border-steel-200 bg-steel-50 px-3 py-2 text-[12.5px] text-steel-600">
                  – Bản chốt này không kèm CĐPS (chốt trước bản cập nhật, hoặc chốt khi chưa nạp CĐPS)
                  — không có mốc để đối chiếu.
                </div>
              ) : !d.cdps ? (
                <div className="rounded-lg border border-xanh-vien bg-xanh-nen px-3 py-2 text-[12.5px] text-xanh-dam">
                  ✓ Không tài khoản nào đổi số so với lúc chốt
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-vang-vien">
                  <table className="w-full text-[12.5px]">
                    <thead className="bg-steel-50 text-left text-steel-600">
                      <tr>
                        <th className="px-2.5 py-1.5 font-semibold">Tài khoản</th>
                        <th className="px-2.5 py-1.5 font-semibold">Thay đổi</th>
                        <th className="px-2.5 py-1.5 font-semibold">Cột lệch</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.cdps.dong.map((r, i) => (
                        <tr key={i} className="border-t border-steel-100">
                          <td className="px-2.5 py-1.5 font-medium">{r.account}</td>
                          <td className="px-2.5 py-1.5">
                            {r.kieu === "đổi" ? "✎ Đổi" : r.kieu === "thêm" ? "＋ Thêm" : "－ Mất"}
                          </td>
                          <td className="px-2.5 py-1.5 text-steel-600">{r.cot || ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
