import os
import requests
import streamlit as st
import openai

# Set your API keys from Streamlit secrets
NEWS_API_KEY = st.secrets["news_api_key"]  # Accessing the key from Streamlit secrets
OPENAI_API_KEY = st.secrets["openai_api_key"]  # Accessing the key from Streamlit secrets
openai.api_key = OPENAI_API_KEY

# Function to fetch news
def fetch_news(query):
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching news: {response.status_code} - {response.text}")
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

query = st.text_input("Enter news topic:")
target_language = st.selectbox("Select Language:", ["es", "fr", "de"])  # Add more languages as needed

if st.button("Get News Digest"):
    if query:
        news_data = fetch_news(query)
        
        if news_data and news_data.get('articles'):
            summaries = []
            for article in news_data['articles']:
                if article.get('content'):  # Ensure content is available
                    summary = generate_summary_and_translate(article['content'], target_language)
                    summaries.append({
                        'title': article['title'],
                        'summary': summary
                    })
            
            if summaries:
                st.subheader("Summaries")
                for summary in summaries:
                    st.markdown(f"**{summary['title']}**")
                    st.write(summary['summary'])
            else:
                st.write("No summaries generated.")
        else:
            st.write("No articles found.")
    else:
        st.warning("Please enter a news topic.")
