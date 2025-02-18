from rest_framework import serializers

from auth_app.models import User
from django.utils.timezone import now 
from core.models import TransportRequest, Vehicle, Notification

class TransportRequestSerializer(serializers.ModelSerializer):
    requester = serializers.ReadOnlyField(source='requester.get_full_name')
    employees = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = TransportRequest
        fields = '__all__'

    def validate(self, data):
        """
        Ensure return_day is not before start_day.
        """
        start_day = data.get("start_day")
        return_day = data.get("return_day")
        start_time = data.get("start_day")

        if start_day and start_day < now().date():
            raise serializers.ValidationError({"start_day": "Start date cannot be in the past."})
        
        

        if return_day and start_day and return_day < start_day:
            raise serializers.ValidationError({"return_day": "Return date cannot be before the start date."})

        return data
    
    def create(self, validated_data):
        """
        Automatically assigns the currently logged-in user as the requester.
        """
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["requester"] = request.user
        return super().create(validated_data)
    
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

    # def validate(self, data):
    #     """ Ensure rental details are provided if the vehicle is rented """
    #     if data.get('source') == Vehicle.RENTED:
    #         if not data.get('rental_company') or not data.get('rental_price_per_day'):
    #             raise serializers.ValidationError("Rental company and rental price per day are required for rented vehicles.")
    #     return data

class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient_name', 'notification_type', 'title', 
            'message', 'is_read', 'action_required', 'priority', 
            'metadata', 'created_at'
        ]
        read_only_fields = fields