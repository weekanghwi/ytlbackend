from django.core.management.base import BaseCommand
import csv
from apiapp.models import DO

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/do.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        doissuedate = lines['doissuedate'] if lines['doissuedate'] else None
        codsubmitdate = lines['codsubmitdate'] if lines['codsubmitdate'] else None
        codapprovedate = lines['codapprovedate'] if lines['codapprovedate'] else None

        DO.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          doissuedate=doissuedate,
          codsubmitdate=codsubmitdate,
          codapprovedate=codapprovedate
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
