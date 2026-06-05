# Launcher Upgrade Plan

## 目的

`C:\Users\aaron\apps\launcher.py` と関連する Streamlit ランチャーを、単なる起動ボタン集ではなく、ローカルアプリ、研究スクリプト、フォルダ、ログ、AI診断をまとめて扱える「ローカルアプリ管理ダッシュボード」に育てる。

このメモでは、まだ実装には入らず、理想構成、Ollama の配置、追加しやすいファイル構成、削除候補判定、リンクフォルダの扱いを整理する。

## 現在の前提

- `C:\Users\aaron\apps` がローカルアプリ群の親フォルダ。
- `10-research-lab` は研究系の重要フォルダで、削除・大きな整理対象からは外す。
- `research-scripts` は研究スクリプト群で、再構築できるとしても価値があるため残す。
- `research-scripts\.venv` は大きいが、現時点では研究環境維持のため削除しない。
- 直下の `research-lab`, `research-scripts`, `pdf-converter`, `app`, `bpp` などは多くがジャンクション。
- ジャンクションはリンク入口として便利なので、基本的には残す。
- 文字化けしている README、UI 文言、config 表示名は編集候補。

## 目指す姿

ランチャーを「固定された番号付きメニュー」ではなく、「ファイルを追加すると自動的に反映される管理画面」にする。

理想:

- アプリ追加時に `launcher.py` を直接編集しない。
- アプリごとの JSON や YAML を追加すると、ランチャーに表示される。
- アプリの表示順は固定番号ではなく、カテゴリ、優先度、名前、最近使用日時などで流動的に決まる。
- ランチャー画面からアプリ起動、停止、ログ確認、フォルダを開く、設定確認ができる。
- 研究スクリプトも「消す対象」ではなく「使いやすく見える化する対象」として扱う。
- Ollama を使って、ログ診断、フォルダ仕分け、スクリプト説明、README 整理を補助する。

## 推奨フォルダ構成

```text
C:\Users\aaron\apps\
  launcher.py
  config.json
  LAUNCHER_UPGRADE_PLAN.md

  launcher_core\
    registry.py
    process_manager.py
    link_manager.py
    diagnostics.py
    ollama_client.py
    cleanup_rules.py

  app-registry\
    pdf-converter.json
    research-lab.json
    finance-tools.json
    factor-data.json

  app-links\
    research-scripts.json
    useful-folders.json

  ai\
    ollama.json
    prompts\
      log_diagnosis.md
      folder_triage.md
      script_summary.md
      readme_repair.md
```

### 役割

`launcher.py`

- Streamlit の画面部分。
- 起動ボタン、停止ボタン、状態表示、ログ表示などを担当。
- できるだけ薄く保つ。

`launcher_core/registry.py`

- `app-registry/*.json` を読み込む。
- アプリ一覧、カテゴリ、表示順を作る。
- 壊れた設定ファイルがあれば警告する。

`launcher_core/process_manager.py`

- Streamlit アプリの起動・停止。
- PID 管理。
- ポート使用状況確認。
- 起動済みアプリの状態確認。

`launcher_core/link_manager.py`

- フォルダを開く。
- ファイルを開く。
- ジャンクションやショートカットの情報を表示する。

`launcher_core/diagnostics.py`

- ログ診断。
- 起動失敗の原因判定。
- 削除候補の説明。
- Ollama に渡す前のルールベース判定。

`launcher_core/ollama_client.py`

- Ollama API 呼び出し。
- 軽量モデル、標準モデル、深い分析モデルの切り替え。

`launcher_core/cleanup_rules.py`

- 削除候補ルール。
- 研究系保護ルール。
- `__pycache__`, `logs`, `output`, `.launcher_pids.json` などの扱い。

## アプリ定義ファイル案

`app-registry/pdf-converter.json` の例:

```json
{
  "id": "pdf-converter",
  "name": "PDF Converter",
  "category": "Practical Tools",
  "type": "streamlit",
  "entry": "30-practical-tools/pdf-converter/app.py",
  "cwd": "30-practical-tools/pdf-converter",
  "port": 8502,
  "python": null,
  "description": "画像、Word、Excel、PDFをPDF化・結合するツール",
  "tags": ["pdf", "document", "converter"],
  "links": [
    {
      "label": "アプリフォルダ",
      "path": "30-practical-tools/pdf-converter"
    },
    {
      "label": "requirements",
      "path": "30-practical-tools/pdf-converter/requirements.txt"
    }
  ],
  "ai": {
    "logDiagnosis": true,
    "folderTriage": false,
    "scriptSummary": false
  },
  "protected": false
}
```

`app-registry/research-lab.json` の例:

```json
{
  "id": "research-lab",
  "name": "Research Lab",
  "category": "Research",
  "type": "streamlit",
  "entry": "10-research-lab/research-lab/app.py",
  "cwd": "10-research-lab/research-lab",
  "port": 8510,
  "python": "10-research-lab/research-scripts/.venv/Scripts/python.exe",
  "description": "研究結果、分析スクリプト、出力フォルダを扱う研究用ダッシュボード",
  "tags": ["research", "finance", "scripts"],
  "links": [
    {
      "label": "研究フォルダ",
      "path": "10-research-lab"
    },
    {
      "label": "研究スクリプト",
      "path": "10-research-lab/research-scripts"
    },
    {
      "label": "実験出力",
      "path": "10-research-lab/research-lab/work"
    }
  ],
  "ai": {
    "logDiagnosis": true,
    "folderTriage": true,
    "scriptSummary": true
  },
  "protected": true
}
```

## 表示順の考え方

固定番号は避ける。代わりに以下のようなルールで並べる。

1. `favorite: true` のものを上に出す。
2. カテゴリ順にまとめる。
3. 同カテゴリ内は `name` の五十音または英字順。
4. 将来的には「最近起動した順」「よく使う順」も選べるようにする。

必要なら `priority` は持たせてもよい。ただし固定番号ではなく、あくまで並び順の補助にする。

```json
{
  "favorite": true,
  "priority": 20
}
```

## ランチャー画面案

### 上部

- アプリ検索欄
- カテゴリフィルタ
- 起動中だけ表示する切り替え
- AI診断ボタン
- 設定再読み込みボタン

### アプリ一覧

各アプリ行に表示するもの:

- アプリ名
- カテゴリ
- 状態: 停止中、起動中、起動失敗、ポート使用中
- ポート番号
- 起動ボタン
- 停止ボタン
- ブラウザで開くボタン
- フォルダを開くボタン
- ログを見るボタン
- AI診断ボタン

### 詳細パネル

アプリを選ぶと表示:

- 説明
- 実行ファイル
- Python パス
- CWD
- 登録 JSON
- 関連リンク
- 最近のログ
- AIによる診断結果

## Ollama 配置案

現在の Ollama モデル:

```text
llama3.1:8b
nomic-embed-text:latest
qwen3.6:35b-a3b-q4_K_M
qwen3:14b
```

推奨役割:

| モデル | 用途 |
|---|---|
| `llama3.1:8b` | 軽量判定、短いログ要約、フォルダ名ベースの仕分け |
| `qwen3:14b` | 標準の相談役。README 修正案、設定生成、起動エラー診断 |
| `qwen3.6:35b-a3b-q4_K_M` | 重い分析。研究スクリプトの意味整理、複数ログ比較、設計相談 |
| `nomic-embed-text:latest` | ローカル検索。README、スクリプト、ログの類似検索 |

推奨設定:

```json
{
  "default_model": "qwen3:14b",
  "fast_model": "llama3.1:8b",
  "deep_model": "qwen3.6:35b-a3b-q4_K_M",
  "embedding_model": "nomic-embed-text:latest",
  "ollama_url": "http://127.0.0.1:11434"
}
```

### 使い分け

軽い処理:

- フォルダ名だけで分類。
- ログの最終 50 行を要約。
- 削除候補に理由を付ける。

使用モデル: `llama3.1:8b`

標準処理:

- 起動エラーの原因説明。
- README の文字化け修正案。
- アプリ設定 JSON の提案。
- スクリプトの短い説明生成。

使用モデル: `qwen3:14b`

重い処理:

- 研究スクリプト群全体の分類。
- 複数の実験出力フォルダの比較。
- 研究テーマごとの整理。
- ランチャー設計の大きな相談。

使用モデル: `qwen3.6:35b-a3b-q4_K_M`

検索:

- 「AIC を使っているスクリプトはどれ」
- 「PDF変換に関係するファイルはどれ」
- 「このログに似た過去のエラーはあるか」

使用モデル: `nomic-embed-text:latest`

## Google 無料 API の位置づけ

基本は Ollama 優先。

Google 系 API は、無料枠や制限が変わる可能性があるため、常時依存しないほうがよい。使うなら補助的にする。

向いている用途:

- OCR
- 画像やPDFの構造理解
- ローカルモデルで判断が弱い文書分類
- たまに使う高精度要約

ランチャーには、API キーがない場合でも動く設計が望ましい。

```json
{
  "provider": "ollama",
  "fallback_provider": "google",
  "google_enabled": false,
  "daily_limit_guard": true
}
```

## 削除候補判定ルール

### 原則

- ランチャーは勝手に削除しない。
- まず「削除候補」と「理由」を表示する。
- 研究系は保護ルールを強くする。
- 削除実行前に、対象パスを明示する。

### 安全な削除候補

- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.ruff_cache`
- 空の `.launcher_pids.json`
- 古いログ
- 空の `output`
- 一時変換ファイル

### 注意が必要な候補

- `.venv`
- `node_modules`
- `dist`
- `build`
- `work`
- `output`
- 日時付きの実験結果フォルダ

### 原則残す候補

- `research-scripts`
- 研究用 `.py` ファイル
- `requirements.txt`
- `README.md`
- `config.json`
- `app.py`
- `launcher.py`
- 手作業で作った可能性のあるデータ

### 研究系保護ルール

以下に該当するものは、自動削除対象にしない。

```text
C:\Users\aaron\apps\10-research-lab\
C:\Users\aaron\apps\research-scripts\
C:\Users\aaron\apps\research-lab\
```

ただし、研究系でも「候補表示」だけはしてよい。

例:

- `work/kf_factors_20260509-*` は古い実験出力候補。
- `.venv` は大容量だが、研究環境なので保護。
- ログは削除候補にしてよいが、重要実験ログは残す選択肢を出す。

## ジャンクションの扱い

`C:\Users\aaron\apps` 直下には、ジャンクションが多い。

ジャンクションは「リンク先のフォルダを、ここにもあるように見せる入口」。Explorer で開くと普通のフォルダのように中に入れる。

便利な点:

- 深い階層へ行かずに済む。
- ランチャーから直接開きやすい。
- 実体を重複保存しないので容量をほぼ食わない。

注意点:

- 中に入ってファイルを消すと、リンク先の実体が消える。
- ジャンクション自体を消す場合と、中身を消す場合は別扱い。
- ランチャーの削除機能では、ジャンクション配下を削除するときに警告を出すべき。

ランチャーでは、ジャンクションを以下のように表示するとよい。

```text
research-scripts
  種類: Junction
  リンク先: C:\Users\aaron\apps\10-research-lab\research-scripts
  操作: 開く / リンク先を表示 / 登録に追加
```

## 文字化け修正候補

優先度高:

- `C:\Users\aaron\apps\config.json`
- `C:\Users\aaron\apps\launcher.py`
- `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\launcher.py`
- `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\README.md`
- `C:\Users\aaron\apps\30-practical-tools\pdf-converter\app.py`

優先度中:

- `C:\Users\aaron\apps\10-research-lab\README.md`
- `C:\Users\aaron\apps\10-research-lab\research-scripts\README.md`

方針:

- 文字化けした文言は、コード構造を変えずに日本語へ戻す。
- 可能なら UI 表示文言を別ファイルへ分離する。
- README は実用手順中心に書き直す。

## 実装ステップ案

### Step 1: 設計整理

- このメモをベースに仕様を固める。
- 既存 `config.json` の意味を整理する。
- 研究系保護ルールを明文化する。

### Step 2: 文字化け修正

- まずランチャー本体の表示名を直す。
- README を読みやすく直す。
- PDF Converter の UI 文言を直す。

### Step 3: Registry 分離

- `app-registry/*.json` を導入。
- `launcher.py` からアプリ定義を外へ出す。
- 既存 `config.json` との互換性を残す。

### Step 4: リンク管理

- アプリごとの「フォルダを開く」「設定を見る」「ログを見る」を追加。
- ジャンクション情報も表示する。

### Step 5: Ollama 連携

- `ai/ollama.json` を追加。
- ログ診断から始める。
- 次にフォルダ仕分け、スクリプト要約へ進める。

### Step 6: 研究スクリプト可視化

- `research-scripts` の `.py` を一覧化。
- スクリプト名、説明、入力、出力、関連フォルダを表示。
- Ollama で説明文を生成するが、結果は手動確認できるようにする。

### Step 7: 削除候補ダッシュボード

- 容量順表示。
- 削除候補理由表示。
- 保護対象表示。
- 実行前に対象一覧を表示。
- 研究系は初期状態で削除不可にする。

## 最初に実装するなら

最初の実装候補は以下。

1. `app-registry` 導入。
2. `launcher.py` からアプリ定義を分離。
3. 表示名の文字化けを直す。
4. フォルダを開くボタンを追加。
5. ログ表示を追加。
6. Ollama ログ診断を追加。

この順番なら、アプリ管理の便利さがすぐ上がり、同時に将来拡張もしやすくなる。

## 未決定事項

- アプリ定義は JSON にするか YAML にするか。
- ~~メインランチャーを `C:\Users\aaron\apps\launcher.py` に統一するか、`30-practical-tools\streamlit-launcher\launcher.py` を母艦にするか。~~ → **決定**: メインは `apps\launcher.py` に統一。`streamlit-launcher` はコードとして悪くないので、別系統の独立ランチャー（実験用・代替起動用）として並存させる。`app-registry` には登録しない。
- Google API をどこまで使うか。
- OCR はローカル OCR を先に入れるか、Google API を先に試すか。
- 研究系 `work` フォルダの古い出力をどう扱うか。
- `qwen3.6:35b` をどの場面で使うか。

## 方針メモ

このランチャーは「消すための掃除ツール」ではなく、「見える形で動かすための管理ツール」にする。

削除機能は補助であり、中心は以下。

- どこに何があるか見える。
- 何を起動できるか見える。
- 何が動いているか見える。
- 失敗した理由が見える。
- 大事な研究資産を壊さず扱える。
- AI は判断を押し付けるのではなく、説明と候補出しをする。
