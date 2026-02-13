import pyodbc

registro = {
    "xIdOF": "OF000123",
    "xIdTipo": "T001",
    "xIdPos": 1,
    "xIdParada": "P045",
    "xDescripcion": "Parada por ajuste",
    "xFecha": "2024-01-15 10:30:00",
    "xTiempo": 15,
    "xObservaciones": "Ajuste de máquina",
    "xTurno": "A",
    "xIgnorar": 0
}

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=TU_SERVIDOR;"
    "DATABASE=TU_BD;"
    "UID=usuario;"
    "PWD=contraseña;"
)

cursor = conn.cursor()

sql = """
INSERT INTO imp.tb_tubo_parada (
    xIdOF,
    xIdTipo,
    xIdPos,
    xIdParada,
    xDescripcion,
    xFecha,
    xTiempo,
    xObservaciones,
    xTurno,
    xIgnorar
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

cursor.execute(sql, (
    registro["xIdOF"],
    registro["xIdTipo"],
    registro["xIdPos"],
    registro["xIdParada"],
    registro["xDescripcion"],
    registro["xFecha"],
    registro["xTiempo"],
    registro["xObservaciones"],
    registro["xTurno"],
    registro["xIgnorar"]
))

conn.commit()
cursor.close()
conn.close()