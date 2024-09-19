from django.core.management.base import BaseCommand
import csv
from apiapp.models import AllTable

class Command(BaseCommand):
  help = 'Import data from CSV file into SSV model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/alltable_pataial.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        all_id = lines['id']
        material = lines['material_id'] if lines['material_id'] else None

        try:
          material_object = AllTable.objects.get(id=all_id)

          # subcon이 비어 있든, 비어 있지 않든 업데이트
          material_object.material_id = material
          material_object.save()
          self.stdout.write(self.style.SUCCESS(f'Successfully updated SSV object with id {all_id}'))

        except AllTable.DoesNotExist:
          self.stdout.write(self.style.ERROR(f'SSV object with id {all_id} does not exist'))

    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
