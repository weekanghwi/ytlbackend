from django.core.management.base import BaseCommand
import csv
from apiapp.models import SSV

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/ssv.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        startdate = lines['startdate'] if lines['startdate'] else None
        completedate = lines['completedate'] if lines['completedate'] else None
        ssvsubmitdate = lines['ssvsubmitdate'] if lines['ssvsubmitdate'] else None
        bsreceivedate = lines['bsreceivedate'] if lines['bsreceivedate'] else None
        bssubmitdate = lines['bssubmitdate'] if lines['bssubmitdate'] else None
        bsapprovedate = lines['bsapprovedate'] if lines['bsapprovedate'] else None

        SSV.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          startdate=startdate,
          completedate=completedate,
          ssvsubmitdate=ssvsubmitdate,
          bsreceivedate=bsreceivedate,
          bssubmitdate=bssubmitdate,
          bsapprovedate=bsapprovedate,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
