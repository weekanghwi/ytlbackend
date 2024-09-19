from django.core.management.base import BaseCommand
import csv
from apiapp.models import SiteTXattninfo, SiteBasicinfo
from django.db import connection

class Command(BaseCommand):
  help = 'Update or create data from CSV file into Site LSM info model'

  def handle(self, *args, **options):
    csv_file_path = 'rawdata/WEEK36_TX.csv'
    unique_ids_in_csv = []

    with open(csv_file_path, mode='r') as file:
      csvFile = csv.DictReader(file)
      
      processed_count = 0
      created_count = 0
      update_count = 0

      for lines in csvFile:
        processed_count += 1

        sitebasicinfo_id = lines['NE NAME']
        cellnum = int(lines['CELL_NUM']) if lines['CELL_NUM'] else None

        unique_id = f'{sitebasicinfo_id}-{cellnum}'
        unique_ids_in_csv.append(unique_id)

        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo_id).first()

        defaults = {
          'sitebasicinfo': sitebasicinfo_instance,
          'siteid': sitebasicinfo_id,
          'cellnum': int(lines['CELL_NUM']) if lines['CELL_NUM'] else None,
          'connectboardid': int(lines['CONNECT_BOARD_ID']) if lines['CONNECT_BOARD_ID'] else None,
          'connectportid': int(lines['CONNECT_PORT_ID']) if lines['CONNECT_PORT_ID'] else None,
          'txattn': int(lines['TX_ATTEN']) if lines['TX_ATTEN'] else None,
        }

        obj, created = SiteTXattninfo.objects.update_or_create(
          siteid=sitebasicinfo_id,
          cellnum=cellnum,
          defaults=defaults
        )

        if created:
          created_count += 1
          self.stdout.write(f'Created new record for {unique_id}')
        else:
          update_count += 1
          self.stdout.write(f'Updated existing record for {unique_id}')
        self.stdout.write(f'Processed {processed_count} rows so far')

      all_site_lsm_info = SiteTXattninfo.objects.all()

      for site_info in all_site_lsm_info:
        unique_id_db = site_info.uid
        if unique_id_db not in unique_ids_in_csv:
          site_info.sitestatus = 'Dismantled'
          site_info.save()

          self.stdout.write(f'Updated remark to dismantled for {unique_id_db}')
    self.stdout.write(self.style.SUCCESS('Successfully updated the database with CSV file'))