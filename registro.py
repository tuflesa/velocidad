import requests
from datetime import date, datetime

SERVER = 'http://localhost:8000/'
HEADERS = {'Authorization': 'token 99c11d78d18c18c99247a0a50ede33d8e223767a'}

hoy = date.today()
ahora = datetime.now()
dato = {
        'fecha': hoy.strftime("%Y-%m-%d"),
        'hora': ahora.strftime("%H:%M:%S"),
        'zona': 2,
        'velocidad': 24.23
    }
print(dato)
r = requests.get(SERVER + 'api/velocidad/registro/', 
                        headers = HEADERS
                        )
print(r.json())
r = requests.post(SERVER + 'api/velocidad/registro/', 
                        data = dato,
                        headers = HEADERS
                        )
print(r.status_code)