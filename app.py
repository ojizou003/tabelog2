import streamlit as st
import pandas as pd
from utils import PREFECTURE_MAP, convert_prefecture_to_roman, GENRE_MAP, convert_genre_to_roman
from scraper import scrape_tabelog # scraper.py から scrape_tabelog 関数をインポート

def run_search(prefecture_jp: str, genre_jp: str, max_pages: int):
    """
    検索実行ボタンが押されたときの処理
    """
    # 処理状況表示用のプレースホルダーを作成
    status_placeholder = st.empty()
    progress_bar = st.progress(0)

    status_placeholder.info(f"'{prefecture_jp}' の '{genre_jp}' を検索中...")

    # 内部処理用にローマ字に変換
    prefecture_roman = convert_prefecture_to_roman(prefecture_jp)
    genre_roman = convert_genre_to_roman(genre_jp)

    if not prefecture_roman:
        status_placeholder.error(f"選択された都道府県 '{prefecture_jp}' のローマ字変換に失敗しました。")
        progress_bar.empty() # プログレスバーを非表示にする
    elif not genre_roman:
        status_placeholder.error(f"選択されたジャンル '{genre_jp}' のローマ字変換に失敗しました。")
        progress_bar.empty() # プログレスバーを非表示にする
    else:
        scraped_data = []
        try:
            # スクレイピング実行 (ジェネレーターとして呼び出す)
            for i, store_details in enumerate(scrape_tabelog(prefecture_jp, genre_jp, max_pages=max_pages)):
                scraped_data.append(store_details)
                # 進捗表示を更新 (ここでは取得した店舗数で簡易的に表示)
                # 最大ページ数 * ページあたりの店舗数 (概算) で全体の進捗を計算することも可能だが、
                # ページあたりの店舗数は変動するため、ここでは取得できた店舗数で表示する
                # より正確な進捗表示には、スクレイパー側で総店舗数を予測するか、ページ数を基に進捗を計算する必要がある
                progress_percentage = min((i + 1) / (max_pages * 20), 1.0) # 例: 最大ページ数、1ページあたり最大20店舗と仮定
                progress_bar.progress(progress_percentage)
                status_placeholder.info(f"'{prefecture_jp}' の '{genre_jp}' を検索中... ({i + 1} 件取得)")


            # 処理完了の表示
            status_placeholder.success('検索が完了しました。')
            progress_bar.empty() # プログレスバーを非表示にする


            if scraped_data:
                # 2.3 データ表示機能 & 5.2 出力項目 - データ表示
                df = pd.DataFrame(scraped_data)
                st.write(f"検索結果: {len(df)} 件")
                st.dataframe(df)

                # 2.4 データ出力機能 & 5.2 出力項目 - ダウンロード機能
                # CSVダウンロードボタン
                csv_filename = f"tabelog_{prefecture_roman}_{genre_roman}_{pd.Timestamp('now').strftime('%Y%m%d_%H%M%S')}.csv"
                st.download_button(
                    label="CSVファイルをダウンロード",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name=csv_filename,
                    mime='text/csv',
                )
            else:
                st.warning('指定された条件では店舗情報が見つかりませんでした。')
        except Exception as e:
            status_placeholder.error(f"スクレイピング中にエラーが発生しました: {e}")
            progress_bar.empty() # プログレスバーを非表示にする

st.title('食べログ営業リスト作成ツール')
st.write('都道府県とジャンルを選択して、食べログから店舗情報を収集します。')

# 5.1 入力項目
prefecture_jp = st.selectbox(
    '都道府県を選択してください:',
    list(PREFECTURE_MAP.keys()) # utils.py の都道府県マップを使用
)

genre_jp = st.selectbox(
    'ジャンルを選択してください:',
    list(GENRE_MAP.keys()) # utils.py のジャンルマップを使用
)

# 最大ページ数入力
max_pages = st.number_input(
    '最大ページ数:(1ページ当たり20件の店舗情報が取得できます)',
    min_value=1,
    max_value=60,
    value=1, # デフォルト値
    step=1
)

# 検索実行ボタン
if st.button('検索実行'):
    run_search(prefecture_jp, genre_jp, max_pages)
