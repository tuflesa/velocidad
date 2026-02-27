import snap7
from snap7.util import get_real
import threading
import requests
import time
from datetime import date, datetime, timedelta

# Listado de máquinas con control de velocidad
SERVER = 'http://10.128.100.242:8000/'
# SERVER = 'http://localhost:8000/'
# HEADERS = {'Authorization': 'token 99c11d78d18c18c99247a0a50ede33d8e223767a'}
HEADERS = {'Authorization': 'token 7e3f7c728e4b6c68de306db3da6e321f43222201'}

def get_speed(linea):
    MAX_ERRORES = 3

    arranque = True
    v_actual = 0
    hf_pot_actual = 0
    hf_freq_actual = 0
    welding_press_actual = 0
    v_registro = None
    v_real = None
    v_registro_anterior = None
    hf_pot_registro = None
    hf_pot_registro_anterior = None
    hf_freq_registro =None
    hf_freq_registro_anterior = None
    welding_press_registro = None
    welding_press_registro_anterior = None
    datos = []
    periodos = []
    n_errores = 0
    
    horario = None
    tnp = None
    cambio_tnp = False
    inicio_prod = None
    fin_prod = None
    turno_mañana = None
    turno_tarde = None
    turno_noche = None
    cambio_turno_1_str = None
    cambio_turno_2_str = None
    cambio_turno_1 = None
    cambio_turno_2 = None
    leerhorario = True
    es_festivo = None
    cambios_de_turno_habilitados = False
    n_turnos = 0
    turno_activo = None
    turno = None
    cambio_de_turno = False
    hora_cambio_turno = None

    IP = linea['ip'] 
    RACK = linea['rack'] 
    SLOT = linea['slot']
    DB = linea['db']
    DW = linea['dw'] 
    NWORDS = linea['nwords']
    siglas = linea['zona']['siglas']
    zona = linea['zona']['id']

    plc = snap7.client.Client()

    while (True):
        if plc.get_connected() == False:
            try:
                plc.connect(IP, RACK, SLOT)
                state = plc.get_cpu_state()
                print(f'Máquina {siglas} State: {state}')
            except:
                arranque = True
                print(f'Máquina {siglas} Error de conexión')

        else:
            try:
                fromPLC = plc.db_read(DB, DW, NWORDS)
                v_real = get_real(fromPLC, 0)
                if (NWORDS > 4):
                    hf_power = get_real(fromPLC, 4)
                    hf_freq = get_real(fromPLC, 8)
                    welding_press = get_real(fromPLC, 12)
                else:
                    hf_power = 0
                    hf_freq = 0
                    welding_press = 0

                inc_velocidad = abs(v_actual - v_real)
                inc_hf_power = abs(hf_pot_actual - hf_power)
                inc_hf_freq = abs(hf_freq_actual - hf_freq)
                inc_welding_press = abs(welding_press_actual - welding_press)

                if (inc_velocidad > 1.5 or inc_hf_power > 5 or inc_hf_freq > 5 or inc_welding_press > 5 or 
                    arranque or cambio_de_turno or cambio_tnp):
                    v_actual = v_real
                    hf_pot_actual = hf_power
                    hf_freq_actual = hf_freq
                    welding_press_actual = welding_press
                    if (v_real > 9): # Automatico
                        v_registro = v_real
                        hf_pot_registro = hf_pot_actual
                        hf_freq_registro = hf_freq_actual
                        welding_press_registro = welding_press_actual
                    else: # Manual no se registra
                        v_registro = 0.0
                        hf_pot_registro = 0.0
                        hf_freq_registro = 0.0
                        welding_press_registro = 0.0
                    
                    hoy = date.today()
                    ahora = datetime.now()

                    if cambio_tnp:
                        if tnp:
                            fecha_registro = fin_prod
                        else:
                            fecha_registro = inicio_prod
                    
                    if cambio_de_turno and turno_activo != None:
                        fecha_registro = hora_cambio_turno
                    
                    if (not cambio_de_turno and not cambio_tnp) or arranque:
                        fecha_registro = hoy.strftime("%Y-%m-%d") + ' ' + ahora.strftime("%H:%M:%S")

                    if (horario!=None):
                        if(ahora >= inicio_prod and ahora <= fin_prod and not (es_festivo)): 
                            tnp = False
                        else: 
                            tnp = True

                    dato = {
                            'fecha': hoy.strftime("%Y-%m-%d"),
                            'hora': ahora.strftime("%H:%M:%S"),
                            'zona': zona,
                            'velocidad': v_registro,
                            'potencia': hf_pot_registro,
                            'frecuencia': hf_freq_registro,
                            'presion': welding_press_registro
                        }
                    periodo = {
                            'zona': zona,
                            'fecha': fecha_registro,
                            'velocidad': v_registro,
                            'tnp': tnp,
                            'turno': 0 if not turno_activo else turno_activo['id']
                        }
                        
                    if (v_registro != v_registro_anterior or
                        hf_pot_registro != hf_pot_registro_anterior or
                        hf_freq_registro != hf_freq_registro_anterior or
                        welding_press_registro != welding_press_registro_anterior or
                        arranque or
                        cambio_de_turno or
                        cambio_tnp):

                        arranque = False
                        cambio_de_turno = False   
                        cambio_tnp = False 
                        datos.append(dato)
                        periodos.append(periodo)

                        v_registro_anterior = v_registro
                        hf_pot_registro_anterior = hf_pot_registro
                        hf_freq_registro_anterior = hf_freq_registro
                        welding_press_registro_anterior = welding_press_registro

                n_errores = 0

            except: # Perdida conexión PLC
                plc.disconnect()
                n_errores += 1
                if n_errores > MAX_ERRORES:
                    hoy = date.today()
                    ahora = datetime.now()
                    dato = {
                            'fecha': hoy.strftime("%Y-%m-%d"),
                            'hora': ahora.strftime("%H:%M:%S"),
                            'zona': zona,
                            'velocidad': -1
                        }
                    periodo = {
                                'zona': zona,
                                'fecha': hoy.strftime("%Y-%m-%d") + ' ' + ahora.strftime("%H:%M:%S") ,
                                'velocidad': -1, 
                                'tnp': tnp,
                                'turno': 0 if not turno_activo else turno_activo['id']
                            }
                    print('perdida de conexión ', periodo)
                    datos.append(dato)
                    periodos.append(periodo)

        # Actualizar horario
        if (not horario or leerhorario):
            try:
                hoy = date.today().strftime("%Y-%m-%d")
                horario = requests.get(SERVER + 'api/velocidad/horariodia/?fecha=' + hoy + '&zona=' + str(zona),
                    headers = HEADERS
                )
                horario = horario.json()
                leerhorario = False
                fecha_str = horario[0]['fecha']
                hora_str = horario[0]['inicio']
                es_festivo = horario[0]['es_festivo']
                inicio_prod = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
                hora_str = horario[0]['fin']
                fin_prod = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
                if (fin_prod <= inicio_prod) :
                    fin_prod += timedelta(days=1)
                ahora = datetime.now()
                if(ahora >= inicio_prod and ahora <= fin_prod and tnp == None): tnp = False
                else: tnp = True
                turno_mañana = horario[0]['turno_mañana']
                turno_tarde = horario[0]['turno_tarde']
                turno_noche = horario[0]['turno_noche']
                cambio_turno_1_str = horario[0]['cambio_turno_1']
                cambio_turno_2_str = horario[0]['cambio_turno_2']
                cambio_turno_1 = None if not cambio_turno_1_str else datetime.strptime(f"{fecha_str} {cambio_turno_1_str}", "%Y-%m-%d %H:%M:%S")
                cambio_turno_2 = None if not cambio_turno_2_str else datetime.strptime(f"{fecha_str} {cambio_turno_2_str}", "%Y-%m-%d %H:%M:%S")

                if (turno_mañana and turno_tarde and turno_noche and cambio_turno_1 and cambio_turno_2):
                    print('Tres turnos ...')
                    cambios_de_turno_habilitados = True
                    n_turnos = 3
                elif (turno_mañana and turno_tarde and cambio_turno_1):
                    print('Dos turnos ...')
                    cambios_de_turno_habilitados = True
                    n_turnos = 2
                elif (turno_mañana):
                    print('Un turno ...')
                    cambios_de_turno_habilitados = True
                    n_turnos = 1

            except:
                print('Horario: Sin conexion DB')
                horario = None
                leerhorario = True

        # Tiempo no productivo (tnp) y cambios de turno
        if (horario and (not es_festivo) and v_real != None):  
            ahora = datetime.now()
            if((not tnp) and fin_prod <= ahora):  # Fin de producción
                tnp = True
                cambio_tnp = True
                if (cambios_de_turno_habilitados):
                    turno_activo = None
                    turno = None

            elif(tnp and inicio_prod <= ahora and fin_prod >= ahora):  # Inicio de producción
                tnp = False
                cambio_tnp = True
                if (cambios_de_turno_habilitados):
                    turno = turno_mañana
                    turno_activo = turno

        if (cambios_de_turno_habilitados and not tnp):
            ahora = datetime.now()
            if((ahora >= cambio_turno_1 and n_turnos == 2) or (n_turnos == 3 and ahora < cambio_turno_2 and ahora >= cambio_turno_1)):
                turno = turno_tarde
                hora_cambio_turno = cambio_turno_1
            elif (n_turnos == 3 and ahora >= cambio_turno_2):
                turno = turno_noche
                hora_cambio_turno = cambio_turno_2
            else:
                turno = turno_mañana

        if (arranque):
            turno_activo = turno
            print(f'Turno activo {turno_activo}')

        elif (turno_activo != turno ): # enviar periodo si hay cambio de turno
            print('Cambio de turno ...')
            print(f'Turno activo {turno_activo}')
            turno_activo = turno
            cambio_de_turno = True
            

        # Actualizacion del horario
        if(horario): 
            ahora = datetime.now()
            if (inicio_prod.date() != ahora.date() and fin_prod < ahora): 
                leerhorario = True
                print('volver a leer horario')


        if (len(datos) > 0):
            try:
                r = requests.post(SERVER + 'api/velocidad/registro/', 
                    data = datos[0],
                    headers = HEADERS
                    )
                if(r.status_code == 201):
                    datos.pop(0)
            except:
                print('Registros: Error al escribir DB')

        if (len(periodos) > 0):
            try:
                print(periodos[0])
                r = requests.post(SERVER + 'api/velocidad/nuevo_periodo/',
                                 data=periodos[0],
                                 headers = HEADERS)
                if(r.status_code == 201):
                    periodos.pop(0)
            except:
                print('Periodos: Error al escribir en DB')

        time.sleep(20)    

try:
    lineas = requests.get(SERVER + 'api/velocidad/lineas/',
        headers = HEADERS
    )
    lineas = lineas.json()
    print(lineas)
except:
    print('Lineas: Sin conexion DB')
    lineas = []


threads = []
for i in range(len(lineas)):
    thread = threading.Thread(target=get_speed, 
                args=(lineas[i],), 
                name=lineas[i]['zona']['siglas'])
    threads.append(thread)
    thread.start()
