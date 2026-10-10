> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# dev.2 配布条件の最終整理

2026-10-10。前回の `6f2fe5e` の監査を引き継ぎ、不足する通知だけを補った。アプリは **1.0.0-dev.2** のまま。アプリ本体の公開ライセンス・ソース公開は所有者未決定で、第三者の条件と別に扱う。

## 配布ファイルの判定

37個のPEファイルは [ファイル単位一覧](DISTRIBUTION_FILES_CURRENT.md) と同名JSONにパス、実PE版、取得元、SHA、著作権と通知を記録済み。既に確認できたDLLは再調査していない。以下は今回の差分と最終判断。

| 対象 | 実ファイル / 取得元 | 条件と実施した対応 | 状態 |
|---|---|---|---|
| `worker/_internal/litert_lm/litert-lm.dll` | PE ProductVersion **0.2.0**。公式PyPI `litert-lm-api 0.18.0` Windows wheelと同一SHA | Google LiteRT-LM / LiteRT本体のApache-2.0本文は既存同梱。今回、固定ソースの内部依存10件の公式全文を追加 | 本体の再配布許諾あり。内蔵依存の通知充足は下記の具体的な範囲だけ未確定 |
| 同フォルダーの `dxcompiler.dll`, `dxil.dll` | **1.9.2602.17 (21d28f727)**、同じ公式wheel | 該当DXC全文にLLVM系と第三者通知を含む。既存 `licenses/native/DirectXShaderCompiler/` を維持 | 通知準備済み |
| `MicrosoftEdgeWebview2Setup.exe` | **1.3.279.5**、Microsoft公式配信、署名Valid | SDK BSDとは別のRuntime EULA全文を取得。第2節の配布条件と第9節のSmartScreen通知を確認し、同意画面・利用ガイドに反映 | 全文取得と通知不足を解消。Runtime不足PCの実導入は未検証 |
| CPython DLL/PYD、OpenSSL、Pillow、Worker bootloader、小型内積DLL | 既存ファイル別一覧の実版 / 公式CPython・wheel | 公式全文、PyInstaller例外、CPython派生元と変更通知を維持。OpenSSL **3.5.9** 更新済み | 既存監査・検証を継承 |
| アプリのCargo/Lit依存、WebView2 SDK静的loader、NSISプラグイン | 既存248件のWindows Cargoグラフ、SDK **1.0.3800.47**、NSIS **3.11**等 | 個別全文、MPL対象の変更なしソース、NSIS例外等を維持 | 既存監査・検証を継承 |
| 個別VC/UCRT/API-set DLL、Intel OpenVINO dispatch | **配布しない** | 既に除外済み。VCは確認後にMicrosoft公式パッケージを取得し、その導入画面で同意。GPU/CPUは既存検証成功 | 不適切な混在と不要DLLは解消済み |

モデルは同梱しない。既存モデルの指定またはアプリ内の公式取得を利用する。Windows 11への対応限定は、この表の再配布条件を代替しない。

## LiteRT-LMで解消した不足

`licenses/native/LiteRT-third-party/` に以下の公式全文と出所/SHA一覧を追加し、インストーラーに同梱する。

| 依存 / 固定ソースの版 | ライセンス | 本文に含まれる権利者 / 条件 |
|---|---|---|
| Abseil 20260526.0、SentencePiece 0.2.2、tokenizers-cpp 0.1.1 | Apache-2.0 | 各作者。適用通知と本文保持、改変表示。独自アプリのソース公開を要求する条件ではない |
| TensorFlow `d9a8da74…` | Apache-2.0 + 同梱の追加通知 | TensorFlow Authors、UC Regents等。本文を省略せず保持 |
| nlohmann/json 3.12.0 | MIT | Niels Lohmann。著作権・許諾・免責保持 |
| miniaudio 0.11.22 | MIT-0 OR Unlicense | David Reid。両方の全文を保持 |
| stb `f58f558c…` | MIT OR Unlicense | Sean Barrett。両方の全文を保持 |
| Skia `226ae9d8…` | BSD-3-Clause | Google Inc.。著作権・条件・免責保持、推奨表示禁止 |
| Dawn v20260720.160313 | BSD-3-Clause + 指定ファイルのApache-2.0 | Dawn & Tint Authors。完全な複合本文を保持 |
| XNNPACK `d89ef666…` | BSD-3-Clause | Facebook, Inc. and affiliates / Google LLC。全文保持 |

これらは公式ソースで確認した版。DLLに内蔵された版を独立して特定したという意味ではない。PE版をPythonパッケージ版に置き換えていない。

v0.18.0のC API/CMakeとengine BUILDにはespeak依存が見当たらず、`omni/tts/kokoro/BUILD` のphonemizerターゲットには明示的なespeak-ng依存がある。実DLLにもespeak/phoneme文字列は見つからず、Dawn/XNNPACK/SentencePieceの識別文字列はある。したがって **WORKSPACEにGPLのespeak宣言があるだけで、写真検索DLL全体をGPLと決めつける根拠はない**。文字列不在だけで非内蔵を証明したとも扱わない。音声検索は音声生成/TTSとは別で、次回にTTSを取り込まない。

## 残る一点と、解決の選択肢

対象は `litert-lm.dll`。残るのはSBOMという書類名の有無ではなく、**実Windows DLLに含まれるDawn/Tintの推移依存、XNNPACK補助依存、tokenizers等について、今回の本文以外にも保持必須の著作権・第三者通知があるか**という条件充足の確認。公開wheelにはその本文がなく、ソース版とバイナリ版の対応も供給元から確定できていない。Google本体のApache許諾は確認済みだが、それを未知の内蔵ライブラリにも適用してよいとは判断しない。

最小の追加証拠は、公式wheel SHA `eb02dc5d0fc6a894a664cfcc63e3aaf3100973ba2c9a6a7eebf4df8749a01038` に対応する第三者通知またはビルド依存の説明。完全SBOMや全ソース公開を必須書式とはしていない。今回は小さい公式ソースと10件の本文取得で調査を区切り、巨大なソース取得・再ビルド・推測による許可判定は行わない。

証拠を得られない場合の具体的な代替は、配布Workerから `litert-lm.dll` と同時取得のDXC 2 DLLを外し、利用者自身が上記固定SHAの **公式Windows wheel** を取得・検証して3 DLLだけをWorkerの `litert_lm/` に準備する方式。Python開発環境の導入は不要だが、保存先権限、途中失敗の復旧、初回診断の案内が必要になる。これを採用するなら別途その限定改修とGPU/CPU検証を行う。現在のインストーラーからDLLだけを抜いて動作不能にする変更は行っていない。この代替方式は **設計案で、実装・検証済みではない**。

## 公開前の残り

上記DLLの通知充足、クリーンWindows 11のWebView2/VC不足時受入、実トレイマウス・ログイン・スリープ・再起動。所有者は別途、アプリ本体の配布条件、Microsoft開発ツール利用権利、署名/SmartScreenの説明を決める。自動更新は対象外。写真開発の整理を確定して音声の隔離開発へ進むことと、一般公開の承認は分ける。
