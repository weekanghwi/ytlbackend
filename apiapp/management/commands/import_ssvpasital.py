from django.core.management.base import BaseCommand
import csv
from apiapp.models import SSV

class Command(BaseCommand):
  help = 'Import data from CSV file into SSV model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/ssvpasital.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        ssv_id = lines['id']
        subcon = lines['subcon'] if lines['subcon'] else None

        try:
          ssv_object = SSV.objects.get(id=ssv_id)

          # subcon이 비어 있든, 비어 있지 않든 업데이트
          ssv_object.ssvsubcon_id = subcon
          ssv_object.save()
          self.stdout.write(self.style.SUCCESS(f'Successfully updated SSV object with id {ssv_id}'))

        except SSV.DoesNotExist:
          self.stdout.write(self.style.ERROR(f'SSV object with id {ssv_id} does not exist'))

    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
