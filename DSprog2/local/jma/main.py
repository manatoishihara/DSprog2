import flet as ft
import requests
import json
import os

# JSONファイルをロードして階層構造を構築
def load_area_hierarchy():
    file_path = "/Users/milktea/Lecture/DSprog2/local/jma/areas.json"

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSONファイルが見つかりません: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    hierarchy = {}
    for center_code, center_info in data["centers"].items():
        region_name = center_info["name"]
        hierarchy[region_name] = {"code": center_code, "offices": {}}

        for office_code in center_info["children"]:
            if office_code in data["offices"]:
                office_info = data["offices"][office_code]
                hierarchy[region_name]["offices"][office_info["name"]] = {"code": office_code}

    return hierarchy

# 天気情報を取得する関数
def get_weather_data(office_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch weather data for code {office_code}"}

# Fletアプリのメイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT

    try:
        area_hierarchy = load_area_hierarchy()
    except FileNotFoundError as e:
        page.add(ft.Text(value=str(e), color="red"))
        return

    weather_container = ft.Column()
    sidebar = ft.Column(width=300, expand=False)
    content_area = ft.Column(expand=True)

    region_dropdown = ft.Dropdown(
        hint_text="地方を選択",
        options=[ft.dropdown.Option(region) for region in area_hierarchy.keys()],
    )
    office_dropdown = ft.Dropdown(hint_text="都道府県を選択", options=[])
    area_dropdown = ft.Dropdown(hint_text="地域を選択", options=[])

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
        offices = area_hierarchy[selected_region]["offices"]
        office_code = offices[selected_office]["code"]
        weather_data = get_weather_data(office_code)

        if "error" in weather_data:
            weather_container.controls.clear()
            weather_container.controls.append(ft.Text(value=weather_data["error"], color="red"))
        else:
            areas = weather_data[0]["timeSeries"][0]["areas"]
            area_dropdown.options = [ft.dropdown.Option(area["area"]["name"]) for area in areas]
            area_dropdown.update()
        weather_container.controls.clear()
        page.update()

    def area_change(e):
        selected_area = e.control.value
        if not selected_area:
            message.value = "地域を選択してください。"
            weather_container.controls.clear()
            page.update()
            return

        message.value = ""
        selected_office = office_dropdown.value
        selected_region = region_dropdown.value

        offices = area_hierarchy[selected_region]["offices"]
        office_code = offices[selected_office]["code"]
        weather_data = get_weather_data(office_code)

        if "error" in weather_data:
            weather_container.controls.clear()
            weather_container.controls.append(ft.Text("地域データの取得に失敗しました。", color="red"))
        else:
            areas = weather_data[0]["timeSeries"][0]["areas"]
            area_data = next((area for area in areas if area["area"]["name"] == selected_area), None)
            if area_data:
                weather_container.controls.clear()
                for i, time in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"][:3]):
                    date = time.split("T")[0]  # 日付だけを抽出
                    weather_code = area_data["weatherCodes"][i]
                    weather_image_url = f"https://www.jma.go.jp/bosai/forecast/img/{weather_code}.svg"
                    waves_info = f"波: {area_data['waves'][i]}" if "waves" in area_data else "波: 情報なし"
                    try:
                        response = requests.head(weather_image_url)
                        if response.status_code == 200:
                            image = ft.Image(src=weather_image_url, width=50, height=50)
                        else:
                            raise Exception("Image not found")
                    except Exception:
                        image = ft.Text("No Image")

                    weather_container.controls.append(
                        ft.Card(
                            content=ft.Column(
                                [
                                    ft.Text(date, weight=ft.FontWeight.BOLD, size=16),
                                    ft.Text(f"天気: {area_data['weathers'][i]}", size=14),
                                    ft.Text(f"風: {area_data['winds'][i]}", size=14),
                                    ft.Text(waves_info, size=14),
                                    image
                                ],
                                spacing=10
                            ),
                            width=400,
                            elevation=2,
                            margin=10
                        )
                    )
            else:
                weather_container.controls.clear()
                weather_container.controls.append(ft.Text(f"選択した地域 ({selected_area}) の詳細情報が見つかりません。", color="red"))
        page.update()

    region_dropdown.on_change = region_change
    office_dropdown.on_change = office_change
    area_dropdown.on_change = area_change

    sidebar.controls.extend([
        ft.Text("地域選択", size=20, weight=ft.FontWeight.BOLD),
        region_dropdown,
        office_dropdown,
        area_dropdown,
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