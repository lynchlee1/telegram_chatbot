import requests    
import zipfile
from io import BytesIO
import os
import json
from bs4 import BeautifulSoup

API_KEY = os.getenv("DART_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_KEY or not BOT_TOKEN or not CHAT_ID:
    from configs import API_KEY, BOT_TOKEN, CHAT_ID

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
    current_hour = today.hour
    if current_hour == 1:
        try:
            with open("requirements.txt", "w", encoding='utf-8') as reqf:
                reqf.write("")
        except Exception as e:
            print(f"Error resetting requirements.txt: {e}")
    # if current_hour >= 21 or current_hour < 6:
    #     return None
    # if current_hour == 20:
    #     info_string = "오늘의 마지막 안내입니다.\n"
    
    reported_corp_codes = set()
    reported_rcept_nos = dict()
    page_no = 1
    no_data = False
    while True:
        data = get_dart_reports(today_yyyymmdd, today_yyyymmdd, page_no)
        if data['status'] != '000':
            no_data = True
            break
        for item in data['list']:
            filter_words = ['정정', '감자', '증자', '선택권', '처분', '자기', '자본', '양수도', '소송', '합병', '분할']
            if any(word in item['report_nm'] for word in filter_words):
                continue
            reported_corp_codes.add(item['corp_code'])
            reported_rcept_nos[item['rcept_no']] = [item.get('corp_name', ''), item.get('report_nm', '')]
        if data['total_count'] == 100: page_no += 1
        else: break

    reported_corp_codes = list(reported_corp_codes)
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

    source_download_url = "https://opendart.fss.or.kr/api/document.xml"
    output_entries = []
    for rcept_no, info in reported_rcept_nos.items():
        corp_name, report_nm = info[0], info[1]
        if '교환' in report_nm: report_type = 'EB'
        elif '전환' in report_nm: report_type = 'CB'
        elif '신주인수권부' in report_nm: report_type = 'BW'
        else: report_type = ''
        url = f"{source_download_url}?crtfc_key={API_KEY}&rcept_no={rcept_no}"
        response = requests.get(url)
        try:
            with zipfile.ZipFile(BytesIO(response.content)) as zf:
                file_list = zf.namelist()
                for name in file_list:
                    with zf.open(name) as f:
                        data = f.read()
                        try:
                            text = data.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                text = data.decode('cp949')
                            except UnicodeDecodeError:
                                text = None
                        if text is not None:
                            soup = BeautifulSoup(text, 'html.parser')
                            all_tables = soup.find_all('table')
                            first_table = next((t for t in all_tables if '권면' in t.get_text()), None)
                            if first_table is not None:
                                target_value = None
                                for tr in first_table.find_all('tr'):
                                    row_text = tr.get_text(' ', strip=True)
                                    if '사채의 권면(전자등록)총액' in row_text:
                                        value_elem = tr.find(lambda tag: tag.name in ['te', 'td', 'th'] and (
                                            tag.get('acode') == 'DNM_SUM' or tag.get('align', '').upper() == 'RIGHT'))
                                        if value_elem is None:
                                            cells = tr.find_all(['te', 'td', 'th'])
                                            if cells:
                                                value_elem = cells[-1]
                                        if value_elem is not None:
                                            target_value = value_elem.get_text(strip=True)
                                        break
                                if target_value is not None:
                                    try:
                                        amount_krw = float(str(target_value).replace(',', ''))
                                        amount_eok = round(amount_krw / (10**8), 1)
                                        formatted = f"- {corp_name} {report_type} {amount_eok}억 \n https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                                        output_entries.append((rcept_no, formatted))
                                    except ValueError:
                                        pass
                        else:
                            pass
        except zipfile.BadZipFile:
            pass
    
    if output_entries:
        last_rcept_nos = load_last_texts()
        if not isinstance(last_rcept_nos, list):
            last_rcept_nos = []
        new_entries = [(rcp, line) for (rcp, line) in output_entries if rcp not in last_rcept_nos]
        if new_entries:
            info_string = today_string + "\n일일 누적 발행내역입니다.\n\n"
            final_text = info_string + "\n\n".join(line for _, line in new_entries)
            print(final_text)
            send_message(final_text)
            save_last_texts(last_rcept_nos + [rcp for rcp, _ in new_entries])
    return None

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)

if __name__ == "__main__":
    run()
