import openpyxl

from app import checks, report, trang_thai as tt
from app.loader import ThongTinFile
from tests.conftest import tao_df


def test_xuat_bao_cao_tao_du_sheet(tmp_path, ctx):
    df = tao_df([{"Description": None, "DebitAccount": "632111", "CreditAccount": "1551", "Amount": 5}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 1, 5.0, ["log 1"])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    wb = openpyxl.load_workbook(path)
    assert wb.sheetnames[:2] == ["Tong quan", "Trang thai khoa so"]
    assert "C1.1" in wb.sheetnames and "C5.2" in wb.sheetnames      # có lỗi -> có sheet
    assert "C1.5" not in wb.sheetnames                               # không lỗi -> không sheet
    assert "C6.1" in wb.sheetnames and "Nhat ky xu ly" in wb.sheetnames
    ws = wb["Tong quan"]
    assert ws["A1"].value.startswith("BÁO CÁO KIỂM TRA KHÓA SỔ")
    assert ws.freeze_panes == "A6"                                   # khóa dòng tiêu đề (bảng bắt đầu ở dòng 5)
    assert wb["Trang thai khoa so"].freeze_panes == "A2"


def test_ten_sheet_an_toan():
    assert report.ten_sheet_an_toan("C1.1") == "C1.1"
    assert report.ten_sheet_an_toan("a/b:c*d?[e]") == "a-b-c-d--e-"
    assert len(report.ten_sheet_an_toan("x" * 40)) == 31


def test_tieu_de_cot_deu_la_tieng_viet(tmp_path, ctx):
    """C4: không để lọt DocNo/DebitAccount/ly_do/ps_no/so_dong ra trước mặt kế toán."""
    df = tao_df([{"Description": None, "ItemName": None, "DebitAccount": "632111",
                  "CreditAccount": "1551", "Amount": 5.0}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    path = report.xuat_bao_cao(kq, ts, ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 1, 5.0, []),
                               str(tmp_path))
    wb = openpyxl.load_workbook(path)
    tieng_anh = {"DocNo", "DocDate", "DebitAccount", "CreditAccount", "Amount", "Description",
                 "ly_do", "TK", "ps_no", "ps_co", "net", "so_dong", "tong", "bat_thuong",
                 "TaxCode", "DocCode", "CreatedByName", "thue_vao_1331", "thue_ra_33311"}
    for ten in wb.sheetnames:
        ws = wb[ten]
        dong_dau = 5 if ten == "Tong quan" else 1
        nhan = [c.value for c in ws[dong_dau] if c.value is not None]
        assert not (set(nhan) & tieng_anh), f"{ten}: còn tên cột tiếng Anh {set(nhan) & tieng_anh}"
    assert [c.value for c in wb["C5.2"][1]] == ["Tài khoản", "Phát sinh Nợ", "Phát sinh Có", "Lý do"]


def test_c65_bat_thuong_ghi_co_khong(tmp_path, ctx):
    """C4: cột bất thường hiện 'Có'/'Không', không phải TRUE/FALSE."""
    rows = [{"DocDate": f"2026-08-{d:02d}"} for d in range(1, 11)] + [{"DocDate": "2026-08-31"}] * 30
    df = tao_df(rows)
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    path = report.xuat_bao_cao(kq, ts, ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, len(rows), 0.0, []),
                               str(tmp_path))
    ws = openpyxl.load_workbook(path)["C6.5"]
    cot = [c.value for c in ws[1]].index("Bất thường") + 1
    gia_tri = {ws.cell(row=r, column=cot).value for r in range(2, ws.max_row + 1)}
    assert gia_tri == {"Có", "Không"}


def test_trang_bia_dung_dau_cham_kieu_viet_nam(tmp_path, ctx):
    """C5: 79.450 chứ không phải 79,450 — trang bìa phải khớp mọi con số còn lại."""
    df = tao_df([{}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 79_450, 1_234_567_890.0, [])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    a2 = openpyxl.load_workbook(path)["Tong quan"]["A2"].value
    assert "79.450 dòng" in a2 and "1.234.567.890" in a2
    assert "79,450" not in a2 and "1,234,567,890" not in a2


def test_sheet_nhat_ky_ghi_dung_canh_bao_cua_loader(tmp_path, ctx):
    """D5: sheet này là nơi DUY NHẤT cảnh báo lúc đọc file nổi lên trước người dùng."""
    df = tao_df([{}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    log = ["Cột Amount: 3 giá trị không phải số, đã ép về 0",
           "Cột DocDate: 2 giá trị không phải ngày hợp lệ, đã để trống"]
    path = report.xuat_bao_cao(kq, ts, ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 1, 0.0, log),
                               str(tmp_path))
    ws = openpyxl.load_workbook(path)["Nhat ky xu ly"]
    assert [c[0].value for c in ws.iter_rows(min_row=1, max_col=1)] == ["Thông điệp", *log]


def test_sheet_nhat_ky_khi_khong_co_canh_bao(tmp_path, ctx):
    df = tao_df([{}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    path = report.xuat_bao_cao(kq, ts, ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 1, 0.0, []),
                               str(tmp_path))
    ws = openpyxl.load_workbook(path)["Nhat ky xu ly"]
    assert [c[0].value for c in ws.iter_rows(min_row=1, max_col=1)] == [
        "Thông điệp", "Không có cảnh báo khi đọc dữ liệu"]


def test_xuat_bao_cao_cot_rong_hoan_toan_khong_loi(tmp_path, ctx):
    df = tao_df([{"Description": None}, {"Description": None}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 2, 0.0, [])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    wb = openpyxl.load_workbook(path)
    assert "C1.1" in wb.sheetnames
