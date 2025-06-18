# 都道府県変換テーブル
PREFECTURE_MAP = {
    '北海道': 'hokkaido',
    '青森県': 'aomori',
    '岩手県': 'iwate',
    '宮城県': 'miyagi',
    '秋田県': 'akita',
    '山形県': 'yamagata',
    '福島県': 'fukushima',
    '茨城県': 'ibaraki',
    '栃木県': 'tochigi',
    '群馬県': 'gunma',
    '埼玉県': 'saitama',
    '千葉県': 'chiba',
    '東京都': 'tokyo',
    '神奈川県': 'kanagawa',
    '新潟県': 'niigata',
    '富山県': 'toyama',
    '石川県': 'ishikawa',
    '福井県': 'fukui',
    '山梨県': 'yamanashi',
    '長野県': 'nagano',
    '岐阜県': 'gifu',
    '静岡県': 'shizuoka',
    '愛知県': 'aichi',
    '三重県': 'mie',
    '滋賀県': 'shiga',
    '京都府': 'kyoto',
    '大阪府': 'osaka',
    '兵庫県': 'hyogo',
    '奈良県': 'nara',
    '和歌山県': 'wakayama',
    '鳥取県': 'tottori',
    '島根県': 'shimane',
    '岡山県': 'okayama',
    '広島県': 'hiroshima',
    '山口県': 'yamaguchi',
    '徳島県': 'tokushima',
    '香川県': 'kagawa',
    '愛媛県': 'ehime',
    '高知県': 'kochi',
    '福岡県': 'fukuoka',
    '佐賀県': 'saga',
    '長崎県': 'nagasaki',
    '熊本県': 'kumamoto',
    '大分県': 'oita',
    '宮崎県': 'miyazaki',
    '鹿児島県': 'kagoshima',
    '沖縄県': 'okinawa',
}

def convert_prefecture_to_roman(prefecture_jp: str) -> str:
    """
    都道府県の漢字表記をローマ字表記に変換する

    Args:
        prefecture_jp: 都道府県の漢字表記

    Returns:
        都道府県のローマ字表記
    """
    return PREFECTURE_MAP.get(prefecture_jp, '')

# ジャンル変換テーブル
GENRE_MAP = {
    '和食': 'washoku',
    '日本料理': 'japanese',
    '寿司': 'sushi',
    '海鮮・魚介': 'seafood',
    '蕎麦': 'soba',
    'うなぎ': 'unagi',
    '焼き鳥': 'yakitori',
    'お好み焼き': 'okkonomiyaki',
    'もんじゃ焼き': 'monjya',
    '洋食': 'yoshoku',
    'フレンチ': 'french',
    'イタリアン': 'italian',
    'スペイン料理': 'spain',
    'ステーキ': 'steak',
    '中華料理': 'chinese',
    '韓国料理': 'korea',
    'タイ料理': 'thai',
    'ラーメン': 'ramen',
    'カレー': 'curry',
    '鍋': 'nabe',
    'もつ鍋': 'motsu',
    '居酒屋': 'izakaya',
    'パン': 'pan',
    'スイーツ': 'sweets',
    'バー・お酒': 'bar',
    '天ぷら': 'tempura',
    '焼肉': 'yakiniku',
    '料理旅館': 'ryokan',
    'ビストロ': 'bistro',
    'ハンバーグ': 'hamburgersteak',
    'とんかつ': 'tonkatsu',
    '串揚げ': 'kushiage',
    'うどん': 'udon',
    'しゃぶしゃぶ': 'syabusyabu',
    '沖縄料理': 'okinawafood',
    'ハンバーガー': 'hamburger',
    'パスタ': 'pasta',
    'ピザ': 'pizza',
    '餃子': 'gyouza',
    'ホルモン': 'horumon',
    'カフェ': 'cafe',
    '喫茶店': 'kissaten',
    'ケーキ': 'cake',
    'タピオカ': 'tapioca',
    '食堂': 'teishoku',
    'ビュッフェ・バイキング': 'viking',
}

def convert_genre_to_roman(genre_jp: str) -> str:
    """
    ジャンルの漢字表記をローマ字表記に変換する
    """
    return GENRE_MAP.get(genre_jp, '')
