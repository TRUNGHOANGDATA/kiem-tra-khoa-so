; Inno Setup — bộ cài trọn gói cho "Kiểm tra khóa sổ cuối kỳ".
; Dựng theo thứ tự:
;   python -m tools.tao_seed
;   pyinstaller tools/app.spec --noconfirm --clean --distpath build/dist --workpath build/work
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" tools/installer.iss
; Kết quả: build/Output/KiemTraKhoaSo-Setup-1.1.0.exe

#define TenApp "Kiểm tra khóa sổ cuối kỳ"
#define PhienBan "1.1.0"
#define TenExe "KiemTraKhoaSo.exe"

[Setup]
AppId={{9F3C1A20-KTKS-4E2B-9C7A-0001CHOTSO}}
AppName={#TenApp}
AppVersion={#PhienBan}
AppPublisher=Phòng Kế toán
DefaultDirName={autopf}\KiemTraKhoaSo
DefaultGroupName=Kiểm tra khóa sổ
DisableProgramGroupPage=yes
; Cài cho MỘT người dùng, không cần quyền admin (dữ liệu ghi ở %LOCALAPPDATA%).
PrivilegesRequired=lowest
OutputDir=..\build\Output
OutputBaseFilename=KiemTraKhoaSo-Setup-{#PhienBan}
SetupIconFile=..\app\app.ico
UninstallDisplayIcon={app}\{#TenExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "vi"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo lối tắt ngoài màn hình"; GroupDescription: "Lối tắt:"

[Files]
; Toàn bộ bản PyInstaller one-folder (đã kèm _seed: kho CĐPS + tên chi nhánh).
Source: "..\build\dist\KiemTraKhoaSo\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#TenApp}"; Filename: "{app}\{#TenExe}"
Name: "{group}\Gỡ cài đặt"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#TenApp}"; Filename: "{app}\{#TenExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#TenExe}"; Description: "Mở ứng dụng ngay"; Flags: nowait postinstall skipifsilent
