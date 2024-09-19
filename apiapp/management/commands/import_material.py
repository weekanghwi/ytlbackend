from django.core.management.base import BaseCommand
import csv
from apiapp.models import Material

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/material.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        dumaterial = lines['dumaterial']
        rumaterial = lines['rumaterial']

        Material.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          dumaterial=dumaterial,
          rumaterial=rumaterial,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
