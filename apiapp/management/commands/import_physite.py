from django.core.management.base import BaseCommand
import csv
from apiapp.models import SitePhyinfo, SiteBasicinfo, AntennaType
from django.db import connection

def truncate_table(table_name):
  with connection.cursor() as cursor:
    cursor.execute(f'TRUNCATE TABLE {table_name};')

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # SitePhyinfo.objects.all().delete()
    truncate_table('apiapp_sitephyinfo')
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/WEEK40.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo_id = lines['LTE_Site_ID']
        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo_id).first()

        phyanttype_id = lines['Antenna_Type'] if lines['Antenna_Type'] else None
        antennatype_instance = AntennaType.objects.filter(antennatype=phyanttype_id).first()

        secid = int(lines['LTE_Sec_ID']) if lines['LTE_Sec_ID'] else None
        portnum = int(lines['Port_Num']) if lines['Port_Num'] else None
        height = int(lines['Height']) if lines['Height'] else None
        azimuth = int(lines['Azimuth']) if lines['Azimuth'] else None
        mtilt =  int(lines['M_Tilt']) if lines['M_Tilt'] else None
        etilt = int(lines['E_Tilt']) if lines['E_Tilt'] else None
        band = int(lines['Tec']) if lines['Tec'] else None

        SitePhyinfo.objects.create(
          sitebasicinfo=sitebasicinfo_instance,
          secid=secid,
          portnum=portnum,
          band=band,
          antennatype=antennatype_instance,
          antennaheight=height,
          azimuth=azimuth,
          mtilt=mtilt,
          etilt=etilt,
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
