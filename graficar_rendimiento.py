import pandas as pd
import matplotlib.pyplot as plt
import os

def generar_grafica():
    archivo = 'backtest_cuantico.csv'
    
    if not os.path.exists(archivo):
        print("❌ No hay datos para graficar todavía.")
        return

    # 1. Cargar datos
    df = pd.read_csv(archivo)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha')

    # 2. Configurar la figura
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Eje Izquierdo: Precio de BTC
    color_precio = 'tab:orange'
    ax1.set_xlabel('Fecha / Hora')
    ax1.set_ylabel('Precio BTC-USD ($)', color=color_precio)
    ax1.plot(df['Fecha'], df['Precio'], color=color_precio, linewidth=2, label='Precio BTC')
    ax1.tick_params(axis='y', labelcolor=color_precio)
    ax1.grid(True, alpha=0.3)

    # Eje Derecho: Veredicto Cuántico
    ax2 = ax1.twinx()
    color_veredicto = 'tab:blue'
    ax2.set_ylabel('Veredicto Cuántico (PauliZ)', color=color_veredicto)
    
    # Dibujamos barras para el veredicto (verde si > 0, rojo si < 0)
    colores_barras = ['green' if x > 0 else 'red' for x in df['Veredicto']]
    ax2.bar(df['Fecha'], df['Veredicto'], color=colores_barras, alpha=0.4, width=0.01, label='Veredicto')
    ax2.axhline(0, color='black', linestyle='--', linewidth=0.8) # Línea de neutralidad
    ax2.tick_params(axis='y', labelcolor=color_veredicto)

    # Título y ajustes
    plt.title('🤖 Oráculo Cuántico: Correlación Precio vs Veredicto')
    fig.tight_layout()
    
    # Guardar la imagen
    plt.savefig('rendimiento_cuantico.png')
    print("✅ Gráfica guardada como 'rendimiento_cuantico.png'")

if __name__ == "__main__":
    generar_grafica()
