!include "WinVer.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"
!define LPS_HOOK_DIRECTORY "${__FILEDIR__}"

!macro LPS_CHECK_VC_RUNTIME
  InitPluginsDir
  File "/oname=$PLUGINSDIR\vc-runtime.ps1" "${LPS_HOOK_DIRECTORY}\vc-runtime.ps1"
  nsExec::ExecToStack '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PLUGINSDIR\vc-runtime.ps1" -Mode Check'
  Pop $R5
  Pop $R6
  ${If} $R5 != 0
    MessageBox MB_OKCANCEL|MB_ICONINFORMATION "AI WorkerにはMicrosoft Visual C++ v14 Runtime（x64、14.44以降）が必要です。公式パッケージを取得します（約25 MiB、導入用に約100 MiBの空き容量。共通Runtimeの導入には管理者確認が必要になる場合があります）。$\r$\n写真や検索データは送信しません。Microsoftの利用条件を確認して導入できます。$\r$\nオフラインではMicrosoft公式VC_redist.x64.exeを別途導入し、このセットアップを再実行してください。取得しますか？" /SD IDCANCEL IDOK lps_vc_download
    Abort
    lps_vc_download:
    DetailPrint "Microsoft公式Visual C++ Runtimeを取得・署名確認しています…"
    nsExec::ExecToStack '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PLUGINSDIR\vc-runtime.ps1" -Mode Download -Destination "$PLUGINSDIR\VC_redist.x64.exe"'
    Pop $R5
    Pop $R6
    ${If} $R5 != 0
      Delete "$PLUGINSDIR\VC_redist.x64.exe"
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "公式Runtimeの取得またはMicrosoft署名の確認に失敗しました。接続を確認して再試行してください。オフラインでは公式パッケージを別途導入してセットアップを再実行できます。" /SD IDCANCEL IDRETRY lps_vc_download
      Abort
    ${EndIf}
    ; The official package shows Microsoft's terms; never silently accept them.
    ExecWait '"$PLUGINSDIR\VC_redist.x64.exe" /norestart' $R5
    ${If} $R5 == 3010
      MessageBox MB_ICONINFORMATION "Microsoft Runtimeの導入にWindows再起動が必要です。作業を保存して手動で再起動し、このセットアップを再実行してください。" /SD IDOK
      Abort
    ${EndIf}
    nsExec::ExecToStack '"$WINDIR\Sysnative\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$PLUGINSDIR\vc-runtime.ps1" -Mode Check'
    Pop $R5
    Pop $R6
    ${If} $R5 != 0
      MessageBox MB_ICONSTOP "必要なx64 Visual C++ Runtimeが確認できません。Microsoft公式パッケージの導入を完了し、セットアップを再実行してください。アプリの既存データは保持されています。" /SD IDOK
      Abort
    ${EndIf}
  ${EndIf}
!macroend

!macro LPS_REFUSE_RUNNING
  !insertmacro RestartManager_StartSession $R0
  ${If} $R0 == ""
    MessageBox MB_ICONSTOP "アプリの実行状態を安全に確認できません。アプリを完全終了し、セットアップを再実行してください。既存のファイルは変更しません。" /SD IDOK
    Abort
  ${Else}
    !insertmacro RestartManager_RegisterFile $R0 "$INSTDIR\${MAINBINARYNAME}.exe"
    ${If} $0 == 0
      StrCpy $1 0
      StrCpy $2 0
      StrCpy $3 0
      StrCpy $R7 0
      ${GetParameters} $R8
      ClearErrors
      ${GetOptions} $R8 "/UPDATE" $R9
      ${IfNot} ${Errors}
        StrCpy $R7 40
      ${EndIf}
      ; The official updater starts NSIS immediately before exiting. Wait only
      ; on /UPDATE; never terminate a running app or bypass its lock.
      ${Do}
        StrCpy $1 0
        StrCpy $2 0
        StrCpy $3 0
        System::Call 'RSTRTMGR::RmGetList(p R0, *i .r1, *i .r2, p 0, *i .r3) i .r0'
        ${If} $0 == 234
        ${AndIf} $R7 > 0
          Sleep 250
          IntOp $R7 $R7 - 1
        ${Else}
          ${ExitDo}
        ${EndIf}
      ${Loop}
      ${If} $0 == 234
        !insertmacro RestartManager_EndSession $R0
        MessageBox MB_ICONSTOP "アプリが実行中です。タスクトレイの「完全終了」を選び、終了してから再実行してください。検索データとモデルは保持されます。" /SD IDOK
        Abort
      ${EndIf}
      ${If} $0 != 0
        !insertmacro RestartManager_EndSession $R0
        MessageBox MB_ICONSTOP "アプリの実行状態の確認に失敗しました。アプリを完全終了し、セットアップを再実行してください。既存のファイルは変更しません。" /SD IDOK
        Abort
      ${EndIf}
    ${Else}
      !insertmacro RestartManager_EndSession $R0
      MessageBox MB_ICONSTOP "更新対象の実行状態を確認できません。アプリを完全終了し、セットアップを再実行してください。既存のファイルは変更しません。" /SD IDOK
      Abort
    ${EndIf}
    !insertmacro RestartManager_EndSession $R0
  ${EndIf}
!macroend

; Tauri's default macro force-stops the app in silent mode. Replace that
; final check as well, so a launch between our hook and its check is refused.
; Compilation must fail if Tauri changes this integration point.
!macroundef CheckIfAppIsRunning
!macro CheckIfAppIsRunning executablePath appName
  !insertmacro LPS_REFUSE_RUNNING
!macroend

!macro NSIS_HOOK_PREINSTALL
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Local Photo Searchには64ビット版Windowsが必要です。" /SD IDOK
    Abort
  ${EndIf}
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
  IntCmp $0 19045 lps_supported lps_unsupported lps_supported
  lps_unsupported:
    MessageBox MB_ICONSTOP "Windows 10 22H2以降のx64環境が必要です。実機検証済みはWindows 11です。" /SD IDOK
    Abort
  lps_supported:
  ; Refuse replacement while the app owns its Worker. The user uses 完全終了.
  !insertmacro LPS_REFUSE_RUNNING
  !insertmacro LPS_CHECK_VC_RUNTIME
  ${GetParameters} $R8
  ClearErrors
  ${GetOptions} $R8 "/UPDATE" $R9
  ${IfNot} ${Silent}
  ${AndIf} ${Errors}
    MessageBox MB_OKCANCEL "アプリ本体は約120 MiBです。モデルは別途約462 MiB、AIキャッシュ用に最大1 GiB、検索データ用の空き容量が必要です。$\r$\nWebView2が不足する場合はMicrosoft公式セットアップを取得します（インターネット接続が必要、Runtime容量は配布版により変わります）。オフラインでは公式オフラインインストーラーでWebView2を準備してください。$\r$\n$\r$\n写真・モデル・検索データは更新やアンインストールで削除しません。続行しますか？" IDOK lps_continue
    Abort
    lps_continue:
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro LPS_REFUSE_RUNNING
  ; Remove only our optional login entry; preserve all user data and original photos.
  !if "${BUNDLEID}" == "com.local.embeddinggemma.media-search"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "LocalPhotoSearch"
  !else
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "LocalPhotoSearchQA"
  !endif
!macroend
