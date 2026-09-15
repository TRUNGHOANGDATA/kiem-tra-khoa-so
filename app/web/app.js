/* Kiểm tra khóa sổ – frontend thuần, giao tiếp qua window.pywebview.api */
const $ = (id) => document.getElementById(id);
let api = null;
let ketQua = null;              // kết quả chay_kiem_tra
let fileHienTai = null;         // {path, ten, ky, so_dong, tong_ps}
let chiTiet = { ma: null, trang: 1, timKiem: "" };
const KICH_THUOC = 100;

const fmt = (n) => Number(n || 0).toLocaleString("vi-VN", { maximumFractionDigits: 0 });
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const ICON_TT = { da_lam: "✅", chua_lam: "❌", can_ra: "⚠️", khong_ap_dung: "➖" };
const NHAN_TT = { da_lam: "Đã làm", chua_lam: "Chưa làm", can_ra: "Cần rà", khong_ap_dung: "Không áp dụng" };
const NHAN_MD = { do: "Nghiêm trọng", vang: "Cảnh báo", xanh: "Đạt" };
const CLASS_MD = { do: "muc-do-", vang: "muc-vang", xanh: "muc-xanh" };

/* ---------- tiến trình (backend gọi) ---------- */
function onTienTrinh(ten, pct) {
  $("tien-trinh").classList.remove("an");
  $("tien-trinh-thanh").style.width = pct + "%";
  $("tien-trinh-ten").textContent = pct < 100 ? `Đang kiểm tra: ${ten}…` : "Hoàn tất";
}
window.onTienTrinh = onTienTrinh;

/* ---------- toast ---------- */
function toast(msg, nut = []) {
  const t = $("toast");
  t.innerHTML = "";
  t.append(Object.assign(document.createElement("span"), { textContent: msg }));
  nut.forEach(({ ten, onClick }) => {
    const b = document.createElement("button"); b.className = "btn"; b.textContent = ten; b.onclick = onClick; t.append(b);
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
  const info = await api.lay_file_moi_nhat();
  if (info) hienFile(info); else toast("Chưa có file trong thư mục '1. Source' — hãy chọn hoặc kéo file vào.");
}

$("btn-chon-file").onclick = async () => {
  const info = await api.chon_file();
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
  hienFile(await api.nap_file(path));
});

$("btn-kiem-tra").onclick = chayKiemTra;
async function chayKiemTra() {
  $("btn-kiem-tra").disabled = true; onTienTrinh("Bắt đầu", 0);
  const kq = await api.chay_kiem_tra(fileHienTai?.path || null);
  $("btn-kiem-tra").disabled = false; $("tien-trinh").classList.add("an");
  if (kq.loi) { toast(kq.loi); return; }
  ketQua = kq; veKetQua(); chuyenManHinh(2);
}

function chuyenManHinh(n) {
  $("man-hinh-1").classList.toggle("an", n !== 1);
  $("man-hinh-2").classList.toggle("an", n !== 2);
}

/* ---------- màn hình 2 ---------- */
function veKetQua() {
  const t = ketQua.tomtat;
  const b = $("banner");
  b.className = "banner " + (t.san_sang ? "san-sang" : "chua-san-sang");
  $("banner-ket-luan").textContent = t.san_sang ? "SẴN SÀNG KHÓA SỔ" : `CHƯA SẴN SÀNG — còn ${t.con_viec} việc`;
  $("so-do").textContent = t.so_do; $("so-vang").textContent = t.so_vang;
  const tongCheck = ketQua.nhom.flatMap((n) => n.checks).filter((c) => !c.la_thong_ke).length;
  $("so-xanh").textContent = tongCheck - t.so_do - t.so_vang;
  veTabA(); veTabB(); anChiTiet();
}

function veTabA() {
  const ul = $("ds-buoc"); ul.innerHTML = "";
  ketQua.trang_thai.forEach((b) => {
    const li = document.createElement("li"); li.className = `buoc tt-${b.trang_thai}`;
    li.innerHTML = `<div class="icon">${ICON_TT[b.trang_thai]}</div>
      <div><div class="ten">${esc(b.buoc)}</div><div class="tom-tat">${esc(b.tom_tat)}</div></div>
      <span class="nhan">${NHAN_TT[b.trang_thai]}</span><span>›</span>`;
    li.onclick = () => moChiTiet(b.ma_check, `${esc(b.buoc)} — chứng minh (${b.ma_check})`);
    ul.append(li);
  });
}

function veTabB() {
  const luoi = $("luoi-nhom"); luoi.innerHTML = "";
  ketQua.nhom.forEach((n) => {
    const d = document.createElement("div"); d.className = `the-nhom nhom-${n.muc_do}`;
    const ds = n.checks.map((c) =>
      `<li data-ma="${esc(c.ma)}"><span><i class="muc-do ${CLASS_MD[c.muc_do]}"></i>${esc(c.ma)} ${esc(c.ten)}</span><b>${c.la_thong_ke ? "📊" : fmt(c.so_loi)}</b></li>`).join("");
    d.innerHTML = `<div class="so">${n.ma === "G6" ? "📊" : fmt(n.so_loi)}</div><div class="ten">${esc(n.ten)}</div>
      <div class="tom-tat">${n.ma === "G6" ? "Bảng thống kê" : NHAN_MD[n.muc_do]}</div><ul class="ds-check">${ds}</ul>`;
    d.querySelectorAll("li").forEach((li) => li.onclick = (ev) => {
      ev.stopPropagation(); const c = n.checks.find((x) => x.ma === li.dataset.ma);
      chonThe(d); moChiTiet(c.ma, `${esc(c.ma)} · ${esc(c.ten)}${c.ghi_chu ? " — " + esc(c.ghi_chu) : ""}`);
    });
    d.onclick = () => { const c = n.checks.find((x) => x.so_loi > 0) || n.checks[0]; chonThe(d); moChiTiet(c.ma, `${esc(c.ma)} · ${esc(c.ten)}`); };
    luoi.append(d);
  });
}
function chonThe(d) { document.querySelectorAll(".the-nhom").forEach((x) => x.classList.remove("dang-chon")); d.classList.add("dang-chon"); }

/* ---------- chi tiết ---------- */
async function moChiTiet(ma, tieuDe, trang = 1) {
  chiTiet = { ma, trang, timKiem: chiTiet.ma === ma ? chiTiet.timKiem : "" };
  $("o-tim-kiem").value = chiTiet.timKiem;
  const kq = await api.lay_chi_tiet(ma, trang, KICH_THUOC, chiTiet.timKiem);
  if (kq.loi) { toast(kq.loi); return; }
  $("chi-tiet-tieu-de").textContent = `${tieuDe} · ${fmt(kq.tong)} dòng`;
  const tb = $("bang-chi-tiet");
  if (!kq.tong) { tb.innerHTML = `<tr><td class="bang-trong">Không có dòng nào.</td></tr>`; }
  else {
    const soCot = new Set(["Amount", "ps_no", "ps_co", "net", "tong", "so_dong", "thue_vao_1331", "thue_ra_33311", "UnitCost", "Quantity9"]);
    tb.innerHTML = `<thead><tr>${kq.cot.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${
      kq.dong.map((r) => `<tr>${kq.cot.map((c) => soCot.has(c) && typeof r[c] === "number"
        ? `<td class="so">${fmt(r[c])}</td>` : `<td>${esc(r[c])}</td>`).join("")}</tr>`).join("")}</tbody>`;
  }
  vePhanTrang(kq.tong, trang, tieuDe);
  $("khung-chi-tiet").classList.remove("an");
  $("khung-chi-tiet").scrollIntoView({ behavior: "smooth", block: "start" });
}
function anChiTiet() { $("khung-chi-tiet").classList.add("an"); }

function vePhanTrang(tong, trang, tieuDe) {
  const soTrang = Math.max(1, Math.ceil(tong / KICH_THUOC));
  const p = $("phan-trang"); p.innerHTML = "";
  const nut = (ten, t, tat) => { const b = document.createElement("button"); b.className = "btn"; b.textContent = ten;
    b.disabled = tat; b.onclick = () => moChiTiet(chiTiet.ma, tieuDe.replace(/ · .*dòng$/, ""), t); return b; };
  p.append(nut("‹ Trước", trang - 1, trang <= 1),
    Object.assign(document.createElement("span"), { textContent: `Trang ${trang}/${soTrang}` }),
    nut("Sau ›", trang + 1, trang >= soTrang));
}

$("o-tim-kiem").addEventListener("input", (ev) => {
  clearTimeout($("o-tim-kiem")._t);
  $("o-tim-kiem")._t = setTimeout(() => { chiTiet.timKiem = ev.target.value.trim();
    moChiTiet(chiTiet.ma, $("chi-tiet-tieu-de").textContent.replace(/ · .*dòng$/, ""), 1); }, 300);
});

/* ---------- tabs & footer ---------- */
$("tab-a").onclick = () => chuyenTab("a"); $("tab-b").onclick = () => chuyenTab("b");
function chuyenTab(t) {
  $("tab-a").classList.toggle("dang-chon", t === "a"); $("tab-b").classList.toggle("dang-chon", t === "b");
  $("noi-dung-a").classList.toggle("an", t !== "a"); $("noi-dung-b").classList.toggle("an", t !== "b");
  anChiTiet();
}
$("btn-xuat").onclick = async () => {
  const kq = await api.xuat_bao_cao();
  if (kq.loi) { toast(kq.loi); return; }
  toast("Đã xuất báo cáo Excel", [
    { ten: "Mở file Excel", onClick: () => api.mo_file(kq.path) },
    { ten: "Mở thư mục", onClick: () => api.mo_thu_muc(kq.path) },
  ]);
};
$("btn-kiem-tra-lai").onclick = async () => { chuyenManHinh(1); await chayKiemTra(); };
$("btn-file-khac").onclick = () => { chuyenManHinh(1); anChiTiet(); };

window.addEventListener("pywebviewready", khoiTao);
