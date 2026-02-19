import requests
import json
import base64
import streamlit as st

def call_openrouter_ai(prompt, image_input=None, task="marketing"):
    """
    Motor de Inteligencia Artificial conectado a OpenRouter (Gemini / OpenAI).
    Procesa tanto texto plano como análisis de imágenes (Visión).
    """
    # Intentamos obtener la clave API de los secretos de Streamlit
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        return "⚠️ Error: Falta configurar OPENROUTER_API_KEY en los secretos (st.secrets) de Streamlit."

    # ==========================================
    # 1. DEFINICIÓN DE ROLES (SYSTEM PROMPTS)
    # ==========================================
    if task == "legal":
        system_instruction = """Eres un Agente de Aduanas y experto en Aranceles de Colombia (DIAN).
Tu trabajo es analizar el producto que el usuario te menciona o la imagen que te envía, y decirle:
1. Qué subpartida arancelaria aproximada le corresponde.
2. Si requiere vistos buenos (ej. INVIMA, SIC, etc.).
3. Consejos para evitar retenciones en la aduana.
Responde de forma clara, profesional y en viñetas."""

    elif task == "marketing":
        # ¡EL PROMPT MAESTRO DEL CEO!
        system_instruction = """Eres un copywriter experto en E-commerce y especialista en el algoritmo de SEO de MercadoLibre. 
Tu objetivo es analizar la imagen o los datos del producto proporcionado y generar una publicación altamente persuasiva que convierta clics en ventas.

REGLAS ESTRICTAS DEL ALGORITMO:
1. TÍTULO: Debe tener exactamente entre 40 y 60 caracteres. Fórmula obligatoria: [Producto] + [Característica Principal]. PROHIBIDO usar palabras como "Oferta", "Envío Gratis" o "Nuevo".
2. FORMATO DE TEXTO: MercadoLibre SOLO acepta texto plano. ESTÁ ESTRICTAMENTE PROHIBIDO usar formato Markdown como negritas (**), cursivas (*), o títulos grandes (#).
3. VIÑETAS: Usa únicamente símbolos simples como "-" para las listas.
4. TONO: Persuasivo, profesional y enfocado en resolver los problemas del comprador (Beneficios > Características).

DEVUELVE TU RESPUESTA EXACTAMENTE CON ESTA ESTRUCTURA:

TÍTULO OPTIMIZADO:
[Escribe el título aquí - Cuenta bien los caracteres]

📝 Caracteristicas Adicionales:
- [Característica técnica 1]
- [Característica técnica 2]
- [Característica técnica 3]

🚀 ¿POR QUÉ ELEGIR ESTE PRODUCTO? (Descripción):
ETIQUETAS Palabras clave(SEO) en todo el parrafo sutiles.
[1 Párrafo gancho: Identifica el dolor o deseo del cliente en una frase corta]
[1 Párrafo de solución: Explica cómo el producto mejora su vida]"""

    else:
        system_instruction = "Eres un asistente experto en importaciones y comercio exterior."

    # ==========================================
    # 2. CONSTRUCCIÓN DEL MENSAJE (TEXTO + IMAGEN)
    # ==========================================
    # Formato estándar de OpenRouter/OpenAI para visión
    user_content = []
    
    # Agregamos el texto
    user_content.append({"type": "text", "text": prompt})
    
    # Si hay imagen, la convertimos a Base64 y la inyectamos
    if image_input is not None:
        try:
            # Usamos .getvalue() para leer la memoria sin mover el cursor (el bug que arreglamos)
            b64_str = base64.b64encode(image_input.getvalue()).decode('utf-8')
            
            # Determinamos el tipo de imagen
            mime_type = "image/jpeg"
            if image_input.name.lower().endswith(".png"):
                mime_type = "image/png"
                
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_str}"
                }
            })
        except Exception as e:
            return f"⚠️ Error procesando la imagen: {str(e)}"

    # ==========================================
    # 3. PETICIÓN A LA API
    # ==========================================
    # Usamos Gemini 2.5 Flash a través de OpenRouter (super rápido y económico)
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://importpro-suite.com", # Opcional, para estadísticas en OpenRouter
        "X-Title": "ImportPro Suite",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-2.5-flash", 
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.7, # Creatividad controlada para marketing
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"❌ Error de API ({response.status_code}): {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"🔌 Error de conexión con la IA: {str(e)}"
