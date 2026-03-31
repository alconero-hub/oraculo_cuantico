import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import numpy as np

def generar_grafica():
    if not os.path.exists('backtest_cuantico.csv'):
        print("❌ No hay datos en 'backtest_cuantico.csv' para graficar.")
        return

    # 1. Carga de datos
    df = pd.read_csv('backtest_cuantico.csv')
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='mixed')
    df = df.sort_values('Fecha')

    # 2. Cálculo de Ganancia Acumulada
    # Llenamos los NaN con 0 para que la suma no se rompa
    df['Resultado_Limpio'] = df['Resultado_60min'].fillna(0)
    df['Profit_Acumulado'] = df['Resultado_Limpio'].cumsum()

    # Filtramos para mostrar solo los últimos 100 registros en la gráfica visual
    df_plot = df.tail(100)

    # 3. Configuración de la Figura
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Eje para el Veredicto y el Profit
    ax2 = ax1.twinx() 

    # --- EJE 1: PRECIO DE BTC ---
    ax1.plot(df_plot['Fecha'], df_plot['Precio_Entrada'], color='#00ffcc', linewidth=1.5, label='Precio BTC', alpha=0.6)
    ax1.set_ylabel('Precio BTC (USD)', color='#00ffcc', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#00ffcc')

    # --- EJE 2: VEREDICTO CUÁNTICO (Barras) ---
    colores = []
    for v in df_plot['Veredicto']:
        if abs(v) < 0.05: colores.append('#444444') # Standby (Gris)
        elif v > 0.15: colores.append('#00ff00')    # Compra (Verde)
        elif v < -0.15: colores.append('#ff0000')   # Venta (Rojo)
        else: colores.append('#ffff00')             # Espera (Amarillo)

    ax2.bar(df_plot['Fecha'], df_plot['Veredicto'], color=colores, width=0.02, label='Q-Score (Veredicto)', alpha=0.4)

    # --- LÍNEA DE PROFIT ACUMULADO (La nueva estrella) ---
    ax2.plot(df_plot['Fecha'], df_plot['Profit_Acumulado'] / 10, color='#ff00ff', linewidth=3, label='Profit Acumulado (x10 %)')
    # Nota: Divido por 10 o escalo para que sea visible junto al Q-Score que es de -1 a 1
    
    # 4. Formato y Detalles
    ax2.set_ylabel('Q-Score / Profit Relativo', color='white', fontsize=12)
    ax2.set_ylim(-1.2, 1.2) # Mantenemos el foco en el rango del oráculo
    ax2.axhline(0, color='white', linewidth=0.8, alpha=0.3)

    # Títulos con info dinámica
    total_profit = df['Profit_Acumulado'].iloc[-1]
    plt.title(f'Oráculo 128Q | Profit Total: {total_profit:+.2f}% | Precisión 10k Shots', fontsize=15, pad=20, color='white')

    # Formato de fecha
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=30)

    # Leyenda única unificada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=False)

    plt.grid(True, alpha=0.05)
    plt.tight_layout()
    
    # Guardado
    plt.savefig('rendimiento_cuantico.png', dpi=150)
    plt.close()
    print(f"📊 Gráfica actualizada. Profit acumulado actual: {total_profit:+.2f}%")

if __name__ == "__main__":
    generar_grafica()
