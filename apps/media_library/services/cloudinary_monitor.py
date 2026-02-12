"""
Cloudinary Usage Monitoring Service
Tracks usage against free tier limits and provides alerts
"""

import os
from datetime import datetime
from typing import Any, Dict, List

import cloudinary
import cloudinary.api


class CloudinaryMonitor:
    """
    Monitor Cloudinary usage and provide alerts for free tier limits

    Free Tier Limits:
    - Storage: 25 GB
    - Bandwidth: 25 GB/month
    - Transformations: 25,000/month
    - Credits: 25 credits/month
    """

    # Free tier limits
    STORAGE_LIMIT_GB = 25
    BANDWIDTH_LIMIT_GB = 25
    TRANSFORMATIONS_LIMIT = 25000
    CREDITS_LIMIT = 25

    # Alert thresholds (percentage)
    WARNING_THRESHOLD = 80  # 80% usage
    CRITICAL_THRESHOLD = 95  # 95% usage

    def __init__(self):
        """Initialize Cloudinary monitor"""
        self.is_enabled = os.environ.get("USE_CLOUDINARY") == "True"

        if not self.is_enabled:
            raise ValueError("Cloudinary is not enabled. Set USE_CLOUDINARY=True")

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current Cloudinary usage statistics

        Returns:
            dict: Usage statistics with percentages and alerts
        """
        try:
            # Get usage from Cloudinary API
            usage = cloudinary.api.usage()

            # Calculate storage usage
            storage_used_bytes = usage.get("storage", {}).get("usage", 0)
            storage_used_gb = storage_used_bytes / (1024**3)
            storage_percentage = (storage_used_gb / self.STORAGE_LIMIT_GB) * 100

            # Calculate bandwidth usage
            bandwidth_used_bytes = usage.get("bandwidth", {}).get("usage", 0)
            bandwidth_used_gb = bandwidth_used_bytes / (1024**3)
            bandwidth_percentage = (bandwidth_used_gb / self.BANDWIDTH_LIMIT_GB) * 100

            # Calculate transformations usage
            transformations_used = usage.get("transformations", {}).get("usage", 0)
            transformations_percentage = (
                transformations_used / self.TRANSFORMATIONS_LIMIT
            ) * 100

            # Calculate credits usage
            credits_used = usage.get("credits", {}).get("usage", 0)
            credits_percentage = (credits_used / self.CREDITS_LIMIT) * 100

            # Get resource counts
            resources = usage.get("resources", 0)

            # Build response
            stats = {
                "storage": {
                    "used_gb": round(storage_used_gb, 2),
                    "limit_gb": self.STORAGE_LIMIT_GB,
                    "used_bytes": storage_used_bytes,
                    "percentage": round(storage_percentage, 2),
                    "status": self._get_status(storage_percentage),
                    "alert": self._get_alert_message("storage", storage_percentage),
                },
                "bandwidth": {
                    "used_gb": round(bandwidth_used_gb, 2),
                    "limit_gb": self.BANDWIDTH_LIMIT_GB,
                    "used_bytes": bandwidth_used_bytes,
                    "percentage": round(bandwidth_percentage, 2),
                    "status": self._get_status(bandwidth_percentage),
                    "alert": self._get_alert_message("bandwidth", bandwidth_percentage),
                },
                "transformations": {
                    "used": transformations_used,
                    "limit": self.TRANSFORMATIONS_LIMIT,
                    "percentage": round(transformations_percentage, 2),
                    "status": self._get_status(transformations_percentage),
                    "alert": self._get_alert_message(
                        "transformations", transformations_percentage
                    ),
                },
                "credits": {
                    "used": credits_used,
                    "limit": self.CREDITS_LIMIT,
                    "percentage": round(credits_percentage, 2),
                    "status": self._get_status(credits_percentage),
                    "alert": self._get_alert_message("credits", credits_percentage),
                },
                "resources": {
                    "count": resources,
                },
                "overall_status": self._get_overall_status(
                    [
                        storage_percentage,
                        bandwidth_percentage,
                        transformations_percentage,
                        credits_percentage,
                    ]
                ),
                "timestamp": datetime.now().isoformat(),
            }

            return stats

        except Exception as e:
            return {
                "error": str(e),
                "message": "Failed to fetch Cloudinary usage statistics",
                "timestamp": datetime.now().isoformat(),
            }

    def _get_status(self, percentage: float) -> str:
        """
        Get status based on usage percentage

        Args:
            percentage: Usage percentage

        Returns:
            str: Status ('ok', 'warning', 'critical')
        """
        if percentage >= self.CRITICAL_THRESHOLD:
            return "critical"
        elif percentage >= self.WARNING_THRESHOLD:
            return "warning"
        else:
            return "ok"

    def _get_alert_message(self, resource_type: str, percentage: float) -> str | None:
        """
        Get alert message if usage is high

        Args:
            resource_type: Type of resource (storage, bandwidth, etc.)
            percentage: Usage percentage

        Returns:
            str or None: Alert message if applicable
        """
        if percentage >= self.CRITICAL_THRESHOLD:
            return f"CRITICAL: {resource_type.capitalize()} usage is at {percentage:.1f}%! Approaching limit."
        elif percentage >= self.WARNING_THRESHOLD:
            return f"WARNING: {resource_type.capitalize()} usage is at {percentage:.1f}%. Consider cleanup."
        return None

    def _get_overall_status(self, percentages: List[float]) -> str:
        """
        Get overall status based on all usage percentages

        Args:
            percentages: List of usage percentages

        Returns:
            str: Overall status
        """
        max_percentage = max(percentages)

        if max_percentage >= self.CRITICAL_THRESHOLD:
            return "critical"
        elif max_percentage >= self.WARNING_THRESHOLD:
            return "warning"
        else:
            return "ok"

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all active alerts

        Returns:
            list: List of alert dictionaries
        """
        stats = self.get_usage_stats()

        if "error" in stats:
            return [
                {
                    "level": "error",
                    "message": stats["message"],
                    "timestamp": stats["timestamp"],
                }
            ]

        alerts = []

        # Check each resource type
        for resource_type in ["storage", "bandwidth", "transformations", "credits"]:
            resource_stats = stats.get(resource_type, {})
            alert_message = resource_stats.get("alert")

            if alert_message:
                alerts.append(
                    {
                        "level": resource_stats["status"],
                        "resource": resource_type,
                        "message": alert_message,
                        "percentage": resource_stats["percentage"],
                        "timestamp": stats["timestamp"],
                    }
                )

        return alerts

    def should_cleanup(self) -> bool:
        """
        Check if cleanup is recommended based on usage

        Returns:
            bool: True if cleanup is recommended
        """
        stats = self.get_usage_stats()

        if "error" in stats:
            return False

        # Recommend cleanup if storage or bandwidth is above warning threshold
        storage_percentage = stats["storage"]["percentage"]
        bandwidth_percentage = stats["bandwidth"]["percentage"]

        return (
            storage_percentage >= self.WARNING_THRESHOLD
            or bandwidth_percentage >= self.WARNING_THRESHOLD
        )

    def get_recommendations(self) -> List[str]:
        """
        Get recommendations based on current usage

        Returns:
            list: List of recommendation strings
        """
        stats = self.get_usage_stats()

        if "error" in stats:
            return ["Unable to fetch usage statistics. Check Cloudinary connection."]

        recommendations = []

        # Storage recommendations
        storage_percentage = stats["storage"]["percentage"]
        if storage_percentage >= self.CRITICAL_THRESHOLD:
            recommendations.append(
                "🔴 URGENT: Delete unused media files immediately to avoid service disruption."
            )
        elif storage_percentage >= self.WARNING_THRESHOLD:
            recommendations.append(
                "⚠️ Run cleanup command to remove orphaned files: python manage.py cleanup_media --orphaned"
            )

        # Bandwidth recommendations
        bandwidth_percentage = stats["bandwidth"]["percentage"]
        if bandwidth_percentage >= self.CRITICAL_THRESHOLD:
            recommendations.append(
                "🔴 URGENT: Bandwidth limit almost reached. Optimize images and enable caching."
            )
        elif bandwidth_percentage >= self.WARNING_THRESHOLD:
            recommendations.append(
                "⚠️ Consider enabling CDN caching and using smaller image sizes."
            )

        # Transformations recommendations
        transformations_percentage = stats["transformations"]["percentage"]
        if transformations_percentage >= self.CRITICAL_THRESHOLD:
            recommendations.append(
                "🔴 URGENT: Transformation limit almost reached. Cache transformed images."
            )
        elif transformations_percentage >= self.WARNING_THRESHOLD:
            recommendations.append(
                "⚠️ Reduce on-the-fly transformations. Pre-generate common sizes."
            )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "✅ Usage is healthy. Continue monitoring regularly."
            )

        return recommendations

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of usage with alerts and recommendations

        Returns:
            dict: Complete summary
        """
        stats = self.get_usage_stats()
        alerts = self.get_alerts()
        recommendations = self.get_recommendations()

        return {
            "stats": stats,
            "alerts": alerts,
            "recommendations": recommendations,
            "should_cleanup": self.should_cleanup(),
            "overall_status": stats.get("overall_status", "unknown"),
        }
