<?php
// index.php
if (isset($_GET['exploit'])) {
    echo "Exploit parameter received: " . htmlspecialchars($_GET['exploit']);
} else {
    echo "Serveur Web interne en ligne.";
}
?>