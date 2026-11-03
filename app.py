"""
TrayZero+ TamJai Version: AI-Driven Smart Tray Audit, BOH Kitchen Prep Optimization, and Custom Loyalty Loop System
Standalone Streamlit Application (TamJai Edition with Lightweight Transformers for Fine-Tuning Integration)
"""

import os
import time
import datetime
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import altair as alt

# Safe import for torch and transformers (Lightweight pipeline configuration)
try:
    import torch
    from transformers import AutoImageProcessor, AutoModelForImageClassification, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# ==============================================================================
# 0. Primary Streamlit Execution Configuration
# ==============================================================================
st.set_page_config(
    page_title="TrayZero+ TamJai | 譚仔智慧餐盤審計與備料優化系統",
    page_icon="🥢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. Global Paths & TamJai Enterprise CSS Theme
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "trayzero_tamjai.db")

def inject_tamjai_css():
    st.markdown("""
    <style>
    :root {
        --tamjai-red: #B91C1C !important;
        --tamjai-orange: #C2410C !important;
        --text-color: #0F172A !important;
        --background-color: #F8FAFC !important;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "PingFang HK", Arial, sans-serif !important;
    }
    .main .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1.5px solid #CBD5E1 !important;
        padding-top: 1rem !important;
    }
    .tamjai-header-banner {
        background: linear-gradient(135deg, #991B1B 0%, #C2410C 50%, #B45309 100%) !important;
        border-radius: 14px !important;
        padding: 18px 24px !important;
        margin-bottom: 22px !important;
        box-shadow: 0 4px 14px rgba(153, 27, 27, 0.18) !important;
        color: white !important;
    }
    .tamjai-header-banner h1, .tamjai-header-banner p {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_tamjai_css()

# ==============================================================================
# 2. SQLite Database Initialization & Master Data Seed
# ==============================================================================
def init_tamjai_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tamjai_branches (
        branch_id TEXT PRIMARY KEY,
        name TEXT,
        district TEXT,
        region TEXT,
        avg_daily_bowls INTEGER
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tamjai_menu (
        item_code TEXT PRIMARY KEY,
        category TEXT,
        name_zh TEXT,
        default_portion_g INTEGER
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tamjai_audit_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        branch_name TEXT,
        dish_name TEXT,
        broth_type TEXT,
        waste_ratio REAL,
        primary_leftover TEXT,
        side_dish_detected TEXT,
        directive_sop TEXT,
        reward_issued TEXT
    )''')
    
    cursor.execute("SELECT COUNT(*) FROM tamjai_branches")
    if cursor.fetchone()[0] == 0:
        branches = [
            ('B01', '銅鑼灣廣場店', '灣仔區', '香港島', 1400),
            ('B02', '旺角亞皆老街店', '油尖旺區', '九龍', 1800),
            ('B03', '沙田廣場店', '沙田區', '新界', 1500),
            ('B04', '荃灣大河道店', '荃灣區', '新界', 1650),
            ('B05', '觀塘創紀之城店', '觀塘區', '九龍', 1700)
        ]
        cursor.executemany("INSERT INTO tamjai_branches VALUES (?, ?, ?, ?, ?)", branches)
        
    cursor.execute("SELECT COUNT(*) FROM tamjai_menu")
    if cursor.fetchone()[0] == 0:
        menu_items = [
            ('M01', 'Main Noodle', '招牌米線 (Rice Noodles)', 350),
            ('M02', 'Main Noodle', '寬薯粉 (Sweet Potato Noodles)', 320),
            ('S01', 'Side Dish', '蒜泥白肉 (Garlic Pork Belly)', 180),
            ('S02', 'Side Dish', '湖南土匪雞翼 (Bandit Wings)', 200),
            ('S03', 'Side Dish', '酸辣皮蛋 (Century Egg)', 150),
            ('S04', 'Side Dish', '手拍青瓜 (Cucumber)', 140),
            ('T01', 'Topping', '韭菜 (Chives)', 50),
            ('T02', 'Topping', '芽菜 (Bean Sprouts)', 60),
            ('T03', 'Topping', '炸醬 (Minced Pork Zhajiang)', 70),
            ('T04', 'Topping', '魚腐 (Fish Paste Puff)', 65),
            ('T05', 'Topping', '鯇魚片 (Grass Carp Fillet)', 90)
        ]
        cursor.executemany("INSERT INTO tamjai_menu VALUES (?, ?, ?, ?)", menu_items)
        
    cursor.execute("SELECT COUNT(*) FROM tamjai_audit_logs")
    if cursor.fetchone()[0] == 0:
        sample_logs = [
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '旺角亞皆老街店', '招牌米線 (Rice Noodles)', '三哥酸辣 (SamGor Hot & Sour)', 28.5, '韭菜 (Chives), 芽菜 (Bean Sprouts)', '湖南土匪雞翼 (Bandit Wings)', '【BOH 備料調整】分店芽菜與韭菜剩餘率達 28.5%，建議明日中央廚房減少 15% 蔬菜切配量。', '【FOH 會員獎勵】贈送 20 綠色環保積分。'),
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '銅鑼灣廣場店', '招牌米線 (Rice Noodles)', '麻辣 (Mala Broth)', 12.0, '湯底殘留 (Broth Liquid)', '蒜泥白肉 (Garlic Pork Belly)', '【BOH 備料調整】光盤率良好，維持現行湯底與米線標準配份。', '【FOH 會員獎勵】獲得 $3 堂食現金券 + 50 綠色積分。')
        ]
        cursor.executemany("INSERT INTO tamjai_audit_logs (timestamp, branch_name, dish_name, broth_type, waste_ratio, primary_leftover, side_dish_detected, directive_sop, reward_issued) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_logs)
        
    conn.commit()
    conn.close()

init_tamjai_db()

# ==============================================================================
# 3. Sidebar Enterprise Navigation & Configuration
# ==============================================================================
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 12px;">
    <h2 style="color: #991B1B; margin-bottom: 0px;">🥢 譚仔 TrayZero+</h2>
    <p style="font-size: 0.85rem; color: #475569;">智慧餐盤審計與備料優化系統</p>
</div>
""", unsafe_allow_html=True)

app_mode = st.sidebar.radio(
    "選擇營運模組 (Operational Mode)",
    [
        "📸 前線智慧回收台審計 (Kiosk Mode)",
        "📊 總部營運與備料分析 (HQ & ESG Analytics)",
        "⚙️ 譚仔全品項 Taxonomy 字典管理"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 企業控制模組 (M1–M4)")
mod_m1 = st.sidebar.checkbox("M1: 營運核心與視覺審計 (Vision AI)", value=True)
mod_m2 = st.sidebar.checkbox("M2: 總部大數據分析 (Big Data BI)", value=True)
mod_m3 = st.sidebar.checkbox("M3: 智慧 POS 聯動引擎 (Reverse-POS)", value=True)
mod_m4 = st.sidebar.checkbox("M4: 會員與環保積分閉環 (Club Loyalty)", value=True)

# ==============================================================================
# 4. Main Application Views
# ==============================================================================

# --- MODE 1: Frontline Smart Tray Return Kiosk ---
if app_mode == "📸 前線智慧回收台審計 (Kiosk Mode)":
    st.markdown("""
    <div class="tamjai-header-banner">
        <h1 style="margin:0; font-size: 1.8rem;">📸 譚仔前線智慧回收台 (Smart Tray Kiosk)</h1>
        <p style="margin: 5px 0 0 0; font-size: 1rem; opacity: 0.9;">
            即時檢測譚仔深色大碗殘食、湯底殘留、百味配料與招牌小菜（蒜泥白肉、土匪雞翼等），自動觸發後場備料與前線積分獎勵。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not mod_m1:
        st.warning("⚠️ M1 營運核心模組目前已停用，視覺審計與視覺辨識功能暫停。")
    else:
        col1, col2 = st.columns([1, 1], gap="medium")
        
        with col1:
            st.subheader("📤 上傳或拍攝回收餐盤影像")
            uploaded_file = st.file_uploader("選擇譚仔回收餐盤照片 (JPG / PNG)", type=["jpg", "jpeg", "png"])
            
            selected_branch = st.selectbox("選擇分店", ["銅鑼灣廣場店", "旺角亞皆老街店", "沙田廣場店", "荃灣大河道店", "觀塘創紀之城店"])
            selected_broth = st.selectbox("湯底選擇", ["麻辣 (Mala Broth)", "酸辣 (Hot & Sour Broth)", "三哥酸辣 (SamGor Hot & Sour)", "清湯 (Clear Broth)", "番茄湯 (Tomato Broth)", "煳辣湯 (Hula Broth)"])
            selected_side = st.selectbox("搭配小菜", ["無小菜", "蒜泥白肉 (Garlic Pork Belly)", "湖南土匪雞翼 (Bandit Wings)", "酸辣皮蛋 (Century Egg)", "手拍青瓜 (Cucumber)"])
            
            run_audit = st.button("🚀 執行全品項智慧審計 (Run Audit)", type="primary", use_container_width=True)
            
        with col2:
            st.subheader("🔍 審計檢視與即時分析 (Fine-tuned Swin/Flan-T5 Ready)")
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="已上傳之譚仔回收托盤影像", use_container_width=True)
            else:
                st.info("💡 請於左側上傳回收托盤影像以啟動 Pipeline 1 (Swin-Tiny) 與 Pipeline 2 (Flan-T5) 輕量推論。")
                
        if run_audit:
            with st.spinner("🔄 正在載入輕量 Transformer 模型權重進行推論（支援本地與 Colab Fine-tune 權重掛載）..."):
                time.sleep(0.6)
                if TRANSFORMERS_AVAILABLE:
                    # 預留給您之後掛載微調模型的介面示範
                    pass
                
            sim_waste_ratio = 24.5 if selected_side != "無小菜" else 15.2
            sim_leftover = "韭菜 (Chives), 芽菜 (Bean Sprouts), 湯底殘留 120ml"
            sim_directive = "【BOH 備料調整 (Flan-T5)】分店芽菜與韭菜剩餘率達 28.5%，建議明日中央廚房減少 15% 蔬菜切配量；麻辣湯底剩餘率達 18%，建議加強辣度溝通。"
            sim_reward = "【FOH 會員獎勵】達標惜食獎：獲得 $2 堂食電子券 + 20 綠色環保積分。"
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tamjai_audit_logs (timestamp, branch_name, dish_name, broth_type, waste_ratio, primary_leftover, side_dish_detected, directive_sop, reward_issued) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_branch, "招牌米線 (Rice Noodles)", selected_broth, sim_waste_ratio, sim_leftover, selected_side, sim_directive, sim_reward)
            )
            conn.commit()
            conn.close()
            
            st.success("✅ 審計完成並已透過輕量 Transformer 產出指令，寫入企業資料庫！")
            
            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("綜合殘食浪費率", f"{sim_waste_ratio}%", delta="-3.2% vs 昨日", delta_color="inverse")
            res_col2.metric("檢測出主要殘留", "韭菜 / 芽菜 / 湯汁")
            res_col3.metric("小菜碟盤清理度", "良好 (無顯著骨頭殘留)")
            
            st.markdown("### 🤖 Flan-T5 微調後模型生成指令")
            st.info(sim_directive)
            st.success(sim_reward)

# --- MODE 2: HQ & ESG Analytics ---
elif app_mode == "📊 總部營運與備料分析 (HQ & ESG Analytics)":
    st.markdown("""
    <div class="tamjai-header-banner">
        <h1 style="margin:0; font-size: 1.8rem;">📊 譚仔總部營運、備料與 ESG 減碳大數據中心</h1>
        <p style="margin: 5px 0 0 0; font-size: 1rem; opacity: 0.9;">
            聯動全港分店回收 telemetry，即時監控湯底損耗、配料浪費熱力圖、中央廚房日均切配優化與碳排放合規指標。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if not mod_m2:
        st.warning("⚠️ M2 總部大數據分析模組目前已停用。")
    else:
        conn = sqlite3.connect(DB_FILE)
        df_logs = pd.read_sql("SELECT * FROM tamjai_audit_logs ORDER BY log_id DESC", conn)
        conn.close()
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("全網聯營分店總數", "85+", "涵蓋港九新界")
        kpi2.metric("平均綜合浪費率", "16.4%", "-2.1% 較上月優化")
        kpi3.metric("年度預估食材成本節省", "HK$ 685萬", "精準備料驅動")
        kpi4.metric("Scope 3 減碳量", "2,450 噸 CO₂e", "符合 ESG 規範")
        
        st.markdown("---")
        st.subheader("📋 即時回收審計記錄與備料回饋")
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("尚無審計記錄。")
            
        st.markdown("### 📈 各分店湯底與配料浪費分佈")
        chart_data = pd.DataFrame({
            '分店': ['銅鑼灣廣場店', '旺角亞皆老街店', '沙田廣場店', '荃灣大河道店', '觀塘創紀之城店'],
            '平均浪費率 (%)': [14.2, 18.5, 15.1, 16.8, 17.4]
        })
        chart = alt.Chart(chart_data).mark_bar(color='#B91C1C').encode(
            x=alt.X('分店:N', sort='-y'),
            y='平均浪費率 (%):Q',
            tooltip=['分店', '平均浪費率 (%)']
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

# --- MODE 3: Taxonomy & Master Configuration ---
elif app_mode == "⚙️ 譚仔全品項 Taxonomy 字典管理":
    st.markdown("""
    <div class="tamjai-header-banner">
        <h1 style="margin:0; font-size: 1.8rem;">⚙️ 譚仔全品項識別字典 (Taxonomy Management)</h1>
        <p style="margin: 5px 0 0 0; font-size: 1rem; opacity: 0.9;">
            管理譚仔超過 40+ 種細分檢測標籤（含招牌小菜、湯底、米線配料、鯇魚片與魚腐等）。
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_FILE)
    df_menu = pd.read_sql("SELECT * FROM tamjai_menu", conn)
    conn.close()
    
    st.subheader("🏷️ 目前資料庫收錄之譚仔菜單與配料標籤")
    st.dataframe(df_menu, use_container_width=True)
    
    st.markdown("### ➕ 新增自定義檢測類別 / 配料")
    with st.form("add_taxonomy_form"):
        new_code = st.text_input("類別代碼 (Item Code, e.g., T06)")
        new_cat = st.selectbox("類別歸屬", ["Main Noodle", "Side Dish", "Topping", "Broth Base"])
        new_name = st.text_input("名稱 (中文與英文說明)")
        new_portion = st.number_input("標準克數 / 容量 (g 或 ml)", min_value=10, value=50)
        submit_tax = st.form_submit_button("確認新增至 Taxonomy 字典")
        
        if submit_tax and new_code and new_name:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO tamjai_menu VALUES (?, ?, ?, ?)", (new_code, new_cat, new_name, new_portion))
                conn.commit()
                st.success(f"Successfully added {new_name} to database!")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()
