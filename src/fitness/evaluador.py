from models.cromosoma import decodificar_individuo


def evaluar(individuo, clases, num_dias, num_bloques, docentes):
    score = 1000.0
    penalizacion = 0

    asignaciones = decodificar_individuo(individuo, clases, num_dias, num_bloques)

    # Restricción 1: No cruce de docentes (mismo docente, mismo día, misma hora)
    penalizacion += verificar_cruce_docentes(asignaciones)

    # Restricción 2: No cruce de nivel+paralelo (mismos estudiantes)
    penalizacion += verificar_cruce_estudiantes(asignaciones)

    # Restricción 3: Horas del docente dentro de rango
    penalizacion += verificar_horas_docentes(asignaciones, docentes)

    # Preferencia 1: Distribuir clases en diferentes días
    penalizacion += verificar_distribucion_dias(asignaciones)

    # Preferencia 2: Horarios de mañana sobre tarde
    penalizacion += verificar_preferencia_horario(asignaciones)

    # Preferencia 3: No más de una clase del mismo nivel+paralelo por bloque consecutivo largo
    penalizacion += verificar_carga_diaria(asignaciones)

    score -= penalizacion
    return (max(score, 0),)


def verificar_cruce_docentes(asignaciones):
    penalizacion = 0
    for i in range(len(asignaciones)):
        for j in range(i + 1, len(asignaciones)):
            a1 = asignaciones[i]
            a2 = asignaciones[j]
            if a1["doc_id"] == a2["doc_id"] and a1["doc_id"] != 0:
                if a1["dia_idx"] == a2["dia_idx"]:
                    inicio1 = a1["bloque_idx"]
                    fin1 = inicio1 + a1["clase"]["duracion"]
                    inicio2 = a2["bloque_idx"]
                    fin2 = inicio2 + a2["clase"]["duracion"]
                    if inicio1 < fin2 and inicio2 < fin1:
                        penalizacion += 100
    return penalizacion


def verificar_cruce_estudiantes(asignaciones):
    penalizacion = 0
    for i in range(len(asignaciones)):
        for j in range(i + 1, len(asignaciones)):
            a1 = asignaciones[i]
            a2 = asignaciones[j]
            if (
                a1["clase"]["pra_nivel"] == a2["clase"]["pra_nivel"]
                and a1["clase"]["par_id"] == a2["clase"]["par_id"]
            ):
                if a1["dia_idx"] == a2["dia_idx"]:
                    inicio1 = a1["bloque_idx"]
                    fin1 = inicio1 + a1["clase"]["duracion"]
                    inicio2 = a2["bloque_idx"]
                    fin2 = inicio2 + a2["clase"]["duracion"]
                    if inicio1 < fin2 and inicio2 < fin1:
                        penalizacion += 100
    return penalizacion


def verificar_horas_docentes(asignaciones, docentes):
    penalizacion = 0
    horas_docente = {}
    for a in asignaciones:
        doc_id = a["doc_id"]
        if doc_id and doc_id != 0:
            horas_docente[doc_id] = (
                horas_docente.get(doc_id, 0) + a["clase"]["duracion"]
            )

    for doc in docentes:
        horas = horas_docente.get(doc["doc_id"], 0)
        if horas > doc["doc_horas_maximas"]:
            penalizacion += 50 * (horas - doc["doc_horas_maximas"])
        if horas > 0 and horas < doc["doc_horas_minimas"]:
            penalizacion += 20 * (doc["doc_horas_minimas"] - horas)
    return penalizacion


def verificar_distribucion_dias(asignaciones):
    penalizacion = 0
    dias_usados = {}
    for a in asignaciones:
        key = (a["clase"]["pra_id"], a["dia_idx"])
        dias_usados[key] = dias_usados.get(key, 0) + 1
    for key, count in dias_usados.items():
        if count > 1:
            penalizacion += 10 * (count - 1)
    return penalizacion


def verificar_preferencia_horario(asignaciones):
    penalizacion = 0
    for a in asignaciones:
        if a["bloque_idx"] >= 7:
            penalizacion += 2
    return penalizacion


def verificar_carga_diaria(asignaciones):
    penalizacion = 0
    carga_por_dia = {}
    for a in asignaciones:
        key = (a["clase"]["pra_nivel"], a["clase"]["par_id"], a["dia_idx"])
        carga_por_dia[key] = carga_por_dia.get(key, 0) + a["clase"]["duracion"]
    for key, horas in carga_por_dia.items():
        if horas > 6:
            penalizacion += 15 * (horas - 6)
    return penalizacion
