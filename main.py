import tkinter as tk
from tkinter import messagebox
import csv
import threading
import time

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("💡 [시스템 알림] pyserial 라이브러리가 감지되지 않아 가상 모드로 전환합니다.")

from kiosk_ui import KioskApp

# 대한민국 식약처 및 의학 기준 영양소 일일 상한 섭취량 (UL)
SAFE_LIMITS = {
    "남성": {
        "베타카로틴(mcg)": 7000.0, "비타민A(mcg)": 3000.0, "비타민C(mg)": 2000.0, 
        "비타민D(mcg)": 100.0, "식물성 비타민D2(mcg)": 10000.0, "동물성 비타민D3(mcg)": 100.0, 
        "비타민E(mgα-TE)": 1000.0, "비타민K(mcg)": 120.0, "비타민B1(mg)": 1.2, 
        "비타민B2(mg)": 1.5, "비타민B3(mg)": 35.0, "비타민B6(mg)": 100.0, 
        "비타민B9(mcg DFE)": 1000.0, "비타민B12(mcg)": 500.0, "비타민B7(mcg)": 30.0, 
        "비타민B5(mg)": 10.0, "콜린(mg)": 595.0, "요오드(mcg)": 1100.0, 
        "철분(mg)": 45.0, "아연(mg)": 40.0, "셀레늄(mcg)": 400.0, 
        "구리(mcg)": 10000.0, "망간(mg)": 11.0, "크롬(mcg)": 35.0, 
        "소듐(mg)": 2300.0, "포타슘(mg)": 3500.0, "인(mg)": 4000.0, 
        "D-감마 토코페롤(mg)": 1000.0, "붕소(mg)": 20.0, "몰리브덴(mcg)": 2000.0, 
        "프로바이오틱스(CFU)": 100000000.0, "칼슘(mg)": 2500.0, "EPA + DHA(mg)": 1000.0, 
        "단백질(g)": 100.0, "루테인(mg)": 20.0, "총지아잔틴(mg)": 2.0, 
        "아스타잔틴(mg)": 12.0, "L-류신(mg)": 10000.0, "L-글루타민(mg)": 20000.0, 
        "L-이소류신(mg)": 10000.0, "L-발린(mg)": 5000.0, "마그네슘(mg)": 350.0   
    },
    "여성": {
        "베타카로틴(mcg)": 7000.0, "비타민A(mcg)": 3000.0, "비타민C(mg)": 2000.0, 
        "비타민D(mcg)": 100.0, "식물성 비타민D2(mcg)": 10000.0, "동물성 비타민D3(mcg)": 1.1, 
        "비타민E(mgα-TE)": 540.0, "비타민K(mcg)": 90.0, "비타민B1(mg)": 5.0, 
        "비타민B2(mg)": 1.2, "비타민B3(mg)": 35.0, "비타민B6(mg)": 100.0, 
        "비타민B9(mcg DFE)": 1000.0, "비타민B12(mcg)": 500.0, "비타민B7(mcg)": 30.0, 
        "비타민B5(mg)": 10.0, "콜린(mg)": 425.0, "요오드(mcg)": 1100.0, 
        "철분(mg)": 45.0, "아연(mg)": 40.0, "셀레늄(mcg)": 400.0, 
        "구리(mcg)": 10000.0, "망간(mg)": 11.0, "크롬(mcg)": 25.0, 
        "소듐(mg)": 2300.0, "포타슘(mg)": 3500.0, "인(mg)": 4000.0, 
        "D-감마 토코페롤(mg)": 1000.0, "붕소(mg)": 20.0, "몰리브덴(mcg)": 2000.0, 
        "프로바이오틱스(CFU)": 100000000.0, "칼슘(mg)": 2500.0, "EPA + DHA(mg)": 500.0, 
        "단백질(g)": 100.0, "루테인(mg)": 20.0, "총지아잔틴(mg)": 2.0, 
        "아스타잔틴(mg)": 12.0, "L-류신(mg)": 10000.0, "L-글루타민(mg)": 20000.0, 
        "L-이소류신(mg)": 10000.0, "L-발린(mg)": 5000.0, "마그네슘(mg)": 350.0   
    }
}

class KioskBrain:
    def __init__(self, csv_file_path):
        self.db = []
        self.cart = []
        self.gender = "남성"
        self.height = 0.0      
        self.weight = 0.0      
        self.bmi = 0.0         
        self.current_nutrients = {}
        self.load_data(csv_file_path)

    def load_data(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # CSV 헤더의 공백 문제를 방지하기 위해 키를 모두 깔끔하게 다듬음
                    clean_row = {str(k).strip(): v for k, v in row.items() if k is not None}

                    # 여러 이름(한/영/띄어쓰기)을 모두 시도해서 값을 가져오는 방어형 함수
                    def get_val(*keys):
                        for k in keys:
                            if k in clean_row:
                                val = clean_row[k]
                                return float(val) if val and str(val).strip() else 0.0
                        return 0.0

                    category_val = clean_row.get('category', clean_row.get('카테고리', '미분류')).strip()
                    name_val = clean_row.get('name', clean_row.get('제품명 (브랜드)', clean_row.get('제품명', '이름없음'))).strip()

                    self.db.append({
                        "category": category_val,
                        "name": name_val,
                        "nutrients": {
                            "베타카로틴(mcg)": get_val('베타카로틴 (mcg)', '베타카로틴(mcg)'),
                            "비타민A(mcg)": get_val('비타민 A (mcg)', '비타민A(mcg)'),
                            "비타민C(mg)": get_val('비타민 C (mg)', '비타민C(mg)'),
                            "비타민D(mcg)": get_val('비타민 D (mcg)', '비타민D(mcg)'),
                            "식물성 비타민D2(mcg)": get_val('식물성 비타민 D2 (mcg)', '식물성 비타민D2(mcg)'),
                            "동물성 비타민D3(mcg)": get_val('동물성 비타민 D3 (mcg)', '동물성 비타민D3(mcg)'),
                            "비타민E(mgα-TE)": get_val('비타민 E (mgα-TE)', '비타민E(mgα-TE)'),
                            "비타민K(mcg)": get_val('비타민 K (mcg)', '비타민K(mcg)'),
                            "비타민B1(mg)": get_val('비타민 B1 (mg)', '비타민B1(mg)'),
                            "비타민B2(mg)": get_val('비타민 B2 (mg)', '비타민B2(mg)'),
                            "비타민B3(mg)": get_val('비타민 B3 (mg)', '비타민B3(mg)'),
                            "비타민B6(mg)": get_val('비타민 B6 (mg)', '비타민B6(mg)'),
                            "비타민B9(mcg DFE)": get_val('비타민 B9 (mcg DFE)', '비타민B9(mcg DFE)'),
                            "비타민B12(mcg)": get_val('비타민 B12 (mcg)', '비타민B12(mcg)'),
                            "비타민B7(mcg)": get_val('비타민 B7 (mcg)', '비타민B7(mcg)'),
                            "비타민B5(mg)": get_val('비타민 B5 (mg)', '비타민B5(mg)'),
                            "콜린(mg)": get_val('콜린 (mg)', '콜린(mg)'),
                            "요오드(mcg)": get_val('요오드 (mcg)', '요오드(mcg)'),
                            "철분(mg)": get_val('철분 (mg)', '철분(mg)'),
                            "아연(mg)": get_val('아연 (mg)', '아연(mg)'),
                            "마그네슘(mg)": get_val('마그네슘 (mg)', '마그네슘(mg)'),
                            "셀레늄(mcg)": get_val('셀레늄 (mcg)', '셀레늄(mcg)'),
                            "구리(mcg)": get_val('구리 (mcg)', '구리(mcg)'),
                            "망간(mg)": get_val('망간 (mg)', '망간(mg)'),
                            "크롬(mcg)": get_val('크롬 (mcg)', '크롬(mcg)'),
                            "소듐(mg)": get_val('소듐 (mg)', '소듐(mg)'),
                            "포타슘(mg)": get_val('포타슘 (mg)', '포타슘(mg)'),
                            "인(mg)": get_val('인 (mg)', '인(mg)'),
                            "D-감마 토코페롤(mg)": get_val('D-감마 토코페롤 (mg)', 'D-감마 토코페롤(mg)'),
                            "붕소(mg)": get_val('붕소 (mg)', '붕소(mg)'),
                            "몰리브덴(mcg)": get_val('몰리브덴 (mcg)', '몰리브덴(mcg)'),
                            "프로바이오틱스(CFU)": get_val('프로바이오틱스 (CFU)', '프로바이오틱스(CFU)'),
                            "칼슘(mg)": get_val('칼슘 (mg)', '칼슘(mg)'),
                            "EPA + DHA(mg)": get_val('EPA + DHA (mg)', 'EPA+DHA(mg)', 'EPA + DHA(mg)'),
                            "단백질(g)": get_val('단백질 (g)', '단백질(g)'),
                            "루테인(mg)": get_val('루테인 (mg)', '루테인(mg)'),
                            "총지아잔틴(mg)": get_val('총지아잔틴 (mg)', '총지아잔틴(mg)'),
                            "아스타잔틴(mg)": get_val('아스타잔틴 (mg)', '아스타잔틴(mg)'),
                            "L-류신(mg)": get_val('L-류신 (mg)', 'L-류신(mg)'),
                            "L-글루타민(mg)": get_val('L-글루타민 (mg)', 'L-글루타민(mg)'),
                            "L-이소류신(mg)": get_val('L-이소류신 (mg)', 'L-이소류신(mg)'),
                            "L-발린(mg)": get_val('L-발린 (mg)', 'L-발린(mg)')
                        }
                    })
            print(f"✅ 데이터베이스 로드 성공! 총 {len(self.db)}개 품목 매핑 완료.")
        except Exception as e:
            print(f"❌ CSV 파일 로드 중 오류 발생: {e}")

    def add_to_cart(self, item):
        self.cart.append(item.get('name', '이름없음'))
        for key in self.current_nutrients:
            self.current_nutrients[key] += item['nutrients'].get(key, 0.0)

    def set_profile(self, gender, height, weight):
        self.gender = gender
        self.height = height
        self.weight = weight
        height_m = height / 100.0
        if height_m > 0:
            self.bmi = round(weight / (height_m ** 2), 1)
        else:
            self.bmi = 0.0
            
        max_protein = round(weight * 2.0, 1)
        SAFE_LIMITS["남성"]["단백질(g)"] = max_protein
        SAFE_LIMITS["여성"]["단백질(g)"] = max_protein
        print(f"⚙️ 단백질 상한선 동적 설정 완료: 체중 {weight}kg -> 일일 최대 {max_protein}g")
        
        self.reset()

    def reset(self):
        self.cart = []
        self.current_nutrients = {key: 0.0 for key in SAFE_LIMITS[self.gender].keys()}


class KioskGuideFlow:
    def __init__(self, root, brain, on_complete_callback):
        self.root = root
        self.brain = brain
        self.on_complete = on_complete_callback
        
        self.gender = "남성"
        self.height_str = ""
        self.weight_str = ""
        
        self.frame = tk.Frame(root, bg="#000000")
        self.frame.pack(fill="both", expand=True)
        
        self.show_privacy_screen()

    def show_privacy_screen(self):
        self.clear_frame()
        
        center_container = tk.Frame(self.frame, bg="#000000")
        center_container.pack(expand=True)
        
        title = tk.Label(center_container, text="📋 개인정보 수집 · 이용 동의", font=("Noto Sans KR", 16, "bold"), fg="#DEFF9A", bg="#000000")
        title.pack(pady=(15, 10))
        
        text_frame = tk.Frame(center_container, bg="#151515", bd=1, relief="solid")
        text_frame.pack(pady=10, padx=30, fill="both", expand=True)
        
        privacy_text = (
            "▶ 수집·이용 목적\n"
            "   키오스크 기반 맞춤형 영양소 추천 서비스 제공\n\n"
            "▶ 수집하는 항목\n"
            "   성별, 키, 몸무게\n\n"
            "▶ 보유 및 이용 기간\n"
            "   키오스크 이용일로부터 1년 보관 후 파기\n\n"
            "▶ 동의 거부 권리 및 불이익\n"
            "   귀하는 동의를 거부할 권리가 있으나, 거부 시\n"
            "   맞춤형 영양소 추천 서비스 이용이 제한됩니다."
        )
        
        text_label = tk.Label(text_frame, text=privacy_text, font=("Noto Sans KR", 12), fg="#FFFFFF", bg="#151515", justify="left", anchor="w", padx=20, pady=20)
        text_label.pack(fill="both", expand=True)
        
        btn_frame = tk.Frame(center_container, bg="#000000")
        btn_frame.pack(pady=15)
        
        reject_btn = tk.Label(btn_frame, text="동의 안함", font=("Noto Sans KR", 12, "bold"), width=12, height=1, bg="#3A3A3C", fg="#FFFFFF", relief="raised", bd=1)
        reject_btn.bind("<Button-1>", lambda e: self.reject_privacy())
        reject_btn.pack(side="left", padx=20)
        
        agree_btn = tk.Label(btn_frame, text="동의함", font=("Noto Sans KR", 12, "bold"), width=12, height=1, bg="#DAFFDE", fg="#000000", relief="raised", bd=1)
        agree_btn.bind("<Button-1>", lambda e: self.show_gender_screen())
        agree_btn.pack(side="left", padx=20)

    def reject_privacy(self):
        messagebox.showwarning("서비스 제한 안내", "개인정보 수집에 동의하셔야만\n맞춤형 영양소 추천 서비스를 이용하실 수 있습니다.")
        self.show_privacy_screen()

    def show_gender_screen(self):
        self.clear_frame()
        self.current_step = "GENDER"
        
        title = tk.Label(self.frame, text="성별을 선택해 주세요", font=("Noto Sans KR", 22, "bold"), fg="#FFFFFF", bg="#000000")
        title.pack(expand=True, pady=(30, 0))
        
        btn_frame = tk.Frame(self.frame, bg="#000000")
        btn_frame.pack(expand=True, pady=(0, 30))
        
        male_btn = tk.Label(btn_frame, text="👨 남성 (Male)", font=("Noto Sans KR", 16, "bold"), width=15, height=2, bg="#DAFFDE", fg="#000000", relief="raised", bd=1)
        male_btn.bind("<Button-1>", lambda e: self.select_gender("남성"))
        male_btn.pack(side="left", padx=25)
        
        female_btn = tk.Label(btn_frame, text="👩 여성 (Female)", font=("Noto Sans KR", 16, "bold"), width=15, height=2, bg="#DAFFDE", fg="#000000", relief="raised", bd=1)
        female_btn.bind("<Button-1>", lambda e: self.select_gender("여성"))
        female_btn.pack(side="left", padx=25)

    def select_gender(self, gender):
        self.gender = gender
        self.show_number_pad_screen("HEIGHT")

    def show_number_pad_screen(self, step):
        self.clear_frame()
        self.current_step = step
        
        if step == "HEIGHT":
            msg, unit, current_val = "본인의 신장(키)을 입력하세요", " cm", self.height_str
        else:
            msg, unit, current_val = "본인의 체중(몸무게)을 입력하세요", " kg", self.weight_str

        center_container = tk.Frame(self.frame, bg="#000000")
        center_container.pack(expand=True)

        top_frame = tk.Frame(center_container, bg="#000000")
        top_frame.pack(pady=10)

        title = tk.Label(top_frame, text=msg, font=("Noto Sans KR", 16, "bold"), fg="#FFFFFF", bg="#000000")
        title.pack(side="left", padx=15)
        
        display_text = current_val + unit if current_val else "0" + unit
        self.display_label = tk.Label(top_frame, text=display_text, font=("Helvetica", 20, "bold"), fg="#DEFF9A", bg="#151515", width=12, bd=1, relief="solid")
        self.display_label.pack(side="left", padx=15)
        
        pad_frame = tk.Frame(center_container, bg="#000000")
        pad_frame.pack(pady=10)
        
        buttons = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0', '⌫']
        row, col = 0, 0
        
        for btn_txt in buttons:
            cmd = lambda x=btn_txt: self.press_key(x)
            btn = tk.Label(pad_frame, text=btn_txt, font=("Helvetica", 14, "bold"), width=6, height=1, bg="#DAFFDE", fg="#000000", relief="raised", bd=1)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.grid(row=row, column=col, padx=8, pady=6)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        action_frame = tk.Frame(center_container, bg="#000000")
        action_frame.pack(pady=10)
        
        prev_label = tk.Label(action_frame, text="◀ 이전", font=("Noto Sans KR", 12, "bold"), width=10, height=1, bg="#3A3A3C", fg="#FFFFFF", relief="raised", bd=1)
        prev_label.bind("<Button-1>", lambda e: self.go_back())
        prev_label.pack(side="left", padx=15)
        
        next_text = "선택 완료 ▶" if step == "WEIGHT" else "다음 ▶"
        next_label = tk.Label(action_frame, text=next_text, font=("Noto Sans KR", 12, "bold"), width=12, height=1, bg="#DEFF9A", fg="#000000", relief="raised", bd=1)
        next_label.bind("<Button-1>", lambda e: self.go_next())
        next_label.pack(side="left", padx=15)

    def press_key(self, key):
        if self.current_step == "HEIGHT":
            val = self.height_str
        else:
            val = self.weight_str
            
        if key == '⌫':
            val = val[:-1]
        elif key == '.':
            if '.' not in val and len(val) > 0:
                val += '.'
        else:
            if len(val) < 5:
                val += key
                
        if self.current_step == "HEIGHT":
            self.height_str = val
            unit = " cm"
        else:
            self.weight_str = val
            unit = " kg"
            
        self.display_label.config(text=val + unit if val else "0" + unit)

    def go_back(self):
        if self.current_step == "HEIGHT":
            self.show_gender_screen()
        elif self.current_step == "WEIGHT":
            self.show_number_pad_screen("HEIGHT")

    def go_next(self):
        try:
            if self.current_step == "HEIGHT":
                h = float(self.height_str)
                if not (100 <= h <= 250):
                    raise ValueError
                self.show_number_pad_screen("WEIGHT")
                
            elif self.current_step == "WEIGHT":
                h = float(self.height_str)
                w = float(self.weight_str)
                if not (20 <= w <= 250):
                    raise ValueError
                
                self.brain.set_profile(self.gender, h, w)
                
                self.frame.destroy()
                self.on_complete()
                
        except ValueError:
            messagebox.showerror("입력값 검증 요망", "올바른 신체 스펙 숫자를 입력해 주세요.\n(예: 키 100~250cm, 몸무게 20~250kg 내외)")

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()


def listen_to_arduino(app_instance):
    if not SERIAL_AVAILABLE:
        return

    arduino_port = '/dev/cu.usbmodem31301' 
    
    while True:
        try:
            print(f"🔌 아두이노 포트 연결 시도 중... ({arduino_port})")
            ser = serial.Serial(arduino_port, 115200, timeout=1)
            time.sleep(2)  
            print("⚙️ 아두이노 브릿지 통신 라인 연결 성공!")
            
            while True:
                if ser.in_waiting > 0:
                    scanned_data = ser.readline().decode('utf-8-sig').strip()
                    if scanned_data and scanned_data != "SYSTEM_READY":
                        print(f"📷 스캔 데이터 수신: {scanned_data}")
                        
                        matched_item = None
                        for item in app_instance.brain.db:
                            if scanned_data.lower() in item['name'].lower():
                                matched_item = item
                                break
                        
                        if matched_item:
                            app_instance.root.after(0, lambda target=matched_item: app_instance.handle_product_selection(target))
                time.sleep(0.1)  
                
        except (serial.SerialException, OSError) as e:
            print(f"⚠️ 아두이노 통신 오류 발생 또는 연결 끊김: {e}")
            print("🔄 3초 후에 재연결을 시도합니다...")
            time.sleep(3)


def start_main_kiosk_system():
    app = KioskApp(root, brain, SAFE_LIMITS)
    
    serial_thread = threading.Thread(target=listen_to_arduino, args=(app,), daemon=True)
    serial_thread.start()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("개인 맞춤형 헬스케어 영양제 키오스크")
    
    root.geometry("800x450") 
    root.resizable(False, False) 
    root.configure(bg="#000000") 
    
    brain = KioskBrain('supplements_db.csv')
    guide_flow = KioskGuideFlow(root, brain, start_main_kiosk_system)
    
    root.mainloop()