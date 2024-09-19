from django.contrib.gis import admin
from .models import *

# Register your models here.
class ClusterAdmin(admin.OSMGeoAdmin):
  list_display = ['region', 'cluster']
  search_fields = ['cluster']

  # class Media:
  #   js = (
  #     'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js',
  #     'js/custom_clustermap.js',
  #   )


admin.site.register(Subcon)
admin.site.register(Region)
admin.site.register(State)
admin.site.register(ContractType)
admin.site.register(SiteConfig)
admin.site.register(AntennaType)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(COICApproveStatus)
admin.site.register(OPTType)
admin.site.register(OPTIssuetype)
admin.site.register(PIC)
admin.site.register(ReviewStatus)
admin.site.register(PACApproveStatus)
admin.site.register(FACApproveStatus)
admin.site.register(SSVIssuetype)
