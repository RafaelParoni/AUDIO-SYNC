; Inno Setup Script para AudioSync
; Este script empacota o executável gerado em um instalador.

#define MyAppName "AudioSync"
#define MyAppVersion "1.1"
#define MyAppPublisher "Rafael Paroni - rafaelparoni.vercel.app"
#define MyAppExeName "AudioSync.exe"

[Setup]
; O AppId identifica exclusivamente o aplicativo.
; Não modifique o AppId se quiser lançar atualizações para este mesmo aplicativo no futuro.
AppId={{5D01E171-4241-435E-A25D-80A30B1A7E14}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Instala na pasta padrão de programas do usuário atual (não requer permissão de admin)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
; Pasta e nome do arquivo de setup de saída
OutputDir=SetupOutput
OutputBaseFilename=AudioSync_Setup_v{#MyAppVersion}
SetupIconFile=AudioSyncNoText.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia a pasta inteira gerada pelo PyInstaller (modo onedir) e todos os seus subdiretórios
Source: "dist\AudioSync\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Cria atalhos no Menu Iniciar e na Área de Trabalho
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Permite rodar o app assim que a instalação terminar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
