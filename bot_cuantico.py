import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml
import re

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Canal para 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    # Buscamos el chip real con menos cola
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Conectado a QPU Real: {backend.name}")

    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        # --- NUEVA LÓGICA DE CIRCUITO (SENSIBILIDAD BAJISTA) ---
        for i in range(len(datos)):
            # Usamos RX para una codificación más simétrica
            qml.RX(float(datos[i]), wires=i)
        
        # Entrelazamiento en cadena para propagar la tendencia
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
        qml.CNOT(wires=[3, 4])
        
        # Inversor PauliX en el qubit de medida para detectar caídas
        qml.PauliX(wires=4)
        
        # Medimos el valor esperado de PauliZ en el último qubit
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de Conexión: {e}"); exit(1)

# --- 2. DATOS DE MERCADO ---
try:
    # Descargamos datos de 15 min de Bitcoin
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    if df.empty:
        print("⚠️ No hay datos de Yahoo Finance"); exit(0)

    # Limpieza de datos (Anti-Series Error)
    precios = df['Close'].squeeze()
    if isinstance(precios, pd.DataFrame): precios = precios.iloc[:, 0]
    
    ultimo_p = float(precios.iloc[-1])
    # ADN: Cambios porcentuales de las últimas 4 velas
    cambios = precios.pct_change().dropna().tail(4).values
    
    # Filtro de Volatilidad (Ahorro de QPU)
    volatilidad = np.mean(np.abs(cambios)) * 100
    umbral_minimo = 0.20 # 0.02% de movimiento mínimo

    if volatilidad < umbral_minimo:
        print(f"😴 Mercado muy plano ({volatilidad:.4f}%). Veredicto 0.0.")
        resultado = 0.0
        status_backend = "Standby (Low Vol)"
    else:
        print(f"🔥 Volatilidad detectada ({volatilidad:.4f}%). Consultando Oráculo...")
        # Mapeo de datos a ángulos cuánticos
        adn = [np.arctan(float(x) * 100) for x in cambios]
        # Ejecución en IBM y conversión segura a float
        resultado = float(np.array(oraculo_cuantico(adn)).item())
        status_backend = backend.name

except Exception as e:
    print(f"❌ Error procesando datos: {e}"); exit(1)

# --- 3. ACTUALIZAR README (Semáforo Dinámico) ---
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
    
    try:
        with open(archivo_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        inicio = ""
        fin = ""

        # El nuevo bloque que queremos insertar
        nuevo_bloque = (
            f"{inicio}\n"
            f"> **Última Señal:** {semaforo} Precio BTC: ${precio:,.2f} Veredicto: {res:+.4f} | Hardware: {b_name}\n"
            f"{fin}"
        )

        # Buscamos el patrón desde la primera marca hasta la última
        # Esto evita que se dupliquen las líneas
        patron = re.compile(f"{re.escape(inicio)}.*?{re.escape(fin)}", re.DOTALL)

        if patron.search(contenido):
            # Reemplazamos todo el bloque antiguo por el nuevo
            nuevo_contenido = patron.sub(nuevo_bloque, contenido)
            with open(archivo_path, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            print("✅ README saneado y actualizado.")
        else:
            print("❌ No encontré las marcas. No he escrito nada para no duplicar.")

    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")

# --- 4. GUARDADO FORZOSO DEL CSV ---
archivo = 'backtest_cuantico.csv'
nueva_fila = pd.DataFrame([{
    'Fecha': datetime.now().strftime("%Y-%m-%d %H:%M"),
    'Veredicto': round(resultado, 4),
    'Precio': round(ultimo_p, 2),
    'Backend': status_backend
}])

# Adjuntamos la nueva fila al histórico
if os.path.exists(archivo):
    df_old = pd.read_csv(archivo)
    pd.concat([df_old, nueva_fila], ignore_index=True).to_csv(archivo, index=False)
else:
    nueva_fila.to_csv(archivo, index=False)

# Llamamos a la actualización del README antes de terminar
actualizar_readme(resultado, ultimo_p, volatilidad, status_backend)
print(f"🚀 Proceso completado. Veredicto final: {resultado:+.4f}")
