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
    
    umbral_minimo = 0.30 

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
    # Definición de semáforo
    if vol < 0.01: 
        semaforo = "⚪ **DORMIDO**"
    elif res > 0.15: 
        semaforo = "🟢 **COMPRA**"
    elif res < -0.15: 
        semaforo = "🔴 **VENTA**"
    else: 
        semaforo = "🟡 **ESPERA**"

    archivo_path = "README.md"
    inicio_tag = ""
    fin_tag = ""

    try:
        if not os.path.exists(archivo_path):
            with open(archivo_path, "w") as f: f.write("# Oráculo BTC\n" + inicio_tag + "\n" + fin_tag)

        with open(archivo_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        # BLOQUE NUEVO
        nuevo_bloque = (
            f"{inicio_tag}\n"
            f"> **Última Señal:** {semaforo} | **Precio:** ${precio:,.2f}\n"
            f"> **Veredicto:** {res:+.4f} | **Hardware:** {b_name}\n"
            f"> **Actualizado:** {datetime.now().strftime('%H:%M:%S')} UTC\n"
            f"{fin_tag}"
        )

        # SI EXISTEN LAS ETIQUETAS: Reemplazo Quirúrgico
        if inicio_tag in contenido and fin_tag in contenido:
            import re
            patron = re.compile(f"{re.escape(inicio_tag)}.*?{re.escape(fin_tag)}", re.DOTALL)
            nuevo_contenido = patron.sub(nuevo_bloque, contenido)
        else:
            # SI NO EXISTEN: Las pegamos al final
            print("⚠️ Etiquetas no encontradas. Inyectando al final del archivo...")
            nuevo_contenido = contenido + "\n\n## 🚦 Estado del Oráculo\n" + nuevo_bloque

        with open(archivo_path, "w", encoding="utf-8") as f:
            f.write(nuevo_contenido)
        print("✅ README actualizado con éxito.")

    except Exception as e:
        print(f"⚠️ Error en README: {e}")
        
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
