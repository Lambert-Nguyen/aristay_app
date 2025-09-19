from rest_framework import serializers


class CalendarEventSerializer(serializers.Serializer):
    """Generic event serializer for unified calendar responses.

    This aligns with tests that import CalendarEventSerializer directly.
    All fields are optional to accommodate both task and booking shapes.
    """
    id = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    start = serializers.CharField(required=False)
    end = serializers.CharField(required=False, allow_null=True)
    allDay = serializers.BooleanField(required=False)
    type = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    color = serializers.CharField(required=False)
    property_name = serializers.CharField(required=False, allow_null=True)
    guest_name = serializers.CharField(required=False, allow_null=True)
    assigned_to = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    url = serializers.CharField(required=False, allow_null=True)


class CalendarTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    title = serializers.CharField()
    due_date = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    property_name = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()

    def get_property_name(self, obj):
        prop = getattr(obj, "property_ref", None)
        return prop.name if prop else None

    def get_assigned_to(self, obj):
        user = getattr(obj, "assigned_to", None)
        return user.username if user else None


class CalendarBookingSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="pk")
    property_name = serializers.SerializerMethodField()
    guest_name = serializers.CharField()
    check_in_date = serializers.DateTimeField()
    check_out_date = serializers.DateTimeField()
    status = serializers.CharField()

    def get_property_name(self, obj):
        prop = getattr(obj, "property", None)
        return prop.name if prop else None


class CalendarFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    property_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)
    task_type = serializers.CharField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    include_tasks = serializers.BooleanField(required=False, default=True)
    include_bookings = serializers.BooleanField(required=False, default=True)


