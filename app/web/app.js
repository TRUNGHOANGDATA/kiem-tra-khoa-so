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
  "thong-ke": '<path d="M3 3v18h18"/><path d="M8 17v-6.5"/><path d="M13 17V6.5"/><path d="M18 17v-3.5"/>',
  "bang-tinh": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v5h5"/><path d="M8 13h2"/><path d="M14 13h2"/><path d="M8 17h2"/><path d="M14 17h2"/>',
  "tim-kiem": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.9-3.9"/>',
  "mui-phai": '<path d="m9 6 6 6-6 6"/>',
  "mui-trai": '<path d="m15 6-6 6 6 6"/>',
  "tai-ve": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  "thu-muc": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.7-.9L9.6 3.9A2 2 0 0 0 7.9 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  "lam-lai": '<path d="M21 12a9 9 0 0 1-15.4 6.4L3 16"/><path d="M3 12a9 9 0 0 1 15.4-6.4L21 8"/><path d="M21 3v5h-5"/><path d="M3 21v-5h5"/>',
};
const bieuTuong = (ten, lop = "icon") =>
  `<svg class="${lop}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"` +
  ` stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${HINH[ten] || ""}</svg>`;

const ICON_TT = { da_lam: "kiem", chua_lam: "loi", can_ra: "canh-bao", khong_ap_dung: "bo-qua" };
const NHAN_TT = { da_lam: "Đã làm", chua_lam: "Chưa làm", can_ra: "Cần rà", khong_ap_dung: "Không áp dụng" };
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
     - pct > 0 (giai đoạn 29 check, callback tới thật) -> thanh phần trăm thật.
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
  $("file-ten").textContent = info.ten; $("file-ky").textContent = info.ky;
  $("file-so-dong").textContent = fmt(info.so_dong); $("file-tong-ps").textContent = fmt(info.tong_ps);
  $("the-file").classList.remove("an"); $("btn-kiem-tra").disabled = false;
  $("header-file").textContent = `${info.ten} · kỳ ${info.ky}`;
}

async function khoiTao() {
  api = window.pywebview.api;
  const info = await taiFile(() => api.lay_file_moi_nhat(), "Đang đọc file…");
  if (info) hienFile(info); else toast("Chưa có file trong thư mục '1. Source' — hãy chọn hoặc kéo file vào.");
}

$("btn-chon-file").onclick = async () => {
  const info = await taiFile(() => api.chon_file(), "Đang đọc file…");
  if (!info) return;              // người dùng bấm Huỷ — không phải lỗi
  hienFile(info);
};

const vung = $("vung-keo-tha");
["dragenter", "dragover"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.add("keo-qua"); }));
["dragleave", "drop"].forEach((e) => vung.addEventListener(e, (ev) => { ev.preventDefault(); vung.classList.remove("keo-qua"); }));
vung.addEventListener("drop", async (ev) => {
  const f = ev.dataTransfer.files[0];
  const path = f && f.pywebviewFullPath;            // pywebview gắn đường dẫn thật vào File
  if (!path) { toast("Không lấy được đường dẫn file — hãy dùng nút 'Chọn file…'"); return; }
  hienFile(await taiFile(() => api.nap_file(path), "Đang đọc file…"));
});

$("btn-kiem-tra").onclick = chayKiemTra;
async function chayKiemTra() {
  $("btn-kiem-tra").disabled = true;
  // Lần gọi này có thể phải đọc lại Excel trước khi chạy check -> mở ở chế độ
  // không xác định; onTienTrinh sẽ tự chuyển sang phần trăm khi số thật tới.
  datTienTrinh("Đang chuẩn bị kiểm tra…");
  try {
    const kq = await api.chay_kiem_tra(fileHienTai?.path || null);
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
  $("banner-ky").textContent = `Kỳ ${t.ky} · ${t.ten} · ${fmt(t.so_dong)} dòng`;
  $("so-do").textContent = fmt(t.so_do); $("so-vang").textContent = fmt(t.so_vang);
  const tongCheck = ketQua.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke).length;
  $("so-xanh").textContent = fmt(tongCheck - t.so_do - t.so_vang);
  veTabA(); veTabB(); anChiTiet();
}

function veTabA() {
  const ul = $("ds-buoc"); ul.innerHTML = "";
  const dem = { da_lam: 0, chua_lam: 0, can_ra: 0, khong_ap_dung: 0 };
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
  $("dem-buoc").textContent =
    `${dem.da_lam} đã làm · ${dem.chua_lam} chưa làm · ${dem.can_ra} cần rà · ${dem.khong_ap_dung} không áp dụng`;
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
async function moChiTiet(ma, tieuDe, trang = 1) {
  // Giữ tiêu đề gốc trong state: tách lại từ DOM sẽ nuốt mất tên check ngay khi gõ tìm kiếm.
  chiTiet = { ma, tieuDe, trang, timKiem: chiTiet.ma === ma ? chiTiet.timKiem : "" };
  $("o-tim-kiem").value = chiTiet.timKiem;
  const kq = await api.lay_chi_tiet(ma, trang, KICH_THUOC, chiTiet.timKiem);
  if (kq.loi) { toast(kq.loi); return; }
  $("chi-tiet-tieu-de").textContent = tieuDe;
  $("chi-tiet-dem").textContent = `${fmt(kq.tong)} dòng${chiTiet.timKiem ? " khớp từ khóa" : ""}`;
  const tb = $("bang-chi-tiet");
  if (!kq.tong) {
    tb.innerHTML = `<tbody><tr><td class="bang-trong">${bieuTuong("tim-kiem", "icon icon-to")}` +
      `<span>${chiTiet.timKiem ? "Không có dòng nào khớp từ khóa." : "Không có dòng nào."}</span></td></tr></tbody>`;
  } else {
    // Nhãn cột và danh sách cột số do backend cấp (app.checks.base.TEN_COT) — không lặp lại ở đây.
    const cot = kq.cot || [];
    const nhan = kq.nhan || cot;
    const soCot = new Set(kq.cot_so || []);
    // Diễn giải chứng từ có thể dài vài trăm ký tự: kẹp còn 3 dòng để nhịp hàng
    // không vỡ trên bảng 30.000 dòng, chuỗi đầy đủ đưa vào title để rê chuột đọc.
    const oChu = (v) => {
      const s = String(v ?? "");
      const tip = s.length > 60 ? ` title="${esc(s)}"` : "";
      return `<td><span class="o-chu"${tip}>${esc(v)}</span></td>`;
    };
    const oDuLieu = (r, c) => typeof r[c] === "boolean" ? `<td>${r[c] ? "Có" : "Không"}</td>`
      : soCot.has(c) && typeof r[c] === "number" ? `<td class="so">${fmt(r[c])}</td>`
      : oChu(r[c]);
    tb.innerHTML = `<thead><tr>${cot.map((c, i) =>
        `<th scope="col" class="${soCot.has(c) ? "so" : ""}">${esc(nhan[i] ?? c)}</th>`).join("")}</tr></thead><tbody>${
      kq.dong.map((r) => `<tr>${cot.map((c) => oDuLieu(r, c)).join("")}</tr>`).join("")}</tbody>`;
  }
  vePhanTrang(kq.tong, trang);
  $("khung-chi-tiet").classList.remove("an");
  $("khung-chi-tiet").scrollIntoView({ behavior: "smooth", block: "start" });
}
function anChiTiet() { $("khung-chi-tiet").classList.add("an"); }

function vePhanTrang(tong, trang) {
  const soTrang = Math.max(1, Math.ceil(tong / KICH_THUOC));
  const p = $("phan-trang"); p.innerHTML = "";
  const nut = (ten, icon, ben, t, tat) => {
    const b = document.createElement("button");
    b.className = "btn"; b.type = "button"; b.disabled = tat;
    const sv = bieuTuong(icon, "icon icon-nho");
    b.innerHTML = ben === "trai" ? sv : "";
    b.append(document.createTextNode(ten));
    if (ben === "phai") b.insertAdjacentHTML("beforeend", sv);
    b.onclick = () => moChiTiet(chiTiet.ma, chiTiet.tieuDe, t);
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

/* ---------- tabs & footer ---------- */
$("tab-a").onclick = () => chuyenTab("a"); $("tab-b").onclick = () => chuyenTab("b");
function chuyenTab(t) {
  $("tab-a").classList.toggle("dang-chon", t === "a"); $("tab-b").classList.toggle("dang-chon", t === "b");
  $("tab-a").setAttribute("aria-pressed", String(t === "a"));
  $("tab-b").setAttribute("aria-pressed", String(t === "b"));
  $("noi-dung-a").classList.toggle("an", t !== "a"); $("noi-dung-b").classList.toggle("an", t !== "b");
  anChiTiet();
}
$("btn-xuat").onclick = async () => {
  const kq = await api.xuat_bao_cao();
  if (kq.loi) { toast(kq.loi); return; }
  // api.mo_file/mo_thu_muc trả {loi} khi file đã bị xóa/di chuyển — phải nói ra,
  // nếu không người dùng bấm nút và không thấy gì xảy ra.
  const baoLoi = (r) => { if (r && r.loi) toast(r.loi); };
  toast("Đã xuất báo cáo Excel", [
    { ten: "Mở file Excel", icon: "bang-tinh", onClick: async () => baoLoi(await api.mo_file(kq.path)) },
    { ten: "Mở thư mục", icon: "thu-muc", onClick: async () => baoLoi(await api.mo_thu_muc(kq.path)) },
  ]);
};
$("btn-kiem-tra-lai").onclick = async () => { chuyenManHinh(1); await chayKiemTra(); };
$("btn-file-khac").onclick = () => { chuyenManHinh(1); anChiTiet(); };

window.addEventListener("pywebviewready", khoiTao);
