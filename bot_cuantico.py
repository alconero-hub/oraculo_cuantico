Ese error es un clásico de PennyLane 0.35+ cuando se comunica con hardware real. Ocurre porque, al medir en una QPU física, PennyLane a veces devuelve el resultado como un array de NumPy (con un solo valor, pero array al fin y al cabo) y la función float() de Python se confunde al intentar convertirlo.

Para arreglarlo, debemos usar .item() o asegurarnos de que el resultado sea tratado como un escalar de NumPy antes de la conversión.

🛠️ El bot_cuantico.py Corregido (Hardware Real)
He aplicado la corrección en la línea del resultado y he añadido un pequeño "filtro de seguridad" para el ADN, ya que a veces los datos de Yahoo Finance pueden dar problemas de formato al entrar en el circuito cuántico.

Python
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
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    # Buscamos el chip real con menos cola
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    
    print(f"📡 Conectando a procesador cuántico real: {backend.name}")
    
    dev = qml.device('qiskit.remote', 
                     wires=5, 
                     backend=backend, 
                     shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i) # Forzamos float aquí también
        
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
        print("⚠️ No hay datos."); exit(0)
        
    ultimo_p = float(df['Close'].iloc[-1])
    cambios = df['Close'].pct_change().dropna().tail(4).values * 100
    adn = [np.arctan(x) for x in cambios]
    
    print("🧠 Ejecutando en hardware de IBM (esto puede tardar por la cola)...")
    
    # CORRECCIÓN AQUÍ: Usamos np.array(...).item() para evitar el error de scalar
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

print(f"🚀 [REAL QPU] Veredicto guardado: {resultado:+.4f} | Precio: ${ultimo_p}")
