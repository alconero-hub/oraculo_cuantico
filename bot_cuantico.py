import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Importaciones protegidas
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONEXIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Usamos el canal oficial de IBM Quantum
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    # Intentamos obtener un backend real, si falla usamos simulador para no romper el flujo
    try:
        backend = service.least_busy(operational=True, simulator=False)
        backend_name = backend.name
    except:
        backend_name = "ibmq_qasm_simulator"
    
    # Dispositivo PennyLane con el conector de Qiskit
    dev = qml.device('qiskit.remote', wires=5, backend=backend_name, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos, pesos):
        for i in range(4): qml.RY(datos[i], wires=i)
        for i in range(4): qml.CNOT(wires=[i, 4])
        qml.RY(pesos, wires=4)
        return qml.expval(qml.PauliZ(4))

    print(f"✅ Conectado a: {backend_name}")
except Exception as e:
    print(f"❌ Fallo de conexión: {e}")
    exit(1)

# --- 2. DATOS Y ESTRATEGIA ---
data = yf.download("BTC-USD", period="2d", interval="15m", progress=False)
if data.empty: exit(1)

ultimo_p = float(data['Close'].iloc[-1])
# ADN: Relación de precios actuales vs pasados
adn = [np.arctan(ultimo_p/data['Close'].iloc[-i]) for i in range(2, 6)]

# Ejecución del oráculo
resultado = float(oraculo_cuantico(adn, 0.5))

# --- 3. GUARDADO ---
archivo = 'backtest_cuantico.csv'
# Crear DataFrame con la predicción
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': round(ultimo_p, 2)
}])

# Leer existente o crear nuevo
if os.path.exists(archivo):
    df = pd.read_csv(archivo)
    df = pd.concat([df, nueva_fila], ignore_index=True)
else:
    df = nueva_fila

df.to_csv(archivo, index=False)
print(f"🚀 Predicción guardada: {resultado:+.4f}")
