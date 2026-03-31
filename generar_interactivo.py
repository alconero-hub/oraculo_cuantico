import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def crear_web_interactiva():
    if not os.path.exists('backtest_cuantico.csv'):
        return

    df = pd.read_csv('backtest_cuantico.csv')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df['Profit_Acumulado'] = df['Resultado_60min'].fillna(0).cumsum()

    # Crear figura con ejes secundarios
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Gráfico de Precio
    fig.add_trace(
        go.Scatter(x=df['Fecha'], y=df['Precio_Entrada'], name="Precio BTC", line=dict(color='#00ffcc')),
        secondary_y=False,
    )

    # 2. Barras de Veredicto (Q-Score)
    fig.add_trace(
        go.Bar(x=df['Fecha'], y=df['Veredicto'], name="Q-Score", marker_color='rgba(255, 255, 255, 0.3)'),
        secondary_y=True,
    )

    # 3. Línea de Profit
    fig.add_trace(
        go.Scatter(x=df['Fecha'], y=df['Profit_Acumulado'], name="Profit %", line=dict(color='#ff00ff', width=3)),
        secondary_y=True,
    )

    # Diseño Dark Mode profesional
    fig.update_layout(
        template='plotly_dark',
        title='📊 Panel Interactivo Oráculo 128Q',
        xaxis_title='Fecha/Hora (UTC)',
        paper_bgcolor='#0d1117',
        plot_bgcolor='#0d1117'
    )

    fig.write_html('index.html')
    print("🌐 Dashboard interactivo generado en index.html")

if __name__ == "__main__":
    crear_web_interactiva()
