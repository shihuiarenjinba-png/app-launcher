# apps-launcher（ローカルアプリ母艦）

ローカルの Streamlit アプリ群を一覧・起動・停止・診断するための母艦ランチャーです。
各アプリ本体（`40-finance/*`, `10-research-lab/*` など）と重い実行環境（`.venv`/生成データ）は
このリポジトリには含めず、**起動の仕組み（実行タブ）だけ**を管理します。

## 構成

| パス | 役割 |
|------|------|
| `launcher.py` | Streamlit 製の母艦 UI 本体 |
| `launcher_core/` | レジストリ読込・プロセス管理・診断・Ollama 連携などのコア |
| `app-registry/*.json` | 登録アプリの定義（entry / port / リンク / タグ など） |
| `config.json` | ランチャー共通設定（host / base_port） |
| `ai/ollama.json` `ai/prompts/` | ログ診断などに使う Ollama 設定とプロンプト |
| `start_stats_app.bat` | 起動用バッチ |

## 起動方法

```bash
streamlit run launcher.py
```

ブラウザで母艦 UI が開き、登録済みアプリの起動・停止・ブラウザ起動・ログ確認ができます。

## アプリを追加する

`launcher.py` 本体は編集せず、`app-registry/` に JSON を1つ追加します。

```json
{
  "id": "my-app",
  "name": "アプリ名",
  "category": "Finance",
  "type": "streamlit",
  "entry": "path/to/app.py",
  "cwd": "path/to",
  "port": 8510,
  "description": "説明",
  "tags": ["..."]
}
```

## このリポジトリに含めないもの

`.gitignore` のアロー方式により、以下は追跡対象外です（手元にはそのまま残ります）。

- `.venv/`（仮想環境）、`__pycache__/`、`*.pyc`
- `10-research-lab/`・`40-finance/` などのアプリ本体（各自別リポジトリ管理）
- `work/` などの生成データ、`logs/`・`*.log`、`.launcher_pids.json`
