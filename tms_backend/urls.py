from django.contrib import admin
from django.urls import include, path
from auth_app.urls import urlpatterns as auth_urls
from core.urls import urlpatterns as core_urls
from rest_framework.routers import DefaultRouter

from core.views import VehicleViewSet

router = DefaultRouter()
router.register(r'vehicles',VehicleViewSet)
urlpatterns = [
    path('',include(auth_urls)),
    path("transport-requests/",include(core_urls)),
    path("",include(router.urls))
   
]
