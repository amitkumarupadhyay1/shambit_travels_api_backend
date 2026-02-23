import logging
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from ..models import PricingRule

logger = logging.getLogger(__name__)


class PricingService:
    # PHASE 3: Age threshold now configurable via PricingConfiguration
    # This is a fallback default if config is not available
    CHARGEABLE_AGE_THRESHOLD = 5

    @staticmethod
    def get_chargeable_age_threshold():
        """
        Get the chargeable age threshold from configuration.
        Falls back to default if configuration is not available.
        """
        try:
            from ..models import PricingConfiguration

            config = PricingConfiguration.get_config()
            return config.chargeable_age_threshold
        except Exception as e:
            logger.warning(
                f"Failed to get age threshold from config: {e}. Using default."
            )
            return PricingService.CHARGEABLE_AGE_THRESHOLD

    @staticmethod
    def calculate_hotel_cost(
        hotel_tier, start_date, end_date, num_rooms=1, use_legacy=False
    ):
        """
        PHASE 1: Calculate hotel cost based on date range and number of rooms.

        Args:
            hotel_tier: HotelTier instance
            start_date: datetime.date - Trip start date
            end_date: datetime.date - Trip end date
            num_rooms: int - Number of rooms required
            use_legacy: bool - If True, use legacy multiplier calculation

        Returns:
            dict: {
                'total_cost': Decimal,
                'cost_per_night': Decimal,
                'num_nights': int,
                'breakdown': list of {date, is_weekend, price_per_night}
            }
        """
        from datetime import timedelta

        # Check if hotel tier has new pricing model
        if not use_legacy and hotel_tier.base_price_per_night:
            total_cost = Decimal("0.00")
            breakdown = []
            current_date = start_date

            while current_date < end_date:
                # Check if weekend (Friday=4, Saturday=5, Sunday=6)
                is_weekend = current_date.weekday() >= 4

                # Calculate price for this night
                base_price = hotel_tier.base_price_per_night
                if is_weekend:
                    price_per_night = base_price * hotel_tier.weekend_multiplier
                else:
                    price_per_night = base_price

                # Multiply by number of rooms
                night_cost = price_per_night * num_rooms
                total_cost += night_cost

                breakdown.append(
                    {
                        "date": current_date,
                        "is_weekend": is_weekend,
                        "price_per_night": price_per_night,
                        "num_rooms": num_rooms,
                        "night_cost": night_cost,
                    }
                )

                current_date += timedelta(days=1)

            num_nights = (end_date - start_date).days
            cost_per_night = total_cost / num_nights if num_nights > 0 else total_cost

            return {
                "total_cost": total_cost.quantize(Decimal("0.01")),
                "cost_per_night": cost_per_night.quantize(Decimal("0.01")),
                "num_nights": num_nights,
                "num_rooms": num_rooms,
                "breakdown": breakdown,
                "uses_new_pricing": True,
            }
        else:
            # Legacy fallback: return None to indicate legacy pricing should be used
            return {
                "total_cost": None,
                "cost_per_night": None,
                "num_nights": (
                    (end_date - start_date).days if start_date and end_date else 1
                ),
                "num_rooms": num_rooms,
                "breakdown": [],
                "uses_new_pricing": False,
            }

    @staticmethod
    def calculate_total(
        package,
        experiences,
        hotel_tier,
        transport_option,
        travelers=None,
        start_date=None,
        end_date=None,
        num_rooms=1,
        num_travelers=1,
    ):
        """
        Calculates total price based on selected components and active rules.
        Logic is strictly backend-side and deterministic.

        PHASE 1 UPDATE: Now supports date-based hotel pricing.

        Args:
            package: Package instance
            experiences: QuerySet or list of Experience instances
            hotel_tier: HotelTier instance
            transport_option: TransportOption instance
            travelers: Optional list of traveler dicts with 'age' field for age-based pricing
            start_date: Optional datetime.date for hotel pricing
            end_date: Optional datetime.date for hotel pricing
            num_rooms: Number of rooms required (default: 1)

        Returns:
            Decimal: Total price (per-person if travelers not provided, total if provided)
        """
        # Get price breakdown for detailed calculation
        breakdown = PricingService.get_price_breakdown(
            package,
            experiences,
            hotel_tier,
            transport_option,
            travelers,
            start_date,
            end_date,
            num_rooms,
            num_travelers=num_travelers,
        )

        return breakdown["final_total"]

    @staticmethod
    def get_price_breakdown(
        package,
        experiences,
        hotel_tier,
        transport_option,
        travelers=None,
        start_date=None,
        end_date=None,
        num_rooms=1,
        num_travelers=1,  # PHASE 2: Simple traveler count for experience pricing
    ):
        """
        Get detailed price breakdown for transparency.

        PHASE 1 UPDATE: Now includes date-based hotel pricing.
        PHASE 2 UPDATE: Now includes num_travelers for experience pricing.

        Args:
            package: Package instance
            experiences: QuerySet or list of Experience instances
            hotel_tier: HotelTier instance
            transport_option: TransportOption instance
            travelers: Optional list of traveler dicts with 'age' field (for age-based pricing)
            start_date: Optional datetime.date for hotel pricing
            end_date: Optional datetime.date for hotel pricing
            num_rooms: Number of rooms required (default: 1)
            num_travelers: Number of travelers for experience pricing (default: 1)

        Returns:
            dict: Detailed price breakdown including age-based calculations and hotel costs
        """
        # 1. Base experiences price (PHASE 3: Use chargeable travelers for age-based pricing)
        base_experience_per_person = (
            sum(Decimal(str(exp.base_price)) for exp in experiences)
            if experiences
            else Decimal("0.00")
        )

        # PHASE 3: Calculate chargeable travelers first for accurate pricing
        age_threshold = PricingService.get_chargeable_age_threshold()
        chargeable_travelers = num_travelers  # Default to all travelers
        total_travelers = num_travelers

        if travelers:
            total_travelers = len(travelers)
            chargeable_travelers = sum(
                1 for t in travelers if t.get("age", 0) >= age_threshold
            )

        # Use chargeable travelers for experience cost calculation
        base_experience_total = base_experience_per_person * Decimal(
            str(chargeable_travelers)
        )

        # 2. Transport cost (optional - may be selected later)
        transport_cost = (
            transport_option.base_price if transport_option else Decimal("0.00")
        )

        # 3. Hotel cost calculation (PHASE 1: New logic)
        hotel_cost_info = None
        if hotel_tier.base_price_per_night:
            # Use new date-based pricing if base_price_per_night is set
            if start_date and end_date:
                # Use provided dates
                hotel_cost_info = PricingService.calculate_hotel_cost(
                    hotel_tier, start_date, end_date, num_rooms
                )
                hotel_cost = hotel_cost_info["total_cost"] or Decimal("0.00")
            else:
                # Fallback: Use 1 night with base price (better than multiplier)
                hotel_cost = hotel_tier.base_price_per_night * num_rooms
                hotel_cost_info = {
                    "uses_new_pricing": True,
                    "total_cost": hotel_cost,
                    "cost_per_night": hotel_tier.base_price_per_night,
                    "num_nights": 1,
                    "num_rooms": num_rooms,
                    "breakdown": [],
                }
        else:
            # Legacy: Use multiplier-based pricing only if base_price_per_night not set
            hotel_cost = Decimal("0.00")
            hotel_cost_info = {
                "uses_new_pricing": False,
                "total_cost": None,
                "cost_per_night": None,
                "num_nights": 1,
                "num_rooms": num_rooms,
                "breakdown": [],
            }

        # 4. Subtotal calculation
        if hotel_cost_info["uses_new_pricing"]:
            # New model: Add hotel cost directly
            subtotal_before_rules = base_experience_total + transport_cost + hotel_cost
            # For display: subtotal includes all components before taxes
            subtotal_before_hotel = base_experience_total + transport_cost
            subtotal_after_hotel = base_experience_total + transport_cost + hotel_cost
        else:
            # Legacy model: Apply multiplier
            subtotal_before_hotel = base_experience_total + transport_cost
            subtotal_after_hotel = subtotal_before_hotel * hotel_tier.price_multiplier
            subtotal_before_rules = subtotal_after_hotel

        # 5. Apply Pricing Rules
        applicable_rules = PricingService.get_applicable_rules(package)

        total_markup = Decimal("0.00")
        total_discount = Decimal("0.00")
        applied_rules = []

        current_total = subtotal_before_rules

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

        # Age-based pricing already applied in base calculation
        # final_total is the total for all chargeable travelers
        total_amount = final_total
        if chargeable_travelers > 0:
            per_person_price = (
                total_amount / Decimal(str(chargeable_travelers))
            ).quantize(Decimal("0.01"))
        else:
            per_person_price = total_amount

        return {
            "base_experience_total": base_experience_total.quantize(Decimal("0.01")),
            "transport_cost": transport_cost.quantize(Decimal("0.01")),
            "subtotal_before_hotel": subtotal_before_hotel.quantize(Decimal("0.01")),
            "hotel_multiplier": hotel_tier.price_multiplier,
            "subtotal_after_hotel": subtotal_after_hotel.quantize(Decimal("0.01")),
            # PHASE 1: New hotel cost fields
            "hotel_cost": (
                hotel_cost.quantize(Decimal("0.01"))
                if hotel_cost_info["uses_new_pricing"]
                else None
            ),
            "hotel_cost_per_night": (
                hotel_cost_info["cost_per_night"].quantize(Decimal("0.01"))
                if hotel_cost_info["cost_per_night"]
                else None
            ),
            "hotel_num_nights": hotel_cost_info["num_nights"],
            "hotel_num_rooms": hotel_cost_info["num_rooms"],
            "hotel_breakdown": hotel_cost_info["breakdown"],
            "uses_new_hotel_pricing": hotel_cost_info["uses_new_pricing"],
            # End PHASE 1 additions
            # PHASE 2: Traveler count
            "num_travelers": total_travelers if travelers else num_travelers,
            "base_experience_per_person": base_experience_per_person.quantize(
                Decimal("0.01")
            ),
            # End PHASE 2 additions
            "total_markup": total_markup.quantize(Decimal("0.01")),
            "total_discount": total_discount.quantize(Decimal("0.01")),
            "final_total": final_total,  # Total price for all chargeable travelers
            "applied_rules": applied_rules,
            # Age-based pricing fields
            "chargeable_travelers": chargeable_travelers,
            "total_travelers": total_travelers if travelers else num_travelers,
            "total_amount": total_amount,  # Same as final_total (already includes chargeable travelers)
            "per_person_price": per_person_price,
            "chargeable_age_threshold": age_threshold,
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
            cheapest_hotel = (
                package.hotel_tiers.filter(base_price_per_night__isnull=False)
                .order_by("base_price_per_night")
                .first()
                or package.hotel_tiers.order_by("price_multiplier").first()
            )
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
            most_expensive_hotel = (
                package.hotel_tiers.filter(base_price_per_night__isnull=False)
                .order_by("-base_price_per_night")
                .first()
                or package.hotel_tiers.order_by("-price_multiplier").first()
            )
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
