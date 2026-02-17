import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import CellIsRule

# ==========================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Calculadora Pro", layout="wide", page_icon="📦")

# ==========================================
# 🎨 ESTILO VISUAL PROFESIONAL (NUEVO)
# ==========================================
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.block-container {
    padding-top: 2rem;
}
h1, h2, h3 {
    margin-top: 20px;
}
div[data-testid="stMetric"] {
    background-color: #1e293b;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MEMORIA DE LA APP
# ==========================================
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

if 'mensajes_chat' not in st.session_state:
    st.session_state['mensajes_chat'] = [
        {"role": "assistant", "content": "¡Hola! Asistente aduanero 100% operativo. ¿Qué producto consultamos hoy?"}
    ]

def guardar_simulacion(nombre_producto, metodo, inputs, costo_u, ingreso_n, viabilidad):
    fila = {
        "Producto": nombre_producto, "Método": metodo, **inputs,
        "Costo Unitario (Res)": costo_u, "Ingreso ML (Res)": ingreso_n, "Viabilidad (Res)": viabilidad
    }
    st.session_state['historial'].append(fila)
    st.success(f"✅ '{nombre_producto}' guardado exitosamente.")

# ==========================================
# 2. OBTENER TRM REAL
# ==========================================
@st.cache_data
def obtener_trm_colombia():
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        return float(requests.get(url).json()[0]['valor'])
    except:
        return 4000.0

TRM_HOY = obtener_trm_colombia()

# ==========================================
# 3. IA OPENROUTER
# ==========================================
def consultar_openrouter(prompt):
    modelos_a_probar = [
        "google/gemini-2.5-flash",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "google/gemma-3-27b:free"
    ]
    
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except:
        return "⚠️ Error de configuración interna. (Falta API Key)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://calculadorapro.com",
        "X-Title": "Calculadora Aduanas"
    }
    
    instruccion = """
    Eres un experto en aduanas en Colombia.
    1. Subpartida sugerida (10 dígitos).
    2. % Arancel.
    3. % IVA.
    Advierte que debe verificarse oficialmente.
    """

    for modelo in modelos_a_probar:
        try:
            data = {
                "model": modelo,
                "messages": [
                    {"role": "system", "content": instruccion},
                    {"role": "user", "content": prompt}
                ]
            }
            respuesta = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if respuesta.status_code == 200:
                return respuesta.json()['choices'][0]['message']['content']
            elif respuesta.status_code == 429:
                continue
        except:
            continue

    return "❌ Servidores ocupados."

# ==========================================
# FUNCIONES MATEMÁTICAS (SIN CAMBIOS)
# ==========================================
def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0
    precio_cop = precio_usd * trm
    flete_cop = flete_usd * trm
    base_impuestos = (precio_cop * cantidad) + flete_cop
    valor_arancel = base_impuestos * arancel_pct
    valor_iva = (base_impuestos + valor_arancel) * iva_pct
    costo_total = base_impuestos + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = costo_total / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_total, costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0)

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_pedido_cop, costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0)

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"### 💱 TRM Oficial del día: `${TRM_HOY:,.2f} COP`")

tab1, tab2, tab3, tab_comparador = st.tabs([
    "✈️ Avión", "🛒 AliExpress", "📊 Comparador"
])

# --- AVION ---
with tab1:
    st.subheader("Simulación Avión")
    p_usd = st.number_input("Precio USD", value=1.0)
    cant = st.number_input("Cantidad", value=100)
    flete = st.number_input("Flete USD", value=200.0)
    ar = st.number_input("Arancel", value=0.15)
    iva = st.number_input("IVA", value=0.19)
    adm = st.number_input("Tarifa Admin", value=100000.0)
    pml = st.number_input("Precio ML", value=50000.0)
    cml = st.number_input("Comisión ML", value=0.24)

    if st.button("Calcular Avión"):
        c_tot, c_u, i_n, v = calcular_alibaba_avion(
            p_usd, TRM_HOY, cant, flete, ar, iva, adm, pml, cml
        )
        estado = "🟢 Óptimo" if v >= 1.5 else "🟡 Revisar"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Inversión Total", f"${c_tot:,.0f}")
        col2.metric("Costo Unitario", f"${c_u:,.2f}")
        col3.metric("Ingreso Neto", f"${i_n:,.2f}")
        col4.metric("Viabilidad", f"{v:,.2f}x", delta=estado)

# --- ALIEXPRESS ---
with tab2:
    st.subheader("Simulación AliExpress")
    costo = st.number_input("Costo Pedido", value=300000.0)
    cant = st.number_input("Cantidad Productos", value=10)
    pml = st.number_input("Precio ML", value=100000.0)
    cml = st.number_input("Comisión ML", value=0.24)

    if st.button("Calcular AliExpress"):
        c_tot, c_u, i_n, v = calcular_aliexpress(costo, cant, pml, cml)
        estado = "🟢 Óptimo" if v >= 1.5 else "🟡 Revisar"
        col1, col2, col3 = st.columns(3)
        col1.metric("Costo Unitario", f"${c_u:,.2f}")
        col2.metric("Ingreso Neto", f"${i_n:,.2f}")
        col3.metric("Viabilidad", f"{v:,.2f}x", delta=estado)

# --- COMPARADOR ---
with tab_comparador:
    st.subheader("Análisis Visual")

    if len(st.session_state['historial']) > 0:
        df = pd.DataFrame(st.session_state['historial'])

        st.markdown("### 📌 Resumen Ejecutivo")

        promedio = df["Viabilidad (Res)"].mean()
        mejor = df.loc[df["Viabilidad (Res)"].idxmax()]["Producto"]

        c1, c2 = st.columns(2)
        c1.metric("Viabilidad Promedio", f"{promedio:.2f}x")
        c2.metric("Producto Más Rentable", mejor)

        fig = px.bar(
            df,
            x="Producto",
            y="Viabilidad (Res)",
            color="Viabilidad (Res)",
            color_continuous_scale="RdYlGn"
        )

        fig.update_layout(
            plot_bgcolor='#0f172a',
            paper_bgcolor='#0f172a',
            font_color='white'
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aún no hay datos guardados.")
