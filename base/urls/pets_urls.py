from django.urls import path
from base.views import pet_views as views

urlpatterns = [

    path('create/', views.createPet, name="create-pet"),
    path('create/found/', views.createPetFound, name="create-pet-found"),
    path('', views.getPets, name="pets"),
    path('<str:pk>/', views.getPet, name="pet"),

]
