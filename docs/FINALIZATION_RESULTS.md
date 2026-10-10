> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# 1.0.0-dev.2 最終整理結果

2026-10-10。開始commit `6f2fe5e`、作業ツリーclean、既存インストーラーSHA-256 `6d52632fe40fb3a70b7904fc1d8985f3fcc4bfcba2b6fe67674a7081f3a4d991` を確認して再開。既存ユーザーの写真・モデル・SQLite・ベクトル・設定・キャッシュを変更しない。RC/正式版への昇格、タグ、Push、公開なし。アプリ本体の公開ライセンスも未選択のまま。

## 今回の変更

- LiteRT-LM固定ソースの宣言依存10件について、公式ライセンス全文と版/取得元/本文SHAを追加。Dawnの指定ファイル別Apache条件も省略しない。
- Microsoft公式配布ページのAPIからWebView2 Runtime EULA全文を取得し、SDKのBSDとは別に同梱。インストーラーの同意画面へ全文を組み込み、SmartScreenとMicrosoftへの通信の通知を追加。
- ファイル別監査の判定を更新。SBOM不在だけでは許諾の否定としない。実DLLの追加必須通知に範囲を絞り、espeakの任意TTSターゲットと写真検索を区別。未確定DLLを外して利用者が公式wheelを取得する代替案と、必要な限定改修を具体化。
- Windows 11 64bitを初期サポート対象に統一。RTX 2070以外は未検証、CPU4スレッドの少数試験と大量処理未評価を明記。
- ユーザーガイド・READMEを補い、未公開の日本語リリースノート案、音声検索の構造/互換性/最初の隔離検証の引き継ぎを追加。音声実装なし。

## 検証範囲

写真検索のコード、Worker、モデル、schemaは変更していない。既存の性能・ベクトル一致・GPU/CPU・UI・停止再開・保存先移行・更新/削除の成功記録は [RC監査結果](RC_AUDIT_RESULTS.md) を継承し、今回再実行したとは報告しない。

今回の対象はTauri再梱包と、別製品IDの隔離QAインストールによる実配置のライセンス/通知/SHA一致確認。`scripts/verify-final-distribution.py` が全通知の実配置、公式EULA原文、固定10件の本文SHA、Worker全ファイルの非変更、不適切なDLLの非同梱を検証する。結果は `data/release-tests/license-finalization/packaging-results.json`。クリーンWindowsや実トレイ操作の成功とは扱わない。

成果物の版・サイズ・SHA・署名・最終source commitは `data/release-tests/rc-audit/artifacts.json` と `SHA256SUMS.txt`。現行37PEのファイル別SHAは `docs/DISTRIBUTION_FILES_CURRENT.json`。再梱包によりインストーラーSHAは開始時から変わる。クリーンWindows試験用の入力成果物も今回の版に更新する。

保護データは既存 `rc-audit-before.json` と読み取り比較し、1624件/3フォルダー、ベクトル集計SHAとモデルSHAの保持を確認する。追加結果は検証後に以下へ記録する。

### 実施結果

- `npm run tauri -- build` 成功（TypeScript typecheck/Vite/Rust release/NSIS）。Workerの再ビルド・写真の再解析なし。
- 別製品IDのQAインストールexit 0、隔離QAの既存DB SHAも不変。536ライセンス関連ファイル、THIRD_PARTY_NOTICES、USER_GUIDEがソースとSHA一致。Worker全50ファイルが変更前および実配置と一致。
- 10件の公式本文SHAがsources.jsonと一致。Runtime HTMLがMicrosoft APIの原文と一致。Tauri生成のUTF-8 BOM付きlicense_fileが同意画面用本文と一致し、NSISのlicense page参照も確認。**実画面の同意操作や不足Runtime導入を今回試したわけではない。**
- 不要VC/UCRT/API-set/Intel dispatchは引き続き非同梱。37PEの取得元一致も欠落0。
- 本番DBはintegrity=ok、1624ファイル/1624ベクトル/3フォルダー。設定・AIキャッシュのスナップショット一致。ベクトルSHA `01a08bc22ff1b33c0fd1b89aa57d3b752e0cb29dc7a30874bbb42112efbe8554`、モデルSHA `e7a8a2204b91e0f96e92960e84a09a89212e1633dcb7575a9bf3378b4df77f4c`、旧アプリ本体も保持。記録は `data/release-tests/finalization-protected-after.json`。
- 最終インストーラー **34,151,637 bytes / 32.57MiB**、版 **1.0.0-dev.2**、SHA-256 **`9c101ff9b5d65b298acac58f218c69b5a21183689194854d2d0c6615b4904ad1`**。保存先 `target/release/bundle/nsis/Local Photo Search_1.0.0-dev.2_x64-setup.exe`。未署名の開発版。実行ファイルは `target/release/embeddinggemma-media-search.exe`。
- clean-windows入力のinstallerを同じSHAへ更新。VMの起動・ホストのログイン/スリープ設定変更なし。C空き69.19GiB / E空き1160.13GiBを確認し、作業ファイルはEへ保存。
- 自作の変更箇所はdiff whitespace check、資料のローカルリンクを確認。公式ライセンス/EULA本文の元の空白は保全する。

## 公開を妨げる残りと次の開発

`litert-lm.dll` の実推移依存に関する追加必須通知の充足、クリーンWindowsの不足Runtime導入受入、実トレイ/ログイン/スリープ/再起動の確認。アプリ本体の公開条件、Microsoft開発ツール利用権利、署名/SmartScreen方針は所有者判断。詳細は [配布条件](DISTRIBUTION_CLOSURE.md)。

写真開発の成果を保存して、[音声開発の引き継ぎ](AUDIO_SEARCH_HANDOFF.md) から隔離した短いWAV/API試験へ進める。一般公開の承認が済んだという意味ではない。
