import requests
import base64
import streamlit as st

def call_openrouter_ai(prompt, image_input=None, task="marketing"):
    """
    Motor de Inteligencia Artificial conectado a OpenRouter (Gemini / OpenAI).
    Procesa tanto texto plano como análisis de imágenes (Visión).
    """

    # ==========================================
    # 0. VALIDACIÓN DE API KEY
    # ==========================================
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        return "⚠️ Error: Falta configurar OPENROUTER_API_KEY en los secretos (st.secrets) de Streamlit."

    # ==========================================
    # 1. DEFINICIÓN DE ROLES
    # ==========================================
    if task == "legal":
        reglas_estrictas = """Eres un Agente de Aduanas y experto en Aranceles de Colombia (DIAN).
Responde de forma clara, profesional y en viñetas:

1. Subpartida arancelaria aproximada.
2. IVA Y ARANCEL EN COLOMBIA (REALES O ESTIMADOS)
   https://muisca.dian.gov.co/WebArancel/DefConsultaNomenclaturaPorCodigo.faces
   (Indica que deben confirmar aquí con la subpartida sugerida.
   Prioriza datos reales. Si existe protección a la industria nacional
   como en ropa con arancel 35%-40%, indícalo claramente.)
3. Si requiere vistos buenos (INVIMA, SIC, ICA, etc.).

IMPORTANTE:
- Máximo 400 tokens.
- No agregar relleno innecesario.
- No hacer introducciones ni despedidas.
"""

    elif task == "marketing":
        reglas_estrictas = """INSTRUCCIÓN SUPREMA: Eres un Copywriter SEO Senior para MercadoLibre.

Tu objetivo es crear una publicación EXTENSA, MUY DETALLADA y ALTAMENTE PERSUASIVA que maximice las ventas, respetando estrictamente estas reglas técnicas:

REGLAS INQUEBRANTABLES:
1. TÍTULO: 40-60 caracteres. Fórmula: [Producto] + [Característica Principal]. PROHIBIDO usar palabras como "Oferta" o "Gratis".
2. FORMATO PLANO: MercadoLibre NO acepta estilos. PROHIBIDO usar asteriscos (*), negritas (**), o numerales (#).
3. VIÑETAS: Usa solo el símbolo "-" al inicio de la línea.
4. CERO RELLENO: No saludes, no te despidas, no des consejos extra.

ESTRUCTURA OBLIGATORIA:

TÍTULO OPTIMIZADO:
[Escribe el título aquí]

📝 CARACTERÍSTICAS Y BENEFICIOS:
- [Característica 1 + beneficio real]
- [Característica 2 + beneficio real]
- [Característica 3 + beneficio real]
- [Característica 4 + beneficio real]
- [Característica 5 + beneficio real]

🚀 ¿POR QUÉ ELEGIR ESTE PRODUCTO?

[Párrafo 1 - Problema + solución + SEO]

[Párrafo 2 - Calidad, materiales, experiencia superior]

[Párrafo 3 - Confianza + llamado a la acción]
"""

    else:
        reglas_estrictas = "Eres un asistente experto en importaciones."

    # ==========================================
    # 2. BLINDAJE DEL PROMPT
    # ==========================================
    texto_blindado = f"{reglas_estrictas}\n\n---\nDATOS DEL PRODUCTO A ANALIZAR:\n{prompt}"

    # ==========================================
    # 3. CONSTRUCCIÓN DEL MENSAJE (TEXTO + IMAGEN)
    # ==========================================
    user_content = []
    user_content.append({"type": "text", "text": texto_blindado})

    if image_input is not None:
        try:
            b64_str = base64.b64encode(image_input.getvalue()).decode("utf-8")
            mime_type = "image/png" if image_input.name.lower().endswith(".png") else "image/jpeg"

            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_str}"
                }
            })
        except Exception as e:
            return f"⚠️ Error procesando la imagen: {str(e)}"

    # ==========================================
    # 4. CONFIGURACIÓN DINÁMICA DE TOKENS
    # ==========================================
    if task == "legal":
        max_tokens_config = 400
        temperature_config = 0.3  # Más técnico y preciso
    else:
        max_tokens_config = 1000
        temperature_config = 0.6  # Más creativo para marketing

    # ==========================================
    # 5. PETICIÓN A OPENROUTER
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
            {
                "role": "user",
                "content": user_content
            }
        ],
        "temperature": temperature_config,
        "max_tokens": max_tokens_config
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ Error de API ({response.status_code}): {response.text}"

    except requests.exceptions.RequestException as e:
        return f"🔌 Error de conexión con la IA: {str(e)}"
