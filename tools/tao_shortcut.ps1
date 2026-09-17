# Tạo shortcut có ĐÚNG icon cho tool.
#
# Vì sao cần: file .bat không mang được icon riêng — Windows luôn vẽ icon mặc định
# của .bat (hoặc của python.exe khi chạy qua nó). Chỉ SHORTCUT (.lnk) mới đặt được
# IconLocation. Nên muốn thấy cái khiên thì phải chạy qua shortcut này.
param(
    # Thư mục đặt shortcut. Bỏ trống = tạo cả ở Desktop lẫn thư mục dự án.
    [string]$Dich = ""
)

$ErrorActionPreference = "Stop"
$goc = Split-Path -Parent $PSScriptRoot
$bat = Join-Path $goc "Kiem_tra_khoa_so.bat"
$ico = Join-Path $goc "app\app.ico"
$ten = "Kiem tra khoa so cuoi ky.lnk"

foreach ($p in @($bat, $ico)) {
    if (-not (Test-Path $p)) { throw "Khong tim thay: $p" }
}

$thuMuc = if ($Dich) { @($Dich) } else { @([Environment]::GetFolderPath("Desktop"), $goc) }
$shell = New-Object -ComObject WScript.Shell
foreach ($tm in $thuMuc) {
    if (-not (Test-Path $tm)) { New-Item -ItemType Directory -Force -Path $tm | Out-Null }
    $lnk = $shell.CreateShortcut((Join-Path $tm $ten))
    $lnk.TargetPath       = $bat
    $lnk.WorkingDirectory = $goc          # .bat tự cd, nhưng đặt cho chắc
    $lnk.IconLocation     = "$ico,0"
    $lnk.Description      = "Kiem tra khoa so cuoi ky - DN san xuat TT200"
    $lnk.WindowStyle      = 7             # 7 = thu nho: cua so console khong dap vao mat
    $lnk.Save()
    Write-Output "Da tao: $(Join-Path $tm $ten)"
}
