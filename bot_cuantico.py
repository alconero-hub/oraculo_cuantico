import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService

# --- 1. CONFIGURACIÓN DE CONEXIÓN (Modo Estabilidad 0.45) ---
token_ibm = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Inicializamos el servicio de IBM
    service = QiskitRuntimeService(channel="ibm_quantum", token=token_ibm)
    
    # Buscamos el procesador real con menos cola
    backend_fisico = service.least_busy(simulator=False, min_num_qubits=5)
    
    # Definimos el dispositivo usando el nombre del backend (vital para evitar conflictos)
    n_shots = 1024
    dev = qml.device('qiskit.remote', 
                     wires=5, 
                     backend=backend_fisico.name, 
                     shots=n_shots)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos, memoria):
        # Capa de carga de datos (ADN)
        for i in range(4): qml.RY(datos[i], wires=i)
        # Capa de memoria y entrelazamiento
        qml.RZ(memoria, wires=4)
        for i in range(4): qml.CNOT(wires=[i, 4])
        # Capa variacional (Pesos)
        for i in range(4): qml.RX(pesos[i], wires=i)
        qml.RY(pesos[4], wires=4)
        return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(4))

    print(f"✅ Conexión exitosa al procesador: {backend_fisico.name}")

except Exception as e:
    print(f"❌ Error crítico de inicialización: {e}")
    exit(1)

# --- 2. ESCUDO DE VOLATILIDAD ---
print("🔍 Analizando agitación del mercado...")
data_short = yf.download("BTC-USD", period="5d", interval="15m", progress=False)
data_long = yf.download("BTC-USD", period="1y", interval="1d", progress=False)

if data_short.empty or len(data_short) < 2:
    print("⚠️ No se pudieron obtener datos de Yahoo Finance.")
    exit(1)

ultimo_p = float(data_short['Close'].iloc[-1])
previo_p = float(data_short['Close'].iloc[-2])
volatilidad = abs((ultimo_p - previo_p) / previo_p) * 100

# Umbral de activación (0.10% para no quemar segundos de IBM en lateral)
UMBRAL_VOL = 0.10

if volatilidad < UMBRAL_VOL:
    print(f"💤 MERCADO LATERAL ({volatilidad:.3f}%). Abortando para ahorrar Trial.")
    exit(0) 

print(f"🔥 VOLATILIDAD DETECTADA ({volatilidad:.3f}%). Ejecutando QPU...")

# --- 3. PROCESAMIENTO DE ADN CUÁNTICO ---
def calc_fase(df, p1, p2):
    return float(np.arctan(df['Close'].iloc[p1] / df['Close'].iloc[p2]))

adn = [
    calc_fase(data_short, -1, -2),   # Inercia 15m
    calc_fase(data_short, -1, -96),  # Inercia 24h
    calc_fase(data_long, -1, -21),   # Inercia 21d
    calc_fase(data_long, -1, -90)    # Inercia 90d
]

# Pesos optimizados (Trial)
pesos_v = np.array([1.8, -0.5, 0.6, 1.2, -1.0])
res_raw, mem_raw = oraculo_cuantico(adn, pesos_v, 0.1)
res, mem = float(res_raw), float(mem_raw)

# --- 4. GUARDADO EN BASE DE DATOS (CSV) ---
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
    try:
        df = pd.read_csv(archivo_csv)
        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    except:
        df = pd.DataFrame([nueva_fila])
else:
    df = pd.DataFrame([nueva_fila])

df.to_csv(archivo_csv, index=False)

print("-" * 30)
print(f"📊 REGISTRO COMPLETADO")
print(f"Veredicto: {res:+.4f}")
print(f"Precio BTC: ${ultimo_p:,.2f}")
print("-" * 30)
