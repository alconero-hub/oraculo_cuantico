import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

def generar_grafica():
    if not os.path.exists('backtest_cuantico.csv'):
        print("❌ No hay datos para graficar.")
        return

    # 1. Carga y limpieza de datos
    df = pd.read_csv('backtest_cuantico.csv')
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha').tail(100) # Mostramos los últimos 100 registros

    # 2. Configuración de estilo
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(12, 7))
    ax2 = ax1.twinx()

    # --- EJE 1: PRECIO DE BTC (Línea Neón) ---
    ax1.plot(df['Fecha'], df['Precio'], color='#00ffcc', linewidth=2, label='Precio BTC ($)', alpha=0.8)
    ax1.fill_between(df['Fecha'], df['Precio'], alpha=0.1, color='#00ffcc')
    ax1.set_ylabel('Precio BTC (USD)', color='#00ffcc', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#00ffcc')

    # --- EJE 2: VEREDICTO CUÁNTICO (Barras) ---
    # Definimos colores basados en la intensidad y el umbral de 0.05
    colores = []
    for v in df['Veredicto']:
        if abs(v) < 0.01: colores.append('#444444') # Standby / Lateral
        elif v > 0.6: colores.append('#00ff00')     # Compra Fuerte
        elif v > 0.15: colores.append('#77ff77')    # Compra
        elif v < -0.6: colores.append('#ff0000')    # Venta Fuerte
        elif v < -0.15: colores.append('#ff7777')   # Venta
        else: colores.append('#ffff00')             # Espera (Amarillo)

    # Dibujamos las barras del veredicto
    ax2.bar(df['Fecha'], df['Veredicto'], color=colores, width=0.03, label='Q-Score', alpha=0.6)
    
    # Añadimos una media móvil del veredicto para ver la "inteligencia" acumulada
    df['MA_Veredicto'] = df['Veredicto'].rolling(window=5).mean()
    ax2.plot(df['Fecha'], df['MA_Veredicto'], color='white', linestyle='--', linewidth=1, alpha=0.5, label='Tendencia Q')

    ax2.set_ylabel('Confianza Cuántica (Q-Score)', color='white', fontsize=12)
    ax2.set_ylim(-1.1, 1.1) # El Q-Score siempre va de -1 a 1
    ax2.axhline(0, color='white', linewidth=0.5, alpha=0.3)
    ax2.axhline(0.15, color='green', linewidth=0.8, linestyle=':', alpha=0.4)
    ax2.axhline(-0.15, color='red', linewidth=0.8, linestyle=':', alpha=0.4)

    # --- FORMATO FINAL ---
    plt.title(f'Oráculo Cuántico 128Q | Ventana 32h | Precisión 10k Shots', fontsize=14, pad=20)
    
    # Formato de fecha en el eje X
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=30)
    
    # Leyendas
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=False)

    plt.grid(True, alpha=0.1)
    plt.tight_layout()
    
    # Guardar
    plt.savefig('rendimiento_cuantico.png', dpi=150)
    plt.close()
    print("📈 Gráfica de 128 Cúbits actualizada en 'rendimiento_cuantico.png'")

if __name__ == "__main__":
    generar_grafica()
