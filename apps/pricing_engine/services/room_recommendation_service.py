"""
PHASE 3: Intelligent Room Recommendation Service

Provides smart room allocation recommendations based on:
- Traveler composition (age, gender)
- Family structures
- Budget optimization
- Privacy preferences
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RoomRecommendationService:
    """
    Intelligent room recommendation engine that analyzes traveler composition
    and suggests optimal room allocation strategies.
    """

    # Age thresholds for room allocation logic
    CHILD_AGE_THRESHOLD = 10  # Children under 10 can share with parents
    TEEN_AGE_THRESHOLD = 18  # Teens may need separate rooms
    ADULT_AGE_THRESHOLD = 18  # Adults

    @staticmethod
    def analyze_traveler_composition(travelers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the composition of travelers to understand group dynamics.

        Args:
            travelers: List of dicts with 'name', 'age', 'gender'

        Returns:
            Dict with composition analysis
        """
        if not travelers:
            return {
                "total": 0,
                "adults": 0,
                "teens": 0,
                "children": 0,
                "males": 0,
                "females": 0,
                "unspecified_gender": 0,
                "is_family": False,
                "is_mixed_gender": False,
                "has_children": False,
            }

        adults = sum(
            1
            for t in travelers
            if t.get("age", 0) >= RoomRecommendationService.ADULT_AGE_THRESHOLD
        )
        teens = sum(
            1
            for t in travelers
            if RoomRecommendationService.CHILD_AGE_THRESHOLD
            <= t.get("age", 0)
            < RoomRecommendationService.ADULT_AGE_THRESHOLD
        )
        children = sum(
            1
            for t in travelers
            if t.get("age", 0) < RoomRecommendationService.CHILD_AGE_THRESHOLD
        )

        males = sum(
            1 for t in travelers if t.get("gender", "").upper() in ["M", "MALE"]
        )
        females = sum(
            1 for t in travelers if t.get("gender", "").upper() in ["F", "FEMALE"]
        )
        unspecified = len(travelers) - males - females

        # Heuristics for family detection
        is_family = (
            children > 0
            and adults >= 1
            and adults <= 2  # Has children with 1-2 adults
            or (
                adults == 2 and teens > 0 and children > 0
            )  # Parents with teens and children
        )

        is_mixed_gender = males > 0 and females > 0

        return {
            "total": len(travelers),
            "adults": adults,
            "teens": teens,
            "children": children,
            "males": males,
            "females": females,
            "unspecified_gender": unspecified,
            "is_family": is_family,
            "is_mixed_gender": is_mixed_gender,
            "has_children": children > 0,
        }

    @staticmethod
    def recommend_rooms(
        travelers: List[Dict[str, Any]],
        hotel_tier,
        base_price_per_night: Optional[Decimal] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent room recommendations based on traveler composition.

        Args:
            travelers: List of traveler dicts with 'name', 'age', 'gender'
            hotel_tier: HotelTier instance
            base_price_per_night: Optional override for price calculation

        Returns:
            List of recommendation dicts, sorted by priority
        """
        if not travelers:
            return []

        composition = RoomRecommendationService.analyze_traveler_composition(travelers)
        max_occupancy = hotel_tier.max_occupancy_per_room
        num_travelers = composition["total"]

        # Use provided price or get from hotel tier
        if base_price_per_night is None:
            base_price_per_night = hotel_tier.base_price_per_night or Decimal("0")

        recommendations = []

        # Recommendation 1: Family Room (if applicable)
        if composition["is_family"] and composition["children"] > 0:
            # Check if family room is available
            family_room_price = (
                hotel_tier.room_types.get("family") if hotel_tier.room_types else None
            )

            if family_room_price and num_travelers <= 4:
                recommendations.append(
                    {
                        "num_rooms": 1,
                        "type": "family",
                        "priority": 1,
                        "reasoning": f"Family room for {num_travelers} people (parents with children under {RoomRecommendationService.CHILD_AGE_THRESHOLD})",
                        "description": "Single family room - Most convenient for families with young children",
                        "cost_per_night": Decimal(str(family_room_price)),
                        "allocation": [
                            {
                                "room_number": 1,
                                "room_type": "family",
                                "occupants": list(range(num_travelers)),
                                "notes": "All family members together",
                            }
                        ],
                        "pros": [
                            "Children stay with parents",
                            "Most convenient for supervision",
                            "Often more economical than multiple rooms",
                        ],
                        "cons": [
                            "Less privacy for adults",
                            "May be crowded if children are older",
                        ],
                    }
                )

            # Alternative: 2 rooms for family
            if num_travelers > 4 or composition["teens"] > 0:
                num_rooms = 2
                recommendations.append(
                    {
                        "num_rooms": num_rooms,
                        "type": "family_split",
                        "priority": 2,
                        "reasoning": f"2 rooms for family with {composition['teens']} teen(s) or {num_travelers} total members",
                        "description": "Two rooms - Parents in one, children/teens in another",
                        "cost_per_night": base_price_per_night * num_rooms,
                        "allocation": [
                            {
                                "room_number": 1,
                                "room_type": "double",
                                "occupants": list(range(min(2, composition["adults"]))),
                                "notes": "Parents/Adults",
                            },
                            {
                                "room_number": 2,
                                "room_type": "double",
                                "occupants": list(
                                    range(composition["adults"], num_travelers)
                                ),
                                "notes": "Children/Teens",
                            },
                        ],
                        "pros": [
                            "More privacy for adults",
                            "Better for older children/teens",
                            "Comfortable sleeping arrangements",
                        ],
                        "cons": [
                            "Higher cost than single family room",
                            "Requires supervision for young children",
                        ],
                    }
                )

        # Recommendation 2: Gender-Separated Rooms (for mixed gender groups)
        if (
            composition["is_mixed_gender"]
            and not composition["is_family"]
            and composition["adults"] >= 3
        ):
            male_rooms = max(
                1, (composition["males"] + max_occupancy - 1) // max_occupancy
            )
            female_rooms = max(
                1, (composition["females"] + max_occupancy - 1) // max_occupancy
            )
            total_rooms = male_rooms + female_rooms

            # Build allocation
            allocation = []
            male_indices = [
                i
                for i, t in enumerate(travelers)
                if t.get("gender", "").upper() in ["M", "MALE"]
            ]
            female_indices = [
                i
                for i, t in enumerate(travelers)
                if t.get("gender", "").upper() in ["F", "FEMALE"]
            ]

            # Allocate males
            for room_num in range(male_rooms):
                start_idx = room_num * max_occupancy
                end_idx = min(start_idx + max_occupancy, len(male_indices))
                allocation.append(
                    {
                        "room_number": room_num + 1,
                        "room_type": "double",
                        "occupants": male_indices[start_idx:end_idx],
                        "notes": f"Male travelers ({end_idx - start_idx} people)",
                    }
                )

            # Allocate females
            for room_num in range(female_rooms):
                start_idx = room_num * max_occupancy
                end_idx = min(start_idx + max_occupancy, len(female_indices))
                allocation.append(
                    {
                        "room_number": male_rooms + room_num + 1,
                        "room_type": "double",
                        "occupants": female_indices[start_idx:end_idx],
                        "notes": f"Female travelers ({end_idx - start_idx} people)",
                    }
                )

            recommendations.append(
                {
                    "num_rooms": total_rooms,
                    "type": "gender_separated",
                    "priority": 1 if not composition["is_family"] else 3,
                    "reasoning": f"{male_rooms} room(s) for {composition['males']} male(s), {female_rooms} room(s) for {composition['females']} female(s)",
                    "description": "Gender-separated rooms - Privacy and comfort for all",
                    "cost_per_night": base_price_per_night * total_rooms,
                    "allocation": allocation,
                    "pros": [
                        "Privacy and comfort for all travelers",
                        "Culturally appropriate for many groups",
                        "Reduces awkwardness in mixed groups",
                    ],
                    "cons": [
                        "Higher cost than shared rooms",
                        "May require more coordination",
                    ],
                }
            )

        # Recommendation 3: Budget Option (Maximum Occupancy)
        min_rooms = max(1, (num_travelers + max_occupancy - 1) // max_occupancy)

        # Build allocation for budget option
        budget_allocation = []
        for room_num in range(min_rooms):
            start_idx = room_num * max_occupancy
            end_idx = min(start_idx + max_occupancy, num_travelers)
            occupants_count = end_idx - start_idx
            budget_allocation.append(
                {
                    "room_number": room_num + 1,
                    "room_type": "double",
                    "occupants": list(range(start_idx, end_idx)),
                    "notes": f"{occupants_count} people per room",
                }
            )

        recommendations.append(
            {
                "num_rooms": min_rooms,
                "type": "budget",
                "priority": 4,
                "reasoning": f"{num_travelers} travelers, {max_occupancy} per room (maximum occupancy)",
                "description": f"{min_rooms} room(s) - Most economical option",
                "cost_per_night": base_price_per_night * min_rooms,
                "allocation": budget_allocation,
                "pros": [
                    "Most economical option",
                    "Minimizes accommodation costs",
                    "Good for budget-conscious travelers",
                ],
                "cons": [
                    "Less privacy",
                    "May be crowded",
                    "Not suitable for all group types",
                ],
            }
        )

        # Recommendation 4: Comfort Option (More rooms for privacy)
        if num_travelers >= 3:
            comfort_rooms = min(
                num_travelers, max(min_rooms + 1, (num_travelers + 1) // 2)
            )

            # Build allocation for comfort option
            comfort_allocation = []
            travelers_per_room = num_travelers / comfort_rooms
            for room_num in range(comfort_rooms):
                start_idx = int(room_num * travelers_per_room)
                end_idx = (
                    int((room_num + 1) * travelers_per_room)
                    if room_num < comfort_rooms - 1
                    else num_travelers
                )
                occupants_count = end_idx - start_idx
                comfort_allocation.append(
                    {
                        "room_number": room_num + 1,
                        "room_type": "double",
                        "occupants": list(range(start_idx, end_idx)),
                        "notes": f"{occupants_count} people per room",
                    }
                )

            recommendations.append(
                {
                    "num_rooms": comfort_rooms,
                    "type": "comfort",
                    "priority": 3,
                    "reasoning": f"{comfort_rooms} rooms for {num_travelers} travelers (balanced privacy and cost)",
                    "description": f"{comfort_rooms} room(s) - Balanced comfort and cost",
                    "cost_per_night": base_price_per_night * comfort_rooms,
                    "allocation": comfort_allocation,
                    "pros": [
                        "Better privacy than budget option",
                        "More comfortable sleeping arrangements",
                        "Good balance of cost and comfort",
                    ],
                    "cons": [
                        "More expensive than budget option",
                        "Still requires some room sharing",
                    ],
                }
            )

        # Recommendation 5: Maximum Privacy (1 person per room)
        if num_travelers >= 2 and num_travelers <= 5:
            privacy_allocation = [
                {
                    "room_number": i + 1,
                    "room_type": (
                        "single"
                        if hotel_tier.room_types and "single" in hotel_tier.room_types
                        else "double"
                    ),
                    "occupants": [i],
                    "notes": "Private room",
                }
                for i in range(num_travelers)
            ]

            # Calculate cost (use single room price if available)
            single_price = (
                Decimal(str(hotel_tier.room_types.get("single", base_price_per_night)))
                if hotel_tier.room_types
                else base_price_per_night
            )

            recommendations.append(
                {
                    "num_rooms": num_travelers,
                    "type": "privacy",
                    "priority": 5,
                    "reasoning": "1 room per person for maximum privacy",
                    "description": f"{num_travelers} room(s) - Maximum privacy (1 per room)",
                    "cost_per_night": single_price * num_travelers,
                    "allocation": privacy_allocation,
                    "pros": [
                        "Maximum privacy for all travelers",
                        "No room sharing required",
                        "Most comfortable option",
                    ],
                    "cons": [
                        "Most expensive option",
                        "May not be necessary for all groups",
                    ],
                }
            )

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])

        # Add recommendation rank
        for idx, rec in enumerate(recommendations):
            rec["rank"] = idx + 1
            rec["is_recommended"] = idx == 0

        logger.info(
            f"Generated {len(recommendations)} room recommendations for {num_travelers} travelers "
            f"(composition: {composition})"
        )

        return recommendations

    @staticmethod
    def get_recommended_allocation(
        travelers: List[Dict[str, Any]], hotel_tier, preference: str = "auto"
    ) -> Dict[str, Any]:
        """
        Get the single best room allocation based on preference.

        Args:
            travelers: List of traveler dicts
            hotel_tier: HotelTier instance
            preference: 'auto', 'budget', 'comfort', 'privacy', 'family', 'gender_separated'

        Returns:
            Single recommendation dict
        """
        recommendations = RoomRecommendationService.recommend_rooms(
            travelers, hotel_tier
        )

        if not recommendations:
            return {
                "num_rooms": 1,
                "type": "default",
                "reasoning": "Default allocation",
                "cost_per_night": hotel_tier.base_price_per_night or Decimal("0"),
                "allocation": [],
            }

        # If auto, return the top priority recommendation
        if preference == "auto":
            return recommendations[0]

        # Find recommendation matching preference
        for rec in recommendations:
            if rec["type"] == preference:
                return rec

        # Fallback to first recommendation
        return recommendations[0]
