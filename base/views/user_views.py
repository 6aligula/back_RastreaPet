from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.models import User
from base.serializers import UserSerializer, UserSerializerWithToken

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed

from django.contrib.auth.hashers import make_password
from rest_framework import status
import re
import logging

logger = logging.getLogger('base')

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            data = super().validate(attrs)

            serializer = UserSerializerWithToken(self.user).data

            for k, v in serializer.items():
                data[k] = v

            username = self.user.username
            logger.info(f'Inicio de sesión exitoso para el usuario: {username}')
            return data
        except AuthenticationFailed:
            logger.warning('Intento de inicio de sesión fallido')
            raise
            

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

def email_exists(email, exclude_user=None):
    users = User.objects.filter(email=email)
    if exclude_user:
        users = users.exclude(id=exclude_user.id)
    return users.exists()

def name_and_email_exist(name, email):
    return User.objects.filter(first_name=name, email=email).exists()

def is_password_strong(password: str) -> bool:
    rules = [
        lambda s: len(s) >= 8,
        lambda s: re.search("[a-z]", s),
        lambda s: re.search("[A-Z]", s),
        lambda s: re.search("[0-9]", s),
        lambda s: re.search('[@_!#$%^&*()<>?/\\|}{~:]', s)
    ]
    
    return all(rule(password) for rule in rules)

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}$"
    return bool(re.match(pattern, email))

@api_view(['POST'])
def registerUser(request):
    data = request.data
    email = (data['email']).strip().lower()
    name = (data['name']).strip()
    password = (data['password']).strip()

    if not is_valid_email(email):
        logger.warning('Intento de registro con correo electrónico no válido.')
        return Response({'detail': 'Formato de correo electrónico no válido'}, status=status.HTTP_400_BAD_REQUEST)
    
    if email_exists(email):
        logger.error(f'Intento de registro con correo electrónico existente: {email}.')
        return Response({'detail': 'La información proporcionada no es válida'}, status=status.HTTP_400_BAD_REQUEST)
    
    if name_and_email_exist(name, email):
        logger.error(f'Intento de registro con correo electrónico y nombre existentes: {email}, {name}.')
        return Response({'detail': 'Este email y usuario ya existen'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not is_password_strong(password):
        logger.warning('Intento de registro con contraseña débil.')
        return Response({'detail': 'Contraseña debil, debe contener minúsculas, mayúsculas, numeros y caracteres especiales'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create(
            first_name=name,
            username=email,
            email=email,
            password=make_password(password)
        )
        serializer = UserSerializerWithToken(user, many=False)
        logger.info(f'Usuario registrado con éxito: {email}.')
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error al registrar usuario: {str(e)}.')
        message = {'detail': 'La información proporcionada no es válida, revisa el formato de tu correo'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user = request.user
    serializer = UserSerializerWithToken(user, many=False)

    data = request.data
    email = (data['email']).strip().lower()
    name = (data['name']).strip()
    password = (data['password']).strip()

    if not is_valid_email(email):
        logger.warning(f'Usuario {user.username} intentó actualizar con un correo electrónico inválido.')
        return Response({'detail': 'Formato de correo electrónico no válido'}, status=status.HTTP_400_BAD_REQUEST)

    if email_exists(email, exclude_user=user):
        logger.warning(f'Usuario {user.username} intentó actualizar con un correo electrónico ya existente.')
        return Response({'detail': 'La información proporcionada no es válida'}, status=status.HTTP_400_BAD_REQUEST)

    if not is_password_strong(password):
        logger.warning(f'Usuario {user.username} intentó actualizar con una contraseña débil.')
        return Response({'detail': 'Contraseña débil, debe contener minúsculas, mayúsculas, números y caracteres especiales'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user.first_name = name
        user.username = email
        user.email = email

        if password != '':
            user.password = make_password(password)

        user.save()
        logger.info(f'Perfil del usuario {user.username} actualizado con éxito.')
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error al actualizar el perfil del usuario {user.username}: {str(e)}.')
        return Response({'detail': 'No se pudo actualizar el perfil del usuario'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    try:
        serializer = UserSerializer(user, many=False)
        logger.info(f'Perfil del usuario {user.username} ha sido accedido con éxito.')
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'Error al acceder al perfil del usuario {user.username}: {str(e)}.')
        return Response({'detail': 'No se pudo acceder al perfil del usuario'}, status=status.HTTP_400_BAD_REQUEST)