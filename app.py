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
    # Fetch top headlines based on the keyword
    url = f'https://newsapi.org/v2/top-headlines?q={keyword}&apiKey={NEWS_API_KEY}'
    
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

# Create a two-column layout
col1, col2 = st.columns(2)

# Left column for keyword input and original articles
with col1:
    keyword = st.text_input("Enter a keyword to filter articles:")
    if st.button("Get News Digest"):
        if keyword:
            with st.spinner("Fetching news..."):
                news_data = fetch_news(keyword)
            
            if news_data:
                if 'articles' in news_data and news_data['articles']:
                    # Display original articles
                    st.subheader("Original Articles")
                    for article in news_data['articles']:
                        st.markdown(f"**{article['title']}**")
                        st.write(article['content'])
                else:
                    st.write("No articles found for the given keyword.")
            else:
                st.write("No data returned from the API.")
        else:
            st.warning("Please enter a keyword to filter articles.")

# Right column for language selection and translation
with col2:
    st.subheader("Translate and Summarize")
    languages = {
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "id": "Indonesian",
        "th": "Thai",
        "vi": "Vietnamese",
        "ms": "Malay",
        "tl": "Filipino (Tagalog)",
        "hi": "Hindi"
    }
    
    # Create a button for each language
    for lang_code, lang_name in languages.items():
        if st.button(f"Translate to {lang_name}"):
            with st.spinner(f"Translating to {lang_name}..."):
                summaries = []
                for article in news_data['articles']:
                    if article.get('content'):  # Ensure content is available
                        # Generate AI summary and translated result
                        summary = generate_summary_and_translate(article['content'], lang_code)
                        summaries.append({
                            'title': article['title'],
                            'translated': summary
                        })
                
                # Display translated results
                st.subheader(f"Translated Articles in {lang_name}")
                for summary in summaries:
                    st.markdown(f"**{summary['title']}**")
                    st.write(summary['translated'])
