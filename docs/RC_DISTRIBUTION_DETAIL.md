> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。

# dev.2 配布ファイルと再配布条件の調査

2026-10-10。判定は開発用成果物に対するもの。未確定条件を残したままRC/一般公開に進めない。

**追補:** その後、WebView2 Runtime全文とLiteRT宣言依存10件の本文を追加し、同意画面/配布通知に反映した。下記は前回監査の記録として保持する。現在の判定、SBOM不在だけでは禁止としない整理、残る具体的な条件は [最終整理](DISTRIBUTION_CLOSURE.md) を優先する。

## ファイル単位の証拠

[dev.1一覧](DISTRIBUTION_FILES_DEV1.md)は改修前の82 PE（EXE/DLL/PYD/NSISプラグイン）の記録。[現行一覧](DISTRIBUTION_FILES_CURRENT.md)と同名JSONに実ファイルSHA-256、PEのFileVersion/ProductVersion、取得元、インポート、ライセンス、著作権、通知の場所を記録する。PEが版を報告しない場合は「未報告」で、親パッケージの版を推測で記入しない。libffiはCPython固定ソースが3.4.4を指定するがDLL自身の版は未報告。

PyInstallerの実Analysis TOCで取得元を特定し、同名ファイルの探索だけでなくSHA一致を確認。NSISの同じスクリプトを非圧縮で一時コンパイルし、実際に埋め込まれるプラグインを抽出する。生成uninstall.exeと最終installer.exeのハッシュはRC_AUDIT_RESULTSの成果物記録を参照。WebView2LoaderはDLLとしてではなくStatic.libとしてアプリにリンクされているため別途照合した。

## LiteRT-LM / LiteRT: 未解決の公開ゲート

[公式PyPI litert-lm-api 0.18.0](https://pypi.org/project/litert-lm-api/0.18.0/) Windows wheelは26,403,380 bytes、SHA-256 `eb02dc5d0fc6a894a664cfcc63e3aaf3100973ba2c9a6a7eebf4df8749a01038`。監査用に公式wheelだけ取得し、導入済みlitert-lm.dll、dxcompiler.dll、dxil.dll、旧Intel dispatchの4 DLLがすべて同じバイト列であることを確認。モデルを取得し直していない。

Pythonパッケージは0.18.0だが、native litert-lm.dllのProductVersionは**0.2.0**。固定版[LiteRT-LM v0.18.0](https://github.com/google-ai-edge/LiteRT-LM/tree/v0.18.0)はApache-2.0で、WORKSPACEはLiteRT commit `26895c9fbcc25c43faa8c1a98cd1fd28951602c3`、TensorFlow commit `d9a8da74b4c3de28a39ab34ad007838d6bc30c67`等を指定する。該当LiteRT LICENSEを追加。

しかしwheelにLICENSE/NOTICE/SBOMがなく、Windows DLLのリンクマップ/ビルド証明と完全な内蔵通知を確定できない。v0.18.0のWindows prebuiltツリーと現在mainのツリーも異なり、mainのビルド内容をこのwheelの証拠にしていない。宣言依存にはAbseil 20260526.0、SentencePiece 0.2.2、nlohmann/json 3.12.0、miniaudio 0.11.22、stb、Skia、tokenizers-cpp 0.1.1、espeak-ng 1.52.0等がある。**宣言はWindows DLLへのリンクの証明ではない**。espeak-ngのGPL条件を「このDLLに入っている/いない」とも断定しない。

必要な次の証拠: 当該wheel SHAに対応するWindows build commit/options/link mapまたはSBOM、リンクされた各依存の正確な版と全文通知、GPL等の条件の適用有無。Apacheの本文だけで全依存の条件を代替しない。これが得られなければ、このDLLを同梱して一般配布しない。公式ランタイムを利用者が別途取得する方式も選択肢だが、今回は開発版を維持し構成を根本変更していない。

## OpenVINO / Intel NPU

旧wheelの `vendors/intel_openvino/dispatch/LiteRtDispatch.dll` は未同梱の `openvino.dll` をインポートする。アプリが選択するWebGPU/GPUとXNNPACK/CPUはIntel NPU dispatchを使わないため、**dispatchを同梱対象から除外**した。実配布WorkerのGPU/CPU診断が両方成功。OpenVINO本体を追加取得/導入せず、他GPU/NPUの対応を主張しない。

[OpenVINO 2025.4.0 source LICENSE](https://github.com/openvinotoolkit/openvino/blob/2025.4.0/LICENSE)はApache-2.0だが、これは未知の旧dispatchが必要とするIntel binaryの版/条件を確定するものではない。Intel配布のバイナリや第三者依存には実製品版の条件照合が必要。`licenses/native/OpenVINO-reference`は参照資料と明記しており、再配布許可の判断根拠に使わない。

## Microsoft Visual C++ / UCRT

旧dev.1のMSVCP140.dllはMSVC開発ツール、VCRUNTIME DLLはCPython、UCRT/API setsはCodexのlibheif実行環境からPyInstallerが収集していた。出所と保守経路が混在していたため、個別DLLをパッケージから除いた。

[Microsoft再配布資料](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files)はlicensed Visual Studio usersとライセンス条件による制限、公式Redistributableのcentral deploymentを説明する。単に「無料DLLなので再配布可」としない。現在はVCパッケージ自体も同梱せず、利用者が不足時に確認し、[公式取得先](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170)から取得して公式利用条件で導入する。

取得時のMicrosoft Authenticode、製品名x64、最低版を確認。今回の実取得は14.44.35211.0、25,635,768 bytes、署名Valid。ホストの共通Runtimeは14.51.36247.0であり削除/更新していない。Windows PowerShell 5.1で実取得と署名検証成功、未署名/別製品/オフラインの拒否を隔離fixtureで確認。ユーザー単位のアプリ導入と、必要時に管理者確認を要するMicrosoft共通Runtime導入を分けた。アプリ削除で共通Runtimeを削除しない。

Windows 10/11は[OSのUCRT](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment)を利用する。開発PCのAPI shimを持ち込まない。Build Tools/SDKの利用条件とアプリ内のstatic runtimeを含む開発者の利用権利確認も、アプリ所有者による公開前の確認対象であり、Apache通知だけでMicrosoftの権利を付与するものではない。

## DXC / WebView2 / NSIS

DXCのProductVersionは1.9.2602.17 (21d28f727)。[該当Microsoft revisionの全文](https://github.com/microsoft/DirectXShaderCompiler/blob/21d28f727/LICENSE.TXT)（LLVM系と組込第三者の通知含む）を保持し、ライセンス条件をアプリの条件で上書きしない。

WebView2 SDKのofficial NuGet 1.0.3800.47のx64 Static.libとRust crate同梱libがバイト一致。SDK LICENSE.txt（Microsoft BSD 3-clause）に加え不足していたNOTICE.txtを同梱。SDKとRuntimeの条件は別。

WebView2 Bootstrapperは1.3.279.5/1,857,232 bytes/Microsoft署名Valid。[公式導入ガイド](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)が認める小型Bootstrapper同梱方式とTauri標準embedBootstrapperを使用する。NSISdlがHTTPS取得に対応しない問題を回避。Runtime本体は同梱せず、導入前にMicrosoftの条件/通信を案内する。Runtime条件の全文固定保存は、公式配布ページの動的利用条件データ取得が503で未完了。SDKのBSD条件をRuntimeの条件と誤認しない。Runtime不足PCで実導入/条件導線も公開前の受入ゲート。

NSIS 3.11のCOPYING（zlib/libpng、bzip2、CPL/LZMA例外）を同梱。内蔵プラグインとstubは改変していない。nsis-tauri-utils 0.5.3は公式SHA-1一致を検証し、固定tagのMIT全文を同梱。

Windows Cargoグラフ（ビルド依存含む）248件を個別一覧と実通知ファイルで照合。alloc-stdlib 0.3.0、selectors 0.38.0、tauri-plugin 2.7.1、webview2-com 0.39.1、webview2-com-macros 0.8.1、webview2-com-sys 0.39.1の6件は通知ファイルが欠けていた。各published crateの.cargo_vcs_info.json固定commitの公式LICENSEを取得。selectorsはCargoとソースヘッダーのMPL-2.0に対応するMozilla正式本文、変更なしcrateソース、固定ソース取得先を同梱した。現行Windows依存の一覧/ファイル欠落は0。これは別配布native wheelの完全性を保証しない。

WebView2自体には[Microsoft公式の診断データ方針](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/data-privacy)がある。アプリ独自のテレメトリー未実装と、Runtime自身の必須/任意診断データや更新通信は区別する。写真/検索語の外部送信機能は追加していない。一般配布時にRuntime条件とプライバシー説明の受入も確認する。

## CPython / Pillow / 内蔵ネイティブ依存

CPython 3.14.8はPSFと同梱第三者通知、PyInstaller 6.22.3 bootloaderはGPLと例外全文を同梱。Pillow 12.3.0の配布wheel LICENSEはMIT-CMU/HPNDに加え、Brotli 1.2.0、FreeType 2.14.3、HarfBuzz 14.2.1、LCMS 2.19.1、libavif 1.4.2、libjpeg-turbo 3.1.4.1、libpng 1.6.58、libwebp 1.6.0、OpenJPEG 2.5.4、libtiff 4.7.1、xz 5.8.3、zlib-ng 2.3.3の全文通知を含む。著作権/免責/各条件を削らない。

実行時のPillow featuresとPE版を照合。LCMSは実行APIが2.19までしか報告せず、2.19.1はwheel通知上の版と区別。CPython実行時SQLite=3.50.4/OpenSSL=3.5.9。libffiはDLL未報告、公式CPython固定ソース指定3.4.4。小型検索DLLはCPython補償和から派生しPSF本文と改変元を同梱。DLLは外部PEインポートなし。

## CPython / OpenSSLセキュリティ更新

旧3.14.3に同梱されたOpenSSL 3.0.18には、[公式の後続修正](https://www.openssl-library.org/news/vulnerabilities-3.0/index.html)があった。CMS/DTLSサービスを提供しないことだけでHTTPS証明書処理も安全とは判断しなかった。

[公式CPython 3.14.8のセキュリティリリース](https://www.python.org/downloads/release/python-3148/)はWindows同梱OpenSSLを3.5.9へ更新している。[公式NuGet方式](https://docs.python.org/3.14/using/windows.html#the-nuget-org-packages)のx64パッケージをE側へ別置きし、旧環境を残した。取得15,554,015 bytes、展開41,662,246 bytes。package SHA-256 `ce85f674d9a63029f709cbff7a3da1c6bc5bfcfaefdd9999f98fa0290470c454` を固定し、python.exe/python314.dllのPSF署名Validを確認。インストーラーの利用者にPythonの導入を求める変更ではない。

`prepare-python-runtime.ps1` は同じCPython 3.14 ABIの既存固定第三者パッケージを再利用し、無関係なOpenSSL DLLを混ぜず公式runtime全体を更新。LiteRT-LM 0.18.0/Pillow 12.3.0/PyInstaller 6.22.3は変更なし。build-workerは3.14.8/3.5.9を必須チェックする。配布WorkerのCPython由来21 DLL/PYDが公式NuGetとバイト一致。実行中のfrozen WorkerからPython 3.14.8/OpenSSL 3.5.9/検索nativeを取得し、最小PATHの正常起動/終了、同じbuild runtimeのHTTPS証明書検証を確認した。

CPython固定ソースのPCbuild/python.propsもOpenSSL=3.5.9、SQLite=3.50.4、libffi=3.4.4、zstd=1.5.7を指定。pyexpatの組込Expatは公式releaseで2.8.5に更新。OpenSSLのApache全文は固定3.5.9 tagから同梱。[OpenSSL 3.5の公式一覧](https://www.openssl-library.org/news/vulnerabilities-3.5/index.html)と修正版を照合した（2026-10-10）。これをLiteRT/Pillowを含む全native依存に脆弱性がない証明とはしない。

正確な内積/合成10万件、実モデルと人工画像の解析/日本語検索/類似/差分/停止再開、配布Worker/インストーラーは更新後に再試験。実ユーザーの写真/モデル/ベクトルは再解析しない。証拠は `packaged-runtime.json`、`python-3.14.8-acquisition.json` と [dev.2検証結果](RC_AUDIT_RESULTS.md)。旧OpenSSL更新ゲートは解決したが、native wheelの完全SBOMとクリーンWindows受入は継続する。

## 公開前に所有者が決めること

アプリ本体の公開ライセンス、Build Tools利用権利、コード署名/SmartScreenの説明方針。ユーザーは「今は決めず開発版を維持」を選択した。ソース公開/非公開も未決定で、MIT等を勝手に適用していない。署名鍵/ホスティングなしで自動更新を追加せず、手動更新を優先。上記未確定条件とクリーンWindows受入完了まではdev.2を維持する。
