<?php
// login.php
header('Content-Type: application/json');
echo json_encode(['status' => 'error', 'message' => 'Invalid credentials']);
?>