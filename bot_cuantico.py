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
    # Inicializamos el servicio
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    
    # BUSCAR MÁQUINA REAL: Filtramos para excluir simuladores y buscar el menos ocupado
    # operational=True (que esté encendida)
    # simulator=False (que sea hardware real)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    
    print(f"📡 Conectando a procesador cuántico real: {backend.name}")
    print(f"⏳ Trabajos en cola: {backend.status().pending_jobs}")

    # Definimos el dispositivo PennyLane apuntando al chip físico
    dev = qml.device('qiskit.remote', 
                     wires=5, 
                     backend=backend, 
                     shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        # Codificación de datos en rotaciones de fase
        for i in range(len(datos)):
            qml.RY(datos[i], wires=i)
        
        # Entrelazamiento máximo (Capa de cómputo real)
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
        qml.CNOT(wires=[3, 4])
        
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error al acceder a la QPU: {e}")
    exit(1)

# --- 2. DATOS DE MERCADO ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False)
    if df.empty:
        print("⚠️ No hay datos.")
        exit(0)
        
    # ADN Cuántico: Cambios porcentuales normalizados
    cambios = df['Close'].pct_change().dropna().tail(4).values * 100
    adn = [np.arctan(x) for x in cambios]
    
    # EJECUCIÓN EN CHIP REAL (Esto puede tardar unos minutos dependiendo de la cola)
    print("🧠 Calculando veredicto en hardware de IBM...")
    resultado = float(oraculo_cuantico(adn))
    
except Exception as e:
    print(f"❌ Error en el proceso: {e}")
    exit(1)

# --- 3. REGISTRO DE RESULTADOS ---
archivo = 'backtest_cuantico.csv'
precio_actual = round(float(df['Close'].iloc[-1]), 2)
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': precio_actual,
    'Backend': backend.name
}])

if os.path.exists(archivo):
    df_old = pd.read_csv(archivo)
    pd.concat([df_old, nueva_fila], ignore_index=True).to_csv(archivo, index=False)
else:
    nueva_fila.to_csv(archivo, index=False)

print(f"🚀 [REAL QPU] Predicción guardada: {resultado} | BTC: ${precio_actual}")
