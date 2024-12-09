import flet as ft
import requests
import json
import os
import sqlite3
from datetime import datetime

# SQLiteデータベースのパスを指定
DB_PATH = "/Users/milktea/Lecture/DSprog2/local/jma/weather_forecast.db"

# JSONファイルの絶対パスを指定
JSON_PATH = "/Users/milktea/Lecture/DSprog2/local/jma/areas.json"

# SQLiteデータベースの初期化
def initialize_database():
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 地方テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_code TEXT NOT NULL UNIQUE,
        region_name TEXT NOT NULL UNIQUE
    )
    """)

    # 都道府県テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Prefectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prefecture_code TEXT NOT NULL UNIQUE,
        prefecture_name TEXT NOT NULL,
        region_id INTEGER NOT NULL,
        FOREIGN KEY(region_id) REFERENCES Regions(id)
    )
    """)

    # 地域テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT NOT NULL UNIQUE,
        area_name TEXT NOT NULL,
        prefecture_id INTEGER NOT NULL,
        FOREIGN KEY(prefecture_id) REFERENCES Prefectures(id)
    )
    """)

    # 天気情報テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS WeatherReports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        weather_code TEXT NOT NULL,
        weather TEXT NOT NULL,
        wind TEXT NOT NULL,
        wave TEXT,
        area_id INTEGER NOT NULL,
        UNIQUE(date, area_id),
        FOREIGN KEY(area_id) REFERENCES Areas(id)
    )
    """)

    conn.commit()
    conn.close()

# JSONファイルをロードして階層構造を構築
def load_area_hierarchy():
    # JSONファイルの存在確認
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"JSONファイルが見つかりません: {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    hierarchy = {}
    for center_code, center_info in data["centers"].items():
        region_name = center_info["name"]
        hierarchy[region_name] = {"code": center_code, "offices": {}}

        for office_code in center_info["children"]:
            if office_code in data["offices"]:
                office_info = data["offices"][office_code]
                hierarchy[region_name]["offices"][office_info["name"]] = {"code": office_code}

    # データベースに挿入
    insert_hierarchy_data(data)
    return hierarchy

# 階層データをデータベースに挿入
def insert_hierarchy_data(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 地方データ
    for region_code, region_info in data['centers'].items():
        cursor.execute("""
        INSERT OR IGNORE INTO Regions (region_code, region_name)
        VALUES (?, ?)
        """, (region_code, region_info['name']))

    # 都道府県データ
    for prefecture_code, prefecture_info in data['offices'].items():
        cursor.execute("SELECT id FROM Regions WHERE region_code = ?", (prefecture_info['parent'],))
        region_id = cursor.fetchone()
        if region_id:
            cursor.execute("""
            INSERT OR IGNORE INTO Prefectures (prefecture_code, prefecture_name, region_id)
            VALUES (?, ?, ?)
            """, (prefecture_code, prefecture_info['name'], region_id[0]))

    # 地域データ
    for class10_code, class10_info in data['class10s'].items():
        parent_office_code = class10_info.get('parent')
        if parent_office_code:
            cursor.execute("SELECT id FROM Prefectures WHERE prefecture_code = ?", (parent_office_code,))
            prefecture_id = cursor.fetchone()
            if prefecture_id:
                cursor.execute("""
                INSERT OR IGNORE INTO Areas (area_code, area_name, prefecture_id)
                VALUES (?, ?, ?)
                """, (class10_code, class10_info['name'], prefecture_id[0]))

    conn.commit()
    conn.close()

# 天気データを取得してデータベースに保存
def save_weather_data(office_code, weather_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # エリアコードとエリアIDのマッピングを作成
    cursor.execute("SELECT area_code, id FROM Areas")
    area_code_to_id = dict(cursor.fetchall())

    for area in weather_data[0]['timeSeries'][0]['areas']:
        area_code = area['area']['code']
        area_id = area_code_to_id.get(area_code)
        if not area_id:
            print(f"エリアがデータベースに存在しません: {area_code}")
            continue

        weather_codes = area['weatherCodes']
        weathers = area['weathers']
        winds = area['winds']
        waves = area.get('waves', ["情報なし"] * len(weather_codes))

        for i, date in enumerate(weather_data[0]['timeSeries'][0]['timeDefines']):
            cursor.execute("""
            INSERT INTO WeatherReports (date, weather_code, weather, wind, wave, area_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date, area_id) DO UPDATE SET
                weather_code=excluded.weather_code,
                weather=excluded.weather,
                wind=excluded.wind,
                wave=excluded.wave
            """, (date.split("T")[0], weather_codes[i], weathers[i], winds[i], waves[i], area_id))

    conn.commit()
    conn.close()

# 天気データを取得する関数
def get_weather_data(office_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        save_weather_data(office_code, weather_data)  # データベースに保存
        return weather_data
    else:
        return {"error": f"Failed to fetch weather data for code {office_code}"}

# データベース内のデータが最新か確認
def is_weather_data_up_to_date():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 今日の日付を取得
    today = datetime.now().strftime('%Y-%m-%d')

    # 今日のデータが存在するか確認
    cursor.execute("""
    SELECT 1 FROM WeatherReports WHERE date = ?
    """, (today,))
    result = cursor.fetchone()
    conn.close()

    return result is not None

# アプリ起動時にデータを更新
def update_weather_data(area_hierarchy):
    for region_name, region_info in area_hierarchy.items():
        for office_name, office_info in region_info["offices"].items():
            office_code = office_info["code"]
            weather_data = get_weather_data(office_code)  # APIから天気データを取得
            if "error" not in weather_data:
                save_weather_data(office_code, weather_data)  # データベースに保存

# Fletアプリのメイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT

    initialize_database()  # データベース初期化

    try:
        area_hierarchy = load_area_hierarchy()  # 地域データを読み込む
    except FileNotFoundError as e:
        page.add(ft.Text(value=str(e), color="red"))
        return

    # 天気データが最新でない場合、更新を実行
    if not is_weather_data_up_to_date():
        update_weather_data(area_hierarchy)

    # UIの設定
    weather_container = ft.Column(scroll="auto")
    sidebar = ft.Column(width=300, expand=False)
    content_area = ft.Column(expand=True)

    region_dropdown = ft.Dropdown(
        hint_text="地方を選択",
        options=[ft.dropdown.Option(region) for region in area_hierarchy.keys()],
    )
    office_dropdown = ft.Dropdown(hint_text="都道府県を選択", options=[])
    area_dropdown = ft.Dropdown(hint_text="地域を選択", options=[])
    date_dropdown = ft.Dropdown(hint_text="日付を選択", options=[])

    # 初期メッセージを設定
    message = ft.Text(value="地方を選択してください。", color="blue", size=14)

    def region_change(e):
        selected_region = e.control.value
        if not selected_region:
            message.value = "地方を選択してください。"
            weather_container.controls.clear()
            page.update()
            return

        message.value = "都道府県を選択してください。"
        offices = area_hierarchy[selected_region]["offices"]
        office_dropdown.options = [ft.dropdown.Option(office) for office in offices.keys()]
        office_dropdown.update()
        area_dropdown.options = []
        area_dropdown.update()
        date_dropdown.options = []
        date_dropdown.update()
        weather_container.controls.clear()
        page.update()

    def office_change(e):
        selected_office = e.control.value
        if not selected_office:
            message.value = "都道府県を選択してください。"
            weather_container.controls.clear()
            page.update()
            return

        message.value = "地域を選択してください。"
        selected_region = region_dropdown.value

        # データベースから地域情報を取得
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT area_name FROM Areas
        INNER JOIN Prefectures ON Areas.prefecture_id = Prefectures.id
        WHERE Prefectures.prefecture_name = ?
        """, (selected_office,))
        area_names = [row[0] for row in cursor.fetchall()]
        conn.close()

        area_dropdown.options = [ft.dropdown.Option(area_name) for area_name in area_names]
        area_dropdown.update()
        date_dropdown.options = []
        date_dropdown.update()
        weather_container.controls.clear()
        page.update()

    def area_change(e):
        selected_area = e.control.value
        if not selected_area:
            message.value = "地域を選択してください。"
            weather_container.controls.clear()
            page.update()
            return

        message.value = "日付を選択してください。"

        # データベースから利用可能な日付を取得
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT date FROM WeatherReports
        INNER JOIN Areas ON WeatherReports.area_id = Areas.id
        WHERE Areas.area_name = ?
        ORDER BY date DESC
        """, (selected_area,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()

        date_dropdown.options = [ft.dropdown.Option(date) for date in dates]
        date_dropdown.update()
        weather_container.controls.clear()
        page.update()

    def date_change(e):
        selected_date = e.control.value
        if not selected_date:
            message.value = "日付を選択してください。"
            weather_container.controls.clear()
            page.update()
            return

        message.value = ""
        selected_area = area_dropdown.value

        # データベースから選択した日付の天気情報を取得
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT date, weather, wind, wave, weather_code FROM WeatherReports
        INNER JOIN Areas ON WeatherReports.area_id = Areas.id
        WHERE Areas.area_name = ? AND date = ?
        """, (selected_area, selected_date))
        report = cursor.fetchone()
        conn.close()

        weather_container.controls.clear()

        if report:
            date_text, weather_desc, wind, wave, weather_code = report
            waves_info = f"波: {wave}" if wave else "波: 情報なし"
            weather_image_url = f"https://www.jma.go.jp/bosai/forecast/img/{weather_code}.svg"
            try:
                response = requests.head(weather_image_url)
                if response.status_code == 200:
                    image = ft.Image(src=weather_image_url, width=80, height=80)
                else:
                    image = ft.Text("No Image")
            except Exception:
                image = ft.Text("No Image")

            # テキストの幅とオーバーフロー設定
            weather_text = ft.Text(
                weather_desc,
                size=18,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLACK,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            )

            weather_card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(date_text, weight=ft.FontWeight.BOLD, size=20, color=ft.colors.BLACK),
                            image,
                            weather_text,
                            ft.Text(f"風: {wind}", size=16, color=ft.colors.BLACK),
                            ft.Text(waves_info, size=16, color=ft.colors.BLACK),
                        ],
                        spacing=10,
                        alignment="center",
                    ),
                    padding=20
                ),
                width=450,
                elevation=3,
                margin=10
            )

            weather_container.controls.append(weather_card)
        else:
            weather_container.controls.append(ft.Text(f"選択した日付 ({selected_date}) の天気情報が見つかりません。", color="red"))
        page.update()

    # 更新ボタンのクリックイベントハンドラ
    def refresh_button_click(e):
        message.value = "データを更新しています..."
        page.update()
        update_weather_data(area_hierarchy)
        message.value = "データの更新が完了しました。"
        page.update()

    region_dropdown.on_change = region_change
    office_dropdown.on_change = office_change
    area_dropdown.on_change = area_change
    date_dropdown.on_change = date_change

    # 更新ボタンを作成
    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        tooltip="データを更新",
        on_click=refresh_button_click
    )

    # AppBarを設定
    page.appbar = ft.AppBar(
        title=ft.Text("天気予報アプリ"),
        actions=[
            refresh_button
        ]
    )

    sidebar.controls.extend([
        ft.Text("地域選択", size=20, weight=ft.FontWeight.BOLD),
        region_dropdown,
        office_dropdown,
        area_dropdown,
        date_dropdown,
        message
    ])

    page.add(
        ft.Row(
            [
                ft.Container(sidebar, bgcolor=ft.colors.SURFACE_VARIANT, padding=10),
                ft.Container(weather_container, padding=10, expand=True)
            ],
            expand=True
        )
    )

ft.app(target=main)