import json
import os
import time
import urllib.request
from datetime import datetime, timezone

#
import urllib.error
#

ES_URL = os.getenv("ES_URL", "http://es01:9200").rstrip("/")
ES_USER = os.environ["ES_USER"]
ES_PASSWORD = os.environ["ES_PASSWORD"]
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
INDEX = os.getenv("ALERT_INDEX", "kibana-alerts")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
STATE_FILE = "/state/last_seen.json"

def es_search(body):
    credentials = f"{ES_USER}:{ES_PASSWORD}".encode()
    import base64
    auth = base64.b64encode(credentials).decode()
    request = urllib.request.Request(
        f"{ES_URL}/{INDEX}/_search",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
	    "User-Agent": "siem-discord-relay/1.0",
	    "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def send_to_discord(doc):
    text = (
        f"🚨 **Alerte Kibana**\n"
        f"**Règle :** {doc.get('rule_name', 'inconnue')}\n"
        f"**Message :** {doc.get('message', 'Aucun détail')}\n"
        f"**Date :** {doc.get('@timestamp', 'inconnue')}"
    )
    payload = json.dumps({"content": text[:1900]}).encode()
    request = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=payload,
        headers={
	    "Content-Type":"application/json",
	    "User-Agent": "siem-discord-relay/1.0",
	},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        response.read()

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        # Au premier lancement, ne pas envoyer toutes les anciennes alertes.
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "id": "0",
        }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()
print(f"Relais démarré; reprise à partir de {state['timestamp']}")

while True:
    try:
        ts, doc_id = state["timestamp"], state["id"]
        result = es_search({
            "size": 100,
            "query": {
                "bool": {
                    "should": [
                        {"range": {"@timestamp": {"gt": ts}}},
                        {"bool": {
                            "filter": [{"term": {"@timestamp": ts}}],
                            "must_not": [{"ids": {"values": [doc_id]}}],
                        }},
                    ],
                    "minimum_should_match": 1,
                }
            },
            "sort": [{"@timestamp": "asc"}, {"alert_id": "asc"}],
        })

        for hit in result["hits"]["hits"]:
            send_to_discord(hit["_source"])
            state = {
                "timestamp": hit["_source"].get("@timestamp", ts),
                "id": hit["_id"],
            }
            save_state(state)

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if "discord.com" in str(exc.url):
            endpoint = "Discord webhook"
        else:
            endpoint = "Elasticsearch"
        print(f"Erreur HTTP {exc.code} sur {endpoint}: {body}", flush=True)
    except Exception as exc:
        print(f"Erreur pendant la vérification : {type(exc).__name__}: {exc}", flush=True)

#    except Exception as exc:
#        print(f"Erreur pendant la vérification : {exc}", flush=True)

    time.sleep(POLL_SECONDS)
