from datetime import date, datetime, timedelta
import requests

SERVER = 'http://localhost:8000/'
HEADERS = {'Authorization': 'token 7e3f7c728e4b6c68de306db3da6e321f43222201'}

zona = 1


hoy = date.today().strftime("%Y-%m-%d")
horario = requests.get(SERVER + 'api/velocidad/horariodia/?fecha=' + hoy + '&zona=' + str(zona),
    headers = HEADERS
    )
horario = horario.json()
if (len(horario)>0):  
    fecha_str = horario[0]['fecha']
    hora_str = horario[0]['inicio']
    inicio_prod = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
    hora_str = horario[0]['fin']
    fin_prod = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
    if (fin_prod <= inicio_prod) :
        fin_prod += timedelta(days=1)

else:
    horario = None

print(horario)
