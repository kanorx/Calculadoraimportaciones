import requests
import base64
import streamlit as st

def call_openrouter_ai(prompt, image_input=None, task="marketing"):
    """
    Motor de Inteligencia Artificial conectado a OpenRouter (Gemini / OpenAI).
    Procesa tanto texto plano como análisis de imágenes (Visión).
    """
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        return "⚠️ Error: Falta configurar OPENROUTER_API_KEY en los secretos (st.secrets) de Streamlit."

    # ==========================================
    # 1. DEFINICIÓN DE ROLES (LA CAMISA DE FUERZA)
    # ==========================================
    if task == "legal":
        reglas_estrictas = """Eres un Agente de Aduanas y experto en Aranceles de Colombia (DIAN).
Responde de forma clara, profesional y en viñetas:
1. Subpartida arancelaria aproximada.
2. Si requiere vistos buenos (INVIMA, SIC, etc.).
3. Consejos para evitar retenciones."""

    elif task == "marketing":
        reglas_estrictas = """INSTRUCCIÓN SUPREMA: Eres un robot formateador estricto para MercadoLibre.
REGLAS INQUEBRANTABLES:
1. TÍTULO: 40-60 caracteres. Fórmula: [Producto] + [Característica]. PROHIBIDO usar "Oferta", "Envío", "Gratis", "Nuevo".
2. FORMATO: TEXTO PLANO ABSOLUTO. PROHIBIDO usar asteriscos (*), negritas (**), o numerales (#).
3. VIÑETAS: Usa solo guiones "-".
4. CERO CHARLA: No saludes, no des consejos, no te despidas. Limítate a imprimir la estructura solicitada.

ESTRUCTURA OBLIGATORIA (Cópiala exactamente):
TÍTULO OPTIMIZADO:
[Título]

📝 Caracteristicas Adicionales:
- [Caract 1]
- [Caract 2]
- [Caract 3]

🚀 ¿POR QUÉ ELEGIR ESTE PRODUCTO? (Descripción):
[1 Párrafo gancho identificando el dolor del cliente. Integra palabras clave SEO sutilmente]
[1 Párrafo de solución explicando cómo mejora su vida]"""

    else:
        reglas_estrictas = "Eres un asistente experto en importaciones."

    # FUSIONAMOS LAS REGLAS CON LA PREGUNTA DEL USUARIO
    texto_blindado = f"{reglas_estrictas}\n\n---\nDATOS DEL PRODUCTO A ANALIZAR:\n{prompt}"

    # ==========================================
    # 2. CONSTRUCCIÓN DEL MENSAJE (TEXTO + IMAGEN)
    # ==========================================
    user_content = []
    user_content.append({"type": "text", "text": texto_blindado})
    
    if image_input is not None:
        try:
            b64_str = base64.b64encode(image_input.getvalue()).decode('utf-8')
            mime_type = "image/png" if image_input.name.lower().endswith(".png") else "image/jpeg"
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_str}"}
            })
        except Exception as e:
            return f"⚠️ Error procesando la imagen: {str(e)}"

    # ==========================================
    # 3. PETICIÓN A LA API
    # ==========================================
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://importpro-suite.com",
        "X-Title": "ImportPro Suite",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash", 
        "messages": [
            # Eliminamos el rol 'system' y mandamos todo como 'user' para obligarlo a obedecer
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.5, # Bajamos la creatividad casi a cero para que no invente formatos
        "max_tokens": 800
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Error de API ({response.status_code}): {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"🔌 Error de conexión con la IA: {str(e)}"
