from django.core.management.base import BaseCommand
import csv
from apiapp.models import ReferenceRET

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    ReferenceRET.objects.all().delete()
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/ret_reference.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        tbindex = lines['tbindex']
        band = lines['band'] if lines['band'] else None
        sec_id = int(lines['sec_id']) if lines['sec_id'] else None
        port_number = int(lines['port_number']) if lines['port_number'] else None
        ant_type = lines['ant_type'] if lines['ant_type'] else None
        card = lines['card'] if lines['card'] else None
        remark = lines['remark'] if lines['remark'] else None

        ReferenceRET.objects.create(
          uid=tbindex,
          band=band,
          secid=sec_id,
          portnum=port_number,

          channelcard=ant_type,
          antennatype=card,
          remark=remark,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
