> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# 配布・セキュリティ監査

2026-10-10。一般公開を許可する文書ではない。以下の表はdev.1監査の記録。dev.2での解消・残課題は [RCファイル別監査](RC_DISTRIBUTION_DETAIL.md) と [現行全PE一覧](DISTRIBUTION_FILES_CURRENT.md) を参照。個別VC/UCRT DLLと未使用Intel dispatchは同梱から除き、公式VC取得/署名検証とWebView2 Bootstrapper同梱へ変更した。

## モデル

[Google公式Embedding Modelsガイド](https://developers.google.com/edge/litert-lm/embedding_models)が指定する[LiteRT Communityの740M](https://huggingface.co/litert-community/embeddinggemma-2-740m-litert-lm)を使用。2026-10-10に配布APIのライセンス`apache-2.0`、gated=false、revision=`24d962e906c7d332c6428e71c9676855024569e2`、ファイル484,622,336 bytes、LFS SHA-256=`e7a8a2204b91e0f96e92960e84a09a89212e1633dcb7575a9bf3378b4df77f4c`を確認。既存モデルと一致。ダウンロードは利用者の確認後だけ。モデルをインストーラーやGitに含めない。[モデルカード](https://huggingface.co/google/embeddinggemma-2)への確認導線を提供。

## 同梱通知と残る確認

| 対象 | 現状 | 判定 |
|---|---|---|
| CPython 3.14.3 | licenses/python/CPython/LICENSE.txt、組込第三者通知を同梱 | 基本通知あり |
| Pillow 12.3.0 | licenses/python/Pillow/LICENSEに第三者通知含む | 基本通知あり |
| LiteRT-LM API 0.18.0 | Apache-2.0 LICENSE同梱 | DLLの静的リンク依存の完全通知は未確認 |
| Lit/Tauri/Rust | 既存のnpm/Rustパッケージ一覧と通知 | tray-icon等の実ビルド依存と同梱一覧を再照合 |
| PyInstaller bootloader | GPLのbootloader例外文同梱 | 通知あり |
| dxcompiler.dll / dxil.dll | LiteRT-LM wheelの付属DLL、ProductVersion 1.9.2602.17 (21d28f727) | 実リビジョン[Microsoft DXC通知](https://github.com/microsoft/DirectXShaderCompiler/blob/21d28f727/LICENSE.TXT)をlicenses/native/DirectXShaderCompilerへ追加。その他DLLのゲートは別途残る |
| LiteRtDispatch.dll / native litert-lm.dll | OpenVINO等の経路も含む | 実バイナリのSBOM/推移通知が未確認。推測で再配布可能としない |
| MSVCP/VCRUNTIME/UCRT等 | PyInstallerで収集された実行用DLL | [Microsoft再配布条件](https://learn.microsoft.com/cpp/windows/redistributing-visual-cpp-files)と取得元を確認する必要あり |
| アプリ本体 | GitHub非公開、ライセンス未指定 | 公開時に著作権者が公開ライセンスを選択する |

ランタイム通知が確定できない場合は、利用者が公式wheelを別途取得する構成を検討する。配布版に同梱したDLLを根拠なく合法と判断しない。開発ツールの大型再インストールや有料署名は実行していない。

## 脆弱性照会

`scripts/audit-release.py`でCargo.lock/npm lock/Python lockの561パッケージの名称とバージョンだけを[OSV](https://osv.dev/)へ照会。写真・設定・検索文は送信しない。結果はローカル`data/release-tests/dependency-audit.json`。

- glib 0.18.5: [RUSTSEC-2024-0429](https://rustsec.org/advisories/RUSTSEC-2024-0429.html)、Iteratorのメモリ安全性問題。
- proc-macro-error 1.0.4: [RUSTSEC-2024-0370](https://rustsec.org/advisories/RUSTSEC-2024-0370.html)、保守停止通知。
- `cargo tree --target x86_64-pc-windows-msvc --locked --offline`のWindows経路には両パッケージを含まない。Linux用のlock依存を勝手に更新しない。Windowsで使用する照会対象には該当警告なし。
- wheelのnative静的依存、DLLの内部ライブラリ、OSドライバー、WebView2、CPython実行ファイルまで網羅した脆弱性監査ではない。安全性を保証するゼロ件判定ではない。

## 通信とローカル境界

Workerはstdin/stdoutのversioned IPCで待受ポートなし。Rust側はメソッドを許可リストに限定し、OS起動は登録済み写真IDをSQLiteで検証。CSPは自己資源、IPC、画像data URLだけ。公式ページ起動は固定URLの許可リスト。モデル取得は固定HTTPS配布ファイルから開始し、最終SHAで検証。HFの公式CDNへredirectする場合がある。外部送信はモデル取得のHTTPメタデータのみで、写真や検索文を送信する機能なし。広告・テレメトリーなし。

技術ログはローカル、最大2 MiB。起動時に前回分を置き換える。ローカルのファイルパスやランタイム例外を含むことがある。秘密情報を設定/送信する認証機能はない。ログ共有時は利用者が内容を確認する。OS/WebView2自体の通信をアプリ独自の非通信保証と混同しない。

## 署名と整合性

コード署名証明書/更新鍵/配布ホスト未提供のため自動更新は採用しない。手動更新を優先する。現在のexe/セットアップは未署名。SmartScreen警告を無効化する誘導は行わない。正式公開前に署名方針を決め、クリーンPCで警告と実際の導入を確認する。成果物のSHA-256一覧をビルド後に生成してローカル保持し、公開時には別の信頼できる場所で確認できるようにする。

## 公開ゲート

クリーンWindows（開発ツールなし）/WebView2不足環境、上記DLL通知・配布条件、実スリープ/再起動、実ドライブ切断の未検証は残る。現行のLiteRT-LM内蔵通知・Microsoft Runtime条件・クリーンPC受入が解決するまでは`1.0.0-dev.2`として扱い、`v1.0.0-rc.1`と正式版を作らない。Push/一般公開にはユーザーの最終確認が必要。
