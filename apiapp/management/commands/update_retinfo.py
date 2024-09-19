from django.core.management.base import BaseCommand
import csv
from apiapp.models import SiteRETinfo, SiteBasicinfo
from django.db import connection

class Command(BaseCommand):
  help = 'Update or create data from CSV file into Site LSM info model'

  def handle(self, *args, **options):
    csv_file_path = 'rawdata/WEEK48_RET.csv'
    unique_ids_in_csv = []

    with open(csv_file_path, mode='r') as file:
      csvFile = csv.DictReader(file)
      
      processed_count = 0
      created_count = 0
      update_count = 0

      for lines in csvFile:
        processed_count += 1

        sitebasicinfo_id = lines['NE NAME']
        cellnum = int(lines['CellNum']) if lines['CellNum'] else None

        unique_id = f'{sitebasicinfo_id}-{cellnum}'
        unique_ids_in_csv.append(unique_id)

        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo_id).first()

        defaults = {
          'sitebasicinfo': sitebasicinfo_instance,
          'cellnum': int(lines['CellNum']) if lines['CellNum'] else None,
          'cellidentity': int(lines['CellIdentity']) if lines['CellIdentity'] else None,
          'pci': int(lines['PCI']) if lines['PCI'] else None,
          'earfcndl': int(lines['EarfcnDl']) if lines['EarfcnDl'] else None,
          'earfcnul': int(lines['EarfcnUl']) if lines['EarfcnUl'] else None,
          'freqband': int(lines['FreqBandIndicator']) if lines['FreqBandIndicator'] else None,
          'rsi': int(lines['RSI']) if lines['RSI'] else None,
          'tac': int(lines['TAC'].replace("H'", ''), 16) if lines['TAC'] else None,
          'channelcard': lines['CHANNEL CARD'] if lines['CHANNEL CARD'] else None
        }

        obj, created = SiteRETinfo.objects.update_or_create(
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

      all_site_lsm_info = SiteLSMinfo.objects.all()

      for site_info in all_site_lsm_info:
        unique_id_db = site_info.uid
        if unique_id_db not in unique_ids_in_csv:
          site_info.sitestatus = 'Dismantled'
          site_info.save()

          self.stdout.write(f'Updated remark to dismantled for {unique_id_db}')
    self.stdout.write(self.style.SUCCESS('Successfully updated the database with CSV file'))