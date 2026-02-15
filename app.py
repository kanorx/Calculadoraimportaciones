import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import io
import google.generativeai as genai

# ==========================================
# 0. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="Calculadora Pro", layout="wide", page_icon="📦")

# ==========================================
# 1. MEMORIA DE LA APP (HISTORIAL Y CHAT)
# ==========================================
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

# Nueva memoria para el historial del chat con la IA
if 'mensajes_chat' not in st.session_state:
    st.session_state['mensajes_chat'] = [
        {"role": "assistant", "content": "¡Hola! Soy tu asistente aduanero. Dime qué producto quieres importar y te ayudaré con la subpartida y el arancel estimado."}
    ]

def guardar_simulacion(nombre_producto, metodo, inputs, costo_u, ingreso_n, viabilidad):
    fila = {
        "Producto": nombre_producto, "Método": metodo, **inputs,
        "Costo Unitario (Res)": costo_u, "Ingreso ML (Res)": ingreso_n, "Viabilidad (Res)": viabilidad
    }
    st.session_state['historial'].append(fila)
    st.success(f"✅ '{nombre_producto}' guardado en el portafolio.")

# ==========================================
# 2. OBTENER TRM
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
# 3. CONFIGURACIÓN DE LA IA
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    IA_CONFIGURADA = True
except (KeyError, FileNotFoundError):
    IA_CONFIGURADA = False

# ==========================================
# 4. ASISTENTE FLOTANTE (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("🤖 IA Aduanera (Fase De Pruebas)")
    
    if not IA_CONFIGURADA:
        st.error("⚠️ Falta configurar la API Key en los secretos.")
    else:
        # Mostrar el historial de mensajes
        for msg in st.session_state['mensajes_chat']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Campo flotante en la parte inferior del sidebar para escribir
        if prompt := st.chat_input("Escribe tu producto aquí..."):
            # 1. Guardar y mostrar lo que escribió el usuario
            st.session_state['mensajes_chat'].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            # 2. Consultar a la IA
            with st.chat_message("assistant"):
                with st.spinner("Analizando..."):
                    try:
                        # Buscar modelo válido
                        modelo_elegido = None
                        for m_name in [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]:
                            if 'flash' in m_name or 'pro' in m_name:
                                modelo_elegido = m_name
                                break
                                
                        if modelo_elegido:
                            modelo = genai.GenerativeModel(modelo_elegido)
                            instruccion = f"""
                            Eres un experto en aduanas y aranceles en Colombia. 
                            El usuario pregunta: '{prompt}'.
                            Responde de forma clara, amigable y muy breve dando la subpartida sugerida aproximada, % de arancel y % de IVA.
                            No inventes ningun dato solo usa datos oficiales de Colombia.
                            Recuerda decirle que 🚩 este porcentaje puede haber cambiado que verifique con el codigo de la partida arancelaria.
                            """
                            respuesta = modelo.generate_content(instruccion)
                            
                            # Mostrar respuesta
                            st.markdown(respuesta.text)
                            # Guardar respuesta en la memoria
                            st.session_state['mensajes_chat'].append({"role": "assistant", "content": respuesta.text})
                        else:
                            st.error("No se encontró un modelo disponible.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
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
# 6. INTERFAZ PRINCIPAL (DERECHA)
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizado automáticamente)*")

# Solo 5 pestañas ahora, la IA ya no está aquí
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
        arancel_pct_av = st.number_input("% Arancel", value=0.15, key="ara_av")
        iva_pct_av = st.number_input("% IVA", value=0.19, key="iva_av")
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
    st.info("Sube la plantilla Excel descargada en la pestaña 'Comparador' para recalcular lotes enteros.")
    archivo_subido = st.file_uploader("Elige tu plantilla Excel (.xlsx)", type=["xlsx"])
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
        st.success("¡Archivo importado con éxito!")

# --- PESTAÑA 5: COMPARADOR Y EXPORTAR ---
with tab_comparador:
    st.subheader("📊 Tu Portafolio de Simulaciones")
    if len(st.session_state['historial']) > 0:
        df_historial = pd.DataFrame(st.session_state['historial'])
        st.dataframe(df_historial[["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]], use_container_width=True)
        
        fig = px.bar(df_historial, x="Producto", y="Viabilidad (Res)", color="Método", 
                     title="Comparación de Viabilidad por Producto", text_auto='.2f')
        fig.add_hline(y=1.5, line_dash="dot", annotation_text="Meta Mínima (1.5x)", annotation_position="bottom right")
        st.plotly_chart(fig, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Plantilla_Importacion')
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button("📥 Descargar Plantilla Excel", data=buffer.getvalue(), file_name="Plantilla_Calculadora.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
        with col_btn2:
            if st.button("Limpiar Historial", use_container_width=True): 
                st.session_state['historial'] = []
                st.rerun()
    else: st.info("Aún no has guardado simulaciones.")
