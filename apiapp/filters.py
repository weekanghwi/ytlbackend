import django_filters
from django.db.models import Q, F, Value, FloatField, ExpressionWrapper
from django.db.models.functions import Radians, Sin, Cos, Sqrt, ATan2
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point, fromstr
from .models import *
from django.db.models import Subquery, OuterRef, Count, IntegerField, Exists
from math import radians
from urllib.parse import unquote

from .serializers import SiteLSMinfoPCIFilterSerializer
from .util.haversine_distance import haversine_distance
class CharFilterInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
  pass


#--------------------------------------------------------------------------------------------------
#All the Category or Type filters------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class StateFilter(django_filters.FilterSet):
  region =  django_filters.CharFilter(field_name='region__region', lookup_expr='icontains')
  class Meta:
    model = State
    fields = ['region']

#--------------------------------------------------------------------------------------------------
#Cluster filters-----------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class ClusterFilter(django_filters.FilterSet):
  cluster = django_filters.CharFilter(lookup_expr='icontains')
  region = django_filters.MultipleChoiceFilter(
    field_name='region',
    choices=[(1, 'Central'), (2, 'Northern'), (3, 'Southern'), (4, 'Eastern'), (5, 'Sabah'), (6, 'Sarawak')]
  )
  class Meta:
    model = Cluster
    fields = ['cluster', 'region']

#--------------------------------------------------------------------------------------------------
#Site PHYINFO Filter-------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SitePhyinfoFilter(django_filters.FilterSet):
  uid = django_filters.CharFilter(lookup_expr='exact')
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid')
  class Meta:
    model = SitePhyinfo
    fields = ['sitebasicinfo']

class SiteLSMinfoFilter(django_filters.FilterSet):
  siteid = django_filters.CharFilter(lookup_expr='icontains')
  uid = django_filters.CharFilter(lookup_expr='exact')
  class Meta:
    model = SiteLSMinfo
    fields = ['siteid']

class BTSManagerFilter(django_filters.FilterSet):
  # siteid = django_filters.CharFilter(lookup_expr='icontains')
  siteid = django_filters.CharFilter(method='filter_siteids')
  freqband = django_filters.CharFilter(lookup_expr='exact')
  region = django_filters.CharFilter(field_name='sitebasicinfo__region__region', lookup_expr='exact')
  class Meta:
    model = SiteLSMinfo
    fields = ['siteid' ,'freqband', 'region']

  def filter_siteids(self, queryset, name, value):
    if value:
      siteids = value.split(',')
      query = Q()
      for siteid in siteids:
        query |= Q(siteid__icontains=siteid)
      return queryset.filter(query)
    return queryset

#--------------------------------------------------------------------------------------------------
#SiteBasicinfo filters-----------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class NonpageSiteBasicinfoFilter(django_filters.FilterSet):
  siteid = django_filters.CharFilter(lookup_expr='icontains')
  region = django_filters.CharFilter(field_name='region__region', lookup_expr='exact')
  radius = django_filters.NumberFilter(method='filter_by_distance')

  class Meta:
    model = SiteBasicinfo
    fields = ['siteid', 'region', 'radius']

  def filter_by_distance(self, queryset, name, value):
    siteid = self.request.GET.get('siteid', None)
    search_siteinfo = SiteBasicinfo.objects.filter(siteid=siteid).first()

    if search_siteinfo:
      srid = 4326  # WGS84
      point = fromstr(f"POINT({search_siteinfo.lon} {search_siteinfo.lat})", srid=srid)
    else:
      return queryset

    radius = int(value) * 1000  # km to m
    queryset = SiteBasicinfo.objects.all()

    queryset = queryset.annotate(distance=Distance('point', point)).filter(distance__lte=radius)
    return queryset

class SitebasicinfoFilter(django_filters.FilterSet):
  q = django_filters.CharFilter(method='filter_q')
  cluster = django_filters.CharFilter(field_name='cluster__cluster', lookup_expr='icontains')
  region = CharFilterInFilter(field_name='region__region', lookup_expr='in')
  state = CharFilterInFilter(field_name='state__state', lookup_expr='in')
  contracttype = CharFilterInFilter(field_name='contracttype__contracttype', lookup_expr='in')
  siteconfig = CharFilterInFilter(field_name='siteconfig__siteconfig', lookup_expr='in')
  btsmanager_count = django_filters.CharFilter(method='filter_btsmanager_count')
  antennatypes = django_filters.CharFilter(method='filter_antennatypes')

  class Meta:
    model = SiteBasicinfo
    fields = []

  def filter_q(self, queryset, name, value):
    return queryset.filter(
      Q(siteid__icontains=value) | Q(sitename__icontains=value)
    )

  def __init__(self, *args, **kwargs):
    super(SitebasicinfoFilter, self).__init__(*args, **kwargs)
    self.queryset = self.queryset.annotate(
      btsmanager_count=Subquery(
        SiteLSMinfo.objects.filter(
          sitebasicinfo=OuterRef('pk')
        ).values('sitebasicinfo').annotate(
          cnt=Count('id')
        ).values('cnt'),
          output_field=IntegerField()
      )
    )

  def filter_btsmanager_count(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(btsmanager_count__isnull=True)
    elif value == 'Not Null':
      return queryset.filter(btsmanager_count__gte=1)
    else:
      return queryset
    # return queryset.filter(btsmanager_count=value)
  
  def filter_antennatypes(self, queryset, name, value):
    if value == 'Updated':
      return queryset.annotate(
        has_antenna_type=Exists(
          SitePhyinfo.objects.filter(
            sitebasicinfo=OuterRef('pk'),
            antennatype__isnull=False
          )
        )
      ).filter(has_antenna_type=True)
    elif value == 'Pending':
      return queryset.annotate(
        has_antenna_type=Exists(
          SitePhyinfo.objects.filter(
            sitebasicinfo=OuterRef('pk'),
            antennatype__isnull=False
          )
        )
      ).filter(has_antenna_type=False)
    else:
      return queryset
    
#--------------------------------------------------------------------------------------------------
#OPTReview filters---------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class OPTReviewFilter(django_filters.FilterSet):
  sitebasicinfo_id = django_filters.CharFilter(field_name='sitebasicinfo__id')
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  class Meta:
    model = OptReview
    fields = ['sitebasicinfo']

#--------------------------------------------------------------------------------------------------
#AllTable filters----------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class AllTableFilter(django_filters.FilterSet):
  sitebasicinfo_id = django_filters.CharFilter(field_name='sitebasicinfo__id')
  region = CharFilterInFilter(field_name='sitebasicinfo__region__region', lookup_expr='in')
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  contracttype = django_filters.CharFilter(method='filter_contracttype')

  #DO Filter
  doissuedate = django_filters.CharFilter(method='filter_date_field_do')
  codsubmitdate = django_filters.CharFilter(method='filter_date_field_do')
  codapprovedate = django_filters.CharFilter(method='filter_date_field_do')
  #Install Filter
  startdate = django_filters.CharFilter(method='filter_date_field_install')
  completedate  = django_filters.CharFilter(method='filter_date_field_install')
  integrationdate = django_filters.CharFilter(method='filter_date_field_install')
  integrationondate = django_filters.CharFilter(method='filter_date_field_install')
  oaairdate = django_filters.CharFilter(method='filter_date_field_install')
  coisubmitdate = django_filters.CharFilter(method='filter_date_field_install')
  coiapprovedate = django_filters.CharFilter(method='filter_date_field_install')
  coicsubmitdate = django_filters.CharFilter(method='filter_date_field_install')
  coicapprovestatus = CharFilterInFilter(field_name='install__coicapprovestatus__coicapprovestatus', lookup_expr='in')
  pnochotriggerdate = django_filters.CharFilter(method='filter_date_field_install')
  pnochocompletedate = django_filters.CharFilter(method='filter_date_field_install')
  #SSV Filter
  ssvstartdate = django_filters.CharFilter(method='filter_date_field_ssv')
  ssvcompletedate = django_filters.CharFilter(method='filter_date_field_ssv')
  ssvsubmitdate = django_filters.CharFilter(method='filter_date_field_ssv')
  bsreceivedate = django_filters.CharFilter(method='filter_date_field_ssv')
  bssubmitdate = django_filters.CharFilter(method='filter_date_field_ssv')
  bsapprovedate = django_filters.CharFilter(method='filter_date_field_ssv')
  ssvsubcon = CharFilterInFilter(field_name='ssv__ssvsubcon__subcon', lookup_expr='in')
  #OPT Filter
  optstartdate = django_filters.CharFilter(method='filter_date_field_opt')
  optcompletedate = django_filters.CharFilter(method='filter_date_field_opt')
  optsubmitdate = django_filters.CharFilter(method='filter_date_field_opt')
  optapprovedate = django_filters.CharFilter(method='filter_date_field_opt')
  opttype = CharFilterInFilter(field_name='optimization__opttype__opttype', lookup_expr='in')
  #Certification filter
  pacsubmitdate = django_filters.CharFilter(method='filter_date_field_certi')
  facsubmitdate = django_filters.CharFilter(method='filter_date_field_certi')
  pacapprovestatus = CharFilterInFilter(field_name='certification__pacapprovestatus__pacapprovestatus', lookup_expr='in')
  facapprovestatus = CharFilterInFilter(field_name='certification__facapprovestatus__facapprovestatus', lookup_expr='in')

  class Meta:
    model = AllTable
    fields = ['sitebasicinfo']
  
  def filter_contracttype(self, queryset, name, value):
    values = value.split(',')
    query = Q()
    for val in values:
      query |= Q(sitebasicinfo__contracttype__contracttype__icontains=val)
      return queryset.filter(query)
    
  def filter_date_field_do(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(**{f'do__{name}__isnull': True})
    elif value == 'Not Null':
      return queryset.filter(**{f'do__{name}__isnull': False})
    else:
      return queryset
  def filter_date_field_install(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(**{f'install__{name}__isnull': True})
    elif value == 'Not Null':
      return queryset.filter(**{f'install__{name}__isnull': False})
    else:
      return queryset
  def filter_date_field_ssv(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(**{f'ssv__{name}__isnull': True})
    elif value == 'Not Null':
      return queryset.filter(**{f'ssv__{name}__isnull': False})
    else:
      return queryset
  def filter_date_field_opt(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(**{f'optimization__{name}__isnull': True})
    elif value == 'Not Null':
      return queryset.filter(**{f'optimization__{name}__isnull': False})
    else:
      return queryset
  def filter_date_field_certi(self, queryset, name, value):
    if value == 'Null':
      return queryset.filter(**{f'certification__{name}__isnull': True})
    elif value == 'Not Null':
      return queryset.filter(**{f'certification__{name}__isnull': False})
    else:
      return queryset

#--------------------------------------------------------------------------------------------------
#TEST RESULT---------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class TestResultFilter(django_filters.FilterSet):
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  class Meta:
    model = TestResult
    fields = ['sitebasicinfo']

#--------------------------------------------------------------------------------------------------
#Statistic-----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class StatisticFailFilter(django_filters.FilterSet):
  region = django_filters.CharFilter(field_name='sitebasicinfo__region__region', lookup_expr='icontains')
  band = django_filters.CharFilter()
  class Meta:
    models = Statistic
    fields = ['band', 'region']

class StatisticDataFilter(django_filters.FilterSet):
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  secid = django_filters.CharFilter(field_name='sitephyinfo__uid', lookup_expr='icontains')
  region = django_filters.CharFilter(field_name='sitebasicinfo__region__region', lookup_expr='icontains')
  band = django_filters.CharFilter()
  class Meta:
    models = Statistic
    fields = ['sitebasicinfo', 'band', 'region']

class StatisticCalculatedFilter(django_filters.FilterSet):
  category = django_filters.CharFilter()
  region = django_filters.CharFilter(field_name='region__region', lookup_expr='icontains')
  band = django_filters.CharFilter()
  weeknum = django_filters.CharFilter()
  class Meta:
    models = StatisticCalculated
    fields = ['region']

class StatisticCalClusterFilter(django_filters.FilterSet):
  region = django_filters.CharFilter(field_name='region__region', lookup_expr='exact')
  band = django_filters.CharFilter()
  weeknum = django_filters.CharFilter()
  cluster = django_filters.CharFilter(lookup_expr='exact')
  class Meta:
    models = StatisticCalculatedCluster
    fields = ['region', 'band', 'weeknum', 'cluster']

class StatisticFilter(django_filters.FilterSet):
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  region = django_filters.CharFilter(field_name='sitebasicinfo__region__region', lookup_expr='exact')
  band = django_filters.CharFilter()
  cluster = django_filters.CharFilter(lookup_expr='icontains')
  cell_availability = django_filters.CharFilter(method='filter_dynamic')
  attach_setup_success_rate = django_filters.CharFilter(method='filter_dynamic')
  rrc_setup_success_rate = django_filters.CharFilter(method='filter_dynamic')
  erab_setup_success_rate_ngbr = django_filters.CharFilter(method='filter_dynamic')
  volte_setup_success_rate_gbr = django_filters.CharFilter(method='filter_dynamic')
  call_drop_rate_erab_ngbr = django_filters.CharFilter(method='filter_dynamic')
  volte_call_drop_rate_erab_gbr = django_filters.CharFilter(method='filter_dynamic')
  hosr_intra_frequency = django_filters.CharFilter(method='filter_dynamic')
  hosr_inter_frequency = django_filters.CharFilter(method='filter_dynamic')
  x2_handover_out_success_rate = django_filters.CharFilter(method='filter_dynamic')
  x2_handover_in_success_rate = django_filters.CharFilter(method='filter_dynamic')
  s1_handover_out_success_rate = django_filters.CharFilter(method='filter_dynamic')
  s1_handover_in_success_rate = django_filters.CharFilter(method='filter_dynamic')
  dl_bler = django_filters.CharFilter(method='filter_dynamic')
  ul_bler = django_filters.CharFilter(method='filter_dynamic')

  def filter_dynamic(self, queryset, name, value):
    operator = value[:2] if value[:2] in ['>=', '<='] else value[0]

    lookup_expr = ''
    if operator == '>=':
      lookup_expr = 'gte'
    elif operator == '<=':
      lookup_expr = 'lte'
    elif operator == '=':
      lookup_expr = 'exact'

    try:
      val = float(value.lstrip('>=<='))
    except ValueError:
      return queryset

    if lookup_expr:
      return queryset.filter(**{f"{name}__{lookup_expr}": val})
    else:
      return queryset


  class Meta:
    model = Statistic
    fields = ['band', 'region', 'year', 'weeknum']

class SamePCIFileter(django_filters.FilterSet):
  sitebasicinfo = django_filters.CharFilter(field_name='sitebasicinfo__siteid', lookup_expr='icontains')
  distance = django_filters.NumberFilter(method='filter_by_distance')
  earfcnul = django_filters.NumberFilter(field_name='earfchul')
  region = django_filters.CharFilter(field_name='sitebasicinfo__region__region', lookup_expr='exact')

  class Meta:
    model = SiteLSMinfo
    fields = ['sitebasicinfo', 'distance', 'earfcnul', 'region']

  def filter_by_distance(self, queryset, name, value):
    filtered_queryset = []
    for lsmdata in queryset:
      site = lsmdata.sitebasicinfo
      if site and site.lat and site.lon:
        nearby_sites = queryset.filter(
          ~Q(id=lsmdata.id),
          sitebasicinfo__lat__isnull=False,
          sitebasicinfo__lon__isnull=False,
        ).annotate(
          distance=haversine_distance(
            float(site.lat), float(site.lon),
            'sitebasicinfo__lat', 'sitebasicinfo__lon'
          )
        ).filter(distance__lte=value)

        if nearby_sites:
          filtered_queryset.append(lsmdata)

    return queryset.filter(id__in=[obj.id for obj in filtered_queryset])
    



