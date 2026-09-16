/* Kiểm tra khóa sổ – frontend thuần, giao tiếp qua window.pywebview.api */
const $ = (id) => document.getElementById(id);
let api = null;
let ketQua = null;              // kết quả chay_kiem_tra
let fileHienTai = null;         // {path, ten, ky, so_dong, tong_ps}
let chiTiet = { ma: null, tieuDe: "", trang: 1, timKiem: "" };
const KICH_THUOC = 100;

const fmt = (n) => Number(n || 0).toLocaleString("vi-VN", { maximumFractionDigits: 0 });
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

/* ---------- biểu tượng nội tuyến ----------
   Emoji cũ (dấu tích, dấu chéo, tam giác cảnh báo, dấu trừ, biểu đồ cột) đã bị
   bỏ hẳn khỏi cả ba file web: mỗi máy vẽ một kiểu và không thừa kế
   được màu của trạng thái. Thay bằng một họ SVG duy nhất — 24x24, nét 1.75,
   fill none, đầu/góc bo tròn, stroke="currentColor" nên tự lấy màu token của
   trạng thái bao quanh. Chuỗi trong HINH là hằng của chính file này (không
   phải dữ liệu backend) nên đưa vào innerHTML là an toàn. */
const HINH = {
  "kiem": '<circle cx="12" cy="12" r="9"/><path d="m8.4 12.3 2.5 2.5 4.7-5.1"/>',
  "loi": '<circle cx="12" cy="12" r="9"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
  "canh-bao": '<path d="M10.3 4.3 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0Z"/><path d="M12 9.5v4.2"/><path d="M12 17.2h.01"/>',
  "bo-qua": '<circle cx="12" cy="12" r="9"/><path d="M8.3 12h7.4"/>',
  "hoi": '<circle cx="12" cy="12" r="9"/><path d="M9.1 9.2a3 3 0 0 1 5.5 1.6c0 2-3 2.6-3 4.2"/><path d="M12 17.3h.01"/>',
  "thong-ke": '<path d="M3 3v18h18"/><path d="M8 17v-6.5"/><path d="M13 17V6.5"/><path d="M18 17v-3.5"/>',
  "bang-tinh": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v5h5"/><path d="M8 13h2"/><path d="M14 13h2"/><path d="M8 17h2"/><path d="M14 17h2"/>',
  "tim-kiem": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.9-3.9"/>',
  "mui-phai": '<path d="m9 6 6 6-6 6"/>',
  "mui-trai": '<path d="m15 6-6 6 6 6"/>',
  "tai-ve": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  "thu-muc": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9L9.6 3.9A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  "lam-lai": '<path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"/><path d="M3 12a9 9 0 0 1 15.4-6.4L21 8"/><path d="M21 3v5h-5"/><path d="M3 21v-5h5"/>',
  "chep": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  "khoa": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
};
const bieuTuong = (ten, lop = "icon") =>
  `<svg class="${lop}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"` +
  ` stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${HINH[ten] || ""}</svg>`;

const ICON_TT = { da_lam: "kiem", chua_lam: "loi", can_ra: "canh-bao", khong_ap_dung: "bo-qua", tu_xac_nhan: "hoi" };
const NHAN_TT = { da_lam: "Đã làm", chua_lam: "Chưa làm", can_ra: "Cần rà", khong_ap_dung: "Không áp dụng", tu_xac_nhan: "Tự xác nhận" };
const NHAN_MD = { do: "Nghiêm trọng", vang: "Cảnh báo", xanh: "Đạt" };
const ICON_MD = { do: "loi", vang: "canh-bao", xanh: "kiem" };
const CLASS_MD = { do: "cham-do", vang: "cham-vang", xanh: "cham-xanh" };
const CLASS_KET_LUAN = { chua_san_sang: "chua-san-sang", can_ra_soat: "can-ra-soat", san_sang: "san-sang" };
const ICON_KET_LUAN = { chua_san_sang: "loi", can_ra_soat: "canh-bao", san_sang: "kiem" };
/* Khóa mọi khóa do backend cấp về tập đã biết trước khi ghép vào tên class —
   giao diện không bao giờ dựng selector từ chuỗi lạ. */
const khoaTT = (v) => (ICON_TT[v] ? v : "khong_ap_dung");
const khoaMD = (v) => (NHAN_MD[v] ? v : "xanh");
const khoaKL = (v) => (CLASS_KET_LUAN[v] ? v : "chua_san_sang");

/* ---------- tiến trình ----------
   Giai đoạn đọc Excel (~8,4 s trên file 79.450 dòng) chặn hẳn luồng Python:
   không một lệnh evaluate_js nào tới được trình duyệt trong lúc đó, nên thanh
   chạy theo phần trăm bắt buộc đứng im ở giá trị JS đặt trước khi await — đúng
   hiện tượng khách báo. Vì vậy:
     - pct không phải số dương  -> chế độ KHÔNG XÁC ĐỊNH: vệt sáng chạy bằng
       CSS animation của trình duyệt, chuyển động không phụ thuộc Python;
     - pct > 0 (giai đoạn 37 check, callback tới thật) -> thanh phần trăm thật.
   Cả hai chế độ đều kèm chữ mô tả pha + aria-busy, không bao giờ chỉ có
   chuyển động làm tín hiệu "đang chạy". */
function datTienTrinh(nhan, pct) {
  const nen = $("tien-trinh-nen");
  const thanh = $("tien-trinh-thanh");
  $("tien-trinh").classList.remove("an");
  $("tien-trinh-ten").textContent = nhan;
  nen.setAttribute("aria-busy", "true");
  const xacDinh = typeof pct === "number" && isFinite(pct) && pct > 0;
  nen.classList.toggle("khong-xac-dinh", !xacDinh);
  if (xacDinh) {
    const p = Math.max(0, Math.min(100, Math.round(pct)));
    thanh.style.transform = `scaleX(${p / 100})`;
    $("tien-trinh-pct").textContent = p + "%";
    nen.setAttribute("aria-valuenow", String(p));
    nen.setAttribute("aria-valuetext", p + "%");
  } else {
    thanh.style.transform = "";
    $("tien-trinh-pct").textContent = "Đang xử lý…";
    nen.removeAttribute("aria-valuenow");
    nen.setAttribute("aria-valuetext", "Đang xử lý, chưa đo được tiến độ");
  }
}
function anTienTrinh() {
  $("tien-trinh").classList.add("an");
  $("tien-trinh-nen").setAttribute("aria-busy", "false");
}
function onTienTrinh(ten, pct) { datTienTrinh(ten, pct); }
window.onTienTrinh = onTienTrinh;

/* Đọc file (~85% thời gian chờ) không tự phát tiến trình cho tới khi xong — phải mở
   thanh & khóa nút "Kiểm tra" TRƯỚC khi await, nếu không cửa sổ đứng im suốt lúc đó.
   hamGoiApi có thể trả về null (vd người dùng bấm Huỷ hộp thoại chọn file) hoặc {loi}. */
async function taiFile(hamGoiApi, nhanBatDau) {
  const nutKiemTra = $("btn-kiem-tra");
  const dangDisable = nutKiemTra.disabled;
  nutKiemTra.disabled = true;
  datTienTrinh(nhanBatDau);          // không truyền pct -> chế độ không xác định
  try {
    return await hamGoiApi();
  } finally {
    anTienTrinh();
    nutKiemTra.disabled = dangDisable;   // hienFile() sẽ mở lại nếu nạp thành công
  }
}

/* ---------- sao chép ----------
   Công việc thật của công cụ này kết thúc ở chỗ kế toán cầm được số chứng từ
   (PX2608-000366) mang sang Bravo tra. Nguyên nhân gốc khiến trước đây không
   chép được nằm ở app/main.py (pywebview tiêm user-select: none); phần dưới là
   những lối chép NGẮN hơn cả bôi đen: bấm một ô, chép một dòng, chép cả trang.

   navigator.clipboard trước, document.execCommand('copy') dự phòng: đây là
   webview nhúng, không bảo đảm Async Clipboard API luôn có (ngữ cảnh không an
   toàn, chính sách quyền của WebView2…). Cả hai hỏng thì PHẢI nói ra — im lặng
   là kiểu hỏng tệ nhất cho thao tác chép. */
function chepDuPhong(s) {
  const o = document.createElement("textarea");
  o.value = s;
  o.setAttribute("readonly", "");
  // Không dùng display:none / hidden: phần tử phải thật sự được vẽ thì select() mới chạy.
  o.style.cssText = "position:fixed;top:0;left:0;width:1px;height:1px;padding:0;border:0;opacity:0";
  document.body.append(o);
  const boiDen = document.getSelection();
  const truoc = boiDen && boiDen.rangeCount ? boiDen.getRangeAt(0) : null;
  o.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  o.remove();
  if (truoc && boiDen) { boiDen.removeAllRanges(); boiDen.addRange(truoc); }
  return ok;
}

async function chep(s) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(s);
      return true;
    }
  } catch (e) { /* hết quyền hoặc không có ngữ cảnh an toàn -> thử execCommand */ }
  return chepDuPhong(s);
}

/* Chép + báo thành lời. Phản hồi đi qua toast (role="status", aria-live) nên
   trình đọc màn hình cũng nghe được, không chỉ thấy màu. */
async function chepVaBao(s, moTa, nhayVao) {
  if (!s) { toast("Ô này không có dữ liệu để chép"); return false; }
  const ok = await chep(s);
  if (ok) {
    toast("Đã chép " + moTa);
    if (nhayVao) {
      nhayVao.classList.add("da-chep");
      clearTimeout(nhayVao._tChep);
      nhayVao._tChep = setTimeout(() => nhayVao.classList.remove("da-chep"), 800);
    }
  } else {
    toast("Không chép được vào bộ nhớ tạm — hãy bôi đen bằng chuột rồi nhấn Ctrl+C");
  }
  return ok;
}

/* TAB phân tách + có dòng tiêu đề = dán thẳng vào Excel thành đúng cột.
   Đọc ngược từ DOM chứ không từ dữ liệu thô: cái người dùng nhìn thấy (số đã
   định dạng kiểu Việt Nam, ngày dd/mm/yyyy, "Có"/"Không") đúng là cái được chép.
   Tab/xuống dòng lọt vào ô sẽ phá cấu trúc TSV nên bị gộp thành dấu cách. */
const _sach = (v) => String(v).replace(/\s+/g, " ").trim();
const _oCuaDong = (tr) =>
  [...tr.children].filter((o) => !o.classList.contains("o-chep")).map((o) => _sach(o.textContent));
function _tieuDeBang(bang) {
  const h = bang.querySelector("thead tr");
  return h ? _oCuaDong(h) : [];
}
// bang mặc định là bảng chi tiết — modal "Xem thay đổi" truyền bảng của chính nó
// (#bang-diff) để chép đúng tiêu đề cột của bảng đang mở, không lẫn sang bảng kia.
function tsv(dsDong, bang = $("bang-chi-tiet")) {
  const tieu = _tieuDeBang(bang);
  return [tieu, ...dsDong].filter((h) => h.length).map((h) => h.join("\t")).join("\n");
}

/* ---------- toast ---------- */
function toast(msg, nut = []) {
  const t = $("toast");
  t.innerHTML = "";
  t.append(Object.assign(document.createElement("span"), { textContent: msg }));
  nut.forEach(({ ten, icon, onClick }) => {
    const b = document.createElement("button");
    b.className = "btn"; b.type = "button";
    b.innerHTML = bieuTuong(icon);               // chỉ hằng nội bộ
    b.append(document.createTextNode(ten));
    b.onclick = onClick;
    t.append(b);
  });
  t.classList.remove("an");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.add("an"), nut.length ? 12000 : 4000);
}

/* ---------- màn hình 1 ---------- */
function hienFile(info) {
  if (!info || info.loi) { toast(info?.loi || "Không đọc được file"); return; }
  fileHienTai = info;
  const dv = info.don_vi || [];
  const nhieu = dv.length > 1;
  // Tên thẻ nói theo cái người dùng vừa làm: một chi nhánh thì nêu tên chi nhánh,
  // nhiều chi nhánh thì nêu số lượng — không dồn 12 mã vào một dòng rồi tràn.
  $("file-ten").textContent = nhieu
    ? `${dv.length} chi nhánh · ${info.so_file} file` : info.ten;
  $("file-ky").textContent = info.ky;
  $("file-so-dong").textContent = fmt(info.so_dong); $("file-tong-ps").textContent = fmt(info.tong_ps);

  const ul = $("ds-don-vi-nap"); ul.innerHTML = "";
  ul.classList.toggle("an", !nhieu);
  if (nhieu) {
    dv.forEach((u) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="dv-ma">${esc(u.ma)}</span>
        <span class="dv-nguon">${esc(u.nguon)}</span>
        <span class="dv-so so">${fmt(u.so_dong)} dòng</span>
        <span class="dv-ky so">kỳ ${esc(u.ky)}</span>`;
      ul.append(li);
    });
  }
  $("the-file").classList.remove("an"); $("btn-kiem-tra").disabled = false;
  $("header-file").textContent = nhieu
    ? `${dv.length} chi nhánh · kỳ ${info.ky}` : `${info.ten} · kỳ ${info.ky}`;
}

async function khoiTao() {
  api = window.pywebview.api;
  // KHÔNG tự nạp file mặc định: người dùng luôn tự chọn (kéo-thả / "Chọn file…" /
  // "Nạp cả thư mục"). Tránh nạp nhầm file cũ hay file không phải bảng kê rồi báo lỗi
  // ngay khi mở. Màn hình 1 (chọn file) là màn mặc định nên không cần làm gì thêm.
}

$("btn-chon-file").onclick = async () => {
  // allow_multiple: chọn được nhiều file trong cùng một lần mở hộp thoại.
  const info = await taiFile(() => api.chon_nhieu_file(), "Đang đọc file…");
  if (!info) return;              // người dùng bấm Huỷ — không phải lỗi
  hienFile(info);
};

$("btn-quet-thu-muc").onclick = async () => {
  hienFile(await taiFile(() => api.quet_thu_muc(), "Đang quét thư mục '1. Source'…"));
};

const vung = $("vung-keo-tha");
["dragenter", "dragover"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.add("keo-qua"); }));
["dragleave", "drop"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.remove("keo-qua"); }));
vung.addEventListener("drop", async (ev) => {
  // Kéo NHIỀU file cùng lúc = nhiều chi nhánh. Chỉ lấy file có đường dẫn thật;
  // nếu kéo 5 file mà chỉ 3 file lấy được đường dẫn thì phải nói ra, không thể
  // lặng lẽ kiểm tra 3 chi nhánh rồi để người dùng tưởng đã đủ 5.
  const ds = [...ev.dataTransfer.files];
  const path = ds.map((f) => f.pywebviewFullPath).filter(Boolean);
  if (!path.length) { toast("Không lấy được đường dẫn file — hãy dùng nút 'Chọn file…'"); return; }
  if (path.length < ds.length) toast(`Chỉ lấy được đường dẫn của ${path.length}/${ds.length} file đã kéo`);
  hienFile(await taiFile(() => api.nap_nhieu_file(path),
    path.length > 1 ? `Đang đọc ${path.length} file…` : "Đang đọc file…"));
});

$("btn-kiem-tra").onclick = chayKiemTra;
async function chayKiemTra() {
  $("btn-kiem-tra").disabled = true;
  // Lần gọi này có thể phải đọc lại Excel trước khi chạy check -> mở ở chế độ
  // không xác định; onTienTrinh sẽ tự chuyển sang phần trăm khi số thật tới.
  datTienTrinh("Đang chuẩn bị kiểm tra…");
  try {
    // Gửi CẢ danh sách đường dẫn: gửi mỗi file đầu sẽ khiến backend coi là đã đổi
    // lựa chọn rồi nạp lại một mình nó, vứt mất các chi nhánh còn lại.
    const kq = await api.chay_kiem_tra(fileHienTai?.cac_path || null);
    if (kq.loi) { toast(kq.loi); return; }
    ketQua = kq; veKetQua(); chuyenManHinh(2);
  } finally {
    $("btn-kiem-tra").disabled = false; anTienTrinh();
  }
}

function chuyenManHinh(n) {
  $("man-hinh-1").classList.toggle("an", n !== 1);
  $("man-hinh-2").classList.toggle("an", n !== 2);
}

/* ---------- màn hình 2 ---------- */
function veKetQua() {
  const t = ketQua.tomtat;
  const muc = khoaKL(t.muc_do_ket_luan);
  $("banner").className = "banner " + CLASS_KET_LUAN[muc];
  $("banner-icon").innerHTML = bieuTuong(ICON_KET_LUAN[muc], "icon icon-banner");
  $("banner-ket-luan").textContent = t.cau_ket_luan;
  const nhieu = (ketQua.don_vi || []).length > 1;
  // Khi có nhiều chi nhánh, tên chi nhánh phải đứng đầu dòng phụ: mọi con số bên
  // dưới chỉ đúng cho MỘT chi nhánh, đọc nhầm sang chi nhánh khác là sai hoàn toàn.
  $("banner-ky").textContent = (nhieu ? `Chi nhánh ${t.chi_nhanh} · ` : "")
    + `Kỳ ${t.ky} · ${t.ten} · ${fmt(t.so_dong)} dòng`;
  $("so-do").textContent = fmt(t.so_do); $("so-vang").textContent = fmt(t.so_vang);
  const tongCheck = ketQua.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke).length;
  $("so-xanh").textContent = fmt(tongCheck - t.so_do - t.so_vang);
  $("khoi-chot-so").innerHTML = veKhoiChot(t.chot);
  $("banner-drift").innerHTML = veBannerDrift(t.chot);
  veThanhDonVi(); veTabA(); veTabB(); anChiTiet();
}

/* Khối "Chốt sổ" dưới banner kết luận — thuộc về CHI NHÁNH đang xem (t.chot), không
   phải toàn bộ file, đúng như banner phía trên nó. Hai trạng thái loại trừ nhau:
   chưa chốt (một nút chính) hoặc đã chốt (thẻ xanh + hai nút phụ). Khi đã chốt mà
   dữ liệu nguồn lệch so với bản đã chốt (doi_chieu === "LECH") thì thêm một dòng
   cảnh báo vàng — KHÔNG đổi màu cả thẻ, vì bản thân việc "đã chốt" vẫn đúng. */
function veKhoiChot(chot) {
  const khoa = bieuTuong("khoa", "icon icon-nho");
  if (chot && chot.trang_thai === "DA_CHOT") {
    const ngay = chot.ngay_chot ? new Date(chot.ngay_chot).toLocaleString("vi-VN") : "";
    const canhBao = chot.doi_chieu === "LECH"
      ? `<div class="chot-lech">${bieuTuong("canh-bao", "icon icon-nho")}Dữ liệu nguồn đã khác bản đã chốt</div>`
      : "";
    return `<div class="khoi-chot da-chot">
      <div class="khoi-chot-dong">${khoa}<b>Đã chốt</b>${ngay ? " " + esc(ngay) : ""}${chot.ghi_chu ? " · " + esc(chot.ghi_chu) : ""}</div>
      ${canhBao}
      <div class="hang-nut">
        <button class="btn btn-phu" type="button" onclick="moLaiKy()">Mở lại kỳ</button>
        <button class="btn btn-phu" type="button" onclick="moModalChot(true)">Chốt lại</button>
      </div></div>`;
  }
  return `<div class="khoi-chot">
    <button class="btn btn-chinh" type="button" onclick="moModalChot(false)">${khoa}Chốt sổ kỳ này</button>
  </div>`;
}

/* Banner đối chiếu với bản đã chốt — RIÊNG với khối "Chốt sổ" ở trên vì trả lời
   một câu hỏi khác: dữ liệu NGUỒN (file Excel) có còn khớp với ảnh đã đóng băng
   lúc chốt hay không. Chưa chốt thì không có gì để đối chiếu -> im lặng. Đã chốt
   & khớp -> dải xanh ngắn, không cần làm gì. Đã chốt & lệch -> băng cam nổi bật
   hơn hẳn khối "Chốt sổ", vì đây là việc kế toán cần xử lý trước khi tin vào kết
   luận đã chốt. Không tự suy luận gì thêm ngoài chot.doi_chieu backend trả về. */
function veBannerDrift(chot) {
  if (!chot || chot.trang_thai !== "DA_CHOT") return "";
  if (chot.doi_chieu === "KHOP") {
    const ngay = chot.ngay_chot ? new Date(chot.ngay_chot).toLocaleDateString("vi-VN") : "";
    return `<div class="dai-khop">${bieuTuong("kiem", "icon icon-nho")}` +
      `Dữ liệu khớp bản đã chốt${ngay ? " " + esc(ngay) : ""}</div>`;
  }
  if (chot.doi_chieu !== "LECH") return "";
  const t = chot.tom_tat_lech || {};
  const dDong = t.delta_dong || 0;
  const dPs = t.delta_ps || 0;
  return `<div class="banner-lech">
    <div class="banner-lech-dau">${bieuTuong("canh-bao", "icon icon-nho")}Kỳ đã chốt nhưng dữ liệu nguồn đã thay đổi</div>
    <div class="banner-lech-chi-tiet">Δ dòng: <b>${dDong > 0 ? "+" : ""}${fmt(dDong)}</b> ·
      Δ tổng phát sinh: <b>${dPs > 0 ? "+" : ""}${fmt(dPs)}</b> ·
      <b>${fmt(t.so_ct_anh_huong || 0)}</b> chứng từ ảnh hưởng</div>
    <div class="hang-nut">
      <button class="btn btn-phu" type="button" onclick="moModalDiff()">Xem thay đổi</button>
      <button class="btn btn-chinh" type="button" onclick="capNhatChotLai()">Cập nhật &amp; chốt lại</button>
    </div>
  </div>`;
}

/* ---------- modal chốt sổ ----------
   Số liệu trong modal luôn đọc lại từ ketQua.tomtat của CHI NHÁNH ĐANG XEM tại thời
   điểm bấm nút (không chụp lại lúc mở màn kết quả) — nếu người dùng vừa đổi chi
   nhánh trên thanh chọn rồi mới bấm "Chốt sổ", modal phải nói đúng chi nhánh đó. */
function moModalChot(chotLai) {
  const t = ketQua?.tomtat || {};
  $("modal-chot-tieu-de").textContent = chotLai ? "Chốt lại kỳ này" : "Chốt sổ kỳ này";
  $("modal-chot-thong-tin").innerHTML =
    `Kỳ <b>${esc(t.ky)}</b> · Chi nhánh <b>${esc(t.chi_nhanh)}</b><br/>` +
    `Số dòng: <b>${fmt(t.so_dong)}</b> · Tổng phát sinh: <b>${fmt(t.tong_ps)}</b><br/>` +
    `Kết luận: <b>${esc(t.cau_ket_luan || "")}</b>`;
  $("modal-chot-ghi-chu").value = "";
  $("modal-chot").classList.remove("an");
  $("modal-chot-ghi-chu").focus();
}
function dongModalChot() { $("modal-chot").classList.add("an"); }

/* Sau khi chốt/mở lại, KHÔNG gọi lại chayKiemTra() (nó đọc lại Excel từ đầu) — chỉ
   xin lại gói tóm tắt của đúng chi nhánh đang xem qua chon_don_vi(), backend tính
   lại chot dựa trên kho vừa ghi rồi trả về, JS dựng lại màn hình từ đó. */
async function xacNhanChot() {
  const ghiChu = $("modal-chot-ghi-chu").value.trim();
  const kq = await api.chot_so(ghiChu);
  if (kq.loi) { toast(kq.loi); return; }
  dongModalChot();
  const kq2 = await api.chon_don_vi(ketQua.dang_xem);
  if (kq2.loi) { toast(kq2.loi); return; }
  ketQua = kq2; veKetQua();
  toast("Đã chốt sổ kỳ này");
}
async function moLaiKy() {
  if (!confirm("Mở lại kỳ này? Bản đã chốt vẫn được giữ trong lịch sử.")) return;
  const kq = await api.mo_lai_ky();
  if (kq.loi) { toast(kq.loi); return; }
  const kq2 = await api.chon_don_vi(ketQua.dang_xem);
  if (kq2.loi) { toast(kq2.loi); return; }
  ketQua = kq2; veKetQua();
  toast("Đã mở lại kỳ");
}

/* Nút chính của banner-lech: đóng băng dữ liệu NGUỒN hiện tại làm bản chốt mới,
   thay cho bản cũ đã lệch — bản cũ vẫn nằm trong lịch sử (Task 10), không mất gì. */
async function capNhatChotLai() {
  if (!confirm("Đóng băng dữ liệu MỚI làm bản chốt hiện hành? Bản cũ vẫn được giữ trong lịch sử."))
    return;
  const kq = await api.chot_so("Cập nhật dữ liệu mới");
  if (kq.loi) { toast(kq.loi); return; }
  const kq2 = await api.chon_don_vi(ketQua.dang_xem);
  if (kq2.loi) { toast(kq2.loi); return; }
  ketQua = kq2; veKetQua();
  toast("Đã cập nhật và chốt lại kỳ này");
}

/* Thanh chọn chi nhánh. Ẩn hẳn khi chỉ một chi nhánh. Khi nhiều: một dòng TÓM TẮT
   (đếm theo mức độ) + dải thẻ SẮP THEO MỨC ĐỘ NẶNG — chi nhánh cần xử lý nằm bên
   trái, nhìn thấy trước. Mỗi thẻ có chấm màu + nhãn việc, không chỉ dựa vào màu. */
/* Nhãn chốt ngắn gọn cho thẻ chi nhánh trên thanh chọn — ba trạng thái loại trừ
   nhau: chưa chốt (trung tính), đã chốt khớp (xanh), đã chốt nhưng dữ liệu nguồn
   đổi so với bản đã chốt (vàng, cần chú ý). Không tự suy luận gì thêm ngoài
   `chot` backend trả về — không có bản chốt thì luôn là "Chưa chốt", im lặng. */
function nhanChot(chot) {
  if (!chot || chot.trang_thai !== "DA_CHOT")
    return '<span class="chip-chot chua">Chưa chốt</span>';
  if (chot.doi_chieu === "LECH")
    return `<span class="chip-chot lech">${bieuTuong("canh-bao", "icon icon-nho")}Dữ liệu đã đổi</span>`;
  const ngay = (chot.ngay_chot || "").slice(8, 10) + "/" + (chot.ngay_chot || "").slice(5, 7);
  return `<span class="chip-chot khop">${bieuTuong("khoa", "icon icon-nho")}Đã chốt ${esc(ngay)}</span>`;
}

const HANG_KL = { chua_san_sang: 0, can_ra_soat: 1, san_sang: 2 };  // nặng -> nhẹ
function _soViec(u) {
  const muc = khoaKL(u.muc_do_ket_luan);
  if (muc === "chua_san_sang") return (u.so_do || 0) + (u.so_chua_lam || 0);
  if (muc === "can_ra_soat") return (u.so_vang || 0) + (u.so_can_ra || 0);
  return 0;
}
function _nhanViec(u) {
  const muc = khoaKL(u.muc_do_ket_luan);
  if (muc === "san_sang") return "Sẵn sàng";
  return `${fmt(_soViec(u))} ${muc === "chua_san_sang" ? "việc" : "cần rà"}`;
}
function veThanhDonVi() {
  const ds = ketQua.don_vi || [];
  const nhieu = ds.length > 1;
  const thanh = $("thanh-don-vi");
  thanh.classList.toggle("an", !nhieu);
  $("btn-xuat-tong-hop").classList.toggle("an", !nhieu);
  if (!nhieu) { thanh.innerHTML = ""; return; }

  // Đếm theo mức độ cho dòng tóm tắt — chỉ hiện mục có số > 0.
  const dem = { chua_san_sang: 0, can_ra_soat: 0, san_sang: 0 };
  ds.forEach((u) => { dem[khoaKL(u.muc_do_ket_luan)] += 1; });
  const nhanDem = [
    ["chua_san_sang", "chưa sẵn sàng", "dv-dem-do"],
    ["can_ra_soat", "cần rà soát", "dv-dem-vang"],
    ["san_sang", "sẵn sàng", "dv-dem-xanh"],
  ].filter(([k]) => dem[k] > 0)
    .map(([k, ten, lop]) => `<span class="dv-dem ${lop}">${dem[k]} ${ten}</span>`).join("");

  // Sắp nặng -> nhẹ, giữ thứ tự gốc trong cùng mức. Không đụng u.i (chon_don_vi cần).
  const sap = ds.map((u, thu_tu) => ({ u, thu_tu }))
    .sort((a, b) => (HANG_KL[khoaKL(a.u.muc_do_ket_luan)] - HANG_KL[khoaKL(b.u.muc_do_ket_luan)])
      || (a.thu_tu - b.thu_tu));

  const rail = sap.map(({ u }) => {
    const muc = khoaKL(u.muc_do_ket_luan);
    const dangXem = u.i === ketQua.dang_xem;
    return `<button type="button" class="chip-dv kl-${CLASS_KET_LUAN[muc]}${dangXem ? " dang-chon" : ""}"
        aria-pressed="${dangXem}" data-i="${u.i}"
        title="${esc(u.ma)} · kỳ ${esc(u.ky)} · ${esc(u.cau_ket_luan)}">
      <span class="chip-dv-cham" aria-hidden="true"></span>
      <span class="chip-dv-ma">${esc(u.ma)}</span>
      <span class="chip-dv-phu">${esc(_nhanViec(u))}</span>
      <span class="chip-dv-chot">${nhanChot(u.chot)}</span>
    </button>`;
  }).join("");

  thanh.innerHTML = `<div class="dv-tomtat">
      <span class="dv-tong">${ds.length} chi nhánh</span>${nhanDem}
    </div>
    <div class="dv-rail">${rail}</div>`;
  thanh.querySelectorAll(".chip-dv").forEach((b) => {
    b.onclick = () => doiDonVi(Number(b.dataset.i));
  });
}

async function doiDonVi(i) {
  if (i === ketQua.dang_xem) return;
  const kq = await api.chon_don_vi(i);
  if (kq.loi) { toast(kq.loi); return; }
  ketQua = kq; veKetQua();
  // Vùng cuộn giữ nguyên vị trí cũ sẽ khiến chi nhánh mới mở ra ở giữa danh sách —
  // đưa về đầu để bước 1 luôn là thứ nhìn thấy trước.
  $("vung-cuon").scrollTop = 0;
}

function veTabA() {
  const ul = $("ds-buoc"); ul.innerHTML = "";
  const dem = { da_lam: 0, chua_lam: 0, can_ra: 0, tu_xac_nhan: 0, khong_ap_dung: 0 };
  ketQua.trang_thai.forEach((b, i) => {
    const tt = khoaTT(b.trang_thai);
    dem[tt] += 1;
    // Bước "không áp dụng" (và bước suy ra không có bảng chứng minh) luôn mở ra bảng
    // rỗng — dựng bằng <div> không bấm được, để người dùng không bấm vào ngõ cụt.
    // Bước bấm được dựng bằng <button> thật: có focus ring và bàn phím miễn phí.
    const bamDuoc = tt !== "khong_ap_dung" && b.co_chung_cu !== false;
    const o = document.createElement(bamDuoc ? "button" : "div");
    o.className = `buoc tt-${tt}` + (bamDuoc ? " bam-duoc" : " khong-bam");
    if (bamDuoc) o.type = "button";
    o.innerHTML = `<span class="buoc-stt so">${i + 1}</span>
      <span class="buoc-icon">${bieuTuong(ICON_TT[tt])}</span>
      <span class="buoc-chu"><span class="ten">${esc(b.buoc)}</span><span class="tom-tat">${esc(b.tom_tat)}</span></span>
      <span class="chip-tt">${bieuTuong(ICON_TT[tt], "icon icon-nho")}${esc(NHAN_TT[tt])}</span>
      <span class="buoc-mo">${bamDuoc ? bieuTuong("mui-phai", "icon icon-nho") + '<span class="an-chu">Mở bảng chứng minh</span>' : ""}</span>`;
    if (bamDuoc) o.onclick = () => moChiTiet(b.ma_check, b.buoc + ` — chứng minh (${b.ma_check})`);
    const li = document.createElement("li"); li.append(o); ul.append(li);
  });
  $("tieu-de-buoc").textContent = `${ketQua.trang_thai.length} bước khóa sổ cuối kỳ`;
  // "tự xác nhận" phải nằm trong dòng đếm, nếu không tổng các mục < số bước và
  // kế toán tưởng thiếu bước. Chỉ hiện mục nào có số > 0 để dòng không rối.
  const phan = [[dem.da_lam, "đã làm"], [dem.chua_lam, "chưa làm"], [dem.can_ra, "cần rà"],
                [dem.tu_xac_nhan, "tự xác nhận"], [dem.khong_ap_dung, "không áp dụng"]];
  $("dem-buoc").textContent = phan.filter(([n]) => n > 0).map(([n, t]) => `${n} ${t}`).join(" · ");
}

function veTabB() {
  const luoi = $("luoi-nhom"); luoi.innerHTML = "";
  ketQua.nhom.forEach((n) => {
    const md = khoaMD(n.muc_do);
    const laTK = n.ma === "G6";
    const d = document.createElement("div"); d.className = `the-nhom nhom-${md}`;

    // Đầu thẻ là <button> riêng, danh sách check là các <button> riêng — không
    // lồng phần tử tương tác vào nhau, mọi đường vào đều đi được bằng bàn phím.
    const dau = document.createElement("button");
    dau.className = "the-nhom-dau"; dau.type = "button";
    dau.innerHTML = `<span><span class="the-nhom-ma">${esc(n.ma)}</span>
        <span class="the-nhom-ten">${esc(n.ten)}</span>
        <span class="the-nhom-phu">${bieuTuong(laTK ? "thong-ke" : ICON_MD[md], "icon icon-nho")}${
          laTK ? "Bảng thống kê" : esc(NHAN_MD[md])}</span></span>
      <span class="the-nhom-so so">${laTK ? bieuTuong("thong-ke", "icon icon-banner") : fmt(n.so_loi)}</span>`;
    dau.onclick = () => {
      const c = n.checks.find((x) => x.so_loi > 0) || n.checks[0];
      if (!c) return;
      chonThe(d); moChiTiet(c.ma, c.ma + " · " + c.ten);
    };
    d.append(dau);

    const ul = document.createElement("ul"); ul.className = "ds-check";
    n.checks.forEach((c) => {
      const b = document.createElement("button");
      b.className = "check-nut"; b.type = "button";
      b.innerHTML = `<i class="cham ${CLASS_MD[khoaMD(c.muc_do)]}" aria-hidden="true"></i>
        <span class="check-ten">${esc(c.ma)} ${esc(c.ten)}</span>
        <span class="check-so so">${c.la_thong_ke ? bieuTuong("thong-ke", "icon icon-nho") : fmt(c.so_loi)}</span>`;
      b.onclick = () => { chonThe(d); moChiTiet(c.ma, c.ma + " · " + c.ten + (c.ghi_chu ? " — " + c.ghi_chu : "")); };
      const li = document.createElement("li"); li.append(b); ul.append(li);
    });
    d.append(ul);
    luoi.append(d);
  });
}
function chonThe(d) { document.querySelectorAll(".the-nhom").forEach((x) => x.classList.remove("dang-chon")); d.classList.add("dang-chon"); }

/* ---------- chi tiết ---------- */
/* Dựng phần <thead>/<tbody> từ một gói dữ liệu dạng {tong,cot,nhan,cot_so,cot_so_le,dong}
   — DÙNG CHUNG cho bảng chi tiết (moChiTiet) và bảng "Xem thay đổi" (modal-diff),
   vì cả hai đọc đúng một shape cột/nhãn do backend cấp (app.checks.base.TEN_COT).
   Không lặp lại nhãn cột hay danh sách cột số ở đây. */
function dungNoiDungBang(kq, thongBaoRong) {
  if (!kq.tong) {
    return `<tbody><tr><td class="bang-trong">${bieuTuong("tim-kiem", "icon icon-to")}` +
      `<span>${thongBaoRong}</span></td></tr></tbody>`;
  }
  const cot = kq.cot || [];
  const nhan = kq.nhan || cot;
  const soCot = new Set(kq.cot_so || []);
  // Cột có phần thập phân (số lượng): làm tròn 0 chữ số biến 0,059 thành "0" —
  // đọc đúng thành "không có số lượng", ngược hẳn với dòng đang được nêu.
  const soLe = new Set(kq.cot_so_le || []);
  const fmtSo = (c, v) => soLe.has(c)
    ? Number(v).toLocaleString("vi-VN", { maximumFractionDigits: 9 }) : fmt(v);
  // Diễn giải chứng từ có thể dài vài trăm ký tự: kẹp còn 3 dòng để nhịp hàng
  // không vỡ trên bảng 30.000 dòng, chuỗi đầy đủ đưa vào title để rê chuột đọc.
  // Giá trị ngắn (số CT, ngày, số hiệu TK) không bao giờ được xuống dòng:
  // "PX2608-000366" bị bẻ làm đôi vừa khó đọc vừa khó bôi đen trúng một mã —
  // mà đây đúng là chuỗi kế toán cần mang sang Bravo.
  const oChu = (v) => {
    const s = String(v ?? "");
    const tip = s.length > 60 ? ` title="${esc(s)}"` : "";
    const lop = s.length <= 30 ? "o-chu o-ngan" : "o-chu";
    return `<td><span class="${lop}"${tip}>${esc(v)}</span></td>`;
  };
  const oDuLieu = (r, c) => typeof r[c] === "boolean" ? `<td>${r[c] ? "Có" : "Không"}</td>`
    : soCot.has(c) && typeof r[c] === "number" ? `<td class="so">${fmtSo(c, r[c])}</td>`
    : oChu(r[c]);
  // Cột đầu là nút chép cả dòng — <button> thật nên vào được bằng bàn phím và có
  // focus ring; luôn hiện (không chỉ khi rê chuột) để người dùng còn biết là có.
  // aria-label mang số thứ tự dòng do JS sinh, không phải chuỗi từ backend.
  const nutChep = (i) =>
    `<td class="o-chep"><button class="nut-chep" type="button" data-dong="${i}"` +
    ` aria-label="Chép cả dòng ${i + 1}" title="Chép cả dòng này (kèm tiêu đề cột)">` +
    `${bieuTuong("chep", "icon icon-nho")}</button></td>`;
  return `<thead><tr><th scope="col" class="o-chep"><span class="an-chu">Chép dòng</span></th>${
    cot.map((c, i) =>
      `<th scope="col" class="${soCot.has(c) ? "so" : ""}">${esc(nhan[i] ?? c)}</th>`).join("")}</tr></thead><tbody>${
    kq.dong.map((r, i) => `<tr>${nutChep(i)}${cot.map((c) => oDuLieu(r, c)).join("")}</tr>`).join("")}</tbody>`;
}

async function moChiTiet(ma, tieuDe, trang = 1) {
  // Giữ tiêu đề gốc trong state: tách lại từ DOM sẽ nuốt mất tên check ngay khi gõ tìm kiếm.
  chiTiet = { ma, tieuDe, trang, timKiem: chiTiet.ma === ma ? chiTiet.timKiem : "" };
  $("o-tim-kiem").value = chiTiet.timKiem;
  const kq = await api.lay_chi_tiet(ma, trang, KICH_THUOC, chiTiet.timKiem);
  if (kq.loi) { toast(kq.loi); return; }
  $("chi-tiet-tieu-de").textContent = tieuDe;
  $("chi-tiet-dem").textContent = `${fmt(kq.tong)} dòng${chiTiet.timKiem ? " khớp từ khóa" : ""}`;
  $("btn-chep-trang").disabled = !kq.tong;
  $("bang-chi-tiet").innerHTML = dungNoiDungBang(kq,
    chiTiet.timKiem ? "Không có dòng nào khớp từ khóa." : "Không có dòng nào.");
  vePhanTrangVao($("phan-trang"), kq.tong, trang, (t) => moChiTiet(chiTiet.ma, chiTiet.tieuDe, t));
  $("khung-chi-tiet").classList.remove("an");
  // Bảng chiếm trọn vùng kết quả -> danh sách lui đi (xem style.css .co-chi-tiet).
  $("vung-cuon").classList.add("co-chi-tiet");
}
function anChiTiet() {
  $("khung-chi-tiet").classList.add("an");
  $("vung-cuon").classList.remove("co-chi-tiet");
}

/* Bấm một ô = chép ô đó. Uỷ quyền trên <table> nên vẫn sống sau mỗi lần dựng lại
   innerHTML, và chỉ gắn MỘT lần khi nạp trang. DÙNG CHUNG cho bảng chi tiết và
   bảng "Xem thay đổi" (modal-diff) — cả hai đều được dựng bởi dungNoiDungBang()
   nên có cùng cấu trúc nút-chép-dòng/ô.
   Không được tranh chỗ với bôi đen: nếu con trỏ có di chuyển giữa mousedown và
   click (kéo để chọn), hoặc đang có sẵn một vùng bôi đen, thì đây là thao tác
   chọn chữ của người dùng — im lặng, không chép. */
function ganChepBang(bang) {
  let diemNhan = null;
  bang.addEventListener("mousedown", (ev) => { diemNhan = [ev.clientX, ev.clientY]; });
  bang.addEventListener("click", (ev) => {
    const nut = ev.target.closest(".nut-chep");
    if (nut) {
      const tr = nut.closest("tr");
      chepVaBao(tsv([_oCuaDong(tr)], bang), "cả dòng (kèm tiêu đề cột)", tr);
      return;
    }
    const o = ev.target.closest("td");
    if (!o || o.classList.contains("bang-trong")) return;
    const keo = diemNhan && (Math.abs(ev.clientX - diemNhan[0]) > 4 || Math.abs(ev.clientY - diemNhan[1]) > 4);
    const dangBoiDen = !(document.getSelection()?.isCollapsed ?? true);
    if (keo || dangBoiDen) return;
    const gt = o.textContent.trim();
    chepVaBao(gt, gt.length > 40 ? "ô này" : `“${gt}”`, o);
  });
}
ganChepBang($("bang-chi-tiet"));
ganChepBang($("bang-diff"));

/* Phân trang DÙNG CHUNG: nhận thẳng khung <div> đích và hàm đổi trang, để bảng
   chi tiết (gọi lại moChiTiet) và modal-diff (gọi lại taiDiff) không phải chia
   sẻ một state phân trang chung. */
function vePhanTrangVao(p, tong, trang, onDoiTrang) {
  const soTrang = Math.max(1, Math.ceil(tong / KICH_THUOC));
  p.innerHTML = "";
  const nut = (ten, icon, ben, t, tat) => {
    const b = document.createElement("button");
    b.className = "btn"; b.type = "button"; b.disabled = tat;
    const sv = bieuTuong(icon, "icon icon-nho");
    b.innerHTML = ben === "trai" ? sv : "";
    b.append(document.createTextNode(ten));
    if (ben === "phai") b.insertAdjacentHTML("beforeend", sv);
    b.onclick = () => onDoiTrang(t);
    return b;
  };
  const dau = tong ? (trang - 1) * KICH_THUOC + 1 : 0;
  const cuoi = Math.min(tong, trang * KICH_THUOC);
  p.append(nut("Trước", "mui-trai", "trai", trang - 1, trang <= 1),
    Object.assign(document.createElement("span"), { className: "so", textContent: `Trang ${fmt(trang)}/${fmt(soTrang)}` }),
    nut("Sau", "mui-phai", "phai", trang + 1, trang >= soTrang),
    Object.assign(document.createElement("span"), {
      className: "phan-trang-dem", textContent: `Dòng ${fmt(dau)}–${fmt(cuoi)} / ${fmt(tong)}` }));
}

$("o-tim-kiem").addEventListener("input", (ev) => {
  clearTimeout($("o-tim-kiem")._t);
  $("o-tim-kiem")._t = setTimeout(() => { chiTiet.timKiem = ev.target.value.trim();
    moChiTiet(chiTiet.ma, chiTiet.tieuDe, 1); }, 300);
});

$("btn-chep-trang").onclick = () => {
  const ds = [...$("bang-chi-tiet").querySelectorAll("tbody tr")]
    .filter((tr) => !tr.querySelector(".bang-trong")).map(_oCuaDong);
  if (!ds.length) { toast("Trang này không có dòng nào để chép"); return; }
  chepVaBao(tsv(ds), `${fmt(ds.length)} dòng của trang này (kèm tiêu đề cột)`);
};
$("btn-dong-chi-tiet").onclick = anChiTiet;

/* ---------- modal "Xem thay đổi" ----------
   Chỉ mở được từ banner-lech (chot.doi_chieu === "LECH") — liệt kê dòng thêm/bớt
   giữa dữ liệu nguồn hiện tại và bản đã chốt. Dùng LẠI dungNoiDungBang()/
   vePhanTrangVao()/ganChepBang() của bảng chi tiết vì backend trả cùng một shape
   {tong,trang,cot,nhan,cot_so,cot_so_le,dong}, chỉ thêm cột "Thay đổi". State
   riêng (_diff), không đụng vào chiTiet của bảng kia. */
let _diff = { trang: 1, timKiem: "" };
async function moModalDiff() {
  _diff = { trang: 1, timKiem: "" };
  $("diff-tim-kiem").value = "";
  $("modal-diff").classList.remove("an");
  await taiDiff();
}
function dongModalDiff() { $("modal-diff").classList.add("an"); }

async function taiDiff(trang = _diff.trang) {
  _diff.trang = trang;
  const kq = await api.lay_diff_chot(trang, KICH_THUOC, _diff.timKiem);
  if (kq.loi) { toast(kq.loi); return; }
  const tt = kq.tom_tat || {};
  $("diff-tom-tat").textContent =
    `Thêm ${fmt(tt.so_them)} · Bớt ${fmt(tt.so_bot)} · ${fmt(tt.so_ct_anh_huong)} chứng từ`;
  $("bang-diff").innerHTML = dungNoiDungBang(kq,
    _diff.timKiem ? "Không có dòng nào khớp từ khóa." : "Không có thay đổi nào.");
  vePhanTrangVao($("phan-trang-diff"), kq.tong, trang, (t) => taiDiff(t));
}

$("diff-tim-kiem").addEventListener("input", (ev) => {
  clearTimeout($("diff-tim-kiem")._t);
  $("diff-tim-kiem")._t = setTimeout(() => { _diff.timKiem = ev.target.value.trim(); taiDiff(1); }, 300);
});

/* ---------- tabs & footer ---------- */
$("tab-a").onclick = () => chuyenTab("a"); $("tab-b").onclick = () => chuyenTab("b");
function chuyenTab(t) {
  $("tab-a").classList.toggle("dang-chon", t === "a"); $("tab-b").classList.toggle("dang-chon", t === "b");
  $("tab-a").setAttribute("aria-pressed", String(t === "a"));
  $("tab-b").setAttribute("aria-pressed", String(t === "b"));
  $("noi-dung-a").classList.toggle("an", t !== "a"); $("noi-dung-b").classList.toggle("an", t !== "b");
  anChiTiet();
}
async function xuat(goiApi, nhan) {
  const kq = await goiApi();
  if (kq.loi) { toast(kq.loi); return; }
  // api.mo_file/mo_thu_muc trả {loi} khi file đã bị xóa/di chuyển — phải nói ra,
  // nếu không người dùng bấm nút và không thấy gì xảy ra.
  const baoLoi = (r) => { if (r && r.loi) toast(r.loi); };
  toast(nhan, [
    { ten: "Mở file Excel", icon: "bang-tinh", onClick: async () => baoLoi(await api.mo_file(kq.path)) },
    { ten: "Mở thư mục", icon: "thu-muc", onClick: async () => baoLoi(await api.mo_thu_muc(kq.path)) },
  ]);
}
$("btn-xuat").onclick = () => {
  const cn = ketQua?.tomtat?.chi_nhanh;
  const nhieu = (ketQua?.don_vi || []).length > 1;
  return xuat(() => api.xuat_bao_cao(),
    nhieu ? `Đã xuất báo cáo chi nhánh ${cn}` : "Đã xuất báo cáo Excel");
};
$("btn-xuat-tong-hop").onclick = () =>
  xuat(() => api.xuat_tong_hop(),
    `Đã xuất báo cáo tổng hợp ${(ketQua?.don_vi || []).length} chi nhánh`);
$("btn-kiem-tra-lai").onclick = async () => { chuyenManHinh(1); await chayKiemTra(); };
$("btn-file-khac").onclick = () => { chuyenManHinh(1); anChiTiet(); };

window.addEventListener("pywebviewready", khoiTao);
