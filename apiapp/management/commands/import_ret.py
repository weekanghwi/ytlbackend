from django.core.management.base import BaseCommand
import csv
from apiapp.models import SiteRETinfo, SiteBasicinfo
from django.db import connection

def truncate_table(table_name):
  with connection.cursor() as cursor:
    cursor.execute(f'TRUNCATE TABLE {table_name};')

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # SiteRETinfo.objects.all().delete()
    truncate_table('apiapp_siteretinfo')
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/WEEK36_RET.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo_id = lines['NE NAME']
        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo_id).first()

        siteid = lines['NE NAME']
        connectboardtype = int(lines['CONNECT_BOARD_TYPE']) if lines['CONNECT_BOARD_TYPE'] else None
        connectboardid = int(lines['CONNECT_BOARD_ID']) if lines['CONNECT_BOARD_ID'] else None
        connectportid = int(lines['CONNECT_PORT_ID']) if lines['CONNECT_PORT_ID'] else None
        cascaderrhid = int(lines['CASCADE_RRH_ID']) if lines['CASCADE_RRH_ID'] else None
        aldid = int(lines['ALD_ID']) if lines['ALD_ID'] else None
        antidsubnetid = int(lines['ANT_ID_SUBUNIT_ID']) if lines['ANT_ID_SUBUNIT_ID'] else None
        tilt = int(lines['TILT']) if lines['TILT'] else None

        if tilt is not None and tilt <= 1000:
          SiteRETinfo.objects.create(
            sitebasicinfo=sitebasicinfo_instance,
            siteid=siteid,
            connectboardtype=connectboardtype,
            connectboardid=connectboardid,
            connectportid=connectportid,
            cascaderrhid=cascaderrhid,
            aldid=aldid,
            antidsubnetid=antidsubnetid,
            tilt=tilt
          )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
