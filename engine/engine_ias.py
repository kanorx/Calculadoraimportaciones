import streamlit as st
import requests
import base64

def call_openrouter_ai(prompt, image_input=None, task="legal"):
    """
    Motor de Inteligencia Artificial conectado a Gemini 2.5 Flash.
    Maneja el procesamiento de lenguaje natural y visión multimodal.
    """
    try: 
        key = st.secrets["OPENROUTER_API_KEY"]
    except: 
        return "⚠️ Error: Configura tu API Key en los secretos (secrets.toml)."

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    
    if task == "legal":
        sys_msg = "Experto aduanero Colombia. Indica: 1. Subpartida (10 dígitos), 2. % Arancel, 3. % IVA. Sé técnico."
    else:
        sys_msg = "Experto SEO E-commerce. Genera Título ganador, 5 bullet points AIDA y keywords para Mercado Libre Colombia."

    content = [{"type": "text", "text": f"{sys_msg}\n\nInput: {prompt}"}]
    
    # Lógica de Visión Multimodal (si el usuario sube una imagen)
    if image_input:
        b64_str = base64.b64encode(image_input.read()).decode('utf-8')
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}})

    payload = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": content}]}

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
        return res.json()['choices'][0]['message']['content'] if res.status_code == 200 else f"Error API: {res.status_code}"
    except: 
        return "❌ Sin conexión a la IA. Revisa tu internet o la API Key."
