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
    """ Vérifie la version et applique la mise à jour si nécessaire """
    print("🔍 Vérification de la version...")

    try:
        response = urequests.get(GITHUB_VERSION_URL, headers=HEADERS)
        remote_version = response.text.strip()
        response.close()

        local_version = get_current_version()

        if remote_version > local_version:
            print(f"🆕 Nouvelle version disponible ({remote_version} > {local_version})")

            # Récupération de la liste des fichiers
            file_list = get_file_list_from_github()
            if not file_list:
                print("❌ Échec de récupération de la liste des fichiers.")
                return
            
            update_success = True  # On part du principe que la mise à jour va bien se passer

            # **Étape 1 : Télécharger tous les fichiers SAUF `version.txt`**
            for file_name, file_url in file_list.items():
                if file_name == "version.txt":
                    continue  # On le traite à la fin
                if not download_file(file_url, file_name):
                    update_success = False  # Échec d'un fichier

            # **Étape 2 : Si toutes les mises à jour sont réussies, on met à jour `version.txt`**
            if update_success:
                print("✅ Tous les fichiers ont été mis à jour correctement.")
                if "version.txt" in file_list:
                    if download_file(file_list["version.txt"], "version.txt"):
                        print("✅ version.txt mis à jour avec succès.")
                    else:
                        print("❌ Échec de la mise à jour de version.txt !")
            else:
                print("❌ Une ou plusieurs mises à jour ont échoué. version.txt n'a PAS été modifié.")

            print("🔄 Redémarrage du Pico W...")
            time.sleep(2)
            machine.reset()

        else:
            print("✅ Déjà à jour")

    except Exception as e:
        print(f"⚠️ Erreur réseau lors de la vérification de version : {e}")


# Vérifier et mettre à jour si nécessaire
update_if_needed()

