import gc
import pandas as pd
import streamlit as st
from utils import PREFECTURE_MAP, convert_prefecture_to_roman, GENRE_MAP, convert_genre_to_roman
from scraper import scrape_tabelog_range

DISPLAY_LIMIT = 1000  # 表示負荷軽減のための最大表示行数


def collect_range(prefecture_jp: str, genre_jp: str, start_page: int, end_page: int, status_placeholder, progress_bar):
    data = []
    # 進捗は概算（ページ数×20件想定）
    estimated_total_items = max(1, (end_page - start_page + 1) * 20)
    for i, store_details in enumerate(scrape_tabelog_range(prefecture_jp, genre_jp, start_page, end_page)):
        data.append(store_details)
        progress = min((i + 1) / estimated_total_items, 1.0)
        progress_bar.progress(progress)
        if genre_jp:
            status_placeholder.info(f"'{prefecture_jp}' の '{genre_jp}' を検索中... ({i + 1} 件取得)")
        else:
            status_placeholder.info(f"'{prefecture_jp}' の '全ジャンル' を検索中... ({i + 1} 件取得)")
    return data


def render_table_and_download(df: pd.DataFrame, label_prefix: str):
    st.write(f"検索結果: {len(df)} 件")
    df.index = range(1, len(df) + 1)
    if len(df) > DISPLAY_LIMIT:
        st.caption(f"表示は先頭 {DISPLAY_LIMIT} 行まで。全件はCSVでダウンロードできます。")
        st.dataframe(df.head(DISPLAY_LIMIT))
    else:
        st.dataframe(df)
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"CSVファイルをダウンロード（{label_prefix}）",
        data=csv_bytes,
        file_name=f"tabelog_{convert_prefecture_to_roman(prefecture_jp)}_{convert_genre_to_roman(genre_jp)}_{label_prefix}.csv",
        mime="text/csv",
    )


# UI 本体
st.title('飲食店営業リスト作成ツール')
st.subheader('電話番号、住所、URLなど')
st.write('サイドバーで都道府県とジャンル、ページ範囲を選択してください。')

prefecture_jp = st.sidebar.selectbox(
    '都道府県を選択してください(必須):',
    [''] + list(PREFECTURE_MAP.keys()),
    index=0
)

genre_jp = st.sidebar.selectbox(
    'ジャンルを選択してください:',
    [''] + list(GENRE_MAP.keys()),
    index=0
)

start_page = st.sidebar.number_input(
    '開始ページ',
    min_value=1,
    max_value=60,
    value=1,
    step=1,
    format="%d"
)

end_page = st.sidebar.number_input(
    '終了ページ',
    min_value=1,
    max_value=60,
    value=1,
    step=1,
    format="%d"
)

st.sidebar.caption('一度に処理できるのは30ページ未満です。ページ範囲を分けて実行してください。')
st.sidebar.caption('1ページ当たり20件の店舗情報が取得できます。')
st.sidebar.caption('収集する項目は、店名、ジャンル、住所、電話番号、予約・お問い合わせ先、ホームページURL、席数です。')
st.sidebar.caption('食べログに情報がない項目は空欄になります。')

status_placeholder = st.empty()
progress_bar = st.progress(0)

if st.sidebar.button('スクレイピング開始'):
    # 入力検証
    if not prefecture_jp:
        st.sidebar.error('都道府県を選択してください。')
    elif start_page > end_page:
        st.sidebar.error('終了ページは開始ページ以上の値を設定してください。')
    elif (end_page - start_page) >= 30:  # 一度に処理できるのは30ページ未満
        st.sidebar.error('一度に処理できるのは30ページ未満です。ページ範囲を分けて実行してください。')
    else:
        try:
            data = collect_range(prefecture_jp, genre_jp, int(start_page), int(end_page), status_placeholder, progress_bar)
            status_placeholder.success('スクレイピングが完了しました。')
            progress_bar.empty()
            if data:
                df = pd.DataFrame(data)
                render_table_and_download(df, f"range_{int(start_page)}-{int(end_page)}pages")
            else:
                st.warning('指定された条件では店舗情報が見つかりませんでした。')
        except Exception as e:
            status_placeholder.error(f"スクレイピング中にエラーが発生しました: {e}")
            progress_bar.empty()
            # 念のためGC
            gc.collect()
