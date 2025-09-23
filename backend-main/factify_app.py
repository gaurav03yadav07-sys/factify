import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from streamlit_extras.card import card
import requests
import joblib
import os
import sqlite3
import time

# --- Import your backend modules ---
# from Scrapper import extract_article_text
# from preprocess import clean_text
# from logger_db import init_db, log_query


@st.cache_data
def fetch_past_checks():
    # This function now reads from your actual, trimmed database
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT url, label, confidence, created_at FROM queries ORDER BY created_at DESC", conn)
    conn.close()
    return df

# Mock functions for demonstration (replace with your actual imports)
def extract_article_text(url):
    time.sleep(1)  # Simulate processing
    return "This is a sample extracted text from the URL for demonstration purposes."

def clean_text(text):
    return text.lower().strip()

# def init_db():
#     pass

# def log_query(source, label, confidence, text_length):
#     pass



# --- MODIFICATION 1: Use your actual database functions ---

DB_PATH = "queries.db"

def init_db():
    """Initializes the SQLite database and table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        label TEXT,
        confidence REAL,
        extracted_len INTEGER,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_query_and_trim(url, label, confidence, extracted_len):
    """
    Logs a new query and ensures only the 5 most recent entries are kept.
    This is the new, improved logging function.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Step 1: Insert the new record
    from datetime import datetime
    c.execute("INSERT INTO queries (url, label, confidence, extracted_len, created_at) VALUES (?, ?, ?, ?, ?)",
              (url, label, confidence, extracted_len, datetime.utcnow().isoformat()))
    
    # Step 2: Trim the database, keeping only the top 5 most recent records
    c.execute("""
    DELETE FROM queries
    WHERE id NOT IN (
        SELECT id FROM queries
        ORDER BY created_at DESC
        LIMIT 5
    )
    """)
    
    conn.commit()
    conn.close()



    












# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Factify",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Enhanced Theme Definition and CSS ---
def get_theme_css(theme):
    if theme == 'dark':
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            .stApp {
                background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
                color: #e1e5e9;
                font-family: 'Inter', sans-serif;
            }
            
            /* Header and text styling */
            h1, h2, h3, h4, h5, h6 {
                color: #ffffff !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em;
            }
 
            /* Main title styling */
            .main-title {
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                margin-bottom: 2rem;
                animation: glow 2s ease-in-out infinite alternate;
            }

            
            
            @keyframes glow {
                from { filter: drop-shadow(0 0 10px rgba(255, 149, 0, 0.3)); }
                to { filter: drop-shadow(0 0 20px rgba(255, 149, 0, 0.6)); }
            }
            
            /* Button styling */
            .stButton > button {
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 25px !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                padding: 0.6rem 1.5rem !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 4px 15px rgba(255, 149, 0, 0.3) !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(255, 149, 0, 0.4) !important;
                filter: brightness(1.1) !important;
            }
            
            .stButton > button:active {
                transform: translateY(0px) !important;
            }
            
            /* Input field styling */
            [data-testid="stTextInput"] > div > div > input,
            [data-testid="stTextArea"] > div > textarea {
                background: rgba(255, 255, 255, 0.05) !important;
                border: 2px solid #ff9500 !important;
                border-radius: 15px !important;
                color: #ffffff !important;
                font-size: 0.95rem !important;
                padding: 0.8rem !important;
                transition: all 0.3s ease !important;
                backdrop-filter: blur(10px) !important;
            }
            
            [data-testid="stTextInput"] > div > div > input:focus,
            [data-testid="stTextArea"] > div > textarea:focus {
                border-color: #ff6b35 !important;
                box-shadow: 0 0 20px rgba(255, 149, 0, 0.3) !important;
                transform: scale(1.02) !important;
            }
            
            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: #9ca3af !important;
                font-weight: 400 !important;
            }
            
            /* Result container styling */
            .result-container {
                background: linear-gradient(135deg, rgba(255, 149, 0, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
                border: 3px solid #ff9500;
                border-radius: 30px;
                padding: 2.5rem;
                text-align: center;
                margin: 2rem auto;
                backdrop-filter: blur(20px);
                animation: fadeInUp 0.6s ease-out;
                box-shadow: 0 10px 40px rgba(255, 149, 0, 0.2);
                max-width: 500px;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .result-label {
                font-size: 2rem !important;
                font-weight: 700 !important;
                margin-bottom: 1rem !important;
                text-transform: uppercase !important;
                letter-spacing: 1px !important;
            }
            
            .confidence-text {
                font-size: 1.8rem !important;
                font-weight: 600 !important;
                color: #ff9500 !important;
                text-shadow: 0 0 20px rgba(255, 149, 0, 0.5) !important;
            }
            
            /* Tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 1rem;
                background: transparent;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: rgba(255, 255, 255, 0.05) !important;
                border-radius: 20px !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                padding: 1rem 2rem !important;
                transition: all 0.3s ease !important;
                backdrop-filter: blur(10px) !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 4px 15px rgba(255, 149, 0, 0.3) !important;
            }
            
            /* Cards and containers */
            .metric-card {
                background: linear-gradient(135deg, rgba(255, 149, 0, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
                border: 2px solid rgba(255, 149, 0, 0.3);
                border-radius: 20px;
                padding: 1.5rem;
                margin: 1rem 0;
                backdrop-filter: blur(20px);
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(255, 149, 0, 0.2);
            }
            
            /* Description text */
            .description-text {
                font-size: 1.1rem;
                line-height: 1.6;
                color: #b8c5d6;
                text-align: center;
                max-width: 800px;
                margin: 2rem auto;
                font-weight: 400;
            }
            
            /* Loading spinner customization */
            .stSpinner > div {
                border-top-color: #ff9500 !important;
                border-right-color: #ff9500 !important;
            }
            
            /* Toggle switch styling */
            .stCheckbox > label {
                background: rgba(255, 255, 255, 0.1) !important;
                border-radius: 20px !important;
                padding: 0.5rem 1rem !important;
                backdrop-filter: blur(10px) !important;
            }
        </style>
        """
    else:  # light theme
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                color: #1a202c;
                font-family: 'Inter', sans-serif;
            }
            
            /* Header and text styling */
            h1, h2, h3, h4, h5, h6 {
                color: #1a202c !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.02em;
            }
            
            /* Main title styling */
            .main-title {
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                margin-bottom: 2rem;
                animation: glow 2s ease-in-out infinite alternate;
            }
            
            @keyframes glow {
                from { filter: drop-shadow(0 0 10px rgba(255, 149, 0, 0.3)); }
                to { filter: drop-shadow(0 0 20px rgba(255, 149, 0, 0.6)); }
            }
            
            /* Button styling */
            .stButton > button {
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%) !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 25px !important;
                font-weight: 600 !important;
                font-size: 0.95rem !important;
                padding: 0.6rem 1.5rem !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 4px 15px rgba(255, 149, 0, 0.3) !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(255, 149, 0, 0.4) !important;
                filter: brightness(1.1) !important;
            }
            
            .stButton > button:active {
                transform: translateY(0px) !important;
            }
            
            /* Input field styling */
            [data-testid="stTextInput"] > div > div > input,
            [data-testid="stTextArea"] > div > textarea {
                background: rgba(255, 255, 255, 0.9) !important;
                border: 2px solid #ff9500 !important;
                border-radius: 15px !important;
                color: #1a202c !important;
                font-size: 0.95rem !important;
                padding: 0.8rem !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            }
            
            [data-testid="stTextInput"] > div > div > input:focus,
            [data-testid="stTextArea"] > div > textarea:focus {
                border-color: #ff6b35 !important;
                box-shadow: 0 0 20px rgba(255, 149, 0, 0.3) !important;
                transform: scale(1.02) !important;
            }
            
            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: #6b7280 !important;
                font-weight: 400 !important;
            }
            
            /* Result container styling */
            .result-container {
                background: rgba(255, 255, 255, 0.9);
                border: 3px solid #ff9500;
                border-radius: 30px;
                padding: 2.5rem;
                text-align: center;
                margin: 2rem auto;
                animation: fadeInUp 0.6s ease-out;
                box-shadow: 0 10px 40px rgba(255, 149, 0, 0.2);
                max-width: 500px;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .result-label {
                font-size: 3rem !important;
                font-weight: 800 !important;
                margin-bottom: 1rem !important;
                text-transform: uppercase !important;
                letter-spacing: 2px !important;
            }
            
            .confidence-text {
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                color: #ff9500 !important;
                text-shadow: 0 0 20px rgba(255, 149, 0, 0.5) !important;
            }
            
            /* Tab styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 1rem;
                background: transparent;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: rgba(255, 255, 255, 0.7) !important;
                border-radius: 20px !important;
                color: #1a202c !important;
                font-weight: 600 !important;
                padding: 1rem 2rem !important;
                transition: all 0.3s ease !important;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 4px 15px rgba(255, 149, 0, 0.3) !important;
            }
            
            /* Cards and containers */
            .metric-card {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(255, 149, 0, 0.3);
                border-radius: 20px;
                padding: 1.5rem;
                margin: 1rem 0;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(255, 149, 0, 0.2);
            }
            
            /* Description text */
            .description-text {
                font-size: 1.1rem;
                line-height: 1.6;
                color: #4a5568;
                text-align: center;
                max-width: 800px;
                margin: 2rem auto;
                font-weight: 400;
            }
            
            /* Loading spinner customization */
            .stSpinner > div {
                border-top-color: #ff9500 !important;
                border-right-color: #ff9500 !important;
            }
            
            /* Toggle switch styling */
            .stCheckbox > label {
                background: rgba(0, 0, 0, 0.05) !important;
                border-radius: 20px !important;
                padding: 0.5rem 1rem !important;
            }



          
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                color: #1a202c;
                font-family: 'Inter', sans-serif;
            }
            
            /* General text and headers */
            h1, h2, h3, h4, h5, h6 {
                color: #1a202c !important;
            }
            [data-testid="stWidgetLabel"] {
                color: #4a5568 !important;
                font-weight: 600 !important;
            }

            /* --- THIS IS THE FIX for the "Send Feedback" button --- */
            .stButton > button {
                background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%) !important;
                color: #ff9500  !important; /* White text for high contrast */
                border: none !important;
                border-radius: 25px !important;
                font-weight: 600 !important;
                text-transform: uppercase;
            }


            
            
            /* Input field styling */
            [data-testid="stTextInput"] > div > div > input,
            [data-testid="stTextArea"] > div > textarea {
                background: rgba(255, 255, 255, 0.9) !important;
                border: 2px solid #ff9500 !important;
                border-radius: 15px !important;
                color: #1a202c !important;
            }
            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {
                color: #6b7280 !important;
            }
        
        





        </style>
        """

# --- 3. Load Model and Initialize DB ---
MODEL_DIR = "model_artifacts"
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

@st.cache_resource
def load_model_and_vectorizer():
    # Mock loading for demonstration
    return "vectorizer", "model"
    # Uncomment below for actual implementation
    # if not os.path.exists(VECT_PATH) or not os.path.exists(MODEL_PATH):
    #     st.error("Model artifacts not found. Please run train.py first to create them.")
    #     st.stop()
    # vectorizer = joblib.load(VECT_PATH)
    # model = joblib.load(MODEL_PATH)
    # return vectorizer, model

vectorizer, model = load_model_and_vectorizer()
init_db()

# --- 4. Session State Initialization ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'selected_page' not in st.session_state:
    st.session_state.selected_page = "Home"


# if 'nav_request' in st.session_state:
#     # FIXED: These lines must be indented to be inside the 'if' block
#     st.session_state.selected_page = st.session_state.nav_request
#     del st.session_state.nav_request# Removed the extra period from this line



# Apply current theme CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)




# --- 5. Navigation and Theme Toggle ---
# Create navigation bar with theme toggle
nav_container = st.container()

with nav_container:
    # CHANGED: Replaced the three-column layout with a two-column layout
    # This gives the menu more space and pushes the toggle to the far right.
    menu_col, theme_col = st.columns([0.9, 0.1])
    
    with menu_col: # Placed the option_menu in the new, wider column
        options = ["Home", "Predict", "Past Checks", "About"]
        
        # This logic for handling navigation remains the same
        if 'force_navigation' in st.session_state:
            # ... (your existing navigation logic) ...
            pass
        else:
            default_index = options.index(st.session_state.get('selected_page', 'Home'))
        
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=["house-fill", "search-heart", "graph-up-arrow", "info-circle-fill"],
            menu_icon=None,
            default_index=default_index,
            orientation="horizontal",
            key="main_menu",
            styles={
                "container": {
                    "padding": "8px",
                    "background": "linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.95) 100%)",
                    "border-radius": "1px",
                    "box-shadow": "0 8px 32px rgba(0, 0, 0, 0.3)",
                    "backdrop-filter": "blur(20px)",
                    "border": "1px solid rgba(255, 149, 0, 0.2)",
                },
                "icon": {
                    "color": "#ff9500",
                    "font-size": "16px",
                },
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "center",
                    "margin": "2px",
                    "padding": "8px 16px",
                    "border-radius": "15px",
                    "font-weight": "600",
                    "transition": "all 0.3s ease",
                    "color": "#ffffff",
                    "background": "transparent",
                    "--hover-color": "rgba(255, 149, 0, 0.15)",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #ff6b35 0%, #ff9500 100%)",
                    "color": "#ffffff",
                    "box-shadow": "0 4px 15px rgba(255, 149, 0, 0.4)",
                    "transform": "translateY(-1px)",
                    "font-weight": "700",
                },
            }
        )
        
        # This logic for handling navigation remains the same
        if selected != st.session_state.get('selected_page', 'Home'):
            st.session_state.selected_page = selected
            st.rerun()
    
    with theme_col: # Placed the theme toggle in the second, smaller column
        st.markdown("<div style='padding-top: 8px; text-align: center;'>", unsafe_allow_html=True)
        theme_emoji = "🌙" if st.session_state.get('theme', 'light') == 'light' else "☀️"
        theme_help = "Switch to Dark Mode" if st.session_state.get('theme', 'light') == 'light' else "Switch to Light Mode"
        
        if st.button(theme_emoji, help=theme_help, key='theme_toggle'):
            st.session_state.theme = 'light' if st.session_state.get('theme', 'dark') == 'dark' else 'dark'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Add spacing
st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
















# --- 6. Page Content Rendering ---
if selected == "Home":
    # Main title with enhanced styling
    st.markdown('<h1 class="main-title">YOUR TRUST MATTERS.</h1>', unsafe_allow_html=True)
    
    # Description
    st.markdown("""
        <div class="description-text">
            In today's fast-paced digital world, it can be nearly impossible to tell the difference 
            between real news and misinformation. We built this tool to help you navigate the noise. 
            Our advanced AI model analyzes text, tone, and context to provide a clear, instant verdict: 
            <strong>real or fake</strong>. Just paste an article or a link, and let our technology give you 
            the clarity and confidence you need to stay informed and safe online.
        </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #ff9500; text-align: center;">🔍 URL Analysis</h3>
                <p style="text-align: center;">Instantly verify news articles by simply pasting the URL</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #ff9500; text-align: center;">📝 Text Analysis</h3>
                <p style="text-align: center;">Analyze any text content for authenticity and reliability</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #ff9500; text-align: center;">📊 Track History</h3>
                <p style="text-align: center;">Keep track of your past checks </p>
            </div>
        """, unsafe_allow_html=True)


# if selected == "Home":
#     # Main title with enhanced styling
#     st.markdown('<h1 class="main-title">YOUR TRUST MATTERS.</h1>', unsafe_allow_html=True)
    
#     # Description
#     st.markdown("""
#         <div class="description-text">
#             In today's fast-paced digital world, it can be nearly impossible to tell the difference 
#             between real news and misinformation. We built this tool to help you navigate the noise. 
#             Our advanced AI model analyzes text, tone, and context to provide a clear, instant verdict: 
#             <strong>real or fake</strong>. Just paste an article or a link, and let our technology give you 
#             the clarity and confidence you need to stay informed and safe online.
#         </div>
#     """, unsafe_allow_html=True)
    
#     # Feature highlights
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">🔍 URL Analysis</h3>
#                 <p style="text-align: center;">Instantly verify news articles by simply pasting the URL</p>
#             </div>
#         """, unsafe_allow_html=True)
#         # ADDED: Navigation button
#         if st.button("Analyze a URL", key="nav_url", use_container_width=True):
#             st.session_state.nav_request = "Predict"
#             st.rerun()

#     with col2:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">📝 Text Analysis</h3>
#                 <p style="text-align: center;">Analyze any text content for authenticity and reliability</p>
#             </div>
#         """, unsafe_allow_html=True)
#         # ADDED: Navigation button
#         if st.button("Analyze Text", key="nav_text", use_container_width=True):
#             st.session_state.nav_request = "Predict"
#             st.rerun()
    
#     with col3:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">📊 Track History</h3>
#                 <p style="text-align: center;">Keep track of your past checks and see trending patterns</p>
#             </div>
#         """, unsafe_allow_html=True) # FIXED: Removed the extra period that was here
#         # ADDED: Navigation button
#         if st.button("View History", key="nav_history", use_container_width=True):
#             st.session_state.nav_request = "Past Checks"
#             st.rerun()


# if selected == "Home":
#     # Main title with enhanced styling
#     st.markdown('<h1 class="main-title">YOUR TRUST MATTERS.</h1>', unsafe_allow_html=True)
    
#     # Description
#     st.markdown("""
#         <div class="description-text">
#             In today's fast-paced digital world, it can be nearly impossible to tell the difference 
#             between real news and misinformation. We built this tool to help you navigate the noise. 
#             Our advanced AI model analyzes text, tone, and context to provide a clear, instant verdict: 
#             <strong>real or fake</strong>. Just paste an article or a link, and let our technology give you 
#             the clarity and confidence you need to stay informed and safe online.
#         </div>
#     """, unsafe_allow_html=True)
    
#     # Feature highlights
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">🔍 URL Analysis</h3>
#                 <p style="text-align: center;">Instantly verify news articles by simply pasting the URL.</p>
#             </div>
#         """, unsafe_allow_html=True)
        
#         # NEW: Add a button that navigates to the 'Predict' page
#         if st.button("Analyze a URL", key="nav_to_url", use_container_width=True):
#             st.session_state.selected_page = "Predict"
#             st.rerun()

#     with col2:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">📝 Text Analysis</h3>
#                 <p style="text-align: center;">Analyze any text content for authenticity and reliability.</p>
#             </div>
#         """, unsafe_allow_html=True)

#         # NEW: Add a button that also navigates to the 'Predict' page
#         if st.button("Analyze Text", key="nav_to_text", use_container_width=True):
#             st.session_state.selected_page = "Predict"
#             st.rerun()
    
#     with col3:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center;">📊 Track History</h3>
#                 <p style="text-align: center;">Keep track of your past checks and see trending patterns.</p>
#             </div>
#         """, unsafe_allow_html=True)

#         # NEW: Add a button that navigates to the 'Past Checks' page
#         if st.button("View History", key="nav_to_history", use_container_width=True):
#             st.session_state.selected_page = "Past Checks"
#             st.rerun()

elif selected == "Predict":
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>Predict News Authenticity</h2>", unsafe_allow_html=True)
    
    # Center the prediction interface
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    
    with col2:
        tab1, tab2 = st.tabs(["🔗 Analyze by URL", "📝 Analyze by Text"])
        
        with tab1:
            st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
            url_input = st.text_input(
                "Enter news article URL...",
                placeholder="https://example.com/news-article",
                label_visibility="collapsed",
                key="url_input"
            )
            
            st.markdown("<div style='margin: 1.5rem 0; text-align: center;'></div>", unsafe_allow_html=True)
            
            if st.button("🚀 CHECK NEWS FROM URL", use_container_width=True):
                if url_input:
                    with st.spinner("🔍 Analyzing URL... Please wait"):
                        # Simulate processing
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                        
                        # Mock analysis
                        text = extract_article_text(url_input)
                        if text and len(text.strip()) >= 10:  # Lowered threshold for demo
                            cleaned_text = clean_text(text)
                            
                            # Mock prediction
                            import random
                            confidence = random.uniform(0.75, 0.98)
                            is_real = random.choice([True, False])
                            label = "Real" if is_real else "Fake"
                            
                            # log_query(url_input, label, confidence, len(text))

                            log_query_and_trim(url_input, label, confidence, len(text))
                            fetch_past_checks.clear()
                            st.session_state['result_label'] = label
                            st.session_state['result_confidence'] = confidence
                            
                            # Clear progress bar
                            progress_bar.empty()
                        else:
                            st.error("❌ Could not extract enough text from the URL. Please try a different URL.")
                else:
                    st.warning("⚠️ Please enter a URL to analyze.")
        
        with tab2:
            st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
            text_input = st.text_area(
                "Paste article text here...",
                height=200,
                placeholder="Paste the full article text here for analysis...",
                label_visibility="collapsed",
                key="text_input"
            )
            
            st.markdown("<div style='margin: 1.5rem 0; text-align: center;'></div>", unsafe_allow_html=True)
            
            if st.button("🚀 CHECK NEWS FROM TEXT", use_container_width=True):
                if text_input and len(text_input.strip()) > 50:
                    with st.spinner("📝 Analyzing text... Please wait"):
                        # Simulate processing
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)
                        
                        cleaned_text = clean_text(text_input)
                        
                        # Mock prediction
                        import random
                        confidence = random.uniform(0.75, 0.98)
                        is_real = random.choice([True, False])
                        label = "Real" if is_real else "Fake"
                        
                        # log_query("TEXT_INPUT", label, confidence, len(text_input))


                        log_query_and_trim("TEXT_INPUT", label, confidence, len(text_input))
                        fetch_past_checks.clear()
                        st.session_state['result_label'] = label
                        st.session_state['result_confidence'] = confidence
                        
                        # Clear progress bar
                        progress_bar.empty()
                else:
                    st.warning("⚠️ Please paste some text (minimum 50 characters) to analyze.")
        
        # Display results
        if 'result_label' in st.session_state:
            st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
            
            label = st.session_state['result_label']
            confidence = st.session_state['result_confidence']
            color = "#28a745" if label == "Real" else "#dc3545"
            
            result_html = f"""
            <div class="result-container">
                <div class="result-label" style="color: {color};">
                    {'✅ ' + label.upper() if label == 'Real' else '❌ ' + label.upper()}
                </div>
                <div class="confidence-text">
                    {confidence:.0%} CONFIDENCE
                </div>
                <div style="margin-top: 1rem; font-size: 1rem; opacity: 0.8;">
                    {'This article appears to be authentic' if label == 'Real' else 'This article may contain misinformation'}
                </div>
            </div>
            """
            
            st.markdown(result_html, unsafe_allow_html=True)
            
            # Option to check another article
            if st.button("🔄 Check Another Article", use_container_width=True):
                if 'result_label' in st.session_state:
                    del st.session_state['result_label']
                if 'result_confidence' in st.session_state:
                    del st.session_state['result_confidence']
                st.rerun()



# elif selected == "Past Checks":
#     st.markdown('<h2 style="text-align: center; margin-bottom: 2rem;">PAST CHECKS & TRENDS</h2>', unsafe_allow_html=True)
    
#     # This function should connect to your actual database
#     # @st.cache_data
#     # def fetch_past_checks():
#     #     # Using mock data for demonstration as in your original code
#     #     import random
#     #     from datetime import datetime, timedelta
#     #     data = []
#     #     for i in range(20):
#     #         data.append({
#     #             'url': f'https://example-news-{i+1}.com/article',
#     #             'label': random.choice(['Real', 'Fake']),
#     #             'confidence': random.uniform(0.75, 0.99),
#     #             'created_at': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S')
#     #         })
#     #     return pd.DataFrame(data)



#     # ADD THIS NEW FUNCTION IN ITS PLACE
# @st.cache_data
# def fetch_past_checks():
#     # This function now reads from your actual, trimmed database
#     conn = sqlite3.connect("queries.db")
#     df = pd.read_sql_query("SELECT url, label, confidence, created_at FROM queries ORDER BY created_at DESC", conn)
#     conn.close()
#     return df





#     df_checks = fetch_past_checks()
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.subheader("📊 Recent Analysis History")
        
#         if df_checks.empty:
#             st.markdown("""
#                 <div class="metric-card">
#                     <p style="text-align: center; color: #6b7280;">
#                         No past checks found. Start analyzing some articles!
#                     </p>
#                 </div>
#             """, unsafe_allow_html=True)
#         else:
#             # This is the corrected loop
#             for index, row in df_checks.head(10).iterrows():
#                 result_color = "#28a745" if row['label'] == 'Real' else "#dc3545"
#                 emoji = "✅" if row['label'] == 'Real' else "❌"
                
#                 st.markdown(f"""
#                     <div class="metric-card">
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <div>
#                                 <strong style="color: {result_color};">{emoji} {row['label'].upper()}</strong>
#                                 <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.25rem;">
#                                     {row['confidence']:.0%} confidence • {row['created_at'][:10]}
#                                 </div>
#                             </div>
#                             <div style="font-size: 0.8rem; opacity: 0.6; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
#                                 {row['url']}
#                             </div>
#                         </div>
#                     </div>
#                 """, unsafe_allow_html=True)
    
#     with col2:
#         st.subheader("📈 Analysis Trends")
        
#         if not df_checks.empty:
#             label_counts = df_checks['label'].value_counts().reset_index()
#             label_counts.columns = ['label', 'count']
            
#             fig = px.pie(
#                 label_counts, 
#                 names='label', 
#                 values='count',
#                 title='Real vs. Fake Distribution',
#                 color='label',
#                 color_discrete_map={'Real': '#28a745', 'Fake': '#dc3545'}
#             )
            
#             font_color = "#c9d1d9" if st.session_state.get('theme', 'dark') == 'dark' else "#000000"

#             fig.update_layout(
#                 font_family="Inter",
#                 title_font_size=14,
#                 showlegend=True,
#                 height=280,
#                 paper_bgcolor='rgba(0,0,0,0)',
#                 plot_bgcolor='rgba(0,0,0,0)',
#                 title_font_color=font_color,
#                 legend=dict(font=dict(color=font_color)),
#                 modebar_color='#ff9900'
#             )
            
#             config = {'displayModeBar': True}
#             st.plotly_chart(fig, use_container_width=True, config=config)
            
#             # This is the corrected summary stats part
#             real_count = df_checks[df_checks['label'] == 'Real'].shape[0]
#             fake_count = df_checks[df_checks['label'] == 'Fake'].shape[0]
#             avg_confidence = df_checks['confidence'].mean()
#             st.markdown(f"""
#                 <div class="metric-card">
#                     <h4 style="text-align: center; color: #ff9500; margin-bottom: 1rem;">📊 Summary Stats</h4>
#                     <div style="text-align: center;">
#                         <p><strong>Total Checks:</strong> {len(df_checks)}</p>
#                         <p><strong>Real Articles:</strong> {real_count}</p>
#                         <p><strong>Fake Articles:</strong> {fake_count}</p>
#                         <p><strong>Avg. Confidence:</strong> {avg_confidence:.1%}</p>
#                     </div>
#                 </div>
#             """, unsafe_allow_html=True)

#         else:
#             st.markdown("""
#                 <div class="metric-card">
#                     <p style="text-align: center; color: #6b7280;">
#                         Not enough data for trends analysis.
#                     </p>
#                 </div>
#             """, unsafe_allow_html=True)









elif selected == "Past Checks":
    st.markdown('<h2 style="text-align: center; margin-bottom: 2rem;">PAST CHECKS & TRENDS</h2>', unsafe_allow_html=True)
    
    # FIXED: This function must be indented to be inside the 'elif' block
    # @st.cache_data
    # def fetch_past_checks():
    #     # This function now reads from your actual, trimmed database
    #     conn = sqlite3.connect("queries.db")
    #     df = pd.read_sql_query("SELECT url, label, confidence, created_at FROM queries ORDER BY created_at DESC", conn)
    #     conn.close()
    #     return df

    df_checks = fetch_past_checks()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Recent Analysis History")
        
        if df_checks.empty:
            st.markdown("""
                <div class="metric-card">
                    <p style="text-align: center; color: #6b7280;">
                        No past checks found. Start analyzing some articles!
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            for index, row in df_checks.head(10).iterrows():
                result_color = "#28a745" if row['label'] == 'Real' else "#dc3545"
                emoji = "✅" if row['label'] == 'Real' else "❌"
                
                st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: {result_color};">{emoji} {row['label'].upper()}</strong>
                                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.25rem;">
                                    {row['confidence']:.0%} confidence • {row['created_at'][:10]}
                                </div>
                            </div>
                            <div style="font-size: 0.8rem; opacity: 0.6; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                {row['url']}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📈 Analysis Trends")
        
        if not df_checks.empty:
            label_counts = df_checks['label'].value_counts().reset_index()
            label_counts.columns = ['label', 'count']
            
            fig = px.pie(
                label_counts, 
                names='label', 
                values='count',
                title='Real vs. Fake Distribution',
                color='label',
                color_discrete_map={'Real': '#28a745', 'Fake': '#dc3545'}
            )
            
            font_color = "#c9d1d9" if st.session_state.get('theme', 'dark') == 'dark' else "#000000"

            fig.update_layout(
                font_family="Inter",
                title_font_size=14,
                showlegend=True,
                height=280,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                title_font_color=font_color,
                legend=dict(font=dict(color=font_color)),
                modebar_color='#ff9900'
            )
            
            config = {'displayModeBar': True}
            st.plotly_chart(fig, use_container_width=True, config=config)
            
            real_count = df_checks[df_checks['label'] == 'Real'].shape[0]
            fake_count = df_checks[df_checks['label'] == 'Fake'].shape[0]
            avg_confidence = df_checks['confidence'].mean()
            st.markdown(f"""
                <div class="metric-card">
                    <h4 style="text-align: center; color: #ff9500; margin-bottom: 1rem;">📊 Summary Stats</h4>
                    <div style="text-align: center;">
                        <p><strong>Total Checks:</strong> {len(df_checks)}</p>
                        <p><strong>Real Articles:</strong> {real_count}</p>
                        <p><strong>Fake Articles:</strong> {fake_count}</p>
                        <p><strong>Avg. Confidence:</strong> {avg_confidence:.1%}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("""
                <div class="metric-card">
                    <p style="text-align: center; color: #6b7280;">
                        Not enough data for trends analysis.
                    </p>
                </div>
            """, unsafe_allow_html=True)







elif selected == "About":
    st.markdown('<h1 class="main-title">ABOUT OUR MISSION</h1>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="description-text">
            In an era flooded with information, separating fact from fiction has become a critical challenge. 
            Our mission is simple: to provide a powerful and accessible tool that empowers you to identify 
            misinformation with confidence.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="description-text">
            We believe that informed communities are strong communities, and that fighting disinformation 
            is not just about technology—it's about protecting the integrity of our shared digital space.
        </div>
    """, unsafe_allow_html=True)
    
    # Team section
    st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #ff9500; text-align: center; margin-bottom: 1.5rem;">🎯 Our Approach</h3>
                <div style="text-align: left; line-height: 1.8;">
                    <p>• <strong>Advanced ML Models:</strong> Using state-of-the-art machine learning algorithms</p>
                    <p>• <strong>Real-time Analysis:</strong> Instant verification of news articles and content</p>
                    <p>• <strong>User-Friendly Interface:</strong> Simple, intuitive design for everyone</p>
                    <p>• <strong>Continuous Learning:</strong> Our models improve with every analysis</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Expandable thank you section
    with st.expander("💝 A Thank You from the Team", expanded=False):
        st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <p style="font-size: 1.1rem; line-height: 1.8;">
                    We sincerely thank you for visiting <strong>Factify – Fake News URL Detector</strong>, 
                    our college minor project in Machine Learning.
                </p>
                <p style="font-size: 1rem; line-height: 1.6; margin-top: 1rem;">
                    This project is the result of hard work, dedication, and collaboration of our entire team. 
                    We built Factify with the vision of helping people identify misleading or fake news online 
                    by analyzing URLs and providing quick, reliable results.
                </p>
                <p style="font-size: 1rem; line-height: 1.6; margin-top: 1rem;">
                    We are grateful to our mentors, faculty, and peers for their constant guidance and 
                    encouragement throughout this journey. Most importantly, we thank you for taking 
                    the time to explore our project.
                </p>
                <p style="font-size: 1rem; line-height: 1.6; margin-top: 1rem; font-weight: 600;">
                    Together, let's take one step closer to a world with truthful and trustworthy information.
                </p>
                <p style="font-size: 1.2rem; margin-top: 1.5rem; color: #ff9500; font-weight: 700;">
                    — Team Factify 🚀
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Contact or feedback section
    # st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
    #     if st.button("💌 Give Feedback", use_container_width=True):
    #         st.balloons()
    #         st.success("Thank you for your interest! Your feedback helps us improve Factify.")

# Find this part in your "About" page code and replace it

    # Contact or feedback section
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="metric-card">
                <h3 style="color: #ff9500; text-align: center; margin-bottom: 1.5rem;">💌 Give Feedback</h3>
                <p style'text-align: center;>We'd love to hear your thoughts!</p>
        """, unsafe_allow_html=True)

        # --- Create the Streamlit Form ---
        with st.form(key="feedback_form"):
            # IMPORTANT: Replace with your Formspree endpoint URL
            formspree_endpoint = "https://formspree.io/f/xdkwooqv"

            user_email = st.text_input(
                "Your Email", 
                placeholder="Enter your email so we can reply"
            )
            user_message = st.text_area(
                "Your Feedback", 
                placeholder="What do you think? Any suggestions?", 
                height=150
            )
            
            # The submit button for the form
            submitted = st.form_submit_button("Send Feedback")
            
            if submitted:
                if not user_email or not user_message:
                    st.warning("Please fill out both fields before sending.")
                else:
                    try:
                        # Send the data to Formspree
                        response = requests.post(
                            formspree_endpoint,
                            data={
                                "email": user_email,
                                "message": user_message
                            }
                        )
                        
                        # Check for a successful submission
                        if response.status_code == 200:
                            st.success("Thank you for your feedback! We've received your message.")
                            st.balloons()
                        else:
                            st.error("Sorry, something went wrong. Please try again later.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
        # Closing the metric-card div
        st.markdown("</div>", unsafe_allow_html=True)










# Footer
st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center; opacity: 0.6; font-size: 0.9rem; border-top: 1px solid rgba(255, 149, 0, 0.2); padding-top: 1rem;'>
        Made with ❤️ by Team Factify | Fighting Misinformation One Article at a Time
    </div>
""", unsafe_allow_html=True)






# elif selected == "About":
#     st.markdown('<h1 class="main-title">ABOUT OUR MISSION</h1>', unsafe_allow_html=True)
    
#     st.markdown("""
#         <div class="description-text">
#             In an era flooded with information, separating fact from fiction has become a critical challenge. 
#             Our mission is simple: to provide a powerful and accessible tool that empowers you to identify 
#             misinformation with confidence.
#         </div>
#     """, unsafe_allow_html=True)
    
#     st.markdown("""
#         <div class="description-text">
#             We believe that informed communities are strong communities, and that fighting disinformation 
#             is not just about technology—it's about protecting the integrity of our shared digital space.
#         </div>
#     """, unsafe_allow_html=True)
    
#     # Team section
#     st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         st.markdown("""
#             <div class="metric-card">
#                 <h3 style="color: #ff9500; text-align: center; margin-bottom: 1.5rem;">🎯 Our Approach</h3>
#                 <div style="text-align: left; line-height: 1.8;">
#                     <p>• <strong>Advanced ML Models:</strong> Using state-of-the-art machine learning algorithms</p>
#                     <p>• <strong>Real-time Analysis:</strong> Instant verification of news articles and content</p>
#                     <p>• <strong>User-Friendly Interface:</strong> Simple, intuitive design for everyone</p>
#                     <p>• <strong>Continuous Learning:</strong> Our models improve with every analysis</p>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
    
#     # Expandable thank you section
#     with st.expander("💝 A Thank You from the Team", expanded=False):
#         st.markdown("""
#             <div style="text-align: center; padding: 1rem;">
#                 <p>... (Your full thank you text here) ...</p>
#                 <p style="font-size: 1.2rem; margin-top: 1.5rem; color: #ff9500; font-weight: 700;">
#                     — Team Factify 🚀
#                 </p>
#             </div>
#         """, unsafe_allow_html=True)
    
#     # --- CHANGED: Replaced the button with a functional HTML form ---
#     st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown("""
#         <style>
#             /* Basic styling for the form elements to match your theme */
#             form { display: flex; flex-direction: column; gap: 1rem; }
#             form input, form textarea {
#                 padding: 0.8rem; border-radius: 15px; border: 2px solid #ff9500;
#                 background-color: transparent; color: inherit; font-family: 'Inter', sans-serif;
#             }
#             form button {
#                 background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%); color: #ffffff;
#                 border: none; border-radius: 25px; font-weight: 600; padding: 0.7rem;
#                 cursor: pointer; text-transform: uppercase;
#             }
#         </style>
        
#         <div class="metric-card">
#             <h3 style="color: #ff9500; text-align: center;">💌 Give Feedback</h3>
#             <p style="text-align: center; margin-bottom: 1.5rem;">We'd love to hear your thoughts!</p>
            
#             <form action="https://formspree.io/f/xdkwooqv" method="POST">
#                 <input type="email" name="email" placeholder="Your email" required>
#                 <textarea name="message" placeholder="Your feedback or suggestion..." required rows="4"></textarea>
#                 <button type="submit">Send Feedback</button>
#             </form>
#         </div>
#         """, unsafe_allow_html=True)

# # --- The Footer remains the same ---
# st.markdown("<div style='margin: 4rem 0 2rem 0;'></div>", unsafe_allow_html=True)
# st.markdown("""
#     <div style='text-align: center; opacity: 0.6; font-size: 0.9rem; border-top: 1px solid rgba(255, 149, 0, 0.2); padding-top: 1rem;'>
#         Made with ❤️ by Team Factify | Fighting Misinformation One Article at a Time
#     </div>
# """, unsafe_allow_html=True)





