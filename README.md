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
