from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base.models import Product, Order, OrderItem, ShippingAddress
from base.serializers import OrderSerializer

from rest_framework import status
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('base')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data
    orderItems = data['orderItems']

    if orderItems and len(orderItems) == 0:
        logger.warning(f'Usuario {user} intentó crear una orden sin artículos.')
        return Response({'detail': 'No hay articulos añadidos a la cesta'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        try:
            order = Order.objects.create(
                user=user,
                paymentMethod='',
                taxPrice=0,
                shippingPrice=0,
                totalPrice=data['totalPrice']
            )
            logger.info(f'Orden creada: {order._id} por el usuario {user}')

            shipping = ShippingAddress.objects.create(
                order=order,
                address=data['shippingAddress']['address'],
                city=data['shippingAddress']['city'],
                postalCode=data['shippingAddress']['postalCode'],
                province=data['shippingAddress']['province'],
                recipientName=data['shippingAddress']['recipientName'],
                comment=data['shippingAddress']['comment'],
                email=data['shippingAddress']['email'],
                mobil=data['shippingAddress']['mobil'],
            )
            logger.info(f'Dirección de envío creada para la orden {order._id}')

            for i in orderItems:
                product = Product.objects.get(_id=i['product'])
                item = OrderItem.objects.create(
                    product=product,
                    order=order,
                    name=product.name,
                    qty=i['qty'],
                    price=i['price'],
                    image=product.image.url,
                )
                logger.info(f'Elemento de orden añadido: {item.name} (ID: {item._id}) a la orden {order._id}')

                product.countInStock -= item.qty
                product.save()
                logger.info(f'Stock actualizado para el producto {product.name}')

            serializer = OrderSerializer(order, many=False)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f'Ocurrió un error al crear la orden: {str(e)}')
            return Response({"detail": "Ocurrió un error al procesar la orden"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getMyOrders(request):
    user = request.user
    try:
        orders = user.order_set.all()
        if not orders.exists():
            logger.info(f'El usuario {user} no tiene órdenes.')
            return Response({"detail": "No hay órdenes disponibles para este usuario"}, status=status.HTTP_204_NO_CONTENT)

        logger.info(f'Obteniendo todas las órdenes para el usuario {user}.')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f'Ocurrió un error al obtener las órdenes para el usuario {user}: {str(e)}')
        return Response({"detail": "Ocurrió un error al obtener las órdenes"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):
    user = request.user

    try:
        order = Order.objects.get(_id=pk)
        if user.is_staff or order.user == user:
            logger.info(f'Usuario {user} accedió a la orden con ID {pk}')
            serializer = OrderSerializer(order, many=False)
            return Response(serializer.data)
        else:
            logger.warning(f'Usuario {user} intentó acceder a una orden no autorizada con ID {pk}')
            return Response({'detail': 'No autorizado para ver este pedido'},
                            status=status.HTTP_400_BAD_REQUEST)
    except Order.DoesNotExist:
        logger.error(f'Usuario {user} intentó acceder a una orden inexistente con ID {pk}')
        return Response({'detail': 'No existe el pedido'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f'Ocurrió un error inesperado al acceder a la orden con ID {pk}: {str(e)}')
        return Response({'detail': 'Ocurrió un error inesperado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        order = Order.objects.get(_id=pk)
        logger.info(f'Se ha accedido al pedido con ID {pk} para realizar un pago.')
    except Order.DoesNotExist:
        logger.warning(f'Intento de acceso a un pedido no existente con ID {pk}.')
        return Response({'error': 'Pedido no encontrado.'}, status=404)

    if order.isPaid:
        logger.warning(f'Intento de pagar un pedido ya pagado con ID {pk}.')
        return Response({'error': 'El pedido ya ha sido pagado.'}, status=400)

    try:
        if order.paymentIntentId:
            payment_intent = stripe.PaymentIntent.retrieve(order.paymentIntentId)
            logger.info(f'Recuperado el intento de pago existente para el pedido {pk}.')
        else:
            customer = stripe.Customer.create()
            ephemeral_key = stripe.EphemeralKey.create(
                customer=customer['id'],
                stripe_version='2022-11-15',
            )
            payment_intent = stripe.PaymentIntent.create(
                amount=int(order.totalPrice * 100),
                currency='eur',
                customer=customer['id']
            )
            order.paymentIntentId = payment_intent.id
            order.save()
            logger.info(f'Creado nuevo intento de pago para el pedido {pk}.')

        return Response({
            'paymentIntent': payment_intent.client_secret,
            'ephemeralKey': ephemeral_key.secret if not order.paymentIntentId else None,
            'customer': customer.id if not order.paymentIntentId else payment_intent.customer
        })

    except Exception as e:
        logger.error(f'Ocurrió un error al realizar el pago para el pedido con ID {pk}: {str(e)}')
        return Response({'error': 'Ocurrió un error al procesar el pago.'}, status=500)

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f'Evento Stripe recibido: {event["type"]}')
    except ValueError:
        logger.warning("Error: Payload inválido.")
        return Response(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("Error: Firma de Stripe inválida.")
        return Response(status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']

        try:
            stripe_payment_intent = stripe.PaymentIntent.retrieve(payment_intent.id)

            if stripe_payment_intent.status == 'succeeded':
                order = Order.objects.get(paymentIntentId=payment_intent.id)
                order.isPaid = True
                order.paidAt = timezone.now()
                order.save()
                logger.info(f'Pago exitoso para la orden con PaymentIntent ID {payment_intent.id}')

        except Exception as e:
            logger.error(f"Error al verificar el PaymentIntent con Stripe: {str(e)}")
            return Response({"error": f"Error al verificar el PaymentIntent con Stripe: {str(e)}"}, status=200)

    elif event['type'] == 'charge.failed':
        charge = event['data']['object']
        try:
            order = Order.objects.get(paymentIntentId=charge['payment_intent'])
            order.isPaid = False
            order.save()
            logger.info(f'Pago fallido para la orden con PaymentIntent ID {charge["payment_intent"]}')
        
        except Exception as e:
            logger.error(f"Error al manejar un pago fallido: {str(e)}")
            return Response({"error": f"Error al manejar un pago fallido: {str(e)}"}, status=200)

    return Response(status=200)