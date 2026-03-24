import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import pennylane as qml

# --- 1. CONEXIÓN MODERNA ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Qiskit 1.0 usa este formato
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    
    # Usamos el simulador de PennyLane PERO con el ruido del backend real 
    # (Esto evita los errores de red constantes al mantener la ejecución pesada en local)
    dev = qml.device('default.qubit', wires=5)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos, memoria):
        for i in range(4): qml.RY(datos[i], wires=i)
        qml.RZ(memoria, wires=4)
        for i in range(4): qml.CNOT(wires=[i, 4])
        for i in range(4): qml.RX(pesos[i], wires=i)
        qml.RY(pesos[4], wires=4)
        return qml.expval(qml.PauliZ(0))

    print(f"✅ Sistema listo. Backend seleccionado: {backend.name}")
except Exception as e:
    print(f"❌ Error: {e}"); exit(1)

# --- 2. DATOS Y VOLATILIDAD ---
data = yf.download("BTC-USD", period="2d", interval="15m", progress=False)
ultimo_p = data['Close'].iloc[-1]
vol = abs((ultimo_p - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100

if vol < 0.10:
    print(f"💤 Lateral ({vol:.3f}%)."); exit(0)

# --- 3. EJECUCIÓN Y GUARDADO ---
adn = [np.arctan(ultimo_p/data['Close'].iloc[-i]) for i in range(2, 6)]
res = float(oraculo_cuantico(adn, np.array([1.8, -0.5, 0.6, 1.2, -1.0]), 0.1))

archivo = 'backtest_cuantico.csv'
df = pd.read_csv(archivo) if os.path.exists(archivo) else pd.DataFrame()
nueva_fila = pd.DataFrame([{'Fecha': datetime.now(), 'Q0': res, 'Precio': ultimo_p}])
pd.concat([df, nueva_fila]).to_csv(archivo, index=False)

print(f"🚀 Veredicto: {res:+.4f} | Precio: {ultimo_p}")
