import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- CONFIGURACIÓN DE ALTO RENDIMIENTO ---
TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_128.npy"
N_QUBITS = 128
N_SHOTS = 10000        # Precisión estadística del 1%
LEARNING_RATE = 0.15   # Velocidad de adaptación de la memoria
UMBRAL_VOL = 0.01      # Filtro de ruido para ahorrar cuota de QPU

def gestionar_memoria(n_qubits=128):
    """Carga los pesos aprendidos o inicializa una nueva red neuronal."""
    if os.path.exists(PESOS_FILE):
        print(f"🧠 Memoria de {n_qubits}-Qubits cargada correctamente.")
        return np.load(PESOS_FILE)
    else:
        print(f"👶 Inicializando nueva arquitectura de {n_qubits} cúbits...")
        # Cada cúbit tiene 2 ángulos de rotación aprendibles (RY, RZ)
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def ejecutar_oraculo():
    try:
        # 1. CAPTURA DE DATOS (Ventana de 32 horas: 128 velas x 15 min)
        print(f"📈 Analizando histórico de 32 horas de BTC...")
        df = yf.download("BTC-USD", period="5d", interval="15m", progress=False, auto_adjust=True)
        precios = df['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        
        # Obtenemos los últimos 128 cambios porcentuales
        cambios = precios.pct_change().dropna().tail(N_QUBITS).values
        vol = np.mean(np.abs(cambios)) * 100

        # FILTRO DE SEGURIDAD: Si no hay volatilidad, no gastamos QPU
        if vol < UMBRAL_VOL:
            print(f"😴 Mercado lateral ({vol:.4f}% < {UMBRAL_VOL}%). Oráculo en Stand
