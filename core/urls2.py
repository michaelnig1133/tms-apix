from django.urls import path

from core.views import (
    MaintenanceRequestActionView,
    MaintenanceRequestCreateView,
    MaintenanceRequestListView,
    RefuelingRequestActionView,
    RefuelingRequestCreateView,
    RefuelingRequestListView,
)

urlpatterns = [
   path('create/', MaintenanceRequestCreateView.as_view(), name='create-maintenance-request'),
   path('list/',MaintenanceRequestListView.as_view(), name= "list-maintenance-request"),
   path('<int:request_id>/action/',MaintenanceRequestActionView.as_view(),name="maintenance-request-action"),
]

urlpatterns_refueling = [
   path('create/', RefuelingRequestCreateView.as_view(), name='create-refueling-request'),
   path('list/',RefuelingRequestListView.as_view(), name= "list-maintenance-request"),
   path('<int:request_id>/action/',RefuelingRequestActionView.as_view(),name="maintenance-request-action"),
]
