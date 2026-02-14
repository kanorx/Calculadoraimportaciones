import streamlit as st

# ==========================================
# 1. FUNCIONES DE CÁLCULO
# ==========================================

def calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin_cop, precio_ml, comision_ml_pct):
    precio_cop = precio_usd * trm
    costo_mercancia_cop = precio_cop * cantidad
    flete_cop = flete_usd * trm
    base_impuestos = costo_mercancia_cop + flete_cop
    valor_arancel = base_impuestos * arancel_pct
    base_iva = base_impuestos + valor_arancel
    valor_iva = base_iva * iva_pct
    costo_pedido_domicilio = base_impuestos + valor_arancel + valor_iva + tarifa_admin_cop
    costo_unitario = costo_pedido_domicilio / cantidad if cantidad > 0 else 0
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    return costo_unitario, ingreso_ml_neto, viabilidad

def calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen_usd, comision_tc_pct, alto_cm, ancho_cm, largo_cm, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml_pct):
    precio_cop = precio_usd * trm
    costo_mercancia_cop = precio_cop * cantidad
    envio_origen_cop = envio_origen_usd * trm
    total_cop_china = costo_mercancia_cop + envio_origen_cop
    valor_comision_tc = total_cop_china * comision_tc_pct
    volumen_m3 = (alto_cm * ancho_cm * largo_cm / 1000000) * cajas
    costo_nacionalizacion = volumen_m3 * cbm_agente
    costo_importado_bogota = total_cop_china + valor_comision_tc + costo_nacionalizacion
    costo_pedido_domicilio = costo_importado_bogota + flete_nacional
    costo_unitario = costo_pedido_domicilio / cantidad if cantidad > 0 else 0
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    return costo_unitario, ingreso_ml_neto, viabilidad, volumen_m3

def calcular_aliexpress(costo_pedido_cop, cantidad, precio_ml, comision_ml_pct):
    costo_unitario = costo_pedido_cop / cantidad if cantidad > 0 else 0
    ingreso_ml_neto = precio_ml * (1 - comision_ml_pct)
    viabilidad = ingreso_ml_neto / costo_unitario if costo_unitario > 0 else 0
    
    return costo_unitario, ingreso_ml_neto, viabilidad

# ==========================================
# 2. INTERFAZ DE USUARIO CON STREAMLIT
# ==========================================

# Configuración básica de la página
st.set_page_config(page_title="Calculadora de Importaciones", layout="centered")

st.title("📦 Calculadora de Viabilidad de Importaciones")
st.write("Ingresa los datos de tu producto para calcular los costos y la viabilidad en MercadoLibre.")

# Menú lateral para seleccionar el método
metodo = st.sidebar.selectbox(
    "Selecciona el método de importación:",
    ("Alibaba (Avión)", "Alibaba (Barco)", "AliExpress")
)

st.header(f"Método: {metodo}")

# --- SECCIÓN: ALIBABA (AVIÓN) ---
if metodo == "Alibaba (Avión)":
    col1, col2 = st.columns(2)
    with col1:
        precio_usd = st.number_input("Precio del producto (USD)", min_value=0.0, value=0.65, step=0.1)
        cantidad = st.number_input("Cantidad (Und)", min_value=1, value=200)
        flete_usd = st.number_input("Costo Flete (USD)", min_value=0.0, value=385.0)
        arancel_pct = st.number_input("% Arancel (Ej: 0.15 para 15%)", min_value=0.0, value=0.15)
        
    with col2:
        trm = st.number_input("TRM Actual (COP)", min_value=0.0, value=4026.0)
        iva_pct = st.number_input("% IVA (Ej: 0.19 para 19%)", min_value=0.0, value=0.19)
        tarifa_admin = st.number_input("Tarifa Administrativa (COP)", min_value=0.0, value=110000.0)
    
    st.subheader("Datos de Venta")
    col3, col4 = st.columns(2)
    with col3:
        precio_ml = st.number_input("Precio de venta en MercadoLibre (COP)", min_value=0.0, value=50000.0)
    with col4:
        comision_ml = st.number_input("Comisión ML (%) (Ej: 0.24)", min_value=0.0, value=0.24)

    if st.button("Calcular Viabilidad", type="primary"):
        costo_u, ingreso_n, viabilidad = calcular_alibaba_avion(precio_usd, trm, cantidad, flete_usd, arancel_pct, iva_pct, tarifa_admin, precio_ml, comision_ml)
        
        st.success("¡Cálculo exitoso!")
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario (COP)", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ingreso_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viabilidad:,.2f}x")

# --- SECCIÓN: ALIBABA (BARCO) ---
elif metodo == "Alibaba (Barco)":
    st.subheader("Costos en Origen")
    col1, col2 = st.columns(2)
    with col1:
        precio_usd = st.number_input("Precio del producto (USD)", min_value=0.0, value=0.65)
        cantidad = st.number_input("Cantidad (Und)", min_value=1, value=200)
        envio_origen = st.number_input("Envío Origen - Agente (USD)", min_value=0.0, value=80.0)
    with col2:
        trm = st.number_input("TRM Actual (COP)", min_value=0.0, value=4000.0)
        comision_tc = st.number_input("Comisión T.C (%)", min_value=0.0, value=0.03)
        flete_nacional = st.number_input("Flete Nacional (COP)", min_value=0.0, value=100000.0)

    st.subheader("Dimensiones y Agente de Carga")
    col3, col4, col5 = st.columns(3)
    with col3:
        alto = st.number_input("Alto (cm)", min_value=0.0, value=60.0)
        cajas = st.number_input("Cantidad de cajas", min_value=1, value=2)
    with col4:
        ancho = st.number_input("Ancho (cm)", min_value=0.0, value=40.0)
        cbm_agente = st.number_input("Valor CBM (COP)", min_value=0.0, value=2500000.0)
    with col5:
        largo = st.number_input("Largo (cm)", min_value=0.0, value=30.0)

    st.subheader("Datos de Venta")
    col6, col7 = st.columns(2)
    with col6:
        precio_ml = st.number_input("Precio de venta en MercadoLibre", min_value=0.0, value=40000.0)
    with col7:
        comision_ml = st.number_input("Comisión ML (%)", min_value=0.0, value=0.24)

    if st.button("Calcular Viabilidad", type="primary"):
        costo_u, ingreso_n, viabilidad, vol_m3 = calcular_alibaba_barco(precio_usd, trm, cantidad, envio_origen, comision_tc, alto, ancho, largo, cajas, cbm_agente, flete_nacional, precio_ml, comision_ml)
        
        st.success("¡Cálculo exitoso!")
        st.info(f"📏 Volumen calculado de la carga: {vol_m3:,.4f} m³")
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario (COP)", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ingreso_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viabilidad:,.2f}x")

# --- SECCIÓN: ALIEXPRESS ---
elif metodo == "AliExpress":
    col1, col2 = st.columns(2)
    with col1:
        costo_pedido = st.number_input("Costo de pedido en domicilio (COP)", min_value=0.0, value=243000.0)
        cantidad = st.number_input("Cantidad (Und)", min_value=1, value=10)
    with col2:
        precio_ml = st.number_input("Precio de venta en ML (COP)", min_value=0.0, value=99900.0)
        comision_ml = st.number_input("Comisión Meli (%)", min_value=0.0, value=0.24)
        
    if st.button("Calcular Viabilidad", type="primary"):
        costo_u, ingreso_n, viabilidad = calcular_aliexpress(costo_pedido, cantidad, precio_ml, comision_ml)
        
        st.success("¡Cálculo exitoso!")
        res1, res2, res3 = st.columns(3)
        res1.metric("Costo Unitario (COP)", f"${costo_u:,.2f}")
        res2.metric("Ingreso Neto ML", f"${ingreso_n:,.2f}")
        res3.metric("Ratio Viabilidad", f"{viabilidad:,.2f}x")
