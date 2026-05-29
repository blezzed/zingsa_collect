from rest_framework import serializers
from apps.forms.models.field_type import FormFieldType

class FormFieldTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormFieldType
        fields = ['name', 'label', 'description', 'category', 'properties_schema']
