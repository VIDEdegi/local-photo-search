> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# Phase 0 実機検証記録

2026-10-10、Windows 11 / Intel Core i7-9700K / RAM 32 GB / RTX 2070 8 GB。

## 保存先とモデル

開始時C空き約1.06 GiB、E空き約1.20 TiB。ユーザー指示によりソース・モデル・ツール・キャッシュ・一時ファイルを `PROJECT_ROOT` に配置。元のCプロジェクトは空で、初期化したGit履歴をEへ引き継いだ。C側と個人ファイルは削除していない。

既存Downloadsモデルは484,622,336 bytes、先頭 `LITERTLM`。Eの `data/models/embeddinggemma-2-740m.litertlm` へ1回コピーし、コピー元・先のSHA-256一致を確認：

`E7A8A2204B91E0F96E92960E84A09A89212E1633DCB7575A9BF3378B4DF77F4C`

再ダウンロードなし。モデルはGit/インストーラー対象外。再度の取り込みは同一ハッシュならコピーしない。初回取り込みはモデル容量 + 2 GiBの空きを確認する。

## 開発環境

既存のNode 24.14.1 / npm 11.11.0 / Python 3.14.3を利用。GPU driver 617.14 / WebView2 154.0.4258.62。Rust/MSVC/SDKは開始時未導入。

- Rust 1.99.0 minimal + rustfmt：専用RUSTUP_HOME/CARGO_HOME。システムPATHを変更しない。
- MSVC 19.44.35229、SDK 10.0.26100.0：Microsoft公式配布パッケージのx64部分だけをEへ展開。フルVisual Studioのインストールを回避。取得量約457 MB。
- `litert-lm-api==0.18.0` のWindows wheel：26,403,380 bytes。専用Python venvへPillow/PyInstallerとともに導入。
- Tauri 2 / Lit 3 / TypeScript 5 / Vite 7。npmとCargoのロックファイルを保持。
- 実WebView2テスト用tauri-driver 2.1.0 / EdgeDriver 154.0.4258.62。アプリの実行時には不要。

MSVC展開には [portable-msvc](https://gist.github.com/mmozeiko/7f3162ec2988e81e56d5c4e22cde9977) を確認して使用。保存先をE/tools内に制限するガードを追加し、Microsoftからのパッケージ取得のみ行った。このツール自体はアプリに同梱しない。

## AI結果

PythonネイティブAPIのimport、指定モデルの読み込み、テキスト/画像の768次元埋め込み、L2正規化、コサイン類似度を実機で確認。GPUログで `NVIDIA GeForce RTX 2070 / Direct3D 12 / Discrete GPU` を確認した。OpenCL/NPU利用不可のログは出るが、採用したWebGPU GPU推論は成功。

| 観測 | CPU 4スレッド | GPU RTX 2070 |
|---|---:|---:|
| モデル読み込み | 0.695秒 | 5.822秒 |
| 最初の文章 | 1.909秒 | 1.586秒 |
| 次の文章 | 0.103秒 | 0.083秒 |
| テスト画像1枚 | 9.439秒 | 1.025秒 |
| プロセス最大Working Set | 806.85 MiB | 566.85 MiB |

`data/probe-{cpu,gpu}-image.json` の個別観測。キャッシュ/コンパイル状態で変動するため一般的な性能保証ではない。GPUの専用VRAM使用量は個別計測していない。写真4種/24枚の統合検証はVALIDATIONを参照。

Python版GPUが成立したためブラウザー版LiteRT-LM/WASMへ切替える必要はなかった。ネイティブランタイム内部のWebGPUと、WebView2上のJavaScript WebGPUを区別する。後者でのモデル推論は未検証・未採用。Workerの推論はWebView2の生存に依存しないが、初期アプリは完全終了時にWorkerも終了する。

## デスクトップ成立性

Tauri 2本番Windows exe、実WebView2のUI/Rust/Python通信、PyInstaller onedirの配布Worker、SQLite作成/再読み込み、NSIS .exe生成を実機検証。日本語Windowsの標準cp932とRust UTF-8の不一致を修正し、通信をUTF-8に固定。プレビューのスタイル反映も実WebView2で検証する。

## 公式資料

[Embedding Models](https://developers.google.com/edge/litert-lm/embedding_models)、[LiteRT-LM](https://github.com/google-ai-edge/LiteRT-LM)、[公式検索デモ](https://github.com/google-ai-edge/LiteRT-LM/tree/main/js/apps/embedding_search)、[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)、[Tauri WebDriver](https://v2.tauri.app/develop/tests/webdriver/)。

公式デモはAPIと検索タスクprefixの参考にした。UI/DB/モデルダウンロード部分は丸ごと移植していない。ライセンス・著作権はTHIRD_PARTY_NOTICESとlicensesを同梱。
