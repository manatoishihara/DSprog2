import flet as ft
import math


class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text


class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        CalcButton.__init__(self, text, button_clicked, expand)
        self.bgcolor = ft.colors.WHITE24
        self.color = ft.colors.WHITE


class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.ORANGE
        self.color = ft.colors.WHITE


class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = ft.colors.BLUE_GREY_100
        self.color = ft.colors.BLACK


class ScienceButton(CalcButton):
    def __init__(self, text, button_clicked):
        CalcButton.__init__(self, text, button_clicked)
        self.bgcolor = "#2A2A2A"
        self.color = ft.colors.WHITE


class CalculatorApp(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.reset()

    def build(self):
        self.result = ft.Text(value="0", color=ft.colors.WHITE, size=24)
        return ft.Container(
            width=400,
            bgcolor=ft.colors.BLACK,
            border_radius=ft.border_radius.all(20),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.result],
                        alignment="end",
                        expand=True,
                    ),
                    ft.Row(
                        controls=[
                            ExtraActionButton("AC", self.button_clicked),
                            ExtraActionButton("+/-", self.button_clicked),
                            ExtraActionButton("%", self.button_clicked),
                            ActionButton("/", self.button_clicked),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ScienceButton("sin", self.button_clicked),
                            ScienceButton("cos", self.button_clicked),
                            ScienceButton("tan", self.button_clicked),
                            ActionButton("*", self.button_clicked),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ScienceButton("x²", self.button_clicked),
                            ScienceButton("√x", self.button_clicked),
                            ScienceButton("log", self.button_clicked),
                            ScienceButton("ln", self.button_clicked)
                        ]
                    ),
                    ft.Row(
                        controls=[
                            DigitButton("7", self.button_clicked),
                            DigitButton("8", self.button_clicked),
                            DigitButton("9", self.button_clicked),
                            ActionButton("-", self.button_clicked),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            DigitButton("4", self.button_clicked),
                            DigitButton("5", self.button_clicked),
                            DigitButton("6", self.button_clicked),
                            ActionButton("+", self.button_clicked),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            DigitButton("1", self.button_clicked),
                            DigitButton("2", self.button_clicked),
                            DigitButton("3", self.button_clicked),
                            ActionButton("=", self.button_clicked),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            DigitButton("0", self.button_clicked),
                            DigitButton("00", self.button_clicked),
                            DigitButton(".", self.button_clicked),
                            ActionButton("^", self.button_clicked),
                        ]
                    ),
                ],
                expand=True,
                alignment="center",
            ),
        )

    def button_clicked(self, e):
        data = e.control.data
        print(f"Button clicked with data = {data}")
        try:
            if self.result.value == "Error" or data == "AC":
                self.result.value = "0"
                self.reset()

            elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "00", "."):
                if self.result.value == "0" or self.new_operand:
                    self.result.value = data
                    self.new_operand = False
                else:
                    self.result.value += data

            elif data in ("+", "-", "*", "/", "^"):
                self.operand1 = float(self.result.value)
                self.operator = data
                self.new_operand = True

            elif data == "=":
                self.result.value = self.calculate(
                    self.operand1, float(self.result.value), self.operator
                )
                self.reset()

            elif data == "%":
                self.result.value = str(float(self.result.value) / 100)
                self.reset()

            elif data == "+/-":
                self.result.value = str(-float(self.result.value))

            elif data == "sin":
                self.result.value = str(math.sin(math.radians(float(self.result.value))))
                self.reset()

            elif data == "cos":
                self.result.value = str(math.cos(math.radians(float(self.result.value))))
                self.reset()

            elif data == "tan":
                self.result.value = str(math.tan(math.radians(float(self.result.value))))
                self.reset()

            elif data == "ln":
                self.result.value = str(math.log(float(self.result.value)))
                self.reset()

            elif data == "log":
                self.result.value = str(math.log10(float(self.result.value)))
                self.reset()

            elif data == "x²":
                self.result.value = str(float(self.result.value) ** 2)
                self.reset()

            elif data == "√x":
                self.result.value = str(math.sqrt(float(self.result.value)))
                self.reset()

        except Exception:
            self.result.value = "Error"

        self.update()

    def calculate(self, operand1, operand2, operator):
        if operator == "+":
            return str(operand1 + operand2)
        elif operator == "-":
            return str(operand1 - operand2)
        elif operator == "*":
            return str(operand1 * operand2)
        elif operator == "/":
            return "Error" if operand2 == 0 else str(operand1 / operand2)
        elif operator == "^":
            return str(operand1 ** operand2)

    def reset(self):
        self.operator = ""
        self.operand1 = 0
        self.new_operand = True


def main(page: ft.Page):
    page.title = "電卓"
    page.window_width = 420
    page.window_height = 600
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    calc = CalculatorApp()
    page.add(calc)


ft.app(target=main)