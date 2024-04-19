#!/bin/bash
# start.sh

# Solo calcula HOST_IP si DJANGO_ALLOWED_HOSTS no está ya definido
if [ -z "$DJANGO_ALLOWED_HOSTS" ]; then
  # Obtiene la dirección IP del host de alguna manera
  HOST_IP=$(hostname -I | awk '{print $1}')

  # Si no se pudo obtener la IP, usa 'localhost'
  if [ -z "$HOST_IP" ]; then
    HOST_IP="localhost"
  fi

  # Exporta la dirección IP a una variable de entorno para Django
  export DJANGO_ALLOWED_HOSTS=$HOST_IP,localhost
else
  # Utiliza DJANGO_ALLOWED_HOSTS como está, asumiendo que start_project.sh lo ha configurado
  export DJANGO_ALLOWED_HOSTS
fi
# Primero, utiliza wait-for.sh para esperar a que MySQL esté listo
/app/wait-for.sh db:5432 -- true

# Ejecuta las migraciones de Django
python manage.py makemigrations
python manage.py migrate

# Crea el superusuario de Django
python manage.py shell < create_superuser.py

# Inicia el servidor con Gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000