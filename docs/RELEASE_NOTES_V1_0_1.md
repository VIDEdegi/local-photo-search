# SakuLoca v1.0.1

Local Photo Searchを **SakuLoca（サクロカ）** に改名しました。名前の由来は「サクッと、ローカル、サーチ。」開発元は **VIDEdegi（ビデデジ）** です。

Windowsのアプリ名、実行ファイル・インストーラー、スタートメニュー、ウィンドウ、トレイ、自動起動、アイコン、ヘルプを新名称に統一しました。新しい配布先は [VIDEdegi/sakuloca](https://github.com/VIDEdegi/sakuloca) です。

写真検索のAIエンジン・SQLiteスキーマ・解析結果は変更していません。写真・モデル・検索データを削除せず、既存の更新署名鍵を継続使用します。内部識別子と `%LOCALAPPDATA%/LocalPhotoSearch/` の保存先は互換性のため維持します。新旧のインストールが共存する場合があります。旧版からの完全自動移行は提供しません。

<small>旧名称『Local Photo Search』v1.0.0をご利用中の方は、SakuLocaへの移行についてGitHub Issuesからお問い合わせください。</small>

問い合わせ先：[GitHub Issues](https://github.com/VIDEdegi/sakuloca/issues)

## インストールと更新

[GitHub Releases](https://github.com/VIDEdegi/sakuloca/releases) の `SakuLoca_1.0.1_x64-setup.exe` を取得してください。「Source code」は開発者向けです。AIモデルは別途指定・取得します。Python・Rust・Node.jsの開発環境は不要です。

SakuLocaは設定から署名付き更新を確認し、内容を確認して導入できます。起動時チェックは設定でOFFにできます。更新前にWorkerを安全に停止します。取得失敗時はトレイから完全終了し、新しいインストーラーで手動更新してください。

## 対応環境・制限

Windows 11 64bit、GPU確認済みはRTX 2070（8GB）。他GPUは未検証。CPUは4スレッド・少数人工画像で確認済みですが、大量写真の実用速度は未評価です。Windows 10・ARM・32bitは初期サポート対象外です。

実行ファイル・インストーラーはWindowsコード未署名のため、SmartScreen警告が出る場合があります。Updaterの更新署名とは別です。クリーンWindows・OSのスリープ／再起動の受入確認は残っています。

無料・オープンソース（独自コードはApache-2.0）。第三者部分とAIモデルは元の条件を維持します。通知は `THIRD_PARTY_NOTICES.md` と `licenses/`。写真・検索語のクラウド送信やアプリ独自テレメトリーはありません。
