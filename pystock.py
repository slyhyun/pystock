import PySimpleGUI as sg
import requests
from bs4 import BeautifulSoup
import mplfinance as mpf
import pandas as pd
import io
import os

# 종목 이름으로 코드 가져오기
def get_stock_code(stock_name):
    try:
        url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
        res = requests.get(url)
        df = pd.read_html(io.StringIO(res.text), header=0)[0]
        df = df[['회사명', '종목코드']]
        df['종목코드'] = df['종목코드'].apply(lambda x : f"{x:06d}")
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
        print("❌ 종목 코드 조회 실패 :", e)
        return None, None
    
# 종목 정보 가져오기 (네이버 금융)
def get_stock_info(stock_code):
    url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
    headers = {'User-Agent' : 'Mozilla/5.0'}
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
            print("❌ 전일대비/등락률 가져오기 실패 :", e)

        # 시가 / 고가 / 저가 / 거래량 / 거래대금 (정확한 위치 기반 추출)
        try:
            label_map = {
                '전일' : ('전일가', '원'),
                '고가' : ('고가', '원'),
                '시가' : ('시가', '원'),
                '저가' : ('저가', '원'),
                '거래량' : ('거래량', '주'),
                '거래대금' : ('거래대금', '백만')
            }

            rate_info = soup.select_one('div.rate_info')
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
            print("❌ 시세 데이터 가져오기 실패 :", e)


        # 시가총액
        try:
            market_sum = soup.select_one('#_market_sum')
            if market_sum:
                parts = market_sum.text.strip().split()
                info['시가총액'] = ' '.join(parts) + '억원' if len(parts) == 2 else market_sum.text.strip() + '억원'
        except Exception as e:
            print("❌ 시가총액 가져오기 실패 :", e)

        # PER, EPS
        try:
            info['PER'] = safe_text(soup.select_one('em#_per'), '배')
            info['EPS'] = safe_text(soup.select_one('em#_eps'), '원')
        except Exception as e:
            print("❌ PER 또는 EPS 가져오기 실패 :", e)

        # 추정 PER, EPS
        try:
            info['추정 PER'] = safe_text(soup.select_one('em#_cns_per'), '배')
            info['추정 EPS'] = safe_text(soup.select_one('em#_cns_eps'), '원')
        except Exception as e:
            print("❌ 추정 PER 또는 EPS 가져오기 실패 :", e)

        # PBR, BPS
        try:
            pbr_tr = soup.select_one('table.per_table').select('tr')[2]
            ems = pbr_tr.select('em')
            pbr_val = ems[0].text.strip().replace('배', '')
            bps_val = ems[1].text.strip().replace('원', '')
            info['PBR'] = pbr_val + '배' if pbr_val else 'N/A'
            info['BPS'] = bps_val + '원' if bps_val else 'N/A'
        except Exception as e:
            print("❌ PBR 또는 BPS 가져오기 실패 :", e)

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
            print("❌ 배당수익률 가져오기 실패 :", e)

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
            print("❌ 외국인소진율 가져오기 실패 :", e)

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
            print("❌ 동일업종 PER 가져오기 실패 :", e)

        return info if info else None

    except Exception as e:
        print("❌ 전체 페이지 파싱 실패 :", e)
        return None

# 일별 시세 테이블 크롤링
def get_price_table(stock_code, pages=3):
    dfs = []
    for page in range(1, pages + 1):
        url = f'https://finance.naver.com/item/sise_day.nhn?code={stock_code}&page={page}'
        res = requests.get(url, headers={'User-Agent' : 'Mozilla/5.0'})
        df = pd.read_html(res.text, header=0)[0]
        dfs.append(df)
    df_all = pd.concat(dfs)
    df_all = df_all.dropna()
    df_all['날짜'] = pd.to_datetime(df_all['날짜'])
    df_all = df_all.rename(columns={'날짜' : 'Date', '시가' : 'Open', '고가' : 'High', '저가' : 'Low', '종가' : 'Close', '거래량' : 'Volume'})
    df_all.set_index('Date', inplace=True)
    df_all = df_all.sort_index()
    return df_all

# 캔들차트 재구성
def resample_ohlcv(df, rule='W'):
    ohlcv = {
        'Open' : 'first',
        'High' : 'max',
        'Low' : 'min',
        'Close' : 'last',
        'Volume' : 'sum'
    }
    return df.resample(rule).apply(ohlcv).dropna()

# 캔들차트 이미지로 저장
def plot_candle_chart(df, filename='chart.png'):
    mc = mpf.make_marketcolors(up='red', down='blue', edge='inherit', wick='gray', volume='inherit')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')
    mpf.plot(df, type='candle', style=s, volume=True, savefig=filename)

# 주식 검색 창
def search_stock_window():
    layout = [
        [sg.Text('종목 이름을 입력하세요', font=('Helvetica', 16))],
        [sg.InputText(key='-STOCK-NAME-', font=('Helvetica', 16))],
        [sg.Button('일봉', key='-D-', font=('Helvetica', 16)), sg.Button('주봉', key='-W-', font=('Helvetica', 16)), sg.Button('월봉', key='-M-', font=('Helvetica', 16))],
        [sg.Button('검색', expand_x=True, font=('Helvetica', 16)), sg.Button('뒤로가기', expand_x=True, font=('Helvetica', 16))],
        [sg.Image(key='-CHART-')],
        [sg.Multiline(key='-INFO-', size=(70, 10), font=('Consolas', 16), disabled=True)]
    ]

    window = sg.Window('주식 검색', layout, modal=True, resizable=True, element_justification='c')
    chart_period = 'D'
    pages_map = {'D' : 3, 'W' : 15, 'M' : 60}
    last_stock_name = ''

    while True:
        event, values = window.read()
        # 뒤로가기 버튼
        if event in (sg.WIN_CLOSED, '뒤로가기'):
            break

        # 사용자가 일봉/주봉/월봉 버튼 중 하나를 클릭했을 때
        if event in ['-D-', '-W-', '-M-']:
            chart_period = event.strip('-')
            if last_stock_name:
                # 종목명으로 종목 코드 조회
                matched_name, stock_code = get_stock_code(last_stock_name)
                # 종목이 없는 경우
                if not stock_code:
                    window['-INFO-'].update("❌ 없는 주식입니다.")
                    window['-CHART-'].update(data=None)
                    continue
                # 있는 경우 시세 정보 주기 가져오기
                df = get_price_table(stock_code, pages=pages_map[chart_period])
                # 주봉, 월봉인 경우 재구성
                if chart_period in ['W', 'M']:
                    df = resample_ohlcv(df, rule=chart_period)
                plot_candle_chart(df)
                with open('chart.png', 'rb') as f:
                    img = f.read()
                window['-CHART-'].update(data=img)

        # 검색 버튼
        if event == '검색':
            stock_name = values['-STOCK-NAME-'].strip()
            if not stock_name:
                window['-INFO-'].update("⚠️ 종목 이름을 입력하세요.")
                continue

            last_stock_name = stock_name
            matched_name, stock_code = get_stock_code(stock_name)
            # 일치하는 종목이 없을 때
            if not stock_code:
                window['-INFO-'].update("❌ 없는 주식입니다.")
                window['-CHART-'].update(data=None)
                continue

            info = get_stock_info(stock_code)
            # 주식 정보 크롤링에 실패했을 때
            if not info:
                window['-INFO-'].update("❌ 주식 정보 조회 실패")
                continue
            
            df = get_price_table(stock_code, pages=pages_map[chart_period])
            # 시세 테이블 크롤링에 실패했을 때
            if df.empty:
                window['-INFO-'].update("❌ 시세 정보가 부족합니다.")
                window['-CHART-'].update(data=None)
                continue
            
            if chart_period in ['W', 'M']:
                df = resample_ohlcv(df, rule=chart_period)
            
            plot_candle_chart(df)
            # 시세 차트 그리기
            with open('chart.png', 'rb') as f:
                img = f.read()

            # 크롤링에 성공했을 때
            info_text = f"[{matched_name}] ({stock_code})\n"
            for k, v in info.items():
                info_text += f"{k} : {v}\n"

            window['-INFO-'].update(info_text)
            window['-CHART-'].update(data=img)

    window.close()
    if os.path.exists('chart.png'):
        os.remove('chart.png')

# 주식 비교 창
def compare_stock_window():
    layout = [
        [sg.Text('종목1 :', font=('Helvetica', 16)), sg.InputText(key='-STOCK1-', font=('Helvetica', 16)), sg.Text('종목2 :', font=('Helvetica', 16)), sg.InputText(key='-STOCK2-', font=('Helvetica', 16))],
        [sg.Button('일봉', key='-D-', font=('Helvetica', 16)), sg.Button('주봉', key='-W-', font=('Helvetica', 16)), sg.Button('월봉', key='-M-', font=('Helvetica', 16))],
        [sg.Button('검색', expand_x=True, font=('Helvetica', 16)), sg.Button('뒤로가기', expand_x=True, font=('Helvetica', 16))],
        [sg.Column([[sg.Image(key='-CHART1-')]]), sg.Column([[sg.Image(key='-CHART2-')]])],
        [sg.Multiline(key='-INFO1-', size=(70, 10), font=('Consolas', 16), disabled=True),
         sg.Multiline(key='-INFO2-', size=(70, 10), font=('Consolas', 16), disabled=True)]
    ]
    window = sg.Window('주식 비교', layout, resizable=True, modal=True, element_justification='c')
    chart_period = 'D'
    pages_map = {'D' : 3, 'W' : 15, 'M' : 60}
    stock_names = ['', '']

    def update_stock(index):
        name, code = get_stock_code(stock_names[index])
        # 일치하는 종목이 없을 때
        if not code:
            window[f'-INFO{index+1}-'].update("❌ 없는 주식입니다.")
            window[f'-CHART{index+1}-'].update(data=None)
            return
        
        # 주식 정보 가져오기
        info = get_stock_info(code)
        # 주식 정보 크롤링에 실패했을 때
        if not info:
            window[f'-INFO{index+1}-'].update("❌ 주식 정보 조회 실패")
            window[f'-CHART{index+1}-'].update(data=None)
            return

        # 시세 정보 가져오기
        df = get_price_table(code, pages=pages_map[chart_period])
        # 시세 정보 크롤링에 실패했을 때
        if df.empty:
            window[f'-INFO{index+1}-'].update("❌ 시세 정보가 부족합니다.")
            window[f'-CHART{index+1}-'].update(data=None)
            return

        # 주봉, 일봉인 경우 재구성
        if chart_period in ['W', 'M']:
            df = resample_ohlcv(df, rule=chart_period)
        filename = f'chart{index+1}.png'
        plot_candle_chart(df, filename=filename)
        with open(filename, 'rb') as f:
            img = f.read()
        info_text = f"[{name}] ({code})\n"
        for k, v in info.items():
            info_text += f"{k}: {v}\n"
        window[f'-INFO{index+1}-'].update(info_text)
        window[f'-CHART{index+1}-'].update(data=img)

    while True:
        event, values = window.read()
        # 뒤로가기 버튼
        if event in (sg.WIN_CLOSED, '뒤로가기'):
            break
        # 주기 변경 시
        if event in ['-D-', '-W-', '-M-']:
            chart_period = event.strip('-')
            if all(stock_names):
                update_stock(0)
                update_stock(1)
        # 검색 버튼 
        if event == '검색':
            stock_names[0] = values['-STOCK1-'].strip()
            stock_names[1] = values['-STOCK2-'].strip()
            # 종목을 전부 입력하지 않았을 때
            if not all(stock_names):
                sg.popup("⚠️ 두 종목을 모두 입력하세요.")
                continue
            update_stock(0)
            update_stock(1)

    window.close()
    for i in [1, 2]:
        if os.path.exists(f'chart{i}.png'):
            os.remove(f'chart{i}.png')

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
            search_stock_window()
        # 주식 비교 버튼
        elif event == '-COMPARE-':
            compare_stock_window()
        # 인기 주식 버튼
        elif event == '-POPULAR-':
            print("👉 인기 주식 기능으로 이동")

    window.close()

if __name__ == '__main__':
    main_menu()