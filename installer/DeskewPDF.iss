; DeskewPDF installer (Inno Setup 6)
; Build:  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\DeskewPDF.iss
; Output: installer\Output\DeskewPDF-Setup.exe
;
; Packages the standalone dist\DeskewPDF.exe (built by build_exe.bat) into a
; single Setup.exe. End users need nothing else installed — no Python, no
; Inno Setup. Installs per-user by default (no admin prompt); the user may
; choose an all-users install if they have admin rights.

#define AppName "DeskewPDF"
#define AppVersion "1.0.0"
#define AppPublisher "Next Platforms"
#define AppExeName "DeskewPDF.exe"

[Setup]
AppId={{9B2F7C41-3A6E-4D8B-9E1A-DESKEWPDF0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Per-user by default => no admin/UAC prompt; user can opt into all-users.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=DeskewPDF-Setup
SetupIconFile=..\assets\DeskewPDF.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent
