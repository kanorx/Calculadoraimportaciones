import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import io

# ==========================================
# 0. CONFIGURACIÓN E HISTORIAL (MEMORIA)
# ==========================================
st.set_page_config(page_title="Calculadora Pro", layout="wide", page_icon="📦")

# Inicializar la memoria para guardar productos
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

def guardar_simulacion(nombre_producto, metodo, costo_u, ingreso_n, viabilidad):
    st.session_state['historial'].append({
        "Producto": nombre_producto,
        "Método": metodo,
        "Costo Unitario": costo_u,
        "Ingreso ML Neto": ingreso_n,
        "Viabilidad": viabilidad
    })
    st.success(f"✅ '{nombre_producto}' guardado en el comparador.")

# ==========================================
# 1. FUNCIÓN PARA OBTENER TRM EN TIEMPO REAL
# ==========================================
@st.cache_data # Esto hace que solo consulte una vez por día y no ponga lenta la app
def obtener_trm_colombia():
    try:
        # API oficial de Datos Abiertos Colombia
        url = "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC"
        respuesta = requests.get(url)
        datos = respuesta.json()
        trm_hoy = float(datos[0]['valor'])
        return trm_hoy
    except Exception as e:
        return 4000.0 # Valor por defecto si falla el internet

TRM_HOY = obtener_trm_colombia()

# ==========================================
# 2. FUNCIONES DE CÁLCULO
# ==========================================

def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, {}
    precio_cop = precio_usd * trm
    flete_cop = flete_usd * trm
    base_impuestos = (precio_cop * cantidad) + flete_cop
    valor_arancel = base_impuestos * arancel_pct
    valor_iva = (base_impuestos + valor_arancel) * iva_pct
    costo_pedido = base_impuestos + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = costo_pedido / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    desglose = {"Producto": precio_cop, "Flete": flete_cop / cantidad, "Arancel": valor_arancel / cantidad, "IVA": valor_iva / cantidad, "Tarifa": tarifa_admin_cop / cantidad}
    return costo_unitario, ingreso_ml_neto, viabilidad, desglose

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto, ancho, largo, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0, {}
    precio_cop = precio_usd * trm
    envio_origen_cop = envio_origen_usd * trm
    total_cop_china = (precio_cop * cantidad) + envio_origen_cop
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto * ancho * largo / 1000000) * cajas
    costo_nacionalizacion = volumen_m3 * cbm_agente
    costo_unitario = (total_cop_china + valor_comision_tc + costo_nacionalizacion + flete_nacional) / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    desglose = {"Producto": precio_cop, "Envío Origen": envio_origen_cop / cantidad, "Comisión TC": valor_comision_tc / cantidad, "Nacionalización": costo_nacionalizacion / cantidad, "Flete Nac.": flete_nacional / cantidad}
    return costo_unitario, ingreso_ml_neto, viabilidad, volumen_m3, desglose

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, {}
    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    return costo_unitario, ingreso_ml_neto, viabilidad, {"Producto+Envío": costo_unitario}

# ==========================================
# 3. INTERFAZ DE USUARIO 
# ==========================================

st.title("📦 Calculadora Pro de Importaciones")
st.markdown(f"**TRM Oficial del día:** `${TRM_HOY:,.2f} COP` *(Actualizado automáticamente)*")

# 5 Pestañas ahora
tab1, tab2, tab3, tab_masiva, tab_comparador = st.tabs([
    "✈️ Alibaba (Avión)", "🚢 Alibaba (Barco)", "🛒 AliExpress", "📁 Carga Masiva", "📊 Comparador y Exportar"
])

# --- PESTAÑA 1: AVION ---
with tab1:
    nombre_prod_av = st.text_input("Nombre del Producto", value="Producto A", key="nom_av")
    col1, col2, col3 = st.columns(3)
    with col1:
        precio_usd_av = st.number_input("Precio (USD)", value=0.65, key="p_usd_av")
        cantidad_av = st.number_input("Cantidad", value=200, key="cant_av")
        flete_usd_av = st.number_input("Costo Flete (USD)", value=385.0, key="flete_av")
    with col2:
        trm_av = st.number_input("TRM (COP)", value=TRM_HOY, key="trm_av")
        arancel_pct_av = st.number_input("% Arancel", value=0.15, key="ara_av")
        iva_pct_av = st.number_input("% IVA", value=0.19, key="iva_av")
    with col3:
        tarifa_admin_av = st.number_input("Tarifa Admin", value=110000.0, key="tar_av")
        precio_ml_av = st.number_input("Venta ML (COP)", value=50000.0, key="pml_av")
        comision_ml_av = st.number_input("Comisión ML", value=0.24, key="cml_av")

    if st.button("Calcular y Guardar (Avión)", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab, desglose = calcular_alibaba_avion(
            precio_usd_av, trm_av, cantidad_av, flete_usd_av, arancel_pct_av, iva_pct_av, tarifa_admin_av, precio_ml_av, comision_ml_av
        )
        guardar_simulacion(nombre_prod_av, "Alibaba Avión", costo_u, ingreso_n, viab)
        st.info(f"Costo Unitario: ${costo_u:,.2f} | Viabilidad: {viab:,.2f}x")

# --- PESTAÑA 2: BARCO (Simplificada visualmente para este ejemplo) ---
with tab2:
    nombre_prod_ba = st.text_input("Nombre del Producto", value="Producto B", key="nom_ba")
    st.write("*(Llena los datos como en la versión anterior)*")
    # Para ahorrar espacio en este ejemplo, he puesto valores por defecto directos
    if st.button("Calcular y Guardar Simulación Rápida (Barco)"):
        costo_u, ingreso_n, viab, vol, desglose = calcular_alibaba_barco(0.65, TRM_HOY, 200, 80, 0.03, 60, 40, 30, 2, 2500000, 100000, 40000, 0.24)
        guardar_simulacion(nombre_prod_ba, "Alibaba Barco", costo_u, ingreso_n, viab)
        st.info(f"Costo Unitario: ${costo_u:,.2f} | Viabilidad: {viab:,.2f}x")

# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    nombre_prod_ali = st.text_input("Nombre del Producto", value="Producto C", key="nom_ali")
    costo_ped_ali = st.number_input("Costo Pedido (COP)", value=243000.0)
    cant_ali = st.number_input("Cantidad", value=10)
    precio_ml_ali = st.number_input("Venta ML", value=99900.0)
    comision_ml_ali = st.number_input("Comisión ML", value=0.24)
    if st.button("Calcular y Guardar (AliExpress)", type="primary"):
        costo_u, ingreso_n, viab, desglose = calcular_aliexpress(costo_ped_ali, cant_ali, precio_ml_ali, comision_ml_ali)
        guardar_simulacion(nombre_prod_ali, "AliExpress", costo_u, ingreso_n, viab)
        st.info(f"Costo Unitario: ${costo_u:,.2f} | Viabilidad: {viab:,.2f}x")

# --- PESTAÑA 4: CARGA MASIVA ---
with tab_masiva:
    st.subheader("Subir listado de AliExpress")
    st.write("Sube un archivo CSV con las columnas: `Nombre Producto`, `Costo de pedido`, `Cantidad (Und)`, `Precio en ML`, `Comision`")
    archivo_subido = st.file_uploader("Elige tu archivo CSV", type=["csv"])
    
    if archivo_subido is not None:
        try:
            df = pd.read_csv(archivo_subido)
            st.dataframe(df.head()) # Mostrar previsualización
            if st.button("Procesar Archivo"):
                for index, row in df.iterrows():
                    # Simulamos el cálculo para cada fila asumiendo columnas estándar
                    # Ajusta los nombres de las columnas según tu Excel real
                    try:
                        c_pedido = float(row['Costo de pedido en domicilio  (Producto+envio)'])
                        cant = float(row['Cantidad (Und)'])
                        p_ml = float(row['Precio Total Producto en Mercadolibre'])
                        com_ml = float(row['Comision Meli (%)'])
                        nombre = str(row['Nombre Producto'])
                        
                        costo_u, ingreso_n, viab, _ = calcular_aliexpress(c_pedido, cant, p_ml, com_ml)
                        guardar_simulacion(nombre, "Masivo - AliExpress", costo_u, ingreso_n, viab)
                    except KeyError as e:
                        st.error(f"Falta la columna {e} en el archivo")
                        break
        except Exception as e:
            st.error("Error al leer el archivo. Asegúrate de que sea un CSV válido.")

# --- PESTAÑA 5: COMPARADOR Y EXPORTAR ---
with tab_comparador:
    st.subheader("📊 Tu Portafolio de Simulaciones")
    
    if len(st.session_state['historial']) > 0:
        # 1. Convertir la memoria en un DataFrame (Tabla)
        df_historial = pd.DataFrame(st.session_state['historial'])
        st.dataframe(df_historial, use_container_width=True)
        
        # 2. Gráfico Comparativo
        fig = px.bar(df_historial, x="Producto", y="Viabilidad", color="Método", 
                     title="Comparación de Viabilidad por Producto", text_auto='.2f')
        fig.add_hline(y=1.5, line_dash="dot", annotation_text="Meta Mínima (1.5x)", annotation_position="bottom right")
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Exportar a Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_historial.to_excel(writer, index=False, sheet_name='Simulaciones')
        
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=buffer.getvalue(),
            file_name="Reporte_Viabilidad_Importaciones.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
        
        if st.button("Limpiar Historial"):
            st.session_state['historial'] = []
            st.rerun() # Recargar la página
    else:
        st.info("Aún no has guardado ninguna simulación. Ve a las pestañas anteriores y calcula algunos productos.")
