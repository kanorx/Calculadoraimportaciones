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
            # Valor por defecto
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
        # Estos son valores estimados, pueden variar
        agencia_aduanal = max(cif * 0.015, 300000)  # 1.5% o mínimo 300,000 COP
        almacenamiento = max(150000, peso_total_kg * 500)  # Basado en peso
        transporte_interno = max(200000, peso_total_kg * 800)
        otros_gastos = 100000  # Estimado
        
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

def gestionar_productos():
    """Interfaz para gestionar productos"""
    st.markdown('<div class="sub-header">📦 Gestión de Productos</div>', unsafe_allow_html=True)
    
    # Inicializar lista de productos en session state
    if 'productos' not in st.session_state:
        st.session_state.productos = []
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Formulario para agregar producto
        with st.form("agregar_producto"):
            st.subheader("Agregar Nuevo Producto")
            nombre = st.text_input("Nombre del producto")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                cantidad = st.number_input("Cantidad", min_value=1, value=1)
            with col_b:
                precio_unitario = st.number_input("Precio unitario (USD)", min_value=0.0, value=0.0, step=10.0)
            with col_c:
                peso_unitario = st.number_input("Peso unitario (KG)", min_value=0.0, value=0.0, step=0.1)
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre:
                    nuevo_producto = Producto(nombre, cantidad, precio_unitario, peso_unitario)
                    st.session_state.productos.append(nuevo_producto)
                    st.success(f"Producto '{nombre}' agregado correctamente")
                    st.rerun()
                else:
                    st.error("Por favor ingresa un nombre para el producto")
    
    with col2:
        # Importar/Exportar datos
        st.subheader("Importar/Exportar")
        
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
                label="📥 Exportar a Excel",
                data=excel_buffer.getvalue(),
                file_name=f"productos_importacion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Importar desde Excel
        archivo_subido = st.file_uploader("Importar desde Excel", type=['xlsx'])
        if archivo_subido:
            try:
                df_import = pd.read_excel(archivo_subido)
                productos_importados = []
                
                for _, row in df_import.iterrows():
                    producto = Producto(
                        nombre=str(row['Nombre']),
                        cantidad=int(row['Cantidad']),
                        precio_unitario_usd=float(row['Precio_Unitario_USD']),
                        peso_unitario_kg=float(row['Peso_Unitario_KG'])
                    )
                    productos_importados.append(producto)
                
                st.session_state.productos = productos_importados
                st.success(f"✅ {len(productos_importados)} productos importados correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"Error al importar archivo: {str(e)}")
    
    # Mostrar tabla de productos
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
        
        # Botones de acción rápida
        col_actions1, col_actions2, col_actions3 = st.columns(3)
        
        with col_actions1:
            if st.button("🗑️ Eliminar Todos los Productos", use_container_width=True):
                st.session_state.productos = []
                st.rerun()
        
        with col_actions2:
            if st.button("📊 Calcular Totales", use_container_width=True):
                # Mostrar resumen rápido
                total_precio_usd = sum(p.precio_total_usd for p in st.session_state.productos)
                total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos)
                st.info(f"**Resumen:** {len(st.session_state.productos)} productos | "
                       f"Total: ${total_precio_usd:,.2f} USD | "
                       f"Peso: {total_peso_kg:,.1f} KG")
        
        with col_actions3:
            # Selector para eliminar producto específico
            if st.session_state.productos:
                producto_a_eliminar = st.selectbox(
                    "Seleccionar producto a eliminar:",
                    options=[f"{i+1}. {p.nombre}" for i, p in enumerate(st.session_state.productos)],
                    key="eliminar_select"
                )
                if st.button("❌ Eliminar Seleccionado", use_container_width=True):
                    if producto_a_eliminar:
                        indice = int(producto_a_eliminar.split('.')[0]) - 1
                        producto_eliminado = st.session_state.productos.pop(indice)
                        st.success(f"Producto '{producto_eliminado.nombre}' eliminado")
                        st.rerun()
    
    else:
        st.info("No hay productos agregados. Usa el formulario arriba para agregar productos.")

def main():
    st.markdown('<h1 class="main-header">📦 Calculadora de Importaciones Colombia - China</h1>', unsafe_allow_html=True)
    
    # Inicializar calculadora
    calc = CalculadoraImportaciones()
    
    # Sidebar para información general
    with st.sidebar:
        st.header("ℹ️ Información General")
        st.info(f"Tasa de cambio actual: **1 USD = ${calc.tasa_cambio:,.0f} COP**")
        
        st.header("⚙️ Configuración")
        tasa_personalizada = st.number_input(
            "Tasa de cambio USD/COP (opcional)",
            min_value=1000.0,
            max_value=10000.0,
            value=float(calc.tasa_cambio),
            step=10.0
        )
        calc.tasa_cambio = tasa_personalizada
        
        tasa_arancel_personalizada = st.slider(
            "Tasa de arancel (DAI) %",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.5
        ) / 100
        
        st.markdown("---")
        st.markdown("### 💡 Tips de Importación")
        st.markdown("""
        - Verifica el arancel específico de tu producto
        - Considera tiempos de tránsito (30-45 días)
        - Ten documentación completa
        - Consulta con agente aduanal
        - Considera seguros adicionales
        """)
    
    # Pestañas para organizar la funcionalidad
    tab1, tab2, tab3 = st.tabs(["📊 Calculadora Principal", "📦 Gestión de Productos", "📈 Reportes"])
    
    with tab1:
        # Gestión de productos integrada en la pestaña principal
        gestionar_productos()
        
        st.markdown("---")
        st.markdown('<div class="sub-header">🚚 Datos de Envío y Cálculos</div>', unsafe_allow_html=True)
        
        # Calcular totales de productos
        total_valor_productos_usd = sum(p.precio_total_usd for p in st.session_state.productos) if st.session_state.productos else 0
        total_peso_kg = sum(p.peso_total_kg for p in st.session_state.productos) if st.session_state.productos else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mostrar resumen de productos si existen
            if st.session_state.productos:
                st.metric("Valor total productos", f"${total_valor_productos_usd:,.2f} USD")
                st.metric("Peso total productos", f"{total_peso_kg:,.1f} KG")
            else:
                st.info("Agrega productos en la sección de arriba")
            
            # Entradas adicionales de envío
            flete_internacional_usd = st.number_input(
                "Flete internacional (USD)",
                min_value=0.0,
                max_value=50000.0,
                value=500.0,
                step=50.0
            )
            
            seguro_usd = st.number_input(
                "Seguro (USD)",
                min_value=0.0,
                max_value=10000.0,
                value=max(50.0, total_valor_productos_usd * 0.01),
                step=10.0
            )
        
        with col2:
            # Resumen rápido
            valor_producto_usd = total_valor_productos_usd
            if valor_producto_usd > 0:
                valor_producto_cop = valor_producto_usd * calc.tasa_cambio
                flete_internacional_cop = flete_internacional_usd * calc.tasa_cambio
                seguro_cop = seguro_usd * calc.tasa_cambio
                
                st.metric("Valor mercancía", 
                         calc.formato_moneda(valor_producto_cop),
                         f"{valor_producto_usd:,.0f} USD")
                
                st.metric("Costo logística",
                         calc.formato_moneda(flete_internacional_cop + seguro_cop),
                         f"{flete_internacional_usd + seguro_usd:,.0f} USD")
        
        # Cálculos principales
        if valor_producto_usd > 0:
            # Conversión a COP
            valor_producto_cop = valor_producto_usd * calc.tasa_cambio
            flete_internacional_cop = flete_internacional_usd * calc.tasa_cambio
            seguro_cop = seguro_usd * calc.tasa_cambio
            
            # Cálculos
            cif_cop = calc.calcular_cif(valor_producto_cop, flete_internacional_cop, seguro_cop)
            dai_cop = calc.calcular_dai(cif_cop, tasa_arancel_personalizada)
            iva_cop = calc.calcular_iva(cif_cop, dai_cop)
            anticipo_iva_cop = calc.calcular_anticipo_iva(iva_cop)
            gastos_varios = calc.calcular_gastos_varios(cif_cop, total_peso_kg)
            
            costo_total_cop = cif_cop + dai_cop + iva_cop + gastos_varios['total']
            costo_total_usd = calc.convertir_a_usd(costo_total_cop)
            
            # Mostrar resultados detallados
            st.markdown("---")
            st.markdown('<div class="sub-header">💰 Desglose de Costos</div>', unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### Costos Internacionales")
                st.markdown(f'<div class="cost-box">Valor CIF (Mercancía + Flete + Seguro):<br><strong>{calc.formato_moneda(cif_cop)}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(cif_cop), "USD")}</div></div>', unsafe_allow_html=True)
                
                st.markdown("#### Impuestos y Aranceles")
                st.markdown(f'<div class="cost-box">DAI (Arancel {tasa_arancel_personalizada*100:.1f}%):<br><strong>{calc.formato_moneda(dai_cop)}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(dai_cop), "USD")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cost-box">IVA (19%):<br><strong>{calc.formato_moneda(iva_cop)}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(iva_cop), "USD")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cost-box">Anticipo de IVA (10%):<br><strong>{calc.formato_moneda(anticipo_iva_cop)}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(anticipo_iva_cop), "USD")}</div></div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown("#### Gastos Nacionales")
                st.markdown(f'<div class="cost-box">Agencia Aduanal:<br><strong>{calc.formato_moneda(gastos_varios["agencia_aduanal"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos_varios["agencia_aduanal"]), "USD")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cost-box">Almacenamiento:<br><strong>{calc.formato_moneda(gastos_varios["almacenamiento"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos_varios["almacenamiento"]), "USD")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cost-box">Transporte Interno:<br><strong>{calc.formato_moneda(gastos_varios["transporte_interno"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos_varios["transporte_interno"]), "USD")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="cost-box">Otros Gastos:<br><strong>{calc.formato_moneda(gastos_varios["otros_gastos"])}</strong><div class="usd-text">{calc.formato_moneda(calc.convertir_a_usd(gastos_varios["otros_gastos"]), "USD")}</div></div>', unsafe_allow_html=True)
            
            # Total final
            st.markdown(f'<div class="total-box">TOTAL ESTIMADO DE IMPORTACIÓN:<br>{calc.formato_moneda(costo_total_cop)}<br><div style="font-size: 1.2rem;">{calc.formato_moneda(costo_total_usd, "USD")}</div></div>', unsafe_allow_html=True)
    
    with tab2:
        # Pestaña dedicada solo a gestión de productos
        gestionar_productos()
    
    with tab3:
        # Pestaña de reportes
        st.markdown('<div class="sub-header">📈 Reportes y Análisis</div>', unsafe_allow_html=True)
        
        if st.session_state.productos and 'costo_total_cop' in locals():
            col_rep1, col_rep2, col_rep3 = st.columns(3)
            
            with col_rep1:
                costo_por_kg = costo_total_cop / total_peso_kg if total_peso_kg > 0 else 0
                st.metric("Costo por KG", calc.formato_moneda(costo_por_kg))
            
            with col_rep2:
                incremento_por_impuestos = ((dai_cop + iva_cop) / cif_cop) * 100
                st.metric("Incremento por impuestos", f"{incremento_por_impuestos:.1f}%")
            
            with col_rep3:
                relacion_costo_impuestos = (costo_total_cop - cif_cop) / cif_cop * 100
                st.metric("Costos adicionales vs CIF", f"{relacion_costo_impuestos:.1f}%")
            
            # Gráfico de distribución de costos
            st.markdown("---")
            st.subheader("Distribución de Costos")
            
            datos_distribucion = {
                'Concepto': ['Mercancía', 'Flete y Seguro', 'DAI', 'IVA', 'Gastos Varios'],
                'Valor COP': [
                    valor_producto_cop,
                    flete_internacional_cop + seguro_cop,
                    dai_cop,
                    iva_cop,
                    gastos_varios['total']
                ]
            }
            
            df_distribucion = pd.DataFrame(datos_distribucion)
            df_distribucion['Porcentaje'] = (df_distribucion['Valor COP'] / costo_total_cop) * 100
            
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
                    valor_producto_cop,
                    flete_internacional_cop,
                    seguro_cop,
                    cif_cop,
                    dai_cop,
                    iva_cop,
                    anticipo_iva_cop,
                    gastos_varios['total'],
                    costo_total_cop
                ],
                'USD': [
                    valor_producto_usd,
                    flete_internacional_usd,
                    seguro_usd,
                    calc.convertir_a_usd(cif_cop),
                    calc.convertir_a_usd(dai_cop),
                    calc.convertir_a_usd(iva_cop),
                    calc.convertir_a_usd(anticipo_iva_cop),
                    calc.convertir_a_usd(gastos_varios['total']),
                    costo_total_usd
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

if __name__ == "__main__":
    main()
