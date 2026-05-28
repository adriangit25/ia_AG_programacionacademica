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


def ejecutar_query(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultados


def ejecutar_insert(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result


def ejecutar_update(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rowcount = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rowcount
