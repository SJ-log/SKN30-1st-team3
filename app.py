import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
import json
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# =========================
# 현재 경로 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent

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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #0f1117; }
    section[data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2e3147;
    }
    section[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    .metric-card {
        background: #1a1d27; border: 1px solid #2e3147;
        border-radius: 12px; padding: 16px 20px; text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #3b82f6; line-height: 1.2; }
    .metric-label { font-size: 12px; color: #6b7280; margin-top: 4px; }
    .page-title   { font-size: 22px; font-weight: 700; color: #f1f5f9; margin-bottom: 4px; }
    .page-subtitle { font-size: 13px; color: #6b7280; margin-bottom: 20px; }
    div[data-testid="stHorizontalBlock"] { gap: 12px; }
    div[data-testid="column"] { padding: 0; }
    .block-container { padding: 1.5rem 2rem; }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-10px); }
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# 데이터 로드
# ============================================
@st.cache_data
def load_csv_data():
    try:
        df_station = pd.read_csv("charging_station_list.csv", encoding='cp949')
        df_car     = pd.read_csv("seoul_car_status.csv",       encoding='cp949')
        df_gu      = pd.read_csv("gu_master.csv",              encoding='cp949')
    except UnicodeDecodeError:
        df_station = pd.read_csv("charging_station_list.csv", encoding='utf-8-sig')
        df_car     = pd.read_csv("seoul_car_status.csv",       encoding='utf-8-sig')
        df_gu      = pd.read_csv("gu_master.csv",              encoding='utf-8-sig')
    return df_station, df_car, df_gu

@st.cache_data
def get_station_data():
    df_station, _, df_gu = load_csv_data()
    merged = pd.merge(df_station, df_gu, on='gu_code', how='inner')
    merged = merged.dropna(subset=['lat', 'lng'])
    merged = merged[(merged['lat'] != 0) & (merged['lng'] != 0)]
    return merged[['id', '충전소', '충전기타입', '주소', '운영기관', 'lat', 'lng', 'gu_name']]

@st.cache_data
def get_shortage_data():
    df_station, df_car, df_gu = load_csv_data()
    df_ev = df_car[df_car['연료명'] == '전기'].groupby('gu_code')['계'].sum().reset_index()
    df_ev = pd.merge(df_ev, df_gu, on='gu_code', how='inner')
    df_ev.rename(columns={'계': '전기차수'}, inplace=True)
    df_st_count = df_station.groupby('gu_code').size().reset_index(name='충전소수')
    df = pd.merge(df_ev, df_st_count, on='gu_code', how='left')
    df['충전소수'] = df['충전소수'].fillna(0)
    df['부족지수'] = df.apply(
        lambda r: round(r['전기차수'] / r['충전소수'], 2) if r['충전소수'] > 0 else 9999, axis=1
    )
    return df

@st.cache_data
def load_price_map_data():
    geo_path     = BASE_DIR / "서울_자치구_경계_2017.geojson"
    fee_csv_path = BASE_DIR / "seoul_charge_final.csv"
    car_csv_path = BASE_DIR / "seoul_car_sum.csv"
    with open(geo_path, "r", encoding="utf-8") as f:
        my_geo = json.load(f)
    fee_df = pd.read_csv(fee_csv_path, encoding="utf-8")
    fee_df.columns = fee_df.columns.str.strip()
    fee_df["시군구"]      = fee_df["시군구"].astype(str).str.strip()
    fee_df["충전유형"]    = fee_df["충전유형"].astype(str).str.strip()
    fee_df["회원가_평균"]   = pd.to_numeric(fee_df["회원가_평균"],   errors="coerce")
    fee_df["비회원가_평균"] = pd.to_numeric(fee_df["비회원가_평균"], errors="coerce")
    car_df = pd.read_csv(car_csv_path, encoding="utf-8")
    car_df.columns = car_df.columns.str.strip()
    car_df = car_df.rename(columns={"시군구명": "시군구", "sum(계)": "전기차대수"})
    car_df["시군구"]     = car_df["시군구"].astype(str).str.strip()
    car_df["전기차대수"] = pd.to_numeric(
        car_df["전기차대수"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    gdf = gpd.read_file(geo_path, encoding="utf-8")
    return my_geo, fee_df, car_df, gdf

@st.cache_data
def load_geojson():
    try:
        gdf = gpd.read_file('hangjeongdong_서울특별시.geojson')
        gdf['sgg'] = gdf['sgg'].astype(int)
        gdf_gu = gdf.dissolve(by='sgg').reset_index()[['sgg', 'sggnm', 'geometry']]
        gdf_gu.columns = ['gu_code', 'gu_name', 'geometry']
        return gdf_gu
    except Exception:
        st.error("GeoJSON 파일을 찾을 수 없습니다.")
        return None


# ============================================
# 홈 페이지
# ============================================
def render_home_page():
    # 히어로 섹션
    st.markdown('''
    <div style="text-align:center; padding:60px 20px 40px;">
        <div style="font-size:64px; margin-bottom:16px; display:inline-block;
                    animation: float 3s ease-in-out infinite;">⚡</div>
        <h1 style="font-size:36px; font-weight:700; color:#f1f5f9;
                   margin-bottom:12px; letter-spacing:-0.5px;">
            서울시 전기차 충전 인프라 분석
        </h1>
        <p style="font-size:16px; color:#6b7280; max-width:560px;
                  margin:0 auto 40px; line-height:1.7;">
            서울시 25개 구의 전기차 등록 현황과 충전소 분포를 분석하여<br>
            충전 인프라 부족 지역을 시각화한 대시보드입니다.
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # 핵심 지표 카드
    df_station, df_car, df_gu = load_csv_data()
    total_stations = len(df_station)
    total_ev       = int(df_car[df_car['연료명'] == '전기']['계'].sum())
    total_gu       = len(df_gu)

    c1, c2, c3 = st.columns(3)
    for col, icon, val, label in [
        (c1, "🔌", f"{total_stations:,}", "등록된 충전소 수"),
        (c2, "🚗", f"{total_ev:,}",       "서울시 전기차 대수"),
        (c3, "🗺️", f"{total_gu}",         "분석 대상 자치구"),
    ]:
        with col:
            st.markdown(f'''
            <div style="background:#1a1d27; border:1px solid #2e3147; border-radius:16px;
                        padding:28px 20px; text-align:center;">
                <div style="font-size:32px; margin-bottom:10px;">{icon}</div>
                <div style="font-size:32px; font-weight:700; color:#3b82f6; line-height:1.1;">{val}</div>
                <div style="font-size:13px; color:#6b7280; margin-top:6px;">{label}</div>
            </div>''', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 메뉴 소개 카드
    st.markdown('''
    <p style="text-align:center; font-size:18px; font-weight:600;
              color:#e2e8f0; margin-bottom:20px;">📋 제공 기능</p>
    ''', unsafe_allow_html=True)

    menus = [
        ("🗺️", "전체 충전소 현황",
         "서울시 모든 충전소의 위치를 지도에 표시합니다. 구별 필터링 및 충전소 상세 정보를 확인할 수 있습니다.",
         "stations"),
        ("📊", "구역별 인프라 부족 정도",
         "전기차 수 대비 충전소 수를 계산하여 충전 인프라가 부족한 구역을 색상으로 시각화합니다.",
         "shortage"),
        ("💰", "요금 / 전기차 지도",
         "자치구별 평균 충전 요금과 전기차 등록 대수를 지도 위에 시각화합니다.",
         "price_map"),
    ]

    cols = st.columns(3)
    for col, (icon, title, desc, page_key) in zip(cols, menus):
        with col:
            st.markdown(f'''
            <div style="background:#1a1d27; border:1px solid #2e3147; border-radius:16px;
                        padding:24px 20px; min-height:180px;">
                <div style="font-size:28px; margin-bottom:12px;">{icon}</div>
                <p style="font-size:15px; font-weight:600; color:#e2e8f0; margin-bottom:8px;">{title}</p>
                <p style="font-size:13px; color:#6b7280; line-height:1.6;">{desc}</p>
            </div>''', unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button(f"{title} 바로가기 →", key=f"home_btn_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 데이터 출처
    st.markdown('''
    <div style="text-align:center; padding:24px; border-top:1px solid #2e3147;
                color:#4b5563; font-size:12px; line-height:1.8;">
        📂 데이터 출처: 서울 열린데이터 광장 &nbsp;|&nbsp;
        🗓️ 기준: 2024년 &nbsp;|&nbsp;
        🔧 Built with Streamlit · Folium · Plotly
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 페이지 3: 요금 / 전기차 지도
# ============================================
def render_price_map_page():
    my_geo, fee_df, car_df, gdf = load_price_map_data()

    st.markdown('<p class="page-title">💰 요금 및 전기차 현황 지도</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">지역구별 평균 충전요금과 자치구별 전기차 대수 조회.</p>', unsafe_allow_html=True)

    st.markdown("옵션 선택")
    mode_col1, _ = st.columns(2)
    with mode_col1:
        mode = st.selectbox("조회 항목", ["요금 확인", "전기차 대수 확인"], key="price_mode")

    plot_df = color_col = map_title = hover_data = rank_df = None

    if mode == "전기차 대수 확인":
        plot_df    = car_df.copy()
        color_col  = "전기차대수"
        map_title  = "서울 자치구별 전기차 대수"
        hover_data = {"전기차대수": ":,.0f"}
        rank_df = (plot_df[["시군구", "전기차대수"]]
                   .sort_values("전기차대수", ascending=False)
                   .reset_index(drop=True))
        rank_df.insert(0, "순위", range(1, len(rank_df) + 1))

    elif mode == "요금 확인":
        opt1, opt2 = st.columns(2)
        with opt1:
            charge_type = st.selectbox("충전유형", ["급속", "완속"], key="price_charge_type")
        with opt2:
            price_type  = st.selectbox("가격종류", ["회원가_평균", "비회원가_평균"], key="price_type")

        title_map  = {"회원가_평균": "회원가 평균", "비회원가_평균": "비회원가 평균"}
        plot_df    = fee_df[fee_df["충전유형"] == charge_type].copy()
        color_col  = price_type
        map_title  = f"서울 자치구별 {charge_type} 충전 {title_map[price_type]}"
        hover_data = {"충전유형": True, "회원가_평균": ":.2f", "비회원가_평균": ":.2f"}
        rank_df = (plot_df[["시군구", "충전유형", "회원가_평균", "비회원가_평균"]]
                   .sort_values(price_type)
                   .reset_index(drop=True))
        rank_df.insert(0, "순위", range(1, len(rank_df) + 1))

    fig = px.choropleth_mapbox(
        plot_df, geojson=my_geo, locations="시군구",
        featureidkey="properties.SIG_KOR_NM", color=color_col,
        hover_name="시군구", hover_data=hover_data,
        color_continuous_scale=[[0.0,"#02eeff"],[0.5,"#0080ff"],[1.0,"#1B00C8"]],
        mapbox_style="carto-positron", zoom=9.5,
        center={"lat": 37.563383, "lon": 126.996039}, opacity=0.95,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=1)
    label_points = gdf.representative_point()
    fig.add_trace(go.Scattermapbox(
        lon=label_points.x, lat=label_points.y, text=gdf["SIG_KOR_NM"], mode="text",
        textfont=dict(size=13, color="white", weight="bold"),
        textposition="middle center", hoverinfo="skip", showlegend=False
    ))
    fig.update_layout(
        title={"text": map_title, "x": 0.5, "xanchor": "center", "font": {"size": 24}},
        margin={"r": 0, "t": 70, "l": 0, "b": 0}, height=650
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

    if mode == "요금 확인":
        compare_df = pd.concat([
            fee_df[["시군구","충전유형","회원가_평균"]].rename(columns={"회원가_평균":"가격"}).assign(가격종류="회원가"),
            fee_df[["시군구","충전유형","비회원가_평균"]].rename(columns={"비회원가_평균":"가격"}).assign(가격종류="비회원가")
        ], ignore_index=True)
        compare_df["구분"] = compare_df["가격종류"] + " " + compare_df["충전유형"]

        summary_rows = []
        for category, grp in compare_df.groupby("구분"):
            min_idx = grp["가격"].idxmin()
            max_idx = grp["가격"].idxmax()
            summary_rows += [
                {"구분": category, "비교": "최저가", "가격": grp.loc[min_idx,"가격"], "지역": grp.loc[min_idx,"시군구"]},
                {"구분": category, "비교": "최고가", "가격": grp.loc[max_idx,"가격"], "지역": grp.loc[max_idx,"시군구"]},
            ]
        summary_df = pd.DataFrame(summary_rows)
        order = ["회원가 급속","회원가 완속","비회원가 급속","비회원가 완속"]
        summary_df["구분"] = pd.Categorical(summary_df["구분"], categories=order, ordered=True)
        summary_df = summary_df.sort_values(["구분","비교"])

        bar_fig = px.bar(
            summary_df, x="구분", y="가격", color="비교", barmode="group",
            text="가격", hover_data={"지역": True, "가격": ":.2f"},
            color_discrete_map={"최저가": "#22ff00", "최고가": "#CB0596"},
            title="충전 유형별 최저가 · 최고가 비교"
        )
        bar_fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        bar_fig.update_layout(
            height=450, title={"x":0.5,"xanchor":"center","font":{"size":22}},
            xaxis_title="", yaxis_title="평균 요금(원)",
            margin={"r":20,"t":60,"l":20,"b":20}
        )
        st.plotly_chart(bar_fig, use_container_width=True)

    rank_title = "서울 자치구별 전기차 충전요금 순위" if mode == "요금 확인" else "서울 자치구별 전기차 대수 순위"
    st.markdown(f'''
    <p style="font-size:28px; font-weight:700; text-align:center; margin-bottom:12px;">
        {rank_title}
    </p>''', unsafe_allow_html=True)

    _, center, _ = st.columns([1.2, 1.6, 1.2])
    with center:
        st.dataframe(rank_df, use_container_width=True, hide_index=True)


# ============================================
# 사이드바
# ============================================
SEOUL_CENTER = [37.5665, 126.9780]

with st.sidebar:
    st.markdown("### ⚡ 서울시 전기차\n### 충전 인프라")
    st.markdown("<hr style='border-color:#2e3147;margin:12px 0'>", unsafe_allow_html=True)

    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    for label, key in [
        ("🏠  소개",                   'home'),
        ("🗺️  전체 충전소 현황",       'stations'),
        ("📊  구역별 인프라 부족 정도", 'shortage'),
        ("💰  요금 / 전기차 지도",      'price_map'),
    ]:
        if st.button(label, use_container_width=True,
                     type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key
            st.rerun()

    st.markdown("<hr style='border-color:#2e3147;margin:12px 0'>", unsafe_allow_html=True)

    if st.session_state.page == 'stations':
        st.markdown("**🔍 구 필터**")
        df_s    = get_station_data()
        gu_list = ['전체'] + sorted(df_s['gu_name'].dropna().unique().tolist())
        selected_gu = st.selectbox("구 선택", gu_list, label_visibility="collapsed")
    else:
        selected_gu = '전체'


# ============================================
# 페이지 라우팅
# ============================================
if st.session_state.page == 'home':
    render_home_page()

elif st.session_state.page == 'stations':
    df_station = get_station_data()
    if selected_gu != '전체':
        df_station = df_station[df_station['gu_name'] == selected_gu]

    st.markdown('<p class="page-title">🗺️ 서울시 전체 충전소 현황</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">서울시 전기차 충전소 위치 및 현황</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, val, label in [
        (c1, f"{len(df_station):,}",              "총 충전소 수"),
        (c2, f"{df_station['gu_name'].nunique()}", "구역 수"),
        (c3, f"{df_station['충전기타입'].nunique()}", "충전기 타입 수"),
    ]:
        with col:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    m = folium.Map(location=SEOUL_CENTER, zoom_start=11, tiles='CartoDB dark_matter')
    from folium.plugins import MarkerCluster
    cluster = MarkerCluster().add_to(m)
    for _, row in df_station.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lng']], radius=4,
            color='#3b82f6', fill=True, fill_color='#60a5fa', fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['충전소']}</b><br>{row['주소']}<br>타입: {row['충전기타입']}<br>운영: {row['운영기관']}",
                max_width=250),
            tooltip=row['충전소']
        ).add_to(cluster)
    st_folium(m, width='100%', height=580, returned_objects=[])

elif st.session_state.page == 'shortage':
    df_shortage = get_shortage_data()
    gdf_gu      = load_geojson()
    gdf_merged  = gdf_gu.merge(df_shortage.drop(columns=['gu_name']), on='gu_code', how='left')
    gu_geojson  = json.loads(gdf_merged.to_json())

    st.markdown('<p class="page-title">📊 구역별 충전 인프라 부족 정도</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">전기차 수 대비 충전소 수 비율 — 빨간색일수록 충전소가 부족한 구역</p>', unsafe_allow_html=True)

    top3 = df_shortage.nlargest(3, '부족지수')
    c1, c2, c3 = st.columns(3)
    for col, (_, row) in zip([c1, c2, c3], top3.iterrows()):
        with col:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value" style="color:#ef4444">{row['gu_name']}</div>
                <div class="metric-label">부족지수 {row['부족지수']:,.0f}
                (전기차 {row['전기차수']:,}대 / 충전소 {row['충전소수']:,}개)</div>
            </div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    m = folium.Map(location=SEOUL_CENTER, zoom_start=11, tiles='CartoDB positron')
    folium.Choropleth(
        geo_data=gu_geojson, data=df_shortage,
        columns=['gu_code', '부족지수'], key_on='feature.properties.gu_code',
        fill_color='YlOrRd', fill_opacity=0.75, line_opacity=0.6,
        line_color='white', legend_name='충전소 부족 지수 (전기차 수 / 충전소 수)',
        nan_fill_color='lightgray'
    ).add_to(m)
    folium.GeoJson(
        gu_geojson,
        style_function=lambda x: {'fillColor':'transparent','color':'transparent','weight':0},
        tooltip=folium.GeoJsonTooltip(
            fields=['gu_name','전기차수','충전소수','부족지수'],
            aliases=['구','전기차 수','충전소 수','부족 지수'],
            localize=True, sticky=True,
            style="background-color:white;border:1px solid #ccc;border-radius:6px;padding:8px;font-size:13px;"
        )
    ).add_to(m)
    for _, row in gdf_merged.iterrows():
        centroid = row.geometry.centroid
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:600;color:#333;white-space:nowrap;">{row["gu_name"]}</div>',
                icon_size=(60, 20), icon_anchor=(30, 10)
            )
        ).add_to(m)
    st_folium(m, width='100%', height=580, returned_objects=[])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**구별 부족 지수 순위**")
    df_rank = df_shortage[['gu_name','전기차수','충전소수','부족지수']].sort_values('부족지수', ascending=False).reset_index(drop=True)
    df_rank.index += 1
    df_rank.columns = ['구','전기차 수','충전소 수','부족 지수']
    st.dataframe(df_rank, use_container_width=True, height=300)

elif st.session_state.page == 'price_map':
    render_price_map_page()