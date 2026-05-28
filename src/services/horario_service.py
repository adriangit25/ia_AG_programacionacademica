import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import ejecutar_query, ejecutar_update, get_connection


def obtener_programacion(per_id, car_id):
    return ejecutar_query(
        """
        SELECT pa.pra_id, pa.mat_id, pa.doc_id, pa.aul_id, pa.pra_nivel, pa.par_id,
               m.mat_nombre, m.mat_codigo, m.mat_horas_docencia, m.mat_horas_practicas,
               m.arc_id, pe.per_semanas
        FROM tbl_programacion_academica pa
        INNER JOIN tbl_materias m ON pa.mat_id = m.mat_id
        INNER JOIN tbl_periodos pe ON pa.per_id = pe.per_id
        WHERE pa.per_id = %s AND pa.car_id = %s AND pa.pra_estado = TRUE
        ORDER BY pa.pra_nivel, m.mat_nombre
    """,
        (per_id, car_id),
    )


def obtener_docentes(esc_id):
    return ejecutar_query(
        """
        SELECT d.doc_id, u.usu_nombres, u.usu_apellidos,
               d.doc_dedicacion, d.doc_horas_minimas, d.doc_horas_maximas,
               array_agg(da.arc_id) as areas
        FROM tbl_docentes d
        INNER JOIN tbl_usuarios u ON d.usu_id = u.usu_id
        INNER JOIN tbl_docente_area da ON d.doc_id = da.doc_id
        WHERE d.esc_id = %s AND d.doc_estado = TRUE AND da.doa_estado = TRUE
        GROUP BY d.doc_id, u.usu_nombres, u.usu_apellidos,
                 d.doc_dedicacion, d.doc_horas_minimas, d.doc_horas_maximas
        ORDER BY u.usu_apellidos
    """,
        (esc_id,),
    )


def obtener_dias():
    return ejecutar_query(
        "SELECT dia_id, dia_nombre, dia_orden FROM tbl_dias ORDER BY dia_orden"
    )


def obtener_bloques():
    return ejecutar_query(
        "SELECT blq_id, blq_hora_inicio, blq_hora_fin, blq_orden FROM tbl_bloques_horarios ORDER BY blq_orden"
    )


def guardar_horarios(horarios):
    conn = get_connection()
    cur = conn.cursor()
    ids_guardados = []
    for h in horarios:
        cur.execute(
            """
            INSERT INTO tbl_horarios (pra_id, dia_id, blq_id_inicio, blq_id_fin, aul_id, hor_duracion, hor_observaciones, hor_estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'Generado por IA', TRUE)
            RETURNING hor_id
        """,
            (
                h["pra_id"],
                h["dia_id"],
                h["blq_id_inicio"],
                h["blq_id_fin"],
                h.get("aul_id"),
                h["duracion"],
            ),
        )
        ids_guardados.append(cur.fetchone()[0])
    conn.commit()
    cur.close()
    conn.close()
    return ids_guardados


def limpiar_horarios_ia(per_id, car_id):
    return ejecutar_update(
        """
        UPDATE tbl_horarios SET hor_estado = FALSE
        WHERE pra_id IN (
            SELECT pra_id FROM tbl_programacion_academica
            WHERE per_id = %s AND car_id = %s AND pra_estado = TRUE
        ) AND hor_observaciones = 'Generado por IA' AND hor_estado = TRUE
    """,
        (per_id, car_id),
    )


def generar_clases(materias):
    clases = []
    for mat in materias:
        semanas = mat["per_semanas"] or 16
        horas_semana = (
            mat["mat_horas_docencia"] + mat["mat_horas_practicas"]
        ) // semanas

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
    return clases


def agrupar_docentes_por_area(docentes):
    docentes_por_area = {}
    for doc in docentes:
        for area_id in doc["areas"]:
            if area_id not in docentes_por_area:
                docentes_por_area[area_id] = []
            docentes_por_area[area_id].append(doc)
    return docentes_por_area
