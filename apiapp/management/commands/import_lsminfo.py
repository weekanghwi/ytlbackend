from django.core.management.base import BaseCommand
import csv
from apiapp.models import SiteLSMinfo, SiteBasicinfo
from django.db import connection

def truncate_table(table_name):
  with connection.cursor() as cursor:
    cursor.execute(f'TRUNCATE TABLE {table_name};')



class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # SiteLSMinfo.objects.all().delete()
    truncate_table('apiapp_sitelsminfo')
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/WEEK41_PCI.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo_id = lines['NE NAME']
        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo_id).first()

        sitebasicinfo = lines['NE NAME']
        cellnum = int(lines['CellNum']) if lines['CellNum'] else None
        cellidentity = int(lines['CellIdentity']) if lines['CellIdentity'] else None
        pci = int(lines['PCI']) if lines['PCI'] else None
        earfcndl = int(lines['EarfcnDl']) if lines['EarfcnDl'] else None
        earfcnul = int(lines['EarfcnUl']) if lines['EarfcnUl'] else None
        freqband = int(lines['FreqBandIndicator']) if lines['FreqBandIndicator'] else None
        rsi = int(lines['RSI']) if lines['RSI'] else None
        tac_hex = lines['TAC'].replace("H'", '')
        tac = int(tac_hex, 16) if tac_hex else None
        channelcard = lines['CHANNEL CARD'] if lines['CHANNEL CARD'] else None

        SiteLSMinfo.objects.create(
          sitebasicinfo=sitebasicinfo_instance,
          siteid=sitebasicinfo,
          cellnum=cellnum,
          cellidentity=cellidentity,
          pci=pci,

          earfcndl=earfcndl,
          earfcnul=earfcnul,
          freqband=freqband,
          rsi=rsi,
          tac=tac,
          channelcard=channelcard
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
