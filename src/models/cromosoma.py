import random


def crear_gen(clases, num_dias, num_bloques, docentes_por_area):
    genes = []
    for clase in clases:
        dia_idx = random.randint(0, num_dias - 1)
        max_bloque = num_bloques - clase["duracion"]
        bloque_idx = random.randint(0, max(0, max_bloque))

        if clase["doc_id"]:
            doc_id = clase["doc_id"]
        else:
            docs_disponibles = docentes_por_area.get(clase["arc_id"], [])
            doc_id = (
                random.choice(docs_disponibles)["doc_id"] if docs_disponibles else None
            )

        genes.extend([dia_idx, bloque_idx, doc_id or 0])
    return genes


def decodificar_individuo(individuo, clases, num_dias, num_bloques):
    asignaciones = []
    for i in range(len(clases)):
        base_idx = i * 3
        dia_idx = individuo[base_idx] % num_dias
        max_bloque = num_bloques - clases[i]["duracion"] + 1
        bloque_idx = individuo[base_idx + 1] % max(1, max_bloque)
        doc_id = individuo[base_idx + 2]
        asignaciones.append(
            {
                "clase": clases[i],
                "dia_idx": dia_idx,
                "bloque_idx": bloque_idx,
                "doc_id": doc_id,
            }
        )
    return asignaciones
