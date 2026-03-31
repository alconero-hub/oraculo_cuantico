import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- CONFIGURACIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_32.npy"
N_QUBITS = 32

def gestionar_memoria(n_qubits=32):
    if os.path.exists(PESOS_FILE):
        return np.load(PESOS_FILE)
    else:
        # 32 qubits x 2 parámetros (RY, RZ)
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def ejecutar_oraculo():
    try:
        # 1. Datos de Mercado (32 velas de 15 min = 8 horas)
        print("📈 Analizando ventana de 8 horas (32 intervalos)...")
        df = yf.download("BTC-USD", period="2d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        cambios = precios.pct_change().dropna().tail(N_QUBITS).values
        vol = np.mean(np.abs(cambios)) * 100

        # Filtro de Volatilidad (Ahorro de QPU)
        if vol < 0.01:
            print(f"😴 Baja volatilidad ({vol:.4f}%). El oráculo sigue durmiendo.")
            return 0.0, ultimo_p, vol, "Standby (Filtro 0.04%)"

        if len(cambios) < N_QUBITS:
            print("⚠️ Faltan datos para 32 qubits.")
            return None

        # 2. Conexión IBM
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        try:
            # Buscamos hardware potente (mínimo 32 qubits)
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=N_QUBITS)
            print(f"📡 Hardware: {backend.name}")
            dev = qml.device('qiskit.remote', wires=N_QUBITS, backend=backend, shots=1024)
        except:
            print("⚠️ Usando simulador (No hay QPU de 32Q libre)")
            dev = qml.device('default.qubit', wires=N_QUBITS)
            backend = type('obj', (object,), {'name': 'Simulator-32Q'})

        pesos_memoria = gestionar_memoria(N_QUBITS)

        @qml.qnode(dev)
        def circuito_32q(datos, pesos):
            # Codificación
            for i in range(N_QUBITS):
                qml.RX(float(datos[i]), wires=i)
            # Aprendizaje
            for i in range(N_QUBITS):
                qml.RY(float(pesos[i][0]), wires=i)
                qml.RZ(float(pesos[i][1]), wires=i)
            # Entrelazamiento Multicapa
            for i in range(N_QUBITS - 1):
                qml.CNOT(wires=[i, i+1]) # Vecinos
            for i in range(0, N_QUBITS - 4, 4):
                qml.CNOT(wires=[i, i+4]) # Saltos largos
            
            return qml.expval(qml.PauliZ(16)) # Medida en el centro absoluto

        adn = [np.arctan(x * 100) for x in cambios]
        res = float(circuito_32q(adn, pesos_memoria))

        # Aprendizaje Reforzado (LR 0.08 para adaptación rápida)
        mov_real = np.mean(cambios) * 100
        error = (mov_real - res)
        np.save(PESOS_FILE, pesos_memoria + (error * 0.08))

        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    # Definición de señales
    if res > 0.60: est, col, emo = "🚀 **COMPRA FUERTE**", "brightgreen", "🔥"
    elif res > 0.15: est, col, emo = "🟢 **COMPRA**", "green", "📈"
    elif res < -0.60: est, col, emo = "💀 **VENTA FUERTE**", "red", "📉"
    elif res < -0.15: est, col, emo = "🔴 **VENTA**", "orange", "⚠️"
    else: est, col, emo = "🟡 **ESPERA**", "yellow", "⏳"

    # Si es modo ahorro
    if b_name.startswith("Standby"):
        est, emo = "💤 **MERCADO CALMADO**", "😴"

    contenido = f"""# 🌌 Oráculo Cuántico BTC (32-Qubits)
![Señal](https://img.shields.io/badge/ORÁCULO-{est.replace(' ', '%20').replace('*','')}-{col}?style=for-the-badge)

## 🚦 Veredicto: {emo} {est}
* **Precio Actual:** `${precio:,.2f}` | **Q-Score:** `{res:+.4f}`
* **Hardware:** `{b_name}` (32 Cúbits Activos)
* **Ventana de Análisis:** 8 Horas (32x15m)
* **Volatilidad:** `{vol:.4f}%`
* **Actualizado:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---
## 📈 Historial
![Gráfica](./rendimiento_cuantico.png)

---
*Procesado con Arquitectura de Entrelazamiento Multicapa 32Q.*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(contenido)

if __name__ == "__main__":
    resultado = ejecutar_oraculo()
    if resultado:
        res, p, v, b = resultado
        actualizar_readme(res, p, v, b)
        # CSV log
        log = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': res, 'Precio': p}])
        if os.path.exists('backtest_cuantico.csv'):
            pd.concat([pd.read_csv('backtest_cuantico.csv'), log]).to_csv('backtest_cuantico.csv', index=False)
        else:
            log.to_csv('backtest_cuantico.csv', index=False)
