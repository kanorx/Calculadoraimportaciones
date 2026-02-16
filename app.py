import streamlit as st
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
        {"role": "assistant", "content": "¡Hola! He activado el sistema de redundancia. Si Llama 3.3 falla, saltaré a otro modelo automáticamente. ¿Qué producto consultamos?"}
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
# 3. INTELIGENCIA ARTIFICIAL (OPENROUTER MULTI-MODELO)
# ==========================================
def consultar_openrouter(prompt, modelo_principal):
    """Función inteligente que salta entre modelos gratuitos si hay saturación"""
    
    # Lista de modelos gratuitos recomendados
    modelos_a_probar = [
        modelo_principal, 
        "nousresearch/hermes-3-llama-3.1-405b:free", 
        "google/gemma-3-27b:free",
        "meta-llama/llama-3.2-3b-instruct:free"
    ]
    
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except:
        return "⚠️ Error: Falta configurar OPENROUTER_API_KEY en los secretos."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://calculadorapro.com",
        "X-Title": "Calculadora Aduanas Pro"
    }
    
    instruccion_sistema = """
    Eres un experto en aduanas de Colombia. 
    Responde con: 1. Subpartida sugerida (10 dígitos), 2. % Arancel, 3. % IVA. 
    Sé breve. Advierte que la información debe verificarse oficialmente.
    """

    for modelo in modelos_a_probar:
        try:
            data = {
                "model": modelo,
                "messages": [
                    {"role": "system", "content": instruccion_sistema},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                texto = response.json()['choices'][0]['message']['content']
                return f"*(Respuesta generada por {modelo})*\n\n{texto}"
            
            if response.status_code == 429: # Saturación
                st.warning(f"⚠️ {modelo} está saturado, probando motor de respaldo...")
                continue 
                
        except:
            continue

    return "❌ Todos los servidores gratuitos están ocupados. Por favor, intenta de nuevo en un minuto."

# ==========================================
# 4. ASISTENTE FLOTANTE (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("🤖 Asistente Aduanero Pro")
    
    opcion_ia = st.radio(
        "Motor de búsqueda principal:",
        ["Llama 3.3 70B (Gratis)", "Gemini Flash Lite (Pago)"]
    )
    
    id_inicio = "meta-llama/llama-3.3-70b-instruct:free" if "Llama" in opcion_ia else "google/gemini-2.5-flash-lite"
    
    st.divider()
    
    for msg in st.session_state['mensajes_chat']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("¿Qué arancel tiene...?"):
        st.session_state['mensajes_chat'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Consultando bases de datos..."):
                respuesta = consultar_openrouter(prompt, id_inicio)
                st.markdown(respuesta)
                st.session_state['mensajes_chat'].append({"role": "assistant", "content": respuesta})
                        
    if st.button("🗑️ Limpiar Chat", use_container_width=True):
        st.session_state['mensajes_chat'] = [{"role": "assistant", "content": "Chat reiniciado. ¿En qué más te ayudo?"}]
        st.rerun()

# ==========================================
# 5. FUNCIONES MATEMÁTICAS
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
# 6. INTERFAZ PRINCIPAL
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizado automáticamente)*")

tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Avión", "🚢 Barco", "🛒 AliExpress", "📁 Carga Masiva", "📊 Comparador"
])

base_inputs = lambda: { "Precio_USD": 0.0, "TRM": TRM_HOY, "Cantidad": 1, "Flete_USD": 0.0, "Arancel_pct": 0.0, "IVA_pct": 0.0, "Tarifa_Admin_COP": 0.0, "Comision_TC_pct": 0.0, "Alto_cm": 0.0, "Ancho_cm": 0.0, "Largo_cm": 0.0, "Cajas": 0, "Valor_CBM_COP": 0.0, "Flete_Nacional_COP": 0.0, "Costo_Pedido_COP": 0.0, "Precio_Venta_ML": 0.0, "Comision_ML_pct": 0.24 }

# --- PESTAÑA 1: AVION ---
with tab1:
    st.subheader("✈️ Simulación Aérea (Alibaba/Courier)")
    nombre_prod_av = st.text_input("Producto", value="Gadget", key="nom_av")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_av = st.number_input("Precio (USD)", value=1.0, key="p_usd_av")
        cantidad_av = st.number_input("Cantidad", value=100, key="cant_av")
        flete_usd_av = st.number_input("Flete (USD)", value=50.0, key="flete_av")
    with col2:
        ar_pct_av = st.number_input("% Arancel", value=0.10, key="ara_av")
        iva_pct_av = st.number_input("% IVA", value=0.19, key="iva_av")
        adm_av = st.number_input("Tarifa Admin", value=110000.0, key="tar_av")
    with col3:
        pml_av = st.number_input("Venta ML (COP)", value=100000.0, key="pml_av")
        cml_av = st.number_input("Comisión ML %", value=0.24, key="cml_av")

    if st.button("Calcular (Avión)", type="primary"):
        c_u, i_n, v = calcular_alibaba_avion(precio_usd_av, TRM_HOY, cantidad_av, flete_usd_av, ar_pct_av, iva_pct_av, adm_av, pml_av, cml_av)
        guardar_simulacion(nombre_prod_av, "Avión", {"Precio_USD": precio_usd_av, "TRM": TRM_HOY, "Cantidad": cantidad_av, "Flete_USD": flete_usd_av, "Arancel_pct": ar_pct_av, "IVA_pct": iva_pct_av, "Tarifa_Admin_COP": adm_av, "Precio_Venta_ML": pml_av, "Comision_ML_pct": cml_av}, c_u, i_n, v)
        st.metric("Costo Unitario", f"${c_u:,.0f}")
        st.metric("Ratio Viabilidad", f"{v:.2f}x")

# --- PESTAÑA 2: BARCO ---
with tab2:
    st.subheader("🚢 Simulación Marítima (LCL)")
    nombre_prod_ba = st.text_input("Producto", value="Decoración", key="nom_ba")
    col1, col2, col3 = st.columns(3)
    with col1:
        p_usd_ba = st.number_input("Precio (USD)", value=5.0, key="p_ba")
        cant_ba = st.number_input("Cantidad", value=50, key="c_ba")
        env_ba = st.number_input("Envío China (USD)", value=20.0, key="env_ba")
    with col2:
        alt_ba = st.number_input("Alto (cm)", value=40.0)
        anc_ba = st.number_input("Ancho (cm)", value=40.0)
        lar_ba = st.number_input("Largo (cm)", value=40.0)
    with col3:
        caj_ba = st.number_input("Cajas", value=2)
        cbm_ba = st.number_input("Valor CBM COP", value=2400000.0)
        pml_ba = st.number_input("Venta ML (COP)", value=200000.0, key="pml_ba")

    if st.button("Calcular (Barco)", type="primary"):
        c_u, i_n, v, vol = calcular_alibaba_barco(p_usd_ba, TRM_HOY, cant_ba, env_ba, 0.03, alt_ba, anc_ba, lar_ba, caj_ba, cbm_ba, 100000.0, pml_ba, 0.24)
        guardar_simulacion(nombre_prod_ba, "Barco", {"Precio_USD": p_usd_ba, "TRM": TRM_HOY, "Cantidad": cant_ba, "Alto_cm": alt_ba, "Ancho_cm": anc_ba, "Largo_cm": lar_ba, "Cajas": caj_ba, "Valor_CBM_COP": cbm_ba, "Precio_Venta_ML": pml_ba, "Comision_ML_pct": 0.24}, c_u, i_n, v)
        st.info(f"📐 Volumen: {vol:.4f} m³")
        st.metric("Costo Unitario", f"${c_u:,.0f}")

# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    st.subheader("🛒 Simulación Directa AliExpress")
    n_ali = st.text_input("Producto", value="Accesorios")
    c_ali = st.number_input("Costo Pedido (COP)", value=500000.0)
    q_ali = st.number_input("Cantidad", value=10)
    v_ali = st.number_input("Venta ML (COP)", value=80000.0)
    
    if st.button("Calcular (AliExpress)", type="primary"):
        c_u, i_n, v = calcular_aliexpress(c_ali, q_ali, v_ali, 0.24)
        guardar_simulacion(n_ali, "AliExpress", {"Costo_Pedido_COP": c_ali, "Cantidad": q_ali, "Precio_Venta_ML": v_ali, "Comision_ML_pct": 0.24}, c_u, i_n, v)
        st.metric("Costo Unitario", f"${c_u:,.0f}")

# --- PESTAÑA 4: CARGA MASIVA ---
with tab_masiva:
    st.subheader("📁 Procesar Archivo Excel")
    archivo_subido = st.file_uploader("Sube tu plantilla", type=["xlsx"])
    if archivo_subido is not None and st.button("Procesar Todo"):
        df_masivo = pd.read_excel(archivo_subido).fillna(0)
        for _, row in df_masivo.iterrows():
            m = str(row.get('Método', ''))
            n = str(row.get('Producto', 'Fila'))
            try:
                if m == "Avión":
                    res = calcular_alibaba_avion(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Arancel_pct'], row['IVA_pct'], row['Tarifa_Admin_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                elif m == "Barco":
                    res = calcular_alibaba_barco(row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], row['Comision_TC_pct'], row['Alto_cm'], row['Ancho_cm'], row['Largo_cm'], row['Cajas'], row['Valor_CBM_COP'], row['Flete_Nacional_COP'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                    res = res[:3] # Quitamos volumen
                elif m == "AliExpress":
                    res = calcular_aliexpress(row['Costo_Pedido_COP'], row['Cantidad'], row['Precio_Venta_ML'], row['Comision_ML_pct'])
                else: continue
                inputs_row = {k: row[k] for k in base_inputs().keys() if k in row}
                guardar_simulacion(n, m, inputs_row, res[0], res[1], res[2])
            except: pass
        st.success("Carga masiva finalizada.")

# --- PESTAÑA 5: COMPARADOR Y REPORTE ---
with tab_comparador:
    st.subheader("📊 Portafolio Consolidado")
    if st.session_state['historial']:
        df_final = pd.DataFrame(st.session_state['historial'])
        st.dataframe(df_final[["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]], use_container_width=True)
        
        # --- EXPORTACIÓN CON SEMÁFORO Y FÓRMULAS ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            columnas = ["Producto", "Método", "Precio_USD", "TRM", "Cantidad", "Flete_USD", "Arancel_pct", "IVA_pct", "Tarifa_Admin_COP", "Comision_TC_pct", "Alto_cm", "Ancho_cm", "Largo_cm", "Cajas", "Valor_CBM_COP", "Flete_Nacional_COP", "Costo_Pedido_COP", "Precio_Venta_ML", "Comision_ML_pct", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]
            for col in columnas:
                if col not in df_final.columns: df_final[col] = 0.0
            
            df_final[columnas].to_excel(writer, index=False, sheet_name='Reporte')
            ws = writer.sheets['Reporte']
            
            # Formatos de celda
            header_fill = PatternFill(start_color="1F4E78", fill_type="solid")
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = Font(color="FFFFFF", bold=True)
            
            for row in range(2, len(df_final) + 2):
                # Re-calculamos fórmulas en el Excel para que el usuario pueda editar valores después
                ws[f'T{row}'] = f'=IF(B{row}="Avión", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+G{row})*(1+H{row})+I{row})/IF(E{row}>0,E{row},1), IF(B{row}="Barco", (((C{row}*D{row}*E{row})+(F{row}*D{row}))*(1+J{row})+((K{row}*L{row}*M{row}/1000000)*N{row}*O{row})+P{row})/IF(E{row}>0,E{row},1), IF(B{row}="AliExpress", Q{row}/IF(E{row}>0,E{row},1), 0)))'
                ws[f'U{row}'] = f'=R{row}*(1-S{row})'
                ws[f'V{row}'] = f'=IF(T{row}>0, U{row}/T{row}, 0)'
                ws[f'T{row}'].number_format = '"$"#,##0'
                ws[f'U{row}'].number_format = '"$"#,##0'
                ws[f'V{row}'].number_format = '0.00'

            # Semáforo de Viabilidad
            green = PatternFill(start_color="C6EFCE", fill_type="solid")
            red = PatternFill(start_color="FFC7CE", fill_type="solid")
            rango = f"V2:V{len(df_final)+1}"
            ws.conditional_formatting.add(rango, CellIsRule(operator='greaterThan', formula=['1.5'], fill=green))
            ws.conditional_formatting.add(rango, CellIsRule(operator='lessThan', formula=['1.2'], fill=red))

        st.download_button("📥 Descargar Reporte Gerencial", buffer.getvalue(), "Reporte_Aduanero_Pro.xlsx", type="primary", use_container_width=True)
        if st.button("🗑️ Borrar Historial"):
            st.session_state['historial'] = []
            st.rerun()
    else:
        st.info("No hay datos para mostrar.")
