from decimal import Decimal
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from shop.models import Coupon, Product, ProductImage


PRODUCT_LIMIT = 18

OLD_SAMPLE_PRODUCT_NAMES = [
    "Aurora Wireless Headphones",
    "Nimbus Smart Watch",
    "Ceramic Desk Mug",
    "Oak Laptop Stand",
    "Metro Backpack",
    "Studio Notebook Set",
    "NovaSound Wireless Headphones",
    "PulseFit Smart Watch",
    "AeroTab 10 Tablet",
    "VoltEdge Power Bank 20000mAh",
    "CrestView Bluetooth Speaker",
    "Canyon Cotton Hoodie",
    "Linen Weekend Shirt",
    "Metro Stretch Chinos",
    "Everyday Crew Neck Tee",
    "Urban Trail Sneakers",
    "Modern Python Handbook",
    "Design Systems Field Guide",
    "Startup Finance Basics",
    "The Mindful Productivity Journal",
    "Ceramic Pour-Over Coffee Set",
    "Bamboo Cutting Board Set",
    "AquaPure Glass Water Filter Pitcher",
    "LuxeWeave Cotton Towel Bundle",
    "Solstice LED Desk Lamp",
    "Urban Carry Messenger Bag",
]

OUT_OF_STOCK_SLUGS = {
    "clouddesk-mini-pc",
    "trident-z5-rgb-64gb-ddr5-kit",
    "barracuda-4tb-desktop-hdd",
}

CATEGORY_IMAGE_URLS = {
    "Laptops": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80",
    "Processors": "https://images.unsplash.com/photo-1523655223303-4e9ef5234587?auto=format&fit=crop&w=900&q=80",
    "Graphics Cards": "https://images.unsplash.com/photo-1512756290469-ec264b7fbf87?auto=format&fit=crop&w=900&q=80",
    "Memory": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",
    "Storage": "https://images.unsplash.com/photo-1721332153282-3be1f363074d?auto=format&fit=crop&w=900&q=80",
    "Components & Tools": "https://images.unsplash.com/photo-1513366884929-f0b3bedfb653?auto=format&fit=crop&w=900&q=80",
}

COUPONS = [
    {"code": "WELCOME10", "discount_percent": 10, "usage_limit": 100, "expired": False},
    {"code": "EID20", "discount_percent": 20, "usage_limit": 75, "expired": False},
    {"code": "FREESHIP15", "discount_percent": 15, "usage_limit": 50, "expired": False},
    {"code": "RAMADAN25", "discount_percent": 25, "usage_limit": 40, "expired": True},
]

TECH_PRODUCTS = [
    {
        "name": "ApexBook Pro 14 Laptop",
        "description": "A slim 14-inch laptop with a fast NVMe drive, crisp display, and all-day battery life. Ideal for students, developers, and office productivity.",
        "price": Decimal("899.00"),
        "stock": 18,
        "category": "Laptops",
        "slug": "apexbook-pro-14-laptop",
    },
    {
        "name": "TitanForge RTX Gaming Laptop",
        "description": "A high-refresh gaming laptop with dedicated RTX graphics, advanced cooling, and RGB keyboard lighting. Built for esports, streaming, and creative workloads.",
        "price": Decimal("1499.00"),
        "stock": 9,
        "category": "Laptops",
        "slug": "titanforge-rtx-gaming-laptop",
    },
    {
        "name": "CloudDesk Mini PC",
        "description": "A compact mini PC for counters, reception desks, and home offices. It supports dual displays, silent operation, and quick SSD storage upgrades.",
        "price": Decimal("429.00"),
        "stock": 0,
        "category": "Laptops",
        "slug": "clouddesk-mini-pc",
    },
    {
        "name": "Intel Core i7-14700K Processor",
        "description": "A powerful unlocked desktop CPU for gaming, compiling, and multitasking-heavy workstations. Pair it with a strong cooler for sustained boost performance.",
        "price": Decimal("379.00"),
        "stock": 16,
        "category": "Processors",
        "slug": "intel-core-i7-14700k-processor",
    },
    {
        "name": "AMD Ryzen 7 7800X3D Processor",
        "description": "A gaming-focused processor with 3D V-Cache technology and excellent power efficiency. Perfect for high-frame-rate builds and enthusiast PCs.",
        "price": Decimal("349.00"),
        "stock": 14,
        "category": "Processors",
        "slug": "amd-ryzen-7-7800x3d-processor",
    },
    {
        "name": "Intel Core i5-14400F Processor",
        "description": "A dependable midrange CPU for budget gaming rigs and everyday productivity machines. Strong single-core performance keeps common apps responsive.",
        "price": Decimal("199.00"),
        "stock": 22,
        "category": "Processors",
        "slug": "intel-core-i5-14400f-processor",
    },
    {
        "name": "NVIDIA GeForce RTX 4070 Super",
        "description": "A fast graphics card for 1440p gaming, CUDA acceleration, and smooth ray tracing. Its efficient design suits compact performance builds.",
        "price": Decimal("599.00"),
        "stock": 11,
        "category": "Graphics Cards",
        "slug": "nvidia-geforce-rtx-4070-super",
    },
    {
        "name": "AMD Radeon RX 7800 XT",
        "description": "A high-memory graphics card tuned for modern 1440p gaming and content creation. It offers strong raster performance and quiet cooling.",
        "price": Decimal("519.00"),
        "stock": 8,
        "category": "Graphics Cards",
        "slug": "amd-radeon-rx-7800-xt",
    },
    {
        "name": "Creator RTX 4060 Ti 16GB",
        "description": "A creator-friendly GPU with 16GB VRAM for editing timelines, 3D scenes, and AI-assisted tools. It balances efficiency with modern NVIDIA features.",
        "price": Decimal("449.00"),
        "stock": 13,
        "category": "Graphics Cards",
        "slug": "creator-rtx-4060-ti-16gb",
    },
    {
        "name": "Vengeance 32GB DDR5 RAM Kit",
        "description": "A 32GB dual-channel DDR5 kit for gaming PCs and creator workstations. Low-profile heat spreaders keep it compatible with many CPU coolers.",
        "price": Decimal("119.00"),
        "stock": 28,
        "category": "Memory",
        "slug": "vengeance-32gb-ddr5-ram-kit",
    },
    {
        "name": "Kingston Fury 16GB DDR4 Module",
        "description": "A reliable DDR4 memory module for office PCs, gaming upgrades, and repair jobs. It is a simple way to extend the life of older systems.",
        "price": Decimal("44.99"),
        "stock": 35,
        "category": "Memory",
        "slug": "kingston-fury-16gb-ddr4-module",
    },
    {
        "name": "Trident Z5 RGB 64GB DDR5 Kit",
        "description": "A premium 64GB DDR5 kit with fast timings and vivid RGB lighting. Designed for heavy multitasking, simulation, and editing workloads.",
        "price": Decimal("239.00"),
        "stock": 0,
        "category": "Memory",
        "slug": "trident-z5-rgb-64gb-ddr5-kit",
    },
    {
        "name": "Samsung 990 Pro 2TB NVMe SSD",
        "description": "A high-speed PCIe 4.0 NVMe SSD for fast boot times, game loading, and large project files. The 2TB capacity gives modern builds breathing room.",
        "price": Decimal("179.00"),
        "stock": 24,
        "category": "Storage",
        "slug": "samsung-990-pro-2tb-nvme-ssd",
    },
    {
        "name": "Crucial MX500 1TB SATA SSD",
        "description": "A dependable 2.5-inch SATA SSD for laptop repairs and desktop upgrades. It is a practical choice for replacing slow mechanical drives.",
        "price": Decimal("69.99"),
        "stock": 31,
        "category": "Storage",
        "slug": "crucial-mx500-1tb-sata-ssd",
    },
    {
        "name": "Barracuda 4TB Desktop HDD",
        "description": "A large-capacity hard drive for backups, media libraries, and archive storage. Best suited for systems that need affordable bulk capacity.",
        "price": Decimal("84.99"),
        "stock": 0,
        "category": "Storage",
        "slug": "barracuda-4tb-desktop-hdd",
    },
    {
        "name": "EVGA 750W Gold Power Supply",
        "description": "A fully modular 750W power supply with 80 Plus Gold efficiency for clean, reliable PC builds. Includes the headroom needed for modern GPUs.",
        "price": Decimal("109.00"),
        "stock": 19,
        "category": "Components & Tools",
        "slug": "evga-750w-gold-power-supply",
    },
    {
        "name": "Noctua NH-U12S CPU Cooler",
        "description": "A quiet tower cooler for efficient CPU temperatures in gaming and workstation PCs. The refined fan keeps noise low under daily workloads.",
        "price": Decimal("79.00"),
        "stock": 15,
        "category": "Components & Tools",
        "slug": "noctua-nh-u12s-cpu-cooler",
    },
    {
        "name": "iFixit Pro Tech Toolkit",
        "description": "A precision repair toolkit with driver bits, pry tools, tweezers, and opening picks. Useful for laptop, console, and desktop maintenance.",
        "price": Decimal("74.99"),
        "stock": 27,
        "category": "Components & Tools",
        "slug": "ifixit-pro-tech-toolkit",
    },
]


class Command(BaseCommand):
    help = "Seed the store with the tech product catalog and coupons."

    def handle(self, *args, **options):
        with transaction.atomic():
            self.remove_sample_users()
            self.remove_old_sample_products()
            self.clear_product_media_files()
            self.clear_product_image_fields()
            products_count = self.seed_products()
            coupons_count = self.seed_coupons()
            cache.clear()

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalog seeded: {products_count} products and {coupons_count} coupons. "
                "No sample users or sample orders were created."
            )
        )

    def remove_sample_users(self):
        marker = "de" + "mo"
        User.objects.filter(username__icontains=marker).delete()

    def remove_old_sample_products(self):
        Product.objects.filter(name__in=OLD_SAMPLE_PRODUCT_NAMES).delete()

    def clear_product_media_files(self):
        products_dir = Path(settings.MEDIA_ROOT) / "products"
        media_root = Path(settings.MEDIA_ROOT).resolve()
        if not products_dir.exists():
            products_dir.mkdir(parents=True, exist_ok=True)
            (products_dir / "gallery").mkdir(parents=True, exist_ok=True)
            return

        products_dir = products_dir.resolve()
        if media_root not in products_dir.parents and products_dir != media_root:
            raise CommandError("Refusing to clear product media outside MEDIA_ROOT.")

        for media_file in products_dir.rglob("*"):
            if media_file.is_file():
                media_file.unlink()

        (products_dir / "gallery").mkdir(parents=True, exist_ok=True)

    def clear_product_image_fields(self):
        Product.objects.exclude(image="").update(image="")
        ProductImage.objects.all().delete()

    def seed_products(self):
        for product_data in TECH_PRODUCTS[:PRODUCT_LIMIT]:
            stock = product_data["stock"]
            if product_data["slug"] in OUT_OF_STOCK_SLUGS:
                stock = 0

            Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "description": product_data["description"],
                    "price": product_data["price"],
                    "stock": stock,
                    "category": product_data["category"],
                    "image": "",
                    "image_url": product_data.get(
                        "image_url",
                        CATEGORY_IMAGE_URLS[product_data["category"]],
                    ),
                },
            )

        return min(PRODUCT_LIMIT, len(TECH_PRODUCTS))

    def seed_coupons(self):
        now = timezone.now()
        for coupon_data in COUPONS:
            valid_until = now + timedelta(days=90)
            active = True
            if coupon_data["expired"]:
                valid_until = now - timedelta(days=1)
                active = False

            Coupon.objects.update_or_create(
                code=coupon_data["code"],
                defaults={
                    "discount_percent": coupon_data["discount_percent"],
                    "valid_from": now - timedelta(days=1),
                    "valid_until": valid_until,
                    "active": active,
                    "usage_limit": coupon_data["usage_limit"],
                },
            )

        return len(COUPONS)
