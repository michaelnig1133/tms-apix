from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from auth_app.permissions import IsTransportManager
from auth_app.serializers import UserDetailSerializer
from core import serializers
from core.models import TransportRequest, Vehicle, Notification
from core.serializers import TransportRequestSerializer, NotificationSerializer, VehicleSerializer
from core.services import NotificationService
from auth_app.models import User
import logging


logger = logging.getLogger(__name__)
# class VehicleCreateView(APIView):
#     permission_classes = [IsTransportManager]

#     def post(self,request):
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object() 
        serializer = self.get_serializer(instance, data=request.data, partial=True)  
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

class AvailableVehiclesListView(generics.ListAPIView):
    queryset = Vehicle.objects.filter(status=Vehicle.AVAILABLE).select_related("driver")
    serializer_class = VehicleSerializer
    permission_classes = [IsTransportManager]

class AvailableDriversView(APIView):
    permission_classes = [IsTransportManager]

    def get(self, request):
        drivers = User.objects.exclude(role__in=[User.SYSTEM_ADMIN,User.EMPLOYEE])  # Only fetch unassigned drivers
        drivers=drivers.filter(assigned_vehicle__isnull=True)
        serializer = UserDetailSerializer(drivers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# class TransportRequestCreateView(generics.CreateAPIView):
#     queryset = TransportRequest.objects.all()
#     serializer_class = TransportRequestSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def perform_create(self, serializer):
#         transport_request = serializer.save(requester=self.request.user)
        
#         # Notify department manager
#         department = self.request.user.department
#         if department and department.department_manager:
#             NotificationService.create_notification(
#                 'new_request',
#                 transport_request,
#                 department.department_manager
#             )

class TransportRequestCreateView(generics.CreateAPIView):
    queryset = TransportRequest.objects.all()
    serializer_class = TransportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        employee = self.request.user
        department = employee.department  # Get the department of the employee
        
        if not department:
            raise serializers.ValidationError("You are not assigned to any department.")

        department_manager = User.objects.filter(department=department, role=User.DEPARTMENT_MANAGER, is_active=True).first()
        
        if not department_manager:
            raise serializers.ValidationError("No department manager is assigned to your department.")

        transport_request = serializer.save(requester=employee)
        
        # Notify department managers of the employee's department
        # for manager in department_managers:
        NotificationService.create_notification(
            'new_request',
            transport_request,
            department_manager
        )


class TransportRequestListView(generics.ListAPIView):
    queryset = TransportRequest.objects.all()
    serializer_class = TransportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.DEPARTMENT_MANAGER:
            return TransportRequest.objects.filter(status='pending',requester__department=user.department)
        elif user.role == user.TRANSPORT_MANAGER:
            return TransportRequest.objects.filter(status='forwarded',current_approver_role=User.TRANSPORT_MANAGER)
        elif user.role == user.CEO:
            # CEO can see all approved requests
            return TransportRequest.objects.filter(status='forwarded',current_approver_role=User.CEO)
        elif user.role == user.FINANCE_MANAGER:
            # Finance manager sees approved requests
            return TransportRequest.objects.filter(status='forwarded',current_approver_role=User.FINANCE_MANAGER)
        # Regular users see their own requests
        return TransportRequest.objects.filter(requester=user)


class TransportRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_next_approver_role(self, current_role):
        """Determine the next approver based on hierarchy."""
        role_hierarchy = {
            User.DEPARTMENT_MANAGER: User.TRANSPORT_MANAGER,
            User.TRANSPORT_MANAGER: User.CEO,
            User.CEO: User.FINANCE_MANAGER,
            User.FINANCE_MANAGER: User.TRANSPORT_MANAGER,
        }
        return role_hierarchy.get(current_role, None)  
    def post(self, request, request_id):
        transport_request = get_object_or_404(TransportRequest, id=request_id)
        action = request.data.get("action")

        if action not in ['forward', 'reject', 'approve']:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        if transport_request.requester.department != request.user.department:
            return Response(
                {"error": "You can only manage requests from employees in your department."},
                status=status.HTTP_403_FORBIDDEN
            )

        current_role = request.user.role
        if current_role != transport_request.current_approver_role:
            return Response({"error": "You are not authorized to act on this request."}, status=status.HTTP_403_FORBIDDEN)

        if action == 'forward':
            next_role = self.get_next_approver_role(current_role)
            if not next_role:
                return Response({"error": "No further approver available."}, status=status.HTTP_400_BAD_REQUEST)

            transport_request.status = 'forwarded'
            transport_request.current_approver_role = next_role

            # Notify the next approver
            next_approvers = User.objects.filter(role=next_role, is_active=True)
            for approver in next_approvers:
                NotificationService.create_notification('forwarded', transport_request, approver)

        elif action == 'reject':
            transport_request.status = 'rejected'
            transport_request.rejection_message = request.data.get("rejection_message", "")

            # Notify requester of rejection
            NotificationService.create_notification(
                'rejected', transport_request, transport_request.requester, rejector=request.user.full_name
            )

        elif action == 'approve' and current_role == User.TRANSPORT_MANAGER:
            vehicle_id = request.data.get("vehicle_id")
            vehicle = Vehicle.objects.select_related("driver").filter(id=vehicle_id).first()

            if not vehicle:
                return Response({"error": "Invalid vehicle ID."}, status=status.HTTP_400_BAD_REQUEST)

            if TransportRequest.objects.filter(vehicle=vehicle, status='approved').exists():
                return Response({"error": "Vehicle is already assigned to another request."}, status=status.HTTP_400_BAD_REQUEST)

            if not vehicle.driver:
                return Response({"error": "Selected vehicle does not have an assigned driver."}, status=status.HTTP_400_BAD_REQUEST)

            # Notify requester and driver
            NotificationService.create_notification(
                'approved', transport_request, transport_request.requester,
                approver=request.user.full_name, vehicle=f"{vehicle.model} ({vehicle.license_plate})",
                driver=vehicle.driver.full_name, destination=transport_request.destination,
                date=transport_request.start_day.strftime('%Y-%m-%d'), start_time=transport_request.start_time.strftime('%H:%M')
            )

            NotificationService.create_notification(
                'assigned', transport_request, vehicle.driver,
                vehicle=f"{vehicle.model} ({vehicle.license_plate})", destination=transport_request.destination,
                date=transport_request.start_day.strftime('%Y-%m-%d'), start_time=transport_request.start_time.strftime('%H:%M')
            )

            transport_request.vehicle = vehicle
            transport_request.status = 'approved'
            vehicle.mark_as_in_use()

        else:
            return Response({"error": f"{current_role} cannot perform {action}."}, status=status.HTTP_403_FORBIDDEN)

        transport_request.save()
        return Response({"message": f"Request {action}ed successfully."}, status=status.HTTP_200_OK)

class TransportRequestHistoryView(generics.ListAPIView):
    serializer_class = TransportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TransportRequest.objects.filter(action_logs__action_by=user).distinct()


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