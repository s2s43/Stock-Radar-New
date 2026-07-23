import streamlit as st
import yfinance as yf
import pandas as pd
from textblob import TextBlob
import datetime

# ==========================================
# 1. دالة جلب البيانات والتحقق الذكي من السوق
# ==========================================
def get_stock_data(ticker_symbol, market_type):
    """جلب بيانات السهم الحالية والتاريخية بناءً على نوع السوق"""
    if market_type == "السوق السعودي (تداول) 🇸🇦":
        ticker_clean = ticker_symbol.strip()
        if not ticker_clean.endswith(".SR"):
            ticker_clean = f"{ticker_clean}.SR"
    else:
        ticker_clean = ticker_symbol.upper().strip()
        
    try:
        ticker = yf.Ticker(ticker_clean)
        hist = ticker.history(period="5d")  # جلب بيانات كافية لحساب التغيرات
        if hist.empty:
            return None, None, "⚠️ لم يتم العثور على بيانات لهذا الرمز. تأكد من صحة المدخلات."
        return hist, ticker, None
    except Exception as e:
        return None, None, f"❌ حدث خطأ أثناء الاتصال بمزود البيانات: {str(e)}"

# ==========================================
# 2. دالة جلب وتحليل الأخبار الذكية (Sentiment)
# ==========================================
def fetch_and_analyze_news(ticker_obj):
    """جلب الأخبار الحية وتحليل المشاعر (إيجابي/سلبي/محايد)"""
    try:
        news_list = ticker_obj.news
        if not news_list:
            return None
            
        analyzed_news = []
        for item in news_list[:5]:  # تحليل آخر 5 أخبار فقط للسرعة
            title = item.get('title', '')
            publisher = item.get('publisher', '')
            link = item.get('link', '')
            
            # تحليل المشاعر باستخدام TextBlob (يدعم الإنجليزية بشكل أساسي)
            analysis = TextBlob(title)
            polarity = analysis.sentiment.polarity
            
            if polarity > 0.1:
                sentiment = "🟢 إيجابي (صعود محتمل)"
            elif polarity < -0.1:
                sentiment = "🔴 سلبي (هبوط محتمل)"
            else:
                sentiment = "🟡 محايد (استقرار)"
                
            analyzed_news.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "sentiment": sentiment
            })
        return analyzed_news
    except:
        return None

# ==========================================
# 3. دالة فحص التنبيهات (Price & Volatility)
# ==========================================
def check_alerts(hist_data, target_price, volatility_threshold):
    """فحص تنبيهات السعر وحجم التقلبات اللحظية"""
    if hist_data is None or len(hist_data) < 2:
        return ["⚠️ بيانات السعر غير كافية لإجراء الفحص اللحظي."]
        
    current_price = hist_data['Close'].iloc[-1]
    prev_price = hist_data['Close'].iloc[-2]
    
    # حساب نسبة التغير اللحظي
    price_change = (current_price - prev_price) / prev_price
    alerts = []
    
    # 1. تنبيه السعر المستهدف
    if current_price >= target_price:
        alerts.append(f"🎯 **تنبيه السعر المستهدف:** تخطى السهم السعر المحدد ({target_price:.2f})، السعر الحالي الآن هو **{current_price:.2f}**.")
        
    # 2. تنبيه التقلب الحاد (Volatility Alert)
    if abs(price_change) >= volatility_threshold:
        direction = "ارتفاع 📈" if price_change > 0 else "انخفاض 📉"
        alerts.append(f"⚡ **تنبيه تقلبات حادة:** شهد السهم {direction} مفاجئ بنسبة **{price_change*100:.2f}%** مقارنة بالإغلاق السابق.")
        
    return alerts

# ==========================================
# 4. بناء واجهة مستخدم Streamlit الرئيسية
# ==========================================
def main():
    st.set_page_config(page_title="Stock Radar - رادار الأسهم الذكي", layout="wide")
    
    st.title("📊 رادار الأسهم الذكي (Stock Radar)")
    st.markdown("منصة ذكية لمراقبة الأسعار، كشف التقلبات الحادة، وتحليل مشاعر الأخبار الحية.")
    
    # --- شريط التحكم الجانبي ---
    st.sidebar.header("⚙️ إعدادات الرادار والمراقبة")
    
    market_choice = st.sidebar.selectbox(
        "اختر السوق المستهدف:", 
        ["السوق الأمريكي 🇺🇸", "السوق السعودي (تداول) 🇸🇦"]
    )
    
    if market_choice == "السوق الأمريكي 🇺🇸":
        ticker_input = st.sidebar.text_input("أدخل رمز السهم الأمريكي (مثال: AAPL, TSLA):", value="AAPL").upper().strip()
        currency = "$"
    else:
        ticker_input = st.sidebar.text_input("أدخل رقم السهم السعودي (مثال: 1120, 2222):", value="1120").strip()
        currency = "ر.س"
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔔 إعدادات التنبيهات اللحظية")
    
    # جلب السعر الافتراضي لتهيئة الخانات بشكل صحيح عند التغيير
    target_price = st.sidebar.number_input(f"السعر المستهدف للتنبيه ({currency}):", min_value=0.0, value=150.0)
    volatility_limit = st.sidebar.slider("حد التقلب المفاجئ المسموح به (%):", min_value=1.0, max_value=10.0, value=3.0) / 100

    trigger_radar = st.sidebar.button("تشغيل رادار الفحص اللحظي", use_container_width=True)

    # --- تشغيل ومعالجة البيانات عند الضغط على الزر ---
    if trigger_radar:
        with st.spinner("جاري الاتصال بقواعد البيانات وفحص السهم..."):
            hist, ticker_obj, error = get_stock_data(ticker_input, market_choice)
            
            if error:
                st.error(error)
                return
                
            current_price = hist['Close'].iloc[-1]
            
            # عرض بطاقة السعر الحالية
            st.metric(label=f"السعر الحالي للسهم ({ticker_input})", value=f"{current_price:.2f} {currency}")
            
            # إنشاء أعمدة لعرض النتائج بشكل منظم ومريح للعين
            col1, col2 = st.columns(2)
            
            # العمود الأول: نظام التنبيهات واختراق الأسعار
            with col1:
                st.subheader("🔔 لوحة التنبيهات الفورية (Alerts)")
                active_alerts = check_alerts(hist, target_price, volatility_limit)
                
                if active_alerts:
                    for alert in active_alerts:
                        st.warning(alert)
                else:
                    st.success("✅ حالة السعر مستقرة وتحت حد التقلبات المعين حالياً.")
            
            # العمود الثاني: الأخبار وتحليل المشاعر الذكي
            with col2:
                st.subheader("📰 آخر أخبار السهم والتحليل الذكي للخبر")
                news_data = fetch_and_analyze_news(ticker_obj)
                
                if news_data:
                    for news in news_data:
                        st.markdown(f"🔹 **[{news['title']}]({news['link']})**")
                        st.caption(f"الناشر: {news['publisher']}")
                        st.info(f"تحليل الذكاء الاصطناعي للخبر: {news['sentiment']}")
                        st.markdown("---")
                else:
                    st.info("ℹ️ لا توجد أخبار حديثة متوفرة لهذا الرمز حالياً عبر المزود.")

if __name__ == "__main__":
    main() 





