from django.core.management.base import BaseCommand
import csv
from apiapp.models import Statistic, SitePhyinfo, SiteBasicinfo, Region
from django.db import connection

class Command(BaseCommand):
  help = 'Update or create data from CSV file into Site LSM info model'

  def handle(self, *args, **options):
    csv_file_path = 'rawdata/WEEK36_STATISTIC.csv'
    unique_ids_in_csv = []

    with open(csv_file_path, mode='r') as file:
      csvFile = csv.DictReader(file)
      
      processed_count = 0
      created_count = 0
      update_count = 0

      for lines in csvFile:
        processed_count += 1

        uid = lines['uid']
        region = lines['region'] if lines['region'] else None
        sitebasicinfo = lines['uid'].split('-')[0] if lines['uid'] else None
        cellnum = int(lines['cellnum']) if lines['cellnum'] else None

        # unique_id = f'{sitebasicinfo_id}-{cellnum}'
        unique_ids_in_csv.append(uid)

        phyinfo_instance = SitePhyinfo.objects.filter(uid=uid).first()
        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo).first()
        region_instance = Region.objects.filter(region__iexact=region).first()

        defaults = {
          'sitebasicinfo': sitebasicinfo_instance,
          'region': region_instance,
          'sitephyinfo': phyinfo_instance,
          'uid': uid,
          'sysid': lines['sys_id'] if lines['sys_id'] else None,
          'band': lines['band'] if lines['band'] else None,
          'year': int(lines['YEAR']) if lines['YEAR'] else None,
          'weeknum': lines['weeknum'] if lines['weeknum'] else None,
          'cluster': lines['cluster'] if lines['cluster'] else None,
          'cellnum': int(lines['cellnum']) if lines['cellnum'] else None,
          'cell_availability': float(lines['Cell_Availability']) if lines['Cell_Availability'] else None,
          'attach_setup_success_rate': float(lines['Attach_Setup_Success_Rate']) if lines['Attach_Setup_Success_Rate'] else None,
          'rrc_setup_success_rate': float(lines['RRC_Setup_Success_Rate']) if lines['RRC_Setup_Success_Rate'] else None,
          'erab_setup_success_rate_ngbr': float(lines['eRAB_Setup_Success_Rate_nGBR']) if lines['eRAB_Setup_Success_Rate_nGBR'] else None,
          'volte_setup_success_rate_gbr': float(lines['VoLTE_Setup_Success_Rate_GBR']) if lines['VoLTE_Setup_Success_Rate_GBR'] else None,
          'call_drop_rate_erab_ngbr': float(lines['Call_Drop_Rate_eRAB_nGBR']) if lines['Call_Drop_Rate_eRAB_nGBR'] else None,
          'volte_call_drop_rate_erab_gbr': float(lines['VoLTE_Call_Drop_Rate_eRAB_GBR']) if lines['VoLTE_Call_Drop_Rate_eRAB_GBR'] else None,
          'hosr_intra_frequency': float(lines['HOSR_Intra_Frequency']) if lines['HOSR_Intra_Frequency'] else None,
          'hosr_inter_frequency': float(lines['HOSR_Inter_Frequency']) if lines['HOSR_Inter_Frequency'] else None,
          'x2_handover_out_success_rate': float(lines['X2_Handover_Out_Success_Rate']) if lines['X2_Handover_Out_Success_Rate'] else None,
          'x2_handover_in_success_rate': float(lines['X2_Handover_In_Success_Rate']) if lines['X2_Handover_In_Success_Rate'] else None,
          's1_handover_out_success_rate': float(lines['S1_Handover_Out_Success_Rate']) if lines['S1_Handover_Out_Success_Rate'] else None,
          's1_handover_in_success_rate': float(lines['S1_Handover_In_Success_Rate']) if lines['S1_Handover_In_Success_Rate'] else None,
          'dl_bler': float(lines['DL_BLER']) if lines['DL_BLER'] else None,
          'ul_bler': float(lines['UL_BLER']) if lines['UL_BLER'] else None,
        }

        obj, created = Statistic.objects.update_or_create(
          uid=uid,
          cellnum=cellnum,
          defaults=defaults
        )

        if created:
          created_count += 1
          self.stdout.write(f'Created new record for {uid}')
        else:
          update_count += 1
          self.stdout.write(f'Updated existing record for {uid}')
        self.stdout.write(f'Processed {processed_count} rows so far')

      all_site_lsm_info = Statistic.objects.all()

      for site_info in all_site_lsm_info:
        unique_id_db = site_info.uid
        if unique_id_db not in unique_ids_in_csv:
          site_info.sitestatus = 'Dismantled'
          site_info.save()

          self.stdout.write(f'Updated remark to dismantled for {unique_id_db}')
    self.stdout.write(self.style.SUCCESS('Successfully updated the database with CSV file'))