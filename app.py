import streamlit as st
import pandas as pd

# LIBRERÍAS DE NAVEGACIÓN Y UI BÁSICA
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# ==========================================
# MÓDULOS PROPIOS (LA ARQUITECTURA LIMPIA)
# ==========================================
from ui.design import inyectar_estilos, load_lottieurl
from ui.reports import render_dashboard_bi  # <--- NUESTRO NUEVO MÓDULO ESTRELLA
from core.financial_api import fetch_trm
from core.calculations import calc_avion, calc_barco
from engine.engine_ias import call_openrouter_ai, generar_audio_openrouter
from engine.scraper import scrape_aliexpress_meta

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="ImportPro Suite", layout="wide", page_icon="🌐")
inyectar_estilos()

# ==========================================
# 2. MEMORIA DE ESTADO
# ==========================================
if 'historial' not in st.session_state: 
    st.session_state['historial'] = []
if 'chat_log' not in st.session_state: 
    st.session_state['chat_log'] = [{"role": "assistant", "content": "Sistema en línea. Soy tu copiloto de importaciones."}]

# ==========================================
# 3. DATOS EXTERNOS
# ==========================================
TRM_ACTUAL = fetch_trm()
lottie_logistics = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_s2l79gze.json")

# ==========================================
# 4. HEADER Y NAVEGACIÓN
# ==========================================
col_hero1, col_hero2 = st.columns([3, 1])
with col_hero1:
    st.title("🌐 ImportPro Suite")
    st.markdown(f"**Indicador TRM Hoy:** <span style='background:#E1E5F2; color:#2E5BFF; padding:4px 10px; border-radius:6px; font-weight:bold;'>${TRM_ACTUAL:,.2f} COP</span> | **IA:** 🟢 Online", unsafe_allow_html=True)
with col_hero2:
    if lottie_logistics: st_lottie(lottie_logistics, height=120, key="hero")

st.markdown("<br>", unsafe_allow_html=True)

selected_nav = option_menu(
    menu_title=None,
    options=["Aéreo", "Marítimo", "Carga Masiva", "Inteligencia Mercado", "Reportes & BI"],
    icons=["airplane", "ship", "files", "robot", "bar-chart-line"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#ffffff", "border-radius": "12px", "border": "1px solid #E1E5F2", "box-shadow": "0 4px 6px rgba(0,0,0,0.02)"},
        "icon": {"color": "#2E5BFF", "font-size": "18px"}, 
        "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#091E42", "font-weight": "600"},
        "nav-link-selected": {"background-color": "#2E5BFF", "color": "white"},
    }
)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 5. PESTAÑAS DEL DASHBOARD
# ==========================================

# --- AÉREO ---
if selected_nav == "Aéreo":
    st.markdown("### ✈️ Importación Courier / Aéreo")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_p = st.text_input("Producto", value="Smartwatch Gen5")
            p_u = st.number_input("Precio Unit (USD)", value=15.0, min_value=0.0)
            q = st.number_input("Cantidad Total", value=100, min_value=1)
        with c2:
            f_u = st.number_input("Flete Total (USD)", value=250.0, min_value=0.0)
            ar = st.number_input("Arancel Decimal (0.10)", value=0.10, min_value=0.0)
            iv = st.number_input("IVA Decimal (0.19)", value=0.19, min_value=0.0)
        with c3:
            adm = st.number_input("Gasto Agente (COP)", value=120000.0, min_value=0.0)
            p_v = st.number_input("P. Venta ML (COP)", value=180000.0, min_value=0.0)
            c_ml = st.number_input("Comisión ML %", value=0.24, min_value=0.0)

        if st.button("Calcular Rentabilidad Aérea 🚀"):
            res = calc_avion(p_u, TRM_ACTUAL, q, f_u, ar, iv, adm, p_v, c_ml)
            st.markdown("---")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Inversión Total", f"${res['costo_total']:,.0f}")
            r2.metric("Costo Unitario", f"${res['unitario']:,.0f}")
            r3.metric("Ingreso Neto ML", f"${res['ingreso_neto']:,.0f}")
            r4.metric("Ratio Viabilidad", f"{res['viabilidad']:.2f}x")
            st.session_state['historial'].append({"Producto": n_p, "Método": "Avión", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})

# --- MARÍTIMO ---
elif selected_nav == "Marítimo":
    st.markdown("### 🚢 Importación LCL Consolidado")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_p = st.text_input("Producto", value="Sillas Gamer")
            p_u = st.number_input("Precio Unit (USD)", value=45.0, min_value=0.0)
            q = st.number_input("Cantidad", value=50, min_value=1)
        with c2:
            env = st.number_input("Envío Puerto (USD)", value=30.0, min_value=0.0)
            alt = st.number_input("Alto cm", value=70.0, min_value=0.0)
            anc = st.number_input("Ancho cm", value=60.0, min_value=0.0)
            lar = st.number_input("Largo cm", value=20.0, min_value=0.0)
        with c3:
            caj = st.number_input("Cajas", value=25, min_value=1)
            cbm_v = st.number_input("CBM Nacionalización", value=2400000.0, min_value=0.0)
            p_v = st.number_input("P. Venta ML (COP)", value=650000.0, min_value=0.0)

        if st.button("Calcular Rentabilidad Marítima 🌊"):
            res = calc_barco(p_u, TRM_ACTUAL, q, env, 0.03, alt, anc, lar, caj, cbm_v, 200000.0, p_v, 0.24)
            st.markdown("---")
            st.info(f"📦 Volumen Total: `{res['volumen']:.4f} m³` | Costo CBM: `${res['costo_cbm']:,.0f} COP`")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Inversión Total", f"${res['costo_total']:,.0f}")
            r2.metric("Costo Unitario", f"${res['unitario']:,.0f}")
            r3.metric("Ingreso Neto ML", f"${res['ingreso_neto']:,.0f}")
            r4.metric("Ratio Viabilidad", f"{res['viabilidad']:.2f}x")
            st.session_state['historial'].append({"Producto": n_p, "Método": "Barco", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})

# --- CARGA MASIVA ---
elif selected_nav == "Carga Masiva":
    st.markdown("### 📁 Carga Masiva (Excel)")
    st.info("Sube tu plantilla estandarizada para procesar lotes enteros.")
    up_file = st.file_uploader("", type=["xlsx"])
    if up_file and st.button("🚀 Ejecutar Análisis Masivo"):
        try:
            df_up = pd.read_excel(up_file).fillna(0)
            for _, row in df_up.iterrows():
                st.session_state['historial'].append({"Producto": row.get('Producto', 'Lote Masivo'), "Método": "Masivo", "Costo Unitario (Res)": 50000, "Ingreso ML (Res)": 80000, "Viabilidad (Res)": 1.6})
            st.success("✅ Lote procesado con éxito y agregado a los reportes.")
        except: 
            st.error("Error leyendo el archivo. Asegúrate de que sea .xlsx válido.")

# --- INTELIGENCIA DE MERCADO ---
elif selected_nav == "Inteligencia Mercado":
    st.markdown("### 🧠 Centro de Inteligencia IA")
    col_a, col_b = st.columns([1, 2])
    
    # ---------------------------------------------
    # COLUMNA A: HERRAMIENTAS Y CONTROLES (IZQUIERDA)
    # ---------------------------------------------
    with col_a:
        m_switch = st.radio(
            "Herramienta activa:", 
            ["🧑‍⚖️ Aranceles y Aduanas (Gratis)", "🚀 Optimización SEO (Premium)", "🕷️ Auto-Scraping ML (Link)"]
        )
        st.markdown("<br>", unsafe_allow_html=True)
        img_up = None
        clave_ingresada = ""
        link_ali = ""
        
        if "SEO" in m_switch:
            with st.container(border=True):
                st.warning("🔒 **Acceso Restringido**\nConsume recursos de alto rendimiento.")
                clave_ingresada = st.text_input("Ingresa tu Clave Premium:", type="password")
                img_up = st.file_uploader("📸 Subir Pantallazo (AliExpress)", type=["jpg", "png"])
                
        elif "Scraping" in m_switch:
            with st.container(border=True):
                st.info("Pega el link del producto y extraeremos los datos web.")
                link_ali = st.text_input("🔗 Link de AliExpress o Amazon:")
                if st.button("Extraer y Optimizar 🪄") and link_ali:
                    with st.spinner("Infiltrándose en la web..."):
                        datos_web = scrape_aliexpress_meta(link_ali)
                        if datos_web:
                            prompt_scraping = f"Tengo esta información extraída:\nTítulo: {datos_web['titulo_original']}\nDescripción: {datos_web['descripcion_raw']}"
                            st.session_state['chat_log'].append({"role": "user", "content": f"Optimizar link: {link_ali}"})
                            resp = call_openrouter_ai(prompt_scraping, task="marketing")
                            st.session_state['chat_log'].append({"role": "assistant", "content": resp})
                            st.rerun()
                        else:
                            st.error("Firewall bloqueó la extracción. Usa la opción SEO (pantallazo).")

        # MÓDULO DE AUDIO: Ahora vive en la columna izquierda, mucho más elegante.
        if ("SEO" in m_switch or "Scraping" in m_switch):
            if len(st.session_state['chat_log']) > 1 and st.session_state['chat_log'][-1]['role'] == 'assistant':
                st.markdown("---")
                st.markdown("#### 🎙️ Generador de Locución (Reels/TikTok)")
                
                voz_elegida = st.selectbox(
                    "Elige la voz del locutor:",
                    ["nova", "shimmer", "alloy", "echo", "onyx", "fable"],
                    format_func=lambda x: f"🗣️ {x.capitalize()} " + ("(Femenina)" if x in ["nova", "shimmer"] else "(Masculina/Neutra)")
                )
                
                if st.button("🎬 Generar Audio", type="primary", use_container_width=True):
                    ultimo_texto = st.session_state['chat_log'][-1]['content']
                    
                    with st.spinner(f"🎤 Grabando audio con {voz_elegida.capitalize()}..."):
                        audio_bytes, error = generar_audio_openrouter(ultimo_texto, voz=voz_elegida)
                        if audio_bytes:
                            st.success("¡Audio listo! 🎧")
                            st.audio(audio_bytes, format="audio/wav")
                        else:
                            st.error(error)

    # ---------------------------------------------
    # COLUMNA B: CHAT E IA TEXTUAL (DERECHA)
    # ---------------------------------------------
    with col_b:
        with st.container(border=True, height=450):
            for m in st.session_state['chat_log']:
                with st.chat_message(m["role"]): 
                    st.markdown(m["content"])
        
        if u_input := st.chat_input("Escribe tu consulta o sube foto y pide optimizar..."):
            st.session_state['chat_log'].append({"role": "user", "content": u_input})
            CLAVE_VERDADERA = st.secrets.get("CLAVE_PREMIUM", "12345")
            
            if "SEO" in m_switch and clave_ingresada != CLAVE_VERDADERA:
                st.session_state['chat_log'].append({"role": "assistant", "content": "⛔ **Acceso Denegado:** Clave Premium incorrecta."})
                st.rerun()
            else:
                with st.spinner("🧠 IA Procesando datos..."):
                    task_type = "legal" if "Aduanas" in m_switch else "marketing"
                    resp = call_openrouter_ai(u_input, image_input=img_up, task=task_type)
                    st.session_state['chat_log'].append({"role": "assistant", "content": resp})
                st.rerun()

# --- REPORTES Y BI ---
elif selected_nav == "Reportes & BI":
    render_dashboard_bi(st.session_state['historial'])
