# base/routing/routing.py
from django.urls import path
from base.consumers.consumers import ChatConsumer 
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),
]
