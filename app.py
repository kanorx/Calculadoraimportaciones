import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import io
from typing import List, Dict

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Importaciones Colombia - China",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para tema claro y oscuro
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
    .usd-text {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Estilos para tema oscuro */
    @media (prefers-color-scheme: dark) {
        .cost-box {
            background-color: #262730;
            border-left: 4px solid #ff4b4b;
        }
        .usd-text {
            color: #ccc;
        }
    }
    
    .product-table {
        margin: 1rem 0;
    }
    .action-buttons {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class Producto:
    def __init__(self, nombre="", cantidad=1, precio_unitario_usd=0, peso_unitario_kg=0):
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

class CalculadoraImportaciones:
    def __init__(self):
        self.tasa_cambio = self.obtener_tasa_cambio()
        self.iva = 0.19  # 19% IVA en Colombia
        self.anticipo_iva = 0.10  # 10% anticipo de IVA
        self.dai_arancel = 0.05  # 5% DAI (Arancel) - puede variar por producto
    
    def obtener_tasa_cambio(self):
        """Obtiene la tasa de cambio actual USD a COP"""
        try:
            return 3950
        except:
            return 3950
    
    def calcular_cif(self, valor_producto, flete_internacional, seguro):
        """Calcula valor CIF (Cost, Insurance, Freight)"""
        return valor_producto + flete_internacional + seguro
    
    def calcular_dai(self, cif, tasa_arancel=None):
        """Calcula Derecho Arancelario a la Importación"""
        if tasa_arancel is None:
            tasa_arancel = self.dai_arancel
        return cif * tasa_arancel
    
    def calcular_iva(self, cif, dai):
        """Calcula IVA sobre CIF + DAI"""
        base_iva = cif + dai
        return base_iva * self.iva
    
    def calcular_anticipo_iva(self, iva):
        """Calcula anticipo de IVA"""
        return iva * self.anticipo_iva
    
    def calcular_gastos_varios(self, cif, peso_total_kg):
        """Calcula gastos varios (agente aduanal, almacenamiento, etc.)"""
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
        """Formatea valores monetarios"""
        if moneda == 'COP':
            return f"${valor:,.0f} COP"
        else:
            return f"${valor:,.2f} USD"
    
    def convertir_a_usd(self, valor_cop):
        """Convierte COP a USD"""
        return valor_cop / self.tasa_cambio

def inicializar_session_state():
    """Inicializa las variables de session state"""
    if 'productos' not in st.session_state:
        st.session_state.productos = []
    if 'calculos_realizados' not in st.session_state:
        st.session_state.calculos_realizados = False
    if 'costo_total_cop' not in st.session_state:
        st.session_state.costo_total_cop = 0

def mostrar_formulario_agregar_producto():
    """Muestra el formulario para agregar productos"""
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
        if submitted:
            if nombre and nombre.strip():
                nuevo_producto = Producto(nombre.strip(), cantidad, precio_unitario, peso_unitario)
                st.session_state.productos.append(nuevo_producto)
                st.success(f"Producto '{nombre}' agregado correctamente")
                st.rerun()
            else:
                st.error("Por favor ingresa un nombre para el producto")

def mostrar_tabla_productos():
    """Muestra la tabla de productos y controles"""
    if st.session_state.productos:
        st.subheader("Lista de Productos")
        
        # Crear DataFrame para mostrar
        datos_productos = []
        for i, producto in enumerate(st.session_state.productos):
            datos_productos.append({
                'ID': i + 1,
                'Producto': producto.nombre,
                'Cantidad': producto.cantidad,
                'Precio Unitario (USD)': f"${producto.precio_unitario_usd:,.2f}",
                'Peso Unitario (KG)': f"{producto.peso_unitario_kg:,.1f}",
                'Precio Total (USD)': f"${producto.precio_total_usd:,.2f}",
                'Peso Total (KG)': f"{producto.peso_total_kg:,.1f}"
            })
        
        df_productos = pd.DataFrame(datos_productos)
        st.dataframe(df_productos, use_container_width=True)
        
        # Controles de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Eliminar Todos los Productos", use_container_width=True):
                st.session_state.productos = []
                st.session_state.calculos_realizados = False
                st.rerun()
        
        with col2:
            total_precio_usd = sum(p.precio_total_usd for p in st.session_state.productos)
            total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos)
            st.info(f"**Resumen:** {len(st.session_state.productos)} productos | "
                   f"Total: ${total_precio_usd:,.2f} USD | "
                   f"Peso: {total_peso_kg:,.1f} KG")
        
        with col3:
            # Selector para eliminar producto específico
            opciones_eliminar = [f"{i+1}. {p.nombre}" for i, p in enumerate(st.session_state.productos)]
            producto_a_eliminar = st.selectbox(
                "Seleccionar producto a eliminar:",
                options=opciones_eliminar,
                key="eliminar_select"
            )
            if st.button("❌ Eliminar Seleccionado", use_container_width=True):
                if producto_a_eliminar:
                    indice = int(producto_a_eliminar.split('.')[0]) - 1
                    producto_eliminado = st.session_state.productos.pop(indice)
                    st.success(f"Producto '{producto_eliminado.nombre}' eliminado")
                    st.session_state.calculos_realizados = False
                    st.rerun()

def gestionar_importacion_exportacion():
    """Gestiona la importación y exportación de datos"""
    st.subheader("Importar/Exportar Datos")
    
    col_exp, col_imp = st.columns(2)
    
    with col_exp:
        # Exportar a Excel
        if st.session_state.productos:
            df_export = pd.DataFrame([{
                'Nombre': p.nombre,
                'Cantidad': p.cantidad,
                'Precio_Unitario_USD': p.precio_unitario_usd,
                'Peso_Unitario_KG': p.peso_unitario_kg
            } for p in st.session_state.productos])
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Productos')
            
            st.download_button(
                label="📥 Exportar Productos a Excel",
                data=excel_buffer.getvalue(),
                file_name=f"productos_importacion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("No hay productos para exportar")
    
    with col_imp:
        # Importar desde Excel
        archivo_subido = st.file_uploader("Importar desde Excel", type=['xlsx'], key="import_excel")
        if archivo_subido is not None:
            try:
                df_import = pd.read_excel(archivo_subido)
                productos_importados = []
                
                required_columns = ['Nombre', 'Cantidad', 'Precio_Unitario_USD', 'Peso_Unitario_KG']
                if all(col in df_import.columns for col in required_columns):
                    for _, row in df_import.iterrows():
                        producto = Producto(
                            nombre=str(row['Nombre']),
                            cantidad=int(row['Cantidad']),
                            precio_unitario_usd=float(row['Precio_Unitario_USD']),
                            peso_unitario_kg=float(row['Peso_Unitario_KG'])
                        )
                        productos_importados.append(producto)
                    
                    st.session_state.productos = productos_importados
                    st.session_state.calculos_realizados = False
                    st.success(f"✅ {len(productos_importados)} productos importados correctamente")
                    st.rerun()
                else:
                    st.error("El archivo Excel no tiene el formato correcto. Las columnas requeridas son: Nombre, Cantidad, Precio_Unitario_USD, Peso_Unitario_KG")
            except Exception as e:
                st.error(f"Error al importar archivo: {str(e)}")

def pestaña_gestion_productos():
    """Pestaña dedicada a la gestión de productos"""
    st.markdown('<div class="sub-header">📦 Gestión de Productos</div>', unsafe_allow_html=True)
    
    mostrar_formulario_agregar_producto()
    st.markdown("---")
    mostrar_tabla_productos()
    st.markdown("---")
    gestionar_importacion_exportacion()

def pestaña_calculadora_principal(calc):
    """Pestaña principal con la calculadora"""
    st.markdown('<div class="sub-header">🚚 Calculadora de Importación</div>', unsafe_allow_html=True)
    
    # Mostrar resumen de productos si existen
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
        st.subheader("Configuración de Impuestos")
        tasa_arancel_personalizada = st.slider(
            "Tasa de arancel (DAI) %",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.5,
            key="arancel_slider"
        ) / 100
    
    # Botón para calcular
    if st.button("🔄 Calcular Costos de Importación", type="primary", use_container_width=True):
        st.session_state.calculos_realizados = True
        calcular_costos_importacion(calc, total_valor_productos_usd, total_peso_kg, 
                                  flete_internacional_usd, seguro_usd, tasa_arancel_personalizada)
    
    # Mostrar resultados si los cálculos están realizados
    if st.session_state.calculos_realizados and 'resultados_calculo' in st.session_state:
        mostrar_resultados_calculo(calc)

def calcular_costos_importacion(calc, valor_productos_usd, peso_total_kg, flete_usd, seguro_usd, tasa_arancel):
    """Realiza los cálculos de importación y guarda los resultados"""
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
        
        # Guardar resultados en session state
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
            'tasa_arancel': tasa_arancel
        }

def mostrar_resultados_calculo(calc):
    """Muestra los resultados del cálculo"""
    resultados = st.session_state.resultados_calculo
    
    st.markdown("---")
    st.markdown('<div class="sub-header">💰 Desglose de Costos</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Costos Internacionales")
        st.markdown(f'<div class="cost-box">Valor CIF (Mercancía + Flete + Seguro):<br><strong>{calc.formato_moneda(resultados["cif_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["cif_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
        
        st.markdown("#### Impuestos y Aranceles")
        st.markdown(f'<div class="cost-box">DAI (Arancel {resultados["tasa_arancel"]*100:.1f}%):<br><strong>{calc.formato_moneda(resultados["dai_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["dai_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">IVA (19%):<br><strong>{calc.formato_moneda(resultados["iva_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["iva_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Anticipo de IVA (10%):<br><strong>{calc.formato_moneda(resultados["anticipo_iva_cop"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(resultados["anticipo_iva_cop"]), "USD")}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Gastos Nacionales")
        gastos = resultados["gastos_varios"]
        st.markdown(f'<div class="cost-box">Agencia Aduanal:<br><strong>{calc.formato_moneda(gastos["agencia_aduanal"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["agencia_aduanal"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Almacenamiento:<br><strong>{calc.formato_moneda(gastos["almacenamiento"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["almacenamiento"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Transporte Interno:<br><strong>{calc.formato_moneda(gastos["transporte_interno"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["transporte_interno"]), "USD")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="cost-box">Otros Gastos:<br><strong>{calc.formato_moneda(gastos["otros_gastos"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos["otros_gastos"]), "USD")}</div></div>', unsafe_allow_html=True)
    
    # Total final
    costo_total_usd = calc.convertir_a_usd(resultados["costo_total_cop"])
    st.markdown(f'<div class="total-box">TOTAL ESTIMADO DE IMPORTACIÓN:<br>{calc.formato_moneda(resultados["costo_total_cop"])}<br><div style="font-size: 1.2rem;">{calc.formato_moneda(costo_total_usd, "USD")}</div></div>', unsafe_allow_html=True)

def pestaña_reportes(calc):
    """Pestaña de reportes y análisis"""
    st.markdown('<div class="sub-header">📈 Reportes y Análisis</div>', unsafe_allow_html=True)
    
    if not st.session_state.calculos_realizados or 'resultados_calculo' not in st.session_state:
        st.info("Realiza primero los cálculos en la pestaña 'Calculadora Principal' para ver los reportes")
        return
    
    resultados = st.session_state.resultados_calculo
    total_valor_productos_usd = sum(p.precio_total_usd for p in st.session_state.productos)
    total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos)
    
    # Métricas clave
    col1, col2, col3 = st.columns(3)
    
    with col1:
        costo_por_kg = resultados["costo_total_cop"] / total_peso_kg if total_peso_kg > 0 else 0
        st.metric("Costo por KG", calc.formato_moneda(costo_por_kg))
    
    with col2:
        incremento_por_impuestos = ((resultados["dai_cop"] + resultados["iva_cop"]) / resultados["cif_cop"]) * 100
        st.metric("Incremento por impuestos", f"{incremento_por_impuestos:.1f}%")
    
    with col3:
        relacion_costo_impuestos = (resultados["costo_total_cop"] - resultados["cif_cop"]) / resultados["cif_cop"] * 100
        st.metric("Costos adicionales vs CIF", f"{relacion_costo_impuestos:.1f}%")
    
    # Tabla de distribución
    st.markdown("---")
    st.subheader("Distribución de Costos")
    
    datos_distribucion = {
        'Concepto': ['Mercancía', 'Flete y Seguro', 'DAI', 'IVA', 'Gastos Varios'],
        'Valor COP': [
            resultados["valor_producto_cop"],
            resultados["flete_internacional_cop"] + resultados["seguro_cop"],
            resultados["dai_cop"],
            resultados["iva_cop"],
            resultados["gastos_varios"]['total']
        ]
    }
    
    df_distribucion = pd.DataFrame(datos_distribucion)
    df_distribucion['Porcentaje'] = (df_distribucion['Valor COP'] / resultados["costo_total_cop"]) * 100
    df_distribucion['Valor USD'] = df_distribucion['Valor COP'] / calc.tasa_cambio
    
    st.dataframe(df_distribucion, use_container_width=True)
    
    # Exportar reporte completo
    st.markdown("---")
    st.subheader("Exportar Reporte Completo")
    
    reporte_data = {
        'Concepto': [
            'Valor mercancía (FOB)',
            'Flete internacional',
            'Seguro',
            'Valor CIF',
            'DAI (Arancel)',
            'IVA',
            'Anticipo IVA',
            'Gastos varios',
            'TOTAL IMPORTACIÓN'
        ],
        'COP': [
            resultados["valor_producto_cop"],
            resultados["flete_internacional_cop"],
            resultados["seguro_cop"],
            resultados["cif_cop"],
            resultados["dai_cop"],
            resultados["iva_cop"],
            resultados["anticipo_iva_cop"],
            resultados["gastos_varios"]['total'],
            resultados["costo_total_cop"]
        ],
        'USD': [
            total_valor_productos_usd,
            resultados["flete_internacional_cop"] / calc.tasa_cambio,
            resultados["seguro_cop"] / calc.tasa_cambio,
            calc.convertir_a_usd(resultados["cif_cop"]),
            calc.convertir_a_usd(resultados["dai_cop"]),
            calc.convertir_a_usd(resultados["iva_cop"]),
            calc.convertir_a_usd(resultados["anticipo_iva_cop"]),
            calc.convertir_a_usd(resultados["gastos_varios"]['total']),
            calc.convertir_a_usd(resultados["costo_total_cop"])
        ]
    }
    
    df_reporte = pd.DataFrame(reporte_data)
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_reporte.to_excel(writer, index=False, sheet_name='Resumen Costos')
        if st.session_state.productos:
            df_productos_export = pd.DataFrame([{
                'Nombre': p.nombre,
                'Cantidad': p.cantidad,
                'Precio_Unitario_USD': p.precio_unitario_usd,
                'Peso_Unitario_KG': p.peso_unitario_kg,
                'Precio_Total_USD': p.precio_total_usd,
                'Peso_Total_KG': p.peso_total_kg
            } for p in st.session_state.productos])
            df_productos_export.to_excel(writer, index=False, sheet_name='Productos')
    
    st.download_button(
        label="📊 Descargar Reporte Completo Excel",
        data=excel_buffer.getvalue(),
        file_name=f"reporte_importacion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def main():
    st.markdown('<h1 class="main-header">📦 Calculadora de Importaciones Colombia - China</h1>', unsafe_allow_html=True)
    
    # Inicializar session state
    inicializar_session_state()
    
    # Inicializar calculadora
    calc = CalculadoraImportaciones()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ Información General")
        st.info(f"Tasa de cambio actual: **1 USD = ${calc.tasa_cambio:,.0f} COP**")
        
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
        
        st.markdown("---")
        st.markdown("### 💡 Tips de Importación")
        st.markdown("""
        - Verifica el arancel específico de tu producto
        - Considera tiempos de tránsito (30-45 días)
        - Ten documentación completa
        - Consulta con agente aduanal
        """)
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["📊 Calculadora Principal", "📦 Gestión de Productos", "📈 Reportes"])
    
    with tab1:
        pestaña_calculadora_principal(calc)
    
    with tab2:
        pestaña_gestion_productos()
    
    with tab3:
        pestaña_reportes(calc)

if __name__ == "__main__":
    main()
