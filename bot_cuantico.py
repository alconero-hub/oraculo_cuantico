import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- CONFIGURACIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_16.npy"
N_QUBITS = 16

def gestionar_memoria(n_qubits=16):
    if os.path.exists(PESOS_FILE):
        print("🧠 Memoria de 16-Qubits cargada.")
        return np.load(PESOS_FILE)
    else:
        print("👶 Creando nueva red neuronal de 16-Qubits...")
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def ejecutar_oraculo():
    try:
        # 1. Obtener Datos y calcular Volatilidad ANTES de llamar a IBM
        print("📈 Analizando volatilidad de las últimas 4 horas...")
        df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        cambios = precios.pct_change().dropna().tail(N_QUBITS).values
        vol = np.mean(np.abs(cambios)) * 100

        # --- FILTRO DE VOLATILIDAD ---
        if vol < 0.30:
            print(f"😴 Mercado lateral ({vol:.4f}%). Saltando QPU para no gastar cuota.")
            return 0.0, ultimo_p, vol, "Standby (Baja Volatilidad)"

        if len(cambios) < N_QUBITS:
            print("⚠️ No hay suficientes velas de 15m para llenar 16 qubits.")
            return None

        # 2. Conectar con IBM solo si hay volatilidad
        print(f"🚀 Volatilidad detectada ({vol:.4f}%). Conectando con IBM Quantum...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        
        try:
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=N_QUBITS)
            print(f"📡 Hardware: {backend.name}")
            dev = qml.device('qiskit.remote', wires=N_QUBITS, backend=backend, shots=1024)
        except:
            print("⚠️ No hay QPU de 16Q disponible. Usando simulador local.")
            dev = qml.device('default.qubit', wires=N_QUBITS)
            backend = type('obj', (object,), {'name': 'Simulador Local (16Q)'})

        pesos_memoria = gestionar_memoria(N_QUBITS)

        @qml.qnode(dev)
        def circuito_16q(datos, pesos):
            # Codificación de 16 periodos
            for i in range(N_QUBITS):
                qml.RX(float(datos[i]), wires=i)
            # Capa de aprendizaje persistente
            for i in range(N_QUBITS):
                qml.RY(float(pesos[i][0]), wires=i)
                qml.RZ(float(pesos[i][1]), wires=i)
            # Entrelazamiento de doble cadena (vecinos y saltos)
            for i in range(N_QUBITS - 1):
                qml.CNOT(wires=[i, i+1])
            for i in range(0, N_QUBITS - 2, 2):
                qml.CNOT(wires=[i, i+2])
            
            return qml.expval(qml.PauliZ(8)) # Medimos en el centro

        adn = [np.arctan(x * 100) for x in cambios]
        res = float(circuito_16q(adn, pesos_memoria))

        # 3. Actualizar Aprendizaje
        mov_real = np.mean(cambios) * 100
        error = (mov_real - res)
        nuevos_pesos = pesos_memoria + (error * 0.05)
        np.save(PESOS_FILE, nuevos_pesos)

        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    # Lógica de señales
    if res > 0.60: estado, color, emoji = "🚀 **COMPRA FUERTE**", "brightgreen", "🔥"
    elif res > 0.15: estado, color, emoji = "🟢 **COMPRA**", "green", "📈"
    elif res < -0.60: estado, color, emoji = "💀 **VENTA FUERTE**", "red", "📉"
    elif res < -0.15: estado, color, emoji = "🔴 **VENTA**", "orange", "⚠️"
    else: estado, color, emoji = "🟡 **ESPERA**", "yellow", "⏳"

    badge_text = estado.replace('*', '').replace(' ', '%20')
    
    contenido = f"""# 🌌 Oráculo Cuántico BTC (16-Qubits)

![Señal](https://img.shields.io/badge/VEREDICTO-{badge_text}-{color}?style=for-the-badge)

## 🚦 Veredicto Actual: {emoji} {estado}
* **Precio Actual:** `${precio:,.2f}` | **Confianza Cuántica:** `{res:+.4f}`
* **Hardware:** `{b_name}` (16 Cúbits)
* **Memoria:** Aprendizaje Reforzado Persistente
* **Análisis:** Ventana de 4 Horas (16x15m)
* **Actualizado:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---
## 📈 Historial de Rendimiento
![Gráfica](./rendimiento_cuantico.png)

---
*Procesado con Entrelazamiento de Doble Cadena y Codificación Parametrizada.*
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(contenido)

if __name__ == "__main__":
    resultado = ejecutar_oraculo()
    if resultado:
        res, p, v, b = resultado
        actualizar_readme(res, p, v, b)
        # Guardar CSV
        log = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': res, 'Precio': p}])
        if os.path.exists('backtest_cuantico.csv'):
            pd.concat([pd.read_csv('backtest_cuantico.csv'), log]).to_csv('backtest_cuantico.csv', index=False)
        else:
            log.to_csv('backtest_cuantico.csv', index=False)
