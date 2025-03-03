### TEST ###
import network
import urequests
import uos
import time
import machine

# URL de base du répertoire contenant les fichiers de mise à jour
GITHUB_BASE_URL = "https://cdn.jsdelivr.net/gh/LaurentS81/Compteur_ECS/contents/Update_files/"
RAW_BASE_URL = "https://cdn.jsdelivr.net/gh/LaurentS81/Compteur_ECS/Update_files/"
VERSION_FILE = "version.txt"

def get_current_version():
    """Lit la version actuelle"""
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except OSError:
        return "0.0"

def get_files_list():
    """Récupère la liste des fichiers dans Update_files/ sur GitHub"""
    try:
        response = urequests.get(GITHUB_BASE_URL)
        if response.status_code == 200:
            files = response.json()
            file_names = [file["name"] for file in files if file["type"] == "file"]
            response.close()
            return file_names
        else:
            print(f"❌ Erreur {response.status_code} lors de la récupération de la liste des fichiers")
            return []
    except Exception as e:
        print(f"⚠️ Erreur lors de la récupération de la liste des fichiers :", e)
        return []

def download_file(filename):
    """Télécharge un fichier depuis GitHub"""
    url = RAW_BASE_URL + filename
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            response.close()
            print(f"✅ {filename} téléchargé avec succès !")
            return True
        else:
            print(f"❌ Erreur {response.status_code} lors du téléchargement de {filename}")
            return False
    except Exception as e:
        print(f"⚠️ Erreur de téléchargement de {filename} :", e)
        return False

def update_if_needed():
    """Vérifie la version et applique la mise à jour si nécessaire"""
    print("🔍 Vérification de la version...")

    try:
        response = urequests.get(RAW_BASE_URL + VERSION_FILE)
        remote_version = response.text.strip()
        response.close()

        local_version = get_current_version()

        if remote_version > local_version:
            print(f"🆕 Nouvelle version disponible ({remote_version} > {local_version})")

            # Télécharger la nouvelle version.txt en premier
            if not download_file(VERSION_FILE):
                print("❌ Échec de la mise à jour : Impossible de mettre à jour version.txt")
                return

            # Récupérer la liste des fichiers à mettre à jour
            files_to_update = get_files_list()

            # Télécharger chaque fichier
            for file in files_to_update:
                if file != VERSION_FILE:  # Ne pas re-télécharger version.txt
                    download_file(file)

            print("🔄 Redémarrage du Pico W...")
            time.sleep(2)
            machine.reset()
        else:
            print("✅ Déjà à jour")

    except Exception as e:
        print("⚠️ Erreur lors de la vérification de version :", e)

# Vérifier et mettre à jour si nécessaire
update_if_needed()

