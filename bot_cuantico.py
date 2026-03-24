import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONEXIÓN (Qiskit 1.x) ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Inicializamos el servicio moderno
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    
    # En Qiskit 1.x, PennyLane prefiere que usemos nombres de backend
    # Usamos el simulador por defecto para asegurar que el DNS no falle en el primer intento
    backend_name = "ibmq_qasm_simulator"
    
    # Nuevo conector PennyLane-Qiskit compatible con 1.x
    dev = qml.device('qiskit.remote', wires=5, backend=backend_name, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        # Codificación simple pero efectiva
        for i in range(len(datos)):
            qml.RY(datos[i], wires=i)
        qml.CNOT(wires=[0, 4])
        return qml.expval(qml.PauliZ(4))

    print(f"✅ Sistema Cuántico 1.x Iniciado en {backend_name}")
except Exception as e:
    print(f"❌ Error de inicialización: {e}")
    exit(1)

# --- 2. DATOS DE MERCADO ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False)
    # Tomamos variaciones porcentuales para el ADN
    cambios = df['Close'].pct_change().dropna().tail(4).values * 100
    adn = [np.arctan(x) for x in cambios] # Convertimos a ángulos
    
    # Ejecución
    resultado = float(oraculo_cuantico(adn))
except Exception as e:
    print(f"❌ Error en datos: {e}")
    exit(1)

# --- 3. PERSISTENCIA ---
archivo = 'backtest_cuantico.csv'
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': round(float(df['Close'].iloc[-1]), 2)
}])

if os.path.exists(archivo):
    df_old = pd.read_csv(archivo)
    pd.concat([df_old, nueva_fila], ignore_index=True).to_csv(archivo, index=False)
else:
    nueva_fila.to_csv(archivo, index=False)

print(f"🚀 Predicción guardada con éxito: {resultado}")
