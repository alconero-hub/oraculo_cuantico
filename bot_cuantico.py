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
    # Canal actualizado para 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Hardware Real Detectado: {backend.name}")

    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i)
        for i in range(4):
            qml.CNOT(wires=[i, 4])
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error en Conexión/QPU: {e}"); exit(1)

# --- 2. DATOS DE MERCADO E INTELIGENCIA DE AHORRO ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    if df.empty: print("⚠️ Sin datos"); exit(0)

    # Limpieza de datos (Anti-Series Error)
    precios = df['Close'].squeeze()
    if isinstance(precios, pd.DataFrame): precios = precios.iloc[:, 0]
    
    ultimo_p = float(precios.iloc[-1])
    cambios = precios.pct_change().dropna().tail(4).values
    
    # MÉTRICA DE VOLATILIDAD (Promedio de cambios absolutos en %)
    volatilidad = np.mean(np.abs(cambios)) * 100
    umbral_minimo = 0.05  # Solo llamamos a IBM si se mueve más de un 0.05%

    if volatilidad < umbral_minimo:
        print(f"😴 Mercado lateral ({volatilidad:.4f}%). Veredicto 0.0 automático (Ahorro QPU).")
        resultado = 0.0
    else:
        print(f"🔥 Movimiento detectado ({volatilidad:.4f}%). Consultando Oráculo...")
        adn = [np.arctan(float(x) * 100) for x in cambios]
        raw_res = oraculo_cuantico(adn)
        resultado = float(np.array(raw_res).item())

except Exception as e:
    print(f"❌ Error en Datos: {e}"); exit(1)

# --- 3. ACTUALIZAR README (Semáforo Dinámico) ---
def actualizar_readme(res, precio, vol):
    if vol < umbral_minimo:
        semaforo = "⚪ **DORMIDO** (Mercado Lateral - Ahorro Activo)"
    elif res > 0.15: 
        semaforo
