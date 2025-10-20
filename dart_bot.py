import requests    
import os
import json

API_KEY = os.getenv("DART_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# File to store the last texts list
LAST_TEXTS_FILE = "last_texts.json"

from datetime import datetime, timezone, timedelta

# Korea timezone (UTC+9)
korea_tz = timezone(timedelta(hours=9))
weekday_kr = {
    0: '(월)',
    1: '(화)',
    2: '(수)', 
    3: '(목)',
    4: '(금)',
    5: '(토)',
    6: '(일)'
}
def save_last_texts(texts):
    try:
        with open(LAST_TEXTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving last texts: {e}")

def load_last_texts():
    try:
        if os.path.exists(LAST_TEXTS_FILE):
            with open(LAST_TEXTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
    except Exception as e:
        print(f"Error loading last texts: {e}")
    return []

def texts_are_same(texts1, texts2):
    if not texts1 and not texts2: return True
    if len(texts1) != len(texts2): return False
    return texts1 == texts2

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
    # Calculate current time each time function runs
    today = datetime.now(korea_tz)
    today_string = today.strftime('%Y-%m-%d %H:%M') + ' ' + weekday_kr[today.weekday()]
    today_yyyymmdd = today.strftime('%Y%m%d')

    info_string = ""
    # Skip execution on weekends
    if today.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
        return None
    # current_hour = today.hour
    # if current_hour >= 21 or current_hour < 6:
    #     return None
    # if current_hour == 20:
    #     info_string = "오늘의 마지막 안내입니다.\n"
    
    reported_corp_codes = []
    page_no = 1
    no_data = False
    while True:
        data = get_dart_reports(today_yyyymmdd, today_yyyymmdd, page_no)
        if data['status'] != '000':
            no_data = True
            break
        for item in data['list']:
            reported_corp_codes.append(item['corp_code'])
        if data['total_count'] == 100: page_no += 1
        else: break
    
    texts = []
    if not no_data:
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
    last_texts = load_last_texts()
    
    if texts and not texts_are_same(texts, last_texts):
        new_texts = []
        old_texts = []
        
        for text in texts:
            if text not in last_texts:
                new_texts.append(text)
            else:
                old_texts.append(text)
        
        ordered_texts = new_texts + old_texts        
        result_text = f"{info_string}{today_string}\n일일 누적 발행내역입니다.\n\n" + "\n".join(ordered_texts)
        send_message(result_text)
        save_last_texts(texts)
    else:
        return None
    return None

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

if __name__ == "__main__":
    run()
