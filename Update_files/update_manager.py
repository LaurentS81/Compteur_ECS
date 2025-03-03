import network
import socket
import time
import json

CREDENTIALS_FILE = 'WIFI_credentials.json'

class WiFiManager:
    def __init__(self):
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)

    def read_credentials(self):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except OSError:
            return None

    def write_credentials(self, ssid, password):
        credentials = {
            'ssid': ssid,
            'password': password
        }
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f)

    def connect(self, ssid, password):
        print(f"Tentative de connexion à {ssid}")
        self.sta_if.active(True)
        self.sta_if.connect(ssid, password)

        for _ in range(10):
            if self.sta_if.isconnected():
                print("Connexion réussie!")
                print("Adresse IP:", self.sta_if.ifconfig()[0])
                return True
            time.sleep(1)

        print("Échec de la connexion.")
        return False

    def start_access_point(self):
        self.ap_if.active(True)
        self.ap_if.config(essid='Pico_AP', password='12345678')
        print("Mode AP activé. Connectez-vous au réseau 'Pico_AP' avec le mot de passe '12345678'")
        print("Accédez à l'interface via http://192.168.4.1")

    def start_web_server(self):
        # Vérifier les identifiants enregistrés
        creds = self.read_credentials()
        connected = False

        if creds:
            connected = self.connect(creds['ssid'], creds['password'])

        if not connected:
            self.start_access_point()
            ip = '192.168.4.1'  # Adresse IP par défaut en mode AP
        else:
            ip = self.sta_if.ifconfig()[0]

        print(f"Serveur Web démarré sur http://{ip}")

        # Démarrer le serveur Web
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.bind(addr)
        s.listen(1)

        while True:
            try:
                cl, addr = s.accept()
                print('Client connecté depuis', addr)

                request = cl.recv(1024).decode()
                print("Requête reçue:", request)

                if 'GET / ' in request:
                    response = self.load_html('index.html')
                elif 'POST /connect' in request:
                    ssid, password = self.parse_post_data(request, cl)
                    print("SSID reçu:", ssid)
                    print("Mot de passe reçu:", password)
                    if ssid and password:
                        self.write_credentials(ssid, password)
                        if self.connect(ssid, password):
                            for _ in range(20):
                                cl.send(self.html_response("SUCCESS", code=200))
                                time.sleep(1)
                        else:
                            cl.send(self.html_response("FAIL", code=400))

                    else:
                        response = self.html_response("SSID ou mot de passe manquant.")
                else:
                    response = self.html_response("Page non trouvée.", code=404)

                cl.send(response)
                cl.close()
                
            except Exception as e:
                print("Erreur détectée:", e)

    def load_html(self, filename):
        try:
            with open(filename, 'r') as f:
                return self.html_response(f.read())
        except OSError:
            return self.html_response("Fichier non trouvé.", code=404)

    def parse_post_data(self, request, client):
        try:
            headers, body = request.split('\r\n\r\n', 1)
            print("En-têtes de la requête:", headers)
            print("Corps brut initial:", body)

            # Extraire le Content-Length
            content_length = 0
            for line in headers.split('\r\n'):
                if 'Content-Length' in line:
                    content_length = int(line.split(':')[1].strip())

            # Lire les données manquantes si nécessaire
            if len(body) < content_length:
                remaining = content_length - len(body)
                body += client.recv(remaining).decode()

            print("Corps brut final:", body)

            # Décodage du corps en dictionnaire
            params = {}
            for pair in body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = key.replace('+', ' ').replace('%20', ' ')
                    value = value.replace('+', ' ').replace('%20', ' ')
                    params[key] = value

            print("Données POST décodées:", params)
            return params.get('ssid'), params.get('password')

        except Exception as e:
            print("Erreur lors de l'analyse des données POST:", e)
            return None, None

    def html_response(self, content, code=200, content_type='text/html'):
        status_message = "OK" if code == 200 else "Bad Request"
        return ('HTTP/1.1 {} {}\r\nContent-Type: {}\r\n\r\n{}'.format(code, status_message, content_type, content)).encode()


# Point d'entrée
wifi_manager = WiFiManager()
wifi_manager.start_web_server()
