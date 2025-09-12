import snap7
import struct
import threading
import requests
import time
from datetime import date, datetime

# Listado de máquinas con control de velocidad
# SERVER = 'http://10.128.100.242:8000/'
SERVER = 'http://localhost:8000/'
# HEADERS = {'Authorization': 'token 99c11d78d18c18c99247a0a50ede33d8e223767a'}
HEADERS = {'Authorization': 'token 7e3f7c728e4b6c68de306db3da6e321f43222201'}

def get_speed(linea):
    # plc_conectado = False
    arranque = True
    v_actual = 0
    v_registro = None
    v_registro_anterior = None
    datos = []

    IP = linea['ip'] 
    RACK = linea['rack'] 
    SLOT = linea['slot']
    DB = linea['db']
    DW = linea['dw'] 
    siglas = linea['zona']['siglas']
    zona = linea['zona']['id']

    plc = snap7.client.Client()

    while (True):
        if plc.get_connected() == False:
            try:
                plc.connect(IP, RACK, SLOT)
                state = plc.get_cpu_state()
                print(f'Máquina {siglas} State: {state}')
                # plc_conectado = True
            except:
                # plc_conectado = False
                arranque = True
                print(f'Máquina {siglas} Error de conexión')

        else:
            try:
                v_raw = plc.db_read(DB, DW, 4)
                v_real = struct.unpack('>f', struct.pack('4B', *v_raw))[0]
                inc_velocidad = abs(v_actual - v_real)

                if (inc_velocidad > 1.5 or arranque):
                    v_actual = v_real
                    if (v_real > 9.5):
                        v_registro = v_real
                    else:
                        v_registro = 0.0
                    hoy = date.today()
                    ahora = datetime.now()
                    dato = {
                            'fecha': hoy.strftime("%Y-%m-%d"),
                            'hora': ahora.strftime("%H:%M:%S"),
                            'zona': zona,
                            'velocidad': v_registro
                        }
                    if (v_registro != v_registro_anterior or arranque):
                        arranque = False    
                        datos.append(dato)
                        v_registro_anterior = v_registro
            except:
                plc.disconnect()
                # plc_conectado = False
                hoy = date.today()
                ahora = datetime.now()
                dato = {
                        'fecha': hoy.strftime("%Y-%m-%d"),
                        'hora': ahora.strftime("%H:%M:%S"),
                        'zona': zona,
                        'velocidad': -1
                    }
                datos.append(dato)
                print(f'Añadir dato: {dato}')
        
        if (len(datos) > 0):
            try:
                r = requests.post(SERVER + 'api/velocidad/registro/', 
                    data = datos[0],
                    headers = HEADERS
                    )
                if(r.status_code == 201):
                    datos.pop(0)
                    print(f'DB actualizada {siglas}')
            except:
                print('Error al escribir DB')
            print(f'Datos pendientes de enviar: {len(datos)}')

        time.sleep(20)    
    # threading.Timer(1,get_speed, [automata, maquina, on]).start()

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
