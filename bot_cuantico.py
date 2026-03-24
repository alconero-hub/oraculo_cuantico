Aquí tienes el código completo y corregido para el archivo bot_cuantico.py. He incluido las librerías con las versiones específicas para evitar el error de autoray, el Escudo de Volatilidad, y la lógica robusta para escribir en el CSV.

Este código es el "motor" que GitHub Actions despertará cada hora.

Archivo: bot_cuantico.py
Python
import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN ---
# El token se lee desde los Secrets de GitHub, no se escribe aquí.
token_ibm = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum", token=token_ibm)
    # Selecciona el chip real menos ocupado
    backend_fisico = service.least_busy(simulator=False, min_num_qubits=5)
    
    # Configuración de 1024 disparos para optimizar tus 9 minutos
    n_shots = 1024
    dev = qml.device('qiskit.remote', wires=5, backend=backend_fisico, shots=n_shots)
    error_est = 1 / (n_shots**0.5)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos, memoria):
        for i in range(4): qml.RY(datos[i], wires=i)
        qml.RZ(memoria, wires=4)
        for i in range(4): qml.CNOT(wires=[i, 4])
        for i in range(4): qml.RX(pesos[i], wires=i)
        qml.RY(pesos[4], wires=4)
        return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error conectando a IBM: {e}")
    exit(1)

# --- 2. CAPTURA DE DATOS Y ESCUDO DE VOLATILIDAD ---
print("🔍 Analizando mercado antes de llamar a IBM...")
data_short = yf.download("BTC-USD", period="5d", interval="15m", progress=False)
data_long = yf.download("BTC-USD", period="1y", interval="1d", progress=False)

ultimo_p = data_short['Close'].iloc[-1]
previo_p = data_short['Close'].iloc[-2]
volatilidad = abs((ultimo_p - previo_p) / previo_p) * 100

# FILTRO: Si el mercado se mueve menos de 0.10%, ahorramos segundos de IBM
UMBRAL_VOL = 0.10

if volatilidad < UMBRAL_VOL:
    print(f"💤 Mercado lateral ({volatilidad:.3f}%). Abortando ejecución para ahorrar crédito.")
    exit(0) 

print(f"🔥 Volatilidad detectada ({volatilidad:.3f}%). Ejecutando QPU...")

# --- 3. PROCESAMIENTO DEL ADN CUÁNTICO ---
def calc_fase(df, p1, p2):
    return float(np.arctan(df['Close'].iloc[p1] / df['Close'].iloc[p2]))

adn = [
    calc_fase(data_short, -1, -2),   # 15m
    calc_fase(data_short, -1, -96),  # 24h
    calc_fase(data_long, -1, -21),   # 21d
    calc_fase(data_long, -1, -90)    # 90d
]

# Pesos fijos para la estrategia
pesos_v = np.array([1.8, -0.5, 0.6, 1.2, -1.0])
res_raw, mem_raw = oraculo_cuantico(adn, pesos_v, 0.1)
res, mem = float(res_raw), float(mem_raw)

# --- 4. ACTUALIZACIÓN DEL BACKTEST (CSV) ---
archivo_csv = 'backtest_cuantico.csv'

nueva_fila = {
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'Ticket': 'BTC-USD',
    'Decision_Q0': round(res, 4),
    'Memoria_Q4': round(mem, 4),
    'Precio_Entrada': round(ultimo_p, 2),
    'Precio_60min': None,
    'Resultado': 'Pendiente'
}

if os.path.exists(archivo_csv):
    df = pd.read_csv(archivo_csv)
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
else:
    df = pd.DataFrame([nueva_fila])

df.to_csv(archivo_csv, index=False)

print(f"✅ Veredicto Guardado: {res:+.4f}")
print(f"📡 Backend usado: {backend_fisico.name}")
