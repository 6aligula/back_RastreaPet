from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html')),

    path('login', TemplateView.as_view(template_name='index.html')),
    path('register', TemplateView.as_view(template_name='index.html')),
    path('profile', TemplateView.as_view(template_name='index.html')),
    path('shipping', TemplateView.as_view(template_name='index.html')),
    path('payment', TemplateView.as_view(template_name='index.html')),
    path('placeorder', TemplateView.as_view(template_name='index.html')),
    path('order/<str:pk>/', TemplateView.as_view(template_name='index.html')),
    path('product/<str:pk>', TemplateView.as_view(template_name='index.html')),
    path('cart/<str:pk>', TemplateView.as_view(template_name='index.html')),
    path('cart', TemplateView.as_view(template_name='index.html')),

    path('api/pets/', include('base.urls.pets_urls')),
    path('api/users/', include('base.urls.user_urls')),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)