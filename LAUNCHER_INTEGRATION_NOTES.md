# ランチャー統合メモ

## 2026-05-15 更新

ランチャー上に細かく出していた金融・分析系アプリを、削除せず `分析・予測・リスク母艦` に束ねる方針へ変更しました。

表に出す入口:

- リサーチラボ
- ファクター/マーケットデータ取得
- 分析・予測・リスク母艦
- ドキュメント→PDF変換

非表示にして母艦へ寄せたもの:

- ファクターシミュレーター
- レジームシミュレーター
- ポートフォリオ分析
- ポートフォリオ監査
- BPPツール

これらの既存コードは削除していません。`app-registry/*.json` 側で `hidden: true` と `merged_into: analysis-hub` を付け、ランチャーの表側からは母艦に集約しています。

## 起動コマンド

```powershell
cd C:\Users\aaron\apps
streamlit run launcher.py --server.port 8515 --server.address 127.0.0.1
```

または絶対パスで:

```powershell
streamlit run C:\Users\aaron\apps\launcher.py --server.port 8515 --server.address 127.0.0.1
```

## 直接、分析母艦だけ起動する場合

```powershell
streamlit run C:\Users\aaron\apps\40-finance\analysis-hub\app.py --server.port 8504 --server.address 127.0.0.1
```
