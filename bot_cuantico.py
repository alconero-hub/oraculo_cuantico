import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator
from qiskit.quantum_info import SparsePauliOp
import pennylane as qml

# --- CONFIGURACIÓN MAESTRA ---
TOKEN = os.getenv("IBM_QUANTUM_TOKEN")
PESOS_FILE = "pesos_cuanticos_128.npy"
CSV_FILE = "backtest_cuantico.csv"
N_QUBITS = 128
N_SHOTS = 5000
LEARNING_RATE = 0.25 # Alto para reaccionar tras 6 horas de pausa
UMBRAL_BASE = 0.15   # Umbral estándar
UMBRAL_SENSITIVO = 0.08 # Umbral si el mercado está muy plano

def gestionar_memoria(n_qubits=128):
    if os.path.exists(PESOS_FILE):
        return np.load(PESOS_FILE)
    else:
        pesos = np.random.uniform(0, np.pi, (n_qubits, 2))
        np.save(PESOS_FILE, pesos)
        return pesos

def obtener_umbral_adaptativo():
    """Baja el umbral si no ha habido actividad en las últimas 12 horas."""
    if not os.path.exists(CSV_FILE):
        return UMBRAL_BASE
    
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return UMBRAL_BASE
        
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        # Buscamos la última vez que el veredicto no fue "WAIT" (es decir, BUY o SELL)
        last_op = df[df['TicketDecision'] != "WAIT"].tail(1)
        
        if last_op.empty:
            return UMBRAL_SENSITIVO
            
        ultima_fecha = last_op['Fecha'].iloc[0]
        horas_sin_operar = (datetime.now() - ultima_fecha).total_seconds() / 3600
        
        if horas_sin_operar > 12:
            print(f"⚠️ Alerta: {horas_sin_operar:.1f}h sin señales claras. Activando Umbral Sensitivo: {UMBRAL_SENSITIVO}%")
            return UMBRAL_SENSITIVO
    except Exception as e:
        print(f"Error calculando umbral adaptativo: {e}")
        
    return UMBRAL_BASE

def cerrar_operaciones_pendientes(precio_actual):
    if not os.path.exists(CSV_FILE): return
    df = pd.read_csv(CSV_FILE)
    if 'Resultado_60min' not in df.columns: df['Resultado_60min'] = np.nan

    ahora = datetime.now()
    for i, row in df.iterrows():
        if pd.isna(row['Resultado_60min']):
            fecha_op = datetime.strptime(str(row['Fecha']), '%Y-%m-%d %H:%M:%S')
            if ahora - fecha_op > timedelta(minutes=45):
                precio_entrada = float(row['Precio_Entrada'])
                veredicto = float(row['Veredicto'])
                gain = ((precio_actual - precio_entrada) / precio_entrada) * 100
                profit_real = gain if veredicto > 0 else -gain
                df.at[i, 'Resultado_60min'] = round(profit_real, 4)
                print(f"✅ Operación del {row['Fecha']} cerrada. Profit: {profit_real:+.2f}%")
    df.to_csv(CSV_FILE, index=False)

def ejecutar_oraculo():
    try:
        # 1. Datos y Umbral Adaptativo
        df_mkt = yf.download("BTC-USD", period="5d", interval="15m", progress=False, auto_adjust=True)
        precios = df_mkt['Close'].squeeze()
        ultimo_p = float(precios.iloc[-1])
        cambios = precios.pct_change().dropna().tail(N_QUBITS).values
        vol = np.mean(np.abs(cambios)) * 100

        cerrar_operaciones_pendientes(ultimo_p)
        
        umbral_actual = obtener_umbral_adaptativo()

        if vol < umbral_actual:
            return 0.0, ultimo_p, vol, f"Standby (<{umbral_actual}%)"

        # 2. Configuración Cuántica (ZNE + Amplificación)
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN)
        runtime_options = {
            "resilience_level": 2,
            "optimization_level": 3,
            "resilience": {"measure_mitigation": True, "zne_mitigation": True, "pec_mitigation": False}
        }

        try:
            backend = service.least_busy(operational=True, simulator=False, min_num_qubits=N_QUBITS)
            dev = qml.device('qiskit.remote', wires=N_QUBITS, backend=backend, shots=N_SHOTS)
        except Exception as e:
            print(f"⚠️ Simulador local: {e}")
            dev = qml.device('default.qubit', wires=N_QUBITS, shots=N_SHOTS)
            backend = type('obj', (object,), {'name': 'Quantum-Sim-128Q'})

        pesos_memoria = gestionar_memoria(N_QUBITS)

        @qml.qnode(dev)
        def circuito(datos, pesos):
            for i in range(N_QUBITS): qml.RX(float(datos[i]), wires=i)
            for i in range(N_QUBITS):
                qml.RY(float(pesos[i][0]), wires=i)
                qml.RZ(float(pesos[i][1]), wires=i)
            for i in range(N_QUBITS - 1): qml.CNOT(wires=[i, i+1])
            for i in range(0, N_QUBITS - 16, 16): qml.CNOT(wires=[i, i+16])
            return qml.expval(qml.PauliZ(64))

        adn = [np.arctan(x * 100) for x in cambios]
        res_bruto = float(circuito(adn, pesos_memoria))
        res = res_bruto * 1.5 

        # 3. Aprendizaje (Refuerzo Cuántico)
        mov_real = np.mean(cambios) * 100
        np.save(PESOS_FILE, pesos_memoria + ((mov_real - res) * LEARNING_RATE))

        return res, ultimo_p, vol, backend.name

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def actualizar_readme(res, precio, vol, b_name):
    if res > 0.15: est, col = "🟢 COMPRA", "green"
    elif res < -0.15: est, col = "🔴 VENTA", "orange"
    else: est, col = "🟡 ESPERA", "yellow"
    if "Standby" in b_name: est, col = "💤 LATERAL", "lightgrey"

    contenido = f"""# 🌌 Oráculo Cuántico 128Q
![Señal](https://img.shields.io/badge/ORÁCULO-{est.replace(' ', '%20')}-{col}?style=for-the-badge)
* **Precio BTC:** `${precio:,.2f}` | **Q-Score:** `{res:+.4f}`
* **Hardware:** `{b_name}` | **Shots:** `{N_SHOTS}`
* **Volatilidad:** `{vol:.4f}%` | **Adaptativo:** `True`
* **Sync:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC`

---
![Gráfica](./rendimiento_cuantico.png)
"""
    with open("README.md", "w", encoding="utf-8") as f: f.write(contenido)

if __name__ == "__main__":
    resultado = ejecutar_oraculo()
    if resultado:
        res, p, v, b = resultado
        actualizar_readme(res, p, v, b)
        nuevo = pd.DataFrame([{
            'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'TicketDecision': "BUY" if res > 0.15 else ("SELL" if res < -0.15 else "WAIT"),
            'Veredicto': res, 'Precio_Entrada': p, 'Volatilidad': v, 'Resultado_60min': np.nan 
        }])
        if os.path.exists(CSV_FILE):
            pd.concat([pd.read_csv(CSV_FILE), nuevo], ignore_index=True).to_csv(CSV_FILE, index=False)
        else:
            nuevo.to_csv(CSV_FILE, index=False)
        print(f"🎯 Fin. Q-Score: {res:+.4f} | Umbral: {v:.4f}%")
