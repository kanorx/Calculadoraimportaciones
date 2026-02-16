import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import io
import json

# Librerías para diseño avanzado de Excel
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import CellIsRule

# ==========================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Calculadora Pro - OpenRouter", layout="wide", page_icon="📦")

# ==========================================
# 1. MEMORIA DE LA APP (HISTORIAL Y CHAT)
# ==========================================
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

if 'mensajes_chat' not in st.session_state:
    st.session_state['mensajes_chat'] = [
        {"role": "assistant", "content": "¡Hola! Estoy conectado a OpenRouter sin límites. Dime qué producto quieres consultar."}
    ]

def guardar_simulacion(nombre_producto, metodo, inputs, costo_u, ingreso_n, viabilidad):
    fila = {
        "Producto": nombre_producto, "Método": metodo, **inputs,
        "Costo Unitario (Res)": costo_u, "Ingreso ML (Res)": ingreso_n, "Viabilidad (Res)": viabilidad
    }
    st.session_state['historial'].append(fila)
    st.success(f"✅ '{nombre_producto}' guardado en el portafolio.")

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
# 3. CONFIGURACIÓN DE OPENROUTER (LA NUEVA IA)
# ==========================================
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
    IA_CONFIGURADA = True
except (KeyError, FileNotFoundError):
    IA_CONFIGURADA = False

def consultar_openrouter(prompt, modelo_id):
    """Función maestra para hablar con cualquier modelo en OpenRouter"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://calculadorapro.com", # Requisito de OpenRouter
        "X-Title": "Calculadora Aduanas" # Requisito de OpenRouter
    }
    
    instruccion_sistema = """
    Eres un experto en aduanas y aranceles en Colombia. 
    Responde de forma clara y breve:
    1. Subpartida sugerida (10 dígitos).
    2. % de Gravamen Arancelario.
    3. % de IVA.
    No inventes datos. Si no estás seguro, pide más detalles técnicos.
    🚩 Advierte que el porcentaje puede variar y debe verificarse en el arancel oficial.
    """
    
    data = {
        "model": modelo_id,
        "messages": [
            {"role": "system", "content": instruccion_sistema},
            {"role": "user", "content": f"El usuario pregunta: '{prompt}'"}
        ]
    }
    
    respuesta = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    
    if respuesta.status_code == 200:
        return respuesta.json()['choices'][0]['message']['content']
    else:
        return f"Error en la API: {respuesta.status_code} - {respuesta.text}"

# ==========================================
# 4. ASISTENTE FLOTANTE (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("🤖 IA Aduanera (OpenRouter)")
    
    if not IA_CONFIGURADA:
        st.error("⚠️ Falta configurar la OPENROUTER_API_KEY en los secretos.")
    else:
        # Selector de Modelo (Gratis vs Pago)
        opcion_modelo = st.radio(
            "Selecciona el Motor de IA:",
            ["Llama 3.3 70B (Gratis)", "Gemini Flash Lite (Pago, 0.10/M)"]
        )
        
        # Asignar el ID real según la opción
        if opcion_modelo == "Llama 3.3 70B (Gratis)":
            modelo_elegido = "meta-llama/llama-3.3-70b-instruct:free"
        else:
            modelo_elegido = "google/gemini-2.5-flash-lite"
            
        st.markdown("---")
        
        # Mostrar Chat
        for msg in st.session_state['mensajes_chat']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input del usuario
        if prompt := st.chat_input("Escribe tu producto aquí..."):
            st.session_state['mensajes_chat'].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(f"Consultando con {opcion_modelo}..."):
                    
                    respuesta_ia = consultar_openrouter(prompt, modelo_elegido)
                    
                    st.caption(f"*(Motor: {opcion_modelo})*")
                    st.markdown(respuesta_ia)
                    st.session_state['mensajes_chat'].append({"role": "assistant", "content": respuesta_ia})
                        
    if st.button("🗑️ Limpiar Chat", use_container_width=True):
        st.session_state['mensajes_chat'] = [{"role": "assistant", "content": "Chat reiniciado. ¿En qué más te ayudo?"}]
        st.rerun()

# ==========================================
# 5. FUNCIONES MATEMÁTICAS (SE MANTIENEN IGUAL)
# ==========================================
def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0
    precio_cop = precio_usd * trm
    flete_cop = flete_usd * trm
    base_impuestos = (precio_cop * cantidad) + flete_cop
    valor_arancel = base_impuestos * arancel_pct
    valor_iva = (base_impuestos + valor_arancel) * iva_pct
    costo_pedido = base_impuestos + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = costo_pedido / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0)

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto, ancho, largo, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0
    precio_cop = precio_usd * trm
    total_cop_china = (precio_cop * cantidad) + (envio_origen_usd * trm)
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto * ancho * largo / 1000000) * cajas
    costo_nacionalizacion = volumen_m3 * cbm_agente
    costo_unitario = (total_cop_china + valor_comision_tc + costo_nacionalizacion + flete_nacional) / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0), volumen_m3

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0)

# ==========================================
# 6. INTERFAZ PRINCIPAL (SE MANTIENE IGUAL)
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizado automáticamente)*")

tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Avión", "🚢 Barco", "🛒 AliExpress", "📁 Carga Masiva", "📊 Comparador"
])

base_inputs = lambda: { "Precio_USD": 0.0, "TRM": TRM_HOY, "Cantidad": 1, "Flete_USD": 0.0, "Arancel_pct": 0.0, "IVA_pct": 0.0, "Tarifa_Admin_COP": 0.0, "Comision_TC_pct": 0.0, "Alto_cm": 0.0, "Ancho_cm": 0.0, "Largo_cm": 0.0, "Cajas": 0, "Valor_CBM_COP": 0.0, "Flete_Nacional_COP": 0.0, "Costo_Pedido_COP": 0.0, "Precio_Venta_ML": 0.0, "Comision_ML_pct": 0.24 }

# --- PESTAÑA 1: AVION ---
with tab1:
    st.subheader("✈️ Simulación de Importación por Avión")
    nombre_prod_av = st.text_input("Nombre del Producto", value="Esponja", key="nom_av")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_av = st.number_input("Precio (USD)", value=0.65, key="p_usd_av")
        cantidad_av = st.number_input("Cantidad", value=200, key="cant_av")
        flete_usd_av = st.number_input("Costo Flete (USD)", value=385.0, key="flete_av")
    with col2:
        trm_av = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_av_input")
        arancel_pct_av = st.number_input("% Arancel", value=0.15, format="%.2f", key="ara_av")
        iva_pct_av = st.number_input("% IVA", value=0.19, format="%.2f", key="iva_av")
    with col3:
        tarifa_admin_av = st.number_input("Tarifa Admin", value=110000.0, key="tar_av")
        precio_ml_av = st.number_input("Venta ML (COP)", value=50000.0, key="pml_av")
        comision_ml_av = st.number_input("Comisión ML (%)", value=0.24, key="cml_av")

    if st.button("Calcular (Avión)", type="primary"):
        costo_u, ing_n, viab = calcular_alibaba_avion(precio_usd_av, trm_av, cantidad_av, flete_usd_av, arancel_pct_av, iva_pct_av, tarifa_admin_av, precio_ml_av, comision_ml_av)
        inputs = base_inputs()
        inputs.update({"Precio_USD": precio_usd_av, "TRM": trm_av, "Cantidad": cantidad_av, "Flete_USD": flete_usd_av, "Arancel_pct": arancel_pct_av, "IVA_pct": iva_pct_av, "Tarifa_Admin_COP": tarifa_admin_av, "Precio_Venta_ML": precio_ml_av, "Comision_ML_pct": comision_ml_av})
        guardar_simulacion(nombre_prod_av, "Avión", inputs, costo_u, ing_n, viab)
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ing_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 2: BARCO ---
with tab2:
    st.subheader("🚢 Simulación de Importación por Barco")
    nombre_prod_ba = st.text_input("Nombre del Producto", value="Lámpara RGB", key="nom_ba")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_ba = st.number_input("Precio (USD)", value=5.20, key="p_usd_ba")
        cantidad_ba = st.number_input("Cantidad", value=64, key="cant_ba")
        envio_origen_ba = st.number_input("Envío Origen (USD)", value=10.0, key="env_or_ba")
        trm_ba = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_ba_input")
    with col2:
        comision_tc_ba = st.number_input("Comisión T.C (%)", value=0.03, key="com_tc_ba")
        alto_ba = st.number_input("Alto caja (cm)", value=44.0, key="alt_ba")
        ancho_ba = st.number_input("Ancho caja (cm)", value=44.0, key="anch_ba")
        largo_ba = st.number_input("Largo caja (cm)", value=47.0, key="larg_ba")
    with col3:
        cajas_ba = st.number_input("Cantidad cajas", value=4, key="caj_ba")
        cbm_agente_ba = st.number_input("CBM (COP)", value=2400000.0, key="cbm_ba")
        flete_nacional_ba = st.number_input("Flete Nacional", value=100000.0, key="fletn_ba")
        precio_ml_ba = st.number_input("Venta ML (COP)", value=179900.0, key="pml_ba")
        comision_ml_ba = st.number_input("Comisión ML (%)", value=0.24, key="cml_ba2")

    if st.button("Calcular (Barco)", type="primary"):
        costo_u, ing_n, viab, vol = calcular_alibaba_barco(precio_usd_ba, trm_ba, cantidad_ba, envio_origen_ba, comision_tc_ba, alto_ba, ancho_ba, largo_ba, cajas_ba, cbm_agente_ba, flete_nacional_ba, precio_ml_ba, comision_ml_ba)
        inputs = base_inputs()
        inputs.update({"Precio_USD": precio_usd_ba, "TRM": trm_ba, "Cantidad": cantidad_ba, "Flete_USD": envio_origen_ba, "Comision_TC_pct": comision_tc_ba, "Alto_cm": alto_ba, "Ancho_cm": ancho_ba, "Largo_cm": largo_ba, "Cajas": cajas_ba, "Valor_CBM_COP": cbm_agente_ba, "Flete_Nacional_COP": flete_nacional_ba, "Precio_Venta_ML": precio_ml_ba, "Comision_ML_pct": comision_ml_ba})
        guardar_simulacion(nombre_prod_ba, "Barco", inputs, costo_u, ing_n, viab)
        st.info(f"📐 Volumen calculado: **{vol:,.4f} m³**")
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ing_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    st.subheader("🛒 Simulación B2C AliExpress")
    nombre_prod_ali = st.text_input("Nombre del Producto", value="Audífonos", key="nom_ali")
    col1, col2 = st.columns(2)
    with col1:
        costo_ped_ali = st.number_input("Costo Pedido (COP)", value=326000.0, key="costo_ali")
        cant_ali = st.number_input("Cantidad", value=10, key="cant_ali")
    with col2:
        precio_ml_ali = st.number_input("Venta ML (COP)", value=101000.0, key="pml_ali")
        comision_ml_ali = st.number_input("Comisión ML (%)", value=0.24, key="cml_ali")
        
    if st.button("Calcular (AliExpress)", type="primary"):
        costo_u, ing_n, viab = calcular_aliexpress(costo_ped_ali, cant_ali, precio_ml_ali, comision_ml_ali)
        inputs = base_inputs()
        inputs.update({"Costo_Pedido_COP": costo_ped_ali, "Cantidad": cant_ali, "Precio_Venta_ML": precio_ml_ali, "Comision_ML_pct": comision_ml_ali})
        guardar_simulacion(nombre_prod_ali, "AliExpress", inputs, costo_u, ing_n, viab)
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ing_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 4: CARGA MASIVA ---
with tab_masiva:
    st.subheader("📁 Procesar Reporte Excel")
    archivo_subido = st.file_uploader("Sube tu plantilla modificada", type=["xlsx"])
    if archivo_subido is not None and st.button("Procesar Archivo Masivo", type="primary"):
        df = pd.read_excel(archivo_subido).fillna(0)
        for _, row in df.iterrows():
            metodo = str(row.get('Método', ''))
            nombre = str(row.get('Producto', 'Fila'))
            try:
                if metodo == "Avión":
                    c_u, i_n, v = calcular_alibaba_avion(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Arancel_pct'], row['IVA_pct'], row['Tarifa_Admin_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                elif metodo == "Barco":
                    c_u, i_n, v, _ = calcular_alibaba_barco(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Comision_TC_pct'], row['Alto_cm'], row['Ancho_cm'], row['Largo_cm'], row['Cajas'], row['Valor_CBM_COP'], row['Flete_Nacional_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                elif metodo == "AliExpress":
                    c_u, i_n, v = calcular_aliexpress(row['Costo_Pedido_COP'], row['Cantidad'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                else: continue
                inputs_row = {k: row[k] for k in base_inputs().keys() if k in row}
                guardar_simulacion(nombre, metodo, inputs_row, c_u, i_n, v)
            except: pass
        st.success("¡Importación masiva completada!")

# --- PESTAÑA 5: COMPARADOR Y EXCEL PRO ---
with tab_comparador:
    st.subheader("📊 Portafolio y Exportación Avanzada")
    if len(st.session_state['historial']) > 0:
        columnas_ordenadas = [
            "Producto", "Método", "Precio_USD", "TRM", "Cantidad", "Flete_USD", 
            "Arancel_pct", "IVA_pct", "Tarifa_Admin_COP", "Comision_TC_pct", 
            "Alto_cm", "Ancho_cm", "Largo_cm", "Cajas", "Valor_CBM_COP", 
            "Flete_Nacional_COP", "Costo_Pedido_COP", "Precio_Venta_ML", 
            "Comision_ML_pct", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"
        ]
        
        df_historial = pd.DataFrame(st.session_state['historial'])
        for col in columnas_ordenadas:
            if col not in df_historial.columns: df_historial[col] = 0.0
        
        df_export = df_historial[columnas_ordenadas]
        st.dataframe(df_export[["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]], use_container_width=True)
        
        # --- LÓGICA DE EXCEL CON SEMÁFORO Y COLORES ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Simulaciones')
            worksheet = writer.sheets['Simulaciones']
            
            # 1. Colores de cabecera
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")

            # 2. Ajuste de columnas y fórmulas
            for col in worksheet.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value: max_length = max(max_length, len(str(cell.value)))
                worksheet.column_dimensions[col_letter].width = max_length + 4

            for row in range(2, len(df_export) + 2):
                # Fórmulas inteligentes
                worksheet[f'T{row}'] = f'=IF(B{row}="Avión", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+G{row})*(1+H{row})+I{row})/IF(E{row}>0,E{row},1), IF(B{row}="Barco", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+J{row})+((K{row}*L{row}*M{row}/1000000)*N{row}*O{row})+P{row})/IF(E{row}>0,E{row},1), IF(B{row}="AliExpress", Q{row}/IF(E{row}>0,E{row},1), 0)))'
                worksheet[f'U{row}'] = f'=R{row}*(1-S{row})'
                worksheet[f'V{row}'] = f'=IF(T{row}>0, U{row}/T{row}, 0)'
                
                # Formatos de número
                worksheet[f'T{row}'].number_format = '"$"#,##0'
                worksheet[f'U{row}'].number_format = '"$"#,##0'
                worksheet[f'V{row}'].number_format = '0.00'

            # 3. Formato Condicional (Semáforo de Viabilidad en Columna V)
            green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            rango_viabilidad = f"V2:V{len(df_export)+1}"
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='greaterThan', formula=['1.5'], fill=green_fill))
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='between', formula=['1.2', '1.5'], fill=yellow_fill))
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='lessThan', formula=['1.2'], fill=red_fill))

        st.download_button("📥 Descargar Excel Inteligente (con Colores)", data=buffer.getvalue(), file_name="Reporte_Importacion_Pro.xlsx", type="primary", use_container_width=True)
        if st.button("🗑️ Limpiar Historial"): 
            st.session_state['historial'] = []
            st.rerun()
    else:
        st.info("Aún no tienes simulaciones guardadas.")
