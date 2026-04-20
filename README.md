# ⚡️🚘 서울시 전기차 충전 인프라 분석 대시보드
> **서울시 구별 전기차 등록 현황 대비 충전소 보급률 및 충전 요금 정보 시각화 서비스**
---
## 👬 팀소개
| **강성준** | **김범중** | **남태식** | **이승민** | **정민규** |

**📆개발기간** : 2026.04.13 - 2026.04.16

***

## 📝 프로젝트 개요
급증하는 전기차 수요에 비해 지역별 충전 인프라의 불균형 문제를 해결하고자, 공공데이터를 기반으로 구역별 충전 환경을 분석하고 시각화하는 Streamlit 웹 서비스를 개발했습니다.

### 🌟 주요 기능
1. **서울시 전체 충전소 현황**
    * 서울 전역에 위치한 전기차 충전소 위치를 클러스터링 마커로 시각화

2. **구역별 인프라 부족 지수**
    * 구별 전기차 등록 수 / 구별 충전소 수를 계산하여 부족 지수 산출
    * 단계 구분도를 통해 인프라 확충이 시급한 구역을 직관적으로 표시

3. **💲구역별 충전 요금 비교**
    * 서울시 내 자치구별 평균 충전 요금을 비교하여 인프라의 성격과 구독의 경제성을 판단하는 기준을 제공

*** 

## ERD 

<img width="1150" height="472" alt="Image" src="https://github.com/user-attachments/assets/7a4ef343-bebf-495c-9f9f-9b82b09cfb25" />

***

## 🛠️ 기술 스택
**1. 언어 및 프레임워크**
* python(3.13.5) : 전체 로직 구현 및 데이터 처리
* Streamlit : 인터페이스 구축

**2. 데이터 분석 및 처리**
* Pandas : CSV 데이터 핸들링
* GeoPandas : 행정동 경계(GeoJSON) 데이터 처리
* MySQL : 초기 데이터 저장 및 쿼리 수행 (배포 시에는 CSV 활용)

***

## 📁 프로젝트 구조 (Tree)

```bash
🚘 project_1/
├── README.md
├── data
│   ├── processed                                   # 전처리 완료 데이터
│   │   ├── FAQ_final3.json                         
│   │   ├── README.md
│   │   ├── charging_station_list.csv
│   │   ├── gu_master.csv
│   │   ├── hangjeongdong_서울특별시.geojson
│   │   ├── seoul_car_status.csv
│   │   ├── seoul_car_sum.csv
│   │   └── seoul_charge_final.csv
│   ├── raw_data                                    # 원본 데이터
│   │   ├── charge_fee                              # 충전소 요금 데이터
│   │   │   └── charge_fee.csv
│   │   ├── charger                                 # 충전소 위치 데이터
│   │   │   └── charging_station_list_raw.csv
│   │   ├── ev_car                                  # 차량 등록 데이터
│   │   │   └── seoul_car_status_raw.csv
│   │   ├── faq                                     # 기업별 수집된 FAQ 원본 (Tesla, Kia 등)
│   │   │   ├── FAQ_0_일반_sorted.csv
│   │   │   ├── FAQ_1_kia_ev_final.csv
│   │   │   ├── FAQ_3_tesla_sorted.csv
│   │   │   ├── FAQ_4_ev_faq_final.csv
│   │   │   └── FAQ_5_mugonghae.csv
│   │   ├── map                                     # 지도 데이터
│   │   │   ├── hangjeongdong_서울특별시_raw.geojson
│   │   │   └── 서울_자치구_경계_2017.geojson
│   │   └── seoul_EV.ipynb                          # 충전소 데이터 정제용 코드
│   └── webcrawling                                 # 웹크롤링 데이터
│       ├── proproject_evb.ipynb
│       ├── proproject_kia.ipynb
│       ├── proproject_mugonghae.ipynb
│       ├── proproject_pse.py
│       └── proproject_tesla.py
├── ERD.png
├── pyproject.toml
├── appCSV.py                                       # Streamlit 메인 실행 파일
└── 데이터베이스 설계 문서 (Database Design Specification).pdf    
```

***

## 🌆 시각화 미리 보기기
1. 홈 화면

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/36a0b02f-1b32-4f4c-a4eb-cce01d810373" />

2. 서울시 충전소 현황

<img width="1512" height="901" alt="Image" src="https://github.com/user-attachments/assets/ecd5cc25-d582-4002-9c6d-6d7e658a8260" />

<img width="1512" height="901" alt="Image" src="https://github.com/user-attachments/assets/5fc0a311-354e-4fe9-823f-ce4112fdcad1" />

3. 구역별 인프라 부족 정도

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/08f50ea9-830d-4b92-a7bb-ce2c9e196ca3" />

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/d5b38eba-d4f8-48d1-86ae-7a279740d5f3" />

4. 요금/전기차 지도

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/16797dd3-6c32-4bf6-a5ca-595c2deddf5c" />

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/f76be543-3bda-40ab-a048-9b6a8ee73ea4" />

5. 전기차 충전 관련 FAQ 조회

<img width="1512" height="863" alt="Image" src="https://github.com/user-attachments/assets/2bc68234-99bb-4150-b463-001f3bc4fed4" />

***

## 💡 분석 인사이트 (Key Insights)

1. 충전 인프라의 역설: 강남구의 인프라 부족 현상 🔍

* 현상: 강남구는 서울시 내에서 절대적인 충전기 대수가 가장 많으나, 동시에   전기차 등록 대수 또한 압도적으로 많습니다. (강남시 부족 지수 : 2.76, 서울시 평균보다 73% 높음)

* 발견: 단순 개수가 아닌 '차량 대비 보급률'로 계산한 인프라 부족 지수를 산출한 결과, 강남구의 충전 인프라 확충이 오히려 타 구역보다 시급한 것으로 나타났습니다.

* 결론: 인프라 구축 시 절대적인 수치보다 지역별 수요(등록 대수)를 고려한 상대적 보급 정책이 필요함을 시사합니다.

2. 지역별 충전 요금의 불균형 발견 💲

* 현상: 이론적으로 전기요금 체계는 지역별로 동일해야 하지만, 실제 데이터 분석 결과 자치구별 평균 충전 회원가에서 유의미한 차이가 발견되었습니다.

* 발견: 특정 구역(예: 업무 밀집 지역 등)의 충전소 운영 업체 비중이나 급속/완속 충전기 비율에 따라 사용자가 실제로 체감하는 비용 편차가 존재합니다.

* 결론: 전기차 이용자는 거주지뿐만 아니라 활동 반경 내의 구역별 요금 정보를 확인함으로써 경제적인 충전 전략을 세울 수 있습니다.

***

## 📊 데이터 출처
* 서울 열린데이터 광장 (서울시 전기차 등록 현황 2026.03월 데이터)
* 차지 인포 (서울시 충전소(기) 현황 2026.03.13 데이터)
