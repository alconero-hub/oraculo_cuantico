import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Canal para 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Hardware: {backend.name}")

    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i)
        for i in range(4):
            qml.CNOT(wires=[i, 4])
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de Conexión: {e}"); exit(1)

# --- 2. DATOS DE MERCADO ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    if df.empty:
        print("⚠️ No hay datos de Yahoo Finance"); exit(0)

    precios = df['Close'].squeeze()
    if isinstance(precios, pd.DataFrame): precios = precios.iloc[:, 0]
    
    ultimo_p = float(precios.iloc[-1])
    cambios = precios.pct_change().dropna().tail(4).values
    
    # Reducimos el umbral a 0.01% para que sea más sensible
    volatilidad = np.mean(np.abs(cambios)) * 100
    umbral_minimo = 0.02 

    if volatilidad < umbral_minimo:
        print(f"😴 Mercado muy plano ({volatilidad:.4f}%).")
        resultado = 0.0
        status_backend = "Standby (Low Vol)"
    else:
        print(f"🔥 Volatilidad detectada ({volatilidad:.4f}%).")
        adn = [np.arctan(float(x) * 100) for x in cambios]
        resultado = float(np.array(oraculo_cuantico(adn)).item())
        status_backend = backend.name

except Exception as e:
    print(f"❌ Error procesando datos: {e}"); exit(1)

# --- 3. ACTUALIZAR README ---
def actualizar_readme(res, precio, vol):
    if vol < umbral_minimo:
        semaforo = "⚪ **DORMIDO** (Mercado Lateral)"
    elif res > 0.15: 
        semaforo = "🟢 **COMPRA** (Señal Alcista)"
    elif res < -0.15: 
        semaforo = "🔴 **VENTA** (Señal Bajista)"
    else: 
        semaforo = "🟡 **ESPERA** (Incertidumbre)"

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            contenido = f.read()
        
        nuevo_texto = (f"\n> **Última Señal:** {semaforo}\n"
                       f"> **Precio BTC:** ${precio:,.2f}\n"
                       f"> **Volatilidad:** {vol:.4f}%\n"
                       f"> **Hardware:** {status_backend}\n"
                       f"> **Actualizado:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n")
        
        inicio, fin = "", ""
        p1 = contenido.split(inicio)[0]
        p2 = contenido.split(fin)[1]
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"{p1}{inicio}{nuevo_texto}{fin}{p2}")
    except Exception as e: print(f"⚠️ Error README: {e}")

# --- 4. GUARDADO FORZOSO DEL CSV ---
archivo = 'backtest_cuantico.csv'
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': round(ultimo_p, 2),
    'Backend': status_backend
}])

if os.path.exists(archivo):
    df_old = pd.read_csv(archivo)
    pd.concat([df_old, nueva_fila], ignore_index=True).to_csv(archivo, index=False)
else:
    nueva_fila.to_csv(archivo, index=False)

actualizar_readme(resultado, ultimo_p, volatilidad)
print(f"🚀 Proceso completado. Veredicto: {resultado:+.4f}")
