import tkinter as tk
from tkinter import font
import csv
import re

# --- [1. 데이터 엔진] ---
# 한국인 영양소 섭취기준 기반 상한선 데이터
SAFE_LIMITS = {
    "남성": {
        "비타민B6(mg)": 100, "비타민B12(㎍)": 2000, "비타민C(mg)": 2000, 
        "비타민D(㎍)": 100, "철분(mg)": 45, "칼슘(mg)": 2500, "오메가3(mg)": 3000
    },
    "여성": {
        "비타민B6(mg)": 100, "비타민B12(㎍)": 2000, "비타민C(mg)": 2000, 
        "비타민D(㎍)": 100, "철분(mg)": 45, "칼슘(mg)": 2500, "오메가3(mg)": 3000
    }
}

class KioskBrain:
    def __init__(self, csv_file_path):
        self.db = []
        self.cart = []
        self.gender = "남성"
        # 0.0으로 모든 성분 초기화
        self.current_nutrients = {key: 0.0 for key in SAFE_LIMITS["남성"].keys()}
        self.load_data(csv_file_path)

    def load_data(self, file_path):
        """CSV 파일을 읽어와 데이터베이스에 저장 (에러 방지용 함수명 통일)"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.db.append({
                        "category": row['카테고리'].strip(),
                        "name": row['제품명 (브랜드)'].strip(),
                        "contents": row['1회 제공량 기준 함량'].strip()
                    })
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            # 인코딩 호환성을 위한 예외 처리
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.db.append({
                            "category": row['카테고리'].strip(),
                            "name": row['제품명 (브랜드)'].strip(),
                            "contents": row['1회 제공량 기준 함량'].strip()
                        })
            except:
                print("CSV 파일을 읽을 수 없습니다. 경로와 인코딩을 확인하세요.")

    def add_to_cart(self, item):
        """선택한 제품의 성분을 정규표현식으로 추출하여 합산"""
        self.cart.append(item['name'])
        raw = item['contents'].upper() 
        
        # 성분별 정규표현식 추출 (단위 무관 숫자만 추출)
        patterns = {
            "비타민B6(mg)": r'B6\s*([\d\.]+)',
            "비타민B12(㎍)": r'B12\s*([\d\.]+)',
            "비타민C(mg)": r'(C|VITAMIN\s*C)\s*([\d\.]+)',
            "비타민D(㎍)": r'D\s*([\d\.]+)',
            "철분(mg)": r'(철분|IRON)\s*([\d\.]+)',
            "칼슘(mg)": r'(칼슘|CALCIUM)\s*([\d\.]+)',
            "오메가3(mg)": r'(오메가3|OMEGA3|OMEGA-3)\s*([\d\.]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, raw)
            if match:
                # 정규표현식 그룹 번호 처리 (C나 아연처럼 이름이 두 개인 경우 대비)
                val = match.group(1) if len(match.groups()) == 1 else match.group(2)
                self.current_nutrients[key] += float(val)

    def reset(self):
        self.cart = []
        for key in self.current_nutrients:
            self.current_nutrients[key] = 0.0

# --- [2. UI 메인 앱] ---
class KioskApp:
    def __init__(self, root, brain):
        self.root = root
        self.brain = brain
        self.root.title("영양제 안전 분석 시스템")
        self.root.geometry("1000x850")
        self.root.configure(bg="#1E1E1E")
        
        self.content_container = tk.Frame(self.root, bg="#1E1E1E")
        self.content_container.pack(fill="both", expand=True)
        
        # 하단 장바구니 영역
        self.cart_bar = tk.Frame(self.root, bg="#2D2D2D", height=100)
        self.cart_bar.pack(side="bottom", fill="x")
        self.cart_items_label = tk.Label(self.cart_bar, text="🛒 선택 목록: 비어 있음", 
                                        font=("Helvetica", 13), fg="#00FFCC", bg="#2D2D2D", padx=20)
        self.cart_items_label.pack(pady=25)

        self.show_start_page()

    def clear_frame(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def update_cart_display(self):
        text = " | ".join(self.brain.cart) if self.brain.cart else "비어 있음"
        self.cart_items_label.config(text=f"🛒 선택 목록: {text}")

    def show_start_page(self):
        self.clear_frame()
        self.brain.reset()
        self.update_cart_display()
        tk.Label(self.content_container, text="💊\nSAFE NUTRI-CHECK", font=("Helvetica", 50, "bold"), fg="#00FFCC", bg="#1E1E1E").pack(pady=80)
        tk.Button(self.content_container, text="키오스크 시작", font=("Helvetica", 22, "bold"), 
                  command=self.show_gender_page, bg="#00FFCC", width=15, height=2).pack()

    def show_gender_page(self):
        self.clear_frame()
        tk.Label(self.content_container, text="사용자의 성별을 선택하세요", font=("Helvetica", 30), fg="white", bg="#1E1E1E").pack(pady=80)
        btn_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        btn_frame.pack()
        tk.Button(btn_frame, text="남성 (Male)", font=("Helvetica", 18), width=15, height=2, 
                  command=lambda: self.set_gender("남성")).pack(side="left", padx=20)
        tk.Button(btn_frame, text="여성 (Female)", font=("Helvetica", 18), width=15, height=2, 
                  command=lambda: self.set_gender("여성")).pack(side="left", padx=20)

    def set_gender(self, gender):
        self.brain.gender = gender
        self.show_category_page()

    def show_category_page(self):
        """종합비타민 등 카테고리 선택 화면 (Lambda 버그 수정 완료)"""
        self.clear_frame()
        self.update_cart_display()
        tk.Label(self.content_container, text=f"[{self.brain.gender}] 영양제 종류 선택", 
                 font=("Helvetica", 25), fg="#00FFCC", bg="#1E1E1E").pack(pady=30)
        
        # 카테고리 중복 제거 및 정렬
        categories = sorted(list(set(item['category'] for item in self.brain.db)))
        
        grid_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        grid_frame.pack(pady=10)
        
        for i, cat in enumerate(categories):
            # c=cat 인자 고정을 통해 버튼 클릭 시 올바른 카테고리 전달
            btn = tk.Button(grid_frame, text=cat, font=("Helvetica", 14), width=18, height=2, 
                            command=lambda c=cat: self.show_brand_page(c))
            btn.grid(row=i//3, column=i%3, padx=10, pady=10)
            
        tk.Button(self.content_container, text="🚀 분석 리포트 확인", font=("Helvetica", 18, "bold"), 
                  bg="#FFCC00", fg="black", padx=30, pady=15, command=self.show_result_page).pack(side="bottom", pady=40)

    def show_brand_page(self, category):
        """카테고리에 맞는 제품(브랜드) 목록 출력"""
        self.clear_frame()
        tk.Label(self.content_container, text=f"[{category}] 제품 목록", font=("Helvetica", 22), fg="white", bg="#1E1E1E").pack(pady=30)
        
        products = [item for item in self.brain.db if item['category'] == category]
        
        # 제품 목록 스크롤이 필요할 수 있으므로 프레임 활용
        list_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        list_frame.pack(pady=10)

        for prod in products:
            btn = tk.Button(list_frame, text=prod['name'], font=("Helvetica", 14), width=55, pady=10,
                            command=lambda p=prod: [self.brain.add_to_cart(p), self.update_cart_display(), self.show_category_page()])
            btn.pack(pady=5)
            
        if not products:
            tk.Label(list_frame, text="해당 카테고리에 제품이 없습니다.", fg="gray", bg="#1E1E1E").pack()

        tk.Button(self.content_container, text="🔙 뒤로 가기", command=self.show_category_page).pack(pady=20)

    def show_result_page(self):
        """최종 합산 결과 및 안전성 분석 화면"""
        self.clear_frame()
        tk.Label(self.content_container, text="📊 개인별 영양 성분 분석 결과", font=("Helvetica", 30, "bold"), fg="white", bg="#1E1E1E").pack(pady=40)
        
        res_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        res_frame.pack(pady=10)

        any_danger = False
        limit_data = SAFE_LIMITS[self.brain.gender]

        for nutrient, limit in limit_data.items():
            val = self.brain.current_nutrients[nutrient]
            if val == 0: continue # 선택 안 한 성분은 생략하여 가독성 향상
            
            is_over = val > limit
            color = "#E74C3C" if is_over else "#2ECC71"
            if is_over: any_danger = True
            
            status_text = f"{nutrient}: {val:.1f} / {limit} (상한선)"
            tk.Label(res_frame, text=status_text, font=("Helvetica", 18, "bold"), fg=color, bg="#1E1E1E", pady=8).pack()

        final_msg = "🚨 주의: 일부 성분이 상한 섭취량을 초과했습니다!" if any_danger else "✅ 안전: 모든 성분이 상한선 이내입니다."
        tk.Label(self.content_container, text=final_msg, font=("Helvetica", 22, "bold"), 
                 bg="#E74C3C" if any_danger else "#2ECC71", fg="white", padx=30, pady=20).pack(pady=30)

        tk.Button(self.content_container, text="🔄 처음으로 돌아가기", font=("Helvetica", 15), 
                  command=self.show_start_page, bg="#00FFCC").pack(side="bottom", pady=30)

if __name__ == "__main__":
    root = tk.Tk()
    # 파일명은 실제 사용 중인 CSV 이름과 일치해야 합니다.
    brain = KioskBrain("supplements_db.csv")
    app = KioskApp(root, brain)
    root.mainloop()