import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
token_ibm = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Inicializamos el servicio (Versión compatible con 0.45)
    service = QiskitRuntimeService(channel="ibm_quantum", token=token_ibm)
    
    # Buscamos el procesador real con menos cola
    backend_fisico = service.least_busy(simulator=False, min_num_qubits=5)
    
    # Definimos el dispositivo usando el nombre del backend
    n_shots = 1024
    dev = qml.device('qiskit.remote', 
                     wires=5, 
                     backend=backend_fisico.name, 
                     shots=n_shots)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos, memoria):
        # Capa ADN
        for i in range(4): qml.RY(datos[i], wires=i)
        # Memoria y Entrelazamiento
        qml.RZ(memoria, wires=4)
        for i in range(4): qml.CNOT(wires=[i, 4])
        # Capa Variacional
        for i in range(4): qml.RX(pesos[i], wires=i)
        qml.RY(pesos[4], wires=4)
        return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(4))

    print(f"✅ Conectado a: {backend_fisico.name}")

except Exception as e:
    print(f"❌ Error crítico de inicialización: {e}")
    exit(1)

# --- 2. ESCUDO DE VOLATILIDAD ---
print("🔍 Analizando mercado...")
data_short = yf.download("BTC-USD", period="5d", interval="15m", progress=False)
data_long = yf.download("BTC-USD", period="1y", interval="1d", progress=False)

ultimo_p = float(data_short['Close'].iloc[-1])
previo_p = float(data_short['Close'].iloc[-2])
volatilidad = abs((ultimo_p - previo_p) / previo_p) * 100

# Umbral 0.10% para ahorrar tus 9 minutos de Trial
UMBRAL_VOL = 0.10

if volatilidad < UMBRAL_VOL:
    print(f"💤 MERCADO LATERAL ({volatilidad:.3f}%). Abortando para ahorrar Trial.")
    exit(0) 

print(f"🔥 MOVIMIENTO DETECTADO. Ejecutando QPU...")

# --- 3. PROCESAMIENTO CUÁNTICO ---
def calc_fase(df, p1, p2):
    return float(np.arctan(df['Close'].iloc[p1] / df['Close'].iloc[p2]))

adn = [calc_fase(data_short,-1,-2), calc_fase(data_short,-1,-96), 
       calc_fase(data_long,-1,-21), calc_fase(data_long,-1,-90)]

pesos_v = np.array([1.8, -0.5, 0.6, 1.2, -1.0])
res_raw, mem_raw = oraculo_cuantico(adn, pesos_v, 0.1)
res, mem = float(res_raw), float(mem_raw)

# --- 4. GUARDADO EN CSV ---
archivo_csv = 'backtest_cuantico.csv'
nueva_fila = {
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'Ticket': 'BTC-USD',
    'Decision_Q0': round(res, 4),
    'Precio_Entrada': round(ultimo_p, 2),
    'Resultado': 'Pendiente'
}

if os.path.exists(archivo_csv):
    df = pd.read_csv(archivo_csv)
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
else:
    df = pd.DataFrame([nueva_fila])

df.to_csv(archivo_csv, index=False)
print(f"✅ Registro completado. Veredicto: {res:+.4f}")
