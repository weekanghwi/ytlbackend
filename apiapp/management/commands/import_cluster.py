from django.core.management.base import BaseCommand
from apiapp.models import Cluster, Region
import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry

def get_first_polygon(geom):
    if geom.geom_type == 'MultiPolygon':
        return geom.geoms[0]
    return geom

class Command(BaseCommand):
  help = 'Import cluster data'

  def handle(self, *args, **kwargs):
    gdf = gpd.read_file(r'E:\webproject\backend_ytlproject\apibackend\Cluster_Boundary\Sarawak.tab')
    gdf['geometry'] = gdf['geometry'].apply(get_first_polygon)
    print(gdf)

    for index, row in gdf.iterrows():
      region = Region.objects.get(region='Sarawak')
      cluster_name = row['Area_Name'] # 가정: cluster_name이 gdf에 있는 필드
      polygon = GEOSGeometry(row['geometry'].wkt)
            
      cluster = Cluster(
        region=region,
        cluster=cluster_name,
        polygon=polygon
      )
      cluster.save()

    print("Import completed successfully")