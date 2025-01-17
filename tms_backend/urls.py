from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from auth_app.views import  UserDetailView, UserListView, UserRegistrationView, AdminApprovalView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('approve/<int:user_id>/', AdminApprovalView.as_view(), name='approve'),
    path('users/', UserListView.as_view(), name='pending-users'),
    path('user/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
]
