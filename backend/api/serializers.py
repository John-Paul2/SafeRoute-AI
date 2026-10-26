"""
SafeRoute AI REST API Serializers
Course Outcome Mapping:
    - CO1 (Intelligent Agent Models): Agent request/response contracts and sensor schema validation
    - CO2 (Informed Search): Coordinates and routing parameter validation
    - CO3 (Knowledge Representation): Route statistics and rule evaluation payloads
    - CO4 (Probabilistic Reasoning): Evidence normalization schema
    - CO5 (Machine Learning): Environmental feature validation for risk inference
"""

from rest_framework import serializers


class PredictRequestSerializer(serializers.Serializer):
    """Validates environmental sensor telemetry for accident risk prediction."""
    weather = serializers.CharField(required=False, default="Clear")
    weather_condition = serializers.CharField(required=False, default=None)
    precipitation = serializers.FloatField(required=False, default=0.0, min_value=0.0, max_value=20.0)
    visibility = serializers.FloatField(required=False, default=10.0, min_value=0.0, max_value=50.0)
    traffic_density = serializers.FloatField(required=False, default=35.0, min_value=0.0, max_value=100.0)
    hour = serializers.IntegerField(required=False, default=14, min_value=0, max_value=23)
    day_of_week = serializers.IntegerField(required=False, default=2, min_value=0, max_value=6)
    temperature = serializers.FloatField(required=False, default=72.0)
    humidity = serializers.FloatField(required=False, default=50.0, min_value=0.0, max_value=100.0)
    wind_speed = serializers.FloatField(required=False, default=5.0, min_value=0.0)
    road_surface = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    time_of_day = serializers.CharField(required=False, default=None, allow_blank=True, allow_null=True)
    junction = serializers.IntegerField(required=False, default=0, min_value=0, max_value=1)
    traffic_signal = serializers.IntegerField(required=False, default=0, min_value=0, max_value=1)
    safety_lambda = serializers.FloatField(required=False, default=1.5, min_value=0.0, max_value=10.0)

    def validate(self, attrs):
        # Normalize weather vs weather_condition
        if attrs.get("weather_condition") and not attrs.get("weather"):
            attrs["weather"] = attrs["weather_condition"]
        elif attrs.get("weather") and not attrs.get("weather_condition"):
            attrs["weather_condition"] = attrs["weather"]
        return attrs


class RouteRequestSerializer(serializers.Serializer):
    """Validates origin, destination, and risk trade-off parameters for pathfinding."""
    origin = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2,
        required=True,
        help_text="[latitude, longitude] origin pair"
    )
    destination = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2,
        required=True,
        help_text="[latitude, longitude] destination pair"
    )
    conditions = serializers.DictField(
        required=False,
        default=dict,
        help_text="Current environmental and traffic sensor observations"
    )
    # Support both 'lambda' and 'safety_lambda'
    safety_lambda = serializers.FloatField(required=False, default=1.5, min_value=0.0, max_value=10.0)
    field_lambda = serializers.FloatField(required=False, default=None, source="lambda", min_value=0.0, max_value=10.0)

    def validate(self, attrs):
        # Resolve 'lambda' parameter alias
        if attrs.get("lambda") is not None:
            attrs["safety_lambda"] = attrs["lambda"]

        orig = attrs["origin"]
        dest = attrs["destination"]

        # Basic latitude and longitude sanity bounds
        if not (-90.0 <= orig[0] <= 90.0 and -180.0 <= orig[1] <= 180.0):
            raise serializers.ValidationError("Origin coordinates [lat, lon] are out of valid range.")
        if not (-90.0 <= dest[0] <= 90.0 and -180.0 <= dest[1] <= 180.0):
            raise serializers.ValidationError("Destination coordinates [lat, lon] are out of valid range.")

        # Ensure origin and destination are distinct
        if abs(orig[0] - dest[0]) < 1e-6 and abs(orig[1] - dest[1]) < 1e-6:
            raise serializers.ValidationError("Origin and destination must be distinct coordinates.")

        return attrs


class RulesRequestSerializer(serializers.Serializer):
    """Validates payload for forward-chaining rule evaluation."""
    conditions = serializers.DictField(required=False, default=dict)
    route_stats = serializers.DictField(required=False, default=dict)
    risk_probability = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)


class HealthCheckSerializer(serializers.Serializer):
    """Serializes health check status."""
    status = serializers.CharField()
    project = serializers.CharField()
    course_outcomes = serializers.DictField()
    timestamp = serializers.DateTimeField()


class MetaSerializer(serializers.Serializer):
    """Serializes project metadata, map bounds, and default values."""
    city = serializers.CharField()
    state = serializers.CharField()
    map_center = serializers.ListField(child=serializers.FloatField())
    default_zoom = serializers.IntegerField()
    bounds = serializers.DictField()
    default_sliders = serializers.DictField()
    supported_weather_conditions = serializers.ListField(child=serializers.CharField())
