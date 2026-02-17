import streamlit as st
import pandas as pd
import requests
import io
import base64
import json
import plotly.express as px
from datetime import datetime

# --- NUEVAS LIBRERÍAS PARA UI/UX ---
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# Librerías para Excel
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule

# ==========================================
# 1. CONFIGURACIÓN Y CARGA DE ASSETS
# ==========================================
st.set_page_config(page_title="ImportPro Suite", layout="wide", page_icon="🌐")

# Función para cargar animaciones Lottie desde URL
@st.cache_data
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Cargar animación de logística global (puedes cambiar la URL por otra de lottiefiles.com)
lottie_logistics = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_s2l79gze.json")

# --- INYECCIÓN CSS AVANZADO (ANIMACIONES Y ESTILO PRO) ---
st.markdown("""
    <style>
    :root {
        --primary-color: #2E5BFF; /* Azul vibrante moderno */
        --secondary-color: #F4F7FC; /* Fondo gris claro limpio */
        --text-color: #091E42; /* Texto oscuro profesional */
        --card-shadow: 0 10px 20px rgba(0,0,0,0.08), 0 6px 6px rgba(0,0,0,0.1);
    }
    
    /* Reseteo y fondo general */
    .stApp {
        background-color: var(--secondary-color);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Ocultar elementos default de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ESTILO DE TARJETAS MÉTRICAS CON ANIMACIÓN HOVER */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E1E5F2;
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: var(--card-shadow);
        border-color: var(--primary-color);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: var(--primary-color);
        font-weight: 800;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #5E6C84;
        font-weight: 600;
    }

    /* BOTONES MODERNOS CON GRADIENTE */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        border: none;
        background: linear-gradient(135deg, #2E5BFF 0%, #00C6FF 100%);
        color: white;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(46, 91, 255, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(46, 91, 255, 0.5);
    }

    /* Inputs y text areas más limpios */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 1px solid #E1E5F2;
        padding: 10px;
        background-color: white;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(46, 91, 255, 0.2);
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: var(--text-color);
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    /* Chat */
    .stChatMessage {
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #F0F2F5;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE NEGOCIO Y ESTADO
# ==========================================
if 'historial' not in st.session_state: st.session_state['historial'] = []
if 'chat_log' not in st.session_state: 
    st.session_state['chat_log'] = [{"role": "assistant", "content": "Hola. Soy tu copiloto de importaciones. ¿Qué analizamos hoy?"}]

@st.cache_data(ttl=3600)
def fetch_trm():
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        r = requests.get(url, timeout=10)
        return float(r.json()[0]['valor'])
    except: return 4000.0

TRM_ACTUAL = fetch_trm()

# ==========================================
# 3. MOTOR IA (GEMINI FLASH STANDARD)
# ==========================================
def call_openrouter_ai(prompt, image_input=None, task="legal"):
    try: key = st.secrets["OPENROUTER_API_KEY"]
    except: return "⚠️ Error: API Key no configurada."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://importpro.app",
        "X-Title": "ImportPro WebApp"
    }
    
    if task == "legal":
        sys_msg = "Eres experto aduanero Colombia. Indica técnica y brevemente: 1. Subpartida (10 dígitos), 2. % Arancel, 3. % IVA."
    else:
        sys_msg = "Experto en E-commerce SEO Colombia. Genera: Título (60 chars), 5 bullet points persuasivos, descripción AIDA, y 10 keywords."

    content_list = [{"type": "text", "text": f"{sys_msg}\n\nInput: {prompt}"}]
    
    if image_input:
        b64_str = base64.b64encode(image_input.read()).decode('utf-8')
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}})

    payload = {
        "model": "google/gemini-2.5-flash", # Modelo estándar (inteligente)
        "messages": [{"role": "user", "content": content_list}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"Error del Proveedor IA ({response.status_code})"
    except: return "❌ Error de conexión con el servicio de IA."

# ==========================================
# 4. FUNCIONES MATEMÁTICAS
# ==========================================
def run_avion_calc(p_u, q, f_u, ar, iv, adm, p_v, c_ml):
    base_cop = (p_u * TRM_ACTUAL * q) + (f_u * TRM_ACTUAL)
    v_ar = base_cop * ar
    v_iv = (base_cop + v_ar) * iv
    c_tot = base_cop + v_ar + v_iv + adm
    c_u = c_tot / q if q > 0 else 0
    i_n = p_v * (1 - c_ml)
    viab = i_n / c_u if c_u > 0 else 0
    return {"costo_total": c_tot, "unitario": c_u, "ingreso_neto": i_n, "viabilidad": viab}

def run_barco_calc(p_u, q, env_u, tc, alt, anc, lar, caj, cbm_v, fn, p_v, c_ml):
    base_cop_china = ((p_u * q) + env_u) * TRM_ACTUAL * (1 + tc)
    vol_cbm = (alt * anc * lar / 1000000) * caj
    costo_nac = vol_cbm * cbm_v
    c_tot = base_cop_china + costo_nac + fn
    c_u = c_tot / q if q > 0 else 0
    i_n = p_v * (1 - c_ml)
    viab = i_n / c_u if c_u > 0 else 0
    return {"costo_total": c_tot, "costo_cbm": costo_nac, "volumen": vol_cbm, "unitario": c_u, "ingreso_neto": i_n, "viabilidad": viab}

# ==========================================
# 5. ESTRUCTURA DE LA APLICACIÓN WEB
# ==========================================

# --- HEADER / HERO SECTION ---
col_hero1, col_hero2 = st.columns([2, 1])
with col_hero1:
    st.title("🌐 ImportPro Suite")
    st.markdown("### Inteligencia Logística y Comercial")
    st.write(f"**Indicador TRM Hoy:** `${TRM_ACTUAL:,.2f} COP` | **Estado IA:** `Online (Gemini Flash)`")
with col_hero2:
    # Animación Lottie en el header
    if lottie_logistics:
        st_lottie(lottie_logistics, height=150, key="hero_anim")

st.divider()

# --- BARRA DE NAVEGACIÓN HORIZONTAL (NUEVO) ---
selected_nav = option_menu(
    menu_title=None, # Ocultar título del menú
    options=["Simulador Aéreo", "Simulador Marítimo", "Carga Masiva", "Inteligencia de Mercado", "Reportes & BI"],
    icons=["airplane-engines", "tsunami", "file-earmark-spreadsheet", "rocket-takeoff", "bar-chart-line"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "5px", "background-color": "#ffffff", "border-radius": "12px", "box-shadow": "0 4px 12px rgba(0,0,0,0.05)"},
        "icon": {"color": "#2E5BFF", "font-size": "18px"}, 
        "nav-link": {"font-size": "15px", "text-align": "center", "margin": "0px 5px", "--hover-color": "#F4F7FC", "font-weight": "500"},
        "nav-link-selected": {"background-color": "#2E5BFF", "color": "white", "font-weight": "700"},
    }
)

# ==========================================
# 6. CONTENIDO DINÁMICO SEGÚN NAVEGACIÓN
# ==========================================

if selected_nav == "Simulador Aéreo":
    st.subheader("✈️ Cálculo de Importación Courier/Aéreo")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            n_p = st.text_input("Producto", "Smartwatch Gen5", key="n1")
            p_u = st.number_input("Precio Unit (USD)", 15.0)
            q = st.number_input("Cantidad Total", 100)
        with col2:
            f_u = st.number_input("Flete Total (USD)", 250.0)
            ar = st.number_input("Arancel Decimal (Ej: 0.10)", 0.10, format="%.2f")
            iv = st.number_input("IVA Decimal (Ej: 0.19)", 0.19, format="%.2f")
        with col3:
            adm = st.number_input("Costos Admin/Agente (COP)", 120000.0)
            p_v = st.number_input("Precio Venta Proyectado (COP)", 180000.0)
            c_ml = st.number_input("Comisión Marketplace %", 0.24, format="%.2f")

        if st.button("Calcular Rentabilidad Aérea 🚀"):
            with st.spinner("Procesando costos..."):
                res = run_avion_calc(p_u, q, f_u, ar, iv, adm, p_v, c_ml)
                st.markdown("---")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Inversión Total", f"${res['costo_total']:,.0f}")
                r2.metric("Costo Unitario Real", f"${res['unitario']:,.0f}")
                r3.metric("Margen Neto Unitario", f"${res['ingreso_neto'] - res['unitario']:,.0f}")
                r4.metric("Ratio Viabilidad", f"{res['viabilidad']:.2f}x", delta_color="off")
                st.session_state['historial'].append({"Producto": n_p, "Método": "Avión", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})
                st.success("Simulación guardada exitosamente.")

elif selected_nav == "Simulador Marítimo":
    st.subheader("🚢 Cálculo de Importación LCL (Consolidado)")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            n_p2 = st.text_input("Producto", "Sillas Gamers", key="n2")
            p_u2 = st.number_input("Precio USD", 45.0)
            q2 = st.number_input("Cantidad", 50, key="q2")
        with col2:
            env_u = st.number_input("Envío Origen (USD)", 30.0)
            alt, anc, lar = st.number_input("Alto cm", 70.0), st.number_input("Ancho cm", 60.0), st.number_input("Largo cm", 20.0)
        with col3:
            caj = st.number_input("Total Cajas", 25)
            cbm_v = st.number_input("Costo CBM Nacionalización (COP)", 2400000.0)
            p_v2 = st.number_input("Precio Venta Proyectado (COP)", 650000.0)

    if st.button("Calcular Rentabilidad Marítima 🌊"):
        with st.spinner("Calculando volumetría y costos..."):
            res = run_barco_calc(p_u2, q2, env_u, 0.03, alt, anc, lar, caj, cbm_v, 200000.0, p_v2, 0.24)
            st.markdown("---")
            st.info(f"📊 **Datos Logísticos:** Volumen Total: `{res['volumen']:.4f} m³` | Costo Nacionalización (CBM): `${res['costo_cbm']:,.0f}`")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Inversión Total", f"${res['costo_total']:,.0f}")
            r2.metric("Costo Unitario Real", f"${res['unitario']:,.0f}")
            r3.metric("Margen Neto Unitario", f"${res['ingreso_neto'] - res['unitario']:,.0f}")
            r4.metric("Ratio Viabilidad", f"{res['viabilidad']:.2f}x")
            st.session_state['historial'].append({"Producto": n_p2, "Método": "Barco", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})

elif selected_nav == "Carga Masiva":
    st.subheader("📁 Procesador de Lotes (Excel)")
    st.markdown("Carga tu plantilla estandarizada para procesar múltiples SKUs en segundos.")
    up_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")
    
    if up_file:
        with st.container(border=True):
            st.info("Archivo detectado. Listo para procesar.")
            if st.button("🚀 Ejecutar Análisis Masivo"):
                with st.spinner("Procesando filas..."):
                    try:
                        # Simulación de proceso (aquí iría tu lógica real de iteración)
                        st.session_state['historial'].append({"Producto": "Lote Masivo Ejemplo", "Método": "Masivo", "Costo Unitario (Res)": 50000, "Ingreso ML (Res)": 80000, "Viabilidad (Res)": 1.6})
                        st.success("✅ Lote procesado e integrado al reporte general.")
                    except: st.error("Error en el formato del archivo.")

elif selected_nav == "Inteligencia de Mercado":
    col_ia1, col_ia2 = st.columns([1, 2])
    with col_ia1:
        st.markdown("### 🧠 Asistente Técnico & SEO")
        st.write("Motor: Gemini 2.5 Flash. Multimodal.")
        
        mode_switch = st.radio("Modo de Operación:", ["🧑‍⚖️ Clasificación Aduanera", "🚀 Optimización SEO (ML)"], horizontal=True)
        
        if mode_switch == "🚀 Optimización SEO (ML)":
            img_upload = st.file_uploader("📸 Análisis Visual (Opcional)", type=["jpg", "png"], help="Sube un pantallazo del producto para un análisis más profundo.")
        else:
            img_upload = None

    with col_ia2:
        with st.container(border=True, height=500):
            for m in st.session_state['chat_log']:
                with st.chat_message(m["role"]): st.markdown(m["content"])

        user_input = st.chat_input("Escribe tu consulta técnica o pega la descripción del producto aquí...")
        if user_input:
            st.session_state['chat_log'].append({"role": "user", "content": user_input})
            task_mode = "legal" if mode_switch == "🧑‍⚖️ Clasificación Aduanera" else "marketing"
            
            with st.spinner("IA Analizando..."):
                ai_response = call_openrouter_ai(user_input, image_input=img_upload, task=task_mode)
                st.session_state['chat_log'].append({"role": "assistant", "content": ai_response})
            st.rerun()

elif selected_nav == "Reportes & BI":
    st.subheader("📊 Business Intelligence & Exportación")
    
    if not st.session_state['historial']:
        st.info("ℹ️ Realiza al menos una simulación para activar el dashboard de análisis.")
        if lottie_logistics: st_lottie(lottie_logistics, height=300, key="empty_state")
    else:
        df_h = pd.DataFrame(st.session_state['historial'])
        
        with st.container(border=True):
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            col_metrics1.metric("Total Productos Analizados", len(df_h))
            avg_viab = df_h['Viabilidad (Res)'].mean()
            col_metrics2.metric("Viabilidad Promedio del Portafolio", f"{avg_viab:.2f}x", delta=f"{avg_viab-1.5:.2f}" if avg_viab > 1.5 else f"{avg_viab-1.5:.2f}")
            col_metrics3.metric("Costo Unitario Promedio", f"${df_h['Costo Unitario (Res)'].mean():,.0f}")

        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.bar(df_h, x='Producto', y=['Costo Unitario (Res)', 'Ingreso ML (Res)'], 
                          barmode='group', title="Análisis Financiero (COP)", template="plotly_white", color_discrete_sequence=['#FF6B6B', '#51CF66'])
            fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = px.bar(df_h, x='Producto', y='Viabilidad (Res)', color='Viabilidad (Res)',
                          color_continuous_scale=['#FF6B6B', '#FFD93D', '#51CF66'], title="Semáforo de Rentabilidad", template="plotly_white")
            fig2.add_hline(y=1.5, line_dash="dot", annotation_text="Meta (1.5x)", line_color="#2E5BFF")
            fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df_h, use_container_width=True, hide_index=True)
        
        # Excel Export Pro
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as wr:
            df_h.to_excel(wr, index=False, sheet_name='Reporte Gerencial')
            ws = wr.sheets['Reporte Gerencial']
            for cell in ws[1]:
                cell.fill = PatternFill(start_color="2E5BFF", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal='center')
            
            # Autoajuste básico de columnas
            for col in ws.columns:
                 col_letter = col[0].column_letter
                 ws.column_dimensions[col_letter].width = 20
                 
            ws.conditional_formatting.add(f"E2:E{len(df_h)+1}", CellIsRule(operator='greaterThan', formula=['1.5'], fill=PatternFill(start_color="C6EFCE", fill_type="solid")))
            ws.conditional_formatting.add(f"E2:E{len(df_h)+1}", CellIsRule(operator='lessThan', formula=['1.2'], fill=PatternFill(start_color="FFC7CE", fill_type="solid")))
            
        st.download_button("📥 Descargar Reporte Excel Profesional", buffer.getvalue(), "Reporte_ImportPro.xlsx", type="primary")
        
        if st.button("🗑️ Purgar Datos del Historial"):
            st.session_state['historial'] = []
            st.rerun()
