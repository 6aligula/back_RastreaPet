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

    ssl_certificate /etc/ssl/fullchain.crt;
    ssl_certificate_key /etc/ssl/private.key;
    ssl_trusted_certificate /etc/ssl/fullchain.crt;


    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";

    # Configuración de las rutas como antes
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $http_host;
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
    build:
      context: ./nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
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
## Creacion del Dockerfile para nginx

```yml
# Utiliza la imagen oficial de Nginx como base
FROM nginx:latest

# Copia la configuración de Nginx y el script de inicio
COPY myproject.conf /etc/nginx/conf.d/default.conf
COPY init-ssl.sh /docker-entrypoint.d/init-ssl.sh

# Asegura que el script de inicio sea ejecutable
RUN chmod +x /docker-entrypoint.d/init-ssl.sh

```

## Comportamiento en Reinicios del Contenedor

Cada vez que el contenedor de Nginx se reinicie (ya sea debido a un reinicio manual, un fallo del contenedor, o un reinicio del sistema Docker), Docker ejecutará nuevamente todos los scripts en /docker-entrypoint.d/, lo que incluye tu script init-ssl.sh. Por lo tanto, fullchain.crt se reconstruirá en cada inicio del contenedor.

## Ventajas de Este Enfoque

* Actualización Automática: Cada vez que actualices tus certificados y reinicies el contenedor, los cambios en certificate.crt o ca_bundle.crt se reflejarán automáticamente en fullchain.crt.

* Consistencia: Garantiza que siempre tengas la versión más actualizada de tus certificados en uso, evitando problemas de certificados caducados o desactualizados.

## Consideraciones

* Rendimiento: Aunque la operación de concatenar dos archivos es muy rápida, si tu contenedor se reinicia con mucha frecuencia, podrías considerar optimizar este proceso.

* Seguridad: Asegúrate de que los certificados y claves sean almacenados y manejados de forma segura, especialmente en lo que respecta a los permisos de los archivos y su exposición a través de volúmenes.


### Pagina para comprobar que los SSL son correctos:
```bash
https://www.ssllabs.com/
```
Tambien se puede probar a hacer un curl:

```bash
curl -v https://backstore.online/api/pets/?page=1&missing=true
```
Respuesta ok:

```bash
*   Trying 158.179.213.157:443...
* Connected to backstore.online (158.179.213.157) port 443 (#0)
* ALPN: offers h2,http/1.1
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
*  CAfile: /etc/ssl/certs/ca-certificates.crt
*  CApath: /etc/ssl/certs
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
* TLSv1.3 (IN), TLS handshake, Certificate (11):
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
* TLSv1.3 (IN), TLS handshake, Finished (20):
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
* TLSv1.3 (OUT), TLS handshake, Finished (20):
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
* ALPN: server accepted http/1.1
* Server certificate:
*  subject: CN=backstore.online
*  start date: Apr 19 00:00:00 2024 GMT
*  expire date: Jul 18 23:59:59 2024 GMT
*  subjectAltName: host "backstore.online" matched cert's "backstore.online"
*  issuer: C=AT; O=ZeroSSL; CN=ZeroSSL RSA Domain Secure Site CA
*  SSL certificate verify ok.
* using HTTP/1.1
> GET /api/pets/?page=1 HTTP/1.1
> Host: backstore.online
> User-Agent: curl/7.88.1
> Accept: */*
> 
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* old SSL session ID is stale, removing
< HTTP/1.1 200 OK
< Server: nginx/1.25.5
< Date: Sat, 20 Apr 2024 13:37:24 GMT
< Content-Type: application/json
< Content-Length: 30
< Connection: keep-alive
< Vary: Accept, Origin
< Allow: GET, OPTIONS
< X-Frame-Options: DENY
< X-Content-Type-Options: nosniff
< Referrer-Policy: same-origin
< Cross-Origin-Opener-Policy: same-origin
< 
* Connection #0 to host backstore.online left intact
{"pets":[],"page":1,"pages":1}

```

# Conectarme al contenedor de redis
```bash
docker exec -it backrastreapet_redis_1 redis-cli
```
Test:
```bash
127.0.0.1:6379> set test hello
OK
127.0.0.1:6379> get test
"hello"
127.0.0.1:6379> keys *
1) "test"
```

# Probar en vio de mensajes:
Instalar websocat en debian
```bash
docker pull solsson/websocat
```
### Conectarme a la room test:
```bash
docker run --rm -it solsson/websocat ws://192.168.1.165/ws/chat/test/
```
Recibiendo mensaje desde postman:
```bash
{"message": "Hola, Paco"}
```

### Enviar Mensajes de Forma No Interactiva
Si quieres enviar un solo mensaje y luego cerrar la conexión, puedes hacerlo usando echo y un pipe en Unix/Linux. Este método es útil para scripts o cuando no necesitas una sesión interactiva abierta.

```bash
echo '{"message": "Hola, Paco"}' | docker run --rm -i solsson/websocat ws://192.168.1.165/ws/chat/test/
```
### Enviar y recibir mensajes de forma interactiva
```bash
docker run --rm -it solsson/websocat ws://192.168.1.165/ws/chat/test/
{"message": "Hola, Manolo"}
{"message": "Hola, Manolo"}
{"message": "Hola, Paco"}
```
