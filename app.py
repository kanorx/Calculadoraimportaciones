import streamlit as st
import pandas as pd
import plotly.express as px
import time

# =============================
# CONFIGURACIÓN GENERAL
# =============================
st.set_page_config(
    page_title="Simulador Importaciones PRO",
    layout="wide",
    page_icon="📦"
)

# =============================
# CSS PREMIUM
# =============================
st.markdown("""
<style>

body {
    background-color: #0f172a;
}

h2, h3 {
    margin-top: 25px;
    margin-bottom: 15px;
}

.stNumberInput {
    margin-bottom: 10px;
}

.card {
    background-color: #1e293b;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
    margin-bottom: 20px;
}

.fade-in {
    animation: fadeIn 0.8s ease-in-out;
}

@keyframes fadeIn {
    from {opacity: 0;}
    to {opacity: 1;}
}

</style>
""", unsafe_allow_html=True)

# =============================
# FUNCIONES
# =============================
def calcular_alibaba_avion(precio_usd, trm, cantidad, flete,
                           arancel, iva, admin,
                           precio_ml, comision_ml):

    costo_producto = precio_usd * trm * cantidad
    costo_flete = flete
    base_arancel = costo_producto + costo_flete
    valor_arancel = base_arancel * (arancel/100)
    base_iva = base_arancel + valor_arancel
    valor_iva = base_iva * (iva/100)

    costo_total = costo_producto + costo_flete + valor_arancel + valor_iva + admin
    costo_unitario = costo_total / cantidad

    ingreso_ml = precio_ml - (precio_ml * (comision_ml/100))
    viabilidad = ingreso_ml / costo_unitario

    return costo_total, costo_unitario, ingreso_ml, viabilidad

# =============================
# SIDEBAR
# =============================
st.sidebar.title("📦 Simulador PRO")
st.sidebar.markdown("Herramienta para pequeños importadores")

# =============================
# TABS
# =============================
tab_avion, tab_comparador = st.tabs(["✈️ Importación Aérea", "📊 Comparador"])

# ============================================================
# TAB AVIÓN
# ============================================================
with tab_avion:

    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)

    st.subheader("Simulación Aérea")

    st.markdown("### Datos del Producto")
    col1, col2 = st.columns(2)

    precio_usd = col1.number_input("Precio USD", value=5.0)
    trm = col2.number_input("TRM", value=4000.0)
    cantidad = col1.number_input("Cantidad", value=100)
    flete = col2.number_input("Flete Total", value=300000.0)

    st.markdown("### Impuestos y Costos")
    col3, col4 = st.columns(2)

    arancel = col3.number_input("Arancel (%)", value=10.0)
    iva = col4.number_input("IVA (%)", value=19.0)
    admin = col3.number_input("Gastos Administrativos", value=200000.0)

    st.markdown("### Precio y Plataforma")
    col5, col6 = st.columns(2)

    precio_ml = col5.number_input("Precio Venta Mercado Libre", value=80000.0)
    comision_ml = col6.number_input("Comisión ML (%)", value=15.0)

    if st.button("Calcular Simulación Aérea", type="primary"):

        progress_bar = st.progress(0)

        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)

        c_tot, c_u, i_n, v = calcular_alibaba_avion(
            precio_usd, trm, cantidad, flete,
            arancel, iva, admin,
            precio_ml, comision_ml
        )

        progress_bar.empty()

        st.markdown('<div class="fade-in">', unsafe_allow_html=True)

        res1, res2, res3, res4 = st.columns(4)

        res1.metric("Costo Total", f"${c_tot:,.0f}")
        res2.metric("Costo Unitario", f"${c_u:,.0f}")
        res3.metric("Ingreso Neto ML", f"${i_n:,.0f}")

        delta_color = "normal"
        if v < 1.2:
            delta_color = "inverse"

        res4.metric(
            "Ratio Rentabilidad",
            f"{v:,.2f}x",
            delta="Óptimo" if v >= 1.5 else "Revisar",
            delta_color=delta_color
        )

        if v >= 1.5:
            st.success("🟢 Producto altamente viable")
        elif v >= 1.2:
            st.warning("🟡 Margen aceptable pero ajustable")
        else:
            st.error("🔴 Producto no recomendable")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# TAB COMPARADOR
# ============================================================
with tab_comparador:

    st.subheader("Comparador de Productos")

    st.markdown('<div class="card fade-in">', unsafe_allow_html=True)

    data = {
        "Producto": ["Producto A", "Producto B", "Producto C"],
        "Método": ["Aéreo", "Aéreo", "Aéreo"],
        "Costo Unitario (Res)": [30000, 40000, 25000],
        "Ingreso ML (Res)": [60000, 65000, 50000],
        "Viabilidad (Res)": [2.0, 1.6, 2.1]
    }

    df_export = pd.DataFrame(data)

    # =============================
    # MÉTRICAS RESUMEN
    # =============================
    promedio_viabilidad = df_export["Viabilidad (Res)"].mean()
    mejor_producto = df_export.loc[df_export["Viabilidad (Res)"].idxmax()]["Producto"]
    total_inversion = df_export["Costo Unitario (Res)"].sum()

    colA, colB, colC = st.columns(3)

    colA.metric("Viabilidad Promedio", f"{promedio_viabilidad:.2f}x")
    colB.metric("Producto Más Rentable", mejor_producto)
    colC.metric("Suma Costos Unitarios", f"${total_inversion:,.0f}")

    # =============================
    # GRÁFICO 1
    # =============================
    fig = px.bar(
        df_export,
        x="Producto",
        y=["Costo Unitario (Res)", "Ingreso ML (Res)"],
        barmode="group",
        color_discrete_map={
            'Costo Unitario (Res)': '#ef4444',
            'Ingreso ML (Res)': '#22c55e'
        }
    )

    fig.update_layout(
        plot_bgcolor='#0f172a',
        paper_bgcolor='#0f172a',
        font_color='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # =============================
    # GRÁFICO 2
    # =============================
    fig2 = px.line(
        df_export,
        x="Producto",
        y="Viabilidad (Res)",
        markers=True
    )

    fig2.update_layout(
        plot_bgcolor='#0f172a',
        paper_bgcolor='#0f172a',
        font_color='white'
    )

    st.plotly_chart(fig2, use_container_width=True)

    # =============================
    # TABLA FINAL
    # =============================
    st.dataframe(
        df_export[["Producto", "Método", "Costo Unitario (Res)", "Ingreso ML (Res)", "Viabilidad (Res)"]],
        use_container_width=True,
        height=350
    )

    st.markdown('</div>', unsafe_allow_html=True)
