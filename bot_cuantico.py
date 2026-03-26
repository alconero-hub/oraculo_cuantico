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
    umbral_minimo = 0.02 # 0.02% de movimiento mínimo

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
¡Perfecto! Aquí tienes el bot_cuantico.py completo y blindado.

He unificado la función de actualización del README con la lógica de "sustitución radical" que comentamos, asegurándome de que las etiquetas coincidan exactamente con el README.md que te acabo de dar.

📄 Archivo: bot_cuantico.py (Versión Definitiva 2026)
Python
import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
import pennylane as qml

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
# El token debe estar configurado en GitHub Secrets como IBM_QUANTUM_TOKEN
token = os.getenv("IBM_QUANTUM_TOKEN")

try:
    # Canal oficial para 2026
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    # Seleccionamos el hardware real con menos carga de trabajo
    backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
    print(f"📡 Conectado a QPU Real: {backend.name}")

    # Configuración del dispositivo PennyLane con el backend de IBM
    dev = qml.device('qiskit.remote', wires=5, backend=backend, shots=1024)

    @qml.qnode(dev)
    def oraculo_cuantico(datos):
        # 1. Codificación de datos mediante rotaciones en el eje X (RX)
        for i in range(len(datos)):
            qml.RX(float(datos[i]), wires=i)
        
        # 2. Entrelazamiento CNOT en cadena para correlacionar los cambios
        qml.CNOT(wires=[0, 1])
        qml.CNOT(wires=[1, 2])
        qml.CNOT(wires=[2, 3])
        qml.CNOT(wires=[3, 4])
        
        # 3. Puerta PauliX para mejorar la detección de tendencias bajistas
        qml.PauliX(wires=4)
        
        # 4. Medición del valor esperado de PauliZ
        return qml.expval(qml.PauliZ(4))

except Exception as e:
    print(f"❌ Error de Conexión/QPU: {e}")
    exit(1)

# --- 2. CAPTURA DE DATOS Y FILTRO DE VOLATILIDAD ---
try:
    # Descarga de datos de BTC (velas de 15 minutos)
    df = yf.download("BTC-USD", period="1d", interval="15m", progress=False, auto_adjust=True)
    if df.empty:
        print("⚠️ No se obtuvieron datos de Yahoo Finance.")
        exit(0)

    # Limpieza de Series para evitar errores de formato
    precios = df['Close'].squeeze()
    if isinstance(precios, pd.DataFrame): 
        precios = precios.iloc[:, 0]
    
    ultimo_p = float(precios.iloc[-1])
    # Analizamos las últimas 4 variaciones (1 hora de datos aprox)
    cambios = precios.pct_change().dropna().tail(4).values
    
    # Cálculo de volatilidad para el Modo Ahorro
    volatilidad = np.mean(np.abs(cambios)) * 100
    umbral_minimo = 0.01 # 0.01% de movimiento mínimo para activar la QPU

    if volatilidad < umbral_minimo:
        print(f"😴 Mercado lateral ({volatilidad:.4f}%). Veredicto 0.0 automático.")
        resultado = 0.0
        status_backend = "Standby (Ahorro QPU)"
    else:
        print(f"🔥 Volatilidad detectada ({volatilidad:.4f}%). Consultando a IBM...")
        # Mapeo de ADN Cuántico (arctan para normalizar ángulos)
        adn = [np.arctan(float(x) * 100) for x in cambios]
        # Ejecución en el procesador real
        resultado = float(np.array(oraculo_cuantico(adn)).item())
        status_backend = backend.name

except Exception as e:
    print(f"❌ Error en el procesamiento de datos: {e}")
    exit(1)

# --- 3. FUNCIÓN DE ACTUALIZACIÓN DEL README (Sustitución Radical) ---
def actualizar_readme(res, precio, vol, b_name):
    # Definición de iconos del semáforo
    if vol < umbral_minimo:
        semaforo = "⚪ **DORMIDO** (Mercado Lateral)"
    elif res > 0.15: 
        semaforo = "🟢 **COMPRA** (Señal Alcista Fuerte)"
    elif res < -0.15: 
        semaforo = "🔴 **VENTA** (Señal Bajista Fuerte)"
    else: 
        semaforo = "🟡 **ESPERA** (Incertidumbre/Ruido)"

    try:
        archivo_path = "README.md"
        if not os.path.exists(archivo_path):
            print("⚠️ README.md no encontrado para actualizar.")
            return

        with open(archivo_path, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        inicio_marca = ""
        fin_marca = ""
        
        # Construimos el nuevo bloque de información
        nuevo_bloque = (
            f"{inicio_marca}\n"
            f"> **Última Señal:** {semaforo}\n"
            f"> **Precio BTC:** ${precio:,.2f}\n"
            f"> **Veredicto Cuántico:** {res:+.4f}\n"
            f"> **Volatilidad:** {vol:.4f}%\n"
            f"> **Hardware:** {b_name}\n"
            f"> **Actualizado:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"{fin_marca}"
        )

        # Sustitución entre etiquetas
        if inicio_marca in contenido and fin_marca in contenido:
            parte_pre = contenido.split(inicio_marca)[0]
            parte_post = contenido.split(fin_marca)[1]
            
            with open(archivo_path, "w", encoding="utf-8") as f:
                f.write(f"{parte_pre}{nuevo_bloque}{parte_post}")
            print("✅ README.md actualizado con la señal actual.")
        else:
            print("❌ No se encontraron las marcas de comentario en el README.")

    except Exception as e:
        print(f"⚠️ Error al escribir en README: {e}")

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
actualizar_readme(resultado, ultimo_p, volatilidad)
print(f"🚀 Proceso completado. Veredicto final: {resultado:+.4f}")
