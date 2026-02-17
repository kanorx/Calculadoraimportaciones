import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# Librerías para diseño avanzado de Excel
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import CellIsRule

# ==========================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Calculadora Pro", layout="wide", page_icon="📦")

# ==========================================
# 1. MEMORIA DE LA APP (HISTORIAL Y CHAT)
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
# 3. CONFIGURACIÓN DE LA IA (OPENROUTER PRIVADO)
# ==========================================
def consultar_openrouter(prompt):
    """Prueba el modelo configurado en silencio. Si se satura (429), salta al siguiente."""
    
    # Aquí puedes cambiar el modelo principal si lo deseas en el futuro
    modelos_a_probar = [
        "google/gemini-2.5-flash-lite",               # Modelo principal (Económico y veloz)
        "meta-llama/llama-3.3-70b-instruct:free",     # Respaldo 1
        "nousresearch/hermes-3-llama-3.1-405b:free",  # Respaldo 2
        "google/gemma-3-27b:free"                     # Respaldo 3
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
    Eres un experto en aduanas y aranceles en Colombia. 
    Responde de forma clara y breve:
    1. Subpartida sugerida (10 dígitos).
    2. % de Gravamen Arancelario.
    3. % de IVA.
    No inventes datos. Luego de  dar los datos  brinda este link https://muisca.dian.gov.co/WebArancel/DefConsultaNomenclaturaPorCodigo.faces para que consulten el codigo.
    🚩 Advierte que el porcentaje puede variar y debe verificarse en el arancel oficial.
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
            respuesta = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
            
            if respuesta.status_code == 200:
                texto = respuesta.json()['choices'][0]['message']['content']
                return texto # Se devuelve el texto limpio, sin mencionar el motor
            elif respuesta.status_code == 429:
                continue # Salta en silencio al siguiente modelo si hay saturación
        except Exception:
            continue

    return "❌ Servidores ocupados en este momento. Intenta de nuevo en unos segundos."

# ==========================================
# 4. ASISTENTE FLOTANTE (SIDEBAR LIMPIA)
# ==========================================
with st.sidebar:
    st.title("🤖 Asistente Aduanero")
    st.divider()

    for msg in st.session_state['mensajes_chat']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Escribe el producto (ej. Reloj de cuarzo)..."):
        st.session_state['mensajes_chat'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Consultando normativas y aranceles..."):
                respuesta_ia = consultar_openrouter(prompt)
                st.markdown(respuesta_ia)
                st.session_state['mensajes_chat'].append({"role": "assistant", "content": respuesta_ia})
                    
    if st.button("🗑️ Limpiar Chat", use_container_width=True):
        st.session_state['mensajes_chat'] = [{"role": "assistant", "content": "Chat reiniciado. ¿En qué más te ayudo?"}]
        st.rerun()

# ==========================================
# 5. FUNCIONES MATEMÁTICAS (CON COSTO TOTAL)
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

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto, ancho, largo, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0, 0, 0
    precio_cop = precio_usd * trm
    total_cop_china = (precio_cop * cantidad) + (envio_origen_usd * trm)
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto * ancho * largo / 1000000) * cajas
    costo_cbm_nacionalizacion = volumen_m3 * cbm_agente
    costo_total = total_cop_china + valor_comision_tc + costo_cbm_nacionalizacion + flete_nacional
    costo_unitario = costo_total / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_total, costo_cbm_nacionalizacion, costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0), volumen_m3

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    return costo_pedido_cop, costo_unitario, ingreso_ml_neto, (ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0)

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizada automáticamente)*")

tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Avión", "🚢 Barco", "🛒 AliExpress", "📁 Carga Masiva", "📊 Comparador y Reporte"
])

base_inputs = lambda: { "Precio_USD": 0.0, "TRM": TRM_HOY, "Cantidad": 1, "Flete_USD": 0.0, "Arancel_pct": 0.0, "IVA_pct": 0.0, "Tarifa_Admin_COP": 0.0, "Comision_TC_pct": 0.0, "Alto_cm": 0.0, "Ancho_cm": 0.0, "Largo_cm": 0.0, "Cajas": 0, "Valor_CBM_COP": 0.0, "Flete_Nacional_COP": 0.0, "Costo_Pedido_COP": 0.0, "Precio_Venta_ML": 0.0, "Comision_ML_pct": 0.24 }

# --- PESTAÑA 1: AVION ---
with tab1:
    st.subheader("✈️ Simulación de Importación por Avión")
    nombre_av = st.text_input("Nombre del Producto", value="Esponja Mágica", key="nom_av")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_usd_av = st.number_input("Precio Unitario (USD)", value=0.65, key="p_usd_av")
        c_av = st.number_input("Cantidad a importar", value=200, key="cant_av")
        f_av = st.number_input("Costo Flete (USD)", value=385.0, key="flete_av")
    with col2:
        trm_av = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_av_input")
        ar_av = st.number_input("% Arancel (Ej. 0.15 para 15%)", value=0.15, format="%.2f", key="ara_av")
        iva_av = st.number_input("% IVA (Ej. 0.19 para 19%)", value=0.19, format="%.2f", key="iva_av")
    with col3:
        adm_av = st.number_input("Tarifa Agente/Admin (COP)", value=110000.0, key="tar_av")
        pml_av = st.number_input("Precio de Venta ML (COP)", value=50000.0, key="pml_av")
        cml_av = st.number_input("Comisión MercadoLibre (%)", value=0.24, key="cml_av")

    if st.button("Calcular Inversión (Avión)", type="primary"):
        c_tot, c_u, i_n, v = calcular_alibaba_avion(p_usd_av, trm_av, c_av, f_av, ar_av, iva_av, adm_av, pml_av, cml_av)
        
        st.divider()
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("💰 Inversión Total Pedido", f"${c_tot:,.0f}")
        res2.metric("📦 Costo Unitario", f"${c_u:,.2f}")
        res3.metric("💵 Ingreso Neto ML", f"${i_n:,.2f}")
        res4.metric("⚖️ Ratio Viabilidad", f"{v:,.2f}x")
        
        inputs = base_inputs()
        inputs.update({"Precio_USD": p_usd_av, "TRM": trm_av, "Cantidad": c_av, "Flete_USD": f_av, "Arancel_pct": ar_av, "IVA_pct": iva_av, "Tarifa_Admin_COP": adm_av, "Precio_Venta_ML": pml_av, "Comision_ML_pct": cml_av})
        guardar_simulacion(nombre_av, "Avión", inputs, c_u, i_n, v)

# --- PESTAÑA 2: BARCO ---
with tab2:
    st.subheader("🚢 Simulación de Importación Marítima (LCL)")
    nombre_ba = st.text_input("Nombre del Producto", value="Lámpara RGB", key="nom_ba")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_usd_ba = st.number_input("Precio Unitario (USD)", value=5.20, key="p_usd_ba")
        c_ba = st.number_input("Cantidad a importar", value=64, key="cant_ba")
        env_or_ba = st.number_input("Envío Puerto Origen (USD)", value=10.0, key="env_or_ba")
        trm_ba = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_ba_input")
    with col2:
        com_tc_ba = st.number_input("Comisión Tarjeta/Giro (%)", value=0.03, key="com_tc_ba")
        alt_ba = st.number_input("Alto caja (cm)", value=44.0, key="alt_ba")
        anch_ba = st.number_input("Ancho caja (cm)", value=44.0, key="anch_ba")
        larg_ba = st.number_input("Largo caja (cm)", value=47.0, key="larg_ba")
    with col3:
        caj_ba = st.number_input("Total Cajas", value=4, key="caj_ba")
        cbm_ba = st.number_input("Valor CBM Nacionalización (COP)", value=2400000.0, key="cbm_ba")
        fletn_ba = st.number_input("Flete Nacional (Bodega)", value=100000.0, key="fletn_ba")
        pml_ba = st.number_input("Precio de Venta ML (COP)", value=179900.0, key="pml_ba")
        cml_ba = st.number_input("Comisión MercadoLibre (%)", value=0.24, key="cml_ba2")

    if st.button("Calcular Inversión (Barco)", type="primary"):
        c_tot, c_cbm, c_u, i_n, v, vol = calcular_alibaba_barco(p_usd_ba, trm_ba, c_ba, env_or_ba, com_tc_ba, alt_ba, anch_ba, larg_ba, caj_ba, cbm_ba, fletn_ba, pml_ba, cml_ba)
        
        st.divider()
        st.info(f"📐 Volumen total calculado: **{vol:,.4f} m³**")
        
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("💰 Inversión Total Pedido", f"${c_tot:,.0f}")
        res2.metric("🏢 Costo Nacionalización", f"${c_cbm:,.0f}")
        res3.metric("📦 Costo Unitario Final", f"${c_u:,.2f}")
        res4.metric("⚖️ Ratio Viabilidad", f"{v:,.2f}x")
        
        inputs = base_inputs()
        inputs.update({"Precio_USD": p_usd_ba, "TRM": trm_ba, "Cantidad": c_ba, "Flete_USD": env_or_ba, "Comision_TC_pct": com_tc_ba, "Alto_cm": alt_ba, "Ancho_cm": anch_ba, "Largo_cm": larg_ba, "Cajas": caj_ba, "Valor_CBM_COP": cbm_ba, "Flete_Nacional_COP": fletn_ba, "Precio_Venta_ML": pml_ba, "Comision_ML_pct": cml_ba})
        guardar_simulacion(nombre_ba, "Barco", inputs, c_u, i_n, v)

# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    st.subheader("🛒 Simulación B2C Directo (AliExpress)")
    nombre_ali = st.text_input("Nombre del Producto", value="Audífonos Bluetooth", key="nom_ali")
    col1, col2 = st.columns(2)
    with col1:
        c_ped_ali = st.number_input("Costo Total del Pedido (COP)", value=326000.0, key="costo_ali")
        cant_ali = st.number_input("Cantidad de Productos", value=10, key="cant_ali")
    with col2:
        pml_ali = st.number_input("Precio de Venta ML (COP)", value=101000.0, key="pml_ali")
        cml_ali = st.number_input("Comisión MercadoLibre (%)", value=0.24, key="cml_ali")
        
    if st.button("Calcular Inversión (AliExpress)", type="primary"):
        c_tot, c_u, i_n, v = calcular_aliexpress(c_ped_ali, cant_ali, pml_ali, cml_ali)
        
        st.divider()
        res1, res2, res3 = st.columns(3)
        res1.metric("📦 Costo Unitario", f"${c_u:,.2f}")
        res2.metric("💵 Ingreso Neto ML", f"${i_n:,.2f}")
        res3.metric("⚖️ Ratio Viabilidad", f"{v:,.2f}x")
        
        inputs = base_inputs()
        inputs.update({"Costo_Pedido_COP": c_ped_ali, "Cantidad": cant_ali, "Precio_Venta_ML": pml_ali, "Comision_ML_pct": cml_ali})
        guardar_simulacion(nombre_ali, "AliExpress", inputs, c_u, i_n, v)

# --- PESTAÑA 4: CARGA MASIVA ---
with tab_masiva:
    st.subheader("📁 Procesar Reporte Masivo (Excel)")
    st.markdown("Sube tu plantilla con múltiples productos para calcularlos todos a la vez.")
    archivo_subido = st.file_uploader("Sube tu archivo .xlsx", type=["xlsx"])
    
    if archivo_subido is not None and st.button("Procesar Archivo Masivo", type="primary"):
        df_masivo = pd.read_excel(archivo_subido).fillna(0)
        exitos = 0
        
        for _, row in df_masivo.iterrows():
            metodo = str(row.get('Método', ''))
            nombre = str(row.get('Producto', 'Fila sin nombre'))
            try:
                if metodo == "Avión":
                    c_tot, c_u, i_n, v = calcular_alibaba_avion(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Arancel_pct'], row['IVA_pct'], row['Tarifa_Admin_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                elif metodo == "Barco":
                    c_tot, c_cbm, c_u, i_n, v, vol = calcular_alibaba_barco(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Comision_TC_pct'], row['Alto_cm'], row['Ancho_cm'], row['Largo_cm'], row['Cajas'], row['Valor_CBM_COP'], row['Flete_Nacional_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                elif metodo == "AliExpress":
                    c_tot, c_u, i_n, v = calcular_aliexpress(row['Costo_Pedido_COP'], row['Cantidad'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                else: 
                    continue
                
                inputs_row = {k: row[k] for k in base_inputs().keys() if k in row}
                guardar_simulacion(nombre, metodo, inputs_row, c_u, i_n, v)
                exitos += 1
            except Exception as e: 
                pass
                
        st.success(f"¡Procesamiento masivo finalizado! Se calcularon {exitos} productos.")

# --- PESTAÑA 5: COMPARADOR Y GRÁFICAS PRO ---
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
        
        # 1. Mostrar Tabla Resumen
        st.dataframe(df_export[["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]], use_container_width=True)
        
        # 2. Gráficas Interactiva de Plotly
        st.markdown("---")
        st.subheader("📈 Análisis Visual de Rentabilidad")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            fig1 = px.bar(
                df_export, 
                x='Producto', 
                y=['Costo Unitario (Res)', 'Ingreso ML (Res)'], 
                barmode='group',
                title='Costo vs. Ingreso por Producto',
                labels={'value': 'Pesos (COP)', 'variable': 'Métrica'},
                color_discrete_map={'Costo Unitario (Res)': '#EF553B', 'Ingreso ML (Res)': '#00CC96'}
            )
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_chart2:
            fig2 = px.bar(
                df_export, 
                x='Producto', 
                y='Viabilidad (Res)', 
                title='Ranking de Viabilidad (Semáforo Automático)',
                color='Viabilidad (Res)', 
                color_continuous_scale='RdYlGn',
                labels={'Viabilidad (Res)': 'Ratio (x)'}
            )
            fig2.add_hline(y=1.5, line_dash="dot", annotation_text="Meta (1.5x)", annotation_position="bottom right")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")

        # 3. Lógica de Exportación Excel (openpyxl)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Simulaciones')
            worksheet = writer.sheets['Simulaciones']
            
            # Colores de cabecera
            header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")

            # Autoajuste de columnas
            for col in worksheet.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value: max_length = max(max_length, len(str(cell.value)))
                worksheet.column_dimensions[col_letter].width = max_length + 4

            # Fórmulas de Excel en celdas
            for row in range(2, len(df_export) + 2):
                worksheet[f'T{row}'] = f'=IF(B{row}="Avión", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+G{row})*(1+H{row})+I{row})/IF(E{row}>0,E{row},1), IF(B{row}="Barco", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+J{row})+((K{row}*L{row}*M{row}/1000000)*N{row}*O{row})+P{row})/IF(E{row}>0,E{row},1), IF(B{row}="AliExpress", Q{row}/IF(E{row}>0,E{row},1), 0)))'
                worksheet[f'U{row}'] = f'=R{row}*(1-S{row})'
                worksheet[f'V{row}'] = f'=IF(T{row}>0, U{row}/T{row}, 0)'
                
                worksheet[f'T{row}'].number_format = '"$"#,##0'
                worksheet[f'U{row}'].number_format = '"$"#,##0'
                worksheet[f'V{row}'].number_format = '0.00'

            # Formato Condicional (Colores Viabilidad)
            green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

            rango_viabilidad = f"V2:V{len(df_export)+1}"
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='greaterThan', formula=['1.5'], fill=green_fill))
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='between', formula=['1.2', '1.5'], fill=yellow_fill))
            worksheet.conditional_formatting.add(rango_viabilidad, CellIsRule(operator='lessThan', formula=['1.2'], fill=red_fill))

        st.download_button("📥 Descargar Reporte Inteligente (Excel)", data=buffer.getvalue(), file_name="Reporte_Importacion_Pro.xlsx", type="primary", use_container_width=True)
        if st.button("🗑️ Limpiar Todo el Historial"): 
            st.session_state['historial'] = []
            st.rerun()
    else:
        st.info("Calcula o sube un producto para activar las gráficas y la exportación a Excel.")
