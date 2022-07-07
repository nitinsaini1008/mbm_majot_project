from django.urls import path,include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'',views.UserViewSet)


urlpatterns = [
    path('login/',views.signin,name='signin'),
    path("google-login/", views.google_login, name="google-login"),
    path('logout/<int:id>/',views.signout,name='signout'),
    path('',include(router.urls)),
    
]