# tabelog

## 概要
`tabelog`は、食べログの情報をスクレイピングし、データを取得・分析するためのPythonプロジェクトです。

## 機能
- 食べログの店舗情報のスクレイピング
- 取得データの保存・加工
- データの簡易分析

## ファイル構成
- `app.py` : メインアプリケーション
- `main.py` : エントリーポイント
- `scraper.py` : スクレイピング処理
- `utils.py` : 補助関数
- `test_*.py` : 各種テストコード
- `definition.md` : 用語や仕様の定義
- `memo.md` : 開発メモ

## 必要環境
- Python 3.8以上
- 必要なパッケージは`pyproject.toml`に記載

## 使い方

1. 必要なパッケージのインストール
   ```bash
   pip install -r requirements.txt
   ```
   または
   ```bash
   pip install .
   ```

2. スクレイピングの実行
   ```bash
   python main.py
   ```

## 注意事項
- 本プロジェクトは学習・研究目的で作成されています。スクレイピング対象サイトの利用規約を遵守してください。

## ライセンス
MIT License
