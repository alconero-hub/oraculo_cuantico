import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONEXIÓN (Usando el nuevo canal solicitado) ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Cambiado a ibm_quantum_platform según tu instrucción
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    
    print(f"📡 Hardware Real: {backend.name} | Canal: ibm_quantum_platform")
    
    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i)
        for i in range(4):
            qml.CNOT(wires=[i, 4])
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de inicialización: {e}"); exit(1)

# --- 2. DATOS DE MERCADO (Extracción Anti-Errores) ---
try:
    # Forzamos auto_adjust=True para evitar columnas extrañas
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    
    if df.empty:
        print("⚠️ No hay datos."); exit(0)

    # LIMPIEZA CRÍTICA: Convertimos a Serie plana y tomamos los últimos valores
    # Esto elimina cualquier MultiIndex o estructura de Series que cause el error
    precios = df['Close'].squeeze() 
    
    if isinstance(precios, pd.DataFrame): # Si sigue siendo DataFrame, tomamos la primera columna
        precios = precios.iloc[:, 0]

    ultimo_p = float(precios.iloc[-1])
    
    # Calculamos cambios y ADN
    cambios = precios.pct_change().dropna().tail(4).values
    adn = [np.arctan(float(x) * 100) for x in cambios]
    
    print(f"🧠 Datos procesados. BTC: ${ultimo_p:.2f}. Enviando a QPU...")
    
    # Ejecución con conversión segura
    raw_res = oraculo_cuantico(adn)
    resultado = float(np.array(raw_res).item())
    
except Exception as e:
    print(f"❌ Error en el proceso: {e}"); exit(1)

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

print(f"🚀 [OK] Guardado: {resultado:+.4f}")
