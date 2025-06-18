# tabelog

## 概要
`tabelog`は、食べログの情報をスクレイピングし、データを取得するためのstreamlitアプリです。

## 機能
- 食べログの店舗情報をスクレイピング
- 取得データの表示
- 取得データのcsvファイル出力

## ファイル構成
- `app.py` : メインアプリケーション
- `scraper.py` : スクレイピング処理
- `utils.py` : 補助関数
- `definition.md` : 用語や仕様の定義
- `pyproject.toml` : パッケージ管理ファイル

## 環境
- Python 3.13
- 必要なパッケージは`pyproject.toml`に記載

## 使い方

1. 必要なパッケージのインストール
   ```bash
   uv sync
   ```
2. streamlitを使用してアプリケーションを起動
   ```bash
   streamlit run app.py
   ```

## 注意事項
- 本プロジェクトは学習・研究目的で作成されています。スクレイピング対象サイトの利用規約を遵守してください。

## ライセンス
MIT License
