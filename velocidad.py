import snap7
from snap7.util import get_real
import threading
import requests
import time
from datetime import date, datetime

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

                if (inc_velocidad > 1.5 or inc_hf_power > 5 or inc_hf_freq > 5 or inc_welding_press > 5 or arranque):
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
                    print(f'ahora: {ahora}')
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
                            'fecha': hoy.strftime("%Y-%m-%d") + ' ' + ahora.strftime("%H:%M:%S") ,
                            'velocidad': v_registro,
                        }
                        
                    if (v_registro != v_registro_anterior or
                        hf_pot_registro != hf_pot_registro_anterior or
                        hf_freq_registro != hf_freq_registro_anterior or
                        welding_press_registro != welding_press_registro_anterior or
                        arranque):

                        arranque = False    
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
                            }
                    datos.append(dato)
                    periodos.append(periodo)
        
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
    print('Sin conexion DB')
    lineas = []


threads = []
for i in range(len(lineas)):
    thread = threading.Thread(target=get_speed, 
                args=(lineas[i],), 
                name=lineas[i]['zona']['siglas'])
    threads.append(thread)
    thread.start()

# def get_dword(_bytearray, byte_index):
#    data = _bytearray[byte_index:byte_index + 4]
#    dword = struct.unpack('>I', struct.pack('4B', *data))[0]
#    return dword

# raw_data = plc.db_read(60,0,144)
# bd1_sup = get_dword(raw_data, 0) / 100
# print(f'BD1_SUP Pos: {bd1_sup}')
