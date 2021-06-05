import snap7
import struct
import threading

# Prep. Banda mtt3
IP = '10.128.1.144'
RACK = 0
SLOT = 6

# QS mtt2
# IP = '10.128.1.140'
# RACK = 0
# SLOT = 1

plc = snap7.client.Client()
plc.connect(IP, RACK, SLOT)

state = plc.get_cpu_state()
print(f'State: {state}')

# Lectura periodica de la velocidad desde Prep. Banda mtt3
def get_speed():
    v_raw = plc.db_read(15,2,4)
    v_real = struct.unpack('>f', struct.pack('4B', *v_raw))[0]
    print(f'Velocidad mtt3: {v_real}')
    threading.Timer(1,get_speed).start()

get_speed()

# def get_dword(_bytearray, byte_index):
#     data = _bytearray[byte_index:byte_index + 4]
#     dword = struct.unpack('>I', struct.pack('4B', *data))[0]
#     return dword

# raw_data = plc.db_read(60,0,144)
# bd1_sup = get_dword(raw_data, 0) / 100
# print(f'BD1_SUP Pos: {bd1_sup}')