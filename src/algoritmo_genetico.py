import random
import numpy as np
from deap import base, creator, tools, algorithms
from database import (
    obtener_materias_con_area,
    obtener_docentes_por_area,
    obtener_dias,
    obtener_bloques,
)

# Configuración del algoritmo
POBLACION = 100
GENERACIONES = 200
PROB_CRUCE = 0.7
PROB_MUTACION = 0.3


def ejecutar_algoritmo(per_id, car_id, esc_id):
    # Obtener datos
    materias = obtener_materias_con_area(per_id, car_id)
    docentes = obtener_docentes_por_area(esc_id)
    dias = obtener_dias()
    bloques = obtener_bloques()

    if not materias or not dias or not bloques:
        return {"error": "No hay datos suficientes para generar horarios"}

    # Calcular bloques necesarios por materia
    clases = []
    for mat in materias:
        semanas = mat["per_semanas"] or 16
        horas_semana = (
            mat["mat_horas_docencia"] + mat["mat_horas_practicas"]
        ) // semanas

        # Distribuir en bloques de 2 horas preferentemente
        horas_restantes = horas_semana
        while horas_restantes > 0:
            if horas_restantes >= 2:
                duracion = 2
            else:
                duracion = 1
            clases.append(
                {
                    "pra_id": mat["pra_id"],
                    "mat_nombre": mat["mat_nombre"],
                    "arc_id": mat["arc_id"],
                    "doc_id": mat["doc_id"],
                    "pra_nivel": mat["pra_nivel"],
                    "par_id": mat["par_id"],
                    "duracion": duracion,
                }
            )
            horas_restantes -= duracion

    num_clases = len(clases)
    num_dias = len(dias)
    num_bloques = len(bloques)

    # Docentes disponibles por área
    docentes_por_area = {}
    for doc in docentes:
        for area_id in doc["areas"]:
            if area_id not in docentes_por_area:
                docentes_por_area[area_id] = []
            docentes_por_area[area_id].append(doc)

    # DEAP setup
    if hasattr(creator, "FitnessMax"):
        del creator.FitnessMax
    if hasattr(creator, "Individual"):
        del creator.Individual

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # Un gen = (dia_index, bloque_inicio_index, doc_id_asignado)
    def crear_gen():
        genes = []
        for clase in clases:
            dia_idx = random.randint(0, num_dias - 1)
            max_bloque = num_bloques - clase["duracion"]
            bloque_idx = random.randint(0, max(0, max_bloque))

            # Asignar docente por área o mantener el asignado
            if clase["doc_id"]:
                doc_id = clase["doc_id"]
            else:
                docs_disponibles = docentes_por_area.get(clase["arc_id"], [])
                doc_id = (
                    random.choice(docs_disponibles)["doc_id"]
                    if docs_disponibles
                    else None
                )

            genes.extend([dia_idx, bloque_idx, doc_id or 0])
        return genes

    toolbox.register("individual", tools.initIterate, creator.Individual, crear_gen)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluar(individuo):
        score = 1000.0
        penalizacion = 0

        # Decodificar individuo
        asignaciones = []
        for i in range(num_clases):
            base_idx = i * 3
            dia_idx = individuo[base_idx] % num_dias
            bloque_idx = individuo[base_idx + 1] % (
                num_bloques - clases[i]["duracion"] + 1
            )
            doc_id = individuo[base_idx + 2]
            asignaciones.append(
                {
                    "clase": clases[i],
                    "dia_idx": dia_idx,
                    "bloque_idx": bloque_idx,
                    "doc_id": doc_id,
                }
            )

        # Restricción 1: No cruce de docentes (mismo docente, mismo día, misma hora)
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

        # Restricción 2: No cruce de nivel+paralelo (mismos estudiantes)
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

        # Restricción 3: Horas del docente dentro de rango
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

        # Preferencia: Distribuir clases en diferentes días
        dias_usados = {}
        for a in asignaciones:
            key = (a["clase"]["pra_id"], a["dia_idx"])
            dias_usados[key] = dias_usados.get(key, 0) + 1
        for key, count in dias_usados.items():
            if count > 1:
                penalizacion += 10 * (count - 1)

        # Preferencia: Horarios en la mañana (7-13) sobre la tarde
        for a in asignaciones:
            if a["bloque_idx"] >= 7:
                penalizacion += 2

        score -= penalizacion
        return (max(score, 0),)

    def mutar(individuo):
        idx = random.randint(0, num_clases - 1)
        base_idx = idx * 3
        gene = random.randint(0, 2)
        if gene == 0:
            individuo[base_idx] = random.randint(0, num_dias - 1)
        elif gene == 1:
            max_bloque = num_bloques - clases[idx]["duracion"]
            individuo[base_idx + 1] = random.randint(0, max(0, max_bloque))
        else:
            clase = clases[idx]
            if not clase["doc_id"]:
                docs = docentes_por_area.get(clase["arc_id"], [])
                if docs:
                    individuo[base_idx + 2] = random.choice(docs)["doc_id"]
        return (individuo,)

    toolbox.register("evaluate", evaluar)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutar)
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Ejecutar algoritmo
    pop = toolbox.population(n=POBLACION)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("max", np.max)
    stats.register("avg", np.mean)

    pop, log = algorithms.eaSimple(
        pop,
        toolbox,
        cxpb=PROB_CRUCE,
        mutpb=PROB_MUTACION,
        ngen=GENERACIONES,
        stats=stats,
        halloffame=hof,
        verbose=True,
    )

    # Decodificar mejor solución
    mejor = hof[0]
    fitness_final = mejor.fitness.values[0]
    horarios_generados = []

    for i in range(num_clases):
        base_idx = i * 3
        dia_idx = mejor[base_idx] % num_dias
        bloque_idx = mejor[base_idx + 1] % (num_bloques - clases[i]["duracion"] + 1)
        doc_id = mejor[base_idx + 2]

        dia = dias[dia_idx]
        bloque_inicio = bloques[bloque_idx]
        bloque_fin = bloques[bloque_idx + clases[i]["duracion"] - 1]

        horarios_generados.append(
            {
                "pra_id": clases[i]["pra_id"],
                "dia_id": dia["dia_id"],
                "dia_nombre": dia["dia_nombre"],
                "blq_id_inicio": bloque_inicio["blq_id"],
                "blq_id_fin": bloque_fin["blq_id"],
                "hora_inicio": str(bloque_inicio["blq_hora_inicio"]),
                "hora_fin": str(bloque_fin["blq_hora_fin"]),
                "duracion": clases[i]["duracion"],
                "mat_nombre": clases[i]["mat_nombre"],
                "doc_id": doc_id if doc_id != 0 else None,
                "aul_id": None,
            }
        )

    return {
        "fitness": fitness_final,
        "generaciones": GENERACIONES,
        "poblacion": POBLACION,
        "total_clases": num_clases,
        "horarios": horarios_generados,
    }
