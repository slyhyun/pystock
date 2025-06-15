import PySimpleGUI as sg

def search_stock():
    layout = [
        [sg.Text('종목 이름을 입력하세요', expand_x=True, justification='center', font=('Helvetica', 16))],
        [sg.InputText(key='-STOCK-NAME-', expand_x=True, font=('Helvetica', 16))],
        [sg.Button('검색', expand_x=True, font=('Helvetica', 16)), sg.Button('뒤로가기', expand_x=True, font=('Helvetica', 16))]
    ]

    window = sg.Window('주식 검색', layout, modal=True, resizable=True, element_justification='c')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '뒤로가기'):
            break
        elif event == '검색':
            stock_name = values['-STOCK-NAME-'].strip()
            if stock_name:
                print(f"🔍 입력된 종목 이름 : {stock_name}")
                print("❌ 없는 주식입니다.")
            else:
                print("⚠️ 종목 이름을 입력하세요.")

    window.close()

def main_menu():
    sg.theme('LightBlue')

    layout = [
    [sg.Text('pystock', font=('Helvetica', 16), justification='center', expand_x=True)],
    [sg.Button('📈 주식 검색', size=(20, 2), key='-SEARCH-', expand_x=True, font=('Helvetica', 16))],
    [sg.Button('⚖️ 주식 비교', size=(20, 2), key='-COMPARE-', expand_x=True, font=('Helvetica', 16))],
    [sg.Button('🔥 인기 주식', size=(20, 2), key='-POPULAR-', expand_x=True, font=('Helvetica', 16))],
    [sg.Button('종료', size=(20, 1), expand_x=True, font=('Helvetica', 16))]
]

    window = sg.Window('pystock', layout, resizable=True, element_justification='c')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '종료'):
            break
        elif event == '-SEARCH-':
            search_stock()
        elif event == '-COMPARE-':
            print("👉 주식 비교 기능으로 이동")
        elif event == '-POPULAR-':
            print("👉 인기 주식 기능으로 이동")

    window.close()

if __name__ == '__main__':
    main_menu()