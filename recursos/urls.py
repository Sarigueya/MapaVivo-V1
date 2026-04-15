from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/registro/',                  views.RegistroView.as_view()),
    path('auth/login/',                     views.LoginView.as_view()),
    path('auth/logout/',                    views.LogoutView.as_view()),
    path('auth/perfil/',                    views.MiPerfilView.as_view()),
    path('auth/perfil/organizacion/',       views.ActualizarOrganizacionView.as_view()),
    path('auth/cambiar-password/',          views.CambiarPasswordView.as_view()),

    # Admin
    path('admin/organizaciones/',           views.AdminOrganizacionesView.as_view()),
    path('admin/organizaciones/<int:pk>/',  views.AdminOrganizacionDetalleView.as_view()),
    path('admin/organizaciones/<int:pk>/reset-password/', views.AdminResetPasswordView.as_view()),

    # Recursos
    path('recursos/',                       views.RecursoListCreate.as_view()),
    path('recursos/<int:pk>/',              views.RecursoDetail.as_view()),
    path('recursos/<int:pk>/sin-stock/',    views.RecursoSinStockView.as_view()),
    path('recursos/mios/', views.MisRecursosView.as_view()), # Nueva ruta para ver solo los recursos del usuario autenticado

    # Utilidades
    path('health/',                         views.HealthCheck.as_view()),
]
