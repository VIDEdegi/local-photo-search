> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# 音声検索開発への引き継ぎ

2026-10-10。基点は **1.0.0-dev.2**。写真開発は既存成果を確定し、次は動画より先に音声を追加する。今回は音声の実装なし。公開条件の残りは [配布条件](DISTRIBUTION_CLOSURE.md)、検証の差分は [最終整理結果](FINALIZATION_RESULTS.md)。アプリ本体にOSSライセンスを適用せず、Push/公開は所有者判断まで行わない。

## 現在の完成範囲

写真の差分解析、日本語/参照画像検索、全順位の正確な検索と60件ページング、フィルター、サムネイル、プレビュー/ズーム、初回セットアップ、モデル管理、バックグラウンド設定、保存先コピー移行、キャッシュ上限、ヘルプ。GPUはRTX 2070、CPUは4スレッドの少数試験。実トレイマウス・ログイン・スリープ・再起動・クリーンWindowsは未検証。

`docs/RC_AUDIT_RESULTS.md` の既存テストを継承し、写真速度/画像前処理を変更しない。実ユーザーDBは1624件/3フォルダー、512枚の旧速度検証はv0.1.1の記録。合成10万件検索の1.34秒を音声/写真の解析速度と混同しない。

## 再利用する構造

| 部分 | 現在の構造 / 再利用範囲 |
|---|---|
| `src-tauri/src/main.rs` / UI `src/` | Rustが独立Workerを所有。JSON-lines stdin/stdout IPC v1、待受HTTPなし。ウィンドウ/トレイ/停止・再起動/自動起動設定を再利用 |
| `worker/main.py` | `--data`必須。method別ハンドラー、UTF-8、shutdown。音声用メソッド/パラメーターは互換性を保って追加 |
| `worker/ai.py` | `EmbeddingBackend`はtext/image/close、LiteRtBackendはEmbeddingEngine。GPU/visionとも同じbackend、CPU4スレッド、normalize後再正規化。**audio_backend未指定、audio契約未実装** |
| `worker/library.py`, `prefetch.py` | 走査、差分、ジョブ、DB/AIロック、再試行、全順位キャッシュ。現在の拡張子はjpg/jpeg/png/webpだけ。写真の1回デコード・2件先読みは維持 |
| `worker/model_download.py`, `runtime_cache.py`, `diagnostics.py` | 固定モデル公式取得/整合性、モデルSHA別キャッシュ上限1GiB、隔離プロセス診断を再利用 |
| `worker/database.py` | SQLite schema **1**、WAL、synchronous FULL、foreign_keys。settings/folders/models/files/folder_files/embeddings/jobs。起動時processing→pending。将来移行時は既存backup_before_migrationを利用 |

現在の `files.kind` は既定image。`embeddings` と `jobs` の主キーは **(file_id, model_id)**。vectorはfloat32 BLOB。modelsにはSHA/次元/前処理/正規化/query prefix/runtime/backendがあり、写真のプロファイルを保持する。画像の前処理IDは `pillow-exif-rgb-fit1024-jpeg95-v1`、検索prefixは `task: search query | text: `。GPU/CPU切替時も既存のモデル/プロファイル判定を勝手に変更しない。

## 音声で追加するものと未検証点

公式 [Embedding models](https://developers.google.com/edge/litert-lm/embedding_models) は `Content.AudioFile` と `EmbeddingEngine(audio_backend=...)` の例を示す。**現在の740Mローカルモデルと配布Workerでの音声入力は未試験**。SDK APIの存在を製品対応済みとしない。キャッシュにaudio encoder名が存在しても成功の証拠ではない。

最初に短い隔離WAVで日本語テキストとの検索空間、次元/正規化、入力サンプルレート・チャンネル・最大長、GPU/CPU、速度/RAM/VRAM、エラーを調べる。長い音声の分割・重なり・無音処理・境界精度、対応形式のデコード、時刻付き結果・再生位置は追加設計が必要。音声の文字起こしやTTS対応を自動的に含めない。新しいデコーダーを導入する前にサイズ・再配布条件を確認する。

長いファイルには区間の保存が必要。将来はaudio_segments等の**追加テーブル**にfile_id/start_ms/end_msを持ち、区間埋め込み/ジョブを別に管理する案から検討する。既存写真のembeddings主キーを区間用に上書きしない。音声前処理ID・modality・区間条件をプロファイルとして分離し、既存写真検索へ音声結果が混入しないようにする。schema変更は隔離した旧DBコピーのバックアップ/移行/ロールバックから試験する。

## 推奨順序と次回の最初の作業

1. Gitのclean状態とこの資料を確認。元モデルは読み取りだけにし、`data/release-tests/audio-probe/` 等の専用データ・キャッシュで短い人工WAVのAPI可否を検証。環境変数MEDIA_SEARCH_DATAを必ず隔離先へ変更。
2. その結果から対応形式・分割・プロファイルと追加schemaを決定。モデルの再ダウンロードや写真の全件再解析をしない。
3. デコード/区間抽出、区間ジョブの停止再開、テキスト→音声検索をWorkerに追加。旧写真DBコピーとの互換性試験を行う。
4. UIに音声対象切替、区間時刻・再生・元ファイル操作を追加。既存写真フローを回帰確認。
5. 小規模の実音声で検索品質・長時間処理・中断・負荷・依存通知を検証。動画は後の段階。

ビルド環境は `scripts/env.ps1`、公式CPython3.14.8/OpenSSL3.5.9と既存固定LiteRT-LM0.18.0。Worker改修時だけbuild-worker、配布資料のみならTauriの再梱包でよい。成功済み写真テストを理由なく全件再実行しない。最終公開前の配布ゲートは別途維持する。
