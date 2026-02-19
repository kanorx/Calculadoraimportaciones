import requests
from bs4 import BeautifulSoup

def scrape_aliexpress_meta(url):
    """
    Intenta extraer la información básica de un link de AliExpress 
    usando headers falsos para engañar al firewall.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Buscamos el título y la descripción en las etiquetas de SEO
        title = soup.find("meta", property="og:title")
        desc = soup.find("meta", property="og:description")
        
        title_text = title["content"] if title else soup.title.text if soup.title else "Producto Desconocido"
        desc_text = desc["content"] if desc else "Sin descripción detallada."
        
        return {
            "titulo_original": title_text,
            "descripcion_raw": desc_text
        }
    except Exception as e:
        return None
