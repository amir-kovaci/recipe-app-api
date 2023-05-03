"""Serializers for the user API"""

from django.contrib.auth import (
    get_user_model,
    authenticate)

from rest_framework import serializers
from django.utils.translation import gettext as _

class UserSerializer(serializers.ModelSerializer):
    """Serlializer for the user object"""

    class Meta:
        model = get_user_model()
        fields=['email','password','name']
        extra_kwargs={'password':{'write_only':True,'min_length':5}}

    def create(self,validated_data):
        """Create and return a user with encrypted password"""

        return get_user_model().objects.create_user(**validated_data)
    

class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token"""

    email = serializers.EmailField()
    password=serializers.CharField(
        style={'input': 'password'},
        trim_whitespace=False
    )

    def validate(self,attrbs):
        """Validate and authenticate the user"""
        email = attrbs.get('email')
        password=attrbs.get('password')

        user=authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )

        if not user:
            msg=_('Unable to authenticate with the provided pcredentials.')

            raise serializers.ValidationError(msg,code='authorization')
        
        attrbs['user']=user
        return attrbs