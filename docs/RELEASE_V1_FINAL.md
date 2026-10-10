> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# v1.0.0 正式版の作成・公開準備

2026-10-10、基準 `800d634` / dev.2。所有者指示により、無料・ソース非公開の写真検索正式版 **1.0.0** をローカルで作成する。GitHub Push/公開は別途承認待ち。

変更は版番号、アプリ情報の正式版表示、README/利用ガイド/同意画面の説明、リリースノートの同梱だけ。UI設計・検索アルゴリズム・画像処理・Worker・SQLite schema・依存版は変更しない。モデル取得・写真再解析・大量検索測定・全依存再監査なし。

## 配布方針と既存証拠

無料のWindowsインストーラーをGitHub Releasesで配布し、videdegi.comに紹介・使い方を掲載する。アプリ独自コードはソース非公開で、MIT/Apache-2.0を適用しない。モデルは別途取得/指定する。音声・動画は将来の更新。

既存のライセンス全文・著作権通知をそのまま保持する。所有者はライセンスの繰り返し調査を終了するよう指定した。完全SBOM不在だけを正式版作成の阻害理由としない。網羅的な内蔵依存の安全/許諾保証を追加するものでもない。今回新たな具体的再配布禁止条件や必須通知不足は確認していない。

dev.2の [監査結果](RC_AUDIT_RESULTS.md) と [最終整理記録](FINALIZATION_RESULTS.md) を継承する。過去の開発版資料にある公開未承認/ライセンス未選択は当時の記録で、現在の所有者方針は本資料を優先する。

## 対応環境と制限

Windows 11 64bit、GPU確認済みRTX 2070（8GB）。他GPU・Windows 10/ARM/32bitは初期サポート対象外。CPU4スレッドは少数人工画像/診断の検証のみで、大量処理速度は未評価。開発用Python/Rust/Node不要。WebView2/VC Runtimeの既存公式導入方式を維持する。

アプリ/インストーラーは未署名。Windows/SmartScreen警告が出る場合があり、署名済みとは表示しない。手動更新のみで、更新前にトレイから完全終了する。クリーンWindows、不足Runtimeの実導入、実トレイマウス・ログイン・スリープ・OS再起動は未検証のまま。確認済みと表示しない。

## 今回の限定スモーク

正式版生成、別IDの隔離QAインストール、配布アプリ/WebView2とWorker起動、日本語検索、データ保持、通知の実配置を確認する。検索は既存の検証済みインデックスを隔離コピーして使い、start/全件再解析を呼ばない。既存大量検索・長時間負荷試験を再実行しない。

結果と最終SHAは以下に追記する。機械記録は `data/release-tests/v1-smoke.json`、`data/release-tests/license-finalization/packaging-results.json`、`data/release-tests/rc-audit/artifacts.json`。

### 実施結果

- 正式版のTypeScript/Vite/Rust release/NSISビルド成功。Workerの再ビルドなし。
- 隔離QAの正式版インストールexit 0。既存QA DBのSHA保持。536ライセンス関連ファイル・通知・ガイドの実配置がソースと一致し、Worker全50ファイルもdev.2と同じ。リリースノートも実配置に含まれる。
- 正式版アプリ/WebView2/Workerを起動し、画面から **「海辺の風景」→coast.png** を確認。アプリ情報は1.0.0、開発版表示なし。既存4件の人工画像ベクトルSHA保持、再解析呼び出しなし。
- 最初の試験は別の既存ドライバーとのnativeポート競合を隔離先チェックで検出して検索前に停止。専用ポートで再実行して成功。アプリの問題ではなく試験環境の修正で、既存ドライバーを停止していない。
- 本番DBは1624件/3フォルダー、integrity=ok、既存ベクトル/設定/キャッシュのスナップショット一致。モデルSHAと旧アプリも不変。記録は `data/release-tests/v1-protected-after.json`。
- 最終インストーラー **34,145,381 bytes（32.56MiB）**。SHA-256 **`38122e6456d1415e6f189703c41f579fb0adcae07f45350433dc50593c77f736`**。保存先 `target/release/bundle/nsis/Local Photo Search_1.0.0_x64-setup.exe`。
- 変更したアプリ本体のPE版/ハッシュのみ配布一覧へ更新。他36件のバイナリ記録を継承し、全依存の再監査はしていない。

## 公開するファイルと残る操作

`data/releases/v1.0.0/` に正式版インストーラー、SHA256SUMS.txt、日本語RELEASE_NOTES.md、USER_GUIDE.md、THIRD_PARTY_NOTICES.md、第三者licenses.zipをまとめる。独自アプリのソース、モデル、写真、DB、設定、ログは配布フォルダーへ含めない。

所有者承認後に、ソース非公開を維持する配布専用GitHubリポジトリでv1.0.0 Releaseを作成し、上記ファイルを添付する。既存ソースリポジトリの履歴を公開リポジトリへPushしない。Release公開とvidedegi.com掲載は今回行わない。
