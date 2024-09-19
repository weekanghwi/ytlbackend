from django.core.management.base import BaseCommand
import csv
from apiapp.models import Optimization

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/opt.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        opttype = lines['opttype'] if lines['opttype'] else None
        startdate = lines['startdate'] if lines['startdate'] else None
        completedate = lines['completedate'] if lines['completedate'] else None
        submitdate = lines['submitdate'] if lines['submitdate'] else None
        approvedate = lines['approvedate'] if lines['approvedate'] else None

        Optimization.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          opttype_id=opttype,
          startdate=startdate,
          completedate=completedate,
          submitdate=submitdate,
          approvedate=approvedate,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
