import os
import requests
import streamlit as st
import openai

# Set your API keys from Streamlit secrets
NEWS_API_KEY = st.secrets["news_api_key"]
OPENAI_API_KEY = st.secrets["openai_api_key"]
openai.api_key = OPENAI_API_KEY

# Function to fetch news
def fetch_news(keyword):
    # Fetch top headlines related to science and technology with a keyword filter
    url = f'https://newsapi.org/v2/top-headlines?q={keyword},science,technology&apiKey={NEWS_API_KEY}'
    
    try:
        response = requests.get(url, timeout=10)  # Set a timeout of 10 seconds
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.Timeout:
        st.error("The request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return None

# Function to generate summary and translate using ChatGPT
def generate_summary_and_translate(text, target_language):
    prompt = f"Summarize the following article and translate it to {target_language}:\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# Streamlit application
st.title("News Digest Tool")

# Input for keyword filtering
keyword = st.text_input("Enter a keyword to filter articles:")

# Major languages from SEA and India
target_language = st.selectbox("Select Language:", [
    "zh",  # Chinese
    "ja",  # Japanese
    "ko",  # Korean
    "id",  # Indonesian
    "th",  # Thai
    "vi",  # Vietnamese
    "ms",  # Malay
    "tl",  # Filipino (Tagalog)
    "hi"   # Hindi
])  

if st.button("Get News Digest"):
    if keyword:
        with st.spinner("Fetching news..."):
            news_data = fetch_news(keyword)
        
        if news_data and news_data.get('articles'):
            summaries = []
            for article in news_data['articles']:
                if article.get('content'):  # Ensure content is available
                    # Pre-translated result
                    pre_translated = article['content']
                    
                    with st.spinner("Generating summaries and translations..."):
                        # Generate AI summary and translated result
                        summary = generate_summary_and_translate(article['content'], target_language)
                        
                        # Store results
                        summaries.append({
                            'title': article['title'],
                            'pre_translated': pre_translated,
                            'translated': summary
                        })
            
            if summaries:
                st.subheader("Summaries")
                for summary in summaries:
                    st.markdown(f"**{summary['title']}**")
                    st.write("**Pre-Translated Result:**")
                    st.write(summary['pre_translated'])
                    st.write("**Translated Result:**")
                    st.write(summary['translated'])
                    st.write("**AI Summary:**")
                    st.write(summary['translated'])  # Assuming the translated result is the summary
            else:
                st.write("No summaries generated.")
        else:
            st.write("No articles found.")
    else:
        st.warning("Please enter a keyword to filter articles.")
