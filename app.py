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
# 🎨 ESTILO VISUAL PRO (NO AFECTA LÓGICA)
# ==========================================
st.markdown("""
<style>
body { background-color: #0f172a; }

.block-container { padding-top: 2rem; }

.card-pro {
    background-color: #1e293b;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    margin-bottom: 25px;
}

div[data-testid="stMetric"] {
    background-color: #1e293b;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MEMORIA
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
        "Costo Unitario (Res)": costo_u,
        "Ingreso ML (Res)": ingreso_n,
        "Viabilidad (Res)": viabilidad
    }
    st.session_state['historial'].append(fila)
    st.success(f"✅ '{nombre_producto}' guardado exitosamente.")

# ==========================================
# 2. TRM EN VIVO
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
# 3. OPENROUTER IA
# ==========================================
def consultar_openrouter(prompt):

    modelos = [
        "google/gemini-2.5-flash",
        "meta-llama/llama-3.3-70b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "google/gemma-3-27b:free"
    ]

    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except:
        return "⚠️ Error interno (Falta API Key)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://calculadorapro.com",
        "X-Title": "Calculadora Aduanas"
    }

    instruccion = """
    Eres experto en aduanas colombianas.
    Responde:
    1. Subpartida sugerida.
    2. % Gravamen.
    3. % IVA.
    Advierte que debe verificarse en el arancel oficial.
    """

    for modelo in modelos:
        try:
            data = {
                "model": modelo,
                "messages": [
                    {"role": "system", "content": instruccion},
                    {"role": "user", "content": prompt}
                ]
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except:
            continue

    return "❌ Servidores ocupados."

# ==========================================
# 4. SIDEBAR IA
# ==========================================
with st.sidebar:
    st.title("🤖 Asistente Aduanero")
    st.divider()

    for msg in st.session_state['mensajes_chat']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Consulta producto..."):
        st.session_state['mensajes_chat'].append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Consultando..."):
                respuesta = consultar_openrouter(prompt)
                st.markdown(respuesta)
                st.session_state['mensajes_chat'].append({"role": "assistant", "content": respuesta})

    if st.button("🗑️ Limpiar Chat", use_container_width=True):
        st.session_state['mensajes_chat'] = [{"role": "assistant", "content": "Chat reiniciado."}]
        st.rerun()

# ==========================================
# 5. FUNCIONES MATEMÁTICAS
# ==========================================
def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0,0,0,0
    precio_cop = precio_usd * trm
    flete_cop = flete_usd * trm
    base = (precio_cop * cantidad) + flete_cop
    valor_arancel = base * arancel_pct
    valor_iva = (base + valor_arancel) * iva_pct
    total = base + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = total / cantidad
    ingreso_ml = precio_ml * (1 - comision_ml_pct)
    return total, costo_unitario, ingreso_ml, ingreso_ml / costo_unitario if costo_unitario else 0

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0,0,0,0
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml = precio_ml * (1 - comision_ml_pct)
    return costo_pedido_cop, costo_unitario, ingreso_ml, ingreso_ml / costo_unitario if costo_unitario else 0

# (Barco permanece igual que tu lógica original)

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP`")

tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Avión", "🚢 Barco", "🛒 AliExpress", "📁 Carga Masiva", "📊 Comparador"
])

# ---- AVIÓN ----
with tab1:
    st.subheader("✈️ Importación Aérea")
    nombre = st.text_input("Nombre Producto", key="av_nombre")
    p_usd = st.number_input("Precio USD", value=1.0)
    trm = st.number_input("TRM", value=TRM_HOY)
    cant = st.number_input("Cantidad", value=100)
    flete = st.number_input("Flete USD", value=0.0)
    arancel = st.number_input("Arancel (0.15=15%)", value=0.15)
    iva = st.number_input("IVA (0.19=19%)", value=0.19)
    admin = st.number_input("Tarifa Admin", value=0.0)
    precio_ml = st.number_input("Precio ML", value=0.0)
    comision = st.number_input("Comisión ML", value=0.24)

    if st.button("Calcular Avión", type="primary"):
        total, cu, ingreso, v = calcular_alibaba_avion(p_usd,trm,cant,flete,arancel,iva,admin,precio_ml,comision)
        col1,col2,col3,col4=st.columns(4)
        col1.metric("Inversión Total", f"${total:,.0f}")
        col2.metric("Costo Unitario", f"${cu:,.0f}")
        col3.metric("Ingreso Neto", f"${ingreso:,.0f}")
        col4.metric("Ratio", f"{v:,.2f}x", delta="Óptimo" if v>=1.5 else "Revisar")

# ==========================================
# 📊 COMPARADOR MEJORADO
# ==========================================
with tab_comparador:
    st.subheader("📊 Portafolio")

    if len(st.session_state['historial']) > 0:
        df = pd.DataFrame(st.session_state['historial'])

        st.markdown("### 📌 Resumen Ejecutivo")
        colA,colB,colC=st.columns(3)
        colA.metric("Viabilidad Promedio", f"{df['Viabilidad (Res)'].mean():.2f}x")
        colB.metric("Producto Más Rentable", df.loc[df['Viabilidad (Res)'].idxmax()]['Producto'])
        colC.metric("Total Productos", len(df))

        st.markdown("---")

        fig1 = px.bar(df,x="Producto",y=["Costo Unitario (Res)","Ingreso ML (Res)"],barmode="group")
        fig1.update_layout(plot_bgcolor='#0f172a',paper_bgcolor='#0f172a',font_color='white')
        st.plotly_chart(fig1,use_container_width=True)

        fig2 = px.bar(df,x="Producto",y="Viabilidad (Res)",color="Viabilidad (Res)",color_continuous_scale="RdYlGn")
        fig2.update_layout(plot_bgcolor='#0f172a',paper_bgcolor='#0f172a',font_color='white')
        st.plotly_chart(fig2,use_container_width=True)

    else:
        st.info("Aún no hay productos calculados.")
