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
            st.markdown("### 🧭 Navegación")
            
            # Navegación con botones únicos
            if st.button("🏠 Inicio", key="nav_inicio_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "🏠 Inicio"
                st.rerun()
            
            if st.button("⚙️ Parámetros", key="nav_parametros_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "⚙️ Parámetros"
                st.rerun()
            
            if st.button("📦 Productos", key="nav_productos_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "📦 Productos"
                st.rerun()
            
            if st.button("📊 Aranceles", key="nav_aranceles_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "📊 Aranceles"
                st.rerun()
            
            if st.button("💰 Landed Cost", key="nav_landed_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "💰 Landed Cost"
                st.rerun()
            
            if st.button("🛍️ Ventas", key="nav_ventas_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "🛍️ Ventas"
                st.rerun()
            
            if st.button("📈 Escenarios", key="nav_escenarios_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "📈 Escenarios"
                st.rerun()
            
            if st.button("🎯 Dashboard", key="nav_dashboard_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "🎯 Dashboard"
                st.rerun()
            
            if st.button("💾 Exportar", key="nav_exportar_btn", use_container_width=True):
                st.session_state.pagina_seleccionada = "💾 Exportar"
                st.rerun()
            
            st.markdown("---")
            
            # Estado del sistema
            st.subheader("📊 Estado Actual")
            total_skus = len(st.session_state.productos)
            total_unidades = st.session_state.productos['cantidad'].sum()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("SKUs", total_skus)
            with col2:
                st.metric("Unidades", f"{total_unidades:,}")
            
            if not st.session_state.ventas.empty:
                rent_promedio = st.session_state.ventas['rentabilidad'].mean()
                st.metric("Rentabilidad", f"{rent_promedio:.1%}")
            
            # Botón de recálculo
            if st.button("🔄 Recalcular Todo", use_container_width=True, type="primary"):
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
            total_unidades = st.session_state.productos['cantidad'].sum()
            st.metric("🔄 Unidades Totales", f"{total_unidades:,}")
            
        with col3:
            inversion_total = (st.session_state.productos['cantidad'] * st.session_state.productos['precio_unitario_usd']).sum()
            st.metric("💰 Inversión Total", f"${inversion_total:,.0f} USD")
            
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
            
            if st.button("📊 Calcular Todo Automáticamente", use_container_width=True, key="calc_auto_btn"):
                with st.spinner("Calculando todos los módulos..."):
                    self.recalcular_todo()
                st.success("¡Análisis completo!")
            
            if st.button("🆕 Reiniciar Datos", use_container_width=True, key="reiniciar_btn"):
                if st.button("⚠️ Confirmar Reinicio", type="secondary", key="confirmar_reinicio_btn"):
                    self.inicializar_datos()
                    st.success("¡Datos reiniciados!")
            
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
        """Página de parámetros globales"""
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
                    key="envio_local_input"
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
                    key="comision_elec_input"
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
            if st.button("💾 Guardar Parámetros", use_container_width=True, type="primary", key="guardar_param_btn"):
                st.success("✅ Parámetros guardados correctamente")
                st.session_state.calculos_realizados = False
        
        with col_btn2:
            if st.button("🔄 Recalcular Todo", use_container_width=True, key="recalc_param_btn"):
                self.recalcular_todo()
                st.success("✅ Todos los cálculos actualizados")
        
        with col_btn3:
            if st.button("📊 Validar Parámetros", use_container_width=True, key="validar_param_btn"):
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
            
            if st.button("💾 Guardar Cambios en Productos", use_container_width=True, type="primary", key="guardar_productos_btn"):
                st.session_state.productos = edited_df
                st.session_state.calculos_realizados = False
                st.success("✅ Productos actualizados correctamente")
                st.rerun()

        with col2:
            st.subheader("🚀 Acciones Rápidas")
            
            # Formulario para nuevo producto rápido
            with st.form("nuevo_producto_rapido"):
                st.write("➕ Agregar Producto Rápido")
                nuevo_sku = st.text_input("SKU*", value=f"SKU_{datetime.now().strftime('%y%m%d%H%M')}", key="nuevo_sku_input")
                nueva_desc = st.text_input("Descripción*", key="nueva_desc_input")
                nueva_cant = st.number_input("Cantidad*", min_value=1, value=100, key="nueva_cant_input")
                nuevo_precio = st.number_input("Precio USD*", min_value=0.0, value=10.0, step=0.1, key="nuevo_precio_input")
                nueva_categoria = st.selectbox("Categoría*", ["Electrónicos", "Hogar", "Moda", "Deportes", "Otros"], key="nueva_cat_input")
                
                if st.form_submit_button("🎯 Agregar Producto", use_container_width=True, key="agregar_producto_btn"):
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
                
                if st.button("❌ Eliminar SKU Seleccionado", use_container_width=True, key="eliminar_sku_btn"):
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

    # ... (continuaría con los demás métodos, asegurando que todas las keys sean únicas)

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
            st.success("✅ Todos los cálculos han sido actualizados")
            
        except Exception as e:
            st.error(f"Error en el recálculo: {str(e)}")

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
