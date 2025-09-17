import gc
import pandas as pd
import streamlit as st
from utils import PREFECTURE_MAP, convert_prefecture_to_roman, GENRE_MAP, convert_genre_to_roman
from scraper import scrape_tabelog_range

PHASE_LIMIT = 30
DISPLAY_LIMIT = 1000  # 表示負荷軽減のための最大表示行数


def init_session():
    st.session_state.setdefault('phase', 'idle')  # idle | phase1_done | done
    st.session_state.setdefault('prefecture_jp', '')
    st.session_state.setdefault('genre_jp', '')
    st.session_state.setdefault('requested_pages', 1)
    st.session_state.setdefault('partial_data', None)  # list[dict] or None
    st.session_state.setdefault('next_start_page', None)
    st.session_state.setdefault('end_page', None)
    st.session_state.setdefault('error', None)


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
        file_name=f"tabelog_{convert_prefecture_to_roman(st.session_state['prefecture_jp'])}_{convert_genre_to_roman(st.session_state['genre_jp'])}_{label_prefix}.csv",
        mime="text/csv",
    )


def reset_state(prefecture_jp: str, genre_jp: str, max_pages: int):
    st.session_state.update({
        'phase': 'idle',
        'prefecture_jp': prefecture_jp,
        'genre_jp': genre_jp,
        'requested_pages': int(max_pages),
        'partial_data': None,
        'next_start_page': None,
        'end_page': None,
        'error': None,
    })


# UI 本体
init_session()

st.title('飲食店営業リスト作成ツール')
st.subheader('電話番号、住所、URLなど')
st.write('サイドバーで都道府県とジャンルを選択してください。')

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

max_pages = st.sidebar.number_input(
    '最大ページ数(1~60):',
    min_value=1,
    max_value=60,
    value=1,
    step=1
)

st.sidebar.caption('1ページ当たり20件の店舗情報が取得できます。時間がかかるので1ページからお試しください。')
st.sidebar.caption('収集する項目は、店名、ジャンル、住所、電話番号、予約・お問い合わせ先、ホームページURL、席数です。')
st.sidebar.caption('食べログに情報がない項目は空欄になります。')

status_placeholder = st.empty()
progress_bar = st.progress(0)

if st.sidebar.button('検索実行'):
    if not prefecture_jp:
        st.sidebar.error('都道府県を選択してください。')
    else:
        reset_state(prefecture_jp, genre_jp, max_pages)
        total_pages = st.session_state['requested_pages']
        try:
            if total_pages <= PHASE_LIMIT:
                # 単段階フロー
                data = collect_range(prefecture_jp, genre_jp, 1, total_pages, status_placeholder, progress_bar)
                status_placeholder.success('検索が完了しました。')
                progress_bar.empty()
                if data:
                    df = pd.DataFrame(data)
                    render_table_and_download(df, f"{total_pages}pages")
                else:
                    st.warning('指定された条件では店舗情報が見つかりませんでした。')
                st.session_state['phase'] = 'done'
            else:
                # フェーズ1: 1..30
                data_phase1 = collect_range(prefecture_jp, genre_jp, 1, PHASE_LIMIT, status_placeholder, progress_bar)
                status_placeholder.success('最初の30ページの取得が完了しました。')
                progress_bar.empty()

                st.session_state['partial_data'] = data_phase1
                st.session_state['next_start_page'] = PHASE_LIMIT + 1
                st.session_state['end_page'] = total_pages
                st.session_state['phase'] = 'phase1_done'
        except Exception as e:
            st.session_state['error'] = str(e)
            status_placeholder.error(f"スクレイピング中にエラーが発生しました: {e}")
            progress_bar.empty()

# フェーズ間の処理
if st.session_state['phase'] == 'phase1_done':
    partial = st.session_state.get('partial_data') or []
    if partial:
        df_partial = pd.DataFrame(partial)
        render_table_and_download(df_partial, f"partial_{PHASE_LIMIT}pages")
    else:
        st.info("部分データが空です。条件を見直してください。")

    resume_clicked = st.button('再開（残りのページを取得）')
    if resume_clicked:
        # メモリ解放
        try:
            del df_partial
        except Exception:
            pass
        gc.collect()

        try:
            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            start_p = int(st.session_state['next_start_page'])
            end_p = int(st.session_state['end_page'])
            data_phase2 = collect_range(
                st.session_state['prefecture_jp'],
                st.session_state['genre_jp'],
                start_p,
                end_p,
                status_placeholder,
                progress_bar
            )
            status_placeholder.success('残りのページの取得が完了しました。')
            progress_bar.empty()

            # 結合
            full = (st.session_state.get('partial_data') or []) + data_phase2
            df_full = pd.DataFrame(full)
            render_table_and_download(df_full, f"full_{end_p}pages")

            st.session_state['phase'] = 'done'
        except Exception as e:
            status_placeholder.error(f"再開中にエラーが発生しました: {e}")
            progress_bar.empty()
