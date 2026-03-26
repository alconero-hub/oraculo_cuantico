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
    # Lógica de semáforo
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
            print("❌ No existe el README.md")
            return

        with open(archivo_path, "r", encoding="utf-8") as f:
            lineas = f.readlines()

        nueva_lista_lineas = []
        dentro_de_sector = False
        sector_escrito = False

        for linea in lineas:
            # Si encontramos el inicio, activamos el modo 'borrado'
            if inicio_tag in linea:
                dentro_de_sector = True
                # Escribimos el bloque nuevo una sola vez
                nueva_lista_lineas.append(f"{inicio_tag}\n")
                nueva_lista_lineas.append(f"> **Última Señal:** {semaforo} | **Precio:** ${precio:,.2f}\n")
                nueva_lista_lineas.append(f"> **Veredicto:** {res:+.4f} | **Hardware:** {b_name}\n")
                nueva_lista_lineas.append(f"{fin_tag}\n")
                sector_escrito = True
                continue
            
            # Si encontramos el fin, desactivamos el modo borrado
            if fin_tag in linea:
                dentro_de_sector = False
                continue

            # Si no estamos dentro del sector de datos, mantenemos la línea original
            if not dentro_de_sector:
                nueva_lista_lineas.append(linea)

        # Si por alguna razón no existían las etiquetas, las añadimos al final (seguridad)
        if not sector_escrito:
            nueva_lista_lineas.append(f"\n{inicio_tag}\n> **Señal:** {semaforo}\n{fin_tag}\n")

        # Guardar el archivo limpio
        with open(archivo_path, "w", encoding="utf-8") as f:
            f.writelines(nueva_lista_lineas)
            
        print("✅ README saneado y actualizado sin duplicados.")

    except Exception as e:
        print(f"⚠️ Error crítico en README: {e}")

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
