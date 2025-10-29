from dotenv import load_dotenv
import os

load_dotenv() # 모든 환경 변수를 한 번에 로드

# FRED API 키 사용
FRED_API_KEY = os.getenv("FRED_API_KEY")

# ECOS API 키 사용
ECOS_API_KEY = os.getenv("ECOS_API_KEY") 

print(f"FRED 키 로드 완료: {FRED_API_KEY is not None}")
print(f"ECOS 키 로드 완료: {ECOS_API_KEY is not None}")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# --- (이 위에는 FRED, ECOS API 키 설정 및 데이터 로드 함수 코드가 필요합니다) ---

# --- 메인 실행 및 데이터 통합 ---

if __name__ == "__main__":
    
    # ... (생략: FRED, ECOS 데이터 로드 및 rates_df 통합 코드) ...
    
    # 3. 최종 통합 DataFrame 확인 및 정리 (기존 코드 유지)
    rates_df = pd.DataFrame() # 실제 코드에서는 여기에 데이터가 로드된다고 가정

    # --- 데이터 로드 가정을 위한 임시 코드 (실제 실행 시 제거) ---
    # 실제로는 위의 get_fred_data와 get_ecos_data 함수가 실행되어 rates_df에 데이터가 채워져야 합니다.
    # 월별(freq='M')로 10년치 데이터 (120개월)를 생성합니다.
    dates = pd.to_datetime(pd.date_range(start='2015-10-01', periods=120, freq='M'))
    rates_df = pd.DataFrame({
        'US_Base_Rate': np.random.uniform(0.5, 5.5, 120).cumsum() * 0.01 + 0.5,
        'KOR_Base_Rate': np.random.uniform(0.5, 5.0, 120).cumsum() * 0.01 + 0.5,
        'US_10Y_Treasury': np.random.uniform(1.0, 6.0, 120).cumsum() * 0.01 + 1.0,
    }, index=dates)
    rates_df = rates_df.fillna(method='ffill')
    # --- 임시 코드 끝 ---


    if not rates_df.empty:
        print("\n" + "="*50 + "\n")
        print("✅ 금리 시계열 분석 및 시각화 시작 (기간: 10년치, 주기: 월별)")
        
        # 4. 분석 지표 계산 (금리 격차)
        rates_df['KOR_US_Spread'] = rates_df['US_Base_Rate'] - rates_df['KOR_Base_Rate']
        
        # 5. 시각화 (Matplotlib)
        
        plt.figure(figsize=(14, 7))
        
        # 한국 기준금리 (KOR_Base_Rate)
        plt.plot(rates_df.index, rates_df['KOR_Base_Rate'], 
                 label='한국 기준금리', color='blue', linewidth=2)
        
        # 미국 기준금리 (US_Base_Rate)
        plt.plot(rates_df.index, rates_df['US_Base_Rate'], 
                 label='미국 기준금리', color='red', linewidth=2)
        
        # 미국 10년물 국채 수익률 (US_10Y_Treasury)
        plt.plot(rates_df.index, rates_df['US_10Y_Treasury'], 
                 label='미국 10년물 국채 수익률', color='green', linewidth=2, linestyle='--')
        
        # 금리 역전 구간 강조
        plt.fill_between(rates_df.index, rates_df['KOR_Base_Rate'], rates_df['US_Base_Rate'], 
                         where=(rates_df['US_Base_Rate'] > rates_df['KOR_Base_Rate']), 
                         color='red', alpha=0.1, label='한미 금리 역전')
        
        # 제목에 '월별' 강조
        plt.title('주요국 금리 추이 비교 (10년치 월별 시계열)', fontsize=16) 
        plt.xlabel('날짜', fontsize=12)
        plt.ylabel('금리 (%)', fontsize=12)
        plt.legend(fontsize=10, loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show() 
        
    else:
        print("❌ 데이터 로드 실패로 시각화를 진행할 수 없습니다.")