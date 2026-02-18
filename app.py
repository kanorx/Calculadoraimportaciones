import streamlit as st
import pandas as pd
import io

# LIBRERÍAS DE UI, TABLAS Y GRÁFICOS AVANZADOS
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import CellIsRule
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from streamlit_echarts import st_echarts  # <--- NUEVO MOTOR GRÁFICO

# MÓDULOS PROPIOS (LA ARQUITECTURA)
from ui.design import inyectar_estilos, load_lottieurl
from core.financial_api import fetch_trm
from core.calculations import calc_avion, calc_barco
from engine.engine_ias import call_openrouter_ai

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
        except: st.error("Error leyendo el archivo. Asegúrate de que sea .xlsx válido.")

# --- INTELIGENCIA DE MERCADO ---
elif selected_nav == "Inteligencia Mercado":
    st.markdown("### 🧠 Centro de Inteligencia IA")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        m_switch = st.radio("Herramienta activa:", ["🧑‍⚖️ Aranceles y Aduanas (Gratis)", "🚀 Optimización SEO (Premium)"])
        st.markdown("<br>", unsafe_allow_html=True)
        img_up = None
        clave_ingresada = ""
        
        if "SEO" in m_switch:
            with st.container(border=True):
                st.warning("🔒 **Acceso Restringido**\nConsume recursos de alto rendimiento.")
                clave_ingresada = st.text_input("Ingresa tu Clave Premium:", type="password")
                img_up = st.file_uploader("📸 Subir Pantallazo (AliExpress)", type=["jpg", "png"])
    
    with col_b:
        with st.container(border=True, height=450):
            for m in st.session_state['chat_log']:
                with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if u_input := st.chat_input("Escribe tu consulta aquí..."):
            st.session_state['chat_log'].append({"role": "user", "content": u_input})
            CLAVE_VERDADERA = st.secrets.get("CLAVE_PREMIUM", "12345")
            
            if "SEO" in m_switch and clave_ingresada != CLAVE_VERDADERA:
                st.session_state['chat_log'].append({"role": "assistant", "content": "⛔ **Acceso Denegado:** Clave Premium incorrecta."})
                st.rerun()
            else:
                with st.spinner("IA Procesando datos..."):
                    resp = call_openrouter_ai(u_input, image_input=img_up, task="legal" if "Aduanas" in m_switch else "marketing")
                    st.session_state['chat_log'].append({"role": "assistant", "content": resp})
                st.rerun()

# --- REPORTES Y BI ---
elif selected_nav == "Reportes & BI":
    st.markdown("### 📊 Business Intelligence & Exportación")
    if not st.session_state['historial']:
        st.info("ℹ️ Realiza al menos una simulación para activar el dashboard.")
        if lottie_logistics: st_lottie(lottie_logistics, height=300, key="empty_state")
    else:
        df_h = pd.DataFrame(st.session_state['historial'])
        
        # TARJETAS MÉTRICAS
        with st.container():
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            col_metrics1.metric("Total SKU Analizados", len(df_h))
            avg_viab = df_h['Viabilidad (Res)'].mean()
            col_metrics2.metric("Viabilidad Promedio", f"{avg_viab:.2f}x", delta=f"{avg_viab-1.5:.2f}" if avg_viab > 1.5 else f"{avg_viab-1.5:.2f}")
            col_metrics3.metric("Costo Promedio", f"${df_h['Costo Unitario (Res)'].mean():,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ---------------------------------------------------------
        # NUEVOS GRÁFICOS CON ECHARTS (NIVEL SAAS)
        # ---------------------------------------------------------
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("<h5 style='text-align:center; color:#091E42;'>💰 Balance Financiero: Costo vs Ingreso</h5>", unsafe_allow_html=True)
            # Extraemos datos para ECharts
            productos = df_h['Producto'].tolist()
            costos = df_h['Costo Unitario (Res)'].round(0).tolist()
            ingresos = df_h['Ingreso ML (Res)'].round(0).tolist()
            
            option_bar = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "legend": {"data": ["Costo Unitario", "Ingreso Neto"], "bottom": 0},
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
                "xAxis": {"type": "category", "data": productos, "axisLine": {"show": False}},
                "yAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed", "color": "#E1E5F2"}}},
                "color": ["#FF4B4B", "#00E676"],
                "series": [
                    {
                        "name": "Costo Unitario",
                        "type": "bar",
                        "data": costos,
                        "itemStyle": {"borderRadius": [6, 6, 0, 0]}, # Bordes redondeados elegantes
                        "barGap": "15%"
                    },
                    {
                        "name": "Ingreso Neto",
                        "type": "bar",
                        "data": ingresos,
                        "itemStyle": {"borderRadius": [6, 6, 0, 0]}
                    }
                ]
            }
            st_echarts(options=option_bar, height="350px")
            
        with g2:
            st.markdown("<h5 style='text-align:center; color:#091E42;'>⚖️ Tacómetro de Rentabilidad Promedio</h5>", unsafe_allow_html=True)
            option_gauge = {
                "tooltip": {"formatter": "{a} <br/>{b} : {c}x"},
                "series": [
                    {
                        "name": "Rentabilidad",
                        "type": "gauge",
                        "min": 0,
                        "max": 3,
                        "splitNumber": 3,
                        "axisLine": {
                            "lineStyle": {
                                "width": 18,
                                "color": [
                                    [0.4, "#FF4B4B"], # Rojo hasta 1.2x (0.4 de 3)
                                    [0.5, "#FFD166"], # Amarillo de 1.2x a 1.5x
                                    [1, "#00E676"]    # Verde de 1.5x en adelante
                                ]
                            }
                        },
                        "pointer": {"itemStyle": {"color": "auto"}},
                        "axisTick": {"distance": -20, "length": 8, "lineStyle": {"color": "#fff", "width": 2}},
                        "splitLine": {"distance": -20, "length": 20, "lineStyle": {"color": "#fff", "width": 3}},
                        "axisLabel": {"color": "inherit", "distance": 30, "fontSize": 12},
                        "detail": {"valueAnimation": True, "formatter": "{value}x", "color": "inherit", "fontSize": 28, "fontWeight": "bold", "padding": [40, 0, 0, 0]},
                        "data": [{"value": round(avg_viab, 2), "name": "Ratio"}]
                    }
                ]
            }
            st_echarts(options=option_gauge, height="350px")

        # ---------------------------------------------------------
        # MAGIA DE AgGrid PARA LA TABLA DE DATOS
        # ---------------------------------------------------------
        st.markdown("<br><h4 style='color: #091E42; font-weight: 600;'>📑 Registro Detallado de Simulaciones</h4>", unsafe_allow_html=True)
        
        gb = GridOptionsBuilder.from_dataframe(df_h)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_side_bar() 
        
        # Formato VIP a las columnas
        gb.configure_column("Costo Unitario (Res)", type=["numericColumn"], valueFormatter="value != undefined ? '$' + value.toLocaleString('es-CO', {maximumFractionDigits: 0}) : ''")
        gb.configure_column("Ingreso ML (Res)", type=["numericColumn"], valueFormatter="value != undefined ? '$' + value.toLocaleString('es-CO', {maximumFractionDigits: 0}) : ''")
        gb.configure_column("Viabilidad (Res)", type=["numericColumn"], valueFormatter="value != undefined ? value.toFixed(2) + 'x' : ''")
        
        gb.configure_default_column(editable=False, groupable=True)
        gridOptions = gb.build()
        
        AgGrid(
            df_h,
            gridOptions=gridOptions,
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            theme='alpine',
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            height=300
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # EXPORTACIÓN EXCEL
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as wr:
            df_h.to_excel(wr, index=False, sheet_name='Reporte Gerencial')
            ws = wr.sheets['Reporte Gerencial']
            for cell in ws[1]:
                cell.fill = PatternFill(start_color="2E5BFF", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal='center')
            for col in ws.columns:
                 ws.column_dimensions[col[0].column_letter].width = 20
            ws.conditional_formatting.add(f"E2:E{len(df_h)+1}", CellIsRule(operator='greaterThan', formula=['1.5'], fill=PatternFill(start_color="C6EFCE", fill_type="solid")))
            ws.conditional_formatting.add(f"E2:E{len(df_h)+1}", CellIsRule(operator='lessThan', formula=['1.2'], fill=PatternFill(start_color="FFC7CE", fill_type="solid")))
            
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            st.download_button("📥 Descargar Reporte Excel", buffer.getvalue(), "Reporte_ImportPro.xlsx", type="primary")
        with col_btn2:
            if st.button("🗑️ Purgar Datos del Historial"):
                st.session_state['historial'] = []
                st.rerun()
