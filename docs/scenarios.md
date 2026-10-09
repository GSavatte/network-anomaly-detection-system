# Scénarios

Cette page de la documentation propose une description complète de chaque scénario disponible dans le projet. Nous expliquons également les motivations derrière chaque scénario et comment ils peuvent être utilisés pour protéger le système.

---

## Vue d'ensemble

| SID | Nom du scénario | Type de menace | Sévérité |
| :--- | :--- | :--- | :--- |
| **1000001** | PHP Exploit Attempt | Exploitation applicative | 3 (Basse) |
| **1000002** | Path Traversal Attempt | Traversée de répertoire | 2 (Moyenne) |
| **1000003** | Remote Command Execution (RCE) | Exécution de commandes | 1 (Haute) |
| **1000004** | High Rate HTTP Requests (DoS) | Déni de service | 1 (Haute) |
| **1000005** | HTTP Password Brute Force | Authentification par force brute | 2 (Moyenne) |

---

## Scénario 1 : Exploitation de paramètre PHP

### 1. Description de la menace
Ce scénario simule une tentative d'injection de paramètres dans les requêtes GET web. Les attaquants testent des variables prédéfinies pour identifier de potentielles vulnérabilités/backdoors ou des fonctionnalités cachées dans les scripts PHP.

### 2. Vecteur d'attaque
```bash
curl "[http://192.168.56.101/index.php?exploit=1](http://192.168.56.101/index.php?exploit=1)"
```

### 3. Règle Suricata
```yaml
alert http any any -> any 80 (msg:"WEB-MISC PHP exploit attempt"; flow:to_server,established; http.uri; content:"exploit=1"; classtype:attempted-admin; priority:3; sid:1000001; rev:3;)
```
- `flow:to_server,established` : Analyse uniquement le trafic à destination du serveur sur une connexion TCP établie (évite les faux positifs provenant de paquets non liés à une session HTTP).
- `http.uri` & `content:"exploit=1"` : Inspecte spécifiquement l'URL de la requête HTTP à la recherche de la chaîne exacte.
- `classtype:attempted-admin` & `priority:1` : Catégorise l'attaque comme une tentative d'élévation de privilèges à sévérité critique.

### 4. Extrait d'alerte générée et notification administrateur
<i>Les alertes présentées présentées dans cette documentation ont été tronquées pour ne montrer que les champs pertinents pour ce travail</i>
```json
{
  "timestamp": "2026-10-09T05:27:51.830346+0000",
  "src_ip": "192.168.56.1",
  "dest_ip": "192.168.56.101",
  "alert": {
    "signature_id": 1000001,
    "signature": "WEB-MISC PHP exploit attempt",
    "category": "Attempted Administrator Privilege Gain",
    "severity": 1
  },
  "http": {
    "url": "/index.php?exploit=1"
  }
}
```
- Gravité : **Faible**. Il s'agit d'un bruit de fond ou d'une tentative de test. Aucune action immédiate requise si le serveur ne retourne pas d'erreur 500 ou de contenu sensible. Surveiller si l'IP source réitère des requêtes plus agressives.

## Scénario 2 : Traversée de répertoire

### 1. Description de la menace
L'attaque par traversée de répertoire consiste à manipuler les variables pointant vers des fichiers avec des séquences `../.` L'objectif est de forcer l'application à lire des fichiers système confidentiels (`/etc/passwd`, fichiers de configuration, clés API) situés en dehors de la racine web (`/var/www/html`).

### 2. Vecteur d'attaque
```bash
curl "[http://192.168.56.101/index.php?file=../../../../etc/passwd](http://192.168.56.101/index.php?file=../../../../etc/passwd)"
```

### 3. Règle Suricata
```yaml
alert http any any -> any 80 (msg:"WEB-ATTACK Path Traversal attempt"; flow:to_server,established; http.uri; content:"../"; classtype:web-application-attack; priority:2; sid:1000002; rev:2;)
```
- `content:"../"` : Inspecte spécifiquement l'URL de la requête HTTP à la recherche de la chaîne exacte.
- `classtype:web-application-attack` & `priority:2` : Catégorise l'attaque comme une tentative d'attaque sur une application web à sévérité moyenne.

### 4. Extrait d'alerte générée et notification administrateur
<i>Les alertes présentées présentées dans cette documentation ont été tronquées pour ne montrer que les champs pertinents pour ce travail</i>
```json
{
  "timestamp": "2026-10-09T05:44:12.601650+0000",
  "src_ip": "192.168.56.1",
  "dest_ip": "192.168.56.101",
  "alert": {
    "signature_id": 1000002,
    "signature": "WEB-ATTACK Path Traversal attempt",
    "category": "Web Application Attack",
    "severity": 2
  },
  "http": {
    "url": "/index.php?file=../../../../etc/passwd",
  }
}
```
- Gravité : **Moyenne**. Vérifier dans le log d'accès Apache (`access.log`) la taille de la réponse HTTP envoyée. Si le code HTTP est `200` avec une taille importante, des données système ont pu fuiter. Corriger le code PHP en désactivant l'inclusion directe de fichiers et en assainissant les entrées utilisateur.

## Scénario 3 : Exécution de commandes à distance

### 1. Description de la menace
La RCE est l'une des vulnérabilités les plus critiques. L'attaquant injecte des caractères shell dans les paramètres d'entrée de l'application pour exécuter des commandes système (whoami, id, cat /etc/passwd, ls) au nom de l'utilisateur exécutant le serveur web (potentiellement root).

### 2. Vecteur d'attaque
```bash
curl "[http://192.168.56.101/index.php?cmd=whoami](http://192.168.56.101/index.php?cmd=whoami)"
```

### 3. Règle Suricata
```yaml
alert http any any -> any 80 (msg:"WEB-ATTACK Remote Command Execution attempt"; flow:to_server,established; http.uri; pcre:"/cmd=.*(id|whoami|cat%20\/etc\/passwd|ls)/i"; classtype:web-application-attack; priority:1; sid:1000003; rev:1;)
```
- `pcre:"/cmd=.*(id|whoami|cat%20\/etc\/passwd|ls)/i"` : Utilise une expression régulière pour détecter les paramètres de commande spécifiques.
- `classtype:web-application-attack` & `priority:1` : Catégorise l'attaque comme une tentative d'attaque sur une application web à sévérité élevée.

### 4. Extrait d'alerte générée et notification administrateur
<i>Les alertes présentées présentées dans cette documentation ont été tronquées pour ne montrer que les champs pertinents pour ce travail</i>
```json
{
  "timestamp": "2026-10-09T05:49:00.317998+0000",
  "src_ip": "192.168.56.1",
  "dest_ip": "192.168.56.101",
  "alert": {
    "signature_id": 1000003,
    "signature": "WEB-ATTACK Remote Command Execution attempt",
    "category": "Web Application Attack",
    "severity": 1
  },
  "http": {
    "url": "/index.php?cmd=whoami"
  }
}
```
- Gravité : **Haute**. Alerte prioritaire. Isoler immédiatement l'IP source `192.168.56.1` au niveau du pare-feu. Inspecter le conteneur web à la recherche de processus suspects créés en arrière-plan. Vérifier l'étanchéité du code PHP.

## Scénario 4 : Déni de service par requêtes HTTP à haute fréquence

### 1. Description de la menace
Ce scénario simule un déni de service (DoS) par envoi massif de requêtes HTTP à une application web. L'objectif est de saturer les ressources du serveur et de le rendre indisponible pour les utilisateurs légitimes.

### 2. Vecteur d'attaque
<i>Génération de 50 requêtes HTTP consécutives sans délai :</i>
```ps
1..50 | ForEach-Object { Invoke-WebRequest -Uri "[http://192.168.56.101/index.php](http://192.168.56.101/index.php)" -UseBasicParsing }
```

### 3. Règle Suricata
```yaml
alert http any any -> any 80 (msg:"DOS High Rate HTTP Requests Detected"; flow:to_server,established; detection_filter:track by_src, count 20, seconds 5; classtype:denial-of-service; priority:1; sid:1000005; rev:2;)
```
- `detection_filter:track by_src, count 20, seconds 5` : Détecte les sources envoyant plus de 20 requêtes HTTP en 5 secondes.
- `classtype:denial-of-service` & `priority:1` : Catégorise l'attaque comme un déni de service à sévérité élevée.

### 4. Extrait d'alerte générée et notification administrateur
<i>Les alertes présentées présentées dans cette documentation ont été tronquées pour ne montrer que les champs pertinents pour ce travail</i>
```json
{
  "timestamp": "2026-10-09T05:53:08.205482+0000",
  "src_ip": "192.168.56.1",
  "dest_ip": "192.168.56.101",
  "alert": {
    "signature_id": 1000004,
    "signature": "DOS High Rate HTTP Requests Detected",
    "category": "Detection of a Denial of Service Attack",
    "severity": 1
  }
}
```
- Gravité : **Haute**. Attaque volumétrique entraînant un risque d'indisponibilité. Appliquer un blocage dynamique automatique au niveau pare-feu (ex. fail2ban ou module mod_ratelimit d'Apache) pour l'IP source détectée.

## Scénario 5 : Brute-force d'authentification HTTP POST

### 1. Description de la menace
Ce scénario simule une attaque par force brute sur un formulaire d'authentification web. L'attaquant tente de deviner le mot de passe en envoyant un grand nombre de requêtes POST avec différentes combinaisons de mots de passe.

### 2. Vecteur d'attaque
<i>Génération de 50 requêtes HTTP consécutives sans délai :</i>
```ps
1..15 | ForEach-Object { Invoke-WebRequest -Uri "http://192.168.56.101/login.php" -Method POST -Body @{username="admin"; password="password$_"} -UseBasicParsing }
```

### 3. Règle Suricata
```yaml
alert http any any -> any 80 (msg:"WEB-ATTACK HTTP Password Brute Force Attempt"; flow:to_server,established; http.method; content:"POST"; http.uri; content:"/login.php"; detection_filter:track by_src, count 10, seconds 5; classtype:web-application-attack; priority:2; sid:1000005; rev:1;)
```
- `classtype:web-application-attack` & `priority:2` : Catégorise l'attaque comme une attaque sur une application web à sévérité moyenne.

### 4. Extrait d'alerte générée et notification administrateur
<i>Les alertes présentées présentées dans cette documentation ont été tronquées pour ne montrer que les champs pertinents pour ce travail</i>
```json
{
  "timestamp": "2026-10-09T06:31:03.125367+0000",
  "src_ip": "192.168.56.1",
  "dest_ip": "192.168.56.101",
  "alert": {
    "signature_id": 1000005,
    "signature": "WEB-ATTACK HTTP Password Brute Force Attempt",
    "category": "Web Application Attack",
    "severity": 2
  },
  "http": {
    "url": "/login.php"
  }
}
```
- Gravité : **Moyenne**. Attaque d'authentification par force brute. Mettre en place un verrouillage temporaire des comptes après plusieurs échecs consécutifs, implémenter un captcha ou utiliser un outil de bannissement d'IP comme Fail2ban couplé aux logs d'accès du serveur web.