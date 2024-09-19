from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from .util.haversine_distance import haversine_distance

#public key change from foregionkey to string-----------------------------------------------------
class ForeignKeyAsStringMixin:
  foreign_key_fields = {}

  def to_representation(self, instance):
    ret = super().to_representation(instance)
    for field, attr in self.foreign_key_fields.items():
      foreign_instance = getattr(instance, field)
      ret[field] = getattr(foreign_instance, attr) if foreign_instance else None
    return ret
  
  def to_internal_value(self, data):
    for field, attr in self.foreign_key_fields.items():
      if field in data:
        value = data[field]
        if value is not None:
          model_class = self.fields[field].queryset.model
          try:
            data[field] = model_class.objects.get(**{attr: value}).id
          except model_class.DoesNotExist:
            raise serializers.ValidationError({field: f'{value} does not exist'})
        else:
          data[field] = None
    return super().to_internal_value(data)

#--------------------------------------------------------------------------------------------------
#Region & State------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class RegionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Region
    fields = '__all__'

class StateSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = State
    fields = '__all__'
  foreign_key_fields = {
    'region': 'region',
  }

class ContractTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = ContractType
    fields = '__all__'

class SiteConfigSerializer(serializers.ModelSerializer):
  class Meta:
    model = SiteConfig
    fields = '__all__'

class AntennaTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = AntennaType
    fields = '__all__'

class SubconSerializer(serializers.ModelSerializer):
  class Meta:
    model = Subcon
    fields = '__all__'

class COICapproveStatusSerializer(serializers.ModelSerializer):
  class Meta:
    model = COICApproveStatus
    fields = '__all__'

class SSVIssueSerializer(serializers.ModelSerializer):
  class Meta:
    model = SSVIssuetype
    fields = '__all__'

class OPTTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = OPTType
    fields = '__all__'

class OPTIssueSerializer(serializers.ModelSerializer):
  class Meta:
    model = OPTIssuetype
    fields = '__all__'

class PICSerializer(serializers.ModelSerializer):
  class Meta:
    model = PIC
    fields = '__all__'

class ReviewStatusSerializer(serializers.ModelSerializer):
  class Meta:
    model = ReviewStatus
    fields = '__all__'
  
class PACApproveStatusSerializer(serializers.ModelSerializer):
  class Meta:
    model = PACApproveStatus
    fields = '__all__'

class FACApproveStatusSerializer(serializers.ModelSerializer):
  class Meta:
    model = FACApproveStatus
    fields = '__all__' 

#--------------------------------------------------------------------------------------------------
#Cluster-------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class ClusterSerializer(serializers.ModelSerializer):
  class Meta:
    model = Cluster
    fields = '__all__'
  # foreign_key_fields = {
  #   'cluster': 'cluster'
  # }

#--------------------------------------------------------------------------------------------------
#Site BTS Manager info-----------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SitePhyinfoSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = SitePhyinfo
    fields = '__all__'
    extra_kwargs = {'modified_by': {'read_only': False}}
  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
    'antennatype': 'antennatype',
  }

class SiteLSMinfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = SiteLSMinfo
    fields = '__all__'

class SiteRETinfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = SiteRETinfo
    fields = '__all__'

class SiteTXinfoSerializer(serializers.ModelSerializer):
  class Meta:
    model = SiteTXattninfo
    fields = '__all__'

class BTSManagerSerializer(serializers.ModelSerializer):
  baseinfo = serializers.SerializerMethodField()
  phyinfo = serializers.SerializerMethodField()
  retinfo = serializers.SerializerMethodField()
  txinfo = serializers.SerializerMethodField()
  etilt = serializers.SerializerMethodField()
  angle = serializers.SerializerMethodField()
  radius = serializers.SerializerMethodField()
  lat = serializers.SerializerMethodField()
  lon = serializers.SerializerMethodField()

  class Meta:
    model = SiteLSMinfo
    fields = '__all__'
  
  def get_lat(self, obj: SiteLSMinfo) -> float:
    try:
      sitebasicinfo = SiteBasicinfo.objects.get(siteid=obj.sitebasicinfo)
      return sitebasicinfo.lat
    except SitePhyinfo.DoesNotExist:
      return {}
  
  def get_lon(self, obj: SiteLSMinfo) -> float:
    try:
      sitebasicinfo = SiteBasicinfo.objects.get(siteid=obj.sitebasicinfo)
      return sitebasicinfo.lon
    except SiteLSMinfo.DoesNotExist:
      return {}
  
  def get_angle(self, obj: SiteLSMinfo) -> float:
    try:
      phyinfo = SitePhyinfo.objects.get(uid=obj.uid)
      antennatype = phyinfo.antennatype
      freqband = obj.freqband

      if antennatype == 'Omni':
        return 360
      elif antennatype == 'Indoor':
        return 360
      elif freqband == 20:
        return 15
      elif freqband == 38:
        return 30
      else:
        return 60
    except SitePhyinfo.DoesNotExist:
      return 0 
  
  def get_radius(self, obj: SiteLSMinfo) -> float:
    try:
      freqband = obj.freqband
      if freqband == 20:
        return 0.18
      elif freqband == 38:
        return 0.14
      elif freqband == 40:
        return 0.1
      else:
        return 0.0
    except SitePhyinfo.DoesNotExist:
      return 0.0
  
  def get_baseinfo(self, obj: SiteLSMinfo) -> dict:
    try:
      baseinfo = SiteBasicinfo.objects.get(siteid=obj.siteid)
      return {
        'region': baseinfo.region.region,
        'cluster': baseinfo.cluster.cluster,
        'contracttype': baseinfo.contracttype.contracttype,
        'lat': baseinfo.lat,
        'lon': baseinfo.lon,
      }
    except SiteBasicinfo.DoesNotExist:
      return {}

  def get_phyinfo(self, obj: SiteLSMinfo) -> dict:
    try:
      phyinfo = SitePhyinfo.objects.get(uid=obj.uid)
      return {
        'id': phyinfo.id,
        'uid': phyinfo.uid,
        'secid': phyinfo.secid,
        'portnum': phyinfo.portnum,
        'antennatype': phyinfo.antennatype.antennatype,
        'antennaheight': phyinfo.antennaheight,
        'azimuth': phyinfo.azimuth,
        'mtilt': phyinfo.mtilt,
        'etilt': phyinfo.etilt,
        'modifyat': phyinfo.modify_at,
        'modifyby': phyinfo.modified_by
      }
    except SitePhyinfo.DoesNotExist:
      return {}
  
  def get_retinfo(self, obj: SiteLSMinfo) -> dict:
    try:
      retinfo = SiteRETinfo.objects.filter(uid=obj.uid).first()
      if retinfo is not None:
        return {
          'ret': retinfo.tilt / 10
        }
      else:
        return {}
    except SiteRETinfo.DoesNotExist:
      return {}
    
  def get_txinfo(self, obj: SiteLSMinfo) -> dict:
    try:
      txinfo = SiteTXattninfo.objects.filter(uid=obj.uid).first()
      if txinfo is not None:
        return {
          'txattn': txinfo.txattn
        }
      else:
        return {}
    except SiteTXattninfo.DoesNotExist:
      return {}
  
  def get_etilt(self, obj: SiteLSMinfo) -> float:
    try:
      phyinfo = SitePhyinfo.objects.get(uid=obj.uid)
      retinfo = SiteRETinfo.objects.filter(uid=obj.uid).first()

      if retinfo is not None:
        ret_etilt = retinfo.tilt / 10
        phy_etilt = phyinfo.etilt

        if ret_etilt == phy_etilt:
          return phy_etilt
        else:
          return ret_etilt
      else:
        return phyinfo.etilt
    except (SitePhyinfo.DoesNotExist, SiteRETinfo.DoesNotExist):
      return None

class MissingSiteIDSerializer(serializers.Serializer):
    siteid = serializers.CharField(max_length=15)

    def to_representation(self, instance):
        missing_siteids = SiteBasicinfo.get_missing_siteids()
        return {'missing_siteids': missing_siteids}


#--------------------------------------------------------------------------------------------------
#SiteBasicinfo-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SitebasicinfoSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  lat = serializers.DecimalField(max_digits=20, decimal_places=15)
  lon = serializers.DecimalField(max_digits=20, decimal_places=15)
  btsmanager_count = serializers.SerializerMethodField()
  antennatypes = serializers.SerializerMethodField()

  class Meta:
    model = SiteBasicinfo
    fields = [f.name for f in SiteBasicinfo._meta.fields]
    fields.append('btsmanager_count')
    fields.append('antennatypes')
    # fields = [
    #         'siteid', 'sitename', 'region', 'state', 'lat', 'lon', 'point',
    #         'cluster', 'contracttype', 'siteconfig', 'create_at', 'modify_at',
    #         'btsmanager_count', 'antennatypes'
    #     ]


  foreign_key_fields = {
    'region': 'region',
    'state': 'state',
    'cluster': 'cluster',
    'contracttype': 'contracttype',
    'siteconfig': 'siteconfig'
  }

  def get_btsmanager_count(self, obj: SiteBasicinfo) -> int:
    return SiteLSMinfo.objects.filter(sitebasicinfo=obj).count()
  
  def get_antennatypes(self, obj: SiteBasicinfo) -> str:
    phyinfo = SitePhyinfo.objects.filter(sitebasicinfo=obj, antennatype__isnull=False).first()
    return "Updated" if phyinfo else "Pending"

class SiteLSMinfoPCIFilterSerializer(serializers.ModelSerializer):
  sitebasicinfo = serializers.CharField(source='sitebasicinfo.siteid')
  region = serializers.CharField(source='sitebasicinfo.region.region')
  class Meta:
    model = SiteLSMinfo
    fields = ['sitebasicinfo', 'pci', 'earfcnul', 'region']
  
  # nearby_sites = serializers.SerializerMethodField()

  # def get_nearby_sites(self, obj):
  #   request = self.context.get('request')
  #   radius = float(request.query_params.get('radius', 10)) if request else 10
  #   lsmdata_queryset = SiteLSMinfo.objects.filter(earfcnul=obj.earfcnul, pci=obj.pci).exclude(id=obj.id)
  #   nearby_sites = []

  #   for other_lsmdata in lsmdata_queryset:
  #     other_site = other_lsmdata.sitebasicinfo
  #     if other_site and other_site.lat and other_site.lon:
  #       distance = haversine_distance(float(obj.sitebasicinfo.lat), float(obj.sitebasicinfo.lon), float(other_site.lat), float(other_site.lon))
  #       if distance <= radius:
  #         nearby_sites.append({
  #           'site': SiteLSMinfoPCIFilterSerializer(other_lsmdata, context={'request': request}).data,
  #           'distance': distance
  #         })
  #   return nearby_sites


#--------------------------------------------------------------------------------------------------
#Material------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class MaterialSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = Material
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid'
  }

#--------------------------------------------------------------------------------------------------
#DO------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class DOSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = DO
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid'
  }

#--------------------------------------------------------------------------------------------------
#Install-------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class InstallSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = Install
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
    'coicapprovestatus': 'coicapprovestatus'
  }

#--------------------------------------------------------------------------------------------------
#SSV-----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SSVSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = SSV
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
    'ssvsubcon': 'subcon',
    'ssvissuetype': 'ssvissuetype'
  }

#--------------------------------------------------------------------------------------------------
#Optimization--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class OptimizationSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = Optimization
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
    'opttype': 'opttype',
    'optsubcon': 'subcon',
    'optissuetype': 'optissuetype'
  }

class OPTReviewSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = OptReview
    fields = '__all__'
  foreign_key_fields ={
    'sitebasicinfo': 'siteid',
    'pic': 'pic',
    'reviewstatus': 'reviewstatus'
  }

#--------------------------------------------------------------------------------------------------
#Certi---------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class CertificationSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = Certification
    fields = '__all__'
  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
    'pacapprovestatus': 'pacapprovestatus',
    'facapprovestatus': 'facapprovestatus'
  }

#--------------------------------------------------------------------------------------------------
#AllTable------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class AllTableSerializer(serializers.ModelSerializer):
  sitebasicinfo = SitebasicinfoSerializer()
  material = MaterialSerializer()
  do = DOSerializer()
  install = InstallSerializer()
  ssv = SSVSerializer()
  optimization = OptimizationSerializer()
  certification = CertificationSerializer()
  class Meta:
    model = AllTable
    fields = '__all__'

#FDD Master tracker to CSV ------------------------------------------------------------------------
class AllTableCSVSerializer(serializers.ModelSerializer):
  siteid = serializers.CharField(source='sitebasicinfo.siteid')
  sitename = serializers.CharField(source='sitebasicinfo.sitename')
  cluster = serializers.CharField(source='sitebasicinfo.cluster')
  contract_type = serializers.CharField(source='sitebasicinfo.contracttype')
  region = serializers.CharField(source='sitebasicinfo.region')
  opt_category = serializers.CharField(source='optimization.opttype')
  lat = serializers.CharField(source='sitebasicinfo.lat')
  lon = serializers.CharField(source='sitebasicinfo.lon')
  # do_info = serializers.SerializerMethodField()
  dodate = serializers.CharField(source='do.doissuedate')
  codsubmit = serializers.CharField(source='do.codsubmitdate')
  codapprove = serializers.CharField(source='do.codapprovedate')
  install_start = serializers.CharField(source='install.startdate')
  install_complete = serializers.CharField(source='install.completedate')
  integration = serializers.CharField(source='install.integrationdate')
  integration_turnon = serializers.CharField(source='install.integrationondate')
  onair = serializers.CharField(source='install.oaairdate')
  coisubmit = serializers.CharField(source='install.coisubmitdate')
  coiapprove = serializers.CharField(source='install.coiapprovedate')
  coicsubmit = serializers.CharField(source='install.coicsubmitdate')
  coicapprove = serializers.CharField(source='install.coicapprovestatus')
  pnoc_trigger = serializers.CharField(source='install.pnochotriggerdate')
  pnoc_complete = serializers.CharField(source='install.pnochocompletedate')
  ssv_start = serializers.CharField(source='ssv.ssvstartdate')
  ssv_complete = serializers.CharField(source='ssv.ssvcompletedate')
  ssv_submit = serializers.CharField(source='ssv.ssvsubmitdate')
  bs_receive = serializers.CharField(source='ssv.bsreceivedate')
  bs_submit = serializers.CharField(source='ssv.bssubmitdate')
  bs_approve = serializers.CharField(source='ssv.bsapprovedate')
  opt_start = serializers.CharField(source='optimization.optstartdate')
  opt_complete = serializers.CharField(source='optimization.optcompletedate')
  opt_submit = serializers.CharField(source='optimization.optsubmitdate')
  opt_approve = serializers.CharField(source='optimization.optapprovedate')
  pac_submit = serializers.CharField(source='certification.pacsubmitdate')
  fac_submit = serializers.CharField(source='certification.facsubmitdate')
  pac_approve = serializers.CharField(source='certification.pacapprovestatus')
  fac_approve = serializers.CharField(source='certification.facapprovestatus')
  ssv_subcon = serializers.CharField(source='ssv.ssvsubcon')
  opt_subcon = serializers.CharField(source='optimization.optsubcon')

  class Meta:
    model = AllTable
    fields = [
      'siteid', 'sitename', 'cluster', 'contract_type', 'region', 'opt_category', 'lat', 'lon',
      'do_info',
      # 'dodate', 'codsubmit', 'codapprove',
      'install_start', 'install_complete', 'integration', 'integration_turnon', 'onair', 'coisubmit', 'coiapprove', 'coicsubmit', 'coicapprove', 'pnoc_trigger', 'pnoc_complete',
      'ssv_start', 'ssv_complete', 'ssv_submit', 'bs_receive', 'bs_submit', 'bs_approve',
      'opt_start', 'opt_complete', 'opt_submit', 'opt_approve',
      'pac_submit', 'fac_submit', 'pac_approve', 'fac_approve', 'ssv_subcon', 'opt_subcon'
    ]

    # def get_do_info(self, obj):
    #   return {
    #     'oddate': obj.do.doissuedate,
    #     'codsubmit': obj.do.codsubmitdate,
    #     'codapprove': obj.do.codapprovedate,
    #   }


#--------------------------------------------------------------------------------------------------
#TEST RESULT (POOR SINR)---------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class TestResultSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = TestResult
    fields = '__all__'

  foreign_key_fields = {
      'sitebasicinfo': 'siteid',
    }
  
#--------------------------------------------------------------------------------------------------
#Register------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ['username', 'password', 'email']
    extra_kwargs = {'password': {'write_only': True}}

  def validate_username(self, value):
    if User.objects.filter(username=value).exists():
      raise serializers.ValidationError('Username already exists')
    return value
  
  def validate_email(self, value):
    if User.objects.filter(email=value).exists():
      raise serializers.ValidationError('Email already exists')
    return value
  
#--------------------------------------------------------------------------------------------------
#Statistic-----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class StatisticSerializer(serializers.ModelSerializer):
  sitebasicinfo_details = SitebasicinfoSerializer(source='sitebasicinfo', read_only=True)
  sitephyinfo_details = SitePhyinfoSerializer(source='sitephyinfo', read_only=True)

  class Meta:
    model = Statistic
    fields = '__all__'

  foreign_key_fields = {
    'sitebasicinfo': 'siteid',
  }

class SitebasicStatisticSerializer(serializers.ModelSerializer):
  class Meta:
    model = SiteBasicinfo
    fields = ['siteid', 'lat', 'lon', 'region']
  
class SitephyinfoStatisticSerializer(serializers.ModelSerializer):
  class Meta:
    model = SitePhyinfo
    fields = ['uid', 'secid',  'azimuth', 'mtilt']

class RegioninfoStatisticSerializer(serializers.ModelSerializer):
  class Meta:
    model = Region
    fields = ['region']

class StatisticDataSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  sitebasicinfo_details = SitebasicStatisticSerializer(source='sitebasicinfo', read_only=True)
  sitephyinfo_details = SitephyinfoStatisticSerializer(source='sitephyinfo', read_only=True)
  regioninfo_details = RegioninfoStatisticSerializer(source='region', read_only=True)
  class Meta:
    model = StatisticData
    fields = '__all__'
  
  foreign_key_fields = {
    'region': 'region',
  }

class StatisticDataPRBDLHeatmapSerializer(serializers.ModelSerializer):
  lat = serializers.FloatField(source='sitebasicinfo.lat')
  lon = serializers.FloatField(source='sitebasicinfo.lon')

  class Meta:
    model = StatisticData
    fields = ['lat', 'lon', 'totalprbdl']

class StatisticDataClusterSerializer(serializers.ModelSerializer):
  attach_setup_success_rate = serializers.FloatField()
  class Meta:
    model = StatisticData
    fields = ['region', 'cluster', 'band', 'attach_setup_success_rate']
  

class StatisticCalculatedSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = StatisticCalculated
    fields = '__all__'

  foreign_key_fields = {
    'region': 'region',
  }

class StatisticCalClusterSerializer(ForeignKeyAsStringMixin, serializers.ModelSerializer):
  class Meta:
    model = StatisticCalculatedCluster
    fields = '__all__'
  
  foreign_key_fields = {
    'region': 'region',
  }
  # def to_representation(self, instance):
  #   ret = super().to_representation(instance)
  #   field = self.context['request'].query_params.get('field')
  #   if field:
  #     return {field: ret[field], 'region': ret['region'], 'cluster': ret['cluster'], 'weeknum': ret['weeknum'], 'band': ret['band']}
  #   return ret

class StatisticDynamicFieldSerializer(serializers.ModelSerializer):
  sitebasicinfo_details = SitebasicStatisticSerializer(source='sitebasicinfo', read_only=True)
  sitephyinfo_details = SitephyinfoStatisticSerializer(source='sitephyinfo', read_only=True)
  class Meta:
    model = Statistic
    fields = '__all__'

  def __init__(self, *args, **kwargs):
    fields = kwargs.pop('fields', None)
    super(StatisticDynamicFieldSerializer, self).__init__(*args, **kwargs)

    if fields is not None:
      allowed = set(fields)
      allowed.add('sitebasicinfo_details')
      allowed.add('sitephyinfo_details') 
      existing = set(self.fields)
      for field_name in existing - allowed:
        self.fields.pop(field_name)


class AlarmDataSerializer(serializers.ModelSerializer):
  sitebasicinfo = SitebasicinfoSerializer()
  class Meta:
    model = AlarmData
    fields = '__all__'
