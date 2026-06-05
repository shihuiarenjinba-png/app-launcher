# 未使用・統合候補メモ

このファイルは「もう使わない可能性があるもの」「統合後に役割が薄くなりそうなもの」をまとめるメモです。

現時点では削除していません。削除する場合は、必ず対象パスを確認してから実行します。

## すぐ削除してよい候補

現在の追加候補:

| パス | 理由 | 注意 |
|---|---|---|
| `C:\Users\aaron\apps\launcher_dev_server.out.log` | ランチャー起動確認で作った一時ログ | 起動確認結果を残したい場合だけ保持 |
| `C:\Users\aaron\apps\launcher_dev_server.err.log` | ランチャー起動確認で作った一時ログ | 起動確認結果を残したい場合だけ保持 |

`__pycache__` や空ログなどは前回整理済みですが、アプリを実行すると再生成されることがあります。再生成された場合も、Python の自動生成キャッシュなので削除候補です。

## 再生成されるため削除候補になりやすいもの

| パス | 理由 | 注意 |
|---|---|---|
| `**/__pycache__/` | Python の自動生成キャッシュ | 実行すると再生成されます |
| `**/*.pyc` | Python の自動生成バイトコード | 元の `.py` があれば再生成されます |
| `C:\Users\aaron\apps\logs\` | ランチャー起動ログ | 必要なログがないか確認してから |
| `C:\Users\aaron\apps\.launcher_pids.json` | 起動状態管理ファイル | 起動中アプリがないときのみ候補 |
| `C:\Users\aaron\apps\launcher_core\__pycache__` | 今回の構文チェックで再生成されたキャッシュ | 削除しても再生成されます |

## 統合候補だが、まだ残すもの

| パス | 判断 | 理由 |
|---|---|---|
| `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\launcher.py` | 残す（独立運用） | メイン `apps\launcher.py` とは別系統の独立ランチャー。`app-registry` には登録しない |
| `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\config.json` | 残す（独立運用） | 独立ランチャー用の設定 |
| `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\config.example.json` | 残す | 設定サンプルとして有用 |
| `C:\Users\aaron\apps\30-practical-tools\streamlit-launcher\run-launcher.ps1` | 残す | 独立ランチャーのワンクリック起動用 |

## 研究系の保護対象

以下は削除候補ではなく、保護対象です。

| パス | 理由 |
|---|---|
| `C:\Users\aaron\apps\10-research-lab` | 研究アプリ本体と成果物がある |
| `C:\Users\aaron\apps\research-scripts` | 研究スクリプト群へのジャンクション |
| `C:\Users\aaron\apps\10-research-lab\research-scripts` | 研究スクリプト本体 |
| `C:\Users\aaron\apps\10-research-lab\research-scripts\.venv` | 大容量だが、研究スクリプトの実行環境 |

## 注意候補

| パス | 判断 | 理由 |
|---|---|---|
| `C:\Users\aaron\apps\10-research-lab\research-lab\work` | 候補表示のみ | 実験出力が多く容量は大きいが、研究成果の可能性があるため自動削除しない |
| `C:\Users\aaron\apps\40-finance\app\.cache` | 確認後に候補 | アプリキャッシュの可能性があるが、中身を確認してから |

## ジャンクションについて

`C:\Users\aaron\apps` 直下の `research-scripts`, `research-lab`, `pdf-converter`, `app`, `bpp` などは、多くがジャンクションです。

ジャンクション自体はリンク入口なので、容量はほぼ増えません。削除してもリンク入口が消えるだけですが、使い勝手が落ちる可能性があります。

ただし、ジャンクションの中に入ってファイルを削除すると、リンク先の実体が削除されます。ここは注意します。
