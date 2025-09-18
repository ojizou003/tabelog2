import gc
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as components_html
from utils import PREFECTURE_MAP, convert_prefecture_to_roman, GENRE_MAP, convert_genre_to_roman
from scraper import scrape_tabelog_range

DISPLAY_LIMIT = 1000  # 表示負荷軽減のための最大表示行数
RELOAD_DELAY_MS = 2500  # ダウンロード後にリロードするまでの遅延（ミリ秒）


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
    clicked = st.download_button(
        label=f"CSVファイルをダウンロード（{label_prefix}）",
        data=csv_bytes,
        file_name=f"tabelog_{convert_prefecture_to_roman(prefecture_jp)}_{convert_genre_to_roman(genre_jp)}_{label_prefix}.csv",
        mime="text/csv",
        key=f"download_{label_prefix}",
    )
    if clicked:
        # ダウンロード開始後に完全なブラウザリロード（URLクエリは保持）
        # Streamlitのランタイムリロードではなくwindow.location.reload(true)を使用
        components_html(
            f"""
            <script>
              (function(){{
                if (window.__hardReloading) return; // 多重実行防止
                window.__hardReloading = true;
                setTimeout(function(){{
                  try {{
                    var u = new URL(window.location.href);
                    u.searchParams.set('_rnd', Date.now().toString());
                    var url = u.toString();
                    // 1) assign: 履歴を残す通常の遷移
                    window.location.assign(url);
                    // 2) href: 念のためのフォールバック
                    setTimeout(function(){{ window.location.href = url; }}, 250);
                    // 3) リンククリックでの遷移
                    setTimeout(function(){{
                      try {{
                        var a = document.createElement('a');
                        a.href = url;
                        a.rel = 'noopener';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                      }} catch(_e) {{}}
                    }}, 500);
                    // 4) meta refresh フォールバック
                    setTimeout(function(){{
                      try {{
                        var m = document.createElement('meta');
                        m.httpEquiv = 'refresh';
                        m.content = '0;url=' + url;
                        document.head.appendChild(m);
                      }} catch(_e) {{}}
                    }}, 800);
                  }} catch(e) {{
                    try {{ window.location.reload(true); }} catch(_) {{ window.location.reload(); }}
                  }}
                }}, {RELOAD_DELAY_MS});
              }})();
            </script>
            """,
            height=0,
        )


# UI 本体
st.title('飲食店営業リスト作成ツール')
st.subheader('電話番号、住所、URLなど')
st.write('サイドバーで都道府県とジャンル、ページ範囲を選択してください。')

# クエリパラメータからデフォルトを復元
pref_options = [''] + list(PREFECTURE_MAP.keys())
genre_options = [''] + list(GENRE_MAP.keys())
# 逆引きマップ（英字コード -> 日本語表示名）
INV_PREF_MAP = {v: k for k, v in PREFECTURE_MAP.items()}
INV_GENRE_MAP = {v: k for k, v in GENRE_MAP.items()}

try:
    qp = dict(st.query_params)
except Exception:
    qp = {}

def _to_int(val, fallback):
    try:
        return int(val)
    except Exception:
        return fallback

# クエリには英字コードを保存する想定。見つからなければ日本語からも復元試行。
qp_pref_code = qp.get('prefecture', '')
qp_genre_code = qp.get('genre', '')

# 英字コード -> 日本語
default_pref = INV_PREF_MAP.get(qp_pref_code, qp.get('prefecture', ''))
default_genre = INV_GENRE_MAP.get(qp_genre_code, qp.get('genre', ''))
default_start = _to_int(qp.get('start', 1), 1)
default_end = _to_int(qp.get('end', 1), 1)

pref_index = pref_options.index(default_pref) if default_pref in pref_options else 0
genre_index = genre_options.index(default_genre) if default_genre in genre_options else 0

prefecture_jp = st.sidebar.selectbox(
    '都道府県を選択してください(必須):',
    pref_options,
    index=pref_index
)

genre_jp = st.sidebar.selectbox(
    'ジャンルを選択してください:',
    genre_options,
    index=genre_index
)

start_page = st.sidebar.number_input(
    '開始ページ(1~60)',
    min_value=1,
    max_value=60,
    value=default_start,
    step=1,
    format="%d"
)

end_page = st.sidebar.number_input(
    '終了ページ(1~60)',
    min_value=1,
    max_value=60,
    value=default_end,
    step=1,
    format="%d"
)

# 現在の選択をクエリパラメータに反映（変更がある場合のみ）
# クエリには英字コードを保存
new_qp = {
    'prefecture': convert_prefecture_to_roman(prefecture_jp) if prefecture_jp else '',
    'genre': convert_genre_to_roman(genre_jp) if genre_jp else '',
    'start': str(int(start_page)),
    'end': str(int(end_page)),
}
need_update = False
for k, v in new_qp.items():
    if str(qp.get(k, '')) != str(v):
        need_update = True
        break
if need_update:
    try:
        st.query_params.clear()
        st.query_params.update(new_qp)
    except Exception:
        pass

status_placeholder = st.empty()
progress_bar = st.progress(0)

if st.sidebar.button('データ取得'):
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
            status_placeholder.success('データ取得が完了しました。')
            progress_bar.empty()
            if data:
                df = pd.DataFrame(data)
                render_table_and_download(df, f"range_{int(start_page)}-{int(end_page)}pages")
                st.caption("※次のデータを取得する場合は、ダウンロード後、一度ブラウザを手動でリロードしてください。")
            else:
                st.warning('指定された条件では店舗情報が見つかりませんでした。')
        except Exception as e:
            status_placeholder.error(f"データ取得中にエラーが発生しました: {e}")
            progress_bar.empty()
            # 念のためGC
            gc.collect()

st.sidebar.caption('一度に処理できるのは30ページ未満です。ページ範囲を分けて実行してください。')
st.sidebar.caption('1ページ当たり20件の店舗情報が取得できます。')
st.sidebar.caption('収集する項目は、店名、ジャンル、住所、電話番号、予約・お問い合わせ先、ホームページURL、席数です。')
st.sidebar.caption('食べログに情報がない項目は空欄になります。')