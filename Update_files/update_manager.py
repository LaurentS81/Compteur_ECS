import network
import urequests
import uos
import time
import machine
import deflate  # MicroPython supporte DEFLATE

# URLs de mise à jour sur GitHub
VERSION_FILE = "version.txt"
ZIP_FILE = "update_package.zip"

GITHUB_VERSION_URL = "https://cdn.jsdelivr.net/gh/LaurentS81/Compteur_ECS/version.txt"
GITHUB_ZIP_URL = "https://cdn.jsdelivr.net/gh/LaurentS81/Compteur_ECS/update_package.zip"

def get_current_version():
    """ Lit la version actuelle du firmware depuis version.txt """
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except OSError:
        return "0.0"  # Retourne 0.0 si aucun fichier version.txt n'est trouvé

def download_file(url, filename):
    """ Télécharge un fichier sans erreur de transfert chunked """
    try:
        response = urequests.get(url, stream=True)  # Activer le mode streaming
        if response.status_code == 200:
            with open(filename, "wb") as f:
                while True:
                    chunk = response.raw.read(512)  # Lire en morceaux de 512 octets
                    if not chunk:
                        break
                    f.write(chunk)
            response.close()
            print(f"✅ {filename} téléchargé avec succès !")
            return True
        else:
            print(f"❌ Erreur {response.status_code} lors du téléchargement de {filename}")
            return False
    except Exception as e:
        print(f"⚠️ Erreur de téléchargement de {filename} :", e)
        return False

def extract_zip_manually(zip_filename):
    """ Décompresse un fichier ZIP sans compression sur MicroPython """
    try:
        with open(zip_filename, "rb") as f:
            zip_data = f.read()

        index = 0
        file_count = 0

        while index < len(zip_data):
            if zip_data[index:index+4] == b'PK\x03\x04':  # Signature d'un fichier ZIP
                print("📂 Détection d'un fichier dans le ZIP...")

                # Lire les informations de l'en-tête du fichier ZIP
                file_size = int.from_bytes(zip_data[index+18:index+22], "little")  # Taille correcte
                file_name_length = int.from_bytes(zip_data[index+26:index+28], "little")
                extra_field_length = int.from_bytes(zip_data[index+28:index+30], "little")

                # Extraire le nom du fichier
                file_name_start = index + 30
                file_name_end = file_name_start + file_name_length
                file_name = zip_data[file_name_start:file_name_end].decode()

                print(f"📂 Fichier détecté : {file_name} ({file_size} octets)")

                # Vérifier et ignorer les fichiers système macOS
                if file_name.startswith("__MACOSX") or file_name.endswith(".DS_Store"):
                    print(f"⚠️ Ignoré : {file_name}")
                    index = file_name_end + extra_field_length
                    continue

                file_data_start = file_name_end + extra_field_length
                file_data_end = file_data_start + file_size
                """
                if file_size == 0:
                    print(f"⚠️ Ignoré (fichier vide) : {file_name}")
                    index = file_data_end
                    continue
                """
                # S'assurer que les indices ne dépassent pas la taille du fichier ZIP
                if file_data_end > len(zip_data):
                    print(f"❌ Erreur : Index hors limites pour {file_name}")
                    return False

                # Écrire le fichier extrait
                print(f"📂 Extraction de {file_name} ({file_size} octets)")
                with open(file_name, "wb") as f:
                    f.write(zip_data[file_data_start:file_data_end])

                file_count += 1
                index = file_data_end  # Passer au prochain fichier
            else:
                index += 1  # Continuer la recherche

        if file_count == 0:
            print("❌ Aucun fichier valide trouvé dans le ZIP !")
            return False

        print(f"✅ {file_count} fichiers extraits avec succès !")
        return True

    except Exception as e:
        print("❌ Erreur lors de l'extraction du ZIP :", e)
        return False


def update_if_needed():
    """ Vérifie la version et applique la mise à jour si nécessaire """
    print("🔍 Vérification de la version...")

    try:
        response = urequests.get(GITHUB_VERSION_URL)
        remote_version = response.text.strip()
        response.close()

        local_version = get_current_version()

        if remote_version > local_version:
            print(f"🆕 Nouvelle version disponible ({remote_version} > {local_version})")
            if download_file(GITHUB_ZIP_URL, ZIP_FILE):
                if extract_zip_manually(ZIP_FILE):
                    with open(VERSION_FILE, "w") as f:
                        f.write(remote_version)

                    print("🔄 Redémarrage du Pico W...")
                    time.sleep(2)
                    machine.reset()
        else:
            print("✅ Déjà à jour")

    except Exception as e:
        print("⚠️ Erreur lors de la vérification de version :", e)

# Vérifier et mettre à jour si nécessaire
update_if_needed()
