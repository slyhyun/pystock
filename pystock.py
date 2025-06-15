import PySimpleGUI as sg

def main_menu():
    sg.theme('LightBlue')  # 테마 설정 (원하는 테마로 변경 가능)

    layout = [
        [sg.Text('주식 분석 프로그램', font=('Helvetica', 16), justification='center', expand_x=True)],
        [sg.Button('📈 주식 검색', size=(20, 2), key='-SEARCH-')],
        [sg.Button('⚖️ 주식 비교', size=(20, 2), key='-COMPARE-')],
        [sg.Button('🔥 인기 주식', size=(20, 2), key='-POPULAR-')],
        [sg.Button('종료', size=(20, 1))]
    ]

    window = sg.Window('주식 분석 메인 메뉴', layout, element_justification='c')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '종료'):
            break
        elif event == '-SEARCH-':
            print("👉 주식 검색 기능으로 이동")
            # 주식 검색 화면 함수 호출 예정
        elif event == '-COMPARE-':
            print("👉 주식 비교 기능으로 이동")
            # 주식 비교 화면 함수 호출 예정
        elif event == '-POPULAR-':
            print("👉 인기 주식 기능으로 이동")
            # 인기 주식 화면 함수 호출 예정

    window.close()

# 실행
if __name__ == '__main__':
    main_menu()