# SakuLoca v1.0.1 改名・基本確認

2026-10-11。Local Photo Search v1.0.0をSakuLoca（サクロカ）へ改名。開発元VIDEdegi（ビデデジ）。AIエンジン・Worker・SQLiteスキーマ・依存バージョンは変更していません。

## 確認結果

- TypeScript型チェック、Vite、Rust/Tauri、NSIS、既存鍵による更新署名の生成に成功。
- 正式インストーラーをE:の専用QA先へ新規導入。Windows登録はSakuLoca / VIDEdegi / 1.0.1、実行ファイルはSakuLoca.exe。
- 実アプリ/WebView2/同梱Workerの起動、日本語「海辺の風景→coast.png」、新名称のヘルプ・タイトル、更新確認設定の保存を確認。
- 既存の人工画像4件を隔離コピーして使用。解析を呼ばず、ベクトルSHA-256は前後とも `34ddf249792f62c9a3066582e3ef1ddc855ea6a97477869882f92c3315d82856`、SQLite integrity_checkはok。
- Workerの50ファイルは以前の記録と一致。アプリ識別子・データ保存先・公開鍵は維持。
- 生成したインストーラー本体とtrusted commentの署名を既存公開鍵で検証。latest.jsonのバージョン・署名・新URLと整合。
- 旧UpdaterのGitHub URLはHTTP 200。改名後のリダイレクト確認と新URLの実配信確認は、承認後の公開時に行う。
- 新規試験で作成したアプリ登録は、専用QA先を確認してアンインストール済み。実ユーザーデータは使用・削除していない。

## 配布物

`SakuLoca_1.0.1_x64-setup.exe`：35,280,884 bytes（約33.65MiB）。

SHA-256：`352048f71204721421155501b81e70fdc3d734b05da41b93916ef66adf8ef874`

`data/releases/v1.0.1-public/` にインストーラー、署名、latest.json、SHA256SUMS、リリースノート、ガイド、既存ライセンス通知を用意。公開は所有者の最終承認後。

旧名称版の完全自動移行、クリーンWindows、長時間負荷、OSスリープ/再起動、他GPUは今回検証していません。未署名Windowsアプリの警告は従来どおりです。旧版利用者への問い合わせ案内はリリースノートに掲載しました。
