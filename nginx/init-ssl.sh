#!/bin/sh

# Concatena el certificado y los certificados intermedios en un solo archivo
cat /etc/ssl/certificate.crt /etc/ssl/ca_bundle.crt > /etc/ssl/fullchain.crt

# Asegura que Nginx pueda leer el archivo resultante
chmod 644 /etc/ssl/fullchain.crt
