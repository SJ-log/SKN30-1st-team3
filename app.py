import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
import json
from sqlalchemy import create_engine
from streamlit_folium import st_folium

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="서울시 전기차 충전 인프라",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 스타일 정의
# ============================================
st.markdown("""
<style>
    /* 구글 폰트 가져오기 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .main { background-color: #0f1117; }

    /* 사이드바 배경은 남색, 글씨는 밝은 회색으로 통일*/
    section[data-testid="stSidebar"] {
        background-color: #1a1d27;              
        border-right: 1px solid #2e3147;        
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;              
    }

    /* 메뉴 버튼 */
    .menu-btn {
        display: block;
        width: 100%;
        padding: 12px 16px;
        margin-bottom: 8px;
        background: transparent;
        border: 1px solid #2e3147;
        border-radius: 10px;
        color: #aab0c6;
        font-size: 14px;
        font-family: 'Noto Sans KR', sans-serif;
        cursor: pointer;
        text-align: left;
        transition: all 0.2s;
    }
    .menu-btn:hover { background: #2e3147; color: #fff; }
    .menu-btn.active {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border-color: #3b82f6;
        color: #fff !important;
        font-weight: 500;
    }

    /* 메트릭 카드 */
    .metric-card {
        background: #1a1d27;
        border: 1px solid #2e3147;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #3b82f6;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 12px;
        color: #6b7280;
        margin-top: 4px;
    }

    /* 타이틀 */
    .page-title {
        font-size: 22px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 4px;
    }
    
    .page-subtitle {
        font-size: 13px;
        color: #6b7280;
        margin-bottom: 20px;
    }

    /* 범례 */
    .legend-bar {
        height: 12px;
        border-radius: 6px;
        background: linear-gradient(to right, #ffffb2, #fecc5c, #fd8d3c, #f03b20, #bd0026);
        margin: 6px 0;
    }

    div[data-testid="stHorizontalBlock"] { gap: 12px; }
    div[data-testid="column"] { padding: 0; }
    .block-container { padding: 1.5rem 2rem; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DB 연결
# ============================================
@st.cache_resource
def get_engine():
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'k020912*',   # 개인의 것으로 변경하세요.
        'database': 'seoul_ev',
        'charset': 'utf8mb4'
    }
    return create_engine(
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )

# ============================================
# 데이터 로드
# ============================================

# 충전소 정보
@st.cache_data          
def load_station_data():
    engine = get_engine()
    return pd.read_sql("""
        SELECT c.id, c.충전소, c.충전기타입, c.주소, c.운영기관, c.lat, c.lng, g.gu_name
        FROM charging_station_list c
        JOIN gu_master g ON c.gu_code = g.gu_code
        WHERE c.lat IS NOT NULL AND c.lng IS NOT NULL
    """, engine)

@st.cache_data
def load_shortage_data():
    engine = get_engine()

    # 구별 전기차 수
    df_ev = pd.read_sql("""
        SELECT g.gu_code, g.gu_name, SUM(s.계) AS 전기차수
        FROM seoul_car_status s
        JOIN gu_master g ON s.gu_code = g.gu_code
        WHERE s.연료명 = '전기'
        GROUP BY g.gu_code, g.gu_name
    """, engine)

    # 구별 충전소 수
    df_st = pd.read_sql("""
        SELECT g.gu_code, COUNT(c.id) AS 충전소수
        FROM charging_station_list c
        JOIN gu_master g ON c.gu_code = g.gu_code
        GROUP BY g.gu_code
    """, engine)

    # 부족 지수 계산
    df = pd.merge(df_ev, df_st, on='gu_code', how='left')
    df['충전소수'] = df['충전소수'].fillna(0)
    df['부족지수'] = df.apply(
        lambda r: round(r['전기차수'] / r['충전소수'], 2) if r['충전소수'] > 0 else 9999,
        axis=1
    )
    return df

# 서울특별시 지도를 구로 나누기
@st.cache_data
def load_geojson():
    gdf = gpd.read_file('hangjeongdong_서울특별시.geojson')
    gdf['sgg'] = gdf['sgg'].astype(int)
    gdf_gu = gdf.dissolve(by='sgg').reset_index()[['sgg', 'sggnm', 'geometry']]
    gdf_gu.columns = ['gu_code', 'gu_name', 'geometry']
    return gdf_gu

# ============================================
# 사이드바
# ============================================
with st.sidebar:
    st.markdown("### 서울시 전기차\n### 충전 인프라")
    st.markdown("<hr style='border-color:#2e3147;margin:12px 0'>", unsafe_allow_html=True)

    if 'page' not in st.session_state:
        st.session_state.page = 'stations'

    if st.button("🗺️  전체 충전소 현황",
                 use_container_width=True,
                 type="primary" if st.session_state.page == 'stations' else "secondary"):
        st.session_state.page = 'stations'
        st.rerun()

    if st.button("📊  구역별 인프라 부족 정도",
                 use_container_width=True,
                 type="primary" if st.session_state.page == 'shortage' else "secondary"):
        st.session_state.page = 'shortage'
        st.rerun()
        
    if st.button("💲 구역별 충전 요금",
                 use_container_width=True,
                 type="primary" if st.session_state.page == ):
            
        


    st.markdown("<hr style='border-color:#2e3147;margin:12px 0'>", unsafe_allow_html=True)

    # 구 필터 (전체 충전소 화면에서만)
    if st.session_state.page == 'stations':
        st.markdown("**🔍 구 필터**")
        df_s = load_station_data()
        gu_list = ['전체'] + sorted(df_s['gu_name'].dropna().unique().tolist())
        selected_gu = st.selectbox("구 선택", gu_list, label_visibility="collapsed")
    else:
        selected_gu = '전체'

# ============================================
# 페이지 1 : 전체 충전소 현황
# ============================================
SEOUL_CENTER = [37.5665, 126.9780]

if st.session_state.page == 'stations':
    df_station = load_station_data()

    if selected_gu != '전체':
        df_station = df_station[df_station['gu_name'] == selected_gu]

    # 상단 메트릭
    st.markdown('<p class="page-title">🗺️ 서울시 전체 충전소 현황</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">서울시 전기차 충전소 위치 및 현황</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_station):,}</div>
            <div class="metric-label">총 충전소 수</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{df_station['gu_name'].nunique()}</div>
            <div class="metric-label">구역 수</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{df_station['충전기타입'].nunique()}</div>
            <div class="metric-label">충전기 타입 수</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 지도
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11, tiles='CartoDB dark_matter')

    # 충전소 마커 (클러스터링)
    from folium.plugins import MarkerCluster
    cluster = MarkerCluster().add_to(m)

    for _, row in df_station.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=4,
            color='#3b82f6',
            fill=True,
            fill_color='#60a5fa',
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['충전소']}</b><br>{row['주소']}<br>타입: {row['충전기타입']}<br>운영: {row['운영기관']}",
                max_width=250
            ),
            tooltip=row['충전소']
        ).add_to(cluster)

    st_folium(m, width='100%', height=580, returned_objects=[])

# ============================================
# 페이지 2 : 구역별 인프라 부족 정도
# ============================================
elif st.session_state.page == 'shortage':
    df_shortage = load_shortage_data()
    gdf_gu = load_geojson()

    gdf_merged = gdf_gu.merge(
        df_shortage.drop(columns=['gu_name']),
        on='gu_code', how='left'
    )
    gu_geojson = json.loads(gdf_merged.to_json())

    st.markdown('<p class="page-title">📊 구역별 충전 인프라 부족 정도</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">전기차 수 대비 충전소 수 비율 — 빨간색일수록 충전소가 부족한 구역</p>', unsafe_allow_html=True)

    # 상단 메트릭
    top3 = df_shortage.nlargest(3, '부족지수')
    col1, col2, col3 = st.columns(3)
    for col, (_, row) in zip([col1, col2, col3], top3.iterrows()):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color:#ef4444">{row['gu_name']}</div>
                <div class="metric-label">부족지수 {row['부족지수']:,.0f} (전기차 {row['전기차수']:,}대 / 충전소 {row['충전소수']:,}개)</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 지도
    m = folium.Map(location=SEOUL_CENTER, zoom_start=11, tiles='CartoDB positron')

    folium.Choropleth(
        geo_data=gu_geojson,
        data=df_shortage,
        columns=['gu_code', '부족지수'],
        key_on='feature.properties.gu_code',
        fill_color='YlOrRd',
        fill_opacity=0.75,
        line_opacity=0.6,
        line_color='white',
        legend_name='충전소 부족 지수 (전기차 수 / 충전소 수)',
        nan_fill_color='lightgray'
    ).add_to(m)

    folium.GeoJson(
        gu_geojson,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'transparent',
            'weight': 0
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['gu_name', '전기차수', '충전소수', '부족지수'],
            aliases=['구', '전기차 수', '충전소 수', '부족 지수'],
            localize=True,
            sticky=True,
            style="""
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Noto Sans KR', sans-serif;
            """
        )
    ).add_to(m)

    # 구 이름 라벨
    for _, row in gdf_merged.iterrows():
        centroid = row.geometry.centroid
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:600;color:#333;white-space:nowrap;">{row["gu_name"]}</div>',
                icon_size=(60, 20),
                icon_anchor=(30, 10)
            )
        ).add_to(m)

    st_folium(m, width='100%', height=580, returned_objects=[])

    # 하단 순위표
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**구별 부족 지수 순위**")
    df_rank = df_shortage[['gu_name', '전기차수', '충전소수', '부족지수']].sort_values('부족지수', ascending=False).reset_index(drop=True)
    df_rank.index += 1
    df_rank.columns = ['구', '전기차 수', '충전소 수', '부족 지수']
    st.dataframe(df_rank, use_container_width=True, height=300)
    
# ============================================
# 페이지 3 : 
# ============================================