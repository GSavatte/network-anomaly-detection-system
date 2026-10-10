#!/usr/bin/env bash
# =============================================================================
# simulate_attacks.sh
# Rejoue les 5 scénarios d'attaque de la documentation pour tester Suricata.
#
# Usage :
#   ./simulate_attacks.sh                      # cible par défaut, tous les scénarios
#   ./simulate_attacks.sh 192.168.56.101       # cible explicite, tous les scénarios
#   ./simulate_attacks.sh 192.168.56.101 1 3   # uniquement les scénarios 1 et 3
#
# Variables optionnelles :
#   PAUSE=8 ./simulate_attacks.sh              # pause entre scénarios (secondes)
# =============================================================================
set -u

TARGET="${1:-192.168.56.101}"
[ $# -gt 0 ] && shift
BASE="http://${TARGET}"
PAUSE="${PAUSE:-6}"

if ! command -v curl >/dev/null 2>&1; then
    echo "Erreur : curl n'est pas installé." >&2
    exit 1
fi

# Requête silencieuse qui affiche juste le code HTTP
req() {
    curl -s -o /dev/null -w "  -> HTTP %{http_code}\n" "$@"
}

title() {
    echo
    echo "=== $1 ==="
}

scenario_1() {
    title "Scénario 1 : PHP Exploit Attempt (SID 1000001)"
    req -g "${BASE}/index.php?exploit=1"
}

scenario_2() {
    title "Scénario 2 : Path Traversal (SID 1000002)"
    req -g --path-as-is "${BASE}/index.php?file=../../../../etc/passwd"
}

scenario_3() {
    title "Scénario 3 : Remote Command Execution (SID 1000003)"
    req -g "${BASE}/index.php?cmd=whoami"
}

scenario_4() {
    title "Scénario 4 : DoS HTTP, 50 requêtes consécutives (SID 1000004)"
    for _ in $(seq 1 50); do
        curl -s -o /dev/null "${BASE}/index.php"
    done
    echo "  -> 50 requêtes envoyées"
}

scenario_5() {
    title "Scénario 5 : Brute force POST /login.php, 15 tentatives (SID 1000005)"
    for i in $(seq 1 15); do
        curl -s -o /dev/null -X POST "${BASE}/login.php" \
            --data-urlencode "username=admin" \
            --data-urlencode "password=password${i}"
    done
    echo "  -> 15 requêtes POST envoyées"
}

# Liste des scénarios à exécuter (tous par défaut)
if [ $# -gt 0 ]; then
    SCENARIOS=("$@")
else
    SCENARIOS=(1 2 3 4 5)
fi

echo "Cible : ${BASE}"
echo "Scénarios : ${SCENARIOS[*]}"

first=1
for n in "${SCENARIOS[@]}"; do
    if ! declare -F "scenario_${n}" >/dev/null; then
        echo "Scénario inconnu : ${n} (ignoré)" >&2
        continue
    fi
    if [ "$first" -eq 0 ]; then
        echo "  (pause de ${PAUSE}s)"
        sleep "$PAUSE"
    fi
    first=0
    "scenario_${n}"
done

echo
echo "Terminé."