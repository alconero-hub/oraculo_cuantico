import pandas as pd
import matplotlib.pyplot as plt
import os

def generar_grafica():
    archivo = 'backtest_cuantico.csv'
    if not os.path.exists(archivo): return

    df = pd.read_csv(archivo)
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values('Fecha').tail(50) 

    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Eje Precio BTC
    ax1.set_ylabel('Precio BTC ($)', color='orange')
    ax1.plot(df['Fecha'], df['Precio'], color='orange', linewidth=2, label='BTC Price')
    ax1.tick_params(axis='y', labelcolor='orange')
    
    # Eje Veredicto
    ax2 = ax1.twinx()
    colores = ['green' if x > 0.15 else 'red' if x < -0.15 else 'gray' for x in df['Veredicto']]
    ax2.bar(df['Fecha'], df['Veredicto'], color=colores, alpha=0.3, width=0.02, label='Quantum Signal')
    ax2.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Señal Cuántica')
    ax2.set_ylim(-1.1, 1.1)

    plt.title('Evolución del Oráculo Cuántico (Ahorro de QPU incluido)')
    plt.savefig('rendimiento_cuantico.png')

if __name__ == "__main__":
    generar_grafica()
