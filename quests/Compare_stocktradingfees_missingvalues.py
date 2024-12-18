

from pymongo import MongoClient
# 네트워크 연결 규칙 : protocol://ip:port/path 
client = MongoClient('mongodb://192.168.0.91:27017/')

db_name = client["DB_TEST"]
col_target_name = db_name["COL_COMPARE_FEE"]

import pandas as pd
import numpy as np

'''
    일단 데이터 보기
    1. 각 증권사 에서 거래금액 별 결측치 있는지
    2. 구분 (변경 전후) 별 결측치 있는지 
    3. 계좌별 결측치 있는지 
'''

data_cursor = col_target_name.find({})
data_list = list(data_cursor)
print(len(data_list))
df_comp_fee = pd.DataFrame(data_list)
df_comp_fee.head()

def convert_amount_to_float(amount_str):
    """거래금액 문자열을 숫자로 변환"""
    amount_str = amount_str.replace(' ', '')  # 공백 제거
    if '억원' in amount_str:
        # 1억원 -> 10000 (만원 단위)
        return float(amount_str.replace('억원', '')) * 10000
    else:
        # X만원 -> X
        return float(amount_str.replace('만원', ''))
    

def fill_missing_smartphone(df, agg_func='mean'):
    """
    스마트폰.1 결측치를 채우는 함수
    
    Parameters:
    df : DataFrame
    agg_func : str, 집계 함수 ('mean', 'median', 'max' 등)
    """
    # 원본 데이터 복사
    df_filled = df.copy()
    
    # 변경후 데이터 중 스마트폰.1이 결측치인 레코드만 처리

    # 2. 같은 회사의 다른 거래금액 값의 비율 평균으로 채우기
    mask_still_missing = (df_filled['구분'] == '변경후') & (df_filled['스마트폰.1'].isna())
    for idx in df_filled[mask_still_missing].index:
        company = df_filled.loc[idx, '회사명']
        current_amount = convert_amount_to_float(df_filled.loc[idx, '거래금액'])
        
        # 같은 회사의 다른 변경후 데이터 추출
        other_records = df_filled[(df_filled['회사명'] == company) & 
                                (df_filled['구분'] == '변경후') & 
                                (df_filled['스마트폰.1'].notna())]
        
        if len(other_records) > 0:
            # 각 거래금액 대비 스마트폰.1 비율 계산
            ratios = []
            amounts = []  # 출력용 거래금액 저장
            for _, row in other_records.iterrows():
                amount = convert_amount_to_float(row['거래금액'])
                ratio = row['스마트폰.1'] / amount
                ratios.append(ratio)
                amounts.append(f"{row['거래금액']}:{ratio:.6f}")
            
            # 비율의 평균 계산
            avg_ratio = sum(ratios) / len(ratios)
            # 현재 거래금액에 평균 비율 적용
            fill_value = current_amount * avg_ratio
            
            print(f"case 2 : {idx}, {df_filled.loc[idx, ['회사명', '거래금액', '구분', '스마트폰', '스마트폰.1']]}")
            # print(f"        거래금액별 비율: {amounts}")
            # print(f"        평균 비율: {avg_ratio:.6f}")
            # print(f"        적용값 ({df_filled.loc[idx, '거래금액']} × {avg_ratio:.6f}): {fill_value:.6f}")
            
            df_filled.loc[idx, '스마트폰.1'] = fill_value
    
    # 3. 같은 레코드의 스마트폰 값으로 채우기
    mask_still_missing = (df_filled['구분'] == '변경후') & (df_filled['스마트폰.1'].isna())
    for idx in df_filled[mask_still_missing].index:
        if not pd.isna(df_filled.loc[idx, '스마트폰']):
            print(f"case 3 : {idx}, {df_filled.loc[idx, ['회사명', '거래금액', '구분', '스마트폰', '스마트폰.1']]}")
            df_filled.loc[idx, '스마트폰.1'] = df_filled.loc[idx, '스마트폰']

    mask_target = (df_filled['구분'] == '변경후') & (df_filled['스마트폰.1'].isna())
    # 1. 같은 회사, 같은 거래금액의 변경전 값과 변경율로 채우기
    for idx in df_filled[mask_target].index:
        company = df_filled.loc[idx, '회사명']
        amount = df_filled.loc[idx, '거래금액']
        
        # 같은 회사, 같은 거래금액의 변경전 값과 변경율 찾기
        prev_value = df_filled[(df_filled['회사명'] == company) & 
                             (df_filled['거래금액'] == amount) & 
                             (df_filled['구분'] == '변경전')]['스마트폰.1'].values
        
        rate = df_filled[(df_filled['회사명'] == company) & 
                        (df_filled['거래금액'] == amount) & 
                        (df_filled['구분'] == '변경율')]['스마트폰.1'].values
        
        # if len(prev_value) > 0 and len(rate) > 0 and not np.isnan(prev_value[0]) and not np.isnan(rate[0]):
        if len(prev_value) > 0 and not np.isnan(prev_value[0]) :
            print(f"case 1 : {idx}, {df_filled.loc[idx, ['회사명', '거래금액', '구분', '스마트폰', '스마트폰.1']]}")
            df_filled.loc[idx, '스마트폰.1'] = prev_value[0] * (1 + rate[0])

    # 남은 결측치 확인
    remaining_missing = df_filled[(df_filled['구분'] == '변경후') & 
                                (df_filled['스마트폰.1'].isna())]
    
    return df_filled, remaining_missing

# 함수 사용
df_filled, remaining_missing = fill_missing_smartphone(df_comp_fee, agg_func='mean')

# 결과 출력
print("=== 채우기 전 변경후 결측치 수 ===")
print(len(df_comp_fee[(df_comp_fee['구분'] == '변경후') & (df_comp_fee['스마트폰.1'].isna())]))

print("\n=== 채운 후 변경후 결측치 수 ===")
print(len(remaining_missing))

print("\n=== 남은 결측치가 있는 레코드 ===")
if len(remaining_missing) > 0:
    print(remaining_missing[['회사명', '거래금액', '구분', '스마트폰', '스마트폰.1']].sort_values(['회사명', '거래금액', '구분']))
else:
    print("남은 결측치가 없습니다.")



total_mean = df_filled["스마트폰.1"].dropna().mean()
total_mean

df_mean = df_filled.dropna(subset=["스마트폰.1"]).groupby(by="회사명")["스마트폰.1"].mean()

df_mean.info()
df_mean

df_mean_value = df_filled.copy()
df_mean_value['avg'] = df_filled['회사명'].map(df_mean)
df_fin = df_mean_value[['회사명','거래금액','스마트폰.1','avg']].sort_values(by=['회사명','거래금액','스마트폰.1','avg'],ascending=[True,True,True,True])
df_fin.head()

df_fin[df_fin['avg'] <= total_mean].to_csv("/apps/study_pandas/datasets/Q_Compare_fee_fillnan.csv")
df_fin[df_fin['avg'] <= total_mean].head()