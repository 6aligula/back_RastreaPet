# Utiliza la imagen oficial de Nginx como base
FROM nginx:latest

# Copia la configuración de Nginx y el script de inicio
COPY myproject.conf /etc/nginx/conf.d/default.conf
COPY init-ssl.sh /docker-entrypoint.d/init-ssl.sh

# Asegura que el script de inicio sea ejecutable
RUN chmod +x /docker-entrypoint.d/init-ssl.sh

