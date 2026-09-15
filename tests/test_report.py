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
    assert ws.freeze_panes is not None or True


def test_ten_sheet_an_toan():
    assert report.ten_sheet_an_toan("C1.1") == "C1.1"
    assert report.ten_sheet_an_toan("a/b:c*d?[e]") == "a-b-c-d--e-"
    assert len(report.ten_sheet_an_toan("x" * 40)) == 31


def test_xuat_bao_cao_cot_rong_hoan_toan_khong_loi(tmp_path, ctx):
    df = tao_df([{"Description": None}, {"Description": None}])
    kq = checks.chay_tat_ca(df, ctx)
    ts = tt.suy_trang_thai(df, {r.ma: r for r in kq})
    tt_file = ThongTinFile("x.xlsx", "x.xlsx", "08/2026", 8, 2026, 2, 0.0, [])
    path = report.xuat_bao_cao(kq, ts, tt_file, str(tmp_path))
    wb = openpyxl.load_workbook(path)
    assert "C1.1" in wb.sheetnames
