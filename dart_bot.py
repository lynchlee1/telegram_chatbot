import requests    
import os

API_KEY = os.getenv("DART_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

from datetime import datetime
today = datetime.today()
weekday_kr = {
    0: '(월)',
    1: '(화)',
    2: '(수)', 
    3: '(목)',
    4: '(금)',
    5: '(토)',
    6: '(일)'
}
today_string = today.strftime('%Y-%m-%d %H:%M') + ' ' + weekday_kr[today.weekday()]
today_yyyymmdd = today.strftime('%Y%m%d')

def process_data(data):
    result = []
    if 'status' not in data: return False
    if data['status'] == '000':
        for main_data in data['list']:
            result.append({
                'rcept_no': main_data['rcept_no'],
                'corp_name': main_data['corp_name'],
                'bd_fta': main_data['bd_fta']
            })
        return result
    else: return False

def textize(data, type):
    if not data: return False
    return f"- {data['corp_name']} {type} {round(float(data['bd_fta'].replace(',',''))/10**8,1)}억 \n https://dart.fss.or.kr/dsaf001/main.do?rcpNo={data['rcept_no']}\n"

def get_dart_reports(start_date, end_date, page_no=1):
    base_url = "https://opendart.fss.or.kr/api/list.json"
    
    params = {
        'crtfc_key': API_KEY,
        'bgn_de': start_date,
        'end_de': end_date,
        'last_reprt_at': 'Y',
        'pblntf_ty': 'B',
        'pblntf_detail_ty': 'B001',
        'page_no': page_no,
        'page_count': "100"
    }
    response = requests.get(base_url, params=params)
    return response.json()

def get_dart_report_details(corp_code, date_string):
    base_url_bw = "https://opendart.fss.or.kr/api/bdwtIsDecsn.json"
    base_url_cb = "https://opendart.fss.or.kr/api/cvbdIsDecsn.json"
    base_url_eb = "https://opendart.fss.or.kr/api/exbdIsDecsn.json"

    params = {
        'crtfc_key': API_KEY,
        'corp_code': corp_code,
        'bgn_de': date_string,
        'end_de': date_string
    }
    
    response_bw = requests.get(base_url_bw, params=params)
    response_cb = requests.get(base_url_cb, params=params)
    response_eb = requests.get(base_url_eb, params=params)
    return response_bw.json(), response_cb.json(), response_eb.json()


def run():
    reported_corp_codes = []
    page_no = 1
    while True:
        data = get_dart_reports(today_yyyymmdd, today_yyyymmdd, page_no)
        for item in data['list']:
            reported_corp_codes.append(item['corp_code'])
        if data['total_count'] == 100: page_no += 1
        else: break
    
    texts = []
    texts_codes = list()
    for corp_code in reported_corp_codes:
        bw_data, cb_data, eb_data = [], [], []
        responce_bw, responce_cb, responce_eb = get_dart_report_details(corp_code, today_yyyymmdd)

        bw_data = process_data(responce_bw)
        cb_data = process_data(responce_cb)
        eb_data = process_data(responce_eb)

        if bw_data:
            for data in bw_data:
                if data['rcept_no'] not in texts_codes:
                    texts.append(textize(data, 'BW'))
                    texts_codes.append(data['rcept_no'])
        if cb_data:
            for data in cb_data:
                if data['rcept_no'] not in texts_codes:
                    texts.append(textize(data, 'CB'))
                    texts_codes.append(data['rcept_no'])
        if eb_data:
            for data in eb_data:
                if data['rcept_no'] not in texts_codes:
                    texts.append(textize(data, 'EB'))
                    texts_codes.append(data['rcept_no'])
    if texts:
        result_text = f"{today_string}\n <b>금일 누적 발행내역입니다.</b>\n\n" + "\n".join(texts)
    else:
        result_text = f"{today_string}\n <b>금일 누적 발행내역입니다.</b>\n\n없음"
    send_message(result_text)
    return None

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=data)

if __name__ == "__main__":
    run()
