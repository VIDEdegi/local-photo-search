# 環境構築

現在のPCではEに配置済み。更新時は既存環境を再利用する。開発用のtoolsディレクトリは配布しない。実行だけならインストーラーとユーザー指定モデルでよく、Rust/Python/npmは不要。

## 別Windows PC

Windows 11 x64、WebView2、Git、Node 24、Python 3.14、Rust 1.99.0 MSVC、MSVC x64とWindows SDKが必要。先に保存先の空きを確認する。今回の開発環境はビルド出力を含め約7 GiBを使用し、余裕を含め最低10 GiB以上の空きを推奨する。小容量のシステムドライブへ自動で入れない。

1. ソースを新しい保存先に配置。モデルとdata/tools/targetはGitの対象外。
2. 公式 [Rust](https://www.rust-lang.org/tools/install) をminimal profileで導入する際、RUSTUP_HOMEとCARGO_HOMEをプロジェクト下toolsへ設定する。PATHの恒久変更は任意。rustfmtを追加。
3. [TauriのWindows前提条件](https://v2.tauri.app/start/prerequisites/#windows) に沿ってMSVCとSDKを準備。C容量が足りなければインストールしない。このPCの独立展開構成は `tools/msvc/VC/Tools/MSVC` と `tools/msvc/Windows Kits/10`。env.ps1はその構成を検出する。通常のVS導入構成の場合はDeveloper PowerShellから実行して、そのINCLUDE/LIB/PATHを利用する。
4. Node/Pythonを準備し、以下を実行。既存のPythonを置換しない。

```powershell
cd 'プロジェクト保存先'
New-Item -ItemType Directory -Force tools,tmp | Out-Null
$env:TEMP = "$PWD/tmp"
$env:TMP = $env:TEMP
python -m venv tools/python
. ./scripts/env.ps1
./tools/python/Scripts/python.exe -m pip install -r worker/requirements-lock.txt
# 公式NuGet x64 CPython 3.14.8を別置き。固定SHA/PSF署名を検証。
./scripts/prepare-python-runtime.ps1
npm.cmd ci --no-audit --no-fund
```

5. ユーザーが取得済みの互換litertlmモデルを指定し、容量確認とSHA検証付き取り込みを行う（README）。モデルの再ダウンロードをビルド工程に含めない。
6. READMEの型チェック・実モデルテスト・build.ps1を実行。GPU利用可否は実機で検証し、不可ならCPUを選択。新PC上でのGPU互換性を推測で判断しない。

既存Pythonのバージョンを変えた場合は対応wheelとPyInstallerを再検証する。全ツールの取得は公式配布元を使用する。今回使用したMSVC展開方法/バージョンはPHASE0を参照。portable-msvcは最新版固定ではないので、再現時にはMicrosoftパッケージ版を確認する。

## ライセンス資源

dev.2の配布ビルドはCPython 3.14.8 / OpenSSL 3.5.9を必須とする。`tools/python-runtime-3.14.8` が公式base、`tools/python-build-3.14.8` が既存CPython 3.14の固定第三者パッケージを再利用するbuild環境。取得約15MiB、base展開約40MiBと仮想環境の空きが必要。旧tools/pythonとシステムPythonを削除/置換しない。env.ps1の `MEDIA_SEARCH_BUILD_PYTHON` をテストにも使用する。依存版/SSLが検証に一致しなければprepare/buildは中止する。更新根拠と試験は[配布監査](RC_DISTRIBUTION_DETAIL.md)を参照。

`licenses`はこのビルドの固定依存バージョンに対する通知。依存関係を更新したらnpm production依存とCargo.lockの推移的依存、CPython/Pillow/LiteRT等の同梱バイナリのライセンスを再収集・確認する。モデルは別管理。ロックファイルだけ更新して旧通知を使い続けない。
