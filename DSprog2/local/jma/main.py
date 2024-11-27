import flet as ft
import requests
import json
import os

# JSONファイルから地域コードをロード（地域名をofficesのnameで置き換え）
def load_all_area_codes():
    file_path = os.path.join(os.path.dirname(__file__), "areas.json")
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSONファイルが見つかりません: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    area_codes = {}
    # officesのデータを取得
    for office_code, office_info in data["offices"].items():
        # officesのnameをキー、office_codeを値に設定
        area_codes[office_info["name"]] = office_code

    return area_codes

# 天気情報を取得
def get_weather_data(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch weather data"}

# Fletアプリのメイン
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT

    # 地域コードのロード
    try:
        area_codes = load_all_area_codes()
    except FileNotFoundError as e:
        page.add(ft.Text(value=str(e), color="red"))
        return

    # UI要素の作成
    selected_area = ft.Text(value="地域を選択してください", size=20)
    weather_info = ft.Text(value="", size=16)

    # ドロップダウン変更時のイベント
    def dropdown_change(e):
        selected_area.value = e.control.value
        area_code = area_codes[e.control.value]
        weather_data = get_weather_data(area_code)
        
        if "error" in weather_data:
            weather_info.value = "天気データを取得できませんでした。"
        else:
            # 天気情報を適切に整形して表示
            try:
                forecasts = weather_data[0]["timeSeries"][0]["areas"][0]["weathers"]
                weather_info.value = f"天気予報: {forecasts[0]}"
            except Exception as ex:
                weather_info.value = "データの形式が異なります。"

        page.update()

    # ドロップダウンメニュー
    dropdown = ft.Dropdown(
        hint_text="地域を選択",
        options=[ft.dropdown.Option(name) for name in area_codes.keys()],
        on_change=dropdown_change,
    )

    # ページ要素を追加
    page.add(
        ft.Column(
            [
                ft.Row([ft.Text("天気予報アプリ", size=30)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([dropdown]),
                ft.Row([selected_area]),
                ft.Row([weather_info]),
            ]
        )
    )

# アプリを実行
ft.app(target=main)