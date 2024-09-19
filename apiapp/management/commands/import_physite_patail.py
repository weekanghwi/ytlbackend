from django.core.management.base import BaseCommand
import csv
from apiapp.models import SitePhyinfo

class Command(BaseCommand):
  help = 'Import data from CSV file into SSV model'

  def handle(self, *args, **options):
    # 파일 경로
    csv_file_path = 'rawdata/sitephyinfo_patail.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitephyinfo_id = lines['id']
        etilt = lines['etilt'] if lines['etilt'] else None

        try:
          sitephyinfo_object = SitePhyinfo.objects.get(id=sitephyinfo_id)

          # update 항목이  비어 있든, 비어 있지 않든 업데이트
          sitephyinfo_object.etilt = etilt
          sitephyinfo_object.save()
          self.stdout.write(self.style.SUCCESS(f'Successfully updated object with id {sitephyinfo_id}'))

        except SitePhyinfo.DoesNotExist:
          self.stdout.write(self.style.ERROR(f'object with id {sitephyinfo_id} does not exist'))

    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
