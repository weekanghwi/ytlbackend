from django.core.management.base import BaseCommand
import csv
from apiapp.models import StatisticCalculated, SiteBasicinfo, Region
from django.db import connection

class Command(BaseCommand):
  help = 'Update or create data from CSV file into Site statistic calculated table'

  def handle(self, *args, **options):
    csv_file_path = 'rawdata/STATISTIC_CALCULATED.csv'
    unique_ids_in_csv = []

    with open(csv_file_path, mode='r') as file:
      csvFile = csv.DictReader(file)
      
      processed_count = 0
      created_count = 0
      update_count = 0

      for lines in csvFile:
        processed_count += 1

        category = lines['category']
        region = lines['region']
        unique_id = lines['uid']
        unique_ids_in_csv.append(unique_id)

        region_instance = Region.objects.filter(region__iexact=region).first()

        defaults = {
          'uid': unique_id,
          'category': category,
          'region': region_instance,
          'band': lines['band'] if lines['band'] else None,
          'weeknum': lines['weeknum'] if lines['weeknum'] else None,
          'cell_availability': float(lines['Cell_Avaiability']) if float(lines['Cell_Avaiability']) else None,
          'attach_setup_success_rate': float(lines['Attach_Setup_Success_Rate']) if float(lines['Attach_Setup_Success_Rate']) else None,
          'rrc_setup_success_rate': float(lines['RRC_Setup_Success_Rate']) if float(lines['RRC_Setup_Success_Rate']) else None,
          'erab_setup_success_rate_ngbr': float(lines['eRAB_Setup_Success_Rate_nGBR']) if float(lines['eRAB_Setup_Success_Rate_nGBR']) else None,
          'volte_setup_success_rate_gbr': float(lines['VoLTE_Setup_Success_Rate_GBR']) if float(lines['VoLTE_Setup_Success_Rate_GBR']) else None,
          'call_drop_rate_erab_ngbr': float(lines['Call_Drop_Rate_eRAB_nGBR']) if float(lines['Call_Drop_Rate_eRAB_nGBR']) else None,
          'volte_call_drop_rate_erab_gbr': float(lines['VoLTE_Call_Drop_Rate_eRAB_GBR']) if float(lines['VoLTE_Call_Drop_Rate_eRAB_GBR']) else None,
          'hosr_intra_frequency': float(lines['HOSR_Intra_Frequency']) if float(lines['HOSR_Intra_Frequency']) else None,
          'hosr_inter_frequency': float(lines['HOSR_Inter_Frequency']) if float(lines['HOSR_Inter_Frequency']) else None,
          'x2_handover_out_success_rate': float(lines['X2_Handover_Out_Success_Rate']) if float(lines['X2_Handover_Out_Success_Rate']) else None,
          'x2_handover_in_success_rate': float(lines['X2_Handover_In_Success_Rate']) if float(lines['X2_Handover_In_Success_Rate']) else None,
          's1_handover_out_success_rate': float(lines['S1_Handover_Out_Success_Rate']) if float(lines['S1_Handover_Out_Success_Rate']) else None,
          's1_handover_in_success_rate': float(lines['S1_Handover_In_Success_Rate']) if float(lines['S1_Handover_In_Success_Rate']) else None,
          'dl_bler': float(lines['DL_BLER']) if float(lines['DL_BLER']) else None,
          'ul_bler': float(lines['UL_BLER']) if float(lines['UL_BLER']) else None,
        }

        obj, created = StatisticCalculated.objects.update_or_create(
          uid = unique_id,
          defaults=defaults
        )

        if created:
          created_count += 1
          self.stdout.write(f'Created new record for {unique_id}')
        else:
          update_count += 1
          self.stdout.write(f'Updated existing record for {unique_id}')
        self.stdout.write(f'Processed {processed_count} rows so far')

      all_site_lsm_info = StatisticCalculated.objects.all()

      # for site_info in all_site_lsm_info:
      #   unique_id_db = site_info.uid
      #   if unique_id_db not in unique_ids_in_csv:
      #     site_info.sitestatus = 'Dismantled'
      #     site_info.save()

      #     self.stdout.write(f'Updated remark to dismantled for {unique_id_db}')
    self.stdout.write(self.style.SUCCESS('Successfully updated the database with CSV file'))