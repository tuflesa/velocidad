from datetime import date, datetime, timedelta
import requests

SERVER = 'http://localhost:8000/'
HEADERS = {'Authorization': 'token 7e3f7c728e4b6c68de306db3da6e321f43222201'}

zona = 4


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

    id = horario[0]['turno_tarde']['id']
    maquinista = horario[0]['turno_tarde']['maquinista']['get_full_name']
    turno_mañana = horario[0]['turno_mañana']
    turno_tarde = horario[0]['turno_tarde']
    turno_noche = horario[0]['turno_noche']
    cambio_turno_1_str = horario[0]['cambio_turno_1']
    cambio_turno_2_str = horario[0]['cambio_turno_2']
    cambio_turno_1 = None if not cambio_turno_1_str else datetime.strptime(f"{fecha_str} {cambio_turno_1_str}", "%Y-%m-%d %H:%M:%S")
    cambio_turno_2 = None if not cambio_turno_2_str else datetime.strptime(f"{fecha_str} {cambio_turno_2_str}", "%Y-%m-%d %H:%M:%S")
    # print(f'turno tarde {id} - {turno_tarde} - {maquinista}')
    # print(f'cambio turno 1 {cambio_turno_1}')
    # print(f'cambio turno 2 {cambio_turno_2}')

    ahora = datetime.now()
    n_turnos = 2
    if ((ahora < cambio_turno_1) or (n_turnos == 1)):
        turno_activo = turno_mañana
    elif ((ahora >= cambio_turno_1 and n_turnos == 2) or (n_turnos == 3 and ahora < cambio_turno_2 and ahora >= cambio_turno_1)):
        turno_activo = turno_tarde
    elif (n_turnos == 3 and ahora >= cambio_turno_2):
        turno_activo = turno_noche
    else:
        horario = None

    print(f"Turno activo = {turno_activo['id']} {type(turno_activo['id'])}")
