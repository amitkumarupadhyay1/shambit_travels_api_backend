import logging
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from ..models import PricingRule

logger = logging.getLogger(__name__)


class PricingService:
    @staticmethod
    def calculate_total(package, experiences, hotel_tier, transport_option):
        """
        Calculates total price based on selected components and active rules.
        Logic is strictly backend-side and deterministic.
        """
        # Get price breakdown for detailed calculation
        breakdown = PricingService.get_price_breakdown(
            package, experiences, hotel_tier, transport_option
        )

        return breakdown["final_total"]

    @staticmethod
    def get_price_breakdown(package, experiences, hotel_tier, transport_option):
        """
        Get detailed price breakdown for transparency
        """
        # 1. Base experiences price
        base_experience_total = (
            sum(Decimal(str(exp.base_price)) for exp in experiences)
            if experiences
            else Decimal("0.00")
        )

        # 2. Transport cost
        transport_cost = transport_option.base_price

        # 3. Subtotal before hotel multiplier
        subtotal_before_hotel = base_experience_total + transport_cost

        # 4. Apply Hotel Multiplier
        subtotal_after_hotel = subtotal_before_hotel * hotel_tier.price_multiplier

        # 5. Apply Pricing Rules
        applicable_rules = PricingService.get_applicable_rules(package)

        total_markup = Decimal("0.00")
        total_discount = Decimal("0.00")
        applied_rules = []

        current_total = subtotal_after_hotel

        for rule in applicable_rules:
            rule_amount = Decimal("0.00")

            if rule.rule_type == "MARKUP":
                if rule.is_percentage:
                    rule_amount = current_total * (rule.value / Decimal("100"))
                else:
                    rule_amount = rule.value
                total_markup += rule_amount
                current_total += rule_amount

            elif rule.rule_type == "DISCOUNT":
                if rule.is_percentage:
                    rule_amount = current_total * (rule.value / Decimal("100"))
                else:
                    rule_amount = rule.value
                total_discount += rule_amount
                current_total -= rule_amount

            applied_rules.append(
                {
                    "name": rule.name,
                    "type": rule.rule_type,
                    "value": str(rule.value),
                    "is_percentage": rule.is_percentage,
                    "amount_applied": str(rule_amount),
                }
            )

        # Ensure minimum price (never negative)
        final_total = max(current_total, Decimal("0.00")).quantize(Decimal("0.01"))

        return {
            "base_experience_total": base_experience_total.quantize(Decimal("0.01")),
            "transport_cost": transport_cost.quantize(Decimal("0.01")),
            "subtotal_before_hotel": subtotal_before_hotel.quantize(Decimal("0.01")),
            "hotel_multiplier": hotel_tier.price_multiplier,
            "subtotal_after_hotel": subtotal_after_hotel.quantize(Decimal("0.01")),
            "total_markup": total_markup.quantize(Decimal("0.01")),
            "total_discount": total_discount.quantize(Decimal("0.01")),
            "final_total": final_total,
            "applied_rules": applied_rules,
        }

    @staticmethod
    def get_applicable_rules(package):
        """
        Get all pricing rules applicable to a package
        """
        cache_key = f"pricing_rules_{package.id if package else 'global'}"
        cached_rules = cache.get(cache_key)

        if cached_rules is not None:
            return cached_rules

        now = timezone.now()
        active_rules = (
            PricingRule.objects.filter(is_active=True, active_from__lte=now)
            .filter(Q(active_to__gte=now) | Q(active_to__isnull=True))
            .filter(Q(target_package=package) | Q(target_package__isnull=True))
            .order_by("active_from")
        )  # Apply rules in chronological order

        # Cache for 5 minutes
        cache.set(cache_key, list(active_rules), 300)

        logger.info(
            f"Applied {len(active_rules)} pricing rules for package {package.slug if package else 'global'}"
        )

        return active_rules

    @staticmethod
    def validate_price_components(package, experiences, hotel_tier, transport_option):
        """
        Validate that all pricing components are valid and belong to the package
        """
        errors = []

        # Check if experiences belong to package
        package_experience_ids = set(package.experiences.values_list("id", flat=True))
        selected_experience_ids = set(exp.id for exp in experiences)

        if not selected_experience_ids.issubset(package_experience_ids):
            invalid_ids = selected_experience_ids - package_experience_ids
            errors.append(f"Invalid experience IDs: {invalid_ids}")

        # Check if hotel tier belongs to package
        if hotel_tier.id not in package.hotel_tiers.values_list("id", flat=True):
            errors.append(
                f"Hotel tier {hotel_tier.id} not available for package {package.slug}"
            )

        # Check if transport option belongs to package
        if transport_option.id not in package.transport_options.values_list(
            "id", flat=True
        ):
            errors.append(
                f"Transport option {transport_option.id} not available for package {package.slug}"
            )

        return errors

    @staticmethod
    def get_price_estimate_range(package):
        """
        Get min/max price estimates for a package
        """
        try:
            # Get cheapest combination
            cheapest_experiences = package.experiences.order_by("base_price")[:1]
            cheapest_hotel = package.hotel_tiers.order_by("price_multiplier").first()
            cheapest_transport = package.transport_options.order_by(
                "base_price"
            ).first()

            min_price = PricingService.calculate_total(
                package, cheapest_experiences, cheapest_hotel, cheapest_transport
            )

            # Get most expensive combination
            most_expensive_experiences = package.experiences.order_by("-base_price")[
                :3
            ]  # Assume max 3 experiences
            most_expensive_hotel = package.hotel_tiers.order_by(
                "-price_multiplier"
            ).first()
            most_expensive_transport = package.transport_options.order_by(
                "-base_price"
            ).first()

            max_price = PricingService.calculate_total(
                package,
                most_expensive_experiences,
                most_expensive_hotel,
                most_expensive_transport,
            )

            return {"min_price": min_price, "max_price": max_price, "currency": "INR"}

        except Exception as e:
            logger.error(
                f"Error calculating price range for package {package.slug}: {str(e)}"
            )
            return {
                "min_price": Decimal("0.00"),
                "max_price": Decimal("0.00"),
                "currency": "INR",
            }

    @staticmethod
    def clear_pricing_cache(package_id=None):
        """
        Clear pricing cache for a specific package or all packages
        """
        if package_id:
            cache_key = f"pricing_rules_{package_id}"
            cache.delete(cache_key)
        else:
            # Clear all pricing caches (this is a simple approach)
            cache.clear()

        logger.info(f"Cleared pricing cache for package {package_id or 'all'}")
