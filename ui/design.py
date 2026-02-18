import streamlit as st
import requests

def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def inyectar_estilos():
    st.markdown("""
        <style>
        .stApp { background-color: #F4F7FC !important; font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4, p, span, label, div[data-testid="stMarkdownContainer"] { color: #091E42 !important; }
        
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #ffffff !important;
            color: #091E42 !important;
            -webkit-text-fill-color: #091E42 !important;
            border: 1px solid #DCDFE6 !important;
            border-radius: 8px !important;
        }
        .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            border: 2px solid #2E5BFF !important;
        }
        
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
            border-left: 5px solid #2E5BFF !important;
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover { transform: translateY(-3px); }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2E5BFF !important; font-weight: 800 !important; }

        .stButton>button {
            width: 100% !important;
            border-radius: 10px !important;
            height: 3.5em !important;
            background: linear-gradient(135deg, #2E5BFF 0%, #00C6FF 100%) !important;
            color: white !important;
            -webkit-text-fill-color: white !important;
            border: none !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 10px rgba(46, 91, 255, 0.2) !important;
            transition: 0.3s !important;
        }
        .stButton>button:hover { box-shadow: 0 6px 15px rgba(46, 91, 255, 0.4) !important; transform: translateY(-2px); }
        
        .stChatMessage { border-radius: 15px; background: #ffffff !important; border: 1px solid #E1E5F2 !important; }
        
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
