from datetime import datetime

def calcular_duracao(hora_inicio, hora_fim):
    h1 = datetime.combine(datetime.today(), hora_inicio)
    h2 = datetime.combine(datetime.today(), hora_fim)
    duracao = (h2 - h1).total_seconds() / 3600  # horas
    return round(duracao, 2)