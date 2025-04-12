from django.urls import path

from core.views import (
    MaintenanceRequestActionView,
    MaintenanceRequestCreateView,
    MaintenanceRequestListView,
    RefuelingRequestActionView,
    RefuelingRequestCreateView,
    RefuelingRequestDetailView,
    RefuelingRequestEstimateView,
    RefuelingRequestListView,
)

urlpatterns = [
   path('create/', MaintenanceRequestCreateView.as_view(), name='create-maintenance-request'),
   path('list/',MaintenanceRequestListView.as_view(), name= "list-maintenance-request"),
   path('<int:request_id>/action/',MaintenanceRequestActionView.as_view(),name="maintenance-request-action"),
]

urlpatterns_refueling = [
   path('create/', RefuelingRequestCreateView.as_view(), name='create-refueling-request'),
   path('list/',RefuelingRequestListView.as_view(), name= "list-refueling-request"),
   path('<int:pk>/',RefuelingRequestDetailView.as_view(),name="refueling-request-detail"),
   path('<int:request_id>/estimate/',RefuelingRequestEstimateView.as_view(),name="estimate-refueling-request"),
   path('<int:request_id>/action/',RefuelingRequestActionView.as_view(),name="refueling-request-action"),
]