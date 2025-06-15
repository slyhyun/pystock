import PySimpleGUI as sg
import requests
import pandas as pd
import io

# 종목 이름으로 코드 가져오기
def get_stock_code(stock_name):
    try:
        url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
        res = requests.get(url)
        df = pd.read_html(io.StringIO(res.text), header=0)[0]
        df = df[['회사명', '종목코드']]
        df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
        df['회사명'] = df['회사명'].str.strip()
        search_name = stock_name.strip().lower()

        # 정확히 일치하는 경우는 해당 종목 선택
        exact_match = df[df['회사명'].str.lower() == search_name]
        if not exact_match.empty:
            row = exact_match.iloc[0]
            return row['회사명'], row['종목코드']

        # 정확히 일치하는 종목이 없는 경우
        # 해당 단어를 포함한 가장 먼저 발견된 종목
        partial_match = df[df['회사명'].str.lower().str.contains(search_name)]
        if not partial_match.empty:
            row = partial_match.iloc[0]
            return row['회사명'], row['종목코드']

        return None, None
    # 해당 단어가 포함된 종목이 없을 때
    except Exception as e:
        print("❌ 종목 코드 조회 실패:", e)
        return None, None

# 주식 검색 창
def search_stock():
    layout = [
        [sg.Text('종목 이름을 입력하세요', expand_x=True, justification='center', font=('Helvetica', 16))],
        [sg.InputText(key='-STOCK-NAME-', expand_x=True, font=('Helvetica', 16))],
        [sg.Button('검색', expand_x=True, font=('Helvetica', 16)), sg.Button('뒤로가기', expand_x=True, font=('Helvetica', 16))],
        [sg.Multiline(key='-RESULT-', size=(60, 5), font=('Helvetica', 16), disabled=True)]
    ]

    window = sg.Window('주식 검색', layout, modal=True, resizable=True, element_justification='c')

    while True:
        event, values = window.read()
        # 뒤로가기 버튼
        if event in (sg.WIN_CLOSED, '뒤로가기'):
            break
        # 검색 버튼
        elif event == '검색':
            stock_name = values['-STOCK-NAME-'].strip()
            # 입력하지 않았을 때
            if not stock_name:
                window['-RESULT-'].update("⚠️ 종목 이름을 입력하세요.")
                continue

            matched_name, stock_code = get_stock_code(stock_name)
            # 일치하는 종목이 없을 때
            if not stock_code:
                window['-RESULT-'].update("❌ 해당 종목을 찾을 수 없습니다.")
            else:
                result = f"회사명 : {matched_name}\n종목코드 : {stock_code}"
                window['-RESULT-'].update(result)

    window.close()

# 메인 메뉴
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
        # 종료 버튼
        if event in (sg.WIN_CLOSED, '종료'):
            break
        # 주식 검색 버튼
        elif event == '-SEARCH-':
            search_stock()
        # 주식 비교 버튼
        elif event == '-COMPARE-':
            print("👉 주식 비교 기능으로 이동")
        # 인기 주식 버튼
        elif event == '-POPULAR-':
            print("👉 인기 주식 기능으로 이동")

    window.close()

if __name__ == '__main__':
    main_menu()