import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
from textblob import TextBlob
import json

# Global Styling for Full-Page Occupancy
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
        body { background-color: #f4f4f4; color: #333; }
        .main { background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
        h1 { color: #2a9d8f; font-size: 3em; text-align: center; }
        .stButton button { background: #2a9d8f; color: #fff; border-radius: 8px; padding: 12px 20px; width: 100%; }
        .stDataFrame { border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True
)

# UI Layout
st.title("📚 Book Insights Scraper")

# User input
url = st.text_input("Enter URL:", "https://books.toscrape.com/catalogue/category/books_1/index.html")
if not url.strip():
    st.warning("⚠️ Please enter a valid URL to proceed.")
    st.stop()

# Initialize session state
data_key = "book_data"
if data_key not in st.session_state:
    st.session_state[data_key] = None

# Scrape button
if st.button("🚀 Scrape Data"):
    try:
        with st.spinner("Scraping book data... please wait!"):
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            books = []
            for book in soup.find_all('article', class_='product_pod'):
                try:
                    title = book.h3.a['title']
                    price_elem = book.find('p', class_='price_color')
                    availability_elem = book.find('p', class_='instock availability')
                    rating_elem = book.p.get("class", [])

                    price = float(price_elem.get_text(strip=True).replace('£', '')) if price_elem else None
                    availability = availability_elem.get_text(strip=True) if availability_elem else "Unknown"
                    rating = rating_elem[1] if len(rating_elem) > 1 else "Not Rated"

                    sentiment = TextBlob(title).sentiment.polarity
                    sentiment_label = 'Positive' if sentiment > 0 else 'Neutral' if sentiment == 0 else 'Negative'

                    books.append([title, price, availability, rating, sentiment_label])
                except Exception as e:
                    st.warning(f"⚠️ Skipped a book due to an issue: {e}")

            if books:
                st.session_state[data_key] = pd.DataFrame(books, columns=['Title', 'Price (£)', 'Availability', 'Rating', 'Sentiment'])
                st.success("✅ Scraping completed successfully!")
            else:
                st.error("⚠️ No book data found on this page.")
    except requests.exceptions.RequestException as e:
        st.error(f"❗ Request error: {e}")
    except Exception as e:
        st.error(f"❗ An unexpected error occurred: {e}")

# Display Data
if st.session_state[data_key] is not None:
    st.markdown("### 📘 Scraped Book Data")
    search_query = st.text_input("🔍 Search books by title:", "").strip().lower()
    
    filtered_data = (
        st.session_state[data_key][st.session_state[data_key]['Title'].str.lower().str.contains(search_query, na=False)]
        if search_query else st.session_state[data_key]
    )

    st.dataframe(filtered_data, use_container_width=True)
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download CSV", data=filtered_data.to_csv(index=False).encode('utf-8'), 
                           file_name="book_data.csv", mime="text/csv")
    with col2:
        st.download_button("📥 Download JSON", data=json.dumps(filtered_data.to_dict(orient='records')), 
                           file_name="book_data.json", mime="application/json")

    # Charts Section
    if not filtered_data.empty:
        st.markdown("## 📊 Data Visualization")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💲 Price Distribution")
            fig_price = px.histogram(filtered_data, x='Price (£)', nbins=10, color_discrete_sequence=['#2a9d8f'])
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            st.markdown("### 📌 Sentiment Analysis")
            fig_sentiment = px.pie(filtered_data, names='Sentiment', color_discrete_sequence=['#2a9d8f', '#e9c46a', '#e76f51'])
            st.plotly_chart(fig_sentiment, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("### ⭐ Rating Breakdown")
            fig_rating = px.bar(filtered_data, x='Rating', color='Rating', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_rating, use_container_width=True)
        
        with col4:
            st.markdown("### 📦 Availability Breakdown")
            fig_availability = px.pie(filtered_data, names='Availability', color_discrete_sequence=['#2a9d8f', '#e76f51'])
            st.plotly_chart(fig_availability, use_container_width=True)

# Clear button
if st.button("🔄 Clear Data"):
    st.session_state[data_key] = None
    st.rerun()