import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Importaciones Colombia - China",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .cost-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .total-box {
        background-color: #1f77b4;
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    .profit-box {
        background-color: #28a745;
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 1rem 0;
    }
    .usd-text {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

class Producto:
    def __init__(self, nombre="", cantidad=1, precio_unitario_usd=0, peso_unitario_kg=0, id=None):
        self.id = id if id is not None else datetime.now().timestamp()
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio_unitario_usd = precio_unitario_usd
        self.peso_unitario_kg = peso_unitario_kg
    
    @property
    def precio_total_usd(self):
        return self.cantidad * self.precio_unitario_usd
    
    @property
    def peso_total_kg(self):
        return self.cantidad * self.peso_unitario_kg
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'cantidad': self.cantidad,
            'precio_unitario_usd': self.precio_unitario_usd,
            'peso_unitario_kg': self.peso_unitario_kg
        }

class CalculadoraImportaciones:
    def __init__(self):
        self.tasa_cambio = self.obtener_tasa_cambio()
        self.iva = 0.19
        self.anticipo_iva = 0.10
    
    def obtener_tasa_cambio(self):
        return 3950
    
    def calcular_cif(self, valor_producto, flete_internacional, seguro):
        return valor_producto + flete_internacional + seguro
    
    def calcular_dai(self, cif, tasa_arancel):
        return cif * tasa_arancel
    
    def calcular_iva(self, cif, dai):
        base_iva = cif + dai
        return base_iva * self.iva
    
    def calcular_anticipo_iva(self, iva):
        return iva * self.anticipo_iva
    
    def calcular_gastos_varios(self, cif, peso_total_kg):
        agencia_aduanal = max(cif * 0.015, 300000)
        almacenamiento = max(150000, peso_total_kg * 500)
        transporte_interno = max(200000, peso_total_kg * 800)
        otros_gastos = 100000
        
        return {
            'agencia_aduanal': agencia_aduanal,
            'almacenamiento': almacenamiento,
            'transporte_interno': transporte_interno,
            'otros_gastos': otros_gastos,
            'total': agencia_aduanal + almacenamiento + transporte_interno + otros_gastos
        }
    
    def formato_moneda(self, valor, moneda='COP'):
        if moneda == 'COP':
            return f"${valor:,.0f} COP"
        else:
            return f"${valor:,.2f} USD"
    
    def convertir_a_usd(self, valor_cop):
        return valor_cop / self.tasa_cambio

def inicializar_session_state():
    if 'productos' not in st.session_state:
        st.session_state.productos = []
    if 'calculos_realizados' not in st.session_state:
        st.session_state.calculos_realizados = False
    if 'porcentaje_rentabilidad' not in st.session_state:
        st.session_state.porcentaje_rentabilidad = 30.0
    if 'editing_product_id' not in st.session_state:
        st.session_state.editing_product_id = None
    if 'recalcular_automatico' not in st.session_state:
        st.session_state.recalcular_automatico = False

def mostrar_formulario_agregar_producto():
    with st.form("agregar_producto_form", clear_on_submit=True):
        st.subheader("Agregar Nuevo Producto")
        nombre = st.text_input("Nombre del producto", key="nombre_producto")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            cantidad = st.number_input("Cantidad", min_value=1, value=1, key="cantidad_producto")
        with col_b:
            precio_unitario = st.number_input("Precio unitario (USD)", min_value=0.0, value=0.0, step=10.0, key="precio_producto")
        with col_c:
            peso_unitario = st.number_input("Peso unitario (KG)", min_value=0.0, value=0.0, step=0.1, key="peso_producto")
        
        submitted = st.form_submit_button("➕ Agregar Producto")
        if submitted and nombre and nombre.strip():
            nuevo_producto = Producto(nombre.strip(), cantidad, precio_unitario, peso_unitario)
            st.session_state.productos.append(nuevo_producto)
            st.success(f"Producto '{nombre}' agregado correctamente")
            st.rerun()

def mostrar_tabla_productos_editable():
    if st.session_state.productos:
        st.subheader("Lista de Productos - Haz clic para editar")
        
        datos_productos = []
        for i, producto in enumerate(st.session_state.productos):
            datos_productos.append({
                'ID': i + 1,
                'Producto': producto.nombre,
                'Cantidad': producto.cantidad,
                'Precio Unitario (USD)': producto.precio_unitario_usd,
                'Peso Unitario (KG)': producto.peso_unitario_kg,
                'Precio Total (USD)': producto.precio_total_usd,
                'Peso Total (KG)': producto.peso_total_kg,
                'producto_id': producto.id
            })
        
        for i, producto_data in enumerate(datos_productos):
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 1, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{producto_data['ID']}**")
                with col2:
                    if st.session_state.editing_product_id == producto_data['producto_id']:
                        nuevo_nombre = st.text_input("Nombre", value=producto_data['Producto'], key=f"edit_nombre_{producto_data['producto_id']}")
                    else:
                        st.write(producto_data['Producto'])
                with col3:
                    if st.session_state.editing_product_id == producto_data['producto_id']:
                        nueva_cantidad = st.number_input("Cantidad", value=producto_data['Cantidad'], min_value=1, key=f"edit_cantidad_{producto_data['producto_id']}")
                    else:
                        st.write(producto_data['Cantidad'])
                with col4:
                    if st.session_state.editing_product_id == producto_data['producto_id']:
                        nuevo_precio = st.number_input("Precio USD", value=float(producto_data['Precio Unitario (USD)']), min_value=0.0, step=10.0, key=f"edit_precio_{producto_data['producto_id']}")
                    else:
                        st.write(f"${producto_data['Precio Unitario (USD)']:,.2f}")
                with col5:
                    if st.session_state.editing_product_id == producto_data['producto_id']:
                        nuevo_peso = st.number_input("Peso KG", value=float(producto_data['Peso Unitario (KG)']), min_value=0.0, step=0.1, key=f"edit_peso_{producto_data['producto_id']}")
                    else:
                        st.write(f"{producto_data['Peso Unitario (KG)']:,.1f}")
                with col6:
                    st.write(f"${producto_data['Precio Total (USD)']:,.2f}")
                with col7:
                    if st.session_state.editing_product_id == producto_data['producto_id']:
                        if st.button("💾 Guardar", key=f"save_{producto_data['producto_id']}"):
                            producto_actualizado = Producto(
                                nombre=nuevo_nombre,
                                cantidad=int(nueva_cantidad),
                                precio_unitario_usd=float(nuevo_precio),
                                peso_unitario_kg=float(nuevo_peso),
                                id=producto_data['producto_id']
                            )
                            st.session_state.productos[i] = producto_actualizado
                            st.session_state.editing_product_id = None
                            st.session_state.calculos_realizados = False
                            st.success("Producto actualizado correctamente")
                            st.rerun()
                    else:
                        if st.button("✏️ Editar", key=f"edit_{producto_data['producto_id']}"):
                            st.session_state.editing_product_id = producto_data['producto_id']
                            st.rerun()
                
                st.markdown("---")
        
        # Controles de acción
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗑️ Eliminar Todos", use_container_width=True):
                st.session_state.productos = []
                st.session_state.calculos_realizados = False
                st.session_state.editing_product_id = None
                st.rerun()
        with col2:
            total_precio_usd = sum(p.precio_total_usd for p in st.session_state.productos)
            total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos)
            st.info(f"**Resumen:** {len(st.session_state.productos)} productos | "
                   f"Total: ${total_precio_usd:,.2f} USD | "
                   f"Peso: {total_peso_kg:,.1f} KG")
        with col3:
            opciones_eliminar = [f"{i+1}. {p.nombre}" for i, p in enumerate(st.session_state.productos)]
            if opciones_eliminar:
                producto_a_eliminar = st.selectbox("Seleccionar producto a eliminar:", options=opciones_eliminar, key="eliminar_select")
                if st.button("❌ Eliminar Seleccionado", use_container_width=True) and producto_a_eliminar:
                    indice = int(producto_a_eliminar.split('.')[0]) - 1
                    producto_eliminado = st.session_state.productos.pop(indice)
                    st.session_state.editing_product_id = None
                    st.session_state.calculos_realizados = False
                    st.success(f"Producto '{producto_eliminado.nombre}' eliminado")
                    st.rerun()

def pestaña_calculadora_principal(calc):
    st.markdown('<div class="sub-header">🚚 Calculadora de Importación</div>', unsafe_allow_html=True)
    
    # Configuración de porcentajes
    col_config1, col_config2, col_config3 = st.columns(3)
    
    with col_config1:
        st.subheader("Configuración de Impuestos")
        tasa_arancel_personalizada = st.number_input(
            "Tasa de arancel (DAI) %",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.1,
            key="arancel_input"
        ) / 100
        
        iva_personalizado = st.number_input(
            "IVA %",
            min_value=0.0,
            max_value=100.0,
            value=19.0,
            step=0.1,
            key="iva_input"
        ) / 100
        
        calc.iva = iva_personalizado
    
    with col_config2:
        st.subheader("Configuración de Rentabilidad")
        nuevo_porcentaje = st.number_input(
            "Porcentaje de rentabilidad esperado %",
            min_value=0.0,
            max_value=500.0,
            value=st.session_state.porcentaje_rentabilidad,
            step=5.0,
            key="rentabilidad_input_principal"
        )
        
        if nuevo_porcentaje != st.session_state.porcentaje_rentabilidad:
            st.session_state.porcentaje_rentabilidad = nuevo_porcentaje
            st.session_state.recalcular_automatico = True
    
    with col_config3:
        st.subheader("Resumen de Configuración")
        st.info(f"**DAI:** {tasa_arancel_personalizada*100:.1f}%")
        st.info(f"**IVA:** {iva_personalizado*100:.1f}%")
        st.info(f"**Rentabilidad esperada:** {st.session_state.porcentaje_rentabilidad:.1f}%")
    
    # Mostrar resumen de productos
    if st.session_state.productos:
        total_valor_productos_usd = sum(p.precio_total_usd for p in st.session_state.productos)
        total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos)
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric("Valor total productos", f"${total_valor_productos_usd:,.2f} USD")
        with col_res2:
            st.metric("Peso total productos", f"{total_peso_kg:,.1f} KG")
    else:
        st.info("💡 Agrega productos en la pestaña 'Gestión de Productos' para comenzar los cálculos")
        total_valor_productos_usd = 0
        total_peso_kg = 0
    
    st.markdown("---")
    
    # Configuración de envío
    col_env1, col_env2 = st.columns(2)
    
    with col_env1:
        st.subheader("Costos de Envío")
        flete_internacional_usd = st.number_input(
            "Flete internacional (USD)",
            min_value=0.0,
            max_value=50000.0,
            value=500.0,
            step=50.0,
            key="flete_input"
        )
        
        seguro_usd = st.number_input(
            "Seguro (USD)",
            min_value=0.0,
            max_value=10000.0,
            value=max(50.0, total_valor_productos_usd * 0.01),
            step=10.0,
            key="seguro_input"
        )
    
    with col_env2:
        st.subheader("Acciones")
        if st.button("🔄 Calcular Costos de Importación", type="primary", use_container_width=True) or st.session_state.recalcular_automatico:
            if total_valor_productos_usd > 0:
                st.session_state.calculos_realizados = True
                st.session_state.recalcular_automatico = False
                calcular_costos_importacion(calc, total_valor_productos_usd, total_peso_kg, 
                                          flete_internacional_usd, seguro_usd, tasa_arancel_personalizada)
                st.rerun()
            else:
                st.error("Agrega productos primero para realizar los cálculos")
    
    # Mostrar resultados
    if st.session_state.calculos_realizados and 'resultados_calculo' in st.session_state:
        mostrar_resultados_calculo(calc)

def calcular_costos_importacion(calc, valor_productos_usd, peso_total_kg, flete_usd, seguro_usd, tasa_arancel):
    if valor_productos_usd > 0:
        # Conversión a COP
        valor_producto_cop = valor_productos_usd * calc.tasa_cambio
        flete_internacional_cop = flete_usd * calc.tasa_cambio
        seguro_cop = seguro_usd * calc.tasa_cambio
        
        # Cálculos
        cif_cop = calc.calcular_cif(valor_producto_cop, flete_internacional_cop, seguro_cop)
        dai_cop = calc.calcular_dai(cif_cop, tasa_arancel)
        iva_cop = calc.calcular_iva(cif_cop, dai_cop)
        anticipo_iva_cop = calc.calcular_anticipo_iva(iva_cop)
        gastos_varios = calc.calcular_gastos_varios(cif_cop, peso_total_kg)
        
        costo_total_cop = cif_cop + dai_cop + iva_cop + gastos_varios['total']
        costo_total_usd = calc.convertir_a_usd(costo_total_cop)
        
        # Calcular precios de venta
        precio_venta_sugerido_cop = costo_total_cop * (1 + st.session_state.porcentaje_rentabilidad / 100)
        precio_venta_sugerido_usd = precio_venta_sugerido_cop / calc.tasa_cambio
        
        # Guardar resultados
        st.session_state.resultados_calculo = {
            'valor_producto_cop': valor_producto_cop,
            'flete_internacional_cop': flete_internacional_cop,
            'seguro_cop': seguro_cop,
            'cif_cop': cif_cop,
            'dai_cop': dai_cop,
            'iva_cop': iva_cop,
            'anticipo_iva_cop': anticipo_iva_cop,
            'gastos_varios': gastos_varios,
            'costo_total_cop': costo_total_cop,
            'costo_total_usd': costo_total_usd,
            'tasa_arancel': tasa_arancel,
            'iva_usado': calc.iva,
            'precio_venta_sugerido_cop': precio_venta_sugerido_cop,
            'precio_venta_sugerido_usd': precio_venta_sugerido_usd,
            'utilidad_esperada_cop': precio_venta_sugerido_cop - costo_total_cop,
            'utilidad_esperada_usd': (precio_venta_sugerido_cop - costo_total_cop) / calc.tasa_cambio
        }

def mostrar_resultados_calculo(calc):
    resultados = st.session_state.resultados_calculo
    
    st.markdown("---")
    st.markdown('<div class="sub-header">💰 Desglose de Costos</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Costos Internacionales")
        st.markdown(f'<div class="cost-box">Valor CIF:<br><strong>{calc.formato_moneda(resultados["cif_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["cif_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
        
        st.markdown("#### Impuestos y Aranceles")
        st.markdown(f'<div class="cost-box">DAI ({resultados["tasa_arancel"]*100:.1f}%):<br><strong>{calc.formato_moneda(resultados["dai_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["dai_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">IVA ({resultados["iva_usado"]*100:.1f}%):<br><strong>{calc.formato_moneda(resultados["iva_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["iva_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Gastos Nacionales")
        gastos = resultados["gastos_varios"]
        st.markdown(f'<div class="cost-box">Agencia Aduanal:<br><strong>{calc.formato_moneda(gastos["agencia_aduanal"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["agencia_aduanal"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Almacenamiento:<br><strong>{calc.formato_moneda(gastos["almacenamiento"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["almacenamiento"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Transporte Interno:<br><strong>{calc.formato_moneda(gastos["transporte_interno"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["transporte_interno"]), "USD")}</div></div>', unsafe_allow_html=True)
    
    # Totales
    col_total, col_venta = st.columns(2)
    
    with col_total:
        st.markdown(f'<div class="total-box">COSTO TOTAL:<br>{calc.formato_moneda(resultados["costo_total_cop"])}<br><div style="font-size: 1.2rem;">{calc.formato_moneda(resultados["costo_total_usd"], "USD")}</div></div>', unsafe_allow_html=True)
    
    with col_venta:
        st.markdown(f'<div class="profit-box">PRECIO VENTA SUGERIDO:<br>{calc.formato_moneda(resultados["precio_venta_sugerido_cop"])}<br><div style="font-size: 1.2rem;">{calc.formato_moneda(resultados["precio_venta_sugerido_usd"], "USD")}</div><div style="font-size: 0.9rem;">Utilidad: {calc.formato_moneda(resultados["utilidad_esperada_cop"])}</div></div>', unsafe_allow_html=True)

def pestaña_analisis_ventas(calc):
    st.markdown('<div class="sub-header">💰 Análisis de Ventas y Rentabilidad</div>', unsafe_allow_html=True)
    
    if not st.session_state.calculos_realizados or 'resultados_calculo' not in st.session_state:
        st.info("Realiza primero los cálculos en la pestaña 'Calculadora Principal' para ver el análisis de ventas")
        return
    
    resultados = st.session_state.resultados_calculo
    
    # Configuración de análisis
    col_anal1, col_anal2 = st.columns(2)
    
    with col_anal1:
        st.subheader("Análisis de Rentabilidad")
        
        # Usar un slider con un botón de aplicar para evitar recálculo automático
        nuevo_porcentaje = st.slider(
            "Porcentaje de rentabilidad %",
            min_value=0.0,
            max_value=200.0,
            value=float(st.session_state.porcentaje_rentabilidad),
            step=5.0,
            key="rentabilidad_slider_analisis"
        )
        
        if st.button("🔄 Aplicar Nuevo Porcentaje", key="aplicar_rentabilidad"):
            st.session_state.porcentaje_rentabilidad = nuevo_porcentaje
            st.session_state.recalcular_automatico = True
            st.rerun()
        
        st.metric(
            "Rentabilidad actual", 
            f"{st.session_state.porcentaje_rentabilidad:.1f}%"
        )
    
    with col_anal2:
        st.subheader("Precios de Venta")
        
        # Precio manual
        precio_manual_cop = st.number_input(
            "Precio de venta manual (COP)",
            min_value=0.0,
            value=float(resultados['precio_venta_sugerido_cop']),
            step=10000.0,
            key="precio_manual_input"
        )
        
        if precio_manual_cop > 0:
            utilidad_manual_cop = precio_manual_cop - resultados['costo_total_cop']
            porcentaje_rentabilidad_manual = (utilidad_manual_cop / resultados['costo_total_cop']) * 100
            
            col_manual1, col_manual2 = st.columns(2)
            with col_manual1:
                st.metric("Rentabilidad", f"{porcentaje_rentabilidad_manual:.1f}%")
            with col_manual2:
                st.metric("Utilidad", calc.formato_moneda(utilidad_manual_cop))
    
    # Gráfico de distribución
    st.markdown("---")
    st.subheader("Distribución de Costos y Utilidad")
    
    labels = ['Mercancía', 'Flete y Seguro', 'DAI', 'IVA', 'Gastos Varios', 'Utilidad']
    values = [
        resultados['valor_producto_cop'],
        resultados['flete_internacional_cop'] + resultados['seguro_cop'],
        resultados['dai_cop'],
        resultados['iva_cop'],
        resultados['gastos_varios']['total'],
        resultados['utilidad_esperada_cop']
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#28a745']
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3, marker_colors=colors)])
    fig.update_layout(title="Distribución del Precio de Venta")
    st.plotly_chart(fig, use_container_width=True)
    
    # Análisis por unidad
    st.markdown("---")
    st.subheader("Análisis por Unidad")
    
    if st.session_state.productos:
        total_unidades = sum(p.cantidad for p in st.session_state.productos)
        costo_por_unidad = resultados['costo_total_cop'] / total_unidades
        precio_venta_por_unidad = resultados['precio_venta_sugerido_cop'] / total_unidades
        
        col_unidad1, col_unidad2, col_unidad3 = st.columns(3)
        with col_unidad1:
            st.metric("Total unidades", f"{total_unidades:,}")
        with col_unidad2:
            st.metric("Costo por unidad", calc.formato_moneda(costo_por_unidad))
        with col_unidad3:
            st.metric("Precio venta por unidad", calc.formato_moneda(precio_venta_por_unidad))
        
        # Punto de equilibrio
        st.markdown("---")
        st.subheader("Punto de Equilibrio")
        
        unidades_para_equilibrio = max(1, int(resultados['costo_total_cop'] / precio_venta_por_unidad))
        col_equi1, col_equi2 = st.columns(2)
        with col_equi1:
            st.metric("Unidades para equilibrio", f"{unidades_para_equilibrio:,}")
        with col_equi2:
            st.metric("Margen de seguridad", f"{(total_unidades - unidades_para_equilibrio):,} unidades")

def main():
    st.markdown('<h1 class="main-header">📦 Calculadora de Importaciones Colombia - China</h1>', unsafe_allow_html=True)
    
    # Inicializar session state
    inicializar_session_state()
    
    # Inicializar calculadora
    calc = CalculadoraImportaciones()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ Información General")
        st.info(f"Tasa de cambio: **1 USD = ${calc.tasa_cambio:,.0f} COP**")
        
        st.header("⚙️ Configuración")
        tasa_personalizada = st.number_input(
            "Tasa de cambio USD/COP",
            min_value=1000.0,
            max_value=10000.0,
            value=float(calc.tasa_cambio),
            step=10.0,
            key="tasa_cambio_input"
        )
        calc.tasa_cambio = tasa_personalizada
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["📊 Calculadora Principal", "📦 Gestión de Productos", "💰 Análisis Ventas"])
    
    with tab1:
        pestaña_calculadora_principal(calc)
    
    with tab2:
        st.markdown('<div class="sub-header">📦 Gestión de Productos</div>', unsafe_allow_html=True)
        mostrar_formulario_agregar_producto()
        st.markdown("---")
        mostrar_tabla_productos_editable()
    
    with tab3:
        pestaña_analisis_ventas(calc)

if __name__ == "__main__":
    main()
