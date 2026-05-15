from django.core.management.base import BaseCommand
from inventory.models import ProductCategory, Product, ProductVariant


class Command(BaseCommand):
    help = "Seed full liquor POS catalog (categories, products, variants)"

    def handle(self, *args, **kwargs):

        # =========================
        # 1. CATEGORIES
        # =========================
        categories = [
            "Beer",
            "Keg",
            "Wines",
            "Whisky",
            "Vodka",
            "Gin",
            "Rum",
            "Soft Drinks",
            "Water",
            "Energy Drinks",
        ]

        category_map = {}

        for name in categories:
            cat, _ = ProductCategory.objects.get_or_create(name=name)
            category_map[name] = cat

        self.stdout.write(self.style.SUCCESS("Categories seeded"))

        # =========================
        # 2. PRODUCTS
        # =========================
        products_data = [
            ("Tusker Lager", "Beer"),
            ("Heineken", "Beer"),
            ("White Cap", "Beer"),
            ("Guinness", "Beer"),

            ("Dark Keg", "Keg"),
            ("Regular Keg", "Keg"),

            ("Nederburg Wine", "Wines"),
            ("Baron Romero", "Wines"),

            ("Jameson", "Whisky"),
            ("Johnnie Walker Red", "Whisky"),
            ("Jack Daniels", "Whisky"),

            ("Smirnoff Vodka", "Vodka"),
            ("Absolute Vodka", "Vodka"),

            ("Bombay Sapphire", "Gin"),
            ("Gilbeys Gin", "Gin"),

            ("Captain Morgan", "Rum"),

            ("Coca Cola", "Soft Drinks"),
            ("Fanta Orange", "Soft Drinks"),

            ("Dasani Water", "Water"),

            ("Monster Energy", "Energy Drinks"),
        ]

        product_map = {}

        for name, cat_name in products_data:
            product, _ = Product.objects.get_or_create(
                name=name,
                category=category_map[cat_name]
            )
            product_map[name] = product

        self.stdout.write(self.style.SUCCESS("Products seeded"))

        # =========================
        # 3. VARIANTS (SIZE ONLY — NO PRICES)
        # =========================
        variants = [
            "1L",
            "750ml",
            "500ml",
            "300ml",
            "250ml",
            "30ml",
        ]

        created = 0

        for product in product_map.values():
            for volume in variants:

                ProductVariant.objects.get_or_create(
                    product=product,
                    volume=volume
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Variants seeded: {created}")
        )

        self.stdout.write(
            self.style.SUCCESS("FULL POS CATALOG READY 🚀")
        )