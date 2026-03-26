import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONFIGURACIÓN E IBM QUANTUM ---
token = os.getenv("IBM_QUANTUM_TOKEN")

def ejecutar_oraculo():
    try:
        print("🔍 Buscando hardware cuántico de 8+ cúbits...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        
        # Intentamos buscar un backend real con al menos 8 qubits
        try:
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=8)
            print(f"📡 Conectado a QPU Real: {backend.name}")
            dev = qml.device('qiskit.remote', wires=8, backend=backend, shots=1024)
        except:
            print("⚠️ No hay QPU de 8 cúbits libre. Usando simulador avanzado...")
            dev = qml.device('default.qubit', wires=8)
            backend = type('obj', (object,), {'name': 'IBM Simulator (High Res)'})

        @qml.qnode(dev)
        def circuito_8_qubits(datos):
            # 1. CODIFICACIÓN DOBLE (RX + RZ para capturar tendencia y fuerza)
            for i in range(8):
                qml.RX(float(datos[i]), wires=i)
                qml.RZ(float(datos[i]) * 0.5, wires=i)

            # 2. ENTRELAZAMIENTO CIRCULAR (Todos conectados)
            for i in range(7):
                qml.CNOT(wires=[i, i+1])
            qml.CNOT(wires=[7, 0])

            # 3. CAPA DE INTERFERENCIA (Puertas Hadamard)
            for i in range(8):
                qml.Hadamard(wires=i)

            # 4. MEDICIÓN DEL VALOR ESPERADO EN EL NÚCLEO
            return qml.expval(qml.PauliZ(4))

        # --- 2. CAPTURA DE DATOS (8 INTERVALOS = 2 HORAS) ---
        print("📈 Analizando últimas 2 horas de BTC...")
        df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        
        # Tomamos 8 cambios porcentuales
        cambios = precios.pct_change().dropna().tail(8).values
        vol = np.mean(np.abs(cambios)) * 100
        
        if vol < 0.25:
            print(f"😴 Baja volatilidad ({vol:.4f}%).")
            return 0.0, ultimo_p, vol, f"Standby ({backend.name})"
        
        # Normalización para rotación cuántica
        adn = [np.arctan(float(x) * 100) for x in cambios]
        
        print("🔮 Procesando ADN Cuántico...")
        res = float(np.array(circuito_8_qubits(adn)).item())
        
        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error en el núcleo: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    # --- 3. LÓGICA DE SEÑALES EXTREMAS ---
    if res is None:
        estado, color, emoji = "⚠️ **ERROR**", "red", "❌"
    elif vol < 0.01:
        estado, color, emoji = "⚪ **LATERAL**", "lightgrey", "😴"
    elif res > 0.65:
        estado, color, emoji = "🚀 **COMPRA FUERTE**", "brightgreen", "🔥"
    elif res > 0.15:
        estado, color, emoji = "🟢 **COMPRA**", "green", "📈"
    elif res < -0.65:
        estado, color, emoji = "💀 **VENTA FUERTE**", "red", "📉"
    elif res < -0.15:
        estado, color, emoji = "🔴 **VENTA**", "orange", "⚠️"
    else:
        estado, color, emoji = "🟡 **ESPERA**", "yellow", "⏳"

    # --- 4. RECONSTRUCCIÓN TOTAL ---
    badge_text = estado.replace('*', '').replace(' ', '%20')
    
    contenido = f"""# 🌌 Oráculo Cuántico BTC (8-Qubits Edition)

![Señal](https://img.shields.io/badge/VEREDICTO-{badge_text}-{color}?style=for-the-badge)

## 🚦 Veredicto del Sistema
> # {emoji} {estado}

### 📊 Análisis Técnico Cuántico
* **Precio BTC:** `${precio:,.2f}`
* **Confianza (Q-Score):** `{res:+.4f}`
* **Volatilidad:** `{vol:.4f}%`
* **Hardware:** `{b_name}` (Arquitectura de 8 Cúbits)
* **Ventana Temporal:** `120 min (8x15m)`
* **Actualización:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---

## 📈 Gráfica de Rendimiento
![Gráfica](./rendimiento_cuantico.png)

---
*Procesado con Entrelazamiento Circular y Puertas de Interferencia de Hadamard.*
"""

    try:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"✅ README actualizado con 8 cúbits.")
    except Exception as e:
        print(f"❌ Error escribiendo README: {e}")

# --- 5. EJECUCIÓN ---
if __name__ == "__main__":
    resultado_bot = ejecutar_oraculo()
    if resultado_bot:
        res, precio, vol, b_name = resultado_bot
        actualizar_readme(res, precio, vol, b_name)
        
        # Guardar en CSV
        try:
            archivo_csv = 'backtest_cuantico.csv'
            nuevo_log = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': res, 'Precio': precio}])
            if os.path.exists(archivo_csv):
                pd.concat([pd.read_csv(archivo_csv), nuevo_log]).to_csv(archivo_csv, index=False)
            else:
                nuevo_log.to_csv(archivo_csv, index=False)
        except:
            pass
