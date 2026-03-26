# 🌌 Oráculo Cuántico BTC

![Estado del Bot](https://github.com/alconero-hub/oraculo_cuantico/actions/workflows/run_bot.yml/badge.svg)
![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-green.svg)

Este es un bot de trading experimental que utiliza **computación cuántica real** (IBM Quantum) para analizar la volatilidad de Bitcoin y generar veredictos de mercado mediante entrelazamiento de qubits.

## 🚀 ¿Cómo funciona?
1. **Captura de Datos**: El bot descarga los últimos 60 minutos de velas de BTC-USD vía Yahoo Finance.
2. **ADN Cuántico**: Transforma los cambios porcentuales de precio en ángulos de rotación (puertas RX).
3. **Procesamiento en QPU**: Ejecuta un circuito de entrelazamiento en un procesador cuántico real de IBM.
4. **Veredicto**: Si el resultado (valor esperado) es positivo, la tendencia es alcista; si es negativo, es bajista.

## 🚦 Estado del Oráculo
> **Última Señal:** ⏳ Esperando ejecución limpia del sistema...
## 📈 Rendimiento Histórico
La gráfica a continuación muestra la relación entre el precio (línea naranja) y los veredictos cuánticos (barras).

![Gráfica de Rendimiento](./rendimiento_cuantico.png)

## 🛠️ Instalación y Configuración
Si quieres clonar este oráculo:

1. Obtén tu API Token en [IBM Quantum Computing](https://quantum-computing.ibm.com/).
2. Añádelo a los **Secrets** de tu repositorio de GitHub con el nombre `IBM_QUANTUM_TOKEN`.
3. El bot se activará automáticamente cada 120 minutos.

## 📊 Detalles Técnicos
| Concepto | Tecnología |
| :--- | :--- |
| **Hardware** | IBM Quantum (QPU Real) |
| **Librería Cuántica** | PennyLane + Qiskit 1.x |
| **Frecuencia** | Cada 2 horas |
| **Activo** | BTC-USD |

## ⚠️ Descargo de Responsabilidad
Este proyecto es **estrictamente educativo y experimental**. La computación cuántica en el sector financiero está en fase de investigación. No constituye asesoramiento financiero. El "ruido" de los procesadores actuales puede afectar los veredictos.

---
*Powered by IBM Quantum Platform & PennyLane*
---
*Desarrollado con ❤️ y partículas entrelazadas por alconero-hub*
