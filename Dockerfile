# Usamos una imagen de Python estable
FROM python:3.9-slim

# Instalamos dependencias del sistema
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Instalamos las versiones EXACTAS que no chocan
RUN pip install --no-cache-dir \
    qiskit==0.45.2 \
    qiskit-ibm-runtime==0.20.0 \
    pennylane==0.33.1 \
    pennylane-qiskit==0.33.0 \
    autoray==0.6.7 \
    yfinance pandas numpy

# Copiamos tu código al contenedor
COPY bot_cuantico.py /bot_cuantico.py
COPY backtest_cuantico.csv /backtest_cuantico.csv

# Comando para ejecutar
CMD ["python", "/bot_cuantico.py"]
