from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.forms.models.field_type import FormFieldType
from apps.forms.serializers.field_type_serializers import FormFieldTypeSerializer

class FormFieldTypeListView(APIView):
    """
    Returns a grouped list of available form field types for the frontend Form Builder.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        field_types = FormFieldType.objects.filter(is_active=True).order_by('category', 'label')
        
        # Group by category
        grouped = {}
        for ft in field_types:
            cat = ft.category
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({
                "name": ft.name,
                "label": ft.label,
                "description": ft.description
            })
            
        # Return as an array of categories
        result = [
            {"category": cat, "types": types}
            for cat, types in grouped.items()
        ]
        
        return Response(result)
