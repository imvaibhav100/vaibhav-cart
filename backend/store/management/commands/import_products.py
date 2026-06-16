from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from store.models import Category, Product
from decimal import Decimal
import os


class Command(BaseCommand):
    help = 'Import product images from MEDIA_ROOT/products into Product entries'

    def add_arguments(self, parser):
        parser.add_argument('--category', type=str, default='Imported', help='Category name to use')
        parser.add_argument('--price', type=str, default='0.00', help='Default price for imported products')
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing products for same image name')

    def handle(self, *args, **options):
        cat_name = options['category']
        price = Decimal(options['price'])
        overwrite = options['overwrite']

        category, _ = Category.objects.get_or_create(name=cat_name, defaults={'slug': cat_name.lower().replace(' ', '-')})

        products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        if not os.path.isdir(products_dir):
            self.stdout.write(self.style.ERROR(f'Products folder not found: {products_dir}'))
            return

        files = [f for f in os.listdir(products_dir) if os.path.isfile(os.path.join(products_dir, f))]
        if not files:
            self.stdout.write(self.style.WARNING('No files found in products folder'))
            return

        created = 0
        skipped = 0
        for filename in files:
            name, ext = os.path.splitext(filename)
            image_path = os.path.join(products_dir, filename)

            existing = Product.objects.filter(image__icontains=f'products/{filename}')
            if existing.exists() and not overwrite:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'Skipping existing product for {filename}'))
                continue

            # create product
            prod_name = name.replace('-', ' ').replace('_', ' ').title()
            product = Product(category=category, name=prod_name, description='', price=price)

            # attach image
            with open(image_path, 'rb') as f:
                django_file = File(f)
                product.image.save(filename, django_file, save=False)

            product.save()
            created += 1
            self.stdout.write(self.style.SUCCESS(f'Created product for {filename}'))

        self.stdout.write(self.style.SUCCESS(f'Done: created={created}, skipped={skipped}'))
