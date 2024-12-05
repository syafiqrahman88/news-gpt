import streamlit as st
import openai
import requests
import os
import re  # Import regex module
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO  # Import BytesIO for in-memory file handling

# Check if running locally or on Streamlit Sharing
if "STREAMLIT_SERVER" in os.environ:
    # Access your API keys directly from Streamlit secrets
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    news_api_key = st.secrets["NEWS_API_KEY"]
else:
    # Load environment variables from .env file for local development
    from dotenv import load_dotenv
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    news_api_key = os.getenv("NEWS_API_KEY")

# Language options for translation
languages = {
    'bn': 'Bengali',
    'my': 'Burmese',
    'zh': 'Chinese',
    'hi': 'Hindi',
    'id': 'Indonesian',
    'ja': 'Japanese',
    'km': 'Khmer',
    'ko': 'Korean',
    'lo': 'Lao',
    'ms': 'Malay',
    'ta': 'Tamil',
    'th': 'Thai',
    'vi': 'Vietnamese'
}

# Function to register fonts based on language
def register_font(language):
    if language == 'zh':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansSC-VariableFont_wght.ttf'))  # Use Noto Sans SC
    elif language == 'ja':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansJP-VariableFont_wght.ttf'))  # Use Noto Sans JP
    elif language == 'ko':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansKR-VariableFont_wght.ttf'))  # Use Noto Sans KR
    elif language == 'vi':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSans-VariableFont_wdth,wght.ttf'))  # Use Noto Sans for Vietnamese
    elif language == 'th':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansThai-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Thai
    elif language in ['id', 'ms']:
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSans-VariableFont_wdth,wght.ttf'))  # Use Noto Sans for Indonesian and Malay
    elif language == 'my':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansMyanmar-Regular.ttf'))  # Use Noto Sans Myanmar
    elif language == 'km':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansKhmer-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Khmer
    elif language == 'lo':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansLao-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Lao
    elif language == 'hi':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansDevanagari-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Devanagari
    elif language == 'bn':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansBengali-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Bengali
    elif language == 'ta':
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSansTamil-VariableFont_wdth,wght.ttf'))  # Use Noto Sans Tamil
    else:
        pdfmetrics.registerFont(TTFont('NotoSans', 'fonts/NotoSans-VariableFont_wdth,wght.ttf'))  # Fallback to Noto Sans

def strip_markdown(text):
    """Remove Markdown formatting from the given text."""
    stripped_text = re.sub(r'\*\*(.*?)\*\*|__(.*?)__|\*(.*?)\*|_(.*?)_', r'\1\2\3\4', text)
    return stripped_text.strip()

def translate_and_summarize(content, title, target_language):
    """Translate the content and title to the target language and summarize using OpenAI's API."""
    
    # Enhanced prompt design to ensure bullet points are in the target language
    prompt = (
        f"Please summarize the following article in one to four concise bullet points in {target_language}:\n\n"
        f"{content}\n\n"
        f"Make sure to always give bullet points."
        f"Translate the title and body of the article into {target_language}.\n\n"
        f"Title: {title}\n"
        f"Body: {content}\n\n"
        f"Format the output as follows:\n"
        f"Summary in {target_language}:\n"
        f"- Bullet one\n"
        f"- Bullet two\n"
        f"- Bullet three\n"
        f"- Bullet four\n\n"
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

def analyze_sentiment(title, body):
    """Analyze the sentiment of the title and body using OpenAI's API."""
    
    prompt = (
        f"Analyze the sentiment of the following news article and classify it as Positive, Negative, or Neutral:\n\n"
        f"Title: {title}\n"
        f"Body: {body}\n\n"
        f"Output only the sentiment classification."
    )
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        st.error(f"Error during sentiment analysis: {e}")
        return None

def create_pdf(original_title, translated_title, summary, sentiment, url, language):
    """Create a PDF file with the given content."""
    buffer = BytesIO()  # Create a BytesIO buffer
    c = canvas.Canvas(buffer, pagesize=letter)

    # Register the appropriate font for the language
    register_font(language)
    c.setFont("NotoSans", 16)  # Use the registered font

    # Set up the title (hyperlinked)
    c.drawString(72, 720, original_title)  # Original Title
    c.linkURL(url, (72, 720, 500, 740), relative=1)  # Hyperlink

    # Set translated title
    c.setFont("NotoSans", 12)
    c.drawString(72, 680, translated_title)  # Translated Title

    # Add AI-generated summary
    c.setFont("NotoSans", 12)
    c.drawString(72, 640, "AI-Generated Summary:")
    y_position = 620
    for bullet in summary:
        c.drawString(72, y_position, f"- {bullet.strip()}")
        y_position -= 20  # Move down for the next bullet

    # Add sentiment analysis
    c.setFont("NotoSans", 14)
    c.drawString(72, y_position, "Sentiment Analysis:")
    c.setFont("NotoSans", 12)
    c.drawString(72, y_position - 20, sentiment)  # Sentiment value

    # Save the PDF to the buffer
    c.save()
    buffer.seek(0)  # Move to the beginning of the BytesIO buffer
    return buffer

# Set the title of the app
st.title("News GPT Application")

# Initialize session state for articles and translations if they don't exist
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'translated_content' not in st.session_state:
    st.session_state.translated_content = {}
if 'articles_fetched' not in st.session_state:
    st.session_state.articles_fetched = False  # Flag to track if articles have been fetched

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
                        {"keyword": query},  # Broad keyword like "technology"
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
                    st.session_state.articles_fetched = True  # Set the flag to True after fetching
                else:
                    st.error("No articles found in the response or response format is incorrect.")
                    st.session_state.articles = []  # Set articles to an empty list to avoid further errors

            except ValueError:
                st.error("Failed to decode JSON response.")
                st.write("Response Content:", response.content)  # Use content for debugging

# Create a container for Original Articles
with st.container():
    if st.session_state.articles_fetched:
        st.header("Original Articles")
        if st.session_state.articles:
            for index, article in enumerate(st.session_state.articles):  # Use session state
                # Ensure article is a dictionary before accessing its keys
                if isinstance(article, dict):
                    title = article.get('title', 'No Title')
                    body = article.get('body', 'No Description')  # Use 'body' for description
                    url = article.get('url', '#')

                    # Display article information using st.caption
                    st.subheader(title)
                    st.caption(body)  # Use st.caption to display without Markdown parsing
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
                            title = article.get('title', 'No Title')  # Use original title
                            body = article.get('body', 'No Description')  # Use original body
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
                            st.subheader("AI-Generated Summary:")
                            for bullet in summary:
                                st.write(f"- {bullet.strip()}")
                            st.subheader("Translated Title:")
                            st.write(translated_title)
                            st.subheader("Translated Content:")
                            st.write(translated_body)

                            # Perform sentiment analysis on the original title and body
                            sentiment = analyze_sentiment(title, body)

                            # Determine the color based on sentiment
                            sentiment_color = {
                                "Positive": "green",
                                "Negative": "red",
                                "Neutral": "gray"
                            }.get(sentiment, "gray")  # Default to gray if sentiment is not recognized

                            # Display sentiment result with color formatting using HTML
                            st.markdown(f"<h3>AI-Generated Sentiment: <span style='color: {sentiment_color};'>{sentiment}</span></h3>", unsafe_allow_html=True)

                            # Add a button to download as PDF
                            if st.button("Download as PDF"):
                                pdf_output = create_pdf(title, translated_title, summary, sentiment, url, selected_language)
                                st.download_button("Download PDF", pdf_output, f"{title}.pdf", "application/pdf")
                else:
                    st.warning("Article format is not as expected.")
        else:
            st.warning("No articles found for your query.")
    else:
        st.info("Please input a keyword or phrase into the Search Query and hit 'Fetch Articles'.")