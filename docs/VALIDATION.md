> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# 検証結果 — 0.1.0時点の保存記録

この文書は旧版の検証結果です。v0.1.1の実写真512枚は[PERFORMANCE_AND_CACHE](PERFORMANCE_AND_CACHE.md)、dev.1は[RELEASE_V1_VALIDATION](RELEASE_V1_VALIDATION.md)、現行dev.2は[RC_AUDIT_RESULTS](RC_AUDIT_RESULTS.md)を参照してください。以下の上位1,000件制限はdev.2で解消済み。次機能案は履歴であり、音声/動画は写真版の安定後とする。

2026-10-10、このPCのWindows 11 / RTX 2070で確認。作成した人工画像4種類（りんご、海辺/船、森/道、街並み）と、その作業用コピー24枚を使用。ユーザーの実写真は未登録・未走査。実写真での最終精度評価は別途行う。

## 実機で成功したこと

| 対象 | 結果/証拠 |
|---|---|
| Python LiteRT-LM CPU/GPU | 既存モデルの文章/画像埋め込み768次元、L2正規化、RTX 2070 D3D12選択ログ。probe JSONとPHASE0参照 |
| 日本語の意味検索 | りんご・海辺・森・街並みの4クエリすべてで対応画像が第1位。4/4は小さな人工データでの動作確認であり正解率を表さない |
| 類似画像検索 | 自分自身が第1位、さらに切り抜き/縮小/JPEG再圧縮した別参照画像から元の海辺が第1位 |
| 複数フォルダー | 2フォルダー横断、対象の有効/無効、名前/PNG/更新日フィルター |
| 再起動/差分 | 保存済み解析日時を再利用、変更なし0枚再解析、1枚変更で1枚だけ再解析、消失ファイル除外 |
| 接続切れ | テストフォルダーを一時的に別名へ変更し、アクセス不能時にベクトルを維持、再接続で結果が復帰。本物のSMB/外付け切断は未検証 |
| 中断/再開 | 配布WorkerをGPU実行。24枚中2枚保存後に一時停止→再起動。3枚保存後に処理中Workerを強制終了→復旧して24枚完了。既保存ベクトルのハッシュ一致、SQLite integrity_check=ok |
| CPU/GPU互換性 | 切替後も24ベクトル/1モデルプロファイルだけを保持し、変更なしの再解析0枚 |
| 元ファイル保護 | 24枚の検証画像の解析前/後ハッシュ一致。差分テストの変更/削除対象は検証用コピーだけ |
| Tauri/WebView2 | 本番exe + 配布Workerで日本語フォーム送信、海辺が先頭、遅延サムネイル読み込み、プレビュー実表示、拡大後の幅が1.25倍 |
| 表示 | グリッド/リスト、ライト/ダーク、幅1000/860でメイン領域の横はみ出しなし |
| キャッシュ | 設定操作のIPCでAIキャッシュだけ削除し、インデックスを保持したまま再検索。生成ファイルの整理・未知ファイル保持も単体確認 |
| Windows起動・終了 | 2つ目の起動は終了して既存1Workerを維持。親exeの強制終了でWorkerが残らず、DB整合性ok |
| 元ファイルを開く | 登録済みcoast.pngのOS起動とExplorer /select要求が成功。外部ビューアの画面表示は目視未確認 |
| インストーラー | E/appへインストール、同版再インストール、アンインストール後再インストール。4枚のベクトルのハッシュ維持。インストール済みexeでもWebView2検索/プレビュー検証成功 |
| 配布内容 | モデルなし、Python実行環境同梱、ライセンス通知同梱。最終パッケージのWorkerと本番出力一致。Tauri NSIS識別タグ3bytes以外のexe内容一致 |
| ビルド/静的検査 | TypeScript typecheck、Python compileall、Rust fmt check、本番Tauri Windows exe + NSIS .exe生成成功 |

## 検証コマンドとローカル証拠

READMEの環境設定後：

```powershell
python scripts/test-runtime-cache.py
python scripts/test-worker.py
python scripts/test-checkpoints.py
python scripts/test-desktop.py
python scripts/test-lifecycle.py
python scripts/test-installer.py
python scripts/test-native-actions.py
```

デスクトップ/インストーラー/OS起動テストは専用tauri-driverが必要。driverの起動時に `MEDIA_SEARCH_DATA=data/ui-test` を指定。installerテストは安全ガードにより今回の `PROJECT_ROOT/app` のみに作用する。同版更新の確認であり、将来の異なるバージョンからの更新確認を代替しない。

`data/{worker,checkpoint,desktop,lifecycle,installer,native-actions}-test-results.json`、`data/probe-{cpu,gpu}-image.json`、`data/desktop-{light,dark,preview}.png`。個人設定/DB/画像をGitへ入れない方針により証拠の実ファイルはローカルに保持。この文書には検証結果だけを記録する。

インストーラーテストのアンインストールは、NSISが子プロセスを起動する仕様を考慮し `_?=` オプションで完了まで待機する。参考：[NSIS公式仕様](https://nsis.sourceforge.io/Docs/Chapter3.html#3.2.2)。最初の検証で待機不足による再インストールの競合を検出し、テスト側を修正した。

## 未検証・初期版の制約

- 実写真の意味検索精度、日本語の複雑な検索精度、大規模データ、専用VRAM計測、意図的なGPUメモリ不足、スリープ/シャットダウン中の保存。
- ネイティブのファイル/フォルダー選択ダイアログでの実選択操作。フォルダー登録/画像指定/モデル指定は実IPC経由で検証した。
- 外部画像ビューアでの描画、別PC/開発ツールがない新しいWindowsへのインストール、WebView2未導入PCでのbootstrap、異なるアプリ版からの更新。
- スキーマ移行/バックアップ機構は実装したが、現在v1のみ。将来のv1→v2移行は新スキーマ実装時に検証する。
- 意味検索は正確な全件コサイン計算、上位1000件/60枚ページ。大規模向け近似検索・スクロール仮想化は未実装。
- 更新日/サイズ/ファイルIDが同一のまま意図的に内容を変えた場合は差分検知できない。
- 動画・音声・独立常駐・自動起動・自動更新・コード署名・古いモデルプロファイル削除UIは未実装。
- SDKのOpenVINO/NPU警告は未使用アクセラレーターについてのもの。RTX 2070 GPU/CPUの採用経路では実行成功。一般配布前には同梱DLL/推移的依存のライセンス再監査が必要。

## 次の順番

ユーザー指定の実写真1〜2フォルダーで精度・エラー・速度/メモリを計測し、数千〜数万枚で安定化。別PCで配布/更新を確認。その後FFmpegを使った動画シーン、音声セグメント、独立常駐Workerへ進める。

## 0.1.1の追加検証

[GPU速度・AIキャッシュ調査](PERFORMANCE_AND_CACHE.md)参照。実写真512枚の隔離再解析で既存ベクトルとの完全一致、実DBとモデルの保全を確認。先読み/空き容量/キャッシュ上限の安全性8件、既存の実モデル・配布Worker・実WebView2テスト合格。NSISで0.1.0→0.1.1更新後も元の512件/未処理1,112件とキャッシュを保持。意味検索精度の新たな実写真ランキング評価や10万件の性能試験ではない。
