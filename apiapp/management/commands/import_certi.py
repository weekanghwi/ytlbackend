from django.core.management.base import BaseCommand
import csv
from apiapp.models import Certification

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/certi.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        pacsubmitdate = lines['pacsubmitdate'] if lines['pacsubmitdate'] else None
        facsubmitdate = lines['facsubmitdate'] if lines['facsubmitdate'] else None
        pacapprovestatus = lines['pacapprovestatus'] if lines['pacapprovestatus'] else None
        facapprovestatus = lines['facapprovestatus'] if lines['facapprovestatus'] else None

        Certification.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          pacsubmitdate=pacsubmitdate,
          facsubmitdate=facsubmitdate,
          pacapprovestatus_id=pacapprovestatus,
          facapprovestatus_id=facapprovestatus,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
