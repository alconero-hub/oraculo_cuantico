import os
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN SEGURA
token = os.getenv("IBM_QUANTUM_TOKEN")
service = QiskitRuntimeService(channel="ibm_quantum", token=token)
backend = service.least_busy(simulator=False, min_num_qubits=5)

dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

@qml.qnode(dev)
def oraculo(datos, pesos):
    for i in range(4): qml.RY(datos[i], wires=i)
    for i in range(4): qml.CNOT(wires=[i, 4])
    for i in range(5): qml.RX(pesos[i], wires=i)
    return qml.expval(qml.PauliZ(0))

# 2. LÓGICA DE DATOS (Filtro de volatilidad incluido)
data = yf.download("BTC-USD", period="5d", interval="15m", progress=False)
ultimo, previo = data['Close'].iloc[-1], data['Close'].iloc[-2]
volatilidad = abs((ultimo - previo) / previo) * 100

if volatilidad > 0.10:
    def calc_fase(df, p1, p2): return float(np.arctan(df['Close'].iloc[p1] / df['Close'].iloc[p2]))
    señal = [calc_fase(data,-1,-2), calc_fase(data,-1,-96), 0.1, 0.1] # ADN simplificado
    pesos = np.array([1.8, -0.5, 0.6, 1.2, -1.0])
    
    res = float(oraculo(señal, pesos))
    
    # 3. GUARDAR RESULTADO
    archivo = 'backtest_cuantico.csv'
    nueva_fila = pd.DataFrame([{'Fecha': datetime.now(), 'Q0': res, 'Precio': ultimo}])
    df = pd.read_csv(archivo) if os.path.exists(archivo) else pd.DataFrame()
    pd.concat([df, nueva_fila]).to_csv(archivo, index=False)
    print(f"✅ Ejecución exitosa: {res}")
else:
    print("💤 Mercado lateral, saltando ejecución.")
