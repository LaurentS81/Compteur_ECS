### TEST ###
import network
import urequests
import uos
import time
import machine

# URL de base du répertoire contenant les fichiers de mise à jour
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/LaurentS81/Compteur_ECS/main/Update_files/version.txt"
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

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/LaurentS81/Compteur_ECS/main/Update_files/version.txt"

def update_if_needed():
    """Vérifie la version et applique la mise à jour si nécessaire"""
    print("🔍 Vérification de la version...")

    try:
        response = urequests.get(GITHUB_VERSION_URL)
        remote_version = response.text.strip()
        response.close()

        local_version = get_current_version()

        if remote_version > local_version:
            print(f"🆕 Nouvelle version disponible ({remote_version} > {local_version})")

            # Récupérer la liste des fichiers à mettre à jour
            files_to_update = get_files_list()
            update_success = True  # On part du principe que la mise à jour va bien se passer

            # Télécharger chaque fichier (sauf version.txt)
            for file in files_to_update:
                if file != VERSION_FILE:  
                    if not download_file(file):
                        update_success = False  # Échec d'un fichier

            # **Si tous les fichiers ont été mis à jour avec succès, on met à jour version.txt**
            if update_success:
                print("✅ Tous les fichiers ont été mis à jour correctement.")
                if download_file(VERSION_FILE):
                    print("✅ version.txt mis à jour avec succès.")
                else:
                    print("❌ Échec de la mise à jour de version.txt !")
            else:
                print("❌ Une ou plusieurs mises à jour ont échoué. version.txt n'a PAS été mis à jour.")

            print("🔄 Redémarrage du Pico W...")
            time.sleep(2)
            machine.reset()
        else:
            print(f"Version GitHub : {remote_version} - Version Raspberry : {local_version}")
            print("✅ Déjà à jour")

    except Exception as e:
        print("⚠️ Erreur lors de la vérification de version :", e)

# Vérifier et mettre à jour si nécessaire
update_if_needed()


