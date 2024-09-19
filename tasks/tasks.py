from celery import shared_task
from apibackend.celery import app
from django.core.cache import cache
from apiapp.models import SiteLSMinfo, SiteBasicinfo, SitePhyinfo, AntennaType
from apiapp.serializers import SiteLSMinfoPCIFilterSerializer
from apiapp.views import FilterSamePCISitesAPIView
from apiapp.util.haversine_distance import haversine_distance

import pandas as pd


@app.task
def run_filter_same_pci_sites_task():
  radius = 10.0
  cache_key = f'filtered_results_radius_{radius}'

  lsmdata_queryset = SiteLSMinfo.objects.select_related('sitebasicinfo').filter(sitestatus="OnAir").all()
  view = FilterSamePCISitesAPIView()

  filtered_results = view.get_filtered_results(lsmdata_queryset, radius)

  cache.set(cache_key, filtered_results, timeout=82800)

@shared_task
def process_file(file_path, username):
  try:
    if file_path.endswith('xlsx'):
      df = pd.read_excel(file_path)
    elif file_path.endswith('csv'):
      df = pd.read_csv(file_path)

    required_columns = ['LTE_Site_ID', 'Port_Num', 'LTE_Sec_ID', 'Band', 'Antenna_Type', 'Height', 'Azimuth', 'M_Tilt', 'E_Tilt']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
      return {'error': f'Missing required columns: {", ".join(missing_columns)}'}
    
    for _, row in df.iterrows():
      sitebasicinfo, _ = SiteBasicinfo.objects.get_or_create(siteid=row['LTE_Site_ID'])
      antenna_type, _ = AntennaType.objects.get_or_create(antennatype=row['Antenna_Type'])

      SitePhyinfo.objects.update_or_create(
        sitebasicinfo=sitebasicinfo,
        portnum=row['Port_Num'],
        defaults={
          'secid': row['LTE_Sec_ID'],
          'band': row['Band'],
          'antennatype': antenna_type,
          'antennaheight': row['Height'],
          'azimuth': row['Azimuth'],
          'mtilt': row['M_Tilt'],
          'etilt': row['E_Tilt'],
          'modified_by': username
        }
      )

    return {'message': 'File processed successfully'}

  except Exception as e:
    return {'error': str(e)}
