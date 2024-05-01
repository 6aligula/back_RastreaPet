from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from base.models import Pet, PetImage
from base.serializers import PetSerializer

from rest_framework import status
from django.core.cache import cache
import logging

logger = logging.getLogger('base')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPet(request):
    user = request.user
    logger.info(f"Usuario autenticado: {user.email}")
    logger.info(f"Datos recibidos: {request.data}")

    # Extraer los datos que no son de archivo de request.data
    pet_data = {key: value for key, value in request.data.items() if key != 'images'}

    # Establecer el campo missing en True
    pet_data['missing'] = True  # Aquí establecemos el campo missing como True

    # Crear el serializador sin los datos de las imágenes
    pet_serializer = PetSerializer(data=pet_data)
    if pet_serializer.is_valid():
        pet = pet_serializer.save()  # Guardamos la mascota para poder asociar las imágenes

        # Procesar las imágenes separadamente
        images_data = request.FILES.getlist('images')  # Obtener la lista de archivos de imagen
        for image_file in images_data:
            PetImage.objects.create(pet=pet, image=image_file)

        logger.info('Una nueva mascota ha sido registrada con éxito.')
        return Response(pet_serializer.data, status=status.HTTP_201_CREATED)
    else:
        logger.warning('Intento fallido de registro de nueva mascota debido a datos inválidos.')
        return Response(pet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def createPetFound(request):
    #user = request.user
    #logger.info(f"Usuario autenticado: {user.email}")
    logger.info(f"Datos recibidos: {request.data}")

    # Extraer los datos que no son de archivo de request.data
    pet_data = {key: value for key, value in request.data.items() if key != 'images'}
    
    # Establecer el campo 
    pet_data['name'] = "Sin Identificar"  # Aquí establecemos el campo missing como True
    
    # Crear el serializador sin los datos de las imágenes
    pet_serializer = PetSerializer(data=pet_data)
    if pet_serializer.is_valid():
        pet = pet_serializer.save()  # Guardamos la mascota para poder asociar las imágenes

        # Procesar las imágenes separadamente
        images_data = request.FILES.getlist('images')  # Obtener la lista de archivos de imagen
        if images_data:
            for image_file in images_data:
                PetImage.objects.create(pet=pet, image=image_file)
        else:
            # Si no hay imágenes enviadas, usar la imagen por defecto
            PetImage.objects.create(pet=pet, image='pet_images/default.png')

        logger.info('Una nueva mascota ha sido registrada con éxito.')
        return Response(pet_serializer.data, status=status.HTTP_201_CREATED)
    else:
        logger.warning('Intento fallido de registro de nueva mascota debido a datos inválidos.')
        return Response(pet_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getPets(request):
    query = request.query_params.get('keyword', '')
    missing = request.query_params.get('missing')
    page = request.query_params.get('page', 1)

    cache_key = f'pets-{query}-{missing}-{page}'
    cached_pets = cache.get(cache_key)

    if cached_pets is not None:
        logger.info('Devolviendo datos desde la caché.')
        return Response(cached_pets)

    logger.info(f'Consulta recibida: {query}')
    pets = Pet.objects.filter(name__icontains=query).order_by('_id')

    if missing is not None:
        pets = pets.filter(missing=missing.lower() in ['true', '1', 'yes'])

    paginator = Paginator(pets, 8)
    try:
        pets = paginator.page(page)
    except PageNotAnInteger:
        pets = paginator.page(1)
    except EmptyPage:
        pets = paginator.page(paginator.num_pages)

    serializer = PetSerializer(pets, many=True)
    result = {
        'pets': serializer.data,
        'page': int(page),
        'pages': paginator.num_pages,
    }

    # Cachear el resultado antes de devolverlo
    cache.set(cache_key, result, timeout=300)  # Tiempo en segundos, ajusta según tus necesidades
    return Response(result)
  
@api_view(['GET'])
def getPet(request, pk):
    cache_key = f'pet-{pk}'
    cached_pet = cache.get(cache_key)

    if cached_pet is not None:
        logger.info(f'Devolviendo mascota desde la caché para ID {pk}.')
        return Response(cached_pet)

    try:
        pet = Pet.objects.get(_id=pk)
        serializer = PetSerializer(pet, many=False)
        logger.info(f'Mascota con ID {pk} ha sido accedido.')
        cache.set(cache_key, serializer.data, timeout=300)  # Ajusta el timeout según tus necesidades
        return Response(serializer.data)
    except Pet.DoesNotExist:
        logger.warning(f'Intento de acceso a una mascota no existente con ID {pk}.')
        return Response({'detail': 'Mascota no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Ocurrió un error inesperado al acceder a la mascota con ID {pk}: {str(e)}')
        return Response({'detail': 'Ocurrió un error inesperado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

# from PIL import Image
# from PIL.ExifTags import TAGS, GPSTAGS

# def get_image_exif_data(image_path):
#     image = Image.open(image_path)
#     exif_data = {
#         TAGS[k]: v
#         for k, v in image._getexif().items()
#         if k in TAGS
#     }
    
#     gps_info = {}
#     for key in exif_data['GPSInfo'].keys():
#         decode = GPSTAGS.get(key, key)
#         gps_info[decode] = exif_data['GPSInfo'][key]

#     return gps_info
