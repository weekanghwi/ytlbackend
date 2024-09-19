from django.core.management.base import BaseCommand, CommandError
import csv
from apiapp.models import SiteBasicinfo, Region, State, Cluster, ContractType, SiteConfig
from django.contrib.gis.geos import Point

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/sitebasicinfo.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        siteid = lines['siteid']
        sitename = lines['sitename']
        lat = lines['lat']
        lon = lines['lon']

        if not lat:
          lat = None
        if not lon:
          lon = None
                
        # ForeignKey fields
        region_id = lines['region']
        state_id = lines['state']
        cluster_id = lines['cluster']
        contracttype_id = lines['contracttype']
        siteconfig_id = lines['siteconfig']

        # point = None
        # if lat and lon:
        #   point = Point(float(lon), float(lat))

        SiteBasicinfo.objects.create(
          siteid=siteid,
          sitename=sitename,
          region_id=region_id,
          state_id=state_id,
          lat=lat,
          lon=lon,
          cluster_id=cluster_id,
          contracttype_id=contracttype_id,
          siteconfig_id=siteconfig_id
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
