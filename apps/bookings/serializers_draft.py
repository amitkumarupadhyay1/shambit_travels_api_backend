"""
PHASE 4: Booking Draft Serializers

Protocol Compliance:
- §6: Draft persistence serializers
- Validation before save
- Version control support
"""

from datetime import timedelta

from django.utils import timezone

from packages.models import Package
from rest_framework import serializers

from .models_draft import BookingDraft


class BookingDraftSerializer(serializers.ModelSerializer):
    """Serializer for booking drafts"""

    package_id = serializers.IntegerField(write_only=True)
    package = serializers.SerializerMethodField(read_only=True)
    is_expired = serializers.SerializerMethodField(read_only=True)
    time_remaining = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BookingDraft
        fields = [
            "id",
            "package_id",
            "package",
            "draft_data",
            "created_at",
            "updated_at",
            "expires_at",
            "is_expired",
            "time_remaining",
            "migrated_from_local",
            "version",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "expires_at",
            "is_expired",
            "time_remaining",
            "version",
        ]

    def get_package(self, obj):
        """Return minimal package info"""
        return {
            "id": obj.package.id,
            "name": obj.package.name,
            "slug": obj.package.slug,
        }

    def get_is_expired(self, obj):
        """Check if draft is expired"""
        return obj.is_expired()

    def get_time_remaining(self, obj):
        """Get time remaining in seconds"""
        if obj.is_expired():
            return 0
        delta = obj.expires_at - timezone.now()
        return int(delta.total_seconds())

    def validate_package_id(self, value):
        """Validate package exists"""
        try:
            Package.objects.get(id=value)
        except Package.DoesNotExist:
            raise serializers.ValidationError("Package not found")
        return value

    def validate_draft_data(self, value):
        """Validate draft data structure"""
        required_fields = [
            "packageId",
            "experiences",
            "days",
            "dateRange",
            "travellers",
            "hotelTier",
        ]

        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")

        # Validate travellers
        if not isinstance(value.get("travellers"), list):
            raise serializers.ValidationError("travellers must be a list")

        # Validate experiences
        if not isinstance(value.get("experiences"), list):
            raise serializers.ValidationError("experiences must be a list")

        return value

    def create(self, validated_data):
        """Create draft with user from context"""
        package_id = validated_data.pop("package_id")
        validated_data["package_id"] = package_id
        validated_data["user"] = self.context["request"].user

        # Set expiry to 24 hours from now
        validated_data["expires_at"] = timezone.now() + timedelta(hours=24)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update draft and increment version"""
        validated_data.pop("package_id", None)  # Don't allow package change

        # Increment version for optimistic locking
        instance.version += 1

        # Extend expiry on update
        instance.expires_at = timezone.now() + timedelta(hours=24)

        return super().update(instance, validated_data)


class BookingDraftCreateSerializer(serializers.Serializer):
    """Serializer for creating a draft from localStorage"""

    package_id = serializers.IntegerField()
    draft_data = serializers.JSONField()
    local_storage_key = serializers.CharField(required=False, allow_blank=True)

    def validate_package_id(self, value):
        """Validate package exists"""
        try:
            Package.objects.get(id=value)
        except Package.DoesNotExist:
            raise serializers.ValidationError("Package not found")
        return value

    def validate_draft_data(self, value):
        """Validate draft data structure"""
        required_fields = [
            "packageId",
            "experiences",
            "days",
            "dateRange",
            "travellers",
            "hotelTier",
        ]

        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")

        return value

    def create(self, validated_data):
        """Create draft"""
        user = self.context["request"].user

        draft = BookingDraft.objects.create(
            user=user,
            package_id=validated_data["package_id"],
            draft_data=validated_data["draft_data"],
            migrated_from_local=True,
            local_storage_key=validated_data.get("local_storage_key", ""),
            expires_at=timezone.now() + timedelta(hours=24),
        )

        return draft


class BookingDraftMigrateSerializer(serializers.Serializer):
    """Serializer for migrating localStorage draft to backend"""

    draft_data = serializers.JSONField()

    def validate_draft_data(self, value):
        """Validate draft data structure"""
        if "packageId" not in value:
            raise serializers.ValidationError("packageId is required")

        # Validate package exists
        try:
            Package.objects.get(id=value["packageId"])
        except Package.DoesNotExist:
            raise serializers.ValidationError("Package not found")

        return value

    def create(self, validated_data):
        """Create draft from localStorage data"""
        user = self.context["request"].user
        draft_data = validated_data["draft_data"]

        # Check if user already has a draft for this package
        existing_draft = BookingDraft.objects.filter(
            user=user, package_id=draft_data["packageId"], expires_at__gt=timezone.now()
        ).first()

        if existing_draft:
            # Update existing draft
            existing_draft.draft_data = draft_data
            existing_draft.version += 1
            existing_draft.expires_at = timezone.now() + timedelta(hours=24)
            existing_draft.save()
            return existing_draft

        # Create new draft
        draft = BookingDraft.objects.create(
            user=user,
            package_id=draft_data["packageId"],
            draft_data=draft_data,
            migrated_from_local=True,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        return draft
