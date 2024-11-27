import flet as ft
import requests
import json
import os

# JSONファイルをロードして階層構造を構築
def load_area_hierarchy():
    # JSONファイルの絶対パスを指定（適宜修正してください）
    file_path = "/Users/milktea/Lecture/DSprog2/local/jma/areas.json"

    # ファイルの存在確認
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSONファイルが見つかりません: {file_path}")

    # JSONデータの読み込み
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    hierarchy = {}

    # 地方（centers）のデータを構築
    for center_code, center_info in data["centers"].items():
        region_name = center_info["name"]  # 地方名（例: 北海道地方）
        hierarchy[region_name] = {"code": center_code, "offices": {}}

        # 地方に紐づく地域（offices）のデータを構築
        for office_code in center_info["children"]:
            if office_code in data["offices"]:
                office_info = data["offices"][office_code]
                hierarchy[region_name]["offices"][office_info["name"]] = {"code": office_code}

    return hierarchy

# 天気情報を取得する関数
def get_weather_data(office_code):
    # 気象庁APIのURLを構築
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"
    response = requests.get(url)
    
    # 正常にデータを取得できた場合はJSONを返す
    if response.status_code == 200:
        return response.json()
    else:
        # エラー時の情報を返す
        return {"error": f"Failed to fetch weather data for code {office_code}"}

# Fletアプリのメイン関数
def main(page: ft.Page):
    # アプリケーションのタイトルを設定
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT

    # 地域階層をロード
    try:
        area_hierarchy = load_area_hierarchy()
    except FileNotFoundError as e:
        # JSONファイルが見つからない場合のエラーメッセージ
        page.add(ft.Text(value=str(e), color="red"))
        return

    # UI要素の作成（天気情報と詳細情報用テキスト）
    weather_info = ft.Text(value="", size=16)
    detailed_info = ft.Text(value="", size=14, color="blue")  # 細分化した地域情報用

    # 地方、地域、細分化地域のドロップダウンメニュー
    region_dropdown = ft.Dropdown(
        hint_text="地方を選択",  # 初期メッセージ
        options=[ft.dropdown.Option(region) for region in area_hierarchy.keys()],  # 地方リスト
    )
    office_dropdown = ft.Dropdown(hint_text="地域を選択", options=[])  # 地域リスト（動的更新）
    area_dropdown = ft.Dropdown(hint_text="細分化地域を選択", options=[])  # 細分化地域リスト（動的更新）

    # 地方選択時の処理
    def region_change(e):
        selected_region = e.control.value

        # 選択した地方に対応する地域リストを生成
        offices = area_hierarchy[selected_region]["offices"]
        office_dropdown.options = [ft.dropdown.Option(office) for office in offices.keys()]
        office_dropdown.update()
        area_dropdown.options = []
        weather_info.value = ""
        detailed_info.value = ""
        page.update()

    # 地域選択時の処理
    def office_change(e):
        selected_office = e.control.value
        selected_region = region_dropdown.value

        # 選択した地域のコードを取得
        offices = area_hierarchy[selected_region]["offices"]
        office_code = offices[selected_office]["code"]
        weather_data = get_weather_data(office_code)

        if "error" in weather_data:
            # 天気データ取得に失敗した場合
            weather_info.value = weather_data["error"]
            area_dropdown.options = []
        else:
            # 細分化地域（areas）リストを生成
            areas = weather_data[0]["timeSeries"][0]["areas"]
            area_dropdown.options = [ft.dropdown.Option(area["area"]["name"]) for area in areas]
            weather_info.value = f"{selected_office} の天気情報を取得しました。"
        area_dropdown.update()
        page.update()

    # 細分化地域選択時の処理
    def area_change(e):
        selected_area = e.control.value
        selected_office = office_dropdown.value
        selected_region = region_dropdown.value

        # 天気情報を取得
        offices = area_hierarchy[selected_region]["offices"]
        office_code = offices[selected_office]["code"]
        weather_data = get_weather_data(office_code)

        if "error" in weather_data:
            detailed_info.value = "細分化地域データの取得に失敗しました。"
        else:
            # 選択した細分化地域の天気情報を3日分表示
            areas = weather_data[0]["timeSeries"][0]["areas"]
            area_data = next((area for area in areas if area["area"]["name"] == selected_area), None)
            if area_data:
                # 天気、風、波の情報を3日分フォーマット
                weather_details = []
                for i, time in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"][:3]):
                    # 波情報が存在する場合のみ表示
                    waves_info = f"波: {area_data['waves'][i]}" if "waves" in area_data else "波: 情報なし"
                    day_weather = (
                        f"日時: {time}\n"
                        f"天気: {area_data['weathers'][i]}\n"
                        f"風: {area_data['winds'][i]}\n"
                        f"{waves_info}"
                    )
                    weather_details.append(day_weather)
                detailed_info.value = "\n\n".join(weather_details)
            else:
                detailed_info.value = f"選択した地域 ({selected_area}) の詳細情報が見つかりません。"
        page.update()

    # 各ドロップダウンにイベントリスナーを登録
    region_dropdown.on_change = region_change
    office_dropdown.on_change = office_change
    area_dropdown.on_change = area_change

    # ページにUI要素を追加
    page.add(
        ft.Column(
            [
                ft.Row([ft.Text("天気予報アプリ", size=30)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([region_dropdown]),  # 地方選択メニュー
                ft.Row([office_dropdown]),  # 地域選択メニュー
                ft.Row([area_dropdown]),  # 細分化地域選択メニュー
                ft.Row([weather_info]),  # 天気情報表示エリア
                ft.Row([detailed_info]),  # 詳細情報表示エリア
            ]
        )
    )

# アプリを実行
ft.app(target=main)