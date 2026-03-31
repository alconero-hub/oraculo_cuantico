import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- CONFIGURACIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_128.npy"
N_QUBITS = 128

def gestionar_memoria(n_qubits=128):
    if os.path.exists(PESOS_FILE):
        return np.load(PESOS_FILE)
    else:
        # 128 qubits x 2 parámetros (RY, RZ)
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def ejecutar_oraculo():
    try:
        # 1. Datos de Mercado (128 velas de 15 min = 32 horas)
        print(f"📈 Analizando ventana de 32 horas ({N_QUBITS} intervalos)...")
        df = yf.download("BTC-USD", period="5d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        cambios = precios.pct_change().dropna().tail(N_QUBITS).values
        vol = np.mean(np.abs(cambios)) * 100

        # Filtro de Volatilidad Estructural
        if vol < 0.01:
            print(f"😴 Mercado en hibernación ({vol:.4f}%).")
            return 0.0, ultimo_p, vol, "Standby (Filtro 0.06%)"

        if len(cambios) < N_QUBITS:
            print("⚠️ Datos insuficientes para 128Q.")
            return None

        # 2. Conexión IBM (Buscamos sistemas de gran escala)
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        try:
            # Intentamos buscar procesadores de 127 qubits o más (Eagle/Heron)
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=N_QUBITS)
            print(f"📡 Hardware: {backend.name}")
            dev = qml.device('qiskit.remote', wires=N_QUBITS, backend=backend, shots=4096)
        except:
            print("⚠️ No hay QPU de 128Q disponible. Usando Simulador de Alta Densidad.")
            dev = qml.device('default.qubit', wires=N_QUBITS)
            backend = type('obj', (object,), {'name': 'Quantum-Sim-128Q'})

        pesos_memoria = gestionar_memoria(N_QUBITS)

        @qml.qnode(dev)
        def circuito_128q(datos, pesos):
            # Codificación
            for i in range(N_QUBITS):
                qml.RX(float(datos[i]), wires=i)
            # Memoria Aprendida
            for i in range(N_QUBITS):
                qml.RY(float(pesos[i][0]), wires=i)
                qml.RZ(float(pesos[i][1]), wires=i)
            
            # Entrelazamiento Triple Capa (Small World Architecture)
            for i in range(N_QUBITS - 1):
                qml.CNOT(wires=[i, i+1]) # Capa 1: Vecinos (15m)
            for i in range(0, N_QUBITS - 16, 16):
                qml.CNOT(wires=[i, i+16]) # Capa 2: Medio plazo (4h)
            for i in range(0, N_QUBITS - 96, 96):
                qml.CNOT(wires=[i, i+96]) # Capa 3: Ciclo Diario (24h)
            
            return qml.expval(qml.PauliZ(64)) # Medida en el centro exacto de las 32h

        adn = [np.arctan(x * 100) for x in cambios]
        res = float(circuito_128q(adn, pesos_memoria))

        # Aprendizaje de Ciclo Largo (Learning Rate 0.12)
        mov_real = np.mean(cambios) * 100
        error = (mov_real - res)
        np.save(PESOS_FILE, pesos_memoria + (error * 0.12))

        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    if res > 0.60: est, col, emo = "🚀 **COMPRA FUERTE**", "brightgreen", "🔥"
    elif res > 0.15: est, col, emo = "🟢 **COMPRA**", "green", "📈"
    elif res < -0.60: est, col, emo = "💀 **VENTA FUERTE**", "red", "📉"
    elif res < -0.15: est, col, emo = "🔴 **VENTA**", "orange", "⚠️"
    else: est, col, emo = "🟡 **ESPERA**", "yellow", "⏳"

    if b_name.startswith("Standby"): est, emo = "💤 **LATERAL DIARIO**", "😴"

    contenido = f"""# 🌌 Oráculo Cuántico BTC (128-Qubits)
![Señal](https://img.shields.io/badge/ORÁCULO-{est.replace(' ', '%20').replace('*','')}-{col}?style=for-the-badge)

## 🚦 Veredicto Maestro: {emo} {est}
* **Precio:** `${precio:,.2f}` | **Q-Score:** `{res:+.4f}`
* **Hardware:** `{b_name}` (Arquitectura 128-Cúbits)
* **Ventana de Tiempo:** 32 Horas (Análisis de ciclo completo)
* **Volatilidad Promedio:** `{vol:.4f}%`
* **Actualización:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---
## 📈 Historial (Últimos Movimientos)
![Gráfica](./rendimiento_cuantico.png)

---
*Procesado con Entrelazamiento de Triple Capa (15m, 4h, 24h).*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(contenido)

if __name__ == "__main__":
    resultado = ejecutar_oraculo()
    if resultado:
        res, p, v, b = resultado
        actualizar_readme(res, p, v, b)
        # Log CSV persistente
        log = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': res, 'Precio': p}])
        if os.path.exists('backtest_cuantico.csv'):
            pd.concat([pd.read_csv('backtest_cuantico.csv'), log]).to_csv('backtest_cuantico.csv', index=False)
        else:
            log.to_csv('backtest_cuantico.csv', index=False)
