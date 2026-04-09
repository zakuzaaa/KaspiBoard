from rest_framework import serializers
from .models import Ad

class AdSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source='author.username')
    category_name = serializers.ReadOnlyField(source='category.name')
    city_name = serializers.ReadOnlyField(source='city.name')

    class Meta:
        model = Ad
        fields = [
            'uuid', 'author_name', 'category', 'category_name', 
            'city', 'city_name', 'title', 'description', 
            'price', 'image', 'created_at', 'is_top'
        ]