import PySimpleGUI as sg

def main_menu():
    sg.theme('LightBlue')

    layout = [
        [sg.Text('pystock', font=('Helvetica', 16), justification='center', expand_x=True)],
        [sg.Button('📈 주식 검색', size=(20, 2), key='-SEARCH-', expand_x=True)],
        [sg.Button('⚖️ 주식 비교', size=(20, 2), key='-COMPARE-', expand_x=True)],
        [sg.Button('🔥 인기 주식', size=(20, 2), key='-POPULAR-', expand_x=True)],
        [sg.Button('종료', size=(20, 1), expand_x=True)]
    ]

    window = sg.Window('pystock', layout, resizable=True, element_justification='c')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '종료'):
            break
        elif event == '-SEARCH-':
            print("👉 주식 검색 기능으로 이동")
        elif event == '-COMPARE-':
            print("👉 주식 비교 기능으로 이동")
        elif event == '-POPULAR-':
            print("👉 인기 주식 기능으로 이동")

    window.close()

if __name__ == '__main__':
    main_menu()