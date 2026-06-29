import tkinter as tk
import csv

class KioskApp:
    def __init__(self, root, brain, safe_limits=None):
        self.root = root
        self.brain = brain
        self.safe_limits = safe_limits 
        self.root.title("영양제 안전 분석 시스템")
        
        # 💡 라즈베리파이 터치 LCD 규격 (800x450) 최적화 세팅
        self.root.geometry("800x450") 
        self.root.configure(bg="#1E1E1E")
        
        self.content_container = tk.Frame(self.root, bg="#1E1E1E")
        self.content_container.pack(fill="both", expand=True)
        
        self.cart_bar = tk.Frame(self.root, bg="#2D2D2D", height=50)
        self.cart_bar.pack(side="bottom", fill="x")
        self.cart_items_label = tk.Label(self.cart_bar, text="🛒 선택 목록: 비어 있음", 
                                        font=("Helvetica", 11), fg="#00FFCC", bg="#2D2D2D", padx=10)
        self.cart_items_label.pack(pady=12)

        # 최초 실행 시 main.py 가이드 플로우에서 입력받은 성별, 신체스펙 정보를 유지하며 카테고리로 진입
        self.show_category_page()

    def clear_frame(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def update_cart_display(self):
        text = " | ".join(self.brain.cart) if self.brain.cart else "비어 있음"
        if len(text) > 45:
            text = text[:42] + "..."
        self.cart_items_label.config(text=f"🛒 선택 목록: {text}")

    def enable_touch_scroll(self, canvas):
        """ 터치스크린 환경에서 마우스나 손가락으로 쓸어 넘겨 스크롤(Drag to Scroll)하는 기능 바인딩 """
        canvas.bind("<ButtonPress-1>", lambda event: canvas.scan_mark(event.x, event.y))
        canvas.bind("<B1-Motion>", lambda event: canvas.scan_dragto(event.x, event.y, gain=1, drag_x=False, drag_y=True))

    def show_start_page(self):
        self.clear_frame()
        # 성별 및 신체정보 유지를 위해 장바구니 리스트와 실시간 영양소 누적값만 선택 초기화
        self.brain.cart = []
        if self.safe_limits and self.brain.gender in self.safe_limits:
            self.brain.current_nutrients = {key: 0.0 for key in self.safe_limits[self.brain.gender].keys()}
        else:
            self.brain.current_nutrients = {}
        self.update_cart_display()
        
        tk.Label(self.content_container, text="💊\nSAFE NUTRI-CHECK", 
                 font=("Helvetica", 28, "bold"), fg="#00FFCC", bg="#1E1E1E").pack(pady=30)
        
        tk.Button(self.content_container, text="키오스크 시작", font=("Helvetica", 16, "bold"), 
                  command=self.show_category_page, bg="#00FFCC", fg="black", width=12, height=1).pack(pady=10)

    def show_gender_page(self):
        self.clear_frame()
        tk.Label(self.content_container, text="사용자의 성별을 선택하세요", 
                 font=("Helvetica", 18), fg="white", bg="#1E1E1E").pack(pady=30)
        
        btn_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="남성 (Male)", font=("Helvetica", 14), width=12, height=1, 
                  command=lambda: self.set_gender("남성")).pack(side="left", padx=15)
        tk.Button(btn_frame, text="여성 (Female)", font=("Helvetica", 14), width=12, height=1, 
                  command=lambda: self.set_gender("여성")).pack(side="left", padx=15)

    def set_gender(self, gender):
        self.brain.gender = gender
        if hasattr(self.brain, 'reset'):
            self.brain.reset()
        self.show_category_page()

    def show_category_page(self):
        self.clear_frame()
        self.update_cart_display()
        
        # 현재 로그인된 유저의 성별이 제대로 매핑되어 노출되는 실시간 타이틀바
        tk.Label(self.content_container, text=f"[성인 {self.brain.gender}] 영양제 종류 선택", 
                 font=("Helvetica", 16, "bold"), fg="#00FFCC", bg="#1E1E1E").pack(pady=15)
        
        categories = sorted(list(set(item.get('category', '미분류') for item in self.brain.db)))
        grid_frame = tk.Frame(self.content_container, bg="#1E1E1E")
        grid_frame.pack(pady=5)
        
        for i, cat in enumerate(categories):
            btn = tk.Button(grid_frame, text=cat, font=("Helvetica", 11), width=14, height=1, 
                            command=lambda c=cat: self.show_brand_page(c))
            btn.grid(row=i//4, column=i%4, padx=6, pady=6)
            
        tk.Button(self.content_container, text="🚀 최종 분석 결과 확인", font=("Helvetica", 14, "bold"), 
                  bg="#FFCC00", fg="black", padx=20, pady=8, command=self.show_result_page).pack(side="bottom", pady=15)

    def show_brand_page(self, category):
        self.clear_frame()
        tk.Label(self.content_container, text=f"[{category}] 제품 목록", font=("Helvetica", 16), fg="white", bg="#1E1E1E").pack(pady=15)
        
        # 💡 800x450 화면 규격 비율에 딱 맞춘 스크롤 캔버스 높이 (220)
        scroll_canvas = tk.Canvas(self.content_container, bg="#1E1E1E", highlightthickness=0, height=220)
        scrollbar = tk.Scrollbar(self.content_container, orient="vertical", command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg="#1E1E1E")
        
        scroll_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        # 터치 스크롤 드래그 액션 활성화
        self.enable_touch_scroll(scroll_canvas)

        products = [item for item in self.brain.db if item.get('category') == category]
        for prod in products:
            prod_name = prod.get('name', '알 수 없는 상품')
            btn = tk.Button(scroll_frame, text=prod_name, font=("Helvetica", 11), width=65, pady=6,
                            command=lambda p=prod: self.handle_product_selection(p))
            btn.pack(pady=3)

        tk.Button(self.content_container, text="🔙 뒤로 가기", font=("Helvetica", 11), command=self.show_category_page).pack(side="bottom", pady=10)

    def handle_product_selection(self, product):
        self.brain.add_to_cart(product)
        self.update_cart_display()
        self.show_category_page()

    def show_result_page(self):
        self.clear_frame()
        tk.Label(self.content_container, text="📊 개인별 영양 성분 분석 결과", font=("Helvetica", 18, "bold"), fg="white", bg="#1E1E1E").pack(pady=15)
        
        # 💡 800x450 화면 규격 비율에 딱 맞춘 결과창 스크롤 캔버스 높이 (200)
        scroll_canvas = tk.Canvas(self.content_container, bg="#1E1E1E", highlightthickness=0, height=200)
        scrollbar = tk.Scrollbar(self.content_container, orient="vertical", command=scroll_canvas.yview)
        res_frame = tk.Frame(scroll_canvas, bg="#1E1E1E")
        
        res_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=res_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(fill="both", expand=True, padx=40)
        scrollbar.pack(side="right", fill="y")

        # 터치 스크롤 드래그 액션 활성화
        self.enable_touch_scroll(scroll_canvas)

        any_danger = False
        limit_data = self.safe_limits.get(self.brain.gender, {}) if self.safe_limits else {}

        for nutrient, limit in limit_data.items():
            val = self.brain.current_nutrients.get(nutrient, 0.0)
            if val == 0: continue 
            
            is_over = val > limit
            
            if is_over:
                any_danger = True
                status_text = f"❌ {nutrient}: {val:.1f} / {limit} (상한선 초과!)"
                tk.Label(res_frame, text=status_text, font=("Helvetica", 13, "bold"), fg="#E74C3C", bg="#1E1E1E", pady=4).pack(anchor="w")

        if not any_danger:
            tk.Label(res_frame, text="✨ 모든 영양 성분이 안전 기준치 이내입니다.", font=("Helvetica", 13), fg="#2ECC71", bg="#1E1E1E", pady=20).pack(anchor="w")

        adult_gender_text = f"성인 {self.brain.gender}"
        final_msg = f"🚨 주의: 일부 성분이 {adult_gender_text} 기준 상한량 초과!" if any_danger else f"✅ 안전: {adult_gender_text} 상한선 이내 복용 가능"
        
        tk.Label(self.content_container, text=final_msg, font=("Helvetica", 14, "bold"), 
                 bg="#E74C3C" if any_danger else "#2ECC71", fg="white", padx=20, pady=8).pack(pady=10)

        tk.Button(self.content_container, text="🔄 처음으로 돌아가기", font=("Helvetica", 12), 
                  command=self.show_start_page, bg="#00FFCC", fg="black").pack(side="bottom", pady=10)