import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np

def crear_web_interactiva():
    if not os.path.exists('backtest_cuantico.csv'):
        print("❌ No hay datos para la web.")
        return

    df = pd.read_csv('backtest_cuantico.csv')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # 1. Cálculos de Rendimiento
    df['Profit_Display'] = df['Resultado_60min'].fillna(0).cumsum()
    
    # 2. Cálculo de Precisión (MAE - Error Absoluto Medio)
    # Comparamos el Veredicto (lo que dijo) con el Resultado_60min (lo que pasó)
    df['Error'] = np.abs(df['Veredicto'] - (df['Resultado_60min'].fillna(0) / 100))
    mae_reciente = df['Error'].tail(10).mean() # Promedio de los últimos 10
    
    # 3. Crear el Dashboard
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )

    # A. Precio de BTC (Eje Principal)
    fig.add_trace(
        go.Scatter(x=df['Fecha'], y=df['Precio_Entrada'], 
                   name="Precio BTC ($)", line=dict(color='#00ffcc', width=2)),
        row=1, col=1, secondary_y=False
    )

    # B. Profit Acumulado (Eje Secundario)
    fig.add_trace(
        go.Scatter(x=df['Fecha'], y=df['Profit_Display'], 
                   name="Profit Acumulado %", fill='tozeroy',
                   line=dict(color='#ff00ff', width=3)),
        row=1, col=1, secondary_y=True
    )

    # C. Histograma de Error (Abajo)
    fig.add_trace(
        go.Bar(x=df['Fecha'], y=df['Error'], 
               name="Desviación (Error)", marker_color='#ffa500', opacity=0.6),
        row=2, col=1
    )

    # 4. Anotación de Precisión (El "Semáforo")
    color_mae = "green" if mae_reciente < 0.2 else ("yellow" if mae_reciente < 0.5 else "red")
    
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.1,
        text=f"🎯 Precisión (MAE 10p): <b>{mae_reciente:.4f}</b>",
        showarrow=False, font=dict(size=16, color=color_mae),
        bgcolor="rgba(0,0,0,0.8)", bordercolor=color_mae, borderpad=4
    )

    # Estilo Dark Mode
    fig.update_layout(
        template='plotly_dark',
        title='🌌 Panel Maestro Oráculo 128Q',
        hovermode='x unified',
        paper_bgcolor='#0d1117',
        plot_bgcolor='#0d1117',
        height=800,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.write_html('index.html')
    print(f"🌐 Dashboard actualizado. MAE Reciente: {mae_reciente:.4f}")

if __name__ == "__main__":
    crear_web_interactiva()
