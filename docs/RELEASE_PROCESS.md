# 公開・更新の手順

## GitHubの初回設定

`VIDEdegi/local-photo-search` をまずPrivateで作成します。元の開発履歴は個人用メールを含むため公開せず、検査済みの公開用履歴だけをPushします。

- Issues ON、Discussions/Wiki/Projects/自動マージ OFF。
- Description: Windows向けの無料ローカルAI写真検索アプリ。
- Topics: windows, tauri, photo-search, local-ai, embeddinggemma。
- Homepage: https://videdegi.com （紹介ページ自体は別途準備）。
- mainのRuleset: force push/削除禁止、PR経由、必要チェック `basic`。レビュー必須数は0。管理者の通常PRマージを許可し、緊急時用の管理者バイパスを設定。
- Actionsは読み取り専用。Fork PRのSecrets/書き込み権限は許可しない。
- Dependabot alerts、Secret scanning/Push protection、Private vulnerability reportingを利用できる範囲でON。Dependabotの定期PR設定はまだ追加しない。
- CIが初回実行された後に必須チェックを設定。Privateで使えない保護はPublic化直後に適用。

Public化とRelease公開は所有者の最終承認後に行います。PRマージから公開は実行しません。

## 署名鍵

秘密鍵とパスワードはGit・Releaseに含めません。この開発環境では無視対象の `data/private-signing/` に暗号化した鍵とWindows CurrentUser DPAPIで保護したパスワードを保存します。生成ログにも秘密鍵が含まれ得るため公開禁止です。

鍵ファイルだけでなくパスワードも、所有者が別の暗号化媒体にバックアップしてください。DPAPIの保存ファイルだけでは別PCへの復元は保証できません。鍵紛失は既存アプリの署名付き更新を止めます。GitHubのActions Secretsには現時点で登録しません。

公開鍵だけを `src-tauri/tauri.conf.json` に入れます。更新署名はWindows Authenticode署名とは別です。

## 次回の正式更新

1. package.json/package-lock.json/Cargo.toml/Tauri設定のバージョンを正式SemVerへ揃える。リリースノートと通知を更新。
2. 既存のWorkerを再利用できる変更なら再構築・再解析しない。変更に必要なチェックだけ実施。
3. `./scripts/build-signed.ps1` でインストーラーと `.sig` を作成。
4. `python scripts/prepare-release.py` で `latest.json` とSHA-256を生成。URL・署名・バージョンを確認。
5. ローカルコミット/タグを確定。公開済みタグは変更しない。
6. 所有者承認後にPushし、GitHub ReleaseをDraftで作成。インストーラー、`.sig`、`latest.json`、SHA256SUMS、通知/ガイドを添付し、手動公開。

開発版・QA版は正式Releaseに載せません。`latest.json` の署名は `.sig` の内容そのものを使います。初回v1.0.0は既にv1.0.0を利用しているPCには更新として表示されません。

## 手動更新

トレイから完全終了し、公式Releasesのセットアップを同じインストール先に実行してください。モデル・DB・写真は保持します。更新機能が使えない場合もこの手順を利用できます。
