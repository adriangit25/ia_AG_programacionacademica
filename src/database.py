import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def obtener_programacion(per_id, car_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pa.pra_id, pa.mat_id, pa.doc_id, pa.aul_id, pa.pra_nivel, pa.par_id,
               m.mat_nombre, m.mat_codigo, m.mat_horas_docencia, m.mat_horas_practicas,
               pe.per_semanas
        FROM tbl_programacion_academica pa
        INNER JOIN tbl_materias m ON pa.mat_id = m.mat_id
        INNER JOIN tbl_periodos pe ON pa.per_id = pe.per_id
        WHERE pa.per_id = %s AND pa.car_id = %s AND pa.pra_estado = TRUE
        ORDER BY pa.pra_nivel, m.mat_nombre
    """,
        (per_id, car_id),
    )
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


def obtener_docentes_por_area(esc_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.doc_id, u.usu_nombres, u.usu_apellidos,
               d.doc_dedicacion, d.doc_horas_minimas, d.doc_horas_maximas,
               array_agg(da.arc_id) as areas
        FROM tbl_docentes d
        INNER JOIN tbl_usuarios u ON d.usu_id = u.usu_id
        INNER JOIN tbl_docente_area da ON d.doc_id = da.doc_id
        WHERE d.esc_id = %s AND d.doc_estado = TRUE AND da.doa_estado = TRUE
        GROUP BY d.doc_id, u.usu_nombres, u.usu_apellidos, d.doc_dedicacion, d.doc_horas_minimas, d.doc_horas_maximas
        ORDER BY u.usu_apellidos
    """,
        (esc_id,),
    )
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


def obtener_materias_con_area(per_id, car_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pa.pra_id, m.mat_id, m.arc_id, m.mat_nombre, m.mat_codigo,
               m.mat_horas_docencia, m.mat_horas_practicas,
               pa.doc_id, pa.pra_nivel, pa.par_id,
               pe.per_semanas
        FROM tbl_programacion_academica pa
        INNER JOIN tbl_materias m ON pa.mat_id = m.mat_id
        INNER JOIN tbl_periodos pe ON pa.per_id = pe.per_id
        WHERE pa.per_id = %s AND pa.car_id = %s AND pa.pra_estado = TRUE
        ORDER BY pa.pra_nivel
    """,
        (per_id, car_id),
    )
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


def obtener_dias():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT dia_id, dia_nombre, dia_orden FROM tbl_dias ORDER BY dia_orden")
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


def obtener_bloques():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT blq_id, blq_hora_inicio, blq_hora_fin, blq_orden FROM tbl_bloques_horarios ORDER BY blq_orden"
    )
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tbl_horarios SET hor_estado = FALSE
        WHERE pra_id IN (
            SELECT pra_id FROM tbl_programacion_academica
            WHERE per_id = %s AND car_id = %s AND pra_estado = TRUE
        ) AND hor_observaciones = 'Generado por IA' AND hor_estado = TRUE
    """,
        (per_id, car_id),
    )
    eliminados = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return eliminados
