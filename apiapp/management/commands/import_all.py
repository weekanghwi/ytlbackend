from django.core.management.base import BaseCommand
import csv
from apiapp.models import AllTable

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/all2.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['site']
        do = lines['do']
        install = lines['install']
        ssv = lines['ssv']
        opt = lines['opt']
        certi = lines['certi']

        AllTable.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          do_id=do,
          install_id=install,
          ssv_id=ssv,
          optimization_id=opt,
          certification_id=certi
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))