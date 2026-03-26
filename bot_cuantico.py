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
    # 1. Definir el texto del semáforo
    if vol < 0.01: 
        semaforo = "⚪ **DORMIDO**"
    elif res > 0.15: 
        semaforo = "🟢 **COMPRA**"
    elif res < -0.15: 
        semaforo = "🔴 **VENTA**"
    else: 
        semaforo = "🟡 **ESPERA**"

    archivo_path = "README.md"
    inicio = ""
    fin = ""

    try:
        with open(archivo_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        # 2. El bloque limpio que queremos que quede
        nuevo_bloque = (
            f"{inicio}\n"
            f"> **Última Señal:** {semaforo}\n"
            f"> **Precio BTC:** ${precio:,.2f} | **Veredicto:** {res:+.4f}\n"
            f"> **Hardware:** {b_name} | **Actualizado:** {datetime.now().strftime('%H:%M')} UTC\n"
            f"{fin}"
        )

        # 3. Lógica de Reemplazo Total (Evita duplicados)
        if inicio in contenido and fin in contenido:
            # Dividimos el archivo en 3 partes usando las marcas
            # Tomamos la parte ANTES del primer 'inicio'
            parte_limpia_pre = contenido.split(inicio)[0]
            # Tomamos la parte DESPUÉS del último 'fin'
            parte_limpia_post = contenido.split(fin)[-1]
            
            # Reconstruimos el archivo ignorando cualquier basura que hubiera en medio
            nuevo_contenido = f"{parte_limpia_pre.strip()}\n\n{nuevo_bloque}\n\n{parte_limpia_post.strip()}"
            
            with open(archivo_path, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            print("✅ README saneado: Se eliminaron duplicados y se escribió la nueva señal.")
        else:
            print("❌ Error: No se encontraron las marcas. Revisa el paso 1.")

    except Exception as e:
        print(f"⚠️ Error en actualización: {e}")

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
