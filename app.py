import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

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
</style>
""", unsafe_allow_html=True)

class CalculadoraImportaciones:
    def __init__(self):
        self.tasa_cambio = self.obtener_tasa_cambio()
        self.iva = 0.19  # 19% IVA en Colombia
        self.anticipo_iva = 0.10  # 10% anticipo de IVA
        self.dai_arancel = 0.05  # 5% DAI (Arancel) - puede variar por producto
    
    def obtener_tasa_cambio(self):
        """Obtiene la tasa de cambio actual USD a COP"""
        try:
            # En un entorno real, usarías una API como:
            # response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            # data = response.json()
            # return data['rates']['COP']
            
            # Por simplicidad, usaremos un valor fijo (puedes cambiarlo)
            return 3950  # Tasa de cambio aproximada
        except:
            return 3950  # Valor por defecto en caso de error
    
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
    
    def calcular_gastos_varios(self, cif):
        """Calcula gastos varios (agente aduanal, almacenamiento, etc.)"""
        # Estos son valores estimados, pueden variar
        agencia_aduanal = max(cif * 0.015, 300000)  # 1.5% o mínimo 300,000 COP
        almacenamiento = 150000  # Estimado
        transporte_interno = 200000  # Estimado
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
    
    # Contenido principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="sub-header">📊 Datos de la Importación</div>', unsafe_allow_html=True)
        
        # Entradas del usuario
        valor_producto_usd = st.number_input(
            "Valor de la mercancía (USD)",
            min_value=0.0,
            max_value=1000000.0,
            value=1000.0,
            step=100.0,
            help="Valor FOB de los productos"
        )
        
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
            value=50.0,
            step=10.0
        )
        
        peso_kg = st.number_input(
            "Peso total (KG)",
            min_value=0.0,
            max_value=10000.0,
            value=100.0,
            step=10.0
        )
    
    with col2:
        st.markdown('<div class="sub-header">📈 Resumen Rápido</div>', unsafe_allow_html=True)
        
        # Conversión a COP
        valor_producto_cop = valor_producto_usd * calc.tasa_cambio
        flete_internacional_cop = flete_internacional_usd * calc.tasa_cambio
        seguro_cop = seguro_usd * calc.tasa_cambio
        
        st.metric("Valor mercancía", 
                 calc.formato_moneda(valor_producto_cop),
                 f"{valor_producto_usd:,.0f} USD")
        
        st.metric("Flete internacional",
                 calc.formato_moneda(flete_internacional_cop),
                 f"{flete_internacional_usd:,.0f} USD")
        
        st.metric("Costo total inicial",
                 calc.formato_moneda(valor_producto_cop + flete_internacional_cop + seguro_cop),
                 f"{valor_producto_usd + flete_internacional_usd + seguro_usd:,.0f} USD")
    
    # Cálculos
    cif_cop = calc.calcular_cif(valor_producto_cop, flete_internacional_cop, seguro_cop)
    dai_cop = calc.calcular_dai(cif_cop, tasa_arancel_personalizada)
    iva_cop = calc.calcular_iva(cif_cop, dai_cop)
    anticipo_iva_cop = calc.calcular_anticipo_iva(iva_cop)
    gastos_varios = calc.calcular_gastos_varios(cif_cop)
    
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
    
    # Análisis adicional
    st.markdown("---")
    st.markdown('<div class="sub-header">📈 Análisis de Rentabilidad</div>', unsafe_allow_html=True)
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        costo_por_kg = costo_total_cop / peso_kg if peso_kg > 0 else 0
        st.metric("Costo por KG", calc.formato_moneda(costo_por_kg))
    
    with col6:
        incremento_por_impuestos = ((dai_cop + iva_cop) / cif_cop) * 100
        st.metric("Incremento por impuestos", f"{incremento_por_impuestos:.1f}%")
    
    with col7:
        relacion_costo_impuestos = (costo_total_cop - cif_cop) / cif_cop * 100
        st.metric("Costos adicionales vs CIF", f"{relacion_costo_impuestos:.1f}%")
    
    # Tabla resumen
    st.markdown("---")
    st.markdown('<div class="sub-header">📋 Resumen en Tabla</div>', unsafe_allow_html=True)
    
    resumen_data = {
        'Concepto': [
            'Valor mercancía (FOB)',
            'Flete internacional',
            'Seguro',
            'Valor CIF',
            'DAI (Arancel)',
            'IVA',
            'Anticipo IVA',
            'Gastos varios',
            'TOTAL'
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
        ]
    }
    
    df = pd.DataFrame(resumen_data)
    df['USD'] = df['COP'] / calc.tasa_cambio
    df['COP'] = df['COP'].apply(lambda x: f"${x:,.0f}")
    df['USD'] = df['USD'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(df, use_container_width=True)
    
    # Advertencias y recomendaciones
    st.markdown("---")
    st.markdown('<div class="sub-header">⚠️ Consideraciones Importantes</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
    <strong>Nota:</strong> Esta calculadora proporciona estimados. Los costos reales pueden variar debido a:
    - Cambios en tasas arancelarias específicas por producto
    - Variaciones en la tasa de cambio
    - Gastos adicionales no considerados
    - Requisitos específicos de la DIAN
    - Tipo de producto y regulaciones especiales
    
    <strong>Recomendación:</strong> Siempre consulta con un agente aduanal para cálculos exactos.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
