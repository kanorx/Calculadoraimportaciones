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
        /* 1. ELIMINAR EL ESPACIO MUERTO SUPERIOR DE STREAMLIT */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 95% !important;
        }
        
        /* Forzar fondo claro */
        .stApp { background-color: #F4F7FC !important; font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4, p, span, label, div[data-testid="stMarkdownContainer"] { color: #091E42 !important; }
        
        /* 2. ESTILO DE SAAS PARA CONTENEDORES (Tarjetas flotantes) */
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            background-color: #ffffff !important;
            border-radius: 16px !important;
            border: 1px solid #E1E5F2 !important;
            box-shadow: 0 8px 20px rgba(9, 30, 66, 0.04) !important;
            padding: 20px !important;
            transition: all 0.3s ease;
        }
        div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
            box-shadow: 0 12px 25px rgba(9, 30, 66, 0.08) !important;
            transform: translateY(-2px);
        }
        
        /* Inputs limpios */
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #F8FAFC !important;
            color: #091E42 !important;
            -webkit-text-fill-color: #091E42 !important;
            border: 1px solid #DCDFE6 !important;
            border-radius: 8px !important;
        }
        .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
            border: 2px solid #2E5BFF !important;
            background-color: #ffffff !important;
        }
        
        /* Tarjetas de Métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.04) !important;
            border-left: 5px solid #2E5BFF !important;
        }
        div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #2E5BFF !important; font-weight: 800 !important; }

        /* Botones VIP */
        .stButton>button {
            width: 100% !important;
            border-radius: 8px !important;
            height: 3.5em !important;
            background: linear-gradient(135deg, #2E5BFF 0%, #00C6FF 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 4px 10px rgba(46, 91, 255, 0.2) !important;
            letter-spacing: 0.5px;
        }
        .stButton>button:hover { 
            box-shadow: 0 6px 15px rgba(46, 91, 255, 0.4) !important; 
            transform: translateY(-2px); 
        }
        
        /* Ocultar elementos por defecto de Streamlit */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
