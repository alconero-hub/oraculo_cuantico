import os
import re
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Conexión oficial IBM 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Conectado a QPU Real: {backend.name}")

    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RX(float(datos[i]), wires=i)
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
        qml.CNOT(wires=[3, 4])
        qml.PauliX(wires=4)
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de Conexión/QPU: {e}")
    exit(1)

# --- 2. CAPTURA DE DATOS ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    precios = df['Close'].squeeze()
    ultimo_p = float(precios.iloc[-1])
    cambios = precios.pct_change().dropna().tail(4).values
    volatilidad = np.mean(np.abs(cambios)) * 100
    
    umbral_minimo = 0.20 

    if volatilidad < umbral_minimo:
        print(f"😴 Mercado lateral ({volatilidad:.4f}%).")
        resultado = 0.0
        status_backend = "Standby (Baja Volatilidad)"
    else:
        print(f"🔥 Volatilidad detectada. Consultando IBM...")
        adn = [np.arctan(float(x) * 100) for x in cambios]
        resultado = float(np.array(oraculo_cuantico(adn)).item())
        status_backend = backend.name

except Exception as e:
    print(f"❌ Error en datos: {e}")
    exit(1)

# --- 3. FUNCIÓN DE ACTUALIZACIÓN (SISTEMA REGEX ANTI-DUPLICADOS) ---
def actualizar_readme(res, precio, vol, b_name):
    # --- TÁCTICA DE DECISIÓN EXTREMA ---
    if vol < 0.01:
        estado = "⚪ **MERCADO DORMIDO** (Baja Volatilidad)"
        color_box = "blue"
    elif res > 0.60: # Veredicto muy positivo
        estado = "🚀 **COMPRA FUERTE** (Señal Cuántica Máxima)"
        color_box = "green"
    elif res > 0.15:
        estado = "🟢 **COMPRA MODERADA**"
        color_box = "green"
    elif res < -0.60: # Veredicto muy negativo
        estado = "💀 **VENTA FUERTE** (Alerta de Caída)"
        color_box = "red"
    elif res < -0.15:
        estado = "🔴 **VENTA MODERADA**"
        color_box = "red"
    else:
        estado = "🟡 **ESPERA** (Neutralidad)"
        color_box = "yellow"

    # --- TÁCTICA DE ESCRITURA TOTAL ---
    # No buscamos etiquetas, escribimos el archivo entero cada vez
    contenido_nuevo = f"""# 🌌 Oráculo Cuántico BTC

![Estado](https://img.shields.io/badge/ORÁCULO-{estado.replace(' ', '%20')}-{color_box}?style=for-the-badge)

### 🚦 Veredicto Actual
> # {estado}

**Detalles Técnicos:**
* **Precio Actual:** ${precio:,.2f}
* **Poder Cuántico (Veredicto):** {res:+.4f}
* **Volatilidad:** {vol:.4f}%
* **Procesador:** {b_name}
* **Última Actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

---

### 📈 Gráfica de Rendimiento
![Gráfica](./rendimiento_cuantico.png)

---
*Aviso: Este sistema utiliza entrelazamiento de qubits en hardware real de IBM. No es consejo financiero.*
"""

    try:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(contenido_nuevo)
        print("✅ README reconstruido desde cero con éxito.")
    except Exception as e:
        print(f"❌ Error escribiendo: {e}")
        
# Guardar en CSV (opcional)
try:
    archivo_csv = 'backtest_cuantico.csv'
    nuevo_dato = pd.DataFrame([{'Fecha': datetime.now(), 'Veredicto': resultado, 'Precio': ultimo_p}])
    if os.path.exists(archivo_csv):
        pd.concat([pd.read_csv(archivo_csv), nuevo_dato]).to_csv(archivo_csv, index=False)
    else:
        nuevo_dato.to_csv(archivo_csv, index=False)
except:
    pass

print(f"🚀 Fin del ciclo. Veredicto: {resultado:+.4f}")
