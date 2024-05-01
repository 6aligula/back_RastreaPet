# Utiliza una imagen oficial de Python como padre
FROM python:3.8
    
# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el contenido del directorio actual en el contenedor en /app
COPY . /app

# Actualizar pip
RUN pip install --upgrade pip

# Instala las dependencias del proyecto
RUN pip install -r requirements.txt

# Establecer la variable de entorno para desactivar el buffering de Python
# dejar ENV PYTHONUNBUFFERED 1 en producción no es inherentemente malo y puede ser beneficioso para ciertos tipos de aplicaciones, 
# especialmente aquellas donde la inmediatez de la salida de logs es importante. 
ENV PYTHONUNBUFFERED 1

# Abre el puerto 8000 para que el contenedor sea accesible desde afuera
EXPOSE 8000

# Instala netcat-openbsd para que funcione el script de wait-for.sh
RUN apt-get update && apt-get install -y netcat-openbsd

# Da permisos de ejecución a los scripts
RUN chmod +x /app/start.sh
RUN chmod +x /app/wait-for.sh

# Define el comando que se ejecutará al iniciar el contenedor
CMD ["/app/start.sh"]

