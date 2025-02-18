from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from auth_app.permissions import IsTransportManager
from core.models import TransportRequest, Vehicle, Notification
from core.serializers import TransportRequestSerializer, NotificationSerializer, VehicleSerializer
from core.services import NotificationService
from auth_app.models import User

# class VehicleCreateView(APIView):
#     permission_classes = [IsTransportManager]

#     defbl post(self,request):
#         serializer = VehicleSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 "message":"Vehicle successfully registered",
#             },status=status.HTTP_201_CREATED)
#         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class VehicleViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsTransportManager]


class TransportRequestCreateView(generics.CreateAPIView):
    queryset = TransportRequest.objects.all()
    serializer_class = TransportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        transport_request = serializer.save(requester=self.request.user)
        
        # Notify department manager
        department = self.request.user.department
        if department and department.department_manager:
            NotificationService.create_notification(
                'new_request',
                transport_request,
                department.department_manager
            )

class TransportRequestListView(generics.ListAPIView):
    queryset = TransportRequest.objects.all()
    serializer_class = TransportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.DEPARTMENT_MANAGER:
            return TransportRequest.objects.filter(status='pending')
        elif user.role == user.TRANSPORT_MANAGER:
            return TransportRequest.objects.filter(status='forwarded')
        elif user.role == user.CEO:
            # CEO can see all approved requests
            return TransportRequest.objects.filter(status='forwarded',current_approver_role=User.TRANSPORT_MANAGER)
        elif user.role == user.FINANCE_MANAGER:
            # Finance manager sees approved requests
            return TransportRequest.objects.filter(status='forwarded',current_approver_role=User.CEO)
        # Regular users see their own requests
        return TransportRequest.objects.filter(requester=user)


class TransportRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        transport_request = get_object_or_404(TransportRequest, id=request_id)
        action = request.data.get("action")

        try:
            if action not in ['forward', 'reject', 'approve']:
                return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

            # Department Manager Actions
            if request.user.role == User.DEPARTMENT_MANAGER and transport_request.current_approver_role == User.DEPARTMENT_MANAGER:
                if action == 'forward':
                    transport_request.status = 'forwarded'
                    transport_request.current_approver_role = User.TRANSPORT_MANAGER
                    # Notify Transport Manager
                    transport_managers = User.objects.filter(role=User.TRANSPORT_MANAGER, is_active=True)
                    for manager in transport_managers:
                        NotificationService.create_notification(
                            'forwarded',
                            transport_request,
                            manager
                        )
                elif action == 'reject':
                    transport_request.status = 'rejected'
                    transport_request.rejection_message = request.data.get("rejection_message", "")
                    # Notify requester of rejection
                    NotificationService.create_notification(
                        'rejected',
                        transport_request,
                        transport_request.requester,
                        rejector=request.user.full_name
                    )
                else:
                    return Response({"error": "Department Managers can only forward or reject."}, status=status.HTTP_403_FORBIDDEN)

            # Transport Manager Actions
            elif request.user.role == User.TRANSPORT_MANAGER and transport_request.current_approver_role == User.TRANSPORT_MANAGER:
                if action == 'approve':
                    transport_request.status = 'approved'
                    driver_id = request.data.get("driver_id")
                    driver = get_object_or_404(User, id=driver_id)

                    if TransportRequest.objects.filter(driver=driver, status='approved').exists():
                        return Response({"error": "Driver is already assigned to another request."}, status=status.HTTP_400_BAD_REQUEST)

                    vehicle_id = request.data.get("vehicle_id")
                    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

                    if TransportRequest.objects.filter(vehicle=vehicle, status='approved').exists():
                        return Response({"error": "Vehicle is already assigned to another request."}, status=status.HTTP_400_BAD_REQUEST)

                    transport_request.driver = driver
                    transport_request.vehicle = vehicle
                    # Notify requester and driver
                    NotificationService.create_notification(
                        'approved',
                        transport_request,
                        transport_request.requester,
                        approver=request.user.full_name
                    )
                    NotificationService.create_notification(
                        'assigned',
                        transport_request,
                        transport_request.driver
                    )
                elif action == 'reject':
                    transport_request.status = 'rejected'
                    transport_request.rejection_message = request.data.get("rejection_message", "")
                    NotificationService.create_notification(
                        'rejected',
                        transport_request,
                        transport_request.requester,
                        rejector=request.user.full_name
                    )
                elif action == 'forward':
                    transport_request.status = 'forwarded'
                    transport_request.current_approver_role = User.CEO
                    # Notify CEO
                    ceos = User.objects.filter(role=User.CEO, is_active=True)
                    for ceo in ceos:
                        NotificationService.create_notification(
                            'forwarded',
                            transport_request,
                            ceo
                        )
                else:
                    return Response({"error": "Transport Managers can approve, reject, or forward."}, status=status.HTTP_403_FORBIDDEN)

            # CEO Actions
            elif request.user.role == User.CEO and transport_request.current_approver_role == User.CEO:
                if action == 'forward':
                    transport_request.status = 'forwarded'
                    transport_request.current_approver_role = User.FINANCE_MANAGER
                    # Notify Finance Manager
                    finance_managers = User.objects.filter(role=User.FINANCE_MANAGER, is_active=True)
                    for manager in finance_managers:
                        NotificationService.create_notification(
                            'forwarded',
                            transport_request,
                            manager
                        )
                elif action == 'reject':
                    transport_request.status = 'rejected'
                    transport_request.rejection_message = request.data.get("rejection_message", "")
                    NotificationService.create_notification(
                        'rejected',
                        transport_request,
                        transport_request.requester,
                        rejector=request.user.full_name
                    )
                else:
                    return Response({"error": "CEOs can only forward or reject."}, status=status.HTTP_403_FORBIDDEN)

            # Finance Manager Actions
            elif request.user.role == User.FINANCE_MANAGER and transport_request.current_approver_role == User.FINANCE_MANAGER:
                if action == 'approve':
                    transport_request.status = 'approved'
                    transport_request.current_approver_role = User.TRANSPORT_MANAGER
                    # Notify Transport Manager and requester
                    transport_managers = User.objects.filter(role=User.TRANSPORT_MANAGER, is_active=True)
                    for manager in transport_managers:
                        NotificationService.create_notification(
                            'forwarded',
                            transport_request,
                            manager
                        )
                    NotificationService.create_notification(
                        'approved',
                        transport_request,
                        transport_request.requester,
                        approver=request.user.full_name
                    )
                elif action == 'reject':
                    transport_request.status = 'rejected'
                    transport_request.rejection_message = request.data.get("rejection_message", "")
                    NotificationService.create_notification(
                        'rejected',
                        transport_request,
                        transport_request.requester,
                        rejector=request.user.full_name
                    )
                else:
                    return Response({"error": "Finance Managers can only approve or reject."}, status=status.HTTP_403_FORBIDDEN)

            transport_request.save()
            return Response({"message": f"Request {action}ed successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get user's notifications with pagination
        """
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        notifications = NotificationService.get_user_notifications(
            request.user.id, 
            unread_only=unread_only,
            page=page,
            page_size=page_size
        )

        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'results': serializer.data,
            'unread_count': NotificationService.get_unread_count(request.user.id)
        })


class NotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        """
        Mark a notification as read
        """
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            notification.mark_as_read()
            return Response(status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class NotificationMarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Mark all notifications as read for the current user
        """
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response(status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Get count of unread notifications
        """
        count = NotificationService.get_unread_count(request.user.id)
        return Response({'unread_count': count})