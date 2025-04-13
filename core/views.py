from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from auth_app.permissions import IsTransportManager
from auth_app.serializers import UserDetailSerializer
from core import serializers
from core.models import MaintenanceRequest, RefuelingRequest, TransportRequest, Vehicle, Notification
from core.permissions import IsAllowedVehicleUser
from core.serializers import AssignedVehicleSerializer, MaintenanceRequestSerializer, RefuelingRequestDetailSerializer, RefuelingRequestSerializer, TransportRequestSerializer, NotificationSerializer, VehicleSerializer
from core.services import NotificationService, RefuelingEstimator, log_action
from auth_app.models import User
import logging
from rest_framework.generics import RetrieveAPIView

logger = logging.getLogger(__name__)
class MyAssignedVehicleView(APIView):
    permission_classes = [permissions.IsAuthenticated,IsAllowedVehicleUser]

    def get(self, request):
        try:
            vehicle = request.user.assigned_vehicle  # Thanks to related_name='assigned_vehicle'
        except Vehicle.DoesNotExist:
            return Response({"message": "No vehicle assigned to you."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignedVehicleSerializer(vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        drivers = User.objects.exclude(role__in=[User.SYSTEM_ADMIN,User.EMPLOYEE])  
        drivers=drivers.filter(assigned_vehicle__isnull=True)
        serializer = UserDetailSerializer(drivers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        elif user.role == User.DRIVER:
        # Drivers see only the requests where they are assigned via the vehicle
            return TransportRequest.objects.filter(vehicle__driver=user,status='approved')  # Optional: restrict to approved requests only
        return TransportRequest.objects.filter(requester=user)
    
class MaintenanceRequestCreateView(generics.CreateAPIView):
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Override to set requester and their assigned vehicle automatically."""
        user = self.request.user
        if not hasattr(user, 'assigned_vehicle') or user.assigned_vehicle is None:
            raise serializers.ValidationError({"error": "You do not have an assigned vehicle."})

        transport_manager = User.objects.filter(role=User.TRANSPORT_MANAGER, is_active=True).first()

        if not transport_manager:
            raise serializers.ValidationError({"error": "No active Transport Manager found."})

        # Save the maintenance request
        maintenance_request = serializer.save(requester=user, requesters_car=user.assigned_vehicle)

        # Now correctly call the notification service with the correct parameters
        NotificationService.send_maintenance_notification(
            notification_type='new_maintenance',
            maintenance_request=maintenance_request,  # MaintenanceRequest instance
            recipient=transport_manager  # Recipient (User instance)
        )       


class RefuelingRequestCreateView(generics.CreateAPIView):
    serializer_class = RefuelingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Set the requester and default approver before saving."""
        user = self.request.user
        if not hasattr(user, 'assigned_vehicle') or user.assigned_vehicle is None:
            raise serializers.ValidationError({"error": "You do not have an assigned vehicle."})
        transport_manager = User.objects.filter(role=User.TRANSPORT_MANAGER, is_active=True).first()

        if not transport_manager:
            raise serializers.ValidationError({"error": "No active Transport Manager found."})
        refueling_request=serializer.save(requester=user,requesters_car=user.assigned_vehicle)
        NotificationService.send_refueling_notification(
            notification_type='new_refueling',
            refueling_request=refueling_request,
            recipient=transport_manager
        )
class RefuelingRequestListView(generics.ListAPIView):
    queryset = RefuelingRequest.objects.all()
    serializer_class = RefuelingRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.TRANSPORT_MANAGER:
            return RefuelingRequest.objects.filter(status='pending')
        elif user.role == user.CEO:
            return RefuelingRequest.objects.filter(status='forwarded',current_approver_role=User.CEO)
        elif user.role == user.FINANCE_MANAGER:
            # Finance manager sees approved requests
            return RefuelingRequest.objects.filter(status='forwarded',current_approver_role=User.FINANCE_MANAGER)
        return RefuelingRequest.objects.filter(requester=user)
class RefuelingRequestEstimateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        refueling_request = get_object_or_404(RefuelingRequest, id=request_id)
        if request.user.role != User.TRANSPORT_MANAGER:
            return Response({"error": "Unauthorized"}, status=403)

        distance = request.data.get('estimated_distance_km')
        price = request.data.get('fuel_price_per_liter')

        if not distance or not price:
            return Response({"error": "Distance and fuel price are required."}, status=400)

        try:
            distance = float(distance)
            price = float(price)
            fuel_needed, total_cost = RefuelingEstimator.calculate_fuel_cost(
                distance, refueling_request.requesters_car, price
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        refueling_request.estimated_distance_km = distance
        refueling_request.fuel_price_per_liter = price
        refueling_request.fuel_needed_liters = fuel_needed
        refueling_request.total_cost = total_cost
        refueling_request.save()

        return Response({
            "fuel_needed_liters": fuel_needed,
            "total_cost": total_cost
        }, status=200)
class RefuelingRequestDetailView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RefuelingRequestDetailSerializer
    queryset = RefuelingRequest.objects.all()

    def get(self, request, *args, **kwargs):
        refueling_request = self.get_object()

        if request.user.role not in [
            User.TRANSPORT_MANAGER,
            User.GENERAL_SYSTEM,
            User.CEO,
            User.BUDGET_MANAGER,
            User.FINANCE_MANAGER,
            User.DEPARTMENT_MANAGER,
            User.DRIVER,
        ]:
            return Response({"error": "Access denied."}, status=403)

        serializer = self.get_serializer(refueling_request)
        return Response(serializer.data)

class RefuelingRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_next_approver_role(self, current_role):
        """Determine the next approver based on hierarchy."""
        role_hierarchy = {
            User.TRANSPORT_MANAGER: User.GENERAL_SYSTEM,
            User.GENERAL_SYSTEM: User.CEO,
            User.CEO: User.BUDGET_MANAGER,
            User.BUDGET_MANAGER: User.FINANCE_MANAGER,
        }
        return role_hierarchy.get(current_role, None)

    def post(self, request, request_id):
        refueling_request = get_object_or_404(RefuelingRequest, id=request_id)
        action = request.data.get("action")

        if action not in ['forward', 'reject', 'approve']:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        current_role = request.user.role
        if current_role != refueling_request.current_approver_role:
            return Response({"error": "You are not authorized to act on this request."}, status=status.HTTP_403_FORBIDDEN)

        # ====== FORWARD ACTION ======
        if action == 'forward':
            if current_role == User.TRANSPORT_MANAGER:
                # Ensure estimation is already completed before forwarding
                if not refueling_request.estimated_distance_km or not refueling_request.fuel_price_per_liter:
                    return Response({
                        "error": "You must estimate distance and fuel price before forwarding."
                    }, status=status.HTTP_400_BAD_REQUEST)
            next_role = self.get_next_approver_role(current_role)
            if not next_role:
                return Response({"error": "No further approver available."}, status=status.HTTP_400_BAD_REQUEST)

            refueling_request.status = 'forwarded'
            refueling_request.current_approver_role = next_role
            # # # Notify the next approver

            next_approvers = User.objects.filter(role=next_role, is_active=True)
            for approver in next_approvers:
                NotificationService.send_refueling_notification(
                    notification_type='refueling_forwarded',
                    refueling_request=refueling_request,
                    recipient=approver
                )
            refueling_request.save()

        # ====== REJECT ACTION ======
        elif action == 'reject':
            rejection_message = request.data.get("rejection_message", "").strip()
            if not rejection_message:
                return Response({"error": "Rejection message is required."}, status=status.HTTP_400_BAD_REQUEST)

            refueling_request.status = 'rejected'
            refueling_request.rejection_message = rejection_message
            refueling_request.save()

            # # # Notify requester of rejection
            NotificationService.send_refueling_notification(
                'refueling_rejected', refueling_request, refueling_request.requester,
                rejector=request.user.full_name, rejection_reason=rejection_message
                )
        # ====== APPROVE ACTION ======
        elif action == 'approve':
            if current_role == User.FINANCE_MANAGER and refueling_request.current_approver_role == User.FINANCE_MANAGER:
                # Final approval by Transport Manager after Finance Manager has approved
                refueling_request.status = 'approved'
                refueling_request.save()

                # # # Notify the original requester of approval
                NotificationService.send_refueling_notification(
                    'refueling_approved', refueling_request, refueling_request.requester,
                    approver=request.user.full_name
                )

            else:
                return Response({"error": f"{request.user.get_role_display()} cannot approve this request at this stage."}, 
                                status=status.HTTP_403_FORBIDDEN)
        else:
             Response({"error": "Unexpected error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        return  Response({"message": f"Request {action}ed successfully."}, status=status.HTTP_200_OK)
   
class MaintenanceRequestListView(generics.ListAPIView):
    queryset = MaintenanceRequest.objects.all()
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.TRANSPORT_MANAGER:
            return MaintenanceRequest.objects.filter(status='pending')
        elif user.role == user.CEO:
            return MaintenanceRequest.objects.filter(status='forwarded',current_approver_role=User.CEO)
        elif user.role == user.FINANCE_MANAGER:
            # Finance manager sees approved requests
            return MaintenanceRequest.objects.filter(status='forwarded',current_approver_role=User.FINANCE_MANAGER)
        return MaintenanceRequest.objects.filter(requester=user)
    


class MaintenanceRequestActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_next_approver_role(self, current_role):
        """Determine the next approver based on hierarchy."""
        role_hierarchy = {
            User.TRANSPORT_MANAGER: User.CEO,
            User.CEO: User.FINANCE_MANAGER,
        }
        return role_hierarchy.get(current_role, None)

    def post(self, request, request_id):
        maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
        action = request.data.get("action")

        if action not in ['forward', 'reject', 'approve']:
            return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        current_role = request.user.role
        print("CURRENT ROLE",current_role)
        logger.info(f"CURRENT ROLE: {current_role}, Action: {action}, Request Status: {maintenance_request.status}")

        if current_role != maintenance_request.current_approver_role:
            return Response({"error": "You are not authorized to act on this request."}, status=status.HTTP_403_FORBIDDEN)

        # ====== FORWARD ACTION ======
        if action == 'forward':
            next_role = self.get_next_approver_role(current_role)
            if not next_role:
                return Response({"error": "No further approver available."}, status=status.HTTP_400_BAD_REQUEST)

            maintenance_request.status = 'forwarded'
            maintenance_request.current_approver_role = next_role
            maintenance_request.save()

            # # Notify the next approver
            next_approvers = User.objects.filter(role=next_role, is_active=True)
            for approver in next_approvers:
                NotificationService.send_maintenance_notification(
                    'maintenance_forwarded', maintenance_request, approver
                )

            return Response({"message": "Request forwarded successfully."}, status=status.HTTP_200_OK)

        # ====== REJECT ACTION ======
        elif action == 'reject':
            rejection_message = request.data.get("rejection_message", "").strip()
            if not rejection_message:
                return Response({"error": "Rejection message is required."}, status=status.HTTP_400_BAD_REQUEST)

            maintenance_request.status = 'rejected'
            maintenance_request.rejection_message = rejection_message
            maintenance_request.save()

            # # Notify requester of rejection
            NotificationService.send_maintenance_notification(
                'maintenance_rejected', maintenance_request, maintenance_request.requester,
                rejector=request.user.full_name, rejection_reason=rejection_message
            )

            return Response({"message": "Request rejected successfully."}, status=status.HTTP_200_OK)

        # ====== APPROVE ACTION ======
        elif action == 'approve':
            if current_role == User.FINANCE_MANAGER and maintenance_request.current_approver_role == User.FINANCE_MANAGER:
                # Final approval by Transport Manager after Finance Manager has approved
                maintenance_request.status = 'approved'
                maintenance_request.save()

                # # Notify the original requester of approval
                NotificationService.send_maintenance_notification(
                    'maintenance_approved', maintenance_request, maintenance_request.requester,
                    approver=request.user.full_name
                )

                return Response({"message": "Request approved successfully."}, status=status.HTTP_200_OK)

            else:
                return Response({"error": f"{request.user.get_role_display()} cannot approve this request at this stage."}, 
                                status=status.HTTP_403_FORBIDDEN)
        else:
             Response({"error": "Unexpected error occurred."}, status=status.HTTP_400_BAD_REQUEST)
        return  Response({"message": f"Request {action}ed successfully."}, status=status.HTTP_200_OK)


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

        if request.user.role == User.DEPARTMENT_MANAGER and transport_request.requester.department != request.user.department:
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
            log_action(transport_request, request.user, 'forwarded')

        elif action == 'reject':
            transport_request.status = 'rejected'
            transport_request.rejection_message = request.data.get("rejection_message", "")

            # Notify requester of rejection
            NotificationService.create_notification(
                'rejected', transport_request, transport_request.requester, rejector=request.user.full_name
            )
            log_action(transport_request, request.user, 'rejected', remarks=transport_request.rejection_message)

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
            log_action(transport_request, request.user, 'approved', remarks=f"Vehicle: {vehicle.license_plate}")

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