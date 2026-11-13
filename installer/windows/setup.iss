; Setup wizard of Riot Office for Windows 10/11 (64-bit). Built by build_installer.ps1, which passes
;   /DAppVersion=x.y.z  /DLoVersion=a.b.c  /DStage=<staging folder>  /O<output folder>
;
; What it does, per machine (administrator rights, because LibreOffice installs per machine):
;   1. installs LibreOffice from the bundled MSI, silently, with the English and Italian interface
;      and help, Microsoft Office file types registered, update check and quick starter off;
;      skipped when the same LibreOffice version is already installed;
;   2. installs the Carlito and Caladea fonts (metric-compatible with Calibri and Cambria);
;   3. installs the Riot Office launcher and copies the Riot configuration layer into LibreOffice;
;   4. creates Start menu entries for Riot Office, Writer, Calc, Impress and the guide.
; The wizard speaks English and Italian.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef LoVersion
  #define LoVersion "26.8.3"
#endif
#ifndef Stage
  #define Stage "..\..\build\windows\stage"
#endif
#define AppName "Riot Office"
#define LoMsi "LibreOffice_" + LoVersion + "_Win_x86-64.msi"
#define PyW "{app}\runtime\pythonw.exe"
#define Py "{app}\runtime\python.exe"

[Setup]
AppId={{5B7C1E2A-9D4F-4C61-8A3E-6F2D0B9C7A11}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Orso Peruzzi
AppPublisherURL=https://github.com/battles5/riot-office
AppComments=Local office suite built on LibreOffice
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile={#Stage}\LICENSE.txt
SetupIconFile={#Stage}\assets\icon.ico
WizardImageFile={#Stage}\assets\wizard_side.bmp
WizardSmallImageFile={#Stage}\assets\wizard_small.bmp
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#AppName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
OutputBaseFilename=RiotOffice-Setup-{#AppVersion}
CloseApplications=yes
ShowLanguageDialog=auto

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[CustomMessages]
en.DesktopIcon=Create a desktop shortcut
it.DesktopIcon=Crea un collegamento sul desktop
en.InstallingLO=Installing LibreOffice {#LoVersion} (this takes a few minutes)...
it.InstallingLO=Installazione di LibreOffice {#LoVersion} (richiede qualche minuto)...
en.InstallingHelp=Installing the LibreOffice help...
it.InstallingHelp=Installazione della guida di LibreOffice...
en.Configuring=Applying the Riot Office configuration...
it.Configuring=Applicazione della configurazione di Riot Office...
en.InstallingAddin=Installing the Excel functions for Calc...
it.InstallingAddin=Installazione delle funzioni Excel per Calc...
en.Launch=Start Riot Office
it.Launch=Avvia Riot Office
en.Guide=User guide
it.Guide=Guida
en.LOFailed=LibreOffice could not be installed (msiexec code %1). The log is in %2.
it.LOFailed=Non è stato possibile installare LibreOffice (codice msiexec %1). Il log è in %2.
en.KeepLO=LibreOffice stays installed: remove it from Settings > Apps if you no longer need it.
it.KeepLO=LibreOffice resta installato: rimuovilo da Impostazioni > App se non ti serve più.

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"

[Files]
Source: "{#Stage}\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Stage}\riot_office\*"; DestDir: "{app}\riot_office"; Flags: ignoreversion
Source: "{#Stage}\config\*"; DestDir: "{app}\config"; Flags: ignoreversion
Source: "{#Stage}\addins\*.oxt"; DestDir: "{app}\addins"; Flags: ignoreversion
Source: "{#Stage}\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "{#Stage}\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "{#Stage}\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Stage}\THIRD-PARTY-NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Stage}\fonts\OFL-*.txt"; DestDir: "{app}\fonts"; Flags: ignoreversion
Source: "{#Stage}\fonts\Carlito-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Carlito"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Carlito-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Carlito Bold"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Carlito-Italic.ttf"; DestDir: "{autofonts}"; FontInstall: "Carlito Italic"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Carlito-BoldItalic.ttf"; DestDir: "{autofonts}"; FontInstall: "Carlito Bold Italic"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Caladea-Regular.ttf"; DestDir: "{autofonts}"; FontInstall: "Caladea"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Caladea-Bold.ttf"; DestDir: "{autofonts}"; FontInstall: "Caladea Bold"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Caladea-Italic.ttf"; DestDir: "{autofonts}"; FontInstall: "Caladea Italic"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "{#Stage}\fonts\Caladea-BoldItalic.ttf"; DestDir: "{autofonts}"; FontInstall: "Caladea Bold Italic"; Flags: onlyifdoesntexist uninsneveruninstall
; The MSIs are only needed while installing.
Source: "{#Stage}\libreoffice\*.msi"; DestDir: "{tmp}\libreoffice"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{#PyW}"; Parameters: "-m riot_office"; WorkingDir: "{userdocs}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Riot Writer"; Filename: "{#PyW}"; Parameters: "-m riot_office open writer"; WorkingDir: "{userdocs}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Riot Calc"; Filename: "{#PyW}"; Parameters: "-m riot_office open calc"; WorkingDir: "{userdocs}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Riot Impress"; Filename: "{#PyW}"; Parameters: "-m riot_office open impress"; WorkingDir: "{userdocs}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\{cm:Guide}"; Filename: "{app}\docs\Guide.html"
Name: "{autodesktop}\{#AppName}"; Filename: "{#PyW}"; Parameters: "-m riot_office"; WorkingDir: "{userdocs}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\libreoffice\{#LoMsi}"" /qn /norestart ALLUSERS=1 UI_LANGS=en_US,it REGISTER_ALL_MSO_TYPES=1 ISCHECKFORPRODUCTUPDATES=0 QUICKSTART=0 CREATEDESKTOPLINK=0 RebootYesNo=No REMOVE=gm_o_Onlineupdate /l*v ""{app}\libreoffice-install.log"""; StatusMsg: "{cm:InstallingLO}"; Flags: waituntilterminated; Check: NeedLibreOffice; AfterInstall: CheckMsiResult
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\libreoffice\LibreOffice_{#LoVersion}_Win_x86-64_helppack_en-US.msi"" /qn /norestart ALLUSERS=1"; StatusMsg: "{cm:InstallingHelp}"; Flags: waituntilterminated; Check: NeedLibreOffice
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\libreoffice\LibreOffice_{#LoVersion}_Win_x86-64_helppack_it.msi"" /qn /norestart ALLUSERS=1"; StatusMsg: "{cm:InstallingHelp}"; Flags: waituntilterminated; Check: NeedLibreOffice
Filename: "{#Py}"; Parameters: "-I -m riot_office config install"; WorkingDir: "{app}"; StatusMsg: "{cm:Configuring}"; Flags: runhidden waituntilterminated
Filename: "{#Py}"; Parameters: "-I -m riot_office addin install"; WorkingDir: "{app}"; StatusMsg: "{cm:InstallingAddin}"; Flags: runhidden waituntilterminated
Filename: "{#PyW}"; Parameters: "-m riot_office"; WorkingDir: "{userdocs}"; Description: "{cm:Launch}"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{#Py}"; Parameters: "-I -m riot_office addin uninstall"; WorkingDir: "{app}"; Flags: runhidden; RunOnceId: "RiotAddin"
Filename: "{#Py}"; Parameters: "-I -m riot_office config uninstall"; WorkingDir: "{app}"; Flags: runhidden; RunOnceId: "RiotConfig"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\riot_office"
Type: filesandordirs; Name: "{app}\addins"

[Code]
var
  LoChecked, LoNeeded: Boolean;

{ True unless this exact LibreOffice version is already installed (read from its version.ini). }
function NeedLibreOffice: Boolean;
var
  Ini, Installed: String;
begin
  if not LoChecked then begin
    LoChecked := True;
    LoNeeded := True;
    Ini := ExpandConstant('{commonpf64}\LibreOffice\program\version.ini');
    if FileExists(Ini) then begin
      Installed := GetIniString('Version', 'MsiProductVersion', '', Ini);
      LoNeeded := Pos('{#LoVersion}', Installed) <> 1;
      Log('LibreOffice installed: ' + Installed + ', needed: ' + IntToStr(Ord(LoNeeded)));
    end;
  end;
  Result := LoNeeded;
end;

procedure CheckMsiResult;
begin
  if not FileExists(ExpandConstant('{commonpf64}\LibreOffice\program\soffice.exe')) then
    begin
      Log('LibreOffice is not where it should be after the MSI finished: ' + ExpandConstant('{commonpf64}\LibreOffice\program\soffice.exe'));
      { MsgBox is not silenced by /SUPPRESSMSGBOXES (it would wait forever on an unattended PC); SuppressibleMsgBox is. }
      SuppressibleMsgBox(FmtMessage(CustomMessage('LOFailed'), ['?', ExpandConstant('{app}\libreoffice-install.log')]), mbError, MB_OK, IDOK);
    end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent then
    MsgBox(CustomMessage('KeepLO'), mbInformation, MB_OK);
end;
