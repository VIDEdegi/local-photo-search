> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# dev.2 RC監査・改修・検証結果

追補: 本文は `6f2fe5e` までの実施記録。後続の通知追加・同意画面・配布資料の差分は [最終整理結果](FINALIZATION_RESULTS.md)、現在の配布条件は [DISTRIBUTION_CLOSURE](DISTRIBUTION_CLOSURE.md)。以下の成功済み性能/UI試験を再実行したという意味ではない。

2026-10-10、開始commit `3ea644b`。現行 **1.0.0-dev.2**。ユーザー指示により公開ライセンスは選択せず開発版を維持。LiteRT-LM内蔵通知、Microsoft Runtime条件、クリーンPCと実OS操作の受入が残り、**RC/正式版には昇格しない**。Push/公開なし。

## 修正済み

- 合成10万件検索のPython内積ループを正確な小型C実装へ変更。従来と同じ積/補償和、全順位スコア一致。近似探索、モデル/画像処理/ベクトル形式/SQLiteスキーマ変更なし。
- 上位1,000件制限を解消。旧heapの同点境界でID順を保持しない問題を修正。全候補のスコアとIDだけキャッシュし、60枚のページ情報だけ読む。フィルター変更/走査終了/フォルダー操作の無効化を整備。
- 開発者PATHから混入したUCRT/API sets/個別VC DLL、未使用Intel NPU dispatchを同梱から除外。公式VC取得、確認、署名/製品/版チェック、失敗時の再試行とオフライン案内を追加。
- WebView2のHTTPS取得にNSISdlを使う問題をTauri標準embedBootstrapperで回避。取得済みBootstrapperのMicrosoft署名をビルド時にも確認。
- Windows PowerShell 5.1のUTF-8読込とPowerShell 7由来モジュールパスの不具合を修正。共有RuntimeのUACとアプリのユーザー単位導入を区別。
- 公式CPython 3.14.8をE側へ別置きし、OpenSSL 3.0.18を3.5.9へ更新。21の同梱DLL/PYDを公式NuGetとバイト照合。旧build環境とシステムPythonは保持。署名・固定SHA・HTTPS証明書検証を確認。
- Tauriの標準無人更新にある強制終了経路を拒否処理へ置換。Restart Managerの状態確認に失敗したときも既存ファイルを変更せず中止する。
- SDK Static.libを公式NuGetと照合してWebView2 NOTICEを追加。NSIS/Tauri/OpenSSL/CPython派生Cの通知と出所を同梱。DLL/EXE/PYD/NSISプラグインをファイル単位で記録。
- Windows Cargo依存248件を実グラフで照合し、6件の通知不足を修正。公開crateのVCS commitに対応する全文、MPL対象selectorsの変更なしソースを添付。
- アプリ内ヘルプ/利用ガイド/READMEの1,000件制限やRuntime通信説明を現実装へ合わせた。初回UI、背景設定、移行は既存成果を継承。

## 今回の検証

実ユーザーデータを使う変更試験は実施していない。`data/release-tests/rc-audit`、既存の隔離test領域、E側tmpの合成DBだけを使用。モックと実動作を区別する。

| 検証 | 結果・範囲 |
|---|---|
| 正確な内積 | 1,200ランダム内積でPython sumとdoubleビット一致。破損/欠落補助DLLは正確なPythonへfallback |
| 合成10万件 | CPython 3.14.8上で旧Libraryソースと比較、6.910913→1.335906秒（5.173倍）。更新前も約1.3秒。AI生成/モデル初期化を含まず、OS cold-cache未保証 |
| 合成順位/ページ | 全10万候補、全先頭1,000、1,001位以降/中間/末尾/範囲外、同点、ファイル名/形式/日付の組合せ、無効化/完全走査消失、integrity=ok |
| ページ/RAM | キャッシュ済み5ページ計0.008133秒。全順位キャッシュ12,400,984 bytes（11.83MiB）、ベクトルなし。10万件DB+WAL831,208,528 bytes |
| AI回帰 | 実モデル、人工4画像、日本語4クエリ/画像類似/差分0→変更1/削除/模擬切断復帰/停止再起動が成功 |
| 同梱Worker最小PATH | 更新後にPython/Node/RustをPATHから外してGPU/CPUとも768次元テキスト+64px画像診断成功（プロセス起動を含む7.846/5.251秒）。既存VC/WebView2があるホスト。クリーンPC/CPU実写真速度の証明ではない |
| runtime/TLS | frozen環境がPython 3.14.8/OpenSSL 3.5.9/native検索と報告、shutdown=正常。build runtimeの実HTTPS証明書検証成功。SQLite=3.50.4、Expat=2.8.5 |
| 実WebView2 UI | 日本語検索、サムネイル、プレビュー、125%拡大実寸、リスト/ダーク、860/1000px幅、類似IPC、AIキャッシュ削除後も隔離ベクトル保持 |
| 初回案内/背景 | モデル未設定から既存モデル参照→GPU診断→登録→人工24枚、設定途中reload、背景ONでnative IPC close後継続、停止時1件保存、再開で24件、showで再表示、ヘルプ/設定表示 |
| Worker異常終了 | 対象の隔離子Workerだけ強制終了。アプリが残り日本語案内、native再起動で日本語検索復旧、ベクトルSHA不変、wizard段階保持 |
| QAインストーラー | 別製品名/保存先で0.1.1→dev.2更新→再導入→削除→再導入、別DBのSHA保持、実行中の更新/削除拒否、対象アプリを勝手に終了しない |
| 更新状態確認の故障 | 実NSISを使いsession不可/登録失敗/process列挙失敗を各注入。3件とも終了コード2で中止し、隔離導入済みexeのSHA保持。Tauri最終確認の強制終了も無効化 |
| VC取得/復旧 | PS5.1で公式約25MiB実取得/署名/版/製品チェック成功。未署名、Microsoft署名済み別製品、通信失敗、無効な保存先はfixture注入で拒否を確認。ホストへRuntime導入していない |
| 配布ファイル/通知 | 現行37 PEの実取得元SHA一致。Windows Cargo248件の通知一覧・ファイルを照合、欠落0。native wheelのSBOMが完全なことを意味しない |
| 基盤/解析安全性 | test-release-foundation 9件、test-pipeline-safety 8件成功。モデル取得の範囲/再開/破損/通信失敗/同意、移行コピー/失敗時元保持、先読み/低容量/壊れた画像/停止を隔離試験 |

実写真10万枚や数千件の追加解析は行っていない。v0.1.1の512枚/3.29枚秒等は従来記録で、今回同条件の速度/RAM/VRAM/GPU温度再測定とは主張しない。AI入力、推論、先読みを変更せず、人工画像と既存SQLite/ベクトルの互換性を検証。AI固定キャッシュ298.17MiBと1GiB管理を維持。

## 未解決の公開阻害

1. **LiteRT-LM Windows wheelの実SBOM/完全な内蔵通知**。公式wheel一致は確認したが、版/リンク内容/推移条件の確証が不足。GPL宣言依存の適用有無も推測しない。
2. **WebView2 Runtimeの条件全文と導入導線**。SDKのBSD通知は解決済みだがRuntime条件は別。公式配布ページの動的データ取得が503で全文固定保存は未完了。Microsoft公式導入ガイドに沿うBootstrapper方式を採用し、Runtime不足PCで受入が必要。
3. **開発ツールなしのクリーンWindows受入**。ホストの最小PATH試験だけで配布可能としない。WebView2/VC不足時の実導入、Microsoft Runtime条件の表示導線、オフライン復旧、正式製品名の旧版更新/データ保持が未検証。
4. **実トレイマウス、Windowsログイン、スリープ/復帰、OS再起動**。IPCでのclose/show/pause/startと実Worker障害復旧は成功しているが、実OS操作の代替ではない。
5. アプリ本体の公開条件はユーザーが今は未決定と指定。Build Tools利用権利/署名・SmartScreen方針も公開前の確認対象。MIT/Apache等を勝手に適用していない。

Computer Useは対象ウィンドウ列挙まで成功し、その後の操作許可がタイムアウト。クリック成功やトレイ実マウス確認とは記録しない。トレイの対象ウィンドウも列挙されなかった。ホストのログイン設定、共通Runtime、セキュリティ設定、スリープ/再起動を変更していない。

## 成果物と記録

ローカル変更は検索改善 `32c8a54`、公式runtime更新 `85a21f4`、導入/更新安全化と配布通知 `d31db6f` に分けてコミット。監査文書と保護データ検証ツールも別コミットで保存する。アプリ本体のLICENSEを新設せず、RCタグ/Push/公開は行わない。

- インストーラー: `target/release/bundle/nsis/Local Photo Search_1.0.0-dev.2_x64-setup.exe`
- 実行ファイル: `target/release/embeddinggemma-media-search.exe`（Worker/resourcesと共に使う）
- installer論理サイズ34,129,734 bytes（32.55MiB）、SHA-256 `6d52632fe40fb3a70b7904fc1d8985f3fcc4bfcba2b6fe67674a7081f3a4d991`。アプリ/installerは未署名、公式WebView2 BootstrapperはMicrosoft署名Valid。
- 全PE一覧: `docs/DISTRIBUTION_FILES_CURRENT.md` / JSON、改修前: DEV1版
- 最終版/署名/installer・QA uninstallerのSHA: `data/release-tests/rc-audit/artifacts.json` / `SHA256SUMS.txt`
- 証拠: exact-search.json、installer-results.json、installer-failures.json、vc-runtime.json、packaged-probes.json、packaged-runtime.json、setup-background.json、desktop-test-results.json、recovery-results.json、native-versions.json
- 実ユーザーデータ終了時比較: `data/release-tests/rc-audit-after.json`（開始baseline=rc-audit-before.json）
- [クリーンWindows手順](CLEAN_WINDOWS_ACCEPTANCE.md)。prepare-clean-windows.ps1は入力コピーとwsb生成だけで、環境機能の追加/起動/インストールをしない。
- [ファイル別の再配布調査と公式資料](RC_DISTRIBUTION_DETAIL.md)、[利用ガイド](USER_GUIDE.md)。コミットはGit履歴で参照。RCタグ/公開タグは作成しない。

OpenSSL更新後に上表のsource解析・検索、同梱Worker診断、実WebView2 UI/異常終了復旧/初回24画像の背景解析、隔離QA更新/再導入を再試験済み。ゲスト用PowerShellスクリプトもホストの別保存先で実行して3.14.8/3.5.9を確認したが、ホストには開発ツールが存在するためクリーンWindowsの合格記録にはしない。

公開ライセンスはユーザー指示により今は選ばず開発版を維持。今後ユーザーの確認が必要な作業: 配布時の利用条件と署名方針、利用可能なクリーンVM/実機で上記受入手順、実トレイ/ログイン/スリープ/再起動の確認。native通知とMicrosoft Runtime条件が確定し、受入試験後にRCへ進めるか再評価する。今回RCへの昇格は行わない。
