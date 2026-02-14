import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import io

# ==========================================
# 0. CONFIGURACIÓN E HISTORIAL (MEMORIA)
# ==========================================
st.set_page_config(page_title="Calculadora Pro", layout="wide", page_icon="📦")

if 'historial' not in st.session_state:
    st.session_state['historial'] = []

def guardar_simulacion(nombre_producto, metodo, inputs, costo_u, ingreso_n, viabilidad):
    # Guardamos el nombre, el método, todos los datos de entrada, y los resultados finales
    fila = {
        "Producto": nombre_producto,
        "Método": metodo,
        **inputs,  # Desempaqueta todos los datos del formulario (Precio, TRM, etc.)
        "Costo Unitario (Res)": costo_u,
        "Ingreso ML (Res)": ingreso_n,
        "Viabilidad (Res)": viabilidad
    }
    st.session_state['historial'].append(fila)
    st.success(f"✅ '{nombre_producto}' guardado en el portafolio.")

# ==========================================
# 1. FUNCIÓN PARA OBTENER TRM EN TIEMPO REAL
# ==========================================
@st.cache_data
def obtener_trm_colombia():
    try:
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        respuesta = requests.get(url)
        return float(respuesta.json()[0]['valor'])
    except:
        return 4000.0

TRM_HOY = obtener_trm_colombia()

# ==========================================
# 2. FUNCIONES DE CÁLCULO
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
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    return costo_unitario, ingreso_ml_neto, viabilidad

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto, ancho, largo, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0
    precio_cop = precio_usd * trm
    envio_origen_cop = envio_origen_usd * trm
    total_cop_china = (precio_cop * cantidad) + envio_origen_cop
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto * ancho * largo / 1000000) * cajas
    costo_nacionalizacion = volumen_m3 * cbm_agente
    costo_unitario = (total_cop_china + valor_comision_tc + costo_nacionalizacion + flete_nacional) / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    return costo_unitario, ingreso_ml_neto, viabilidad, volumen_m3

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    return costo_unitario, ingreso_ml_neto, viabilidad

# ==========================================
# 3. INTERFAZ DE USUARIO
# ==========================================
st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizado automáticamente)*")

tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Alibaba (Avión)", "🚢 Alibaba (Barco)", "🛒 AliExpress", "📁 Carga Masiva (Excel)", "📊 Comparador y Exportar"
])

# Variables base estandarizadas para el diccionario de inputs
base_inputs = lambda: {
    "Precio_USD": 0.0, "TRM": TRM_HOY, "Cantidad": 1, "Flete_USD": 0.0, "Arancel_pct": 0.0, 
    "IVA_pct": 0.0, "Tarifa_Admin_COP": 0.0, "Comision_TC_pct": 0.0, "Alto_cm": 0.0, 
    "Ancho_cm": 0.0, "Largo_cm": 0.0, "Cajas": 0, "Valor_CBM_COP": 0.0, "Flete_Nacional_COP": 0.0, 
    "Costo_Pedido_COP": 0.0, "Precio_Venta_ML": 0.0, "Comision_ML_pct": 0.24
}

# --- PESTAÑA 1: ALIBABA (AVIÓN) ---
with tab1:
    st.subheader("✈️ Simulación de Importación por Avión")
    nombre_prod_av = st.text_input("Nombre del Producto", value="Esponja para carro", key="nom_av")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_av = st.number_input("Precio producto (USD)", value=0.65, key="p_usd_av")
        cantidad_av = st.number_input("Cantidad (Und)", value=200, min_value=1, key="cant_av")
        flete_usd_av = st.number_input("Costo Flete (USD)", value=385.0, key="flete_av")
    with col2:
        trm_av = st.number_input("TRM Actual (COP)", value=TRM_HOY, key="trm_av_input")
        arancel_pct_av = st.number_input("% Arancel", value=0.15, key="ara_av")
        iva_pct_av = st.number_input("% IVA", value=0.19, key="iva_av")
    with col3:
        tarifa_admin_av = st.number_input("Tarifa Admin (COP)", value=110000.0, key="tar_av")
        precio_ml_av = st.number_input("Precio Venta ML (COP)", value=50000.0, key="pml_av")
        comision_ml_av = st.number_input("Comisión ML (%)", value=0.24, key="cml_av")

    if st.button("Calcular y Guardar (Avión)", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab = calcular_alibaba_avion(precio_usd_av, trm_av, cantidad_av, flete_usd_av, arancel_pct_av, iva_pct_av, tarifa_admin_av, precio_ml_av, comision_ml_av)
        
        inputs = base_inputs()
        inputs.update({"Precio_USD": precio_usd_av, "TRM": trm_av, "Cantidad": cantidad_av, "Flete_USD": flete_usd_av, "Arancel_pct": arancel_pct_av, "IVA_pct": iva_pct_av, "Tarifa_Admin_COP": tarifa_admin_av, "Precio_Venta_ML": precio_ml_av, "Comision_ML_pct": comision_ml_av})
        guardar_simulacion(nombre_prod_av, "Avión", inputs, costo_u, ingreso_n, viab)
        
        st.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 2: ALIBABA (BARCO) ---
with tab2:
    st.subheader("🚢 Simulación de Importación por Barco")
    nombre_prod_ba = st.text_input("Nombre del Producto", value="Lámpara RGB", key="nom_ba")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_ba = st.number_input("Precio (USD)", value=5.20, key="p_usd_ba")
        cantidad_ba = st.number_input("Cantidad", value=64, min_value=1, key="cant_ba")
        envio_origen_ba = st.number_input("Envío Origen (USD)", value=10.0, key="env_or_ba")
        trm_ba = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_ba_input")
    with col2:
        comision_tc_ba = st.number_input("Comisión T.C (%)", value=0.03, key="com_tc_ba")
        alto_ba = st.number_input("Alto caja (cm)", value=44.0, key="alt_ba")
        ancho_ba = st.number_input("Ancho caja (cm)", value=44.0, key="anch_ba")
        largo_ba = st.number_input("Largo caja (cm)", value=47.0, key="larg_ba")
    with col3:
        cajas_ba = st.number_input("Cantidad cajas", value=4, min_value=1, key="caj_ba")
        cbm_agente_ba = st.number_input("CBM (COP)", value=2400000.0, key="cbm_ba")
        flete_nacional_ba = st.number_input("Flete Nacional", value=100000.0, key="fletn_ba")
        precio_ml_ba = st.number_input("Venta ML (COP)", value=179900.0, key="pml_ba")
        comision_ml_ba = st.number_input("Comisión ML (%)", value=0.24, key="cml_ba2")

    if st.button("Calcular y Guardar (Barco)", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab, vol = calcular_alibaba_barco(precio_usd_ba, trm_ba, cantidad_ba, envio_origen_ba, comision_tc_ba, alto_ba, ancho_ba, largo_ba, cajas_ba, cbm_agente_ba, flete_nacional_ba, precio_ml_ba, comision_ml_ba)
        
        inputs = base_inputs()
        inputs.update({"Precio_USD": precio_usd_ba, "TRM": trm_ba, "Cantidad": cantidad_ba, "Flete_USD": envio_origen_ba, "Comision_TC_pct": comision_tc_ba, "Alto_cm": alto_ba, "Ancho_cm": ancho_ba, "Largo_cm": largo_ba, "Cajas": cajas_ba, "Valor_CBM_COP": cbm_agente_ba, "Flete_Nacional_COP": flete_nacional_ba, "Precio_Venta_ML": precio_ml_ba, "Comision_ML_pct": comision_ml_ba})
        guardar_simulacion(nombre_prod_ba, "Barco", inputs, costo_u, ingreso_n, viab)
        st.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    st.subheader("🛒 Simulación B2C AliExpress")
    nombre_prod_ali = st.text_input("Nombre del Producto", value="Auriculares de clip", key="nom_ali")
    col1, col2 = st.columns(2)
    with col1:
        costo_ped_ali = st.number_input("Costo Pedido (COP)", value=326000.0, key="costo_ali")
        cant_ali = st.number_input("Cantidad", value=10, min_value=1, key="cant_ali")
    with col2:
        precio_ml_ali = st.number_input("Venta ML (COP)", value=101000.0, key="pml_ali")
        comision_ml_ali = st.number_input("Comisión ML (%)", value=0.24, key="cml_ali")
        
    if st.button("Calcular y Guardar (AliExpress)", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab = calcular_aliexpress(costo_ped_ali, cant_ali, precio_ml_ali, comision_ml_ali)
        
        inputs = base_inputs()
        inputs.update({"Costo_Pedido_COP": costo_ped_ali, "Cantidad": cant_ali, "Precio_Venta_ML": precio_ml_ali, "Comision_ML_pct": comision_ml_ali})
        guardar_simulacion(nombre_prod_ali, "AliExpress", inputs, costo_u, ingreso_n, viab)
        st.metric("Ratio Viabilidad", f"{viab:,.2f}x")

# --- PESTAÑA 4: CARGA MASIVA CON EXCEL ---
with tab_masiva:
    st.subheader("📁 Procesar Reporte Excel")
    st.info("Sube aquí el mismo archivo Excel que descargaste de la pestaña 'Comparador y Exportar'. El sistema recalculará todos los productos usando su método correspondiente.")
    
    # Aceptamos .xlsx
    archivo_subido = st.file_uploader("Elige tu plantilla Excel (.xlsx)", type=["xlsx"])
    
    if archivo_subido is not None:
        try:
            # Leemos el excel y rellenamos los espacios vacíos con 0
            df = pd.read_excel(archivo_subido).fillna(0)
            st.dataframe(df.head()) 
            
            if st.button("Recalcular e Importar Portafolio", type="primary"):
                for index, row in df.iterrows():
                    metodo = str(row.get('Método', ''))
                    nombre = str(row.get('Producto', f'Fila {index}'))
                    
                    if metodo == "Avión":
                        costo_u, ing_n, viab = calcular_alibaba_avion(
                            row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], 
                            row['Arancel_pct'], row['IVA_pct'], row['Tarifa_Admin_COP'], 
                            row['Precio_Venta_ML'], row['Comision_ML_pct']
                        )
                    elif metodo == "Barco":
                        costo_u, ing_n, viab, _ = calcular_alibaba_barco(
                            row['Precio_USD'], row['TRM'], row['Cantidad'], row['Flete_USD'], 
                            row['Comision_TC_pct'], row['Alto_cm'], row['Ancho_cm'], row['Largo_cm'], 
                            row['Cajas'], row['Valor_CBM_COP'], row['Flete_Nacional_COP'], 
                            row['Precio_Venta_ML'], row['Comision_ML_pct']
                        )
                    elif metodo == "AliExpress":
                        costo_u, ing_n, viab = calcular_aliexpress(
                            row['Costo_Pedido_COP'], row['Cantidad'], 
                            row['Precio_Venta_ML'], row['Comision_ML_pct']
                        )
                    else:
                        continue # Si no reconoce el método, salta a la siguiente fila
                    
                    # Extraer los inputs de la fila para guardarlos igual
                    inputs = {k: row[k] for k in base_inputs().keys() if k in row}
                    guardar_simulacion(nombre, metodo, inputs, costo_u, ing_n, viab)
                
                st.success("¡Archivo importado y recalculado con éxito! Ve a la pestaña de Exportar.")
        except Exception as e:
            st.error(f"Error al procesar el Excel. Asegúrate de que tenga el formato de la plantilla exportada. Detalle: {e}")

# --- PESTAÑA 5: COMPARADOR Y EXPORTAR ---
with tab_comparador:
    st.subheader("📊 Tu Portafolio de Simulaciones")
    
    if len(st.session_state['historial']) > 0:
        df_historial = pd.DataFrame(st.session_state['historial'])
        
        # Mostrar solo columnas importantes en pantalla para no saturar
        columnas_visuales = ["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]
        st.dataframe(df_historial[columnas_visuales], use_container_width=True)
        
        fig = px.bar(df_historial, x="Producto", y="Viabilidad (Res)", color="Método", 
                     title="Comparación de Viabilidad por Producto", text_auto='.2f')
        fig.add_hline(y=1.5, line_dash="dot", annotation_text="Meta Mínima (1.5x)", annotation_position="bottom right")
        st.plotly_chart(fig, use_container_width=True)
        
        # Generar Excel completo con TODAS las columnas
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Plantilla_Importacion')
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                label="📥 Descargar Plantilla Excel",
                data=buffer.getvalue(),
                file_name="Plantilla_Calculadora_Importaciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        with col_btn2:
            if st.button("Limpiar Historial", use_container_width=True):
                st.session_state['historial'] = []
                st.rerun()
    else:
        st.info("Aún no has guardado ninguna simulación.")
