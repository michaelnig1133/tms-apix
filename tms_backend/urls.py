from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from auth_app.views import  DeactivateUserView, ReactivateUserView, UserDetailView, UserRegistrationView, AdminApprovalView, UserResubmissionView, UserStatusHistoryViewSet

router = DefaultRouter()
router.register(r'status-history', UserStatusHistoryViewSet, basename='status-history')


urlpatterns = [
    path('',include(router.urls)),
    path("admin/", admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('approve/<int:user_id>/', AdminApprovalView.as_view(), name='approve'),
    path('users/', AdminApprovalView.as_view(), name='users'),
    path('user/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path("resubmit/<int:user_id>/", UserResubmissionView.as_view(), name="resubmit"),
    path("activate/<int:user_id>/",ReactivateUserView.as_view(),name="activate"),
    path("deactivate/<int:user_id>/",DeactivateUserView.as_view(),name="activate"),
]
