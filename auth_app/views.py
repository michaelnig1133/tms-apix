from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.mail import send_mail

from auth_app.permissions import IsSystemAdmin
from .models import User
from .serializers import UserDetailSerializer, UserRegistrationSerializer, AdminApproveSerializer

class UserRegistrationView(APIView):
    
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Your registration is in progress. Check your email for updates."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_pending=True)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                "error": "No pending user found with this ID."
            }, status=status.HTTP_404_NOT_FOUND)


class UserListView(APIView):
   
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]

    def get(self, request):
        pending_users = User.objects.all()
        serializer = UserDetailSerializer(pending_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)   


class AdminApprovalView(APIView):
   
    permission_classes = [permissions.IsAuthenticated, IsSystemAdmin]

    def get(self, request, user_id):
       
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                "error": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_pending=True)
        except User.DoesNotExist:
            return Response({
                "error": "No pending user found with this ID."
            }, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if not action or action not in ['approve', 'reject']:
            return Response({
                "error": "Invalid action. Please specify 'approve' or 'reject'."
            }, status=status.HTTP_400_BAD_REQUEST)

        request_data = {
            "is_active": action == 'approve',
            "is_pending": False  
        }

        if action == 'reject':
            rejection_message = request.data.get('rejection_message', '').strip()
            if not rejection_message:
                return Response({
                    "error": "Rejection message is required for rejection."
                }, status=status.HTTP_400_BAD_REQUEST)
            request_data["rejection_message"] = rejection_message

        serializer = AdminApproveSerializer(user, data=request_data, partial=True)
        if serializer.is_valid():
            # serializer.save()

            if action == 'approve':
                email_subject = "Registration Approved"
                email_body = (
                    f"Dear {user.full_name},\n\n"
                    "Your registration has been approved. You can now log in.\n\n"
                    "Best regards,\nAdmin Team"
                )
            elif action == 'reject':
                email_subject = "Registration Rejected"
                email_body = (
                    f"Dear {user.full_name},\n\n"
                    "We regret to inform you that your registration has been rejected.\n"
                    f"Reason:\n\n{rejection_message}\n\n"
                    "For more details, please contact support.\n\n"
                    "Best regards,\nAdmin Team"
                )
                

            email_sent = send_mail(
                email_subject,
                email_body,
                'mebrhit765@gmail.com', 
                [user.email],
            )

            if email_sent == 1:
                if action == "approve":
                    serializer.save()
                elif action=="reject":
                    user.delete()
                return Response({
                    "message": f"User {action}d successfully, and email sent."
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": f"User {action}d, but email could not be sent. Please contact support."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
