from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from base.models import Product
from base.serializers import ProductSerializer

from rest_framework import status
import logging

logger = logging.getLogger('base')

@api_view(['GET'])
def getProducts(request):
    query = request.query_params.get('keyword')
    logger.info(f'Consulta recibida: {query}')

    if query == None:
        query = ''

    products = Product.objects.filter(name__icontains=query).order_by('_id')

    page = request.query_params.get('page')
    logger.info(f'Página solicitada: {page}')
    
    paginator = Paginator(products, 8)

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        logger.warning("Número de página no válido; mostrando la primera página.")
        products = paginator.page(1)
    except EmptyPage:
        logger.warning("Número de página fuera de rango; mostrando la última página.")
        products = paginator.page(paginator.num_pages)

    if page == None:
        page = 1

    page = int(page)

    serializer = ProductSerializer(products, many=True)
    return Response({
        'products': serializer.data,
        'page': page,
        'pages': paginator.num_pages,
    })

@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = Product.objects.get(_id=pk)
        logger.info(f'Producto con ID {pk} ha sido accedido.')
        serializer = ProductSerializer(product, many=False)
        return Response(serializer.data)
    except Product.DoesNotExist:
        logger.warning(f'Intento de acceso a un producto no existente con ID {pk}.')
        return Response({'detail': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f'Ocurrió un error inesperado al acceder al producto con ID {pk}: {str(e)}')
        return Response({'detail': 'Ocurrió un error inesperado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)