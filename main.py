import csv
import re
import sys

# 1. 보건복지부 기준 일일 상한선 (Red Card 기준치)
UPPER_LIMITS = {
    "비타민B6(mg)": 100,
    "비타민D(㎍)": 100,
    "아연(mg)": 35,
    "비타민C(mg)": 2000,
    "비타민A(㎍)": 3000,
    "마그네슘(mg)": 350,
    "철분(mg)": 45,
    "칼슘(mg)": 2500
}

class KioskBrain:
    def __init__(self, csv_file_path):
        self.db = self.load_database(csv_file_path)
        self.cart = [] 
        self.current_nutrients = {key: 0.0 for key in UPPER_LIMITS.keys()}
        self.current_nutrients["아미노산(BCAA/단백질)"] = 0 

    def load_database(self, file_path):
        db = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # 방금 올린 파일의 정확한 열 이름 매칭
                key_name = '제품명 (브랜드)'
                content_name = '1회 제공량 기준 함량'
                category_name = '카테고리'
                
                for i, row in enumerate(reader):
                    barcode = str(1000 + i) # 임시 바코드 발급
                    db[barcode] = {
                        "name": row[key_name].strip(),
                        "category": row[category_name].strip(),
                        "raw_contents": row[content_name].strip()
                    }
            print(f"✅ 데이터베이스 로드 완료! (총 {len(db)}개 제품)")
            return db
        except Exception as e:
            print(f"❌ CSV 로드 에러: {e}")
            print("파일 이름이 'supplements_db.csv'가 맞는지 확인해주세요!")
            sys.exit(1)

    def parse_and_accumulate(self, raw_contents, category):
        """텍스트 함량을 분석해서 수치로 변환 후 장바구니에 누적"""
        if "B6" in raw_contents:
            val = re.search(r'B6\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["비타민B6(mg)"] += float(val.group(1))
            
        if "D" in raw_contents and "IU" not in raw_contents.split('D')[0]: 
            val = re.search(r'D\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["비타민D(㎍)"] += float(val.group(1))
            
        if "아연" in raw_contents:
            val = re.search(r'아연\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["아연(mg)"] += float(val.group(1))
            
        if "A" in raw_contents:
            val = re.search(r'A\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["비타민A(㎍)"] += float(val.group(1))

        if "C" in raw_contents:
            val = re.search(r'C\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["비타민C(mg)"] += float(val.group(1))

        if "마그네슘" in raw_contents:
            val = re.search(r'마그네슘\s*([\d\.]+)', raw_contents)
            if val: self.current_nutrients["마그네슘(mg)"] += float(val.group(1))

        if category in ["단백질", "BCAA"]:
            self.current_nutrients["아미노산(BCAA/단백질)"] += 1

    def scan_item(self, barcode):
        if barcode not in self.db:
            return "⚠️ 등록되지 않은 바코드입니다."

        item = self.db[barcode]
        self.cart.append(item['name'])
        self.parse_and_accumulate(item['raw_contents'], item['category'])
        
        return self.check_warnings(item['name'])

    def check_warnings(self, latest_item):
        warnings = []
        for nutrient, limit in UPPER_LIMITS.items():
            current_val = self.current_nutrients[nutrient]
            if current_val > limit:
                warnings.append(f"🚨 [위험] {nutrient} 상한선({limit}) 초과! (현재 누적: {current_val})")
            elif current_val > (limit * 0.7):
                warnings.append(f"🟡 [주의] {nutrient} 누적량이 상한선에 근접했습니다.")

        if self.current_nutrients["아미노산(BCAA/단백질)"] >= 2:
             warnings.append("🚨 [위험] 단백질과 BCAA가 중복되었습니다. 신장 여과에 무리를 줄 수 있습니다.")

        if not warnings:
            return f"✅ [{latest_item}] 스캔 완료. 안전한 조합입니다."
        else:
            warning_msg = "\n".join(warnings)
            return f"❌ [{latest_item}] 스캔 경고!\n{warning_msg}"

    def show_cart(self):
        print("\n🛒 [현재 복용 예정 영양제]")
        print(", ".join(self.cart) if self.cart else "비어 있음")
        print("-" * 40)


if __name__ == "__main__":
    CSV_FILE_NAME = "supplements_db.csv" # 파일 이름이 이거여야 해!
    
    kiosk = KioskBrain(CSV_FILE_NAME)
    
    print("\n[테스트용 바코드 목록]")
    for code, info in list(kiosk.db.items())[:10]:
        print(f"바코드: {code} | 제품명: {info['name']}")
    
    print("\n" + "="*50)
    print("💊 영양제 과다복용 방지 키오스크 시뮬레이터")
    print("바코드를 입력하세요 (종료하려면 'q' 입력)")
    print("="*50)

    while True:
        user_input = input("\n바코드 스캔 (ex: 1000): ").strip()
        
        if user_input.lower() == 'q':
            print("키오스크를 종료합니다.")
            break
            
        result = kiosk.scan_item(user_input)
        print("\n▶ LCD 출력 화면 ◀")
        print(result)
        kiosk.show_cart()