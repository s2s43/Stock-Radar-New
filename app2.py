import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import plotly.graph_objects as go
from datetime import datetime
import pytz

# ==========================================
# 1. قاموس البحث الذكي عن الأسهم (تحويل الأسماء لرموز)
# ==========================================
COMPANY_DICTIONARY = {
    "الراجحي": "1120.SR", "مصرف الراجحي": "1120.SR",
    "أرامكو": "2222.SR", "أرامكو السعودية": "2222.SR", "ارامكو": "2222.SR",
    "الأهلي": "1180.SR", "البنك الأهلي": "1180.SR",
    "سابك": "2010.SR", "الاتصالات السعودية": "7010.SR", "stc": "7010.SR",
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
# 2. مصفوفة حساب المستهدفات الفنية المضاربية اللحظية
# ==========================================
def calculate_advanced_targets(current_price, high, low):
    range_movement = (high - low) if (high - low) > 0 else (current_price * 0.02)
    return {
        "entry": current_price - (range_movement * 0.2),
        "t1": current_price + (range_movement * 0.4),
        "t2": current_price + (range_movement * 1.0),
        "t3": current_price + (range_movement * 1.8),
        "sl": current_price - (range_movement * 0.6),
        "strict_sl": current_price - (range_movement * 1.2)
    }

# ==========================================
# 3. بناء واجهة مستخدم Streamlit الرئيسية
# ==========================================
def main():
    st.set_page_config(page_title="Stock Radar Pro - رادار الأسهم الاحترافي", layout="wide")
    st.title("📊 رادار الأسهم الاحترافي الذكي (Stock Radar Pro)")
    st.markdown("منصة ذكية لمراقبة الاتجاه الفني، كشف السيولة، وحساب المستهدفات اللحظية لجميع الفريمات.")
    
    st.sidebar.header("⚙️ إعدادات الرادار والمراقبة")
    market_choice = st.sidebar.selectbox("اختر السوق المستهدف:", ["السوق الأمريكي 🇺🇸", "السوق السعودي (تداول) 🇸🇦"])
    user_search = st.sidebar.text_input("أدخل اسم الشركة أو رمزها المباشر:", value="2222")
    timeframe = st.sidebar.selectbox("اختر الفريم الزمني للتحليل (Timeframe):", ["5m", "15m", "1h", "1d", "1wk"])
    trigger_radar = st.sidebar.button("تشغيل رادار الفحص اللحظي والمضاربي", use_container_width=True)

    if trigger_radar:
        ticker_resolved = resolve_ticker(user_search, market_choice)
        currency = "ر.س" if market_choice == "السوق السعودي (تداول) 🇸🇦" else "$"
        
        hist = pd.DataFrame()
        ticker_obj = None
        
        with st.spinner(f"جاري معالجة البيانات الفنية للرمز {ticker_resolved}..."):
            try:
                ticker_obj = yf.Ticker(ticker_resolved)
                period_map = {"5m": "5d", "15m": "5d", "1h": "1mo", "1d": "6mo", "1wk": "2y"}
                hist = ticker_obj.history(interval=timeframe, period=period_map[timeframe])
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال بمزود البيانات: {str(e)}")
                return

        if hist.empty:
            st.error("⚠️ لم يتم العثور على بيانات نشطة لهذا الرمز. يرجى التأكد من كتابة الاسم أو الرمز بشكل صحيح.")
            return
            
        hist = hist.dropna(subset=['Close'])
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        price_change = ((current_price - prev_price) / prev_price) * 100
        
        stock_direction = "📈 صاعد مستقر" if price_change >= 0 else "📉 هابط تصحيحي"
        dir_color = "green" if price_change >= 0 else "red"
        levels = calculate_advanced_targets(current_price, hist['High'].max(), hist['Low'].min())
        
        try:
            info_data = ticker_obj.info
            company_long_name = info_data.get("longName", ticker_resolved)
        except:
            company_long_name = ticker_resolved

        # --- 🕒 حساب حالة توقيت السوق لحظياً ---
        now_utc = datetime.now(pytz.utc)
        market_status_text = "🔄 جاري الفحص..."
        
        if market_choice == "السوق السعودي (تداول) 🇸🇦":
            sa_tz = pytz.timezone('Asia/Riyadh')
            sa_now = now_utc.astimezone(sa_tz)
            sa_time = sa_now.time()
            sa_day = sa_now.weekday()
            
            if sa_day == 4 or sa_day == 5:
                market_status_text = "🔴 السوق مقفل (إجازة أسبوعية)"
            elif sa_time < datetime.strptime("09:30:00", "%H:%M:%S").time():
                market_status_text = "🟡 السوق مغلق (قبل فترة ما قبل الافتتاح)"
            elif datetime.strptime("09:30:00", "%H:%M:%S").time() <= sa_time < datetime.strptime("10:00:00", "%H:%M:%S").time():
                market_status_text = "🟠 فترة ما قبل الافتتاح (Pre-Market)"
            elif datetime.strptime("10:00:00", "%H:%M:%S").time() <= sa_time < datetime.strptime("15:00:00", "%H:%M:%S").time():
                market_status_text = "🟢 السوق مفتوح وجاري التداول اللحظي"
            else:
                market_status_text = "🔴 السوق مغلق (بعد الإغلاق)"
        else:
            us_tz = pytz.timezone('US/Eastern')
            us_now = now_utc.astimezone(us_tz)
            us_time = us_now.time()
            us_day = us_now.weekday()
            
            if us_day == 5 or us_day == 6:
                market_status_text = "🔴 السوق مقفل (إجازة أسبوعية)"
            elif us_time < datetime.strptime("04:00:00", "%H:%M:%S").time():
                market_status_text = "🟡 السوق مغلق (قبل الجلسات الممتدة)"
            elif datetime.strptime("04:00:00", "%H:%M:%S").time() <= us_time < datetime.strptime("09:30:00", "%H:%M:%S").time():
                market_status_text = "🟠 فترة ما قبل الافتتاح الأمريكي (Pre-Market)"
            elif datetime.strptime("09:30:00", "%H:%M:%S").time() <= us_time < datetime.strptime("16:00:00", "%H:%M:%S").time():
                market_status_text = "🟢 السوق مفتوح وجلسة التداول نشطة"
            elif datetime.strptime("16:00:00", "%H:%M:%S").time() <= us_time < datetime.strptime("20:00:00", "%H:%M:%S").time():
                market_status_text = "🔵 فترة ما بعد الإغلاق الرسمي (After-Hours)"
            else:
                market_status_text = "🔴 السوق مغلق بالكامل"

        # --- 🚨 قسم التنبيهات اللحظية المدمجة في نفس البيانات ---
        st.subheader("🔔 مركز الإشعارات والتنبيهات المضاربية اللحظية")
        alert_triggered = False
        
        last_vol = hist['Volume'].iloc[-1]
        liquidity_value = last_vol * current_price
        avg_vol = hist['Volume'].mean()
        
        if last_vol > (avg_vol * 1.5):
            st.error(f"⚡ **تنبيه سيولة غير طبيعية:** تم رصد تدفق سيولة ضخمة مفاجئة تفوق المعدل اليومي بـ 150%! السيولة الحالية: {liquidity_value:,.0f} {currency}")
            alert_triggered = True
            
        if abs(current_price - levels['entry']) / levels['entry'] <= 0.01:
            st.success(f"🎯 **تنبيه قناص الرادار:** السهم يقف مباشرة عند منطقة الدخول والمضاربة اللحظية المثالية ({levels['entry']:.2f} {currency})")
            alert_triggered = True
        elif current_price <= levels['sl']:
            st.warning(f"🚨 **تنبيه كسر فني:** السهم يتداول حالياً تحت مستوى وقف الخسارة المحدد ({levels['sl']:.2f} {currency})")
            alert_triggered = True
            
        if not alert_triggered:
            st.info("✅ جميع المؤشرات السعرية وحجم السيولة تتداول ضمن النطاقات الطبيعية المستقرة حالياً.")
            
        st.markdown("---")

        # --- عرض لوحة فحص المؤشرات الرئيسية مع الاسم وحالة السوق ---
        st.subheader("📌 لوحة فحص المؤشرات اللحظية الأساسية")
        st.markdown(f"### 🏢 الشركة: <span style='color:#1E88E5;'>{company_long_name} ({ticker_resolved})</span>", unsafe_allow_html=True)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric(label=f"السعر الحالي ({currency})", value=f"{current_price:.2f}", delta=f"{price_change:.2f}%")
        with col_m2:
            st.markdown(f"**حالة توقيت البورصة:**\n\n`{market_status_text}`")
        with col_m3:
            st.markdown(f"**الاتجاه الفني الحالي:**\n\n<span style='color:{dir_color}; font-size:18px; font-weight:bold;'>{stock_direction}</span>", unsafe_allow_html=True)
        with col_m4:
            st.metric("حجم سيولة الشمعة الأخيرة", f"{liquidity_value:,.0f} {currency}")
        
        try:
            float_shares = info_data.get("floatShares", info_data.get("sharesOutstanding", 0))
            st.caption(f"الأسهم المتاحة للتداول (Float Shares): {float_shares:,.0f}" if float_shares else "الأسهم المتاحة للتداول: يتم تحديثها دورياً من البورصة")
        except:
            st.caption("الأسهم المتاحة للتداول: يتم تحديثها دورياً من البورصة")
            
        st.markdown("---")
        
        # عرض مناطق الدخول ونصائح التداول
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
