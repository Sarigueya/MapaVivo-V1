from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/',              admin.site.urls),
    path('api/',                include('recursos.urls')),

    # Páginas del frontend
    path('',                    TemplateView.as_view(template_name='index.html'),            name='home'),
    path('login/',              TemplateView.as_view(template_name='login.html'),            name='login'),
    path('solicitar-cuenta/',   TemplateView.as_view(template_name='solicitar-cuenta.html'), name='solicitar-cuenta'),
    path('admin-panel/',        TemplateView.as_view(template_name='admin-panel.html'),      name='admin-panel'),
    path('mi-perfil/',          TemplateView.as_view(template_name='mi-perfil.html'),        name='mi-perfil'),
]
