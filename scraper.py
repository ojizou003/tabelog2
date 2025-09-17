import requests
from bs4 import BeautifulSoup
import time
import logging # logging モジュールを追加

# ロギングの設定 (必要に応じて調整)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# utils.py から都道府県変換マップをインポートする想定
# from .utils import PREFECTURE_MAP # プロジェクト構成による
from utils import convert_prefecture_to_roman, convert_genre_to_roman

BASE_URL = "https://tabelog.com/"

def build_search_url(prefecture_roman: str, genre_roman: str, page_num: int) -> str:
    """
    食べログのジャンル別リストページのURLを構築する

    Args:
        prefecture_roman: 都道府県のローマ字表記
        genre_roman: ジャンルのローマ字表記
        page_num: ページ番号 (1-60)

    Returns:
        構築されたURL
    """
    if genre_roman:
        url = f"{BASE_URL}{prefecture_roman}/rstLst/{genre_roman}/{page_num}/"
    else:
        url = f"{BASE_URL}{prefecture_roman}/rstLst/{page_num}/"
    return url

def get_page_content(url: str) -> BeautifulSoup | None:
    """
    指定されたURLのページコンテンツを取得し、BeautifulSoupオブジェクトとして返す

    Args:
        url: 取得対象のURL
        
    Returns:
        BeautifulSoupオブジェクト、またはエラー時はNone
    """
    try:
        # robots.txt および利用規約を遵守し、適切なアクセス間隔を設ける
        time.sleep(1) # 例: 1秒待機
        response = requests.get(url)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}") # print から logging.error に変更
        return None

def extract_store_urls(soup: BeautifulSoup) -> list[str]:
    """
    リストページから個別の店舗ページのURLを抽出する

    Args:
        soup: リストページのBeautifulSoupオブジェクト
    
    Returns:
        店舗ページのURLのリスト
    """
    store_urls = []
    for link in soup.select('a.list-rst__rst-name-target'):
            store_urls.append(link['href'])
    return store_urls

def extract_store_details(soup: BeautifulSoup) -> dict:
    """
    店舗ページから詳細情報を抽出する

    Args:
        soup: 店舗ページのBeautifulSoupオブジェクト

    Returns:
        抽出された詳細情報の辞書
    """
    details = {
        '店名': ' - ',
        'ジャンル': ' -',
        '住所': ' -',
        '電話番号': ' - ',
        '予約・お問い合わせ': ' - ',
        'ホームページ': ' - ',
        '席数': ' - '
    }
    
    table = soup.find(id='contents-rstdata')
    if not table: # contents-rstdata がない場合のエラーハンドリング
        logging.warning("contents-rstdata div not found.")
        return details # 空の辞書またはデフォルト値を含む辞書を返す

    ths = table.find_all('th')
    tds = table.find_all('td')
    
    for th, td in zip(ths, tds):
        th_text = th.text.strip()
        td_text = td.text.strip()

        if th_text == '店名':
            details['店名'] = td_text
        elif th_text == 'ジャンル':
            details['ジャンル'] = td_text
        elif th_text == '住所':
            # 住所は最初の改行までを取得
            details['住所'] = td_text.replace('\u3000', ' ').split('\n')[0]
        elif th_text == '電話番号':
            details['電話番号'] = td_text
        elif th_text.replace('\n', '').replace(' ', '') == '予約・お問い合わせ': # 改行と空白を除去して比較
             details['予約・お問い合わせ'] = td_text
        elif th_text == 'ホームページ':
            details['ホームページ'] = td_text
        elif th_text == '席数':
            # 席数は最初のpタグのテキストを抽出
            p_tag = td.find('p')
            if p_tag:
                details['席数'] = p_tag.text.strip()
            else:
                details['席数'] = td_text.split('\n')[0] # pタグがない場合は既存ロジックを踏襲
        else:
            pass # その他の項目はスキップ
            
    return details

def scrape_tabelog(prefecture_jp: str, genre_jp: str, max_pages: int = 60):
    """
    食べログから店舗情報をスクレイピングするジェネレーター関数
    スクレイピングした店舗データをyieldします。

    Args:
        prefecture_jp: 都道府県の漢字表記
        genre_jp: ジャンルの漢字表記
        max_pages: 最大取得ページ数 (1-60)

    Yields:
        dict: 収集した店舗情報の辞書
    """
    prefecture_roman = convert_prefecture_to_roman(prefecture_jp)
    genre_roman = convert_genre_to_roman(genre_jp)

    if not prefecture_roman:
        logging.warning(f"Unknown prefecture: {prefecture_jp}")
        return


    for page_num in range(1, min(max_pages, 60) + 1):
        search_url = build_search_url(prefecture_roman, genre_roman, page_num)
        logging.info(f"Scraping page {page_num}: {search_url}")

        list_soup = get_page_content(search_url)
        if not list_soup:
            logging.warning(f"Failed to get content for page {page_num}. Skipping.")
            continue

        store_urls = extract_store_urls(list_soup)
        if not store_urls:
            logging.info(f"No store URLs found on page {page_num}.")
            # ページが存在しない場合の対応 (例: 検索結果の最終ページ)
            if page_num > 1: # 2ページ目以降でURLが見つからない場合は終了と判断
                 logging.info("Assuming end of search results.")
                 break
            continue

        for store_url in store_urls:
            logging.info(f"  Scraping store page: {store_url}")
            store_soup = get_page_content(store_url)
            if store_soup:
                store_details = extract_store_details(store_soup)
                yield store_details # データをyieldする
            else:
                logging.error(f"店舗ページの取得に失敗しました: {store_url}")

    # ジェネレーターなので return は不要

def scrape_tabelog_range(prefecture_jp: str, genre_jp: str, start_page: int, end_page: int):
    """
    食べログから店舗情報をスクレイピングするジェネレーター関数（ページ範囲指定）

    Args:
        prefecture_jp: 都道府県の漢字表記
        genre_jp: ジャンルの漢字表記
        start_page: 開始ページ（1以上）
        end_page: 終了ページ（開始以上、最大60）

    Yields:
        dict: 収集した店舗情報の辞書
    """
    prefecture_roman = convert_prefecture_to_roman(prefecture_jp)
    genre_roman = convert_genre_to_roman(genre_jp)

    if not prefecture_roman:
        logging.warning(f"Unknown prefecture: {prefecture_jp}")
        return

    start = max(1, int(start_page))
    end = min(60, int(end_page))
    if end < start:
        logging.warning(f"Invalid page range: {start_page}..{end_page}")
        return

    for page_num in range(start, end + 1):
        search_url = build_search_url(prefecture_roman, genre_roman, page_num)
        logging.info(f"Scraping page {page_num}: {search_url}")

        list_soup = get_page_content(search_url)
        if not list_soup:
            logging.warning(f"Failed to get content for page {page_num}. Skipping.")
            continue

        store_urls = extract_store_urls(list_soup)
        if not store_urls:
            logging.info(f"No store URLs found on page {page_num}.")
            # ページが存在しない場合の対応 (例: 検索結果の最終ページ)
            if page_num > start:
                logging.info("Assuming end of search results.")
                break
            continue

        for store_url in store_urls:
            logging.info(f"  Scraping store page: {store_url}")
            store_soup = get_page_content(store_url)
            if store_soup:
                store_details = extract_store_details(store_soup)
                yield store_details
            else:
                logging.error(f"店舗ページの取得に失敗しました: {store_url}")

if __name__ == '__main__':
    # テスト実行用のコードなど
    # 例:
    # data_generator = scrape_tabelog("東京都", "ラーメン", max_pages=1)
    # import pandas as pd
    # data_list = list(data_generator) # ジェネレーターからリストに変換
    # df = pd.DataFrame(data_list)
    # print(df)
    pass