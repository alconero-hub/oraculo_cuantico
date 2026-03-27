import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- CONFIGURACIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_16.npy" # Cambiamos nombre para no chocar con el de 8

def gestionar_memoria(n_qubits=16):
    if os.path.exists(PESOS_FILE):
        return np.load(PESOS_FILE)
    else:
        # 16 qubits x 2 angulos de rotación aprendibles
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def ejecutar_oraculo():
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        # Buscamos hardware de 16+ qubits
        try:
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=16)
            b_name = backend.name
            dev = qml.device('qiskit.remote', wires=16, backend=backend, shots=1024)
        except:
            b_name = "Simulador (16-Qubits)"
            dev = qml.device('default.qubit', wires=16)

        pesos_memoria = gestionar_memoria(16)

        @qml.qnode(dev)
        def circuito_16_qubits(datos, pesos):
            # 1. CODIFICACIÓN (16 intervalos de 15min = 4 horas)
            for i in range(16):
                qml.RX(float(datos[i]), wires=i)
            
            # 2. CAPA DE APRENDIZAJE
            for i in range(16):
                qml.RY(float(pesos[i][0]), wires=i)
                qml.RZ(float(pesos[i][1]), wires=i)

            # 3. ENTRELAZAMIENTO DE CADENA DOBLE (Más robusto para 16 qubits)
            for i in range(15):
                qml.CNOT(wires=[i, i+1])
            for i in range(0, 14, 2): # Entrelazamiento saltado para mayor correlación
                qml.CNOT(wires=[i, i+2])
            
            # Medimos en el cúbit central (8)
            return qml.expval(qml.PauliZ(8))

        # Descarga de datos: Necesitamos al menos 17 filas para tener 16 cambios
        df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        cambios = precios.pct_change().dropna().tail(16).values
        vol = np.mean(np.abs(cambios)) * 100
        
        if len(cambios) < 16:
            print("⚠️ Faltan datos para 16 qubits.")
            return None

        adn = [np.arctan(x * 100) for x in cambios]
        res = float(circuito_16_qubits(adn, pesos_memoria))

        # Aprendizaje Reforzado
        movimiento_real = np.mean(cambios) * 100
        # El bot aprende comparando su veredicto con lo que pasó realmente
        error = (movimiento_real - res)
        nuevos_pesos = pesos_memoria + (error * 0.05)
        np.save(PESOS_FILE, nuevos_pesos)

        return res, ultimo_p, vol, b_name

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    # Umbrales ajustados para mayor sensibilidad con 16 qubits
    if res > 0.60: estado, color, emoji = "🚀 **COMPRA FUERTE**", "brightgreen", "🔥"
    elif res > 0.15: estado, color, emoji = "🟢 **COMPRA**", "green", "📈"
    elif res < -0.60: estado, color, emoji = "💀 **VENTA FUERTE**", "red", "📉"
    elif res < -0.15: estado, color, emoji = "🔴 **VENTA**", "orange", "⚠️"
    else: estado, color, emoji = "🟡 **ESPERA**", "yellow", "⏳"

    contenido = f"""# 🌌 Oráculo Cuántico BTC (16-Qubits + Deep Learning)
![Señal](https://img.shields.io/badge/VEREDICTO-{estado.replace(' ', '%20').replace('*','')}-{color}?style=for-the-badge)

## 🚦 Veredicto Actual: {emoji} {estado}
* **Precio Actual:** `${precio:,.2f}` | **Q-Score:** `{res:+.4f}`
* **Hardware:** `{b_name}` (Arquitectura de 16 Cúbits)
* **Memoria:** Adaptativa activa (Pesos actualizados)
* **Ventana de Análisis:** 4 Horas (16x15m)
* **Actualización:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---
## 📈 Gráfica de Rendimiento
![Gráfica](./rendimiento_cuantico.png)
"""
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(contenido)

if __name__ == "__main__":
    resultado = ejecutar_oraculo()
    if resultado:
        res, p, v, b = resultado
        actualizar_readme(res, p, v, b)
        # Registro en CSV
        try:
            log = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': res, 'Precio': p}])
            if os.path.exists('backtest_cuantico.csv'):
                pd.concat([pd.read_csv('backtest_cuantico.csv'), log]).to_csv('backtest_cuantico.csv', index=False)
            else:
                log.to_csv('backtest_cuantico.csv', index=False)
        except: pass
