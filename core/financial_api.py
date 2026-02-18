import requests
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_trm():
    """
    Intenta conectar a la API del gobierno. 
    Si el firewall bloquea el servidor de Streamlit Cloud, 
    salta automáticamente a una API global alternativa.
    """
    # ==========================================
    # PLAN A: API Oficial (Superfinanciera / Socrata)
    # ==========================================
    try:
        url_gob = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res_gob = requests.get(url_gob, headers=headers, timeout=5)
        
        if res_gob.status_code == 200:
            return float(res_gob.json()[0]['valor'])
            
    except Exception:
        pass # If not Plan B

    # ==========================================
    # PLAN B: API Financiera Global (AB=)
    # ==========================================
    try:
        url_alt = "https://open.er-api.com/v6/latest/USD"
        res_alt = requests.get(url_alt, timeout=10)
        
        if res_alt.status_code == 200:
            # Buscamos específicamente el valor del Peso Colombiano (COP)
            return float(res_alt.json()['rates']['COP'])
            
    except Exception:
        pass

    # ==========================================
    # PLAN C: Emergencia Extrema
    # ==========================================
    return 4000.0
