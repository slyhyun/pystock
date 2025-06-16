import PySimpleGUI as sg
import requests
from bs4 import BeautifulSoup
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
    
# 종목 정보 가져오기 (네이버 금융)
def get_stock_info(stock_code):
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    info = {}

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        def safe_text(selector, suffix='', default='N/A'):
            try:
                text = selector.text.strip().replace(suffix, '').replace('\xa0', '')
                return text + suffix if text and text != 'N/A' else default
            except:
                return default

        # 현재가
        info['현재가'] = safe_text(soup.select_one('p.no_today span.blind'), '원')

        # 전일 대비 및 등락률
        try:
            # 전일 대비
            diff_td = soup.select_one('th:contains("전일대비") + td em')
            if diff_td:
                span = diff_td.find('span')
                direction_text = span.text.strip() if span else ''
                full_text = diff_td.get_text(strip=True)
                price_only = full_text.replace(direction_text, '').replace('원', '').strip()
                info['전일 대비'] = f"{price_only}원 {direction_text}" if price_only else 'N/A'

            # 등락률
            rate_td = soup.select_one('th:contains("등락률") + td em')
            if rate_td:
                raw_rate = rate_td.text.strip().replace('상향', '').replace('하향', '').replace('%', '').strip()
                info['등락률'] = raw_rate + '%' if raw_rate else 'N/A'
        except Exception as e:
            print("❌ 전일대비/등락률 가져오기 실패:", e)

        # 시가 / 고가 / 저가 / 거래량 / 거래대금 (정확한 위치 기반 추출)
        try:
            label_map = {
                '전일': ('전일가', '원'),
                '고가': ('고가', '원'),
                '시가': ('시가', '원'),
                '저가': ('저가', '원'),
                '거래량': ('거래량', '주'),
                '거래대금': ('거래대금', '백만')
            }

            rate_info = soup.select_one('div.rate_info')  # ✅ 기본 주가 정보 섹션만 선택
            if rate_info:
                for td in rate_info.select('table.no_info td'):
                    label_span = td.select_one('span.sptxt')
                    value_em = td.select_one('em span.blind')
                    if label_span and value_em:
                        label_text = label_span.text.strip().replace('(', '').replace(')', '')
                        if label_text in label_map:
                            key, unit = label_map[label_text]
                            val = value_em.text.strip().replace(unit, '')
                            info[key] = val + unit if val else 'N/A'
        except Exception as e:
            print("❌ 시세 데이터 (시가, 고가 등) 정밀 추출 실패:", e)


        # 시가총액
        try:
            market_sum = soup.select_one('#_market_sum')
            if market_sum:
                parts = market_sum.text.strip().split()
                info['시가총액'] = ' '.join(parts) + '억원' if len(parts) == 2 else market_sum.text.strip() + '억원'
        except Exception as e:
            print("❌ 시가총액 가져오기 실패:", e)

        # PER, EPS
        try:
            info['PER'] = safe_text(soup.select_one('em#_per'), '배')
            info['EPS'] = safe_text(soup.select_one('em#_eps'), '원')
        except Exception as e:
            print("❌ PER 또는 EPS 가져오기 실패:", e)

        # 추정 PER, EPS
        try:
            info['추정 PER'] = safe_text(soup.select_one('em#_cns_per'), '배')
            info['추정 EPS'] = safe_text(soup.select_one('em#_cns_eps'), '원')
        except Exception as e:
            print("❌ 추정 PER 또는 EPS 가져오기 실패:", e)

        # PBR, BPS
        try:
            pbr_tr = soup.select_one('table.per_table').select('tr')[2]
            ems = pbr_tr.select('em')
            pbr_val = ems[0].text.strip().replace('배', '')
            bps_val = ems[1].text.strip().replace('원', '')
            info['PBR'] = pbr_val + '배' if pbr_val else 'N/A'
            info['BPS'] = bps_val + '원' if bps_val else 'N/A'
        except Exception as e:
            print("❌ PBR 또는 BPS 가져오기 실패:", e)

        # 배당수익률
        try:
            for th in soup.select('table.per_table th'):
                if '배당수익률' in th.text:
                    td = th.find_next_sibling('td')
                    if td:
                        em = td.find('em')
                        val = em.text.strip().replace('%', '') if em else ''
                        info['배당수익률'] = val + '%' if val else 'N/A'
                    break
        except Exception as e:
            print("❌ 배당수익률 가져오기 실패:", e)

        # 외국인소진율
        try:
            for th in soup.select('th'):
                if '외국인소진율' in th.text:
                    td = th.find_next_sibling('td')
                    if td:
                        em = td.find('em')
                        val = em.text.strip().replace('%', '') if em else ''
                        info['외국인소진율'] = val + '%' if val else 'N/A'
                    break
        except Exception as e:
            print("❌ 외국인소진율 가져오기 실패:", e)

        # 동일업종 PER
        try:
            for th in soup.select('th'):
                if '동일업종 PER' in th.text:
                    td = th.find_next_sibling('td')
                    if td:
                        em = td.find('em')
                        val = em.text.strip().replace('배', '') if em else ''
                        info['동일업종 PER'] = val + '배' if val else 'N/A'
                    break
        except Exception as e:
            print("❌ 동일업종 PER 가져오기 실패:", e)

        return info if info else None

    except Exception as e:
        print("❌ 전체 페이지 파싱 실패:", e)
        return None

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
                continue
            
            info = get_stock_info(stock_code)
            # 크롤링에 실패했을 때
            if not info:
                window['-RESULT-'].update("❌ 주식 정보 조회 실패")
                continue
            
            # 크롤링에 성공했을 때
            result = f"회사명 : {matched_name}\n종목코드 : {stock_code}\n\n"
            for k, v in info.items():
                result += f"{k} : {v}\n"
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