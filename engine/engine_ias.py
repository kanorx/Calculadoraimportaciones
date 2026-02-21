import requests
import base64
import json
import wave
import io
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
    # 1. DEFINICIÓN DE ROLES Y LÍMITES DINÁMICOS
    # ==========================================
    if task == "legal":
        reglas_estrictas = """Eres un Agente de Aduanas y experto en Aranceles de Colombia (DIAN).
Responde de forma clara, profesional y en viñetas:
1. Subpartida arancelaria aproximada.
2. IVA Y ARANCEL EN COLOMBIA (REALES O ESTIMADOS) https://muisca.dian.gov.co/WebArancel/DefConsultaNomenclaturaPorCodigo.faces 
(Hacer que confirmen aqui con la subpartida que les diste. El IVA y Arancel que les diste) (IMPORTANTE Prioriza los datos reales frente al Arancel si es posible consulta si hay proteccion a la industria un ejemplo es que hay un arancel alto 35%-40% para la ropa)
3. Si requiere vistos buenos (INVIMA, SIC, etc.)."""
        max_tokens_dinamico = 600
        temperatura_dinamica = 0.1 

    elif task == "marketing":
        reglas_estrictas = """INSTRUCCIÓN SUPREMA: Eres un Copywriter SEO Senior para MercadoLibre.
Tu objetivo es crear una publicación EXTENSA, MUY DETALLADA y ALTAMENTE PERSUASIVA que maximice las ventas, respetando estrictamente estas reglas técnicas:

REGLAS INQUEBRANTABLES:
1. TÍTULO: 40-60 caracteres. Fórmula: [Producto] + [Característica Principal]. PROHIBIDO usar palabras como "Oferta" o "Gratis".
2. FORMATO PLANO: MercadoLibre NO acepta estilos. ESTÁ ESTRICTAMENTE PROHIBIDO usar asteriscos (*), negritas (**), o numerales (#). El texto debe ser 100% limpio y profesional.
3. VIÑETAS: Usa solo el símbolo "-" al inicio de la línea.
4. CERO RELLENO: No me saludes, no des consejos adicionales, no te despidas. Genera SOLO la estructura solicitada.

ESTRUCTURA OBLIGATORIA (Genera contenido abundante y detallado en cada sección):

TÍTULO OPTIMIZADO:
[Escribe el título aquí]

📝 CARACTERÍSTICAS Y BENEFICIOS:
- [Detalla la característica 1 y explica qué beneficio real le da al comprador. Sé descriptivo]
- [Detalla la característica 2 y su beneficio...]
- [Detalla la característica 3 y su beneficio...]
- [Detalla la característica 4 y su beneficio...]
- [Detalla la característica 5 y su beneficio...]

🚀 ¿POR QUÉ ELEGIR ESTE PRODUCTO? (Descripción Detallada):
[Párrafo 1 - El Gancho: Escribe un párrafo de al menos 4 líneas identificando el problema del cliente y cómo este producto es la solución definitiva. Integra palabras clave SEO de forma natural].

[Párrafo 2 - La Experiencia: Escribe un párrafo de al menos 4 líneas profundizando en la calidad, los materiales, la experiencia de uso y por qué es superior a la competencia].

[Párrafo 3 - El Cierre: Genera confianza hablando de durabilidad o practicidad, e incluye un llamado a la acción persuasivo invitando a la compra inmediata]."""
        max_tokens_dinamico = 1000
        temperatura_dinamica = 0.6 

    else:
        reglas_estrictas = "Eres un asistente experto en importaciones."
        max_tokens_dinamico = 500
        temperatura_dinamica = 0.5

    # FUSIONAMOS LAS REGLAS CON LA PREGUNTA DEL USUARIO PARA EVITAR LA AMNESIA DE LA IA
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
            {"role": "user", "content": user_content}
        ],
        "temperature": temperatura_dinamica, 
        "max_tokens": max_tokens_dinamico  
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Error de API ({response.status_code}): {response.text}"
            
    except requests.exceptions.RequestException as e:
        return f"🔌 Error de conexión con la IA: {str(e)}"


def generar_audio_openrouter(texto, voz="nova"):
    """
    Se conecta a OpenAI: GPT Audio Mini mediante OpenRouter 
    utilizando STREAMING forzado, y convierte los datos crudos (PCM16) 
    a un archivo WAV reproducible.
    """
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except KeyError:
        return None, "⚠️ Error: Falta configurar OPENROUTER_API_KEY."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://importpro-suite.com",
        "X-Title": "ImportPro Suite",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-audio-mini",
        "modalities": ["text", "audio"],
        "audio": {
            "voice": voz,
            "format": "pcm16"
        },
            "messages": [
            {
                "role": "user", 
                "content": f"""
                ERES UN TIKTOKER COMERCIAL Y ESTRELLA. 
                Tu objetivo es que el cliente SIENTA que necesita este producto YA.
                
                REGLAS DE ACTUACIÓN:
                1. ¡TU VOZ DEBE SER ENÉRGICA, DINÁMICA Y MUY EMOCIONANTE! 
                2. Usa entonaciones variadas, nada de hablar plano.
                3. Haz pausas dramáticas donde veas puntos.
                4. ¡S suena a exclamación, grítalo con alegría!
                
                TRANSFORMA ESTE TEXTO en un guion de máximo 75 palabras (30-35 segundos):
                No empieces con Atencion el audio.
                
                TEXTO: {texto}
                
                """
            }
        ],
        "stream": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        
        if response.status_code == 200:
            audio_b64_chunks = []
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: ") and decoded_line != "data: [DONE]":
                        try:
                            json_data = json.loads(decoded_line[6:])
                            delta = json_data['choices'][0].get('delta', {})
                            
                            if 'audio' in delta and 'data' in delta['audio']:
                                audio_b64_chunks.append(delta['audio']['data'])
                        except json.JSONDecodeError:
                            continue
            
            if audio_b64_chunks:
                # 1. Unimos todos los pedazos de base64
                full_b64 = "".join(audio_b64_chunks)
                # 2. Decodificamos a bytes crudos (PCM16)
                raw_pcm_bytes = base64.b64decode(full_b64)
                
                # 3. FABRICAMOS EL ARCHIVO WAV EN MEMORIA
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)       # Mono (1 canal)
                    wav_file.setsampwidth(2)       # 16-bit (2 bytes por muestra)
                    wav_file.setframerate(24000)   # 24kHz (Frecuencia estándar de OpenAI)
                    wav_file.writeframes(raw_pcm_bytes)
                
                # Devolvemos el WAV perfecto y listo para Streamlit
                return wav_io.getvalue(), None
            else:
                return None, "❌ Error: La IA respondió, pero no envió fragmentos de audio."
        else:
            return None, f"❌ Error de API ({response.status_code}): {response.text}"
            
    except requests.exceptions.RequestException as e:
        return None, f"🔌 Error de conexión con la IA: {str(e)}"
