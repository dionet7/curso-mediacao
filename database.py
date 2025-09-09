import sqlite3

def conectar():
    return sqlite3.connect("database.db")

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno TEXT,
            data TEXT,
            hora_inicio TEXT,
            hora_fim TEXT,
            tipo_atividade TEXT,
            observadores TEXT,
            co_mediador TEXT,
            duracao_horas REAL
        );
    """)
    conn.commit()
    conn.close()

# def inserir_participacao(aluno, data, hora_inicio, hora_fim, tipo, observadores, co_mediador, duracao):
#     conn = conectar()
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO participacoes (
#             aluno, data, hora_inicio, hora_fim, tipo_atividade,
#             observadores, co_mediador, duracao_horas
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
#     """, (aluno, str(data), str(hora_inicio), str(hora_fim), tipo, observadores, co_mediador, duracao))
#     conn.commit()
#     conn.close()

def inserir_participacao(aluno, data, hora_inicio, hora_fim, tipo, observadores, co_mediador, duracao):
    conn = conectar()
    cursor = conn.cursor()

    # Registro do aluno principal
    cursor.execute("""
        INSERT INTO participacoes (
            aluno, data, hora_inicio, hora_fim, tipo_atividade,
            observadores, co_mediador, duracao_horas
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (aluno, str(data), str(hora_inicio), str(hora_fim), tipo, observadores, co_mediador, duracao))

    # Registro para co-mediador (se houver)
    if tipo == "Co-mediação" and co_mediador:
        cursor.execute("""
            INSERT INTO participacoes (
                aluno, data, hora_inicio, hora_fim, tipo_atividade,
                observadores, co_mediador, duracao_horas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (co_mediador, str(data), str(hora_inicio), str(hora_fim), tipo, aluno, observadores, duracao))

    # Registro para cada observador (como "Observação")
    if observadores:
        for obs in observadores.split(","):
            obs = obs.strip()
            if obs and obs != aluno and obs != co_mediador:
                cursor.execute("""
                    INSERT INTO participacoes (
                        aluno, data, hora_inicio, hora_fim, tipo_atividade,
                        observadores, co_mediador, duracao_horas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (obs, str(data), str(hora_inicio), str(hora_fim), "Observação", aluno, co_mediador, duracao))

    conn.commit()
    conn.close()
