import sys
import os
import random
import numpy as np
from deap import base, creator, tools, algorithms

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.horario_service import (
    obtener_programacion,
    obtener_docentes,
    obtener_dias,
    obtener_bloques,
    generar_clases,
    agrupar_docentes_por_area,
)
from models.cromosoma import crear_gen, decodificar_individuo
from fitness.evaluador import evaluar
from operators.operadores import mutar

# Configuración del algoritmo
POBLACION = 100
GENERACIONES = 200
PROB_CRUCE = 0.7
PROB_MUTACION = 0.3


def ejecutar_algoritmo(per_id, car_id, esc_id):
    # Obtener datos
    materias = obtener_programacion(per_id, car_id)
    docentes = obtener_docentes(esc_id)
    dias = obtener_dias()
    bloques = obtener_bloques()

    if not materias or not dias or not bloques:
        return {"error": "No hay datos suficientes para generar horarios"}

    # Preparar datos
    clases = generar_clases(materias)
    docentes_por_area = agrupar_docentes_por_area(docentes)
    num_clases = len(clases)
    num_dias = len(dias)
    num_bloques = len(bloques)

    # DEAP setup
    if hasattr(creator, "FitnessMax"):
        del creator.FitnessMax
    if hasattr(creator, "Individual"):
        del creator.Individual

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register(
        "individual",
        tools.initIterate,
        creator.Individual,
        lambda: crear_gen(clases, num_dias, num_bloques, docentes_por_area),
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register(
        "evaluate", lambda ind: evaluar(ind, clases, num_dias, num_bloques, docentes)
    )
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register(
        "mutate",
        lambda ind: mutar(ind, clases, num_dias, num_bloques, docentes_por_area),
    )
    toolbox.register("select", tools.selTournament, tournsize=3)

    # Ejecutar
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
    asignaciones = decodificar_individuo(mejor, clases, num_dias, num_bloques)

    horarios_generados = []
    for a in asignaciones:
        dia = dias[a["dia_idx"]]
        bloque_inicio = bloques[a["bloque_idx"]]
        bloque_fin = bloques[a["bloque_idx"] + a["clase"]["duracion"] - 1]

        horarios_generados.append(
            {
                "pra_id": a["clase"]["pra_id"],
                "dia_id": dia["dia_id"],
                "dia_nombre": dia["dia_nombre"],
                "blq_id_inicio": bloque_inicio["blq_id"],
                "blq_id_fin": bloque_fin["blq_id"],
                "hora_inicio": str(bloque_inicio["blq_hora_inicio"]),
                "hora_fin": str(bloque_fin["blq_hora_fin"]),
                "duracion": a["clase"]["duracion"],
                "mat_nombre": a["clase"]["mat_nombre"],
                "doc_id": a["doc_id"] if a["doc_id"] != 0 else None,
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
