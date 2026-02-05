from django.core.management.base import BaseCommand
from django.utils.text import slugify

from cities.models import City, Highlight, TravelTip


class Command(BaseCommand):
    help = "Seed the database with sample cities for ShamBit"

    def handle(self, *args, **options):
        self.stdout.write("🕉️  Seeding cities for ShamBit...")

        cities_data = [
            {
                "name": "Ayodhya",
                "description": "The birthplace of Lord Rama, Ayodhya is one of the seven sacred cities in Hinduism. Experience divine spirituality at the magnificent Ram Mandir and explore ancient temples along the sacred Sarayu River.",
                "meta_title": "Ayodhya Travel Guide - Sacred City of Lord Rama",
                "meta_description": "Discover Ayodhya, the birthplace of Lord Rama. Visit Ram Mandir, explore ancient temples, and experience divine spirituality in this sacred city.",
                "highlights": [
                    {
                        "title": "Ram Mandir",
                        "description": "The magnificent temple dedicated to Lord Rama",
                        "icon": "temple",
                    },
                    {
                        "title": "Sarayu River",
                        "description": "Sacred river for holy baths and prayers",
                        "icon": "waves",
                    },
                    {
                        "title": "Hanuman Garhi",
                        "description": "Ancient temple of Lord Hanuman",
                        "icon": "mountain",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Best Time to Visit",
                        "content": "October to March for pleasant weather and comfortable temple visits.",
                    },
                    {
                        "title": "Dress Code",
                        "content": "Modest clothing required for temple visits. Remove shoes before entering temples.",
                    },
                    {
                        "title": "Local Transport",
                        "content": "Auto-rickshaws and cycle-rickshaws are the best way to navigate the city.",
                    },
                ],
            },
            {
                "name": "Varanasi",
                "description": "One of the world's oldest continuously inhabited cities, Varanasi is the spiritual capital of India. Witness the mesmerizing Ganga Aarti and experience the eternal cycle of life and death on the sacred ghats.",
                "meta_title": "Varanasi Travel Guide - Spiritual Capital of India",
                "meta_description": "Experience Varanasi, the spiritual capital of India. Witness Ganga Aarti, explore ancient ghats, and immerse in the city's divine energy.",
                "highlights": [
                    {
                        "title": "Dashashwamedh Ghat",
                        "description": "Main ghat for the famous Ganga Aarti ceremony",
                        "icon": "flame",
                    },
                    {
                        "title": "Kashi Vishwanath Temple",
                        "description": "One of the twelve Jyotirlingas of Lord Shiva",
                        "icon": "temple",
                    },
                    {
                        "title": "Boat Ride on Ganges",
                        "description": "Sunrise boat ride along the sacred river",
                        "icon": "boat",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Ganga Aarti Timing",
                        "content": "Evening Aarti starts at 7 PM. Arrive early to get a good spot.",
                    },
                    {
                        "title": "Boat Rides",
                        "content": "Early morning boat rides offer the best views and peaceful atmosphere.",
                    },
                    {
                        "title": "Street Food",
                        "content": "Try famous Banarasi paan, lassi, and kachori from local vendors.",
                    },
                ],
            },
            {
                "name": "Rishikesh",
                "description": 'Known as the "Yoga Capital of the World", Rishikesh offers spiritual awakening amidst the Himalayan foothills. Practice yoga, meditation, and experience the divine energy of the holy Ganges.',
                "meta_title": "Rishikesh Travel Guide - Yoga Capital of the World",
                "meta_description": "Discover Rishikesh, the Yoga Capital of the World. Practice yoga, meditation, and adventure sports in the spiritual heart of the Himalayas.",
                "highlights": [
                    {
                        "title": "Laxman Jhula",
                        "description": "Iconic suspension bridge over the Ganges",
                        "icon": "bridge",
                    },
                    {
                        "title": "Yoga Ashrams",
                        "description": "World-renowned centers for yoga and meditation",
                        "icon": "lotus",
                    },
                    {
                        "title": "River Rafting",
                        "description": "Adventure sports on the holy Ganges",
                        "icon": "waves",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Yoga Sessions",
                        "content": "Many ashrams offer drop-in yoga classes. Book in advance during peak season.",
                    },
                    {
                        "title": "Vegetarian Food",
                        "content": "The city is completely vegetarian and alcohol-free. Respect local customs.",
                    },
                    {
                        "title": "Adventure Activities",
                        "content": "River rafting season is from September to June. Avoid monsoon months.",
                    },
                ],
            },
            {
                "name": "Haridwar",
                "description": "Gateway to the gods, Haridwar is where the sacred Ganges descends from the Himalayas to the plains. Participate in the evening Ganga Aarti at Har Ki Pauri and feel the divine presence.",
                "meta_title": "Haridwar Travel Guide - Gateway to the Gods",
                "meta_description": "Experience Haridwar, the gateway to the gods. Witness Ganga Aarti at Har Ki Pauri and take holy dips in the sacred Ganges.",
                "highlights": [
                    {
                        "title": "Har Ki Pauri",
                        "description": "Most sacred ghat for Ganga Aarti and holy baths",
                        "icon": "temple",
                    },
                    {
                        "title": "Mansa Devi Temple",
                        "description": "Hilltop temple accessible by cable car",
                        "icon": "mountain",
                    },
                    {
                        "title": "Chandi Devi Temple",
                        "description": "Ancient temple dedicated to Goddess Chandi",
                        "icon": "temple",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Holy Dip",
                        "content": "Take a holy dip in the Ganges at Har Ki Pauri during sunrise for maximum spiritual benefit.",
                    },
                    {
                        "title": "Aarti Timing",
                        "content": "Evening Ganga Aarti starts at sunset. The atmosphere is most divine during this time.",
                    },
                    {
                        "title": "Cable Car",
                        "content": "Use cable cars to reach hilltop temples. They operate from early morning to evening.",
                    },
                ],
            },
            {
                "name": "Mathura",
                "description": "The birthplace of Lord Krishna, Mathura is steeped in divine love and devotion. Explore ancient temples, participate in colorful festivals, and immerse yourself in Krishna's eternal leela.",
                "meta_title": "Mathura Travel Guide - Birthplace of Lord Krishna",
                "meta_description": "Explore Mathura, the birthplace of Lord Krishna. Visit Krishna Janmabhoomi, ancient temples, and experience divine love and devotion.",
                "highlights": [
                    {
                        "title": "Krishna Janmabhoomi",
                        "description": "The exact birthplace of Lord Krishna",
                        "icon": "temple",
                    },
                    {
                        "title": "Dwarkadhish Temple",
                        "description": "Beautiful temple dedicated to Lord Krishna",
                        "icon": "temple",
                    },
                    {
                        "title": "Vishram Ghat",
                        "description": "Sacred ghat on the Yamuna River",
                        "icon": "waves",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Festival Season",
                        "content": "Visit during Janmashtami or Holi for the most vibrant celebrations.",
                    },
                    {
                        "title": "Temple Visits",
                        "content": "Early morning visits offer peaceful darshan and avoid crowds.",
                    },
                    {
                        "title": "Local Sweets",
                        "content": "Try famous Mathura peda and other Krishna-themed sweets.",
                    },
                ],
            },
            {
                "name": "Vrindavan",
                "description": "The playground of Lord Krishna, Vrindavan resonates with divine love and spiritual bliss. Visit the sacred temples, participate in kirtan, and experience the eternal romance of Radha-Krishna.",
                "meta_title": "Vrindavan Travel Guide - Krishna's Divine Playground",
                "meta_description": "Discover Vrindavan, Krishna's divine playground. Experience Radha-Krishna's eternal love, visit sacred temples, and participate in devotional kirtan.",
                "highlights": [
                    {
                        "title": "Banke Bihari Temple",
                        "description": "Most famous temple of Lord Krishna in Vrindavan",
                        "icon": "temple",
                    },
                    {
                        "title": "ISKCON Temple",
                        "description": "International temple with beautiful architecture",
                        "icon": "temple",
                    },
                    {
                        "title": "Radha Raman Temple",
                        "description": "Ancient temple with self-manifested deity",
                        "icon": "temple",
                    },
                ],
                "travel_tips": [
                    {
                        "title": "Temple Hopping",
                        "content": "Plan a full day to visit multiple temples. Each has unique significance.",
                    },
                    {
                        "title": "Kirtan Sessions",
                        "content": "Participate in evening kirtan sessions for a truly spiritual experience.",
                    },
                    {
                        "title": "Parikrama",
                        "content": "Join the traditional parikrama (circumambulation) of Vrindavan for spiritual merit.",
                    },
                ],
            },
        ]

        created_count = 0
        for city_data in cities_data:
            city_name = city_data["name"]
            city_slug = slugify(city_name)

            # Create or get city
            city, created = City.objects.get_or_create(
                slug=city_slug,
                defaults={
                    "name": city_name,
                    "description": city_data["description"],
                    "meta_title": city_data["meta_title"],
                    "meta_description": city_data["meta_description"],
                    "status": "PUBLISHED",
                },
            )

            if created:
                created_count += 1
                self.stdout.write(f"   ✅ Created city: {city_name}")

                # Add highlights
                for highlight_data in city_data["highlights"]:
                    Highlight.objects.create(
                        city=city,
                        title=highlight_data["title"],
                        description=highlight_data["description"],
                        icon=highlight_data["icon"],
                    )

                # Add travel tips
                for tip_data in city_data["travel_tips"]:
                    TravelTip.objects.create(
                        city=city, title=tip_data["title"], content=tip_data["content"]
                    )
            else:
                self.stdout.write(f"   ⚠️  City already exists: {city_name}")

        self.stdout.write(
            self.style.SUCCESS(f"🎉 Successfully created {created_count} cities!")
        )
        self.stdout.write(
            "🌐 Cities are now available at http://localhost:8000/api/cities/"
        )
