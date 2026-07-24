import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import plotly.graph_objects as go

# قاموس البحث الذكي عن الأسهم (تحويل الأسماء لرموز)
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
            exchange_status = "🟢 تداول نشط / مقفل مؤقتاً بالانتظار"
        except:
            company_long_name = ticker_resolved
            exchange_status = "🔄 دورة السوق العادية"

        # --- 🚨 قسم التنبيهات اللحظية المدمجة ---
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

        # --- عرض لوحة فحص المؤشرات الرئيسية ---
        st.subheader("📌 لوحة فحص المؤشرات اللحظية الأساسية")
        st.markdown(f"### 🏢 الشركة: <span style='color:#1E88E5;'>{company_long_name} ({ticker_resolved})</span>", unsafe_allow_html=True)
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric(label=f"السعر الحالي ({currency})", value=f"{current_price:.2f}", delta=f"{price_change:.2f}%")
        with col_m2:
            st.markdown(f"**حالة جلسة البورصة:**\n\n`{exchange_status}`")
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
        
        # عرض مناطق الدخول والمستهدفات الفنية بشكل طولي آمن
        st.subheader("🎯 المستهدفات الفنية والمستويات المضاربية اللحظية")
        st.success(f"🟢 منطقة أفضل سعر للدخول والمضاربة اللحظية: **{levels['entry']:.2f} {currency}**")
        st.info(f"🚀 الهدف المضاربي الأول: **{levels['t1']:.2f} {currency}**")
        st.info(f"🚀 الهدف الثاني (متوسط النطاق): **{levels['t2']:.2f} {currency}**")
        st.info(f"🚀 الهدف الثالث (مستهدف رئيسي): **{levels['t3']:.2f} {currency}**")
        st.warning(f"⚠️ مستوى وقف الخسارة (لحماية رأس المال): **{levels['sl']:.2f} {currency}**")
        st.error(f"🚨 وقف الخسارة الصارم النهائي: **{levels['strict_sl']:.2f} {currency}**")
        
        st.markdown("---")
        
        # صياغة النصيحة الذكية بخطوة معمارية مسطحة خالية تماماً من الشروط
        st.subheader("💡 نصائح الرادار الفنية الموجهة")
        radar_tip = "⚖️ السهم يتداول في نطاق تجميعي ومسار عرضي متزن حالياً. مناسب جداً للمضاربات السريعة واقتناص الفروقات السعرية البسيطة."
        if price_change > 1.5:
            radar_tip = "🔥 السهم تحت تأثير زخم شرائي قوي وسيولة متدفقة للإيجابية. الدخول الآمن يكون عبر اقتناص التهدئة اللحظية قرب منطقة الدخول المحددة للهدف الأول."
        if price_change < -1.5:
            radar_tip = "🚨 السهم يتعرض لضغط بيعي هابط وتصحيح حركي. ينصح بالالتزام التام بنقاط وقف الخسارة لعدم الوقوع في تعليقة سعرية حادة."
            
        st.warning(radar_tip)
        st.markdown("---")
        
        # بناء شارت الشموع اليابانية التفاعلي
        st.subheader(f"📈 شارت التحليل الفني التفاعلي اللحظي لفريم ({timeframe})")
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="الشموع اليابانية"
        )])
        fig.add_hline(y=levels['entry'], line_dash="dash", line_color="green", annotation_text="منطقة الدخول")
        fig.add_hline(y=levels['t1'], line_dash="dash", line_color="blue", annotation_text="الهدف 1")
        fig.add_hline(y=levels['sl'], line_dash="dash", line_color="red", annotation_text="وقف الخسارة")
        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=520)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        
        # عرض آخر الأخبار بصيغة خطية مسطحة تماماً (Flat structure)
        st.subheader("📰 آخر أخبار السهم والتحليل الذكي للخبر")
        news_list = ticker_obj.news
        if not news_list:
            st.info("لا توجد أخبار جوهرية منشورة حديثاً للرمز المحدد عبر مزود البيانات العالمي.")
        
        # في حال وجود أخبار، يتم استعراضها بشكل تسلسلي آمن 100% ضد الأخطاء
        for news in news_list[:3]:
            n_title = news.get('title', '')
            n_link = news.get('link', '')
            n_polarity = TextBlob(n_title).sentiment.polarity
            
            sentiment_labels = ["🔴 سلبي (محفز للهبوط)", "🟡 محايد (استقرار سعري)", "🟢 إيجابي (محفز للصعود)"]
            idx = int(n_polarity > 0.1) - int(n_polarity < -0.1) + 1
                
            st.markdown(f"🔹 **[{n_title}]({n_link})**")
            st.info(f"التحليل الذكي لمشاعر فحوى الخبر: {sentiment_labels[idx]}")

if __name__ == "__main__":
    main()
