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
    # Usamos el canal solicitado para 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Conectado a QPU Real: {backend.name}")

    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=4096)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        for i in range(len(datos)):
            qml.RY(float(datos[i]), wires=i)
        for i in range(4):
            qml.CNOT(wires=[i, 4])
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error en Conexión/QPU: {e}"); exit(1)

# --- 2. CAPTURA DE DATOS (Anti-Series Error) ---
try:
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    if df.empty: print("⚠️ Sin datos"); exit(0)

    # Limpieza para asegurar escalares puros
    precios = df['Close'].squeeze()
    if isinstance(precios, pd.DataFrame): precios = precios.iloc[:, 0]
    
    ultimo_p = float(precios.iloc[-1])
    cambios = precios.pct_change().dropna().tail(4).values
    adn = [np.arctan(float(x) * 100) for x in cambios]

    print(f"🧠 BTC: ${ultimo_p:.2f} | Procesando en IBM...")
    raw_res = oraculo_cuantico(adn)
    resultado = float(np.array(raw_res).item())
except Exception as e:
    print(f"❌ Error en Datos/Cómputo: {e}"); exit(1)

# --- 3. ACTUALIZAR README (Semáforo) ---
def actualizar_readme(res, precio):
    if res > 0.15: semaforo = "🟢 **COMPRA** (Señal Alcista)"
    elif res < -0.15: semaforo = "🔴 **VENTA** (Señal Bajista)"
    else: semaforo = "🟡 **ESPERA** (Neutral/Ruido)"

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            contenido = f.read()
        
        nuevo_texto = (f"\n> **Última Señal:** {semaforo}\n"
                       f"> **Precio BTC:** ${precio:,.2f}\n"
                       f"> **Hardware:** {backend.name}\n"
                       f"> **Actualizado:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n")
        
        inicio, fin = "", ""
        parte1 = contenido.split(inicio)[0]
        parte2 = contenido.split(fin)[1]
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"{parte1}{inicio}{nuevo_texto}{fin}{parte2}")
        print("✅ README actualizado.")
    except Exception as e: print(f"⚠️ Error README: {e}")

# --- 4. GUARDAR CSV ---
archivo = 'backtest_cuantico.csv'
fila = pd.DataFrame([{'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"), 
                      'Veredicto': round(resultado, 4), 'Precio': round(ultimo_p, 2), 
                      'Backend': backend.name}])

if os.path.exists(archivo):
    pd.concat([pd.read_csv(archivo), fila], ignore_index=True).to_csv(archivo, index=False)
else:
    fila.to_csv(archivo, index=False)

actualizar_readme(resultado, ultimo_p)
print(f"🚀 Ejecución finalizada: {resultado:+.4f}")
