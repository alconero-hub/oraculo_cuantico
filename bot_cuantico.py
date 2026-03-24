import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService

# --- CONFIGURACIÓN DE CONEXIÓN ---
token_ibm = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum", token=token_ibm)
    backend_fisico = service.least_busy(simulator=False, min_num_qubits=5)
    dev = qml.device('qiskit.remote', wires=5, backend=backend_fisico.name, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos, memoria):
        for i in range(4): qml.RY(datos[i], wires=i)
        qml.RZ(memoria, wires=4)
        for i in range(4): qml.CNOT(wires=[i, 4])
        for i in range(4): qml.RX(pesos[i], wires=i)
        qml.RY(pesos[4], wires=4)
        return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(4))
    print(f"✅ Conectado a: {backend_fisico.name}")
except Exception as e:
    print(f"❌ Error IBM: {e}"); exit(1)

# --- ESCUDO DE VOLATILIDAD ---
data = yf.download("BTC-USD", period="5d", interval="15m", progress=False)
vol = abs((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100

if vol < 0.10:
    print(f"💤 Lateral ({vol:.3f}%). Fin."); exit(0)

# --- CÁLCULO ---
adn = [np.arctan(data['Close'].iloc[-1]/data['Close'].iloc[-2]), 0.1, 0.1, 0.1]
res, mem = oraculo_cuantico(adn, np.array([1.8, -0.5, 0.6, 1.2, -1.0]), 0.1)

# --- GUARDADO ---
archivo_csv = 'backtest_cuantico.csv'
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'Q0': round(float(res), 4),
    'Precio': round(float(data['Close'].iloc[-1]), 2)
}])

# En Docker, el archivo siempre está en /app/ (WORKDIR)
df = pd.read_csv(archivo_csv) if os.path.exists(archivo_csv) else pd.DataFrame()
pd.concat([df, nueva_fila], ignore_index=True).to_csv(archivo_csv, index=False)
print(f"✅ Registro guardado: {res}")
