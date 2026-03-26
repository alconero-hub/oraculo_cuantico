import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONFIGURACIÓN E IBM QUANTUM ---
# Asegúrate de tener IBM_QUANTUM_TOKEN en los Secrets de tu repo
token = os.getenv("IBM_QUANTUM_TOKEN")

def ejecutar_oraculo():
    try:
        print("🔍 Iniciando conexión con IBM Quantum...")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
        print(f"📡 Conectado a QPU Real: {backend.name}")

        dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

        @qml.qnode(dev)
        def circuito(datos):
            # Codificación de datos en ángulos de rotación
            for i in range(len(datos)):
                qml.RX(float(datos[i]), wires=i)
            # Entrelazamiento cuántico
            qml.CNOT(wires=[0, 1])
            qml.CNOT(wires=[1, 2])
            qml.CNOT(wires=[2, 3])
            qml.CNOT(wires=[3, 4])
            # Medición del valor esperado
            return qml.expval(qml.PauliZ(4))

        # --- 2. CAPTURA DE DATOS DE MERCADO ---
        print("📈 Descargando datos de BTC-USD...")
        df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        
        # Calculamos volatilidad de los últimos 4 periodos (1 hora)
        cambios = precios.pct_change().dropna().tail(4).values
        vol = np.mean(np.abs(cambios)) * 100
        
        # Umbral para evitar ruido en mercado muerto
        umbral_minimo = 0.20 

        if vol < umbral_minimo:
            print(f"😴 Mercado lateral ({vol:.4f}%). Saltando QPU para ahorrar cuota.")
            return 0.0, ultimo_p, vol, f"Standby ({backend.name})"
        
        # Si hay movimiento, ejecutamos el oráculo
        print("🔮 Ejecutando circuito cuántico...")
        adn = [np.arctan(float(x) * 100) for x in cambios]
        res = float(np.array(circuito(adn)).item())
        
        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error en el núcleo del bot: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    # --- 3. LÓGICA DE DECISIÓN (SISTEMA DE SEÑALES FUERTES) ---
    if res is None:
        estado = "⚠️ **ERROR DE SISTEMA**"
        color = "red"
        emoji = "❌"
    elif vol < 0.01:
        estado = "⚪ **MERCADO LATERAL**"
        color = "lightgrey"
        emoji = "😴"
    elif res > 0.60:
        estado = "🚀 **COMPRA FUERTE**"
        color = "brightgreen"
        emoji = "🔥"
    elif res > 0.15:
        estado = "🟢 **COMPRA**"
        color = "green"
        emoji = "📈"
    elif res < -0.60:
        estado = "💀 **VENTA FUERTE**"
        color = "red"
        emoji = "📉"
    elif res < -0.15:
        estado = "🔴 **VENTA**"
        color = "orange"
        emoji = "⚠️"
    else:
        estado = "🟡 **ESPERA**"
        color = "yellow"
        emoji = "⏳"

    # --- 4. RECONSTRUCCIÓN TOTAL DEL README ---
    # Limpiamos el texto para el badge (URL encode simple)
    badge_text = estado.replace('*', '').replace(' ', '%20')
    
    contenido = f"""# 🌌 Oráculo Cuántico BTC

![Señal](https://img.shields.io/badge/VEREDICTO-{badge_text}-{color}?style=for-the-badge)

## 🚦 Estado del Oráculo
> # {emoji} {estado}

### 📊 Análisis de la Última Ejecución
* **Precio Actual:** `${precio:,.2f}`
* **Veredicto Cuántico:** `{res:+.4f}` (Confianza del Oráculo)
* **Volatilidad Detectada:** `{vol:.4f}%`
* **Hardware:** `{b_name}`
* **Sincronización:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---

## 📈 Gráfica de Rendimiento
La gráfica se actualiza automáticamente con cada veredicto.

![Gráfica](./rendimiento_cuantico.png)

---
*Powered by IBM Quantum Platform | alconero-hub*
"""

    try:
        # El modo 'w' machaca el archivo, asegurando que no haya duplicados
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"✅ README reconstruido exitosamente con señal: {estado}")
    except Exception as e:
        print(f"❌ Error al escribir el archivo README: {e}")

# --- 5. FLUJO PRINCIPAL ---
if __name__ == "__main__":
    resultado_bot = ejecutar_oraculo()
    
    if resultado_bot:
        res, precio, vol, b_name = resultado_bot
        
        # Actualizamos el README con la nueva señal
        actualizar_readme(res, precio, vol, b_name)
        
        # Guardar en el histórico CSV para la gráfica
        try:
            archivo_csv = 'backtest_cuantico.csv'
            nuevo_log = pd.DataFrame([{
                'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                'Veredicto': res, 
                'Precio': precio
            }])
            
            if os.path.exists(archivo_csv):
                # Usamos format='mixed' al leer para evitar el error previo de fechas
                df_hist = pd.read_csv(archivo_csv)
                pd.concat([df_hist, nuevo_log]).to_csv(archivo_csv, index=False)
            else:
                nuevo_log.to_csv(archivo_csv, index=False)
            print("📊 Datos guardados en el CSV.")
        except Exception as e:
            print(f"⚠️ No se pudo actualizar el CSV: {e}")
    else:
        print("🚫 La ejecución falló y no se modificará el README.")
