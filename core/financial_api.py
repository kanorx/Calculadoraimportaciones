import requests
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_trm():
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            return float(res.json()[0]['valor'])
        else:
            return 4000.0
    except Exception as e: 
        return 4000.0
