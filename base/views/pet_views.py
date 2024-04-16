from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from base.models import Pet, PetImage
from base.serializers import PetSerializer

from rest_framework import status
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

@api_view(['GET'])
def getPets(request):
    query = request.query_params.get('keyword')
    logger.info(f'Consulta recibida: {query}')

    if query == None:
        query = ''

    pets = Pet.objects.filter(name__icontains=query).order_by('_id')

    page = request.query_params.get('page')
    logger.info(f'Página solicitada: {page}')
    
    paginator = Paginator(pets, 8)

    try:
        pets = paginator.page(page)
    except PageNotAnInteger:
        logger.warning("Número de página no válido; mostrando la primera página.")
        pets = paginator.page(1)
    except EmptyPage:
        logger.warning("Número de página fuera de rango; mostrando la última página.")
        pets = paginator.page(paginator.num_pages)

    if page == None:
        page = 1

    page = int(page)

    serializer = PetSerializer(pets, many=True)
    return Response({
        'pets': serializer.data,
        'page': page,
        'pages': paginator.num_pages,
    })
    
@api_view(['GET'])
def getPet(request, pk):
    try:
        pet = Pet.objects.get(_id=pk)
        logger.info(f'Mascota con ID {pk} ha sido accedido.')
        serializer = PetSerializer(pet, many=False)
        return Response(serializer.data)
    except Pet.DoesNotExist:
        logger.warning(f'Intento de acceso a una mascota no existente con ID {pk}.')
        return Response({'detail': 'Mascota no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Ocurrió un error inesperado al acceder a la mascota con ID {pk}: {str(e)}')
        return Response({'detail': 'Ocurrió un error inesperado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)