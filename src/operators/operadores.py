import random


def mutar(individuo, clases, num_dias, num_bloques, docentes_por_area):
    num_clases = len(clases)
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
