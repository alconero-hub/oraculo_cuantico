import os
from datetime import datetime

def actualizar_solo_test():
    inicio_marca = ""
    fin_marca = ""
    
    with open("README.md", "r", encoding="utf-8") as f:
        contenido = f.read()
    
    nuevo_bloque = (
        f"{inicio_marca}\n"
        f"> **Última Señal:** 🟢 **TEST EXITOSO**\n"
        f"> **Actualizado:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"{fin_marca}"
    )

    if inicio_marca in contenido and fin_marca in contenido:
        parte_pre = contenido.split(inicio_marca)[0]
        parte_post = contenido.split(fin_marca)[1]
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(f"{parte_pre}{nuevo_bloque}{parte_post}")
        print("✅ Test completado.")

actualizar_solo_test()
