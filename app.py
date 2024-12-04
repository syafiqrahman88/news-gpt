import streamlit as st
import openai
import requests
import os
import re  # Import regex module

# Load environment variables from .env file (only for local development)
load_dotenv()

# Access your API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
news_api_key = os.getenv("NEWS_API_KEY")

# Language options for translation
languages = {
    'zh': 'Simplified Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'id': 'Indonesian',
    'ms': 'Malay',
    'my': 'Burmese',
    'km': 'Khmer',
    'lo': 'Lao',
    'hi': 'Hindi',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'ur': 'Urdu'
}

def strip_markdown(text):
    """Remove Markdown formatting from the given text."""
    # Remove bold and italic formatting
    stripped_text = re.sub(r'\*\*(.*?)\*\*|__(.*?)__|\*(.*?)\*|_(.*?)_', r'\1\2\3\4', text)
    return stripped_text.strip()

def translate_and_summarize(content, title, target_language):
    """Translate the content and title to the target language and summarize using OpenAI's API."""
    
    # Enhanced prompt design to ensure bullet points are in the target language
    prompt = (
        f"Summarize the following article in four concise bullet points in {target_language} without formatting them as bullet points:\n\n"
        f"{content}\n\n"
        f"Translate the title and body of the article into {target_language}.\n\n"
        f"Title: {title}\n"
        f"Body: {content}\n\n"
        f"Format the output as follows:\n"
        f"Summary in {target_language}:\n"
        f"- Point one\n"
        f"- Point two\n"
        f"- Point three\n"
        f"- Point four\n\n"
        f"Translated Title: <translated title>\n"
        f"Translated Content: <translated content>"
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # Switch to GPT-4 for advanced language capabilities
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        st.error(f"Error during translation and summarization: {e}")
        return None

# Set the title of the app
st.title("News GPT Application")

# Initialize session state for articles and translations if they don't exist
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'translated_content' not in st.session_state:
    st.session_state.translated_content = {}

# Sidebar for user input
st.sidebar.header("User Input")

# Input field for search query
query = st.sidebar.text_input("Search Query", "")
days = st.sidebar.number_input("Days Back", min_value=1, max_value=30, value=1)

# Button to fetch articles
if st.sidebar.button("Fetch Articles"):
    if query:
        # Fetch articles from Event Registry API
        url = "https://eventregistry.org/api/v1/article/getArticles"
        
        # Set parameters based on your use case
        params = {
            "apiKey": news_api_key,
            "query": {
                "$query": {
                    "$and": [
                        {"keyword": query},  # Input from the user
                        {"keyword": "semiconductor"},  # Industry-specific keyword
                        {"keyword": "materials engineering"}  # Additional context
                    ]
                }
            },
            "days": days,  # Input from the user
            "resultType": "articles",
            "articlesPage": 1,
            "articlesCount": 10,  # Fetch more articles initially
            "articlesSortBy": "relevance",  # Sort by relevance
            "articlesSortByAsc": False
        }
        
        response = requests.get(url, json=params)

        # Check for HTTP errors
        if response.status_code != 200:
            st.error(f"Error fetching articles: {response.status_code}")
            st.write("Response Content:", response.content)  # Use content for debugging
        else:
            # Try to parse the JSON response
            try:
                response_json = response.json()

                # Access the articles from the nested structure
                if 'articles' in response_json and 'results' in response_json['articles']:
                    # Filter for English articles
                    articles = response_json['articles']['results']
                    # Strip Markdown from the article content
                    for article in articles:
                        article['title'] = strip_markdown(article.get('title', ''))
                        article['body'] = strip_markdown(article.get('body', ''))

                    st.session_state.articles = [article for article in articles if article.get('lang') == 'eng']
                else:
                    st.error("No articles found in the response or response format is incorrect.")
                    st.session_state.articles = []  # Set articles to an empty list to avoid further errors

            except ValueError:
                st.error("Failed to decode JSON response.")
                st.write("Response Content:", response.content)  # Use content for debugging

# Create a container for Original Articles
with st.container():
    st.header("Original Articles")
    if st.session_state.articles:
        for index, article in enumerate(st.session_state.articles):  # Use session state
            # Ensure article is a dictionary before accessing its keys
            if isinstance(article, dict):
                title = article.get('title', 'No Title')
                body = article.get('body', 'No Description')  # Use 'body' for description
                url = article.get('url', '#')

                # Display article information using st.text
                st.subheader(title)
                st.text(body)  # Use st.text to display without Markdown parsing
                st.write(f"[Read more]({url})")

                # Language translation dropdown with a unique key
                selected_language = st.selectbox(
                    "Translate and Summarize to:",
                    list(languages.values()),
                    key=f"language_selectbox_{index}"  # Unique key using index
                )

                # Check if translation has already occurred
                if f"translated_{index}" not in st.session_state:
                    st.session_state[f"translated_{index}"] = None

                # Button to translate and summarize the content when a language is selected
                if st.button("Translate and Summarize", key=f"translate_button_{index}"):
                    if selected_language:
                        # Call the translation and summarization function
                        translated_content = translate_and_summarize(body, title, selected_language)  # Use body for translation
                        # Store the translated content in session state
                        st.session_state[f"translated_{index}"] = translated_content  # Store in session state
                
                # Expander for translated content
                with st.expander("Show Translated Content", expanded=False):
                    if st.session_state[f"translated_{index}"]:
                        # Check if the response is a list and join it into a single string if necessary
                        translated_response = st.session_state[f"translated_{index}"]
                        
                        if isinstance(translated_response, list):
                            # Join the list into a single string
                            translated_response = "\n".join(translated_response)
                        
                        # Now you can safely split the string
                        lines = translated_response.split("\n")
                        summary = []
                        translated_title = ""
                        translated_body = ""

                        for line in lines:
                            if line.startswith("Summary in"):
                                # Extract summary lines that start with "-"
                                summary = [line.strip() for line in lines[lines.index(line) + 1:] if line.startswith("-")]
                            elif line.startswith("Translated Title:"):
                                translated_title = line.replace("Translated Title: ", "").strip()
                            elif line.startswith("Translated Content:"):
                                translated_body = line.replace("Translated Content: ", "").strip()

                        # Remove italics from the translated title and body
                        translated_title = strip_markdown(translated_title)
                        translated_body = strip_markdown(translated_body)

                        # Display the formatted output
                        st.subheader("Summary:")
                        for bullet in summary:
                            st.write(f"- {bullet.strip()}")
                        st.subheader("Translated Title:")
                        st.write(translated_title)
                        st.subheader("Translated Content:")
                        st.write(translated_body)
            else:
                st.warning("Article format is not as expected.")
    else:
        st.warning("No articles found for your query.")