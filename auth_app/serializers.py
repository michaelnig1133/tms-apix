from rest_framework import serializers
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'role', 'department','password','confirm_password']

    def validate(self,data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not much")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.status = "Pending"  
        user.save()
        return user
       


class AdminApproveSerializer(serializers.ModelSerializer):
    rejection_message = serializers.CharField(write_only=True,required=False)
    class Meta:
        model = User
        fields = ['is_active', 'is_pending','rejection_message']

    def validate_is_active(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("The 'is_active' field must be a boolean.")
        return value

    def validate_is_pending(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("The 'is_pending' field must be a boolean.")
        return value    

    def update(self, instance, validated_data):
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_pending = validated_data.get('is_pending', instance.is_pending)
        instance.save()
        return instance
    
class UserDetailSerializer(serializers.ModelSerializer):
  
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number', 'role', 'department', 'is_active', 'is_pending', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_active', 'is_pending', 'created_at', 'updated_at']
