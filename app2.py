import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import plotly.graph_objects as go
from datetime import datetime
import pytz

# ==========================================
# 1. قاموس البحث الذكي (تحويل الأسماء المباشرة إلى رموز بورصة)
# ==========================================
COMPANY_DICTIONARY = {
    # السوق السعودي 🇸🇦
    "الراجحي": "1120.SR", "مصرف الراجحي": "1120.SR",
    "أرامكو": "2222.SR", "أرامكو السعودية": "2222.SR",
    "الأهلي": "1180.SR", "البنك الأهلي": "1180.SR",
    "سابك": "2010.SR", "الاتصالات السعودية": "7010.SR", "stc": "7010.SR",
    # السوق الأمريكي 🇺🇸
    "تسلا": "TSLA", "tesla": "TSLA",
    "أبل": "AAPL", "apple": "AAPL",
    "مايكروسوفت": "MSFT", "microsoft": "MSFT",
    "إنفيديا": "NVDA", "nvidia": "NVDA",
    "جوجل": "GOOGL", "google": "GOOGL"
}

def resolve_ticker(user_input, market_type):
    clean_input = user_input.strip().lower()
    if clean_input in COMPANY_DICTIONARY:
        return COMPANY_DICTIONARY[clean_input]
    if market_type == "السوق السعودي (تداول) 🇸🇦":
        if not clean_input.endswith(".sr") and clean_input.isdigit():
            return f"{clean_input}.SR"
    return user_input.upper().strip()

# ==========================================
# 2. دالة فحص وتحديد حالة وقت السوق اللحظية
# ==========================================
def get_market_status(market_type):
    """تحديد ما إذا كان السوق مفتوحاً، مغلقاً، قبل الافتتاح أو بعده بناءً على التوقيت المحلي"""
    now_utc = datetime.now(pytz.utc)
    
    if market_type == "السوق السعودي (تداول) 🇸🇦":
        tz_sa = pytz.timezone('Asia/Riyadh')
        now_local = now_utc.astimezone(tz_sa)
        current_time = now_local.time()
        weekday = now_local.weekday()  # 0=الأحد, 4=الخميس, 5=الجمعة, 6=السبت
        
        if weekday in: 
            return "🔴 السوق مقفل (إجازة أسبوعية)"
            
        start_pre = datetime.strptime("09:30:00", "%H:%M:%S").time()
        start_market = datetime.strptime("10:00:00", "%H:%M:%S").time()
        end_market = datetime.strptime("15:00:00", "%H:%M:%S").time()
        
        if current_time < start_pre:
            return "🟡 السوق مغلق (قبل فترة ما قبل الافتتاح)"
        elif start_pre <= current_time < start_market:
            return "🟠 فترة ما قبل الافتتاح (Pre-Market)"
        elif start_market <= current_time < end_market:
            return "🟢 السوق مفتوح وجاري التداول اللحظي"
        else:
            return "🔴 السوق مغلق (بعد إغلاق الفترة الرسمية)"
            
    else:  # السوق الأمريكي
        tz_us = pytz.timezone('US/Eastern')
        now_local = now_utc.astimezone(tz_us)
        current_time = now_local.time()
        weekday = now_local.weekday()  # 5=السبت, 6=الأحد
        
        if weekday in:
            return "🔴 السوق مقفل (إجازة أسبوعية)"
            
        start_pre = datetime.strptime("04:00:00", "%H:%M:%S").time()
        start_market = datetime.strptime("09:30:00", "%H:%M:%S").time()
        end_market = datetime.strptime("16:00:00", "%H:%M:%S").time()
        end_post = datetime.strptime("20:00:00", "%H:%M:%S").time()
        
        if current_time < start_pre:
            return "🟡 السوق مغلق (قبل فترة ما قبل الافتتاح)"
        elif start_pre <= current_time < start_market:
            return "🟠 فترة ما قبل الافتتاح الأمريكي (Pre-Market)"
        elif start_market <= current_time < end_market:
            return "🟢 السوق الأمريكي مفتوح حالياً"
        elif end_market <= current_time < end_post:
            return "🔵 فترة ما بعد الإغلاق الرسمي (After-Hours)"
        else:
            return "🔴 السوق مغلق بالكامل"

# ==========================================
# 3. مصفوفة حساب المستهدفات الفنية المضاربية اللحظية
# ==========================================
def calculate_advanced_targets(current_price, high, low):
    """توليد المستويات الفنية والمضاربية الدقيقة حركياً بناء على مستويات الدعم والمقاومة اللحظية"""
    range_movement = (high - low) if (high - low) > 0 else (current_price * 0.02)
    
    optimal_entry = current_price - (range_movement * 0.2)
    target_1 = current_price + (range_movement * 0.4)
    target_2 = current_price + (range_movement * 1.0)
    target_3 = current_price + (range_movement * 1.8)
    stop_loss = current_price - (range_movement * 0.6)
    strict_sl = current_price - (range_movement * 1.2)
    
    return {
        "entry": optimal_entry, "t1": target_1, "t2": target_2, "t3": target_3,
        "sl": stop_loss, "strict_sl": strict_sl
    }

# ==========================================
# 4. بناء واجهة مستخدم Streamlit الرئيسية المحدثة
# ==========================================
def main():
    st.set_page_config(page_title="Stock Radar Pro - رادار الأسهم الاحترافي", layout="wide")
    st.title("📊 رادار الأسهم الاحترافي الذكي (Stock Radar Pro)")
    st.markdown("منصة ذكية لمراقبة الاتجاه الفني، كشف السيولة، وحساب المستهدفات اللحظية لجميع الفريمات.")
    
    # --- شريط التحكم الجانبي ---
    st.sidebar.header("⚙️ إعدادات الرادار والمراقبة")
    market_choice = st.sidebar.selectbox("اختر السوق المستهدف:", ["السوق الأمريكي 🇺🇸", "السوق السعودي (تداول) 🇸🇦"])
    
    user_search = st.sidebar.text_input("أدخل اسم الشركة (مثال: تسلا، أرامكو) أو رمزها المباشر:", value="AAPL")
    timeframe = st.sidebar.selectbox("اختر الفريم الزمني للتحليل (Timeframe):", ["5m", "15m", "1h", "1d", "1wk"])
    
    trigger_radar = st.sidebar.button("تشغيل رادار الفحص اللحظي والمضاربي", use_container_width=True)

    if trigger_radar:
        ticker_resolved = resolve_ticker(user_search, market_choice)
        currency = "ر.س" if market_choice == "السوق السعودي (تداول) 🇸🇦" else "$"
        
        with st.spinner(f"جاري معالجة البيانات الفنية للرمز {ticker_resolved}..."):
            try:
                ticker_obj = yf.Ticker(ticker_resolved)
                
                period_map = {"5m": "5d", "15m": "5d", "1h": "1mo", "1d": "6mo", "1wk": "2y"}
                hist = ticker_obj.history(interval=timeframe, period=period_map[timeframe])
                
                if hist.empty:
                    st.error("⚠️ لم يتم العثور على بيانات نشطة لهذا الرمز. يرجى التأكد من كتابة الاسم أو الرمز بشكل صحيح.")
                    return
                
                hist = hist.dropna(subset=['Close'])
                if hist.empty:
                    st.error("⚠️ البيانات المتوفرة فارغة حالياً.")
                    return
                    
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                price_change = ((current_price - prev_price) / prev_price) * 100
                
                stock_direction = "📈 صاعد مستقر" if price_change >= 0 else "📉 هابط تصحيحي"
                dir_color = "green" if price_change >= 0 else "red"
                
                market_status_text = get_market_status(market_choice)
                
                levels = calculate_advanced_targets(current_price, hist['High'].max(), hist['Low'].min())
                
                # === العرض المرئي للبيانات والحجم ===
                st.subheader("📌 لوحة فحص المؤشرات اللحظية الأساسية")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    st.metric(label=f"السعر الحالي ({currency})", value=f"{current_price:.2f}", delta=f"{price_change:.2f}%")
                with col_m2:
                    st.markdown(f"**حالة توقيت السوق الحالية:**\n\n`{market_status_text}`")
                with col_m3:
                    st.markdown(f"**الاتجاه الفني الحالي:**\n\n<span style='color:{dir_color}; font-size:18px; font-weight:bold;'>{stock_direction}</span>", unsafe_allow_html=True)
                with col_m4:
                    last_vol = hist['Volume'].iloc[-1]
                    liquidity_value = last_vol * current_price
                    st.metric("حجم السيولة المتداولة (آخر شمعة)", f"{liquidity_value:,.0f} {currency}")
                
                info_data = ticker_obj.info
                float_shares = info_data.get("floatShares", info_data.get("sharesOutstanding", 0))
                st.caption(f"الأسهم المتاحة للتداول (Float Shares): {float_shares:,.0f}" if float_shares else "الأسهم المتاحة للتداول: يتم تحديثها دورياً من البورصة")
                
                st.markdown("---")
                
                # === عرض مناطق الدخول والمستهدفات الفنية المضاربية ===
                col_t1, col_t2 = st.columns(2)
                
                with col_t1:
                    st.subheader("🎯 المستهدفات الفنية والمستويات المضاربية اللحظية")
                    st.success(f"🟢 منطقة أفضل سعر للدخول والمضاربة اللحظية: **{levels['entry']:.2f} {currency}**")
                    st.info(f"🚀 الهدف المضاربي الأول: **{levels['t1']:.2f} {currency}**")
                    st.info(f"🚀 الهدف الثاني (متوسط النطاق): **{levels['t2']:.2f} {currency}**")
                    st.info(f"🚀 الهدف الثالث (مستهدف رئيسي): **{levels['t3']:.2f} {currency}**")
                    st.warning(f"⚠️ مستوى وقف الخسارة (لحماية رأس المال): **{levels['sl']:.2f} {currency}**")
                    st.error(f"🚨 وقف الخسارة الصارم النهائي: **{levels['strict_sl']:.2f} {currency}**")
                
                with col_t2:
                    st.subheader("💡 نصائح الرادار الفنية الموجهة")
                    if price_change > 1.5:
                        st.success("🔥 السهم تحت تأثير زخم شرائي قوي وسيولة متدفقة للإيجابية. الدخول الآمن يكون عبر اقتناص التهدئة اللحظية قرب منطقة الدخول المحددة للهدف الأول.")
                    elif price_change < -1.5:
                        st.error("🚨 السهم يتعرض لضغط بيعي هابط وتصحيح حركي. ينصح بالالتزام التام بنقاط وقف الخسارة لعدم الوقوع في تعليقة سعرية حادة.")
                    else:
                        st.warning("⚖️ السهم يتداول في نطاق تجميعي ومسار عرضي متزن حالياً. مناسب جداً للمضاربات السريعة واقتناص الفروقات السعرية البسيطة.")
