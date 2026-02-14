import streamlit as st
import plotly.express as px
import pandas as pd

# ==========================================
# 1. FUNCIONES DE CÁLCULO (Modificadas para retornar el desglose)
# ==========================================

def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, {}
    
    precio_cop = precio_usd * trm
    flete_cop = flete_usd * trm
    base_impuestos = (precio_cop * cantidad) + flete_cop
    valor_arancel = base_impuestos * arancel_pct
    base_iva = base_impuestos + valor_arancel
    valor_iva = base_iva * iva_pct
    
    costo_pedido_domicilio = base_impuestos + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = costo_pedido_domicilio / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    # Desglose de costos por unidad para graficar
    desglose = {
        "Producto": precio_cop,
        "Flete Internacional": flete_cop / cantidad,
        "Arancel": valor_arancel / cantidad,
        "IVA": valor_iva / cantidad,
        "Tarifa Administrativa": tarifa_admin_cop / cantidad
    }
    
    return costo_unitario, ingreso_ml_neto, viabilidad, desglose

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto_cm, ancho_cm, largo_cm, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, 0, {}

    precio_cop = precio_usd * trm
    costo_mercancia_cop = precio_cop * cantidad
    envio_origen_cop = envio_origen_usd * trm
    total_cop_china = costo_mercancia_cop + envio_origen_cop
    
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto_cm * ancho_cm * largo_cm / 1000000) * cajas
    costo_nacionalizacion = volumen_m3 * cbm_agente
    
    costo_importado_bogota = total_cop_china + valor_comision_tc + costo_nacionalizacion
    costo_pedido_domicilio = costo_importado_bogota + flete_nacional
    
    costo_unitario = costo_pedido_domicilio / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    # Desglose de costos por unidad
    desglose = {
        "Producto": precio_cop,
        "Envío Origen (China)": envio_origen_cop / cantidad,
        "Comisión TC": valor_comision_tc / cantidad,
        "Nacionalización (CBM)": costo_nacionalizacion / cantidad,
        "Flete Nacional": flete_nacional / cantidad
    }
    
    return costo_unitario, ingreso_ml_neto, viabilidad, volumen_m3, desglose

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    if cantidad <= 0: return 0, 0, 0, {}

    costo_unitario = costo_pedido_cop / cantidad
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    desglose = {
        "Costo Producto + Envío": costo_unitario
    }
    
    return costo_unitario, ingreso_ml_neto, viabilidad, desglose

# ==========================================
# 2. FUNCIÓN PARA DIBUJAR GRÁFICOS
# ==========================================
def mostrar_resultados_y_graficos(costo_unitario, ingreso_ml_neto, viabilidad, desglose_costos, precio_ml, comision_ml_pct):
    st.divider()
    st.subheader("📊 Resultados del Análisis")
    
    col_metrics, col_charts = st.columns([1, 2])
    
    with col_metrics:
        st.metric("Costo Unitario (COP)", f"${costo_unitario:,.2f}")
        st.metric("Ingreso Neto ML (COP)", f"${ingreso_ml_neto:,.2f}")
        
        ganancia_neta = ingreso_ml_neto - costo_unitario
        color_ganancia = "normal" if ganancia_neta > 0 else "inverse"
        st.metric("Ganancia Neta por Unidad", f"${ganancia_neta:,.2f}", delta=f"${ganancia_neta:,.2f}", delta_color=color_ganancia)
        
        st.metric("Ratio Viabilidad", f"{viabilidad:,.2f}x")
        if viabilidad >= 2.0:
            st.success("✅ Producto Altamente Viable")
        elif viabilidad >= 1.5:
            st.warning("⚠️ Viabilidad Moderada (Revisar márgenes)")
        else:
            st.error("❌ Baja Viabilidad (Poco margen)")

    with col_charts:
        tab_pie, tab_bar = st.tabs(["Desglose de Costos", "Rentabilidad ML"])
        
        with tab_pie:
            # Gráfico de torta para el desglose de costos
            df_costos = pd.DataFrame(list(desglose_costos.items()), columns=['Concepto', 'Costo'])
            fig_pie = px.pie(df_costos, values='Costo', names='Concepto', hole=0.4, 
                             title="Distribución del Costo Unitario")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with tab_bar:
            # Gráfico de barras para ver Precio de Venta vs Costos y Ganancia
            valor_comision = precio_ml * comision_ml_pct
            df_rentabilidad = pd.DataFrame({
                "Concepto": ["Costo Total", "Comisión ML", "Ganancia Neta"],
                "Valor (COP)": [costo_unitario, valor_comision, ganancia_neta]
            })
            fig_bar = px.bar(df_rentabilidad, x="Concepto", y="Valor (COP)", text_auto='.2s',
                             title="Desglose del Precio de Venta en MercadoLibre",
                             color="Concepto", color_discrete_sequence=["#EF553B", "#636EFA", "#00CC96"])
            st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 3. INTERFAZ DE USUARIO CON STREAMLIT
# ==========================================

st.set_page_config(page_title="Calculadora de Importaciones", layout="wide", page_icon="📦")

st.title("📦 Calculadora de Viabilidad de Importaciones")
st.markdown("Calcula tus márgenes, visualiza tus costos y toma decisiones inteligentes antes de importar.")

# Usamos Tabs en lugar de un sidebar para un diseño más moderno
tab1, tab2, tab3 = st.tabs(["✈️ Alibaba (Avión)", "🚢 Alibaba (Barco)", "🛒 AliExpress"])

# --- PESTAÑA 1: ALIBABA (AVIÓN) ---
with tab1:
    with st.expander("📝 Ingresar Datos de Importación", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            precio_usd_av = st.number_input("Precio producto (USD)", value=0.65, key="p_usd_av")
            cantidad_av = st.number_input("Cantidad (Und)", value=200, min_value=1, key="cant_av")
            flete_usd_av = st.number_input("Costo Flete (USD)", value=385.0, key="flete_av")
        with col2:
            trm_av = st.number_input("TRM Actual (COP)", value=4026.0, key="trm_av")
            arancel_pct_av = st.number_input("% Arancel (Ej: 0.15)", value=0.15, key="ara_av")
            iva_pct_av = st.number_input("% IVA (Ej: 0.19)", value=0.19, key="iva_av")
        with col3:
            tarifa_admin_av = st.number_input("Tarifa Admin (COP)", value=110000.0, key="tar_av")
            precio_ml_av = st.number_input("Precio Venta ML (COP)", value=50000.0, key="pml_av")
            comision_ml_av = st.number_input("Comisión ML (%) (Ej: 0.24)", value=0.24, key="cml_av")

    if st.button("Calcular Viabilidad Avión", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab, desglose = calcular_alibaba_avion(
            precio_usd_av, trm_av, cantidad_av, flete_usd_av, arancel_pct_av, iva_pct_av, tarifa_admin_av, precio_ml_av, comision_ml_av
        )
        mostrar_resultados_y_graficos(costo_u, ingreso_n, viab, desglose, precio_ml_av, comision_ml_av)


# --- PESTAÑA 2: ALIBABA (BARCO) ---
with tab2:
    with st.expander("📝 Ingresar Datos de Importación", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            precio_usd_ba = st.number_input("Precio producto (USD)", value=0.65, key="p_usd_ba")
            cantidad_ba = st.number_input("Cantidad (Und)", value=200, min_value=1, key="cant_ba")
            envio_origen_ba = st.number_input("Envío Origen - Agente (USD)", value=80.0, key="env_or_ba")
            trm_ba = st.number_input("TRM Actual (COP)", value=4000.0, key="trm_ba")
        with col2:
            comision_tc_ba = st.number_input("Comisión T.C (%)", value=0.03, key="com_tc_ba")
            alto_ba = st.number_input("Alto caja (cm)", value=60.0, key="alt_ba")
            ancho_ba = st.number_input("Ancho caja (cm)", value=40.0, key="anch_ba")
            largo_ba = st.number_input("Largo caja (cm)", value=30.0, key="larg_ba")
        with col3:
            cajas_ba = st.number_input("Cantidad de cajas", value=2, min_value=1, key="caj_ba")
            cbm_agente_ba = st.number_input("Valor CBM (COP)", value=2500000.0, key="cbm_ba")
            flete_nacional_ba = st.number_input("Flete Nacional (COP)", value=100000.0, key="fletn_ba")
            
        col_ml1, col_ml2 = st.columns(2)
        precio_ml_ba = col_ml1.number_input("Precio Venta ML (COP)", value=40000.0, key="pml_ba")
        comision_ml_ba = col_ml2.number_input("Comisión ML (%)", value=0.24, key="cml_ba")

    if st.button("Calcular Viabilidad Barco", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab, vol_m3, desglose = calcular_alibaba_barco(
            precio_usd_ba, trm_ba, cantidad_ba, envio_origen_ba, comision_tc_ba, alto_ba, ancho_ba, largo_ba, cajas_ba, cbm_agente_ba, flete_nacional_ba, precio_ml_ba, comision_ml_ba
        )
        st.info(f"📐 Volumen calculado de la carga: **{vol_m3:,.4f} m³**")
        mostrar_resultados_y_graficos(costo_u, ingreso_n, viab, desglose, precio_ml_ba, comision_ml_ba)


# --- PESTAÑA 3: ALIEXPRESS ---
with tab3:
    with st.expander("📝 Ingresar Datos de Importación", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            costo_pedido_ali = st.number_input("Costo de pedido en domicilio (COP)", value=243000.0, key="costo_ali")
            cantidad_ali = st.number_input("Cantidad (Und)", value=10, min_value=1, key="cant_ali")
        with col2:
            precio_ml_ali = st.number_input("Precio Venta ML (COP)", value=99900.0, key="pml_ali")
            comision_ml_ali = st.number_input("Comisión ML (%)", value=0.24, key="cml_ali")
            
    if st.button("Calcular Viabilidad AliExpress", type="primary", use_container_width=True):
        costo_u, ingreso_n, viab, desglose = calcular_aliexpress(
            costo_pedido_ali, cantidad_ali, precio_ml_ali, comision_ml_ali
        )
        mostrar_resultados_y_graficos(costo_u, ingreso_n, viab, desglose, precio_ml_ali, comision_ml_ali)
