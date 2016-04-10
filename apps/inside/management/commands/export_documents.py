import os

from apps.inside.models import Document, DocumentCategory
from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    """ Exports Documents uploaded to the Inside document store"""
    output_dir = os.path.join(settings.BASE_DIR, 'insidedocs')

    def handle(self, *args, **options):
        # Get list of documents
        docs = Document.objects.all()

        # Create folders
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        cats = DocumentCategory.objects.all()
        for c in cats:
            cat_dir = os.path.join(self.output_dir, c.title)
            if not os.path.exists(cat_dir):
                os.mkdir(cat_dir)

        # Write files
        for d in docs:
            without_ext = ''.join(d.name.split('.')[:-1])
            ext = d.name.split('.')[-1]
            file_name = '{} - [{}].{}'.format(without_ext, d.date.strftime('%Y-%m-%d'), ext)

            file_path = os.path.join(self.output_dir, d.documentcategory.title, file_name)
            document_data = d.documentdata_set.order_by('pk')
            num_bytes = 0
            with open(file_path, 'wb') as f:
                for data in document_data:
                    num_bytes += f.write(data.data)

            print("Wrote {0:.0f} kB to '{1}'.".format(num_bytes/1024, file_path))
            assert num_bytes == d.size
        print('Total number of documents: {}'.format(docs.count()))
