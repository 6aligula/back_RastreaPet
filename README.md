# Backend Django

Este es el backend de Django de la aplicación, contenerizado para asegurar un entorno de ejecución consistente.

## Dockerización

El backend de Django está configurado para ejecutarse en un contenedor Docker, lo que simplifica el despliegue y la gestión de dependencias.

### Dockerfile

El `Dockerfile` utiliza la imagen de Python 3.8 y prepara el entorno de Django.

```dockerfile
FROM python:3.8
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
EXPOSE 8000
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]

```


### Docker Compose
El archivo `docker-compose.yml` establece el servicio, los volúmenes, los puertos y la red.

```dockerfile
version: '3.9'

services:
  web:
    build: .
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    networks:
      - app-network
  db:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    networks:
      - app-network

networks:
  app-network:
    name: app-network
    driver: bridge

volumes:
  postgres-data:

```
# Comando de Arranque
```bash
chmod + x start.sh wait-for.sh
docker-compose up --build
```

La red app-network conecta el backend con otros servicios, como el frontend. Asegúrese de que la red esté definida como se describe en el archivo docker-compose.yml.


--------------------------------------------------------------
Configuracion de SSl para certbot y let's encrypt

```
server {
    listen 80;
    server_name backstore.online www.backstore.online;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Configuración para servir la aplicación Django a través de HTTP
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
}
```

Una vez creados los cetificados y apuedo detener los contendores y modificar la config de nginx para el ssl

```
server {
    listen 80;
    server_name backstore.online www.backstore.online;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name backstore.online www.backstore.online;

    ssl_certificate /etc/letsencrypt/live/backstore.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/backstore.online/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
    
    location /static/ {
        alias /app/staticfiles/;
    }
    location /media/ {
        alias /app/media/;
    }

    # Otras configuraciones SSL para mejorar la seguridad
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
}
```
Vuelvo a lanzar los contenedores con la nueva configuración

```bash
docker-compose up 
```
El docker-compose preparado para certbot y let's encrypt

```yml
version: '3.9'

services:
  web:
    build: .
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env
    depends_on:
      - db
    networks:
      - app-network
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx:/etc/nginx/conf.d
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot      
    depends_on:
      - web
    networks:
      - app-network
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    depends_on:
      - nginx
    command: certonly --webroot -w /var/www/certbot --email beratmosc@tuta.io -d backstore.online --agree-tos --staging
  db:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    networks:
      - app-network

networks:
  app-network:
    name: app-network
    driver: bridge

volumes:
  postgres-data:
  static_volume:
  media_volume:
  certbot-conf:
  certbot-www:
```

Una ves funcione esto en modo staging osea test ya podemos proceder al modo producción:

```bash
    command: certonly --webroot -w /var/www/certbot --email beratmosc@tuta.io -d backstore.online --agree-tos --staging
```
Deberia quedar asi:
```bash
    command: certonly --webroot -w /var/www/certbot --email beratmosc@tuta.io -d backstore.online --agree-tos
```
------------------------------------------------------------------------------------------------------------

# Configuración para zero ssl:

Despues de crear los certificados en la pagina de Zero ssl:

---------------------------------------------------------------------------
Configuracio de nginx con zero ssl
---------------------------------------------------------------------------
```bash
server {
    listen 443 ssl;
    server_name backstore.online www.backstore.online;

    ssl_certificate /etc/ssl/certificate.crt;
    ssl_certificate_key /etc/ssl/private.key;

    # Concatena el certificado y la cadena de certificados
    ssl_trusted_certificate /etc/ssl/ca_bundle.crt;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

    # Configuración de las rutas como antes
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 10M;
    
    location /static/ {
        alias /app/staticfiles/;
    }
    location /media/ {
        alias /app/media/;
    }

    # Otras configuraciones SSL para mejorar la seguridad
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
}
```

docker-compose.yml
--------------------------------------------
```yml
version: '3.9'

services:
  web:
    build: .
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env
    depends_on:
      - db
    networks:
      - app-network
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx:/etc/nginx/conf.d
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - /etc/ssl/certs/certificate.crt:/etc/ssl/certificate.crt:ro
      - /etc/ssl/certs/ca_bundle.crt:/etc/ssl/ca_bundle.crt:ro
      - /etc/ssl/private/private.key:/etc/ssl/private.key:ro
    
    depends_on:
      - web
    networks:
      - app-network
  
  db:
    image: postgres:16
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    networks:
      - app-network

networks:
  app-network:
    name: app-network
    driver: bridge

volumes:
  postgres-data:
  static_volume:
  media_volume:
```