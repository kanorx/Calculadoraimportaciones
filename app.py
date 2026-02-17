import streamlit as st
import pandas as pd
import requests
import io
import base64
import json
import plotly.express as px
from datetime import datetime

# Librerías para diseño y lógica de Excel
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO UI (CSS PRO)
# ==========================================
st.set_page_config(page_title="ImportPro Intelligence", layout="wide", page_icon="🏢")

# Inyección de CSS para transformar Streamlit en una plataforma SaaS
st.markdown("""
    <style>
    /* Estética General */
    .main { background-color: #f8f9fc; font-family: 'Inter', sans-serif; }
    
    /* Tarjetas de Métricas (Dashboard Look) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #4e73df;
    }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #2e59d9; font-weight: 700; }
    
    /* Botones Premium */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #4e73df;
        color: white;
        font-weight: 700;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #2e59d9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    
    /* Tabs Personalizados */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #fff;
        border-radius: 10px 10px 0 0;
        padding: 12px 25px;
        font-weight: 600;
        color: #4e73df;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #2e59d9; }
    
    /* Chat bubbles */
    .stChatMessage { border-radius: 15px; margin-bottom: 12px; background: white; border: 1px solid #eaecf4; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA DE DATOS Y PERSISTENCIA
# ==========================================
if 'historial' not in st.session_state: st.session_state['historial'] = []
if 'chat_log' not in st.session_state: 
    st.session_state['chat_log'] = [{"role": "assistant", "content": "Sistema listo. ¿Qué subpartida o estrategia de venta analizamos hoy?"}]

@st.cache_data(ttl=3600)
def fetch_trm():
    """Obtiene la TRM oficial de Colombia."""
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        r = requests.get(url, timeout=10)
        return float(r.json()[0]['valor'])
    except: return 4000.0

TRM_ACTUAL = fetch_trm()

# ==========================================
# 3. MOTOR IA (MULTIMODAL / SILENCIOSO)
# ==========================================
def call_openrouter_ai(prompt, image_input=None, task="legal"):
    """
    Motor Gemini 2.5 Flash estándar para máxima precisión.
    Costo por consulta estimado: $0.000441 USD.
    """
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except: return "⚠️ Error: API Key no encontrada."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://importpro.co",
        "X-Title": "ImportPro Suite"
    }
    
    # Contexto dinámico según la pestaña
    if task == "legal":
        sys_msg = "Eres experto aduanero en Colombia. Indica: 1. Subpartida (10 dígitos), 2. % Arancel, 3. % IVA. Sé técnico."
    else:
        sys_msg = "Experto en E-commerce y SEO. Genera Título (60 carac), 5 viñetas de valor, descripción AIDA y keywords."

    content_list = [{"type": "text", "text": f"{sys_msg}\n\nPregunta: {prompt}"}]
    
    if image_input:
        b64_str = base64.b64encode(image_input.read()).decode('utf-8')
        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}})

    payload = {
        "model": "google/gemini-2.5-flash", # Modelo estándar (No Lite) para mayor inteligencia
        "messages": [{"role": "user", "content": content_list}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=25)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"Error API: {response.status_code}"
    except: return "❌ Fallo de conexión con la IA."

# ==========================================
# 4. FUNCIONES MATEMÁTICAS FINANCIERAS
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
    costo_nacionalizacion = vol_cbm * cbm_v
    c_tot = base_cop_china + costo_nacionalizacion + fn
    c_u = c_tot / q if q > 0 else 0
    i_n = p_v * (1 - c_ml)
    viab = i_n / c_u if c_u > 0 else 0
    return {"costo_total": c_tot, "costo_cbm": costo_nacionalizacion, "volumen": vol_cbm, "unitario": c_u, "ingreso_neto": i_n, "viabilidad": viab}

# ==========================================
# 5. SIDEBAR - ASISTENTE INTEGRADO
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3252/3252890.png", width=80)
    st.markdown("### Asistente Aduanero")
    st.caption("Respaldo: Gemini 2.5 Flash")
    st.divider()
    
    for m in st.session_state['chat_log']:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    if user_q := st.chat_input("¿Qué arancel aplica para...?"):
        st.session_state['chat_log'].append({"role": "user", "content": user_q})
        with st.chat_message("user"): st.write(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                r_ia = call_openrouter_ai(user_q, task="legal")
                st.write(r_ia)
                st.session_state['chat_log'].append({"role": "assistant", "content": r_ia})
    
    if st.button("🗑️ Limpiar Historial de Chat"):
        st.session_state['chat_log'] = []
        st.rerun()

# ==========================================
# 6. DASHBOARD PRINCIPAL - TABS
# ==========================================
st.title("🏦 ImportPro: Dashboard de Inteligencia")
st.info(f"💵 TRM Oficial del día: **${TRM_ACTUAL:,.2f} COP**")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✈️ Avión (Courier)", "🚢 Barco (LCL)", "🛒 AliExpress", "📁 Carga Masiva", "📊 Reporte Gerencial", "🚀 Marketing ML"
])

# --- TAB 1: AVION ---
with tab1:
    st.subheader("Simulación de Importación Aérea")
    col1, col2, col3 = st.columns(3)
    with col1:
        n_p = st.text_input("Producto", "Gadget Electrónico", key="n1")
        p_u = st.number_input("Precio Unitario (USD)", 12.50)
        q = st.number_input("Cantidad", 150)
    with col2:
        f_u = st.number_input("Flete Total (USD)", 420.0)
        ar = st.number_input("Arancel % (Ej: 0.10)", 0.10, format="%.2f")
        iv = st.number_input("IVA %", 0.19, format="%.2f")
    with col3:
        adm = st.number_input("Gasto de Agente (COP)", 115000.0)
        p_v = st.number_input("P. Venta ML (COP)", 165000.0)
        c_ml = st.number_input("Comisión ML %", 0.24, format="%.2f")

    if st.button("Calcular Inversión Aérea", key="b1"):
        res = run_avion_calc(p_u, q, f_u, ar, iv, adm, p_v, c_ml)
        st.divider()
        st.markdown(f"#### Resultados para: {n_p}")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("INVERSIÓN TOTAL", f"${res['costo_total']:,.0f}")
        r2.metric("COSTO UNITARIO", f"${res['unitario']:,.0f}")
        r3.metric("INGRESO NETO", f"${res['ingreso_neto']:,.0f}")
        r4.metric("VIABILIDAD", f"{res['viabilidad']:.2f}x")
        st.session_state['historial'].append({"Producto": n_p, "Método": "Avión", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})

# --- TAB 2: BARCO ---
with tab2:
    st.subheader("Simulación Marítima LCL")
    col1, col2, col3 = st.columns(3)
    with col1:
        n_p2 = st.text_input("Producto", "Sillas de Oficina", key="n2")
        p_u2 = st.number_input("Precio USD", 35.0)
        q2 = st.number_input("Cantidad", 48, key="q2")
    with col2:
        env_u = st.number_input("Envío Puerto Origen (USD)", 25.0)
        alt = st.number_input("Alto cm", 60.0)
        anc = st.number_input("Ancho cm", 60.0)
        lar = st.number_input("Largo cm", 60.0)
    with col3:
        caj = st.number_input("Cajas", 12)
        cbm_v = st.number_input("Valor CBM COP (Nacionalización)", 2450000.0)
        p_v2 = st.number_input("P. Venta ML COP", 550000.0)

    if st.button("Calcular Inversión Marítima"):
        res = run_barco_calc(p_u2, q2, env_u, 0.03, alt, anc, lar, caj, cbm_v, 180000.0, p_v2, 0.24)
        st.divider()
        st.info(f"📐 Volumen Total: **{res['volumen']:.4f} m³** | Nacionalización CBM: **${res['costo_cbm']:,.0f}**")
        r1, r2, r3 = st.columns(3)
        r1.metric("INVERSIÓN TOTAL", f"${res['costo_total']:,.0f}")
        r2.metric("COSTO UNITARIO", f"${res['unitario']:,.0f}")
        r3.metric("VIABILIDAD", f"{res['viabilidad']:.2f}x")
        st.session_state['historial'].append({"Producto": n_p2, "Método": "Barco", "Costo Unitario (Res)": res['unitario'], "Ingreso ML (Res)": res['ingreso_neto'], "Viabilidad (Res)": res['viabilidad']})

# --- TAB 4: CARGA MASIVA ---
with tab4:
    st.subheader("📁 Procesador de Inventario Masivo")
    st.markdown("Carga tu archivo Excel para procesar múltiples simulaciones de golpe.")
    up_file = st.file_uploader("Subir Plantilla (.xlsx)", type=["xlsx"])
    
    if up_file and st.button("🚀 Procesar Archivo"):
        try:
            df_up = pd.read_excel(up_file).fillna(0)
            for _, row in df_up.iterrows():
                # Lógica simplificada de carga
                st.session_state['historial'].append({
                    "Producto": row.get('Producto', 'Fila'),
                    "Método": "Masivo",
                    "Costo Unitario (Res)": 0, "Ingreso ML (Res)": 0, "Viabilidad (Res)": 0
                })
            st.success("¡Datos cargados al historial!")
        except: st.error("Error procesando el archivo. Verifica el formato.")

# --- TAB 5: REPORTE GERENCIAL ---
with tab5:
    if st.session_state['historial']:
        df_h = pd.DataFrame(st.session_state['historial'])
        st.subheader("📊 Análisis Comparativo")
        
        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.bar(df_h, x='Producto', y=['Costo Unitario (Res)', 'Ingreso ML (Res)'], 
                          barmode='group', title="Costos vs Ingresos (COP)", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = px.bar(df_h, x='Producto', y='Viabilidad (Res)', color='Viabilidad (Res)',
                          color_continuous_scale='RdYlGn', title="Ratio de Rentabilidad", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df_h, use_container_width=True)
        
        # Exportación Excel Pro con openpyxl
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as wr:
            df_h.to_excel(wr, index=False, sheet_name='Simulaciones')
            ws = wr.sheets['Simulaciones']
            # Estilo cabecera
            for cell in ws[1]:
                cell.fill = PatternFill(start_color="4E73DF", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
            # Semáforo de Viabilidad
            ws.conditional_formatting.add(f"D2:D{len(df_h)+1}", CellIsRule(operator='greaterThan', formula=['1.5'], fill=PatternFill(start_color="C6EFCE", fill_type="solid")))
        
        st.download_button("📥 Descargar Reporte en Excel", buffer.getvalue(), "Estrategia_Importacion.xlsx", type="primary")
    else: st.info("Simula un producto para activar las métricas del dashboard.")

# --- TAB 6: MARKETING ML ---
with tab6:
    st.subheader("🚀 Optimizador: AliExpress ➜ Mercado Libre")
    st.markdown("Transforma datos técnicos o imágenes en publicaciones de alto impacto.")
    
    mcol1, mcol2 = st.columns([1, 2])
    with mcol1:
        ali_img = st.file_uploader("Captura de Pantalla (AliExpress)", type=["jpg", "png", "jpeg"])
    with mcol2:
        ali_txt = st.text_area("Copia el texto técnico aquí:", height=180, placeholder="Pega descripción, especificaciones...")
    
    if st.button("✨ Generar Contenido Estratégico"):
        if ali_txt or ali_img:
            with st.spinner("IA analizando psicología de ventas..."):
                res_mkt = call_openrouter_ai(ali_txt, image_input=ali_img, task="marketing")
                st.markdown("---")
                st.success("Estrategia SEO generada:")
                st.markdown(res_mkt)
        else: st.warning("Por favor proporciona texto o una imagen.")
