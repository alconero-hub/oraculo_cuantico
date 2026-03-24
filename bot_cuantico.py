import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONEXIÓN A QPU REAL ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    # Buscamos el chip real con menos cola
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    
    print(f"📡 Conectando a procesador cuántico real: {backend.name}")
    
    dev = qml.device('qiskit.remote', 
                     wires=5, 
                     backend=backend, 
                     shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        # Convertimos cada dato a float puro para evitar errores en el QNode
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i)
        
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
        qml.CNOT(wires=[3, 4])
        
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de inicialización: {e}")
    exit(1)

# --- 2. DATOS DE MERCADO ---
try:
    # Descargamos un poco más de margen para asegurar que tenemos datos suficientes
    df = yf.download("BTC-USD", period="2d", interval="15m", progress=False)
    if df.empty or len(df) < 5:
        print("⚠️ Datos insuficientes en Yahoo Finance."); exit(0)
        
    # EXTRACCIÓN SEGURA: Usamos .iloc[-1] y forzamos a float escalar
    ultimo_p = float(df['Close'].iloc[-1])
    
    # ADN: Cambios porcentuales de las últimas 4 velas
    cambios = df['Close'].pct_change().dropna().tail(4).values
    adn = [np.arctan(float(x) * 100) for x in cambios]
    
    print(f"🧠 BTC Actual: ${ultimo_p} | Ejecutando en {backend.name}...")
    
    # EJECUCIÓN: Convertimos el resultado de PennyLane a escalar puro
    raw_res = oraculo_cuantico(adn)
    resultado = float(np.array(raw_res).item())
    
except Exception as e:
    print(f"❌ Error en el proceso: {e}")
    exit(1)

# --- 3. REGISTRO ---
archivo = 'backtest_cuantico.csv'
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': round(ultimo_p, 2),
    'Backend': backend.name
}])

if os.path.exists(archivo):
    df_old = pd.read_csv(archivo)
    pd.concat([df_old, nueva_fila], ignore_index=True).to_csv(archivo, index=False)
else:
    nueva_fila.to_csv(archivo, index=False)

print(f"🚀 [ÉXITO] Veredicto: {resultado:+.4f} | Guardado en CSV.")
