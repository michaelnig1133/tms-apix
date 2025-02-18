from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from auth_app.models import User, Department
from core.models import Vehicle, TransportRequest

class TransportRequestWorkflowTest(TestCase):
    def setUp(self):
        # Create department
        self.department = Department.objects.create(name="Test Department")

        # Create test users with different roles
        self.employee = User.objects.create_user(
            email="employee@test.com",
            password="testpass123",
            full_name="Test Employee",
            role=User.EMPLOYEE,
            department=self.department,
            is_active=True,
            phone_number="1234567890"
        )

        self.dept_manager = User.objects.create_user(
            email="dept_manager@test.com",
            password="testpass123",
            full_name="Dept Manager",
            role=User.DEPARTMENT_MANAGER,
            department=self.department,
            is_active=True,
            phone_number="1234567891"
        )

        self.transport_manager = User.objects.create_user(
            email="transport@test.com",
            password="testpass123",
            full_name="Transport Manager",
            role=User.TRANSPORT_MANAGER,
            is_active=True,
            phone_number="1234567892"
        )

        self.ceo = User.objects.create_user(
            email="ceo@test.com",
            password="testpass123",
            full_name="CEO User",
            role=User.CEO,
            is_active=True,
            phone_number="1234567893"
        )

        self.finance_manager = User.objects.create_user(
            email="finance@test.com",
            password="testpass123",
            full_name="Finance Manager",
            role=User.FINANCE_MANAGER,
            is_active=True,
            phone_number="1234567894"
        )

        # Create test vehicle
        self.vehicle = Vehicle.objects.create(
            license_plate="TEST123",
            model="Test Model",
            capacity=4,
            is_available=True
        )

        # Create API client
        self.client = APIClient()

        # Transport request data
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.request_data = {
            "start_day": tomorrow,
            "return_day": tomorrow + timedelta(days=1),
            "start_time": "09:00:00",
            "destination": "Test Destination",
            "reason": "Test reason for transport",
            "employees": [self.employee.id]
        }

    def test_complete_transport_request_workflow(self):
        # 1. Employee creates transport request
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(reverse('create-transport-request'), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request_id = response.data['id']

        # 2. Department Manager forwards request
        self.client.force_authenticate(user=self.dept_manager)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {"action": "forward"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Transport Manager forwards to CEO
        self.client.force_authenticate(user=self.transport_manager)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {"action": "forward"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. CEO forwards to Finance Manager
        self.client.force_authenticate(user=self.ceo)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {"action": "forward"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Finance Manager approves
        self.client.force_authenticate(user=self.finance_manager)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {"action": "approve"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. Transport Manager final approval with vehicle and driver assignment
        self.client.force_authenticate(user=self.transport_manager)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {
                "action": "approve",
                "vehicle_id": self.vehicle.id,
                "driver_id": self.transport_manager.id
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify final state
        transport_request = TransportRequest.objects.get(id=request_id)
        self.assertEqual(transport_request.status, 'approved')
        self.assertEqual(transport_request.vehicle.id, self.vehicle.id)
        self.assertEqual(transport_request.driver.id, self.transport_manager.id)

    def test_department_manager_rejection(self):
        # 1. Employee creates transport request
        self.client.force_authenticate(user=self.employee)
        response = self.client.post(reverse('create-transport-request'), self.request_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request_id = response.data['id']

        # 2. Department Manager rejects request
        self.client.force_authenticate(user=self.dept_manager)
        response = self.client.post(
            reverse('transport-request-action', kwargs={'request_id': request_id}),
            {
                "action": "reject",
                "rejection_message": "Budget constraints"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify rejected state
        transport_request = TransportRequest.objects.get(id=request_id)
        self.assertEqual(transport_request.status, 'rejected')
        self.assertEqual(transport_request.rejection_message, "Budget constraints")
