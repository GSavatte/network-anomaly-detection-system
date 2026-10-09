<?php
// index.php
if (isset($_GET['exploit'])) {
    echo "Exploit parameter: " . htmlspecialchars($_GET['exploit']);
} elseif (isset($_GET['cmd'])) {
    echo "Command simulation: " . htmlspecialchars($_GET['cmd']);
} elseif (isset($_GET['file'])) {
    echo "File parameter: " . htmlspecialchars($_GET['file']);
} else {
    echo "Serveur Web interne en ligne.";
}
?>