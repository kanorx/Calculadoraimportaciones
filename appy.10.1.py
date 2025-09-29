# app.py - VERSIÓN CORREGIDA SIN PARÁMETRO KEY EN METRIC
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import io
import base64

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Importaciones Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CalculadoraImportacionesStreamlit:
    def __init__(self):
        self.inicializar_datos()
        
    def inicializar_datos(self):
        """Inicializar datos en session_state si no existen"""
        if 'parametros' not in st.session_state:
            st.session_state.parametros = {
                'USD_COP': 3800.0,
                'CNY_USD': 0.14,
                'flete_internacional': 2500.0,
                'seguro_porcentaje': 0.02,
                'iva_importacion': 0.19,
                'despacho_aduana': 850000.0,
                'transporte_interno': 1200000.0,
                'almacenaje': 500000.0,
                'margen_objetivo': 0.35,
                'costo_packaging': 2500.0,
                'costo_envio_local': 12000.0,
                'comision_ml_electronicos': 0.12,
                'comision_ml_hogar': 0.14,
                'comision_ml_moda': 0.16,
                'porcentaje_perdidas': 0.02
            }
        
        if 'productos' not in st.session_state:
            st.session_state.productos = pd.DataFrame({
                'sku': ['AUD-001', 'CAM-002', 'CAR-003'],
                'descripcion': ['Auriculares Bluetooth', 'Cámara Seguridad IP', 'Cargador Rápido USB-C'],
                'cantidad': [500, 200, 1000],
                'peso_unitario_kg': [0.2, 0.8, 0.1],
                'volumen_unitario_m3': [0.001, 0.005, 0.0005],
                'precio_unitario_usd': [8.5, 22.0, 3.2],
                'hs_code': ['8518.30.00', '8525.80.19', '8504.40.40'],
                'incoterm': ['FOB', 'FOB', 'FOB'],
                'categoria': ['Electrónicos', 'Electrónicos', 'Electrónicos']
            })
        
        if 'aranceles' not in st.session_state:
            st.session_state.aranceles = pd.DataFrame({
                'hs_code': ['8518.30.00', '8525.80.19', '8504.40.40'],
                'descripcion': ['Auriculares, audífonos', 'Cámaras de televisión', 'Cargadores eléctricos'],
                'arancel_porcentaje': [0.05, 0.08, 0.06],
                'iva_porcentaje': [0.19, 0.19, 0.19],
                'otros_impuestos': [0.0, 0.0, 0.0],
                'fuente': ['DIAN', 'DIAN', 'DIAN'],
                'fecha_actualizacion': [datetime.now().date()] * 3
            })
        
        if 'landed_cost' not in st.session_state:
            st.session_state.landed_cost = pd.DataFrame()
            
        if 'ventas' not in st.session_state:
            st.session_state.ventas = pd.DataFrame()
            
        if 'escenarios' not in st.session_state:
            st.session_state.escenarios = pd.DataFrame()
            
        if 'calculos_realizados' not in st.session_state:
            st.session_state.calculos_realizados = False

    def ejecutar_aplicacion(self):
        """Ejecutar la aplicación principal"""
        # Sidebar
        self.crear_sidebar()
        
        # Contenido principal basado en la selección
        pagina = st.session_state.get('pagina_seleccionada', '🏠 Inicio')
        
        if pagina == '🏠 Inicio':
            self.pagina_inicio()
        elif pagina == '⚙️ Parámetros':
            self.pagina_parametros()
        elif pagina == '📦 Productos':
            self.pagina_productos()
        elif pagina == '📊 Aranceles':
            self.pagina_aranceles()
        elif pagina == '💰 Landed Cost':
            self.pagina_landed_cost()
        elif pagina == '🛍️ Ventas':
            self.pagina_ventas()
        elif pagina == '📈 Escenarios':
            self.pagina_escenarios()
        elif pagina == '🎯 Dashboard':
            self.pagina_dashboard()
        elif pagina == '💾 Exportar':
            self.pagina_exportar()

    def crear_sidebar(self):
        """Crear la barra lateral de navegación"""
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3063/3063155.png", width=80)
            st.title("🚀 Calculadora Pro")
            st.markdown("---")
            
            # Navegación - Usando índice único para evitar claves duplicadas
            opciones = [
                '🏠 Inicio',
                '⚙️ Parámetros', 
                '📦 Productos',
                '📊 Aranceles',
                '💰 Landed Cost',
                '🛍️ Ventas',
                '📈 Escenarios', 
                '🎯 Dashboard',
                '💾 Exportar'
            ]
            
            # Usar una clave única para el selectbox
            seleccion = st.selectbox(
                "Navegación",
                opciones,
                key='sidebar_navegacion'  # Clave única
            )
            
            # Actualizar la página seleccionada
            st.session_state.pagina_seleccionada = seleccion
            
            st.markdown("---")
            
            # Estado del sistema
            st.subheader("📊 Estado Actual")
            total_skus = len(st.session_state.productos)
            total_unidades = st.session_state.productos['cantidad'].sum() if not st.session_state.productos.empty else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("SKUs", total_skus)
            with col2:
                st.metric("Unidades", f"{total_unidades:,}")
            
            if not st.session_state.ventas.empty:
                rent_promedio = st.session_state.ventas['rentabilidad'].mean()
                st.metric("Rentabilidad", f"{rent_promedio:.1%}")
            
            # Botón de recálculo
            if st.button("🔄 Recalcular Todo", use_container_width=True, type="primary", key="btn_recalcular_sidebar"):
                self.recalcular_todo()
                st.success("¡Sistema actualizado!")
            
            st.markdown("---")
            st.caption(f"© 2024 • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    def pagina_inicio(self):
        """Página de inicio"""
        st.title("🚀 Calculadora de Importaciones Pro")
        st.subheader("Herramienta profesional para importar desde China y fijar precios")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_skus = len(st.session_state.productos)
            st.metric("📦 SKUs Registrados", total_skus)
            
        with col2:
            total_unidades = st.session_state.productos['cantidad'].sum() if not st.session_state.productos.empty else 0
            st.metric("🔄 Unidades Totales", f"{total_unidades:,}")
            
        with col3:
            if not st.session_state.productos.empty:
                inversion_total = (st.session_state.productos['cantidad'] * st.session_state.productos['precio_unitario_usd']).sum()
                st.metric("💰 Inversión Total", f"${inversion_total:,.0f} USD")
            else:
                st.metric("💰 Inversión Total", "$0 USD")
            
        with col4:
            if not st.session_state.ventas.empty:
                rent_promedio = st.session_state.ventas['rentabilidad'].mean()
                st.metric("📈 Rentabilidad Promedio", f"{rent_promedio:.1%}")
            else:
                st.metric("📈 Rentabilidad", "Por calcular")
        
        # Layout principal
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            # Progreso del sistema
            st.subheader("🎯 Progreso del Análisis")
            
            progreso = self.calcular_progreso()
            st.progress(progreso / 100, text=f"Completado: {progreso}%")
            
            # Pasos para completar
            pasos = [
                ("⚙️ Configurar parámetros", st.session_state.parametros['USD_COP'] > 0),
                ("📦 Agregar productos", len(st.session_state.productos) > 0),
                ("📊 Configurar aranceles", len(st.session_state.aranceles) > 0),
                ("💰 Calcular Landed Cost", not st.session_state.landed_cost.empty),
                ("🛍️ Calcular ventas", not st.session_state.ventas.empty),
                ("📈 Analizar escenarios", not st.session_state.escenarios.empty)
            ]
            
            for paso, completado in pasos:
                icono = "✅" if completado else "⏳"
                st.write(f"{icono} {paso}")
            
            # Gráfico rápido si hay datos
            if not st.session_state.ventas.empty:
                st.subheader("📊 Vista Rápida - Rentabilidad")
                fig = px.bar(
                    st.session_state.ventas.nlargest(5, 'rentabilidad'),
                    x='sku',
                    y='rentabilidad',
                    title='Top 5 Productos Más Rentables',
                    color='rentabilidad',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_side:
            # Acciones rápidas
            st.subheader("🚀 Acciones Rápidas")
            
            if st.button("📊 Calcular Todo Automáticamente", use_container_width=True, key="btn_calcular_todo"):
                with st.spinner("Calculando todos los módulos..."):
                    self.recalcular_todo()
                st.success("¡Análisis completo!")
            
            if st.button("🆕 Reiniciar Datos", use_container_width=True, key="btn_reiniciar"):
                if st.button("⚠️ Confirmar Reinicio", type="secondary", key="btn_confirmar_reinicio"):
                    self.inicializar_datos()
                    st.success("¡Datos reiniciados!")
                    st.rerun()
            
            # Consejos rápidos
            st.subheader("💡 Consejos")
            st.info("""
            **Para mejores resultados:**
            - Actualiza tipos de cambio regularmente
            - Verifica aranceles con la DIAN
            - Considera 2-5% para pérdidas/roturas
            - Revisa comisiones por categoría en ML
            """)
            
            # Nota legal
            st.warning("""
            **⚠️ Importante:**
            Esta herramienta provee estimaciones.
            Verifique tasas actuales con su agente aduanero.
            """)

    def calcular_progreso(self):
        """Calcular progreso general del análisis"""
        pasos = 6
        completados = 0
        
        if st.session_state.parametros['USD_COP'] > 0:
            completados += 1
        if len(st.session_state.productos) > 0:
            completados += 1
        if len(st.session_state.aranceles) > 0:
            completados += 1
        if not st.session_state.landed_cost.empty:
            completados += 1
        if not st.session_state.ventas.empty:
            completados += 1
        if not st.session_state.escenarios.empty:
            completados += 1
            
        return int((completados / pasos) * 100)

    def pagina_parametros(self):
        """Página de parámetros globales - VERSIÓN CORREGIDA"""
        st.header("⚙️ Parámetros Globales")
        st.markdown("Configura los parámetros base para todos los cálculos")
        
        # Pestañas para organizar parámetros
        tab1, tab2, tab3, tab4 = st.tabs(["💱 Moneda y Logística", "🏛️ Impuestos", "🛍️ Ventas", "📋 Resumen"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💱 Tipos de Cambio")
                st.session_state.parametros['USD_COP'] = st.number_input(
                    "USD → COP",
                    value=float(st.session_state.parametros['USD_COP']),
                    min_value=1000.0,
                    max_value=10000.0,
                    step=100.0,
                    help="Tipo de cambio actual USD a COP",
                    key="usd_cop_input"
                )
                
                st.session_state.parametros['CNY_USD'] = st.number_input(
                    "CNY → USD", 
                    value=st.session_state.parametros['CNY_USD'],
                    min_value=0.01,
                    max_value=1.0,
                    step=0.01,
                    format="%.4f",
                    help="Tipo de cambio CNY a USD",
                    key="cny_usd_input"
                )
            
            with col2:
                st.subheader("🚢 Logística Internacional")
                st.session_state.parametros['flete_internacional'] = st.number_input(
                    "Flete Internacional (USD)",
                    value=float(st.session_state.parametros['flete_internacional']),
                    min_value=0.0,
                    step=100.0,
                    help="Costo del flete marítimo o aéreo",
                    key="flete_input"
                )
                
                st.session_state.parametros['seguro_porcentaje'] = st.number_input(
                    "Seguro (% sobre valor)",
                    value=st.session_state.parametros['seguro_porcentaje'],
                    min_value=0.0,
                    max_value=0.1,
                    step=0.005,
                    format="%.3f",
                    help="Seguro sobre el valor de la mercancía (típico 1-3%)",
                    key="seguro_input"
                )
                
                st.session_state.parametros['porcentaje_perdidas'] = st.number_input(
                    "Pérdidas/Roturas (%)",
                    value=st.session_state.parametros['porcentaje_perdidas'],
                    min_value=0.0,
                    max_value=0.2,
                    step=0.01,
                    format="%.3f",
                    help="Porcentaje estimado por pérdidas en transporte (1-5%)",
                    key="perdidas_input"
                )
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏛️ Impuestos de Importación")
                st.session_state.parametros['iva_importacion'] = st.number_input(
                    "IVA Importación (%)",
                    value=st.session_state.parametros['iva_importacion'],
                    min_value=0.0,
                    max_value=0.5,
                    step=0.01,
                    format="%.3f",
                    help="IVA aplicable a la importación (19% en Colombia)",
                    key="iva_input"
                )
            
            with col2:
                st.subheader("🇨🇴 Costos Nacionales (COP)")
                st.session_state.parametros['despacho_aduana'] = st.number_input(
                    "Despacho Aduanero",
                    value=float(st.session_state.parametros['despacho_aduana']),
                    min_value=0.0,
                    step=10000.0,
                    help="Costo de agente aduanero y trámites",
                    key="despacho_input"
                )
                
                st.session_state.parametros['transporte_interno'] = st.number_input(
                    "Transporte Interno",
                    value=float(st.session_state.parametros['transporte_interno']),
                    min_value=0.0,
                    step=10000.0,
                    help="Transporte desde puerto a bodega",
                    key="transporte_input"
                )
                
                st.session_state.parametros['almacenaje'] = st.number_input(
                    "Almacenaje",
                    value=float(st.session_state.parametros['almacenaje']),
                    min_value=0.0,
                    step=10000.0,
                    help="Costo de almacenamiento mensual",
                    key="almacenaje_input"
                )
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Objetivos de Venta")
                st.session_state.parametros['margen_objetivo'] = st.number_input(
                    "Margen Objetivo (%)",
                    value=st.session_state.parametros['margen_objetivo'],
                    min_value=0.0,
                    max_value=1.0,
                    step=0.05,
                    format="%.3f",
                    help="Margen de ganancia deseado después de todos los costos",
                    key="margen_input"
                )
                
                st.session_state.parametros['costo_packaging'] = st.number_input(
                    "Packaging por unidad (COP)",
                    value=float(st.session_state.parametros['costo_packaging']),
                    min_value=0.0,
                    step=500.0,
                    help="Costo de empaque por producto",
                    key="packaging_input"
                )
                
                st.session_state.parametros['costo_envio_local'] = st.number_input(
                    "Envío Local (COP)",
                    value=float(st.session_state.parametros['costo_envio_local']),
                    min_value=0.0,
                    step=1000.0,
                    help="Costo de envío al cliente final",
                    key="envio_input"
                )
            
            with col2:
                st.subheader("📊 Comisiones Mercado Libre")
                st.session_state.parametros['comision_ml_electronicos'] = st.number_input(
                    "Electrónicos (%)",
                    value=st.session_state.parametros['comision_ml_electronicos'],
                    min_value=0.0,
                    max_value=0.3,
                    step=0.01,
                    format="%.3f",
                    help="Comisión para categoría Electrónicos (12-16%)",
                    key="comision_electronicos_input"
                )
                
                st.session_state.parametros['comision_ml_hogar'] = st.number_input(
                    "Hogar (%)",
                    value=st.session_state.parametros['comision_ml_hogar'],
                    min_value=0.0,
                    max_value=0.3,
                    step=0.01,
                    format="%.3f",
                    help="Comisión para categoría Hogar (14-18%)",
                    key="comision_hogar_input"
                )
                
                st.session_state.parametros['comision_ml_moda'] = st.number_input(
                    "Moda (%)",
                    value=st.session_state.parametros['comision_ml_moda'],
                    min_value=0.0,
                    max_value=0.3,
                    step=0.01,
                    format="%.3f",
                    help="Comisión para categoría Moda (16-20%)",
                    key="comision_moda_input"
                )
        
        with tab4:
            self.mostrar_resumen_parametros()
        
        # Botones de acción
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("💾 Guardar Parámetros", use_container_width=True, type="primary", key="btn_guardar_parametros"):
                st.success("✅ Parámetros guardados correctamente")
                st.session_state.calculos_realizados = False
        
        with col_btn2:
            if st.button("🔄 Recalcular Todo", use_container_width=True, key="btn_recalcular_parametros"):
                self.recalcular_todo()
                st.success("✅ Todos los cálculos actualizados")
        
        with col_btn3:
            if st.button("📊 Validar Parámetros", use_container_width=True, key="btn_validar_parametros"):
                self.validar_parametros()

    def mostrar_resumen_parametros(self):
        """Mostrar resumen de parámetros"""
        st.subheader("📋 Resumen de Parámetros Actuales")
        
        # Crear DataFrame para mostrar
        parametros_display = []
        categorias = {
            '💱 Tipos de Cambio': ['USD_COP', 'CNY_USD'],
            '🚢 Logística': ['flete_internacional', 'seguro_porcentaje', 'porcentaje_perdidas'],
            '🏛️ Impuestos': ['iva_importacion'],
            '🇨🇴 Costos Nacionales': ['despacho_aduana', 'transporte_interno', 'almacenaje'],
            '🎯 Ventas': ['margen_objetivo', 'costo_packaging', 'costo_envio_local'],
            '📊 Comisiones ML': ['comision_ml_electronicos', 'comision_ml_hogar', 'comision_ml_moda']
        }
        
        for categoria, params in categorias.items():
            for param in params:
                valor = st.session_state.parametros[param]
                if param.endswith('_porcentaje') or param in ['margen_objetivo', 'iva_importacion']:
                    valor_formateado = f"{valor:.1%}"
                elif valor >= 1000:
                    valor_formateado = f"{valor:,.0f}"
                else:
                    valor_formateado = f"{valor:.2f}"
                
                parametros_display.append({
                    'Categoría': categoria,
                    'Parámetro': param.replace('_', ' ').title(),
                    'Valor': valor_formateado
                })
        
        df_resumen = pd.DataFrame(parametros_display)
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)

    def validar_parametros(self):
        """Validar que los parámetros sean razonables"""
        errores = []
        advertencias = []
        
        params = st.session_state.parametros
        
        # Validaciones críticas
        if params['USD_COP'] <= 1000:
            errores.append("Tipo de cambio USD muy bajo")
        if params['margen_objetivo'] < 0.1:
            advertencias.append("Margen objetivo muy bajo (<10%)")
        if params['seguro_porcentaje'] > 0.05:
            advertencias.append("Seguro muy alto (>5%)")
        
        if errores:
            st.error("❌ **Errores encontrados:**\n" + "\n".join(f"• {e}" for e in errores))
        if advertencias:
            st.warning("⚠️ **Advertencias:**\n" + "\n".join(f"• {e}" for e in advertencias))
        if not errores and not advertencias:
            st.success("✅ Todos los parámetros están dentro de rangos razonables")

    def pagina_productos(self):
        """Página de gestión de productos"""
        st.header("📦 Gestión de Productos")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Editor de datos principal
            st.subheader("📋 Lista de Productos")
            
            # Calcular totales automáticamente
            productos_con_totales = st.session_state.productos.copy()
            if not productos_con_totales.empty:
                productos_con_totales['Total FOB USD'] = productos_con_totales['cantidad'] * productos_con_totales['precio_unitario_usd']
                productos_con_totales['Peso Total kg'] = productos_con_totales['cantidad'] * productos_con_totales['peso_unitario_kg']
                productos_con_totales['Volumen Total m³'] = productos_con_totales['cantidad'] * productos_con_totales['volumen_unitario_m3']
            
            edited_df = st.data_editor(
                productos_con_totales,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "sku": st.column_config.TextColumn("SKU", width="small", required=True),
                    "descripcion": st.column_config.TextColumn("Descripción", width="medium", required=True),
                    "cantidad": st.column_config.NumberColumn("Cantidad", format="%d", min_value=1, required=True),
                    "peso_unitario_kg": st.column_config.NumberColumn("Peso (kg)", format="%.3f", min_value=0.0),
                    "volumen_unitario_m3": st.column_config.NumberColumn("Volumen (m³)", format="%.4f", min_value=0.0),
                    "precio_unitario_usd": st.column_config.NumberColumn("Precio USD", format="%.2f", min_value=0.0, required=True),
                    "hs_code": st.column_config.TextColumn("HS Code", required=True),
                    "incoterm": st.column_config.SelectboxColumn(
                        "Incoterm",
                        options=["FOB", "CIF", "DDP"],
                        required=True
                    ),
                    "categoria": st.column_config.SelectboxColumn(
                        "Categoría",
                        options=["Electrónicos", "Hogar", "Moda", "Deportes", "Otros"],
                        required=True
                    ),
                    "Total FOB USD": st.column_config.NumberColumn("Total FOB USD", format="%.2f", disabled=True),
                    "Peso Total kg": st.column_config.NumberColumn("Peso Total kg", format="%.1f", disabled=True),
                    "Volumen Total m³": st.column_config.NumberColumn("Volumen Total m³", format="%.3f", disabled=True)
                },
                key="productos_editor"
            )
            
            # Remover columnas calculadas antes de guardar
            if 'Total FOB USD' in edited_df.columns:
                edited_df = edited_df.drop(['Total FOB USD', 'Peso Total kg', 'Volumen Total m³'], axis=1)
            
            if st.button("💾 Guardar Cambios en Productos", use_container_width=True, type="primary", key="btn_guardar_productos"):
                st.session_state.productos = edited_df
                st.session_state.calculos_realizados = False
                st.success("✅ Productos actualizados correctamente")
                st.rerun()

        with col2:
            st.subheader("🚀 Acciones Rápidas")
            
            # Formulario para nuevo producto rápido
            with st.form("nuevo_producto_rapido"):
                st.write("➕ Agregar Producto Rápido")
                nuevo_sku = st.text_input("SKU*", value=f"SKU_{datetime.now().strftime('%y%m%d%H%M')}", key="nuevo_sku")
                nueva_desc = st.text_input("Descripción*", key="nueva_desc")
                nueva_cant = st.number_input("Cantidad*", min_value=1, value=100, key="nueva_cant")
                nuevo_precio = st.number_input("Precio USD*", min_value=0.0, value=10.0, step=0.1, key="nuevo_precio")
                nueva_categoria = st.selectbox("Categoría*", ["Electrónicos", "Hogar", "Moda", "Deportes", "Otros"], key="nueva_categoria")
                
                if st.form_submit_button("🎯 Agregar Producto", use_container_width=True):
                    if nuevo_sku and nueva_desc:
                        nuevo_producto = {
                            'sku': nuevo_sku,
                            'descripcion': nueva_desc,
                            'cantidad': nueva_cant,
                            'peso_unitario_kg': 0.1,
                            'volumen_unitario_m3': 0.001,
                            'precio_unitario_usd': nuevo_precio,
                            'hs_code': '',
                            'incoterm': 'FOB',
                            'categoria': nueva_categoria
                        }
                        
                        st.session_state.productos = pd.concat([
                            st.session_state.productos,
                            pd.DataFrame([nuevo_producto])
                        ], ignore_index=True)
                        
                        st.success(f"✅ Producto {nuevo_sku} agregado")
                        st.session_state.calculos_realizados = False
                        st.rerun()
                    else:
                        st.error("❌ SKU y Descripción son obligatorios")
            
            # Eliminar productos
            st.subheader("🗑️ Eliminar Productos")
            if not st.session_state.productos.empty:
                sku_a_eliminar = st.selectbox(
                    "Seleccione SKU a eliminar:",
                    options=st.session_state.productos['sku'].tolist(),
                    key="eliminar_sku_select"
                )
                
                if st.button("❌ Eliminar SKU Seleccionado", use_container_width=True, key="btn_eliminar_sku"):
                    st.session_state.productos = st.session_state.productos[
                        st.session_state.productos['sku'] != sku_a_eliminar
                    ]
                    st.success(f"✅ SKU {sku_a_eliminar} eliminado")
                    st.session_state.calculos_realizados = False
                    st.rerun()
            
            # Estadísticas
            st.subheader("📊 Estadísticas")
            if not st.session_state.productos.empty:
                total_skus = len(st.session_state.productos)
                total_unidades = st.session_state.productos['cantidad'].sum()
                inversion_total = (st.session_state.productos['cantidad'] * st.session_state.productos['precio_unitario_usd']).sum()
                peso_total = (st.session_state.productos['cantidad'] * st.session_state.productos['peso_unitario_kg']).sum()
                
                st.metric("Total SKUs", total_skus)
                st.metric("Total Unidades", f"{total_unidades:,}")
                st.metric("Inversión Total", f"${inversion_total:,.0f} USD")
                st.metric("Peso Total", f"{peso_total:,.1f} kg")
            else:
                st.info("No hay productos registrados")

    def pagina_aranceles(self):
        """Página de gestión de aranceles"""
        st.header("📊 Gestión de Aranceles e Impuestos")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🏛️ Tabla de Aranceles por HS Code")
            
            edited_df = st.data_editor(
                st.session_state.aranceles,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "hs_code": st.column_config.TextColumn("HS Code", required=True),
                    "descripcion": st.column_config.TextColumn("Descripción", width="large", required=True),
                    "arancel_porcentaje": st.column_config.NumberColumn("Arancel %", format="%.1%", min_value=0.0, max_value=1.0, step=0.01),
                    "iva_porcentaje": st.column_config.NumberColumn("IVA %", format="%.1%", min_value=0.0, max_value=1.0, step=0.01),
                    "otros_impuestos": st.column_config.NumberColumn("Otros %", format="%.1%", min_value=0.0, max_value=1.0, step=0.01),
                    "fuente": st.column_config.TextColumn("Fuente"),
                    "fecha_actualizacion": st.column_config.DateColumn("Fecha Actualización")
                },
                key="aranceles_editor"
            )
            
            if st.button("💾 Guardar Cambios en Aranceles", use_container_width=True, type="primary", key="btn_guardar_aranceles"):
                st.session_state.aranceles = edited_df
                st.session_state.calculos_realizados = False
                st.success("✅ Aranceles actualizados correctamente")
                st.rerun()

        with col2:
            st.subheader("📥 Agregar HS Code")
            with st.form("nuevo_hs_code"):
                hs_code = st.text_input("HS Code*", placeholder="ej. 8518.30.00", key="nuevo_hs_code")
                descripcion = st.text_input("Descripción*", placeholder="ej. Auriculares, audífonos", key="nueva_desc_hs")
                arancel = st.number_input("Arancel %*", min_value=0.0, max_value=1.0, value=0.05, step=0.01, format="%.3f", key="nuevo_arancel")
                iva = st.number_input("IVA %*", min_value=0.0, max_value=1.0, value=0.19, step=0.01, format="%.3f", key="nuevo_iva")
                otros = st.number_input("Otros Impuestos %", min_value=0.0, max_value=1.0, value=0.0, step=0.01, format="%.3f", key="nuevos_otros")
                fuente = st.text_input("Fuente", value="DIAN", key="nueva_fuente")
                
                if st.form_submit_button("➕ Agregar HS Code", use_container_width=True, key="btn_agregar_hs"):
                    if hs_code and descripcion:
                        nuevo_arancel = {
                            'hs_code': hs_code,
                            'descripcion': descripcion,
                            'arancel_porcentaje': arancel,
                            'iva_porcentaje': iva,
                            'otros_impuestos': otros,
                            'fuente': fuente,
                            'fecha_actualizacion': datetime.now().date()
                        }
                        
                        st.session_state.aranceles = pd.concat([
                            st.session_state.aranceles,
                            pd.DataFrame([nuevo_arancel])
                        ], ignore_index=True)
                        
                        st.success(f"✅ HS Code {hs_code} agregado")
                        st.session_state.calculos_realizados = False
                        st.rerun()
                    else:
                        st.error("❌ HS Code y Descripción son obligatorios")
            
            # Estadísticas de aranceles
            st.subheader("📈 Resumen Aranceles")
            if not st.session_state.aranceles.empty:
                avg_arancel = st.session_state.aranceles['arancel_porcentaje'].mean()
                max_arancel = st.session_state.aranceles['arancel_porcentaje'].max()
                min_arancel = st.session_state.aranceles['arancel_porcentaje'].min()
                
                st.metric("Arancel Promedio", f"{avg_arancel:.1%}")
                st.metric("Arancel Máximo", f"{max_arancel:.1%}")
                st.metric("Arancel Mínimo", f"{min_arancel:.1%}")
            
            st.info("💡 **Fuentes recomendadas:**\n- DIAN Colombia\n- Trademap\n- Tariff Download")

    def pagina_landed_cost(self):
        """Página de cálculo de Landed Cost"""
        st.header("💰 Cálculo de Landed Cost")
        
        # Verificar prerequisitos
        if st.session_state.productos.empty:
            st.error("❌ Primero agregue productos en la pestaña '📦 Productos'")
            return
        
        if st.session_state.aranceles.empty:
            st.error("❌ Primero configure aranceles en la pestaña '📊 Aranceles'")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Botón de cálculo
            if st.button("🧮 Calcular Landed Cost", type="primary", use_container_width=True, key="btn_calcular_landed"):
                with st.spinner("Calculando costos de importación..."):
                    self.calcular_landed_cost()
            
            # Mostrar resultados
            if not st.session_state.landed_cost.empty:
                st.subheader("📊 Resultados Landed Cost")
                
                # Tabla con formato mejorado
                df_display = st.session_state.landed_cost.copy()
                st.dataframe(
                    df_display.style.format({
                        'cif_usd': '${:,.2f}',
                        'cif_cop': '${:,.0f}',
                        'arancel_cop': '${:,.0f}',
                        'iva_cop': '${:,.0f}',
                        'costos_nacionales': '${:,.0f}',
                        'costo_total': '${:,.0f}',
                        'costo_unitario': '${:,.0f}'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                # Gráficos
                tab1, tab2 = st.tabs(["📈 Composición de Costos", "📊 Comparación por SKU"])
                
                with tab1:
                    fig_composicion = px.bar(
                        st.session_state.landed_cost,
                        x='sku',
                        y=['cif_cop', 'arancel_cop', 'iva_cop', 'costos_nacionales'],
                        title='Composición del Costo Landed por SKU',
                        labels={'value': 'COP', 'variable': 'Componente', 'sku': 'SKU'},
                        barmode='stack',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_composicion, use_container_width=True)
                
                with tab2:
                    fig_comparacion = px.bar(
                        st.session_state.landed_cost,
                        x='sku',
                        y='costo_unitario',
                        title='Costo Unitario Landed por SKU',
                        labels={'costo_unitario': 'COP', 'sku': 'SKU'},
                        color='costo_unitario',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_comparacion, use_container_width=True)
                
            else:
                st.info("👆 Haz clic en 'Calcular Landed Cost' para ver los resultados")

        with col2:
            st.subheader("ℹ️ Información del Cálculo")
            st.write("""
            **🧮 Fórmulas aplicadas:**
            
            **Valor FOB USD** = Cantidad × Precio Unitario
            **Flete Proporcional** = (Valor FOB / Total FOB) × Flete Internacional  
            **Seguro** = Valor FOB × % Seguro
            **Valor CIF USD** = FOB + Flete + Seguro
            **Valor CIF COP** = CIF USD × Tipo Cambio
            
            **Arancel** = CIF COP × % Arancel
            **IVA** = (CIF COP + Arancel) × % IVA
            **Costos Nacionales** = Proporcional por cantidad
            
            **Costo Total** = CIF + Arancel + IVA + Costos Nacionales
            **Costo Unitario** = Costo Total / Cantidad
            """)
            
            if not st.session_state.landed_cost.empty:
                st.subheader("📈 Métricas Clave")
                costo_promedio = st.session_state.landed_cost['costo_unitario'].mean()
                costo_maximo = st.session_state.landed_cost['costo_unitario'].max()
                costo_minimo = st.session_state.landed_cost['costo_unitario'].min()
                total_importacion = st.session_state.landed_cost['costo_total'].sum()
                
                st.metric("💰 Costo Unitario Promedio", f"${costo_promedio:,.0f} COP")
                st.metric("📦 Costo Más Alto", f"${costo_maximo:,.0f} COP")
                st.metric("💸 Costo Más Bajo", f"${costo_minimo:,.0f} COP")
                st.metric("🏭 Total Importación", f"${total_importacion:,.0f} COP")
                
                # Distribución de costos
                st.subheader("📊 Distribución")
                total_cif = st.session_state.landed_cost['cif_cop'].sum()
                total_arancel = st.session_state.landed_cost['arancel_cop'].sum()
                total_iva = st.session_state.landed_cost['iva_cop'].sum()
                total_nacionales = st.session_state.landed_cost['costos_nacionales'].sum()
                
                datos_distribucion = {
                    'Componente': ['CIF', 'Arancel', 'IVA', 'Costos Nacionales'],
                    'Monto': [total_cif, total_arancel, total_iva, total_nacionales]
                }
                
                fig_torta = px.pie(
                    datos_distribucion,
                    values='Monto',
                    names='Componente',
                    title='Distribución Total de Costos'
                )
                st.plotly_chart(fig_torta, use_container_width=True)

    def calcular_landed_cost(self):
        """Calcular Landed Cost para todos los productos"""
        try:
            parametros = st.session_state.parametros
            productos = st.session_state.productos
            aranceles = st.session_state.aranceles
            
            usd_cop = parametros['USD_COP']
            flete = parametros['flete_internacional']
            seguro = parametros['seguro_porcentaje']
            iva = parametros['iva_importacion']
            costos_nacionales = (
                parametros['despacho_aduana'] +
                parametros['transporte_interno'] + 
                parametros['almacenaje']
            )
            
            resultados = []
            total_fob_usd = (productos['cantidad'] * productos['precio_unitario_usd']).sum()
            
            for _, producto in productos.iterrows():
                # Cálculos básicos
                valor_fob_usd = producto['cantidad'] * producto['precio_unitario_usd']
                flete_proporcional = (valor_fob_usd / total_fob_usd) * flete if total_fob_usd > 0 else 0
                seguro_proporcional = valor_fob_usd * seguro
                
                valor_cif_usd = valor_fob_usd + flete_proporcional + seguro_proporcional
                valor_cif_cop = valor_cif_usd * usd_cop
                
                # Buscar arancel
                arancel_info = aranceles[aranceles['hs_code'] == producto['hs_code']]
                if not arancel_info.empty:
                    arancel_porcentaje = arancel_info['arancel_porcentaje'].iloc[0]
                    iva_porcentaje = arancel_info['iva_porcentaje'].iloc[0]
                    otros_impuestos = arancel_info['otros_impuestos'].iloc[0]
                else:
                    # Valores por defecto si no encuentra HS Code
                    arancel_porcentaje = 0.10  # 10% por defecto
                    iva_porcentaje = iva
                    otros_impuestos = 0.0
                
                arancel_cop = valor_cif_cop * arancel_porcentaje
                iva_cop = (valor_cif_cop + arancel_cop) * iva_porcentaje
                otros_impuestos_cop = valor_cif_cop * otros_impuestos
                
                # Costos nacionales proporcionales
                costos_nacionales_prop = (producto['cantidad'] / productos['cantidad'].sum()) * costos_nacionales
                
                # Ajustar por pérdidas
                factor_perdidas = 1 + parametros['porcentaje_perdidas']
                
                costo_total = (valor_cif_cop + arancel_cop + iva_cop + otros_impuestos_cop + costos_nacionales_prop) * factor_perdidas
                costo_unitario = costo_total / producto['cantidad'] if producto['cantidad'] > 0 else 0
                
                resultados.append({
                    'sku': producto['sku'],
                    'descripcion': producto['descripcion'],
                    'cantidad': producto['cantidad'],
                    'cif_usd': valor_cif_usd,
                    'cif_cop': valor_cif_cop,
                    'arancel_cop': arancel_cop,
                    'iva_cop': iva_cop,
                    'otros_impuestos_cop': otros_impuestos_cop,
                    'costos_nacionales': costos_nacionales_prop,
                    'costo_total': costo_total,
                    'costo_unitario': costo_unitario,
                    'factor_perdidas': factor_perdidas
                })
            
            st.session_state.landed_cost = pd.DataFrame(resultados)
            st.session_state.calculos_realizados = True
            st.success("✅ Landed Cost calculado correctamente")
            
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {str(e)}")
            st.info("💡 Verifique que todos los productos tengan HS Code válido en la tabla de aranceles")

    def pagina_ventas(self):
        """Página de simulación de ventas"""
        st.header("🛍️ Simulación de Ventas y Rentabilidad")
        
        # Verificar prerequisitos
        if st.session_state.landed_cost.empty:
            st.error("❌ Primero calcule el Landed Cost en la pestaña '💰 Landed Cost'")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("📊 Calcular Precios de Venta", type="primary", use_container_width=True, key="btn_calcular_ventas"):
                with st.spinner("Calculando precios y rentabilidad..."):
                    self.calcular_ventas()
            
            if not st.session_state.ventas.empty:
                st.subheader("💰 Resultados de Ventas")
                
                # Mostrar tabla con formato
                df_display = st.session_state.ventas.copy()
                st.dataframe(
                    df_display.style.format({
                        'costo_landed': '${:,.0f}',
                        'precio_venta': '${:,.0f}',
                        'comision_ml': '${:,.0f}',
                        'envio': '${:,.0f}',
                        'packaging': '${:,.0f}',
                        'precio_neto': '${:,.0f}',
                        'rentabilidad': '{:.1%}',
                        'markup': '{:.1f}x'
                    }),
                    use_container_width=True,
                    height=400
                )
                
                # Análisis de rentabilidad
                tab1, tab2, tab3 = st.tabs(["📈 Rentabilidad", "💰 Precios", "🎯 Recomendaciones"])
                
                with tab1:
                    fig_rentabilidad = px.bar(
                        st.session_state.ventas,
                        x='sku',
                        y='rentabilidad',
                        title='Rentabilidad por Producto',
                        labels={'rentabilidad': 'Rentabilidad %', 'sku': 'SKU'},
                        color='rentabilidad',
                        color_continuous_scale='RdYlGn'
                    )
                    st.plotly_chart(fig_rentabilidad, use_container_width=True)
                
                with tab2:
                    fig_precios = go.Figure()
                    fig_precios.add_trace(go.Bar(
                        name='Costo Landed',
                        x=st.session_state.ventas['sku'],
                        y=st.session_state.ventas['costo_landed'],
                        marker_color='lightcoral'
                    ))
                    fig_precios.add_trace(go.Bar(
                        name='Precio Venta',
                        x=st.session_state.ventas['sku'],
                        y=st.session_state.ventas['precio_venta'],
                        marker_color='lightgreen'
                    ))
                    fig_precios.update_layout(
                        title='Comparación: Costo Landed vs Precio Venta',
                        barmode='group'
                    )
                    st.plotly_chart(fig_precios, use_container_width=True)
                
                with tab3:
                    self.mostrar_recomendaciones_ventas()
                
            else:
                st.info("👆 Haz clic en 'Calcular Precios de Venta' para ver los resultados")

        with col2:
            st.subheader("ℹ️ Información del Cálculo")
            st.write("""
            **🧮 Fórmulas aplicadas:**
            
            **Precio Venta** = Costo Landed / (1 - Margen Objetivo)
            **Comisión ML** = Precio Venta × % Comisión (según categoría)
            **Precio Neto** = Precio Venta - Comisión - Envío - Packaging
            **Rentabilidad** = (Precio Neto - Costo Landed) / Costo Landed
            **Markup** = Precio Venta / Costo Landed
            
            **Nota:** El cálculo considera pérdidas por transporte.
            """)
            
            if not st.session_state.ventas.empty:
                st.subheader("📊 Métricas Clave")
                rent_promedio = st.session_state.ventas['rentabilidad'].mean()
                margen_objetivo = st.session_state.parametros['margen_objetivo']
                mejor_producto = st.session_state.ventas.loc[st.session_state.ventas['rentabilidad'].idxmax()]
                peor_producto = st.session_state.ventas.loc[st.session_state.ventas['rentabilidad'].idxmin()]
                
                st.metric("🎯 Rentabilidad Promedio", f"{rent_promedio:.1%}")
                st.metric("📊 Margen Objetivo", f"{margen_objetivo:.1%}")
                st.metric("🏆 Mejor Producto", f"{mejor_producto['rentabilidad']:.1%}")
                st.metric("📉 Peor Producto", f"{peor_producto['rentabilidad']:.1%}")
                
                # Productos que no alcanzan margen objetivo
                productos_bajos = st.session_state.ventas[st.session_state.ventas['rentabilidad'] < margen_objetivo]
                if not productos_bajos.empty:
                    st.warning(f"⚠️ {len(productos_bajos)} productos no alcanzan el margen objetivo")
                    for _, producto in productos_bajos.iterrows():
                        st.write(f"• {producto['sku']}: {producto['rentabilidad']:.1%}")

    def mostrar_recomendaciones_ventas(self):
        """Mostrar recomendaciones basadas en el análisis de ventas"""
        if st.session_state.ventas.empty:
            return
        
        ventas = st.session_state.ventas
        margen_objetivo = st.session_state.parametros['margen_objetivo']
        
        # Análisis
        productos_sobre_margen = ventas[ventas['rentabilidad'] >= margen_objetivo]
        productos_bajo_margen = ventas[ventas['rentabilidad'] < margen_objetivo]
        
        st.subheader("🎯 Recomendaciones Estratégicas")
        
        if len(productos_sobre_margen) > 0:
            st.success(f"✅ **{len(productos_sobre_margen)} productos superan el margen objetivo**")
            mejor_producto = productos_sobre_margen.loc[productos_sobre_margen['rentabilidad'].idxmax()]
            st.write(f"**Producto estrella:** {mejor_producto['descripcion']} ({mejor_producto['rentabilidad']:.1%})")
        
        if len(productos_bajo_margen) > 0:
            st.warning(f"⚠️ **{len(productos_bajo_margen)} productos necesitan atención:**")
            for _, producto in productos_bajo_margen.nsmallest(3, 'rentabilidad').iterrows():
                st.write(f"• **{producto['sku']}**: {producto['rentabilidad']:.1%} (objetivo: {margen_objetivo:.1%})")
                
                # Recomendaciones específicas
                if producto['rentabilidad'] < 0:
                    st.error("  🔴 **Pérdida:** Considerar eliminar producto o renegociar costos")
                elif producto['rentabilidad'] < margen_objetivo * 0.5:
                    st.warning("  🟡 **Crítico:** Revisar costos de importación o aumentar precio")
                else:
                    st.info("  🔵 **Ajustable:** Pequeño aumento de precio podría alcanzar objetivo")

    def calcular_ventas(self):
        """Calcular precios de venta y rentabilidad"""
        try:
            if st.session_state.landed_cost.empty:
                st.warning("⚠️ Primero calcula el Landed Cost")
                return
            
            parametros = st.session_state.parametros
            landed_cost = st.session_state.landed_cost
            productos = st.session_state.productos
            
            margen = parametros['margen_objetivo']
            packaging = parametros['costo_packaging']
            envio = parametros['costo_envio_local']
            
            resultados = []
            
            for _, landed in landed_cost.iterrows():
                producto = productos[productos['sku'] == landed['sku']].iloc[0]
                costo_unitario = landed['costo_unitario']
                categoria = producto['categoria']
                
                # Determinar comisión según categoría
                if categoria == 'Electrónicos':
                    comision_ml = parametros['comision_ml_electronicos']
                elif categoria == 'Hogar':
                    comision_ml = parametros['comision_ml_hogar']
                elif categoria == 'Moda':
                    comision_ml = parametros['comision_ml_moda']
                else:
                    comision_ml = 0.15  # Default
                
                # Cálculos de venta
                precio_venta = costo_unitario / (1 - margen)
                comision = precio_venta * comision_ml
                precio_neto = precio_venta - comision - envio - packaging
                rentabilidad = (precio_neto - costo_unitario) / costo_unitario
                markup = precio_venta / costo_unitario
                
                resultados.append({
                    'sku': landed['sku'],
                    'descripcion': landed['descripcion'],
                    'categoria': categoria,
                    'costo_landed': costo_unitario,
                    'precio_venta': precio_venta,
                    'comision_ml': comision,
                    'comision_porcentaje': comision_ml,
                    'envio': envio,
                    'packaging': packaging,
                    'precio_neto': precio_neto,
                    'rentabilidad': rentabilidad,
                    'markup': markup
                })
            
            st.session_state.ventas = pd.DataFrame(resultados)
            st.session_state.calculos_realizados = True
            st.success("✅ Ventas calculadas correctamente")
            
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {str(e)}")

    def pagina_escenarios(self):
        """Página de análisis de escenarios"""
        st.header("📈 Análisis de Escenarios")
        
        # Verificar prerequisitos
        if st.session_state.ventas.empty:
            st.error("❌ Primero calcule las ventas en la pestaña '🛍️ Ventas'")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔄 Calcular Escenarios", type="primary", use_container_width=True, key="btn_calcular_escenarios"):
                with st.spinner("Analizando escenarios..."):
                    self.calcular_escenarios()
            
            if not st.session_state.escenarios.empty:
                st.subheader("📊 Resultados de Escenarios")
                
                # Mostrar tabla
                st.dataframe(
                    st.session_state.escenarios.style.format({
                        'tipo_cambio': '{:,.0f}',
                        'arancel_porcentaje': '{:.1%}',
                        'flete_usd': '{:,.0f}',
                        'costo_promedio': '{:,.0f}',
                        'rentabilidad_promedio': '{:.1%}',
                        'impacto_rentabilidad': '{:+.1%}'
                    }),
                    use_container_width=True
                )
                
                # Gráficos
                tab1, tab2 = st.tabs(["📈 Comparación", "📊 Sensibilidad"])
                
                with tab1:
                    fig_comparacion = px.bar(
                        st.session_state.escenarios,
                        x='escenario',
                        y='rentabilidad_promedio',
                        title='Rentabilidad por Escenario',
                        labels={'rentabilidad_promedio': 'Rentabilidad %', 'escenario': 'Escenario'},
                        color='rentabilidad_promedio',
                        color_continuous_scale='Viridis',
                        text='rentabilidad_promedio'
                    )
                    fig_comparacion.update_traces(texttemplate='%{text:.1%}', textposition='outside')
                    st.plotly_chart(fig_comparacion, use_container_width=True)
                
                with tab2:
                    fig_sensibilidad = px.line(
                        st.session_state.escenarios,
                        x='escenario',
                        y=['costo_promedio', 'rentabilidad_promedio'],
                        title='Sensibilidad: Costo vs Rentabilidad',
                        labels={'value': 'Valor', 'variable': 'Métrica'},
                        secondary_y=['rentabilidad_promedio']
                    )
                    st.plotly_chart(fig_sensibilidad, use_container_width=True)
                
                # Análisis de riesgo
                st.subheader("📉 Análisis de Riesgo")
                base_rent = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Base']['rentabilidad_promedio'].iloc[0]
                optimista_rent = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Optimista']['rentabilidad_promedio'].iloc[0]
                pesimista_rent = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Pesimista']['rentabilidad_promedio'].iloc[0]
                
                col_risk1, col_risk2, col_risk3 = st.columns(3)
                with col_risk1:
                    st.metric("🟢 Mejor Caso", f"{optimista_rent:.1%}", f"+{(optimista_rent-base_rent):.1%}")
                with col_risk2:
                    st.metric("🟡 Caso Base", f"{base_rent:.1%}")
                with col_risk3:
                    st.metric("🔴 Peor Caso", f"{pesimista_rent:.1%}", f"{(pesimista_rent-base_rent):.1%}")
                
            else:
                st.info("👆 Haz clic para calcular los escenarios")

        with col2:
            st.subheader("🎯 Configuración de Escenarios")
            st.write("""
            **Escenarios predefinidos:**
            
            **🟢 Optimista:**
            - USD → COP: 4,200 (+10%)
            - Arancel: 4% (-33%)
            - Flete: $2,200 USD (-12%)
            
            **🟡 Base:**
            - USD → COP: 3,800  
            - Arancel: 6%
            - Flete: $2,500 USD
            
            **🔴 Pesimista:**
            - USD → COP: 3,400 (-10%)
            - Arancel: 8% (+33%)
            - Flete: $2,800 USD (+12%)
            """)
            
            # Personalizar escenarios
            with st.expander("⚙️ Personalizar Escenarios"):
                st.number_input("Variación Tipo Cambio (%)", value=10.0, key="var_tc")
                st.number_input("Variación Arancel (%)", value=33.0, key="var_arancel")
                st.number_input("Variación Flete (%)", value=12.0, key="var_flete")
            
            if not st.session_state.escenarios.empty:
                st.subheader("📋 Recomendaciones")
                optimista = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Optimista'].iloc[0]
                pesimista = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Pesimista'].iloc[0]
                
                if pesimista['rentabilidad_promedio'] > 0:
                    st.success("✅ Negocio viable incluso en escenario pesimista")
                elif optimista['rentabilidad_promedio'] > 0:
                    st.warning("⚠️ Negocio viable solo en escenarios favorables")
                else:
                    st.error("❌ Reconsiderar el negocio en todos los escenarios")

    def calcular_escenarios(self):
        """Calcular escenarios de sensibilidad"""
        try:
            # Obtener datos base
            costo_base = st.session_state.landed_cost['costo_unitario'].mean()
            rentabilidad_base = st.session_state.ventas['rentabilidad'].mean()
            parametros = st.session_state.parametros
            
            # Escenarios predefinidos con variaciones personalizables
            var_tc = st.session_state.get("var_tc", 10.0) / 100
            var_arancel = st.session_state.get("var_arancel", 33.0) / 100
            var_flete = st.session_state.get("var_flete", 12.0) / 100
            
            escenarios_config = [
                {
                    'nombre': 'Optimista', 
                    'tipo_cambio': parametros['USD_COP'] * (1 + var_tc),
                    'arancel': max(0.01, parametros['iva_importacion'] * (1 - var_arancel)),
                    'flete': max(100, parametros['flete_internacional'] * (1 - var_flete)),
                    'factor_costo': 0.85,
                    'factor_rentabilidad': 1.3
                },
                {
                    'nombre': 'Base',
                    'tipo_cambio': parametros['USD_COP'],
                    'arancel': parametros['iva_importacion'],
                    'flete': parametros['flete_internacional'],
                    'factor_costo': 1.0,
                    'factor_rentabilidad': 1.0
                },
                {
                    'nombre': 'Pesimista',
                    'tipo_cambio': parametros['USD_COP'] * (1 - var_tc),
                    'arancel': parametros['iva_importacion'] * (1 + var_arancel),
                    'flete': parametros['flete_internacional'] * (1 + var_flete),
                    'factor_costo': 1.15,
                    'factor_rentabilidad': 0.7
                }
            ]
            
            escenarios_data = []
            
            for escenario in escenarios_config:
                costo_ajustado = costo_base * escenario['factor_costo']
                rentabilidad_ajustada = rentabilidad_base * escenario['factor_rentabilidad']
                impacto = rentabilidad_ajustada - rentabilidad_base
                
                escenarios_data.append({
                    'escenario': escenario['nombre'],
                    'tipo_cambio': escenario['tipo_cambio'],
                    'arancel_porcentaje': escenario['arancel'],
                    'flete_usd': escenario['flete'],
                    'costo_promedio': costo_ajustado,
                    'rentabilidad_promedio': rentabilidad_ajustada,
                    'impacto_rentabilidad': impacto
                })
            
            st.session_state.escenarios = pd.DataFrame(escenarios_data)
            st.session_state.calculos_realizados = True
            st.success("✅ Escenarios calculados correctamente")
            
        except Exception as e:
            st.error(f"❌ Error en el cálculo: {str(e)}")

    def pagina_dashboard(self):
        """Página de dashboard ejecutivo"""
        st.header("🎯 Dashboard Ejecutivo")
        
        # Verificar si hay datos
        if st.session_state.productos.empty:
            st.error("❌ No hay datos para mostrar. Comience agregando productos.")
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_skus = len(st.session_state.productos)
            st.metric("📦 SKUs", total_skus)
            
        with col2:
            total_unidades = st.session_state.productos['cantidad'].sum() if not st.session_state.productos.empty else 0
            st.metric("🔄 Unidades", f"{total_unidades:,}")
            
        with col3:
            if not st.session_state.productos.empty:
                inversion_total = (st.session_state.productos['cantidad'] * st.session_state.productos['precio_unitario_usd']).sum()
                st.metric("💰 Inversión Total", f"${inversion_total:,.0f} USD")
            else:
                st.metric("💰 Inversión Total", "$0 USD")
            
        with col4:
            if not st.session_state.ventas.empty:
                rent_promedio = st.session_state.ventas['rentabilidad'].mean()
                st.metric("📈 Rentabilidad Promedio", f"{rent_promedio:.1%}")
            else:
                st.metric("📈 Rentabilidad", "Por calcular")
        
        # Layout principal
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # Gráficos principales
            if not st.session_state.landed_cost.empty:
                st.subheader("💰 Análisis de Costos")
                
                tab1, tab2 = st.tabs(["Composición", "Evolución"])
                
                with tab1:
                    fig_composicion = px.sunburst(
                        st.session_state.landed_cost,
                        path=['sku'],
                        values='costo_total',
                        title='Distribución del Costo Total por SKU'
                    )
                    st.plotly_chart(fig_composicion, use_container_width=True)
                
                with tab2:
                    costos_por_sku = st.session_state.landed_cost[['sku', 'costo_unitario']].sort_values('costo_unitario')
                    fig_evolucion = px.bar(
                        costos_por_sku,
                        x='sku',
                        y='costo_unitario',
                        title='Costo Unitario por SKU (Ordenado)',
                        color='costo_unitario'
                    )
                    st.plotly_chart(fig_evolucion, use_container_width=True)
            
            if not st.session_state.ventas.empty:
                st.subheader("📊 Análisis de Rentabilidad")
                
                col_rent1, col_rent2 = st.columns(2)
                
                with col_rent1:
                    # Top productos rentables
                    top_rentables = st.session_state.ventas.nlargest(5, 'rentabilidad')
                    fig_top = px.bar(
                        top_rentables,
                        x='sku',
                        y='rentabilidad',
                        title='Top 5 Productos Más Rentables',
                        color='rentabilidad'
                    )
                    st.plotly_chart(fig_top, use_container_width=True)
                
                with col_rent2:
                    # Rentabilidad por categoría
                    if 'categoria' in st.session_state.ventas.columns:
                        rent_por_categoria = st.session_state.ventas.groupby('categoria')['rentabilidad'].mean().reset_index()
                        fig_categoria = px.pie(
                            rent_por_categoria,
                            values='rentabilidad',
                            names='categoria',
                            title='Rentabilidad Promedio por Categoría'
                        )
                        st.plotly_chart(fig_categoria, use_container_width=True)

        with col_right:
            st.subheader("📋 Resumen Ejecutivo")
            
            # Estado del análisis
            progreso = self.calcular_progreso()
            st.metric("📈 Progreso del Análisis", f"{progreso}%")
            
            # Alertas importantes
            st.subheader("🚨 Alertas Importantes")
            
            if not st.session_state.ventas.empty:
                margen_objetivo = st.session_state.parametros['margen_objetivo']
                productos_bajos = st.session_state.ventas[st.session_state.ventas['rentabilidad'] < margen_objetivo]
                
                if len(productos_bajos) > 0:
                    st.error(f"❌ {len(productos_bajos)} productos no alcanzan margen objetivo")
                else:
                    st.success("✅ Todos los productos superan el margen objetivo")
            
            if not st.session_state.escenarios.empty:
                pesimista_rent = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Pesimista']['rentabilidad_promedio'].iloc[0]
                if pesimista_rent < 0:
                    st.error("🔴 Rentabilidad negativa en escenario pesimista")
                elif pesimista_rent < margen_objetivo * 0.5:
                    st.warning("🟡 Rentabilidad baja en escenario pesimista")
                else:
                    st.success("🟢 Buena resiliencia en escenarios adversos")
            
            # Recomendaciones rápidas
            st.subheader("💡 Recomendaciones Rápidas")
            
            if not st.session_state.ventas.empty:
                mejor_producto = st.session_state.ventas.loc[st.session_state.ventas['rentabilidad'].idxmax()]
                st.write(f"**Enfócate en:** {mejor_producto['descripcion']}")
                st.write(f"**Rentabilidad:** {mejor_producto['rentabilidad']:.1%}")
            
            if st.session_state.parametros['porcentaje_perdidas'] < 0.02:
                st.info("**Considera:** Aumentar porcentaje de pérdidas al 2-3% para ser más conservador")
            
            st.subheader("📊 KPIs Clave")
            if not st.session_state.ventas.empty:
                kpis = {
                    "Margen Promedio": f"{st.session_state.ventas['rentabilidad'].mean():.1%}",
                    "Markup Promedio": f"{st.session_state.ventas['markup'].mean():.1f}x",
                    "Productos Viables": f"{len(st.session_state.ventas[st.session_state.ventas['rentabilidad'] > 0])}/{len(st.session_state.ventas)}",
                    "Inversión por SKU": f"${inversion_total/len(st.session_state.productos):,.0f} USD"
                }
                
                for kpi, valor in kpis.items():
                    st.metric(kpi, valor)

    def pagina_exportar(self):
        """Página de exportación de datos"""
        st.header("💾 Exportar Datos y Reportes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📤 Exportar DataFrames")
            
            datasets = {
                "📦 Productos": st.session_state.productos,
                "📊 Aranceles": st.session_state.aranceles,
                "💰 Landed Cost": st.session_state.landed_cost,
                "🛍️ Ventas": st.session_state.ventas,
                "📈 Escenarios": st.session_state.escenarios
            }
            
            for nombre, df in datasets.items():
                if not df.empty:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Descargar {nombre} como CSV",
                        data=csv,
                        file_name=f"{nombre.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"btn_export_{nombre}"
                    )
                else:
                    st.button(
                        f"📥 {nombre} (No disponible)",
                        disabled=True,
                        use_container_width=True,
                        key=f"btn_disabled_{nombre}"
                    )
            
            # Exportar parámetros
            if st.button("⚙️ Exportar Parámetros como JSON", use_container_width=True, key="btn_export_parametros"):
                parametros_json = json.dumps(st.session_state.parametros, indent=2)
                st.download_button(
                    label="📥 Descargar Parámetros",
                    data=parametros_json,
                    file_name=f"parametros_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    key="btn_download_parametros"
                )

        with col2:
            st.subheader("📋 Reportes Ejecutivos")
            
            if st.button("📄 Generar Reporte Completo PDF", use_container_width=True, key="btn_reporte_completo"):
                self.generar_reporte_completo()
            
            if st.button("📊 Reporte de Rentabilidad", use_container_width=True, key="btn_reporte_rentabilidad"):
                self.generar_reporte_rentabilidad()
            
            st.subheader("⚙️ Gestión de Datos")
            
            # Backup completo
            if st.button("💾 Crear Backup Completo", use_container_width=True, type="primary", key="btn_backup"):
                self.crear_backup_completo()
            
            # Cargar datos
            archivo_cargado = st.file_uploader(
                "🔄 Cargar Datos desde Backup",
                type=['json', 'csv'],
                accept_multiple_files=False,
                key="cargador_datos"
            )
            
            if archivo_cargado is not None:
                if st.button("🔄 Cargar Datos", use_container_width=True, key="btn_cargar_datos"):
                    self.cargar_datos_desde_archivo(archivo_cargado)
            
            st.subheader("🔧 Utilidades")
            
            if st.button("🔄 Reiniciar Todos los Datos", use_container_width=True, key="btn_reiniciar_todo"):
                if st.checkbox("⚠️ Confirmar reinicio completo", key="confirmar_reinicio"):
                    self.inicializar_datos()
                    st.success("✅ Todos los datos han sido reiniciados")
                    st.rerun()

    def generar_reporte_completo(self):
        """Generar reporte ejecutivo completo"""
        reporte = self._generar_contenido_reporte()
        
        # Crear archivo de texto descargable
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo (TXT)",
            data=reporte.encode('utf-8'),
            file_name=f"reporte_importaciones_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_descargar_reporte"
        )
        
        # Mostrar preview
        with st.expander("👁️ Vista Previa del Reporte"):
            st.text(reporte)

    def _generar_contenido_reporte(self):
        """Generar contenido del reporte ejecutivo"""
        reporte = f"""
{'='*60}
REPORTE EJECUTIVO - CALCULADORA DE IMPORTACIONES
{'='*60}
Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*60}

RESUMEN EJECUTIVO
{'-'*60}

📦 DATOS GENERALES:
• SKUs analizados: {len(st.session_state.productos)}
• Total unidades: {st.session_state.productos['cantidad'].sum():,}
• Inversión total: ${(st.session_state.productos['cantidad'] * st.session_state.productos['precio_unitario_usd']).sum():,.2f} USD

"""
        
        if not st.session_state.ventas.empty:
            rent_promedio = st.session_state.ventas['rentabilidad'].mean()
            mejor_producto = st.session_state.ventas.loc[st.session_state.ventas['rentabilidad'].idxmax()]
            peor_producto = st.session_state.ventas.loc[st.session_state.ventas['rentabilidad'].idxmin()]
            
            reporte += f"""
💰 ANÁLISIS FINANCIERO:
• Rentabilidad promedio: {rent_promedio:.1%}
• Margen objetivo: {st.session_state.parametros['margen_objetivo']:.1%}
• Producto más rentable: {mejor_producto['descripcion']} ({mejor_producto['rentabilidad']:.1%})
• Producto menos rentable: {peor_producto['descripcion']} ({peor_producto['rentabilidad']:.1%})

"""
        
        if not st.session_state.escenarios.empty:
            base = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Base'].iloc[0]
            optimista = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Optimista'].iloc[0]
            pesimista = st.session_state.escenarios[st.session_state.escenarios['escenario'] == 'Pesimista'].iloc[0]
            
            reporte += f"""
📈 ANÁLISIS DE ESCENARIOS:
• Escenario base: {base['rentabilidad_promedio']:.1%}
• Escenario optimista: {optimista['rentabilidad_promedio']:.1%} (+{(optimista['rentabilidad_promedio']-base['rentabilidad_promedio']):.1%})
• Escenario pesimista: {pesimista['rentabilidad_promedio']:.1%} ({(pesimista['rentabilidad_promedio']-base['rentabilidad_promedio']):.1%})

"""
        
        reporte += f"""
🎯 RECOMENDACIONES ESTRATÉGICAS:
{'-'*60}

1. ENFOQUE EN PRODUCTOS RENTABLES:
"""
        
        if not st.session_state.ventas.empty:
            top_3 = st.session_state.ventas.nlargest(3, 'rentabilidad')
            for i, (_, producto) in enumerate(top_3.iterrows(), 1):
                reporte += f"   {i}. {producto['descripcion']} - Rentabilidad: {producto['rentabilidad']:.1%}\n"
        
        reporte += f"""
2. PARÁMETROS CLAVE:
   • Tipo cambio USD: {st.session_state.parametros['USD_COP']:,.0f} COP
   • Margen objetivo: {st.session_state.parametros['margen_objetivo']:.1%}
   • Costos logísticos: ${st.session_state.parametros['flete_internacional']:,.0f} USD

3. CONSIDERACIONES:
   • Verificar aranceles actualizados con DIAN
   • Monitorear tipo de cambio regularmente
   • Considerar seguros adicionales para productos de alto valor

{'='*60}
© 2024 Calculadora de Importaciones - Reporte generado automáticamente
{'='*60}
"""
        return reporte

    def generar_reporte_rentabilidad(self):
        """Generar reporte específico de rentabilidad"""
        if st.session_state.ventas.empty:
            st.error("No hay datos de ventas para generar el reporte")
            return
        
        reporte = f"""
REPORTE DE RENTABILIDAD - {datetime.now().strftime('%Y-%m-%d')}
{'-'*50}

RESUMEN POR PRODUCTO:
{'-'*50}

"""
        
        for _, producto in st.session_state.ventas.iterrows():
            reporte += f"""
📦 {producto['sku']} - {producto['descripcion']}
   • Costo Landed: ${producto['costo_landed']:,.0f} COP
   • Precio Venta: ${producto['precio_venta']:,.0f} COP  
   • Rentabilidad: {producto['rentabilidad']:.1%}
   • Markup: {producto['markup']:.1f}x
   • Categoría: {producto['categoria']}
"""
        
        st.download_button(
            label="📥 Descargar Reporte de Rentabilidad",
            data=reporte.encode('utf-8'),
            file_name=f"reporte_rentabilidad_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="btn_descargar_rentabilidad"
        )

    def crear_backup_completo(self):
        """Crear backup de todos los datos"""
        backup_data = {
            'parametros': st.session_state.parametros,
            'productos': st.session_state.productos.to_dict(),
            'aranceles': st.session_state.aranceles.to_dict(),
            'landed_cost': st.session_state.landed_cost.to_dict() if not st.session_state.landed_cost.empty else {},
            'ventas': st.session_state.ventas.to_dict() if not st.session_state.ventas.empty else {},
            'escenarios': st.session_state.escenarios.to_dict() if not st.session_state.escenarios.empty else {},
            'fecha_backup': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        st.download_button(
            label="📥 Descargar Backup Completo",
            data=json.dumps(backup_data, indent=2, ensure_ascii=False),
            file_name=f"backup_calculadora_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            key="btn_descargar_backup"
        )

    def cargar_datos_desde_archivo(self, archivo):
        """Cargar datos desde archivo de backup"""
        try:
            if archivo.type == "application/json":
                datos = json.load(archivo)
                
                if 'parametros' in datos:
                    st.session_state.parametros = datos['parametros']
                if 'productos' in datos:
                    st.session_state.productos = pd.DataFrame(datos['productos'])
                if 'aranceles' in datos:
                    st.session_state.aranceles = pd.DataFrame(datos['aranceles'])
                if 'landed_cost' in datos and datos['landed_cost']:
                    st.session_state.landed_cost = pd.DataFrame(datos['landed_cost'])
                if 'ventas' in datos and datos['ventas']:
                    st.session_state.ventas = pd.DataFrame(datos['ventas'])
                if 'escenarios' in datos and datos['escenarios']:
                    st.session_state.escenarios = pd.DataFrame(datos['escenarios'])
                
                st.success("✅ Datos cargados correctamente desde el backup")
                st.rerun()
                
            else:
                st.error("Formato de archivo no soportado")
                
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")

    def recalcular_todo(self):
        """Recalcular todos los módulos"""
        try:
            if not st.session_state.productos.empty and not st.session_state.aranceles.empty:
                self.calcular_landed_cost()
                if not st.session_state.landed_cost.empty:
                    self.calcular_ventas()
                    if not st.session_state.ventas.empty:
                        self.calcular_escenarios()
            
            st.session_state.calculos_realizados = True
            
        except Exception as e:
            st.error(f"Error en el recálculo: {str(e)}")

def main():
    """Función principal"""
    try:
        calculadora = CalculadoraImportacionesStreamlit()
        calculadora.ejecutar_aplicacion()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        st.info("Por favor, recargue la página o reinicie la aplicación")

if __name__ == "__main__":
    main()
