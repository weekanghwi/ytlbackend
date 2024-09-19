
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Count, Avg, Q, Sum, Case, When, FloatField, ExpressionWrapper, Max, Prefetch
from django.db.models.functions import Coalesce
from django.http import StreamingHttpResponse
from django.db import transaction
from django.contrib.auth.models import User
from django.core.cache import cache

from simplekml import Kml, AltitudeMode
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import action

from .models import *
from .serializers import *
from .filters import *
from datetime import datetime, timedelta
from .util.haversine_distance import haversine_distance
from collections import defaultdict

import csv
import pandas as pd
import math


class CustomLimitOffsetPagination(LimitOffsetPagination):
  default_limit = 50

class CustomLimitOffsetPaginationten(LimitOffsetPagination):
  default_limit = 20

class CustomPagination(LimitOffsetPagination):
  def get_paginated_response(self, data, cluster_total):
    return Response({
      'links': {
        'next': self.get_next_link(),
        'previous': self.get_previous_link()
      },
      'count': self.count,
      'cluster_total': cluster_total,
      'results': data
    })

#--------------------------------------------------------------------------------------------------
#All the Category or Type--------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class RegionListAPIView(ListAPIView):
  queryset = Region.objects.all()
  serializer_class = RegionSerializer
  pagination_class = CustomLimitOffsetPagination

class StateListAPIView(ListAPIView):
  queryset = State.objects.all()
  serializer_class = StateSerializer
  filter_backends = [DjangoFilterBackend]
  filterset_class = StateFilter
  pagination_class = CustomLimitOffsetPagination

class ContractTypeListAPIView(ListAPIView):
  queryset = ContractType.objects.all()
  serializer_class = ContractTypeSerializer
  pagination_class = CustomLimitOffsetPagination

class SiteConfigListAPIView(ListAPIView):
  queryset = SiteConfig.objects.all()
  serializer_class = SiteConfigSerializer
  pagination_class = CustomLimitOffsetPagination

class AntennaTypeListAPIView(ListAPIView):
  queryset = AntennaType.objects.all()
  serializer_class = AntennaTypeSerializer
  pagination_class = CustomLimitOffsetPagination

class SubconListAPIView(ListAPIView):
  queryset = Subcon.objects.all()
  serializer_class = SubconSerializer
  pagination_class = CustomLimitOffsetPagination

class COICapproveStatusListAPIView(ListAPIView):
  queryset = COICApproveStatus.objects.all()
  serializer_class = COICapproveStatusSerializer
  pagination_class = CustomLimitOffsetPagination

class SSVIssueListAPIView(ListAPIView):
  queryset = SSVIssuetype.objects.all()
  serializer_class = SSVIssueSerializer
  pagination_class = CustomLimitOffsetPagination

class OPTTypeListAPIView(ListAPIView):
  queryset = OPTType.objects.all()
  serializer_class = OPTTypeSerializer
  pagination_class = CustomLimitOffsetPagination

class OPTIssueListAPIView(ListAPIView):
  queryset = OPTIssuetype.objects.all()
  serializer_class = OPTIssueSerializer
  pagination_class = CustomLimitOffsetPagination

class PICListAPIView(ListAPIView):
  queryset = PIC.objects.all()
  serializer_class = PICSerializer
  pagination_class = CustomLimitOffsetPagination

class OPTReviewStatusAPIView(ListAPIView):
  queryset = ReviewStatus.objects.all()
  serializer_class = ReviewStatusSerializer
  pagination_class = CustomLimitOffsetPagination

class PACApproveStatusListAPIView(ListAPIView):
  queryset = PACApproveStatus.objects.all()
  serializer_class = PACApproveStatusSerializer
  pagination_class = CustomLimitOffsetPagination

class FACApproveStatusListAPIView(ListAPIView):
  queryset = FACApproveStatus.objects.all()
  serializer_class = FACApproveStatusSerializer
  pagination_class = CustomLimitOffsetPagination

#--------------------------------------------------------------------------------------------------
#Cluster-------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class ClusterViewSet(viewsets.ModelViewSet):
  queryset = Cluster.objects.all()
  serializer_class = ClusterSerializer
  pagination_class = CustomLimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = ClusterFilter

#--------------------------------------------------------------------------------------------------
#Site BTS MANAGER----------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SitePhyinfoViewSet(viewsets.ModelViewSet):
  queryset = SitePhyinfo.objects.all()
  serializer_class = SitePhyinfoSerializer
  pagination_class = LimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = SitePhyinfoFilter
  pagination_class = CustomLimitOffsetPagination

class SiteLSMinfoViewSet(viewsets.ModelViewSet):
  queryset = SiteLSMinfo.objects.all()
  serializer_class = SiteLSMinfoSerializer
  pagination_class = LimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = SiteLSMinfoFilter

class SiteRETinfoViewSet(viewsets.ModelViewSet):
  queryset = SiteRETinfo.objects.all()
  serializer_class = SiteRETinfoSerializer
  pagination_class = CustomLimitOffsetPagination

class SiteTXinfoViewSet(viewsets.ModelViewSet):
  queryset = SiteTXattninfo.objects.all()
  serializer_class = SiteTXinfoSerializer
  pagination_class = CustomLimitOffsetPagination

class BTSManagerViewSet(viewsets.ModelViewSet):
  queryset = SiteLSMinfo.objects.exclude(sitestatus='Dismantled').all().order_by('cellidentity')
  serializer_class = BTSManagerSerializer
  filter_backends = [DjangoFilterBackend]
  filterset_class = BTSManagerFilter
  pagination_class = CustomLimitOffsetPaginationten

class NonPageBTSManagerListAPIView(ListAPIView):
  queryset = SiteLSMinfo.objects.all()
  serializer_class = BTSManagerSerializer
  pagination_class = None
  filter_backends = [DjangoFilterBackend]
  filterset_class = BTSManagerFilter

def BTSManager_KML(request):
  def calculate_fan_coordinates(x_center, y_center, radius, angle, azimuth):
    coords = [(x_center, y_center)]
    for theta in range(0, int(angle) + 1):
      theta_rad = math.radians(theta + azimuth)
      x = float(x_center) + radius * math.cos(theta_rad)
      y = float(y_center) + radius * math.sin(theta_rad)
      coords.append((x, y))
    coords.append((x_center, y_center))
    return coords
  
  def stream():
    
    kml = Kml()

    for i, siteinfo in enumerate(SiteLSMinfo.objects.all()):
      serializer = BTSManagerSerializer(siteinfo)
      serialized_data = serializer.data

      angle = serialized_data.get('angle', 0)
      radius = serialized_data.get('radius', 0)
      azimuth = serialized_data['phyinfo'].get('azimuth', 0)
      latitude = serialized_data.get('lat', 0)
      longitude = serialized_data.get('lon', 0)

      coords = calculate_fan_coordinates(longitude, latitude, radius, angle, azimuth)

      pol = kml.newpolygon(name='BTSManager', outerboundaryis=coords)
      pol.altitudemode = AltitudeMode.relativetoground

      yield f'data: {i+1}/{SiteLSMinfo.objects.count()}\n\n'
    kml.save('site.kml')
    yield 'data: done\n\n'
  return StreamingHttpResponse(stream(), content_type='text/event-stream')

class PendingCreateSitebasicinfoView(viewsets.ModelViewSet):
  queryset = SiteLSMinfo.objects.filter(sitebasicinfo__isnull=True)
  serializer_class = SiteLSMinfoSerializer
  pagination_class = CustomLimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = SiteLSMinfoFilter

#--------------------------------------------------------------------------------------------------
#Sitebasicinfo-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SitebasicinfoViewSet(viewsets.ModelViewSet):
  queryset = SiteBasicinfo.objects.all().order_by('-id')
  serializer_class = SitebasicinfoSerializer
  pagination_class = LimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = SitebasicinfoFilter

class NonpageSitebasicinfoListAPIView(ListAPIView):
  queryset = SiteBasicinfo.objects.all()
  serializer_class = SitebasicinfoSerializer
  pagination_class = None
  filter_backends = [DjangoFilterBackend]
  filterset_class = NonpageSiteBasicinfoFilter


#--------------------------------------------------------------------------------------------------
#DO------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class MaterialViewSet(viewsets.ModelViewSet):
  queryset = Material.objects.all().order_by('-id')
  serializer_class = MaterialSerializer
  pagination_class = LimitOffsetPagination

class DOViewSet(viewsets.ModelViewSet):
  queryset = DO.objects.all().order_by('-id')
  serializer_class = DOSerializer

#--------------------------------------------------------------------------------------------------
#Install-------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class InstallViewSet(viewsets.ModelViewSet):
  queryset = Install.objects.all().order_by('-id')
  serializer_class = InstallSerializer

#--------------------------------------------------------------------------------------------------
#SSV-----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SSVViewSet(viewsets.ModelViewSet):
  queryset = SSV.objects.all().order_by('-id')
  serializer_class = SSVSerializer

#--------------------------------------------------------------------------------------------------
#Optimization-----------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class OptimizationViewSet(viewsets.ModelViewSet):
  queryset = Optimization.objects.all().order_by('-id')
  serializer_class = OptimizationSerializer

class OPTReviewViewSet(viewsets.ModelViewSet):
  queryset = OptReview.objects.all()
  serializer_class = OPTReviewSerializer
  filter_backends = [DjangoFilterBackend]
  filterset_class = OPTReviewFilter

#--------------------------------------------------------------------------------------------------
#Certification-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class CertificationViewSet(viewsets.ModelViewSet):
  queryset = Certification.objects.all().order_by('-id')
  serializer_class = CertificationSerializer

#--------------------------------------------------------------------------------------------------
#Certification-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class AllRelateTableViewSet(viewsets.ModelViewSet):
  queryset = AllTable.objects.all().order_by('-id')
  serializer_class = AllTableSerializer
  pagination_class = LimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = AllTableFilter

#--------------------------------------------------------------------------------------------------
#Daily Report export to csv------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
def Export_FDDMasterTracker_csv(request):
  queryset = AllTable.objects.filter(sitebasicinfo__contracttype__in=[1,2,3,7]).select_related(
    'sitebasicinfo', 'do', 'install', 'ssv', 'optimization', 'certification'
  )

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="FDD Master Tracker.csv"'

  writer = csv.writer(response)
  writer.writerow(
    ['Site ID', 'Site Name', 'Cluster', 'Contrac-Type', 'Region', 'OPT-Type', 'Lat', 'Lat', 'DO-Date', 'COD Submit Date', 'COD Approve Date',
     'Install Start Date', 'Install Complete Date', 'Integration Date', 'Integrateion TurnOn Date', 'OnAir Date', 'COI Submit Date', 'COI Approve Date',
     'COI&C Submit Date', 'COI&C Approve Date', 'PNOC HO Trigger Date', 'PNOC HO Complete Date', 'SSV Start Date', 'SSV Complete Date',
     'SSV Submit Date', 'BS Receive Date', 'BS Submit Date', 'BS Approve Date', 'OPT Start Date', 'OPT Complete Date', 'OPT Submit Datae', 'OPT Approve Date',
     'PAC Submit Date', 'FAC Submit Date', 'PAC Approve Status', 'FAC Approve Status', 'SSV Subcon', 'OPT Subcon']
  )

  for obj in queryset:
    siteid = obj.sitebasicinfo.siteid
    sitename = obj.sitebasicinfo.sitename
    cluster = obj.sitebasicinfo.cluster
    contracttype = obj.sitebasicinfo.contracttype
    region = obj.sitebasicinfo.region.region
    opttype = obj.optimization.opttype if obj else ''
    lat = obj.sitebasicinfo.lat
    lon = obj.sitebasicinfo.lon
    dodate = obj.do.doissuedate
    codsubmitdate = obj.do.codsubmitdate
    codapprovedate = obj.do.codapprovedate
    installstartdate = obj.install.startdate
    installcompletedate = obj.install.completedate
    integrationdate = obj.install.integrationdate
    integrationturnondate = obj.install.integrationondate
    onairdate = obj.install.oaairdate
    coisubmitdate = obj.install.coisubmitdate
    coiapprovedate = obj.install.coiapprovedate
    coicsubmitdate = obj.install.coicsubmitdate
    coicapprovedate = obj.install.coicapprovestatus
    pnochotriggerdate = obj.install.pnochotriggerdate
    pnochocompletedate = obj.install.pnochocompletedate
    ssvstartdate = obj.ssv.ssvstartdate
    ssvcompletedate = obj.ssv.ssvcompletedate
    ssvsubmitdate = obj.ssv.ssvsubmitdate
    bsreceivedate = obj.ssv.bsreceivedate
    bssubmitdate = obj.ssv.bssubmitdate
    bsapprovedate = obj.ssv.bsapprovedate
    optstartdate = obj.optimization.optstartdate
    optcompletedate = obj.optimization.optcompletedate
    optsubmitdate = obj.optimization.optsubmitdate
    optapprovedate = obj.optimization.optapprovedate
    pacsubmitdate = obj.certification.pacsubmitdate
    facsubmitdate = obj.certification.facsubmitdate
    pacapprove = obj.certification.pacapprovestatus
    facapprove = obj.certification.facapprovestatus
    ssvsubcon = obj.ssv.ssvsubcon
    optsubcon = obj.optimization.optsubcon if obj else ''

    row = [siteid, sitename, cluster, contracttype, region, opttype, lat, lon, dodate, codsubmitdate, codapprovedate, installstartdate,
           installcompletedate, integrationdate, integrationturnondate, onairdate, coisubmitdate, coiapprovedate, coicsubmitdate,
           coicapprovedate, pnochotriggerdate, pnochocompletedate, ssvstartdate, ssvcompletedate, ssvsubmitdate, bsreceivedate,
           bssubmitdate, bsapprovedate, optstartdate, optcompletedate, optsubmitdate, optapprovedate, pacsubmitdate, facsubmitdate,
           pacapprove, facapprove, ssvsubcon, optsubcon]
    writer.writerow(row)
    # print(f"Writing row to CSV: {row}")  # 행 쓰는 상태를 출력
  return response


class FDDMasterTrackerCSV(APIView):
  def get(self, request):
    queryset = AllTable.objects.filter(sitebasicinfo__contracttype__in=[1, 2, 3, 7]).select_related(
      'sitebasicinfo', 'do', 'install', 'ssv', 'optimization', 'certification'
    )
    data = []
    for instance in queryset:
      row = {
        'Site ID': instance.sitebasicinfo.siteid,
        'Site Name' :instance.sitebasicinfo.sitename,
        'Cluster': instance.sitebasicinfo.cluster,
        'Contrac-Type': instance.sitebasicinfo.contracttype,
        'Region': instance.sitebasicinfo.region,
        'OPT-Type': instance.optimization.opttype,
        'Lat': instance.sitebasicinfo.lat,
        'Lon': instance.sitebasicinfo.lon,
        'DO-Date': instance.do.doissuedate,
        'COD Submit Date': instance.do.codsubmitdate,
        'COD Approve Date': instance.do.codapprovedate,
        'Install Start Date': instance.install.startdate,
        'Install Complete Date': instance.install.completedate,
        'Integration Date': instance.install.integrationdate,
        'Integrateion TurnOn Date': instance.install.integrationondate,
        'OnAir Date': instance.install.oaairdate,
        'COI Submit Date': instance.install.coisubmitdate,
        'COI Approve Date': instance.install.coiapprovedate,
        'COI&C Submit Date': instance.install.coicsubmitdate,
        'COI&C Approve Date': instance.install.coicapprovestatus,
        'PNOC HO Trigger Date': instance.install.pnochotriggerdate,
        'PNOC HO Complete Date': instance.install.pnochocompletedate,
        'SSV Start Date': instance.ssv.ssvstartdate,
        'SSV Complete Date': instance.ssv.ssvcompletedate,
        'SSV Submit Date': instance.ssv.ssvsubmitdate,
        'BS Receive Date': instance.ssv.bsreceivedate,
        'BS Submit Date': instance.ssv.bssubmitdate,
        'BS Approve Date': instance.ssv.bsapprovedate,
        'OPT Start Date': instance.optimization.optstartdate,
        'OPT Complete Date': instance.optimization.optcompletedate,
        'OPT Sbumit Date': instance.optimization.optsubmitdate,
        'OPT Approve Date': instance.optimization.optapprovedate,
        'PAC Submit Date': instance.certification.pacsubmitdate,
        'FAC Submit Date': instance.certification.facsubmitdate,
        'PAC Approve Status': instance.certification.pacapprovestatus,
        'FAC Approve Status': instance.certification.facapprovestatus,
        'SSV Subcon': instance.ssv.ssvsubcon,
        'OPT Subcon': instance.optimization.optsubcon
      }
      data.append(row)
      # serializer = AllTableCSVSerializer(queryset, many=True)
      # csv_data = serializer.data

    df = pd.DataFrame(data)

    # CSV Response 생성
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="FDD Master Tracker.csv"'

    df.to_csv(path_or_buf=response, index=False)
    return response

class FDDIntegrationTrackerCSV(APIView):
  def get(self, request):
    queryset = AllTable.objects.filter(sitebasicinfo__contracttype__in=[1,2,3,4,5,6,7,8,9]).select_related(
      'sitebasicinfo', 'do', 'install', 'ssv', 'optimization', 'certification'
    )
    data = []
    for instance in queryset:
      row = {
        'Site ID': instance.sitebasicinfo.siteid,
        'WiMAX ID': instance.sitebasicinfo.siteid,
        'Region': instance.sitebasicinfo.region,
        'Cluster': instance.sitebasicinfo.cluster,
        'Site Name': instance.sitebasicinfo.sitename,
        'Site Name': instance.sitebasicinfo.cluster,
        'Install Start Date': instance.install.startdate,
        'Install Complete Date': instance.install.completedate,
        'Integration Date': instance.install.integrationondate,
        'SSV Complete Date': instance.ssv.ssvcompletedate,
        'BS Report Submit Date': instance.ssv.bssubmitdate,
        'BS Report Approve Date': instance.ssv.bsapprovedate,
        'SSV Subcon': instance.ssv.ssvsubcon,
        'OPT Complete Date': instance.optimization.optcompletedate,
        'Contract-Type': instance.sitebasicinfo.contracttype
      }
      data.append(row)
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="LTE_800 Integration Staus Progress Update.csv"'
    df.to_csv(path_or_buf=response, mode='w', encoding='utf-8', compression='gzip', index=False)
    return response

def Export_FDD_Integrate_tracker_csv(request):
  queryset = AllTable.objects.filter(sitebasicinfo__contracttype__in=[1,2,3,4,5,6,7,8,9]).select_related(
    'sitebasicinfo', 'do', 'install', 'ssv', 'optimization', 'certification'
  )

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="LTE800 Integration Status Progress Update.csv"'

  writer = csv.writer(response)
  writer.writerow(
    ['Site ID', 'WiMAX ID', 'Region', 'Cluster', 'Site Name', 'Site Name', 'Install Start Date', 'Install Complete Date',
     'Integration Date', 'SSV Complete Date', 'BS Report Submit Date', 'BS Report Approve Date', 'SSV Subcon', 'OPT Complete Date', 'Contract-Type']
  )

  for obj in queryset:
    siteid = obj.sitebasicinfo.siteid
    wimaxid = obj.sitebasicinfo.siteid
    region = obj.sitebasicinfo.region
    cluster = obj.sitebasicinfo.cluster
    sitename = obj.sitebasicinfo.sitename
    sitename = obj.sitebasicinfo.sitename
    installstartdate = obj.install.startdate
    installcompletedate = obj.install.completedate
    integrationdate = obj.install.integrationondate
    ssvcompletedate = obj.ssv.ssvcompletedate
    bsreportsubmitdate = obj.ssv.bssubmitdate
    bsreportapprovedate = obj.ssv.bsapprovedate
    ssvsubcon = obj.ssv.ssvsubcon
    optcompletedate = obj.optimization.optcompletedate
    contracttype = obj.sitebasicinfo.contracttype

    row = [siteid, wimaxid, region, cluster, sitename, sitename, installstartdate, installcompletedate, integrationdate, ssvcompletedate,
           bsreportsubmitdate, bsreportapprovedate, ssvsubcon, optcompletedate, contracttype]
    writer.writerow(row)
    # print(f"Writing row to CSV: {row}")  # 행 쓰는 상태를 출력
  return response


#--------------------------------------------------------------------------------------------------
#BTS MANAGER EXPORT TO CSV-------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
def Export_btsmanager_csv(request):
  site_lsm_infos = SiteLSMinfo.objects.all()
  site_basic_infos = SiteBasicinfo.objects.all()
  site_phy_infos = SitePhyinfo.objects.all()
  site_ret_infos = SiteRETinfo.objects.all()

  # 각 테이블에서 uid나 sitebasicinfo를 key로 사용해 데이터를 사전에 저장
  basic_info_dict = {info.id: info for info in site_basic_infos}
  phy_info_dict = {info.uid: info for info in site_phy_infos}
  ret_info_dict = {info.uid: info for info in site_ret_infos}

  response = HttpResponse(content_type='text/csv')
  response['Content-Disposition'] = 'attachment; filename="BTS_Manager.csv"'

  writer = csv.writer(response)
  writer.writerow(
    ['LTE_Site_ID', 'LTE_Sec_ID', 'Port_Num', 'Region', 'SiteName', 'Cluster', 'Latitude', 'Longitude', 'Channel_Card', 'Antenna_Type',
     'Height', 'Azimuth', 'M-Tilt', 'E-Tilt', 'EARFCN_DL', 'EARFCN_UL', 'PCI', 'PSS', 'SSS', 'RSI', 'TAC', 'Cell_Identify', 'Radius', 'Angle',
     'modifydate', 'modifyby']
    )  # 컬럼 헤더

  for obj in site_lsm_infos:
    basic_info = basic_info_dict.get(obj.sitebasicinfo_id)
    phy_info = phy_info_dict.get(obj.uid)
    ret_info = ret_info_dict.get(obj.uid)

    site_id = obj.siteid
    secid = phy_info.secid if phy_info else ''
    cell_num = obj.cellnum
    region = basic_info.region.region if basic_info else ''
    # state = basic_info.state.state if basic_info.state.state else ''
    sitename = basic_info.sitename if basic_info else ''
    cluster = basic_info.cluster.cluster if basic_info else ''
    lat = basic_info.lat if basic_info else ''
    lon = basic_info.lon if basic_info else ''
    channelcard = obj.channelcard
    antennatype = phy_info.antennatype.antennatype if phy_info else ''
    height = phy_info.antennaheight if phy_info else ''
    azi = phy_info.azimuth if phy_info else ''
    mtilt = phy_info.mtilt if phy_info else ''
    etilt = ret_info.tilt / 10 if ret_info else (phy_info.etilt if phy_info else '')
    earfcndl = obj.earfcndl
    earfcnul = obj.earfcnul
    pci = obj.pci
    rsi = obj.rsi
    tac = obj.tac
    pss = obj.pss
    sss = obj.sss
    cellidentify = obj.cellidentity
    radius = ''
    if obj.freqband == 40:
      angle = 0.1
    elif obj.freqband == 38:
      angle = 0.14
    elif obj.freqband == 20:
      angle = 0.18
    angle = ''
    if phy_info and phy_info.antennatype:

      if phy_info.antennatype.antennatype == 'Indoor' or phy_info.antennatype.antennatype == 'Omni':
        angle = 360
      else:
        if obj.freqband == 40:
          angle = 60
        elif obj.freqband == 38:
          angle = 30
        elif obj.freqband == 20:
          angle = 15
    modifydate = phy_info.modify_at if phy_info else ''
    modifyby = phy_info.modified_by if phy_info else ''

    row = [site_id, secid, cell_num, region, sitename, cluster, lat, lon, channelcard, antennatype, height, azi, mtilt, etilt, earfcndl, earfcnul, pci, pss, sss, rsi, tac, cellidentify, radius, angle, modifydate, modifyby]
    writer.writerow(row)  # 행 쓰기
    # print(f"Writing row to CSV: {row}")  # 행 쓰는 상태를 출력

  return response

#--------------------------------------------------------------------------------------------------
#FDD Rending page stitistic------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class LSMStatisticAPIView(ListAPIView):
  serializer_class = SiteLSMinfoSerializer

  def get_queryset(self):
    base_queryset = SiteLSMinfo.objects.exclude(sitestatus="Dismantled")
    return base_queryset
  
  def get(self, request, *args, **kwargs):
    base_queryset = self.get_queryset()
    regions = base_queryset.values_list('sitebasicinfo__region__region', flat=True).distinct()
    bands = base_queryset.values_list('freqband', flat=True).distinct()

    unique_sites = base_queryset.values('siteid').distinct()
    unique_site_count = unique_sites.count()
    cell_count = base_queryset.count()

    sitecount_byregion = {'region': [], 'count': []}
    for region in regions:
      sitecount = base_queryset.filter(sitebasicinfo__region__region=region).values(
        'sitebasicinfo__region__region'
      ).annotate(count=Count('siteid', distinct=True)).order_by('sitebasicinfo__region')
      for item in sitecount:
        sitecount_byregion['region'].append(item['sitebasicinfo__region__region'])
        sitecount_byregion['count'].append(item['count'])
    
    cellcount_byregion = {'region': [], 'count': []}
    for region in regions:
      cellcount = base_queryset.filter(sitebasicinfo__region__region=region).values(
        'sitebasicinfo__region__region'
      ).annotate(count=Count('siteid')).order_by('sitebasicinfo__region')
      for item in cellcount:
        cellcount_byregion['region'].append(item['sitebasicinfo__region__region'])
        cellcount_byregion['count'].append(item['count'])

    sitecount_byband = {'band': [], 'count': []}
    for band in bands:
      sitecount = base_queryset.filter(freqband=band).values('freqband').annotate(count=Count('siteid', distinct=True))
      for item in sitecount:
        sitecount_byband['band'].append(item['freqband'])
        sitecount_byband['count'].append(item['count'])
    
    cellcount_byband = {'band': [], 'count': []}
    for band in bands:
      cellcount = base_queryset.filter(freqband=band).values('freqband').annotate(count=Count('siteid'))
      for item in cellcount:
        cellcount_byband['band'].append(item['freqband'])
        cellcount_byband['count'].append(item['count'])

    sitecount_by_regionband = {}
    for band in bands:
      site_count = base_queryset.filter(
        freqband=band
      ).values('sitebasicinfo__region__region').annotate(count=Count('siteid', distinct=True)).order_by('sitebasicinfo__region')
      site_count_by_bands = {
        'region': [],
        'count': []
      }
      for item in site_count:
        site_count_by_bands['region'].append(item['sitebasicinfo__region__region'])
        site_count_by_bands['count'].append(item['count'])
      sitecount_by_regionband[band] = site_count_by_bands
    
    sitecount_by_bandregion = {}
    for region in regions:
      site_count = base_queryset.filter(
        sitebasicinfo__region__region=region
      ).values('freqband').annotate(count=Count('siteid', distinct=True)).order_by('sitebasicinfo__region')
      site_count_by_regions = {'freqband': [], 'count': []}
      for item in site_count:
        site_count_by_regions['freqband'].append(item['freqband'])
        site_count_by_regions['count'].append(item['count'])
      sitecount_by_bandregion[region] = site_count_by_regions

    cellcount_by_regionband = {}
    for band in bands:
      cellcount = base_queryset.filter(
        freqband=band
      ).values('sitebasicinfo__region__region').annotate(count=Count('siteid')).order_by('sitebasicinfo__region')
      cell_count_by_bands = {'region': [], 'count': []}
      for item in cellcount:
        cell_count_by_bands['region'].append(item['sitebasicinfo__region__region'])
        cell_count_by_bands['count'].append(item['count'])
      cellcount_by_regionband[band] = cell_count_by_bands
    
    cellcount_by_bandregion = {}
    for region in regions:
      cellcount = base_queryset.filter(
        sitebasicinfo__region__region=region
      ).values('freqband').annotate(count=Count('siteid')).order_by('sitebasicinfo__region')
      cell_count_by_regions = {'freqband': [], 'count': []}
      for item in cellcount:
        cell_count_by_regions['freqband'].append(item['freqband'])
        cell_count_by_regions['count'].append(item['count'])
      cellcount_by_bandregion[region] = cell_count_by_regions

    return Response({
      'unique_site_count': unique_site_count,
      'sitecount_byregion': sitecount_byregion,
      'sitecount_byband': sitecount_byband,
      'sitecount_by_regionband': sitecount_by_regionband,
      'sitecount_by_bandregion': sitecount_by_bandregion,
      'cell_count': cell_count,
      'cellcount_byregion': cellcount_byregion,
      'cellcount_byband': cellcount_byband,
      'cellcount_by_regionband': cellcount_by_regionband,
      'cellcount_by_bandregion': cellcount_by_bandregion
    })


#--------------------------------------------------------------------------------------------------
#Weekly report List view---------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class WeeklyReportAPIView(ListAPIView):
  serializer_class = AllTableSerializer

  def get_queryset(self):
    base_queryset = AllTable.objects.filter(sitebasicinfo__contracttype__in=[1,2,3, 7])
    return base_queryset
    
  def get(self, request, *args, **kwargs):
    today = timezone.now().date()
    last_friday = today - timedelta(days=(today.weekday() - 4) % 7)
    this_thursday = last_friday + timedelta(days=6)

    base_queryset = self.get_queryset()

    total_doissue = base_queryset.filter(do__doissuedate__isnull=False).count()
    doissue_today = AllTableSerializer(base_queryset.filter(do__doissuedate=today), many=True).data
    doissue_week = AllTableSerializer(base_queryset.filter(do__doissuedate__range=[last_friday, this_thursday]), many=True).data
    total_codsubmit = base_queryset.filter(do__codsubmitdate__isnull=False).count()
    codsubmit_today = AllTableSerializer(base_queryset.filter(do__codsubmitdate=today), many=True).data
    codsubmit_week = AllTableSerializer(base_queryset.filter(do__codsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_codapprove = base_queryset.filter(do__codapprovedate__isnull=False).count()
    codapprove_today = AllTableSerializer(base_queryset.filter(do__codapprovedate=today), many=True).data
    codapprove_week = AllTableSerializer(base_queryset.filter(do__codapprovedate__range=[last_friday, this_thursday]), many=True).data

    total_installstart = base_queryset.filter(install__startdate__isnull=False).count()
    installstart_today = AllTableSerializer(base_queryset.filter(install__startdate=today), many=True).data
    installstart_week = AllTableSerializer(base_queryset.filter(install__startdate__range=[last_friday, this_thursday]), many=True).data
    total_installcomplete = base_queryset.filter(install__completedate__isnull=False).count()
    installcomplete_today = AllTableSerializer(base_queryset.filter(install__completedate=today), many=True).data
    installcomplete_week = AllTableSerializer(base_queryset.filter(install__completedate__range=[last_friday, this_thursday]), many=True).data
    total_integration =  base_queryset.filter(install__integrationdate__isnull=False).count()
    integration_today = AllTableSerializer(base_queryset.filter(install__integrationdate=today), many=True).data
    integration_week = AllTableSerializer(base_queryset.filter(install__integrationdate__range=[last_friday, this_thursday]), many=True).data
    total_onair = base_queryset.filter(install__oaairdate__isnull=False).count()
    onair_today = AllTableSerializer(base_queryset.filter(install__oaairdate=today), many=True).data
    onair_week = AllTableSerializer(base_queryset.filter(install__oaairdate__range=[last_friday, this_thursday]), many=True).data
    total_coisubmit = base_queryset.filter(install__coisubmitdate__isnull=False).count()
    coisubmit_today = AllTableSerializer(base_queryset.filter(install__coisubmitdate=today), many=True).data
    coisubmit_week = AllTableSerializer(base_queryset.filter(install__coisubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_coiapprove = base_queryset.filter(install__coiapprovedate__isnull=False).count()
    coiapprove_today = AllTableSerializer(base_queryset.filter(install__coiapprovedate=today), many=True).data
    coiapprove_week = AllTableSerializer(base_queryset.filter(install__coiapprovedate__range=[last_friday, this_thursday]), many=True).data
    total_coicsubmit = base_queryset.filter(install__coicsubmitdate__isnull=False).count()
    coicsubmit_today = AllTableSerializer(base_queryset.filter(install__coicsubmitdate=today), many=True).data
    coicsubmit_week = AllTableSerializer(base_queryset.filter(install__coicsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_coicapprove = base_queryset.filter(install__coicapprovestatus=1).count()
    total_pnoctrigger = base_queryset.filter(install__pnochotriggerdate__isnull=False).count()
    pnoctrigger_today = AllTableSerializer(base_queryset.filter(install__pnochotriggerdate=today), many=True).data
    pnoctrigger_week = AllTableSerializer(base_queryset.filter(install__pnochotriggerdate__range=[last_friday, this_thursday]), many=True).data
    total_pnoccomplete = base_queryset.filter(install__pnochocompletedate__isnull=False).count()
    pnoccomplete_today = AllTableSerializer(base_queryset.filter(install__pnochocompletedate=today), many=True).data
    pnoccomplete_week = AllTableSerializer(base_queryset.filter(install__pnochocompletedate__range=[last_friday, this_thursday]), many=True).data

    total_ssvstart = base_queryset.filter(ssv__ssvstartdate__isnull=False).count()
    ssvstart_today = AllTableSerializer(base_queryset.filter(ssv__ssvstartdate=today), many=True).data
    ssvstart_week = AllTableSerializer(base_queryset.filter(ssv__ssvstartdate__range=[last_friday, this_thursday]), many=True).data
    total_ssvcomplete = base_queryset.filter(ssv__ssvstartdate__isnull=False).count()
    ssvcomplete_today = AllTableSerializer(base_queryset.filter(ssv__ssvcompletedate=today), many=True).data
    ssvcomplete_week = AllTableSerializer(base_queryset.filter(ssv__ssvcompletedate__range=[last_friday, this_thursday]), many=True).data
    total_ssvsubmit = base_queryset.filter(ssv__ssvsubmitdate__isnull=False).count()
    ssvsubmit_today = AllTableSerializer(base_queryset.filter(ssv__ssvsubmitdate=today), many=True).data
    ssvsubmit_week = AllTableSerializer(base_queryset.filter(ssv__ssvsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_bssubmit = base_queryset.filter(ssv__bssubmitdate__isnull=False).count()
    bssubmit_today = AllTableSerializer(base_queryset.filter(ssv__bssubmitdate=today), many=True).data
    bssubmit_week = AllTableSerializer(base_queryset.filter(ssv__bssubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_bsapprove = base_queryset.filter(ssv__bsapprovedate__isnull=False).count()
    bsapprove_today = AllTableSerializer(base_queryset.filter(ssv__bsapprovedate=today), many=True).data
    bsapprove_week = AllTableSerializer(base_queryset.filter(ssv__bsapprovedate__range=[last_friday, this_thursday]), many=True).data

    total_optstart = base_queryset.filter(optimization__optstartdate__isnull=False).count()
    optstart_today = AllTableSerializer(base_queryset.filter(optimization__optstartdate=today), many=True).data
    optstart_week = AllTableSerializer(base_queryset.filter(optimization__optstartdate__range=[last_friday, this_thursday]), many=True).data
    total_optcomplete = base_queryset.filter(optimization__optcompletedate__isnull=False).count()
    optcomplete_today = AllTableSerializer(base_queryset.filter(optimization__optcompletedate=today), many=True).data
    optcomplete_week = AllTableSerializer(base_queryset.filter(optimization__optcompletedate__range=[last_friday, this_thursday]), many=True).data
    total_optsubmit = base_queryset.filter(optimization__optsubmitdate__isnull=False).count()
    optsubmit_today = AllTableSerializer(base_queryset.filter(optimization__optsubmitdate=today), many=True).data
    optsubmit_week = AllTableSerializer(base_queryset.filter(optimization__optsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_optapprove = base_queryset.filter(optimization__optapprovedate__isnull=False).count()
    optapprove_today = AllTableSerializer(base_queryset.filter(optimization__optapprovedate=today), many=True).data
    optapprove_week = AllTableSerializer(base_queryset.filter(optimization__optapprovedate__range=[last_friday, this_thursday]), many=True).data

    total_pacsubmit = base_queryset.filter(certification__pacsubmitdate__isnull=False).count()
    pacsubmit_today = AllTableSerializer(base_queryset.filter(certification__pacsubmitdate=today), many=True).data
    pacsubmit_week = AllTableSerializer(base_queryset.filter(certification__pacsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_facsubmit = base_queryset.filter(certification__facsubmitdate__isnull=False).count()
    facsubmit_today = AllTableSerializer(base_queryset.filter(certification__facsubmitdate=today), many=True).data
    facsubmit_week = AllTableSerializer(base_queryset.filter(certification__facsubmitdate__range=[last_friday, this_thursday]), many=True).data
    total_pacapprove = base_queryset.filter(certification__pacapprovestatus=1).count()
    total_facapprove = base_queryset.filter(certification__facapprovestatus=1).count()

    return Response({
      'total_doissue': total_doissue,
      'doissue_today': doissue_today,
      'doissue_week': doissue_week,
      'total_codsubmit': total_codsubmit,
      'codsubmit_today':codsubmit_today,
      'codsubmit_week': codsubmit_week,
      'total_codapprove': total_codapprove,
      'codapprove_today': codapprove_today,
      'codapprove_week': codapprove_week,

      'total_installstart':total_installstart,
      'installstart_today': installstart_today,
      'installstart_week': installstart_week,
      'total_installcomplete': total_installcomplete,
      'installcomplete_today': installcomplete_today,
      'installcomplete_week': installcomplete_week,
      'total_integration': total_integration,
      'integration_today': integration_today,
      'integration_week': integration_week,
      'total_onair': total_onair,
      'onair_today': onair_today,
      'onair_week': onair_week,
      'total_coisubmit': total_coisubmit,
      'coisubmit_today': coisubmit_today,
      'coisubmit_week': coisubmit_week,
      'total_coiapprove': total_coiapprove,
      'coiapprove_today': coiapprove_today,
      'coiapprove_week': coiapprove_week,
      'total_coicapprove' :total_coicapprove,
      'total_coicsubmit': total_coicsubmit,
      'coicsubmit_today': coicsubmit_today,
      'coicsubmit_week': coicsubmit_week,
      'total_pnoctrigger': total_pnoctrigger,
      'pnoctrigger_today': pnoctrigger_today,
      'pnoctrigger_week': pnoctrigger_week,
      'total_pnoccomplete': total_pnoccomplete,
      'pnoccomplete_today': pnoccomplete_today,
      'pnoccomplete_week': pnoccomplete_week,

      'total_ssvstart': total_ssvstart,
      'ssvstart_today': ssvstart_today,
      'ssvstart_week': ssvstart_week,
      'total_ssvcomplete': total_ssvcomplete,
      'ssvcomplete_today': ssvcomplete_today,
      'ssvcomplete_week': ssvcomplete_week,
      'total_ssvsubmit': total_ssvsubmit,
      'ssvsubmit_today': ssvsubmit_today,
      'ssvsubmit_week': ssvsubmit_week,
      'total_bssubmit': total_bssubmit,
      'bssubmit_today': bssubmit_today,
      'bssubmit_week': bssubmit_week,
      'total_bsapprove': total_bsapprove,
      'bsapprove_today': bsapprove_today,
      'bsapprove_week': bsapprove_week,

      'total_optstart': total_optstart,
      'optstart_today': optstart_today,
      'optstart_week': optstart_week,
      'total_optcomplete': total_optcomplete,
      'optcomplete_today': optcomplete_today,
      'optcomplete_week': optcomplete_week,
      'total_optsubmit': total_optsubmit,
      'optsubmit_today': optsubmit_today,
      'optsubmit_week': optsubmit_week,
      'total_optapprove': total_optapprove,
      'optapprove_today': optapprove_today,
      'optapprove_week': optapprove_week,

      'total_pacsubmit': total_pacsubmit,
      'pacsubmit_today': pacsubmit_today,
      'pacsubmit_week': pacsubmit_week,
      'total_facsubmit': total_facsubmit,
      'facsubmit_today': facsubmit_today,
      'facsubmit_week': facsubmit_week,
      'total_pacapprove': total_pacapprove,
      'total_facapprove': total_facapprove
    })
  
#--------------------------------------------------------------------------------------------------
#TEST RESULT VIEWSET-------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class TestResultViewSet(viewsets.ModelViewSet):
  queryset = TestResult.objects.all().order_by('-create_at')
  serializer_class = TestResultSerializer
  pagination_class = CustomLimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = TestResultFilter

#--------------------------------------------------------------------------------------------------
#JWT AUTH---- -------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class RegisterView_(APIView):
  def post(self, request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if User.objects.filter(username=username).exists():
      return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email)
    user.save()

    return Response({'message': 'User created'}, status=status.HTTP_201_CREATED)
  
class LoginView_(APIView):
  def post(self, request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = User.objects.filter(username=username).first()

    if user is None:
      return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not user.check_password(password):
      return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
    
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    response = Response({
      'refresh': str(refresh),
      'access': access,
    })

    response.set_cookie(key='jwt', value=access, httponly=True)
    # response.data = { 'jwt': access }

    return response

class UserInfoView(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    try:
      user = request.user
      if user is None:
        raise AuthenticationFailed('User not found')
      return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff
      }, status=status.HTTP_200_OK)
    except AuthenticationFailed as e:
      return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
  
class LogoutView_(APIView):
  def post(self, request):

    response = Response()
    response.delete_cookie('jwt')
    response.data = {
      'message': 'Logged out'
    }

    return response
  
#--------------------------------------------------------------------------------------------------
#statistic-----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class StatisticView(viewsets.ModelViewSet):
  queryset = Statistic.objects.select_related('sitebasicinfo', 'sitephyinfo').exclude(sitestatus='Dismantled').all().order_by('uid')
  serializer_class = StatisticSerializer
  # pagination_class = CustomLimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticFilter

class StatisticDataView(viewsets.ModelViewSet):
  queryset = StatisticData.objects.select_related('sitebasicinfo', 'sitephyinfo').all()
  serializer_class = StatisticDataSerializer
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticDataFilter

class StatisticDataHeatmapView(APIView):
  def get(self, request, *args, **kwargs):
    region = request.query_params.get('region', None)
    cluster = request.query_params.get('cluster', None)
    band = request.query_params.get('band', None)
    show_all = request.query_params.get('show_all', 'false').lower() == 'true'

    if show_all:
      queryset = StatisticData.objects.all()
    else:
      queryset = StatisticData.objects.all()
      if band:
        queryset = queryset.filter(band__iexact=band)
      if region:
        queryset = queryset.filter(sitebasicinfo__region__region__iexact=region)
      if cluster:
        queryset = queryset.filter(sitebasicinfo__cluster__cluster__iexact=cluster)
      
    serializer = StatisticDataPRBDLHeatmapSerializer(queryset, many=True)
    return Response({'heatmap_data': serializer.data})
  
#Statistic paged view -----------------------------------------------------------------------------
class StatisticPagedAPIView(ListModelMixin, GenericAPIView):
  queryset = Statistic.objects.all()
  serializer_class = StatisticDynamicFieldSerializer
  pagination_class = CustomLimitOffsetPagination
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticFailFilter

  def get_queryset(self):
    queryset = super().get_queryset().select_related('sitebasicinfo', 'sitephyinfo')
    fields = self.request.query_params.get('fields')
    if fields:
      fields = fields.split(',')
      if 'cell_availability' in fields:
        queryset = queryset.filter(cell_availability__isnull=False, cell_availability__lt=99)
      if 'attach_setup_success_rate' in fields:
        queryset = queryset.filter(attach_setup_success_rate__isnull=False, attach_setup_success_rate__lt=99)
      if 'rrc_setup_success_rate' in fields:
        queryset = queryset.filter(rrc_setup_success_rate__isnull=False, rrc_setup_success_rate__lt=99)
      if 'erab_setup_success_rate_ngbr' in fields:
        queryset = queryset.filter(erab_setup_success_rate_ngbr__isnull=False, erab_setup_success_rate_ngbr__lt=99)
      if 'volte_setup_success_rate_gbr' in fields:
        queryset = queryset.filter(volte_setup_success_rate_gbr__isnull=False, volte_setup_success_rate_gbr__lt=99)
      if 'call_drop_rate_erab_ngbr' in fields:
        queryset = queryset.filter(call_drop_rate_erab_ngbr__isnull=False, call_drop_rate_erab_ngbr__gt=1)
      if 'volte_call_drop_rate_erab_gbr' in fields:
        queryset = queryset.filter(volte_call_drop_rate_erab_gbr__isnull=False, volte_call_drop_rate_erab_gbr__gt=1)
      if 'hosr_intra_frequency' in fields:
        queryset = queryset.filter(hosr_intra_frequency__isnull=False, hosr_intra_frequency__lt=99)
      if 'hosr_inter_frequency' in fields:
        queryset = queryset.filter(hosr_inter_frequency__isnull=False, hosr_inter_frequency__lt=99)

      if 'x2_handover_out_success_rate' in fields:
        queryset = queryset.filter(x2_handover_out_success_rate__isnull=False, x2_handover_out_success_rate__lt=99)
      if 'x2_handover_in_success_rate' in fields:
        queryset = queryset.filter(x2_handover_in_success_rate__isnull=False, x2_handover_in_success_rate__lt=99)
      if 's1_handover_out_success_rate' in fields:
        queryset = queryset.filter(s1_handover_out_success_rate__isnull=False, s1_handover_out_success_rate__lt=99)
      if 's1_handover_in_success_rate' in fields:
        queryset = queryset.filter(s1_handover_in_success_rate__isnull=False, s1_handover_in_success_rate__lt=99)
      if 'dl_bler' in fields:
        queryset = queryset.filter(dl_bler__isnull=False, dl_bler__gt=1)
      if 'ul_bler' in fields:
        queryset = queryset.filter(ul_bler__isnull=False, ul_bler__gt=1)
    return queryset
  
  def get_serializer(self, *args, **kwargs):
    serializer_class = self.get_serializer_class()
    kwargs['context'] = self.get_serializer_context()
    fields = self.request.query_params.get('fields', None)
    default_fields = ['band']
    if fields:
      fields = fields.split(',')
      kwargs['fields'] = list(set(fields + default_fields))
    else:
      kwargs['fields'] = default_fields
    return serializer_class(*args, **kwargs)
  
  def get(self, request, *args, **kwargs):
    return self.list(request, *args, **kwargs)

#Statistic non Page view---------------------------------------------------------------------------
class StatisticNonPageAPIView(ListModelMixin, GenericAPIView):
  queryset = Statistic.objects.all()
  serializer_class = StatisticDynamicFieldSerializer
  pagination_class = None
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticFailFilter

  def get_queryset(self):
    queryset = super().get_queryset().select_related('sitebasicinfo', 'sitephyinfo')
    fields = self.request.query_params.get('fields')
    if fields:
      fields = fields.split(',')
      if 'cell_availability' in fields:
        queryset = queryset.filter(cell_availability__isnull=False, cell_availability__lt=99)
      if 'attach_setup_success_rate' in fields:
        queryset = queryset.filter(attach_setup_success_rate__isnull=False, attach_setup_success_rate__lt=99)
      if 'rrc_setup_success_rate' in fields:
        queryset = queryset.filter(rrc_setup_success_rate__isnull=False, rrc_setup_success_rate__lt=99)
      if 'erab_setup_success_rate_ngbr' in fields:
        queryset = queryset.filter(erab_setup_success_rate_ngbr__isnull=False, erab_setup_success_rate_ngbr__lt=99)
      if 'volte_setup_success_rate_gbr' in fields:
        queryset = queryset.filter(volte_setup_success_rate_gbr__isnull=False, volte_setup_success_rate_gbr__lt=99)
      if 'call_drop_rate_erab_ngbr' in fields:
        queryset = queryset.filter(call_drop_rate_erab_ngbr__isnull=False, call_drop_rate_erab_ngbr__gt=1)
      if 'volte_call_drop_rate_erab_gbr' in fields:
        queryset = queryset.filter(volte_call_drop_rate_erab_gbr__isnull=False, volte_call_drop_rate_erab_gbr__gt=1)
      if 'hosr_intra_frequency' in fields:
        queryset = queryset.filter(hosr_intra_frequency__isnull=False, hosr_intra_frequency__lt=99)
      if 'hosr_inter_frequency' in fields:
        queryset = queryset.filter(hosr_inter_frequency__isnull=False, hosr_inter_frequency__lt=99)

      if 'x2_handover_out_success_rate' in fields:
        queryset = queryset.filter(x2_handover_out_success_rate__isnull=False, x2_handover_out_success_rate__lt=99)
      if 'x2_handover_in_success_rate' in fields:
        queryset = queryset.filter(x2_handover_in_success_rate__isnull=False, x2_handover_in_success_rate__lt=99)
      if 's1_handover_out_success_rate' in fields:
        queryset = queryset.filter(s1_handover_out_success_rate__isnull=False, s1_handover_out_success_rate__lt=99)
      if 's1_handover_in_success_rate' in fields:
        queryset = queryset.filter(s1_handover_in_success_rate__isnull=False, s1_handover_in_success_rate__lt=99)
      if 'dl_bler' in fields:
        queryset = queryset.filter(dl_bler__isnull=False, dl_bler__gt=1)
      if 'ul_bler' in fields:
        queryset = queryset.filter(ul_bler__isnull=False, ul_bler__gt=1)
    return queryset
  
  def get_serializer(self, *args, **kwargs):
    serializer_class = self.get_serializer_class()
    kwargs['context'] = self.get_serializer_context()
    fields = self.request.query_params.get('fields', None)
    default_fields = ['band']
    if fields:
      fields = fields.split(',')
      kwargs['fields'] = list(set(fields + default_fields))
    else:
      kwargs['fields'] = default_fields
    return serializer_class(*args, **kwargs)
  
  def get(self, request, *args, **kwargs):
    return self.list(request, *args, **kwargs)

#Statistic summary view ---------------------------------------------------------------------------
class StatisticSummaryAPIView(ListAPIView):
  def get_queryset(self):
    base_queryset = StatisticData.objects.select_related('sitebasicinfo').all()
    return base_queryset
  def get(self, request, *args, **kwargs):
    base_queryset = self.get_queryset()
    bands = base_queryset.values_list('band', flat=True).distinct()
    regions = base_queryset.values_list('region', flat=True).distinct()

    #total site statistic sites
    total_statistic_site = base_queryset.filter(cellavail_pmperiodtime__gt=0).values_list('sysid', flat=True).distinct().count()
    total_statistic_cell = base_queryset.filter(cellavail_pmperiodtime__gt=0).count()
    total_statistic_site_by_band = {}
    for band in bands:
      site_count = base_queryset.filter(
        band=band, cellavail_pmperiodtime__gt=0
      ).values('sitebasicinfo__region__region').annotate(count=Count('sysid', distinct=True)).order_by('sitebasicinfo__region')
      site_count_by_bands = {
        'region': [],
        'count': []
      }
      for item in site_count:
        site_count_by_bands['region'].append(item['sitebasicinfo__region__region'])
        site_count_by_bands['count'].append(item['count'])
      total_statistic_site_by_band[band] = site_count_by_bands

    total_statistic_cell_by_band = {}
    for band in bands:
      cell_count = base_queryset.filter(
        band=band, cellavail_pmperiodtime__gt=0
      ).values('sitebasicinfo__region__region').annotate(count=Count('sysid')).order_by('sitebasicinfo__region')
      cell_count_by_bands = {'region': [], 'count': []}
      for item in cell_count:
        cell_count_by_bands['region'].append(item['sitebasicinfo__region__region'])
        cell_count_by_bands['count'].append(item['count'])
      total_statistic_cell_by_band[band] = cell_count_by_bands

    #total user count for overall
    total_user_per_band = {}
    for band in bands:
      total_user_count_by_band = base_queryset.filter(
        band=band
      ).values('weeknum').annotate(total_connect_user=Sum('connectmax'))
      connect_max = {
        'weeknum': [],
        'total_connect_count': []
      }
      for item in total_user_count_by_band:
        connect_max['weeknum'].append(item['weeknum'])
        connect_max['total_connect_count'].append(item['total_connect_user'])
      total_user_per_band[band] = connect_max

    #total user count for overall per band and region
    total_user_per_band_and_region = {}
    for band in bands:
      total_user_count_by_band_region = base_queryset.filter(band=band).values('sitebasicinfo__region__region').annotate(
        total_connect_user_by_region=Sum('connectmax')
      ).order_by('sitebasicinfo__region__region')

      connect_max = {
        'regions': [],
        'total_connect_count': []
      }

      for item in total_user_count_by_band_region:
        connect_max['regions'].append(item['sitebasicinfo__region__region'])
        connect_max['total_connect_count'].append(item['total_connect_user_by_region'])
      total_user_per_band_and_region[band] = connect_max


    return Response({
      'total_user': {
        'band': total_user_per_band
      },
      'total_user_by_region': {
        'band': total_user_per_band_and_region
      },
      'total_statistic_site': total_statistic_site,
      'total_statistic_cell': total_statistic_cell,
      'total_statistic_site_by_band': {
        'band': total_statistic_site_by_band
      },
      'total_statistic_cell_by_band': {
        'band': total_statistic_cell_by_band
      }
    })

#Statistic calculated------------------------------------------------------------------------------
class StatisticCalculatedView(viewsets.ModelViewSet):
  queryset = StatisticCalculated.objects.all()
  serializer_class = StatisticCalculatedSerializer
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticCalculatedFilter

#Statistic calculated trend view-------------------------------------------------------------------
class StatisticCalculatedTrendAPIView(ListAPIView):
  serializer_class = StatisticCalculatedSerializer

  def get_queryset(self):
    current_year = datetime.now().year % 100
    current_week = datetime.now().isocalendar()[1] - 1

    weeknums = [f'{current_year}Week {max(1, current_week - i):02d}' for i in range(10)]
    return StatisticCalculated.objects.filter(weeknum__in=weeknums).order_by('weeknum')
  
  def list(self, request, *args, **kwargs):
    queryset = self.get_queryset()

    field = request.query_params.get('fields', 'cell_availability').lower()

    # data structur
    chart_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))))


    for data in queryset:
      category = data.category
      band = data.band
      region = data.region.region
      weeknum = data.weeknum

      # dynamic field
      value = getattr(data, field, None)
      if value is not None:
        chart_data[field][category][band][region]['weeknum'].append(weeknum)
        chart_data[field][category][band][region]['value'].append(value)

    return Response(chart_data)

#Statistic API View--------------------------------------------------------------------------------
class StatisticAPIView(ListAPIView):
  def get_queryset(self):
    base_queryset = Statistic.objects.select_related('sitebasicinfo').all()
    return base_queryset
  
  def get(self, request, *args, **kwargs):
    base_queryset = self.get_queryset()

    bands = base_queryset.values_list('band', flat=True).distinct()

    #cell_availability_result
    cell_availability_result = {}
    for band in bands:
      cell_availability_by_region = base_queryset.filter(
        cell_availability__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_cell_availability=Avg('cell_availability'),
        count_fail_cell=Count(Case(When(cell_availability__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      cell_availability_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in cell_availability_by_region:
        cell_availability_['region'].append(item['sitebasicinfo__region__region'])
        cell_availability_['avg'].append(item['avg_cell_availability'])
        cell_availability_['count_fail'].append(item['count_fail_cell'])
      
      cell_availability_result[band] = cell_availability_
      
    #attach_setup_success_rate
    attach_setup_success_result = {}
    for band in bands:
      attach_setup_success_rate_by_region = base_queryset.filter(
        attach_setup_success_rate__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_attach_setup_success=Avg('attach_setup_success_rate'),
        count_fail_cell=Count(Case(When(attach_setup_success_rate__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      attach_setup_success_rate_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in attach_setup_success_rate_by_region:
        attach_setup_success_rate_['region'].append(item['sitebasicinfo__region__region'])
        attach_setup_success_rate_['avg'].append(item['avg_attach_setup_success'])
        attach_setup_success_rate_['count_fail'].append(item['count_fail_cell'])
      
      attach_setup_success_result[band] = attach_setup_success_rate_

    #rrc_setup_success_rate
    rrc_setup_success_result = {}
    for band in bands:
      rrc_setup_success_rate_by_region = base_queryset.filter(
        rrc_setup_success_rate__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_rrc_setup_success=Avg('rrc_setup_success_rate'),
        count_fail_cell=Count(Case(When(rrc_setup_success_rate__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      rrc_setup_success_rate_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in rrc_setup_success_rate_by_region:
        rrc_setup_success_rate_['region'].append(item['sitebasicinfo__region__region'])
        rrc_setup_success_rate_['avg'].append(item['avg_rrc_setup_success'])
        rrc_setup_success_rate_['count_fail'].append(item['count_fail_cell'])

      rrc_setup_success_result[band] = rrc_setup_success_rate_
      
    #erab_setup_success_rate_ngbr
    erab_setup_success_result = {}
    for band in bands:
      erab_setup_success_rate_ngbr_by_region = base_queryset.filter(
        erab_setup_success_rate_ngbr__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_erab_setup_success=Avg('erab_setup_success_rate_ngbr'),
        count_fail_cell=Count(Case(When(erab_setup_success_rate_ngbr__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      erab_setup_success_rate_ngbr_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in erab_setup_success_rate_ngbr_by_region:
        erab_setup_success_rate_ngbr_['region'].append(item['sitebasicinfo__region__region'])
        erab_setup_success_rate_ngbr_['avg'].append(item['avg_erab_setup_success'])
        erab_setup_success_rate_ngbr_['count_fail'].append(item['count_fail_cell'])

      erab_setup_success_result[band] = erab_setup_success_rate_ngbr_

    #call_drop_rate_erab_ngbr
    call_drop_result = {}
    for band in bands:
      call_drop_rate_erab_ngbr_by_region = base_queryset.filter(
        call_drop_rate_erab_ngbr__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_call_drop=Avg('call_drop_rate_erab_ngbr'),
        count_fail_cell=Count(Case(When(call_drop_rate_erab_ngbr__gt=1, then=1)))
      ).order_by('sitebasicinfo__region')

      call_drop_rate_erab_ngbr_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in call_drop_rate_erab_ngbr_by_region:
        call_drop_rate_erab_ngbr_['region'].append(item['sitebasicinfo__region__region'])
        call_drop_rate_erab_ngbr_['avg'].append(item['avg_call_drop'])
        call_drop_rate_erab_ngbr_['count_fail'].append(item['count_fail_cell'])

      call_drop_result[band] = call_drop_rate_erab_ngbr_
    
    #volte_call_drop_rate_erab_gbr
    volte_call_drop_result = {}
    for band in bands:
      volte_call_drop_rate_erab_gbr_by_region = base_queryset.filter(
        volte_call_drop_rate_erab_gbr__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_volte_call_drop=Avg('volte_call_drop_rate_erab_gbr'),
        count_fail_cell=Count(Case(When(volte_call_drop_rate_erab_gbr__gt=1, then=1)))
      ).order_by('sitebasicinfo__region')

      volte_call_drop_rate_erab_gbr_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in volte_call_drop_rate_erab_gbr_by_region:
        volte_call_drop_rate_erab_gbr_['region'].append(item['sitebasicinfo__region__region'])
        volte_call_drop_rate_erab_gbr_['avg'].append(item['avg_volte_call_drop'])
        volte_call_drop_rate_erab_gbr_['count_fail'].append(item['count_fail_cell'])

      volte_call_drop_result[band] = volte_call_drop_rate_erab_gbr_
    
    #hosr_intra_frequency
    hosr_intra_frequency_result = {}
    for band in bands:
      hosr_intra_frequency_by_region = base_queryset.filter(
        hosr_intra_frequency__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_hosr_intra_frequency=Avg('hosr_intra_frequency'),
        count_fail_cell=Count(Case(When(hosr_intra_frequency__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      hosr_intra_frequency_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in hosr_intra_frequency_by_region:
        hosr_intra_frequency_['region'].append(item['sitebasicinfo__region__region'])
        hosr_intra_frequency_['avg'].append(item['avg_hosr_intra_frequency'])
        hosr_intra_frequency_['count_fail'].append(item['count_fail_cell'])

      hosr_intra_frequency_result[band] = hosr_intra_frequency_
    
    #hosr_inter_frequency
    hosr_inter_frequency_result = {}
    for band in bands:
      hosr_inter_frequency_by_region = base_queryset.filter(
        hosr_inter_frequency__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_hosr_inter_frequency=Avg('hosr_inter_frequency'),
        count_fail_cell=Count(Case(When(hosr_inter_frequency__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      hosr_inter_frequency_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in hosr_inter_frequency_by_region:
        hosr_inter_frequency_['region'].append(item['sitebasicinfo__region__region'])
        hosr_inter_frequency_['avg'].append(item['avg_hosr_inter_frequency'])
        hosr_inter_frequency_['count_fail'].append(item['count_fail_cell'])

      hosr_inter_frequency_result[band] = hosr_inter_frequency_
    
    #x2_handover_out_success_rate
    x2_handover_out_success_rate_result = {}
    for band in bands:
      x2_handover_out_success_rate_by_region = base_queryset.filter(
        x2_handover_out_success_rate__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_x2_handover_out_success=Avg('x2_handover_out_success_rate'),
        count_fail_cell=Count(Case(When(x2_handover_out_success_rate__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      x2_handover_out_success_rate_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in x2_handover_out_success_rate_by_region:
        x2_handover_out_success_rate_['region'].append(item['sitebasicinfo__region__region'])
        x2_handover_out_success_rate_['avg'].append(item['avg_x2_handover_out_success'])
        x2_handover_out_success_rate_['count_fail'].append(item['count_fail_cell'])

      x2_handover_out_success_rate_result[band] = x2_handover_out_success_rate_

    #x2_handover_in_success_rate
    x2_handover_in_success_rate_result = {}
    for band in bands:
      x2_handover_in_success_rate_by_region = base_queryset.filter(
        x2_handover_in_success_rate__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_x2_handover_in_success=Avg('x2_handover_in_success_rate'),
        count_fail_cell=Count(Case(When(x2_handover_out_success_rate__lt=99, then=1)))
      ).order_by('sitebasicinfo__region')

      x2_handover_in_success_rate_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in x2_handover_in_success_rate_by_region:
        x2_handover_in_success_rate_['region'].append(item['sitebasicinfo__region__region'])
        x2_handover_in_success_rate_['avg'].append(item['avg_x2_handover_in_success'])
        x2_handover_in_success_rate_['count_fail'].append(item['count_fail_cell'])

      x2_handover_in_success_rate_result[band] = x2_handover_in_success_rate_
    
    #dl_bler
    dl_bler_result = {}
    for band in bands:
      dl_bler_by_region = base_queryset.filter(
        dl_bler__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_dl_bler=Avg('dl_bler'),
        count_fail_cell=Count(Case(When(dl_bler__gt=1, then=1)))
      ).order_by('sitebasicinfo__region')

      dl_bler_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in dl_bler_by_region:
        dl_bler_['region'].append(item['sitebasicinfo__region__region'])
        dl_bler_['avg'].append(item['avg_dl_bler'])
        dl_bler_['count_fail'].append(item['count_fail_cell'])

      dl_bler_result[band] = dl_bler_

    #ul_bler
    ul_bler_result = {}
    for band in bands:
      ul_bler_by_region = base_queryset.filter(
        ul_bler__isnull=False, band=band
      ).values('sitebasicinfo__region__region').annotate(
        avg_ul_bler=Avg('ul_bler'),
        count_fail_cell=Count(Case(When(ul_bler__gt=1, then=1)))
      ).order_by('sitebasicinfo__region')

      ul_bler_ = {
        'region': [],
        'avg': [],
        'count_fail': []
      }

      for item in ul_bler_by_region:
        ul_bler_['region'].append(item['sitebasicinfo__region__region'])
        ul_bler_['avg'].append(item['avg_ul_bler'])
        ul_bler_['count_fail'].append(item['count_fail_cell'])

      ul_bler_result[band] = ul_bler_

    return Response({
      'cell_availability_by_region': {
        'band': cell_availability_result
      },
      'attach_setup_success_rate_by_region': {
        'band': attach_setup_success_result
      },
      'rrc_setup_success_rate_by_region': {
        'band': rrc_setup_success_result
      },
      'erab_setup_success_rate_ngbr_by_region': {
        'band': erab_setup_success_result
      },
      'call_drop_rate_erab_ngbr_by_region': {
        'band': call_drop_result
      },
      'volte_call_drop_rate_erab_gbr_by_region': {
        'band': volte_call_drop_result
      },
      'hosr_intra_frequency_by_region': {
        'band': hosr_intra_frequency_result
      },
      'hosr_inter_frequency_by_region': {
        'band': hosr_inter_frequency_result
      },
      'x2_handover_out_success_rate_by_region': {
        'band': x2_handover_out_success_rate_result
      },
      'x2_handover_in_success_rate_by_region': {
        'band': x2_handover_in_success_rate_result
      },
      'dl_bler_by_region': {
        'band': dl_bler_result
      },
      'ul_bler_by_region': {
        'band': ul_bler_result
      }
    })
  
class StatisticWeeklyAPIView(ListAPIView):
  def get_queryset(self):
    base_queryset = StatisticCalculated.objects.all()
    return base_queryset
  def get(self, request, *args, **kwargs):
    base_queryset = self.get_queryset()
    lastweeknum = base_queryset.values_list('weeknum', flat=True).distinct().order_by('weeknum').last()
    statistics_by_band = defaultdict(list)

    statistics = base_queryset.filter(weeknum=lastweeknum, category="All").values(
      'band', 'cell_availability', 'attach_setup_success_rate', 'rrc_setup_success_rate', 'erab_setup_success_rate_ngbr',
      'volte_setup_success_rate_gbr', 'call_drop_rate_erab_ngbr', 'volte_call_drop_rate_erab_gbr', 
      'hosr_intra_frequency', 'hosr_inter_frequency', 'x2_handover_out_success_rate', 'x2_handover_in_success_rate',
      's1_handover_out_success_rate', 's1_handover_in_success_rate', 'dl_bler', 'ul_bler')

    for stat in statistics:
      band = stat['band']
      statistics_by_band[band].append({
        'cell_availability': stat['cell_availability'],
        'attach_setup_success_rate': stat['attach_setup_success_rate'],
        'rrc_setup_success_rate': stat['rrc_setup_success_rate'],
        'erab_setup_success_rate_ngbr': stat['erab_setup_success_rate_ngbr'],
        'volte_setup_success_rate_gbr': stat['volte_setup_success_rate_gbr'],
        'call_drop_rate_erab_ngbr': stat['call_drop_rate_erab_ngbr'],
        'volte_call_drop_rate_erab_gbr': stat['volte_call_drop_rate_erab_gbr'],
        'hosr_intra_frequency': stat['hosr_intra_frequency'],
        'hosr_inter_frequency': stat['hosr_inter_frequency'],
        'x2_handover_out_success_rate': stat['x2_handover_out_success_rate'],
        'x2_handover_in_success_rate': stat['x2_handover_in_success_rate'],
        's1_handover_out_success_rate': stat['s1_handover_out_success_rate'],
        's1_handover_in_success_rate': stat['s1_handover_in_success_rate'],
        'dl_bler': stat['dl_bler'],
        'ul_bler': stat['ul_bler'],
      })
    return Response({
      'statistics_by_band': statistics_by_band,
      'lastweeknum': lastweeknum
    })
  
class StatisticClusterbaseView(ListAPIView):
  serializer_class = StatisticDataClusterSerializer

  def get_queryset(self):
    return StatisticData.objects.values('cluster', 'band').annotate(
      connestabsucc_sum=Coalesce(Sum('connestabsucc'), 0),
      connestabatt_sum=Coalesce(Sum('connestabatt'), 0),
      s1connestabsucc_sum=Coalesce(Sum('s1connestabsucc'), 0),
      s1connestabatt_sum=Coalesce(Sum('s1connestabatt'), 0),
      establnitsuccnbr_sum=Coalesce(Sum('establnitsuccnbr'), 0),
      establnitattnbr_sum=Coalesce(Sum('establnitattnbr'), 0),
    ).annotate(
      attach_setup_success_rate=Case(
        When(
          connestabatt_sum=0,
          then=Value(0.0)
        ),
        When(
          s1connestabatt_sum=0,
          then=Value(0.0)
        ),
        When(
          establnitattnbr_sum=0,
          then=Value(0.0)
        ),
        default=ExpressionWrapper(
          F('connestabsucc_sum') / F('connestabatt_sum') *
          F('s1connestabsucc_sum') / F('s1connestabatt_sum') *
          F('establnitsuccnbr_sum') / F('establnitattnbr_sum') * 100,
          output_field=FloatField()
        ),
        output_field=FloatField()
      )
    ).order_by('cluster')
  
class FilteredStatisticData(APIView):
  def get(self, request, *args, **kwargs):
    queryset = StatisticData.objects.exclude(sitestatus='Dismantled')

    region = request.query_params.get('region')
    # band = request.query_params.get('band')
    cluster = request.query_params.get('cluster')
    siteid = request.query_params.get('siteid')

    if region:
      queryset = queryset.filter(region__region=region)
    # if band:
    #   queryset = queryset.filter(band=band)
    if cluster:
      queryset = queryset.filter(cluster=cluster)
    if siteid:
      queryset = queryset.filter(uid=siteid)
    
    #SITE COUNT BY BAND
    sitecount_all = queryset.values('sysid').distinct().count()
    sitecount_byband = {'band': [], 'count': []}
    site_count = queryset.values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      sitecount_byband['band'].append(item['band'])
      sitecount_byband['count'].append(item['count'])

    #CELL COUNT BY BAND
    cellcount_all = queryset.values('uid').distinct().count()
    cellcount_byband = {'band': [], 'count': []}
    cell_count = queryset.values('band').annotate(count=Count('uid', distinct=True)).order_by('band')
    for item in cell_count:
      cellcount_byband['band'].append(item['band'])
      cellcount_byband['count'].append(item['count'])

    #ACTIVE USER INFO
    activeusercalculate = queryset.values('band').annotate(
      avg_connectno=Avg('connectno'), sum_connectno=Sum('connectno'),
      avg_connectmax=Avg('connectmax'), sum_connectmax=Sum('connectmax')
    ).order_by('band')
    activeuserInfo = {'band': [], 'avg_connectno': [], 'sum_connectno': [], 'avg_connectmax': [], 'sum_connectmax': []}
    for item in activeusercalculate:
      activeuserInfo['band'].append(item['band'])
      activeuserInfo['avg_connectno'].append(item['avg_connectno'])
      activeuserInfo['sum_connectno'].append(item['sum_connectno'])
      activeuserInfo['avg_connectmax'].append(item['avg_connectmax'])
      activeuserInfo['sum_connectmax'].append(item['sum_connectmax'])

    #PRB UTILIZATION INFO
    prbutilizationcalculate = queryset.values('band').annotate(
      avg_prbdl=Avg('totalprbdl'), max_prbdl=Max('totalprbdl'),
      avg_prbul=Avg('totalprbul'), max_prbul=Max('totalprbul')
    ).order_by('band')
    prbutilizationInfo = {'band': [], 'avg_prbdl': [], 'max_prbdl': [], 'avg_prbul': [], 'max_prbul': []}
    for item in prbutilizationcalculate:
      prbutilizationInfo['band'].append(item['band'])
      prbutilizationInfo['avg_prbdl'].append(item['avg_prbdl'])
      prbutilizationInfo['max_prbdl'].append(item['max_prbdl'])
      prbutilizationInfo['avg_prbul'].append(item['avg_prbul'])
      prbutilizationInfo['max_prbul'].append(item['max_prbul'])

    #ALL STATISTIC DATA 
    allitemscalculate = queryset.values('band').annotate(
      cellunavailabletimedown=Sum('cellunavailabletimedown'),
      cellunavailabletimelock=Sum('cellunavailabletimelock'),
      cellavail_pmperiodtime=Sum('cellavail_pmperiodtime'),
      connestabsucc=Sum('connestabsucc'),
      connestabatt=Sum('connestabatt'),
      s1connestabsucc=Sum('s1connestabsucc'),
      s1connestabatt=Sum('s1connestabatt'),
      establnitsuccnbr=Sum('establnitsuccnbr'),
      establnitattnbr=Sum('establnitattnbr'),
      establnitsuccnbr_qci59=Sum('establnitsuccnbr_qci59'),
      estabaddsuccnbr_qci59=Sum('estabaddsuccnbr_qci59'),
      establnitattnbr_qci59=Sum('establnitattnbr_qci59'),
      estabaddattnbr_qci59=Sum('estabaddattnbr_qci59'),
      establnitsuccnbr_qci1=Sum('establnitsuccnbr_qci1'),
      estabaddsuccnbr_qci1=Sum('estabaddsuccnbr_qci1'),
      establnitattnbr_qci1=Sum('establnitattnbr_qci1'),
      estabaddattnbr_qci1=Sum('estabaddattnbr_qci1'),
      calldropqci_eccbdspauditrlcmaccallrelease_qci59=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      calldropqci_eccbrcvresetrequestfromecmb_qci59=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      calldropqci_eccbrcvcellreleaseindfromecmb_qci59=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      calldropqci_eccbradiolinkfailure_qci59=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      calldropqci_eccbdspauditmaccallrelease_qci59=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      calldropqci_eccbarqmaxretransmission_qci59=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      calldropqci_eccbdspauditrlccallrelease_qci59=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      calldropqci_eccbtmoutrrcconnectionreconfig_qci59=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      calldropqci_eccbtmoutrrcconnectionrestablish_qci59=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      calldropqci_eccbsisctpoutofsevice_qci59=Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
      interx2insucc_qci59=Sum('interx2insucc_qci59'),
      inters1insucc_qci59=Sum('inters1insucc_qci59'),
      sumvoltecalldropqci=Sum('sumvoltecalldropqci'),
      sumvolteestablnitsuccnbr=Sum('sumvolteestablnitsuccnbr'),
      sumvolteestabaddsuccnbr=Sum('sumvolteestabaddsuccnbr'),
      sumvolteerablncominghosuccnbr=Sum('sumvolteerablncominghosuccnbr'),
      intrafreqoutsucc=Sum('intrafreqoutsucc'),
      intrafreqoutatt=Sum('intrafreqoutatt'),
      interfreqmeasgapoutsucc=Sum('interfreqmeasgapoutsucc'),
      interfreqnomeasgapoutsucc=Sum('interfreqnomeasgapoutsucc'),
      interfreqmeasgapoutatt=Sum('interfreqmeasgapoutatt'),
      interfreqnomeasgapoutatt=Sum('interfreqnomeasgapoutatt'),
      interx2outsucc=Sum('interx2outsucc'),
      interx2outatt=Sum('interx2outatt'),
      interx2insucc=Sum('interx2insucc'),
      interx2inatt=Sum('interx2inatt'),
      inters1outsucc=Sum('inters1outsucc'),
      inters1outatt=Sum('inters1outatt'),
      inters1insucc=Sum('inters1insucc'),
      inters1inatt=Sum('inters1inatt'),
      dltransmissionnackedretrans=Sum('dltransmissionnackedretrans'),
      dltransmissionretrans0_600=Sum('dltransmissionretrans0_600'),
      ultransmissionnackedretrans=Sum('ultransmissionnackedretrans'),
      ultransmissionretrans0_600=Sum('ultransmissionretrans0_600'),
      connectno=Sum('connectno'),
      connectmax=Sum('connectmax'),
      totalprbdl=Sum('totalprbdl'),
      totalprbul=Sum('totalprbul'),
    )
    lawdataSumInfo = {}
    for item in allitemscalculate:
      band = item.pop('band')
      lawdataSumInfo[band] = item

    return Response({
      'sitecount_all': sitecount_all, 'sitecount_byband': sitecount_byband, 'cellcount_all': cellcount_all, 'cellcount_byband': cellcount_byband,
      'activeuserInfo': activeuserInfo, 'prbutilizationInfo': prbutilizationInfo, 'lawdataSumInfo': lawdataSumInfo
    })
  
class StatisticS1InHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['s1_handover_in_success_rate'] for stat in statistics_all]
    s1inho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    values_23 = [stat['s1_handover_in_success_rate'] for stat in statistics_23]
    s1inho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    values_26 = [stat['s1_handover_in_success_rate'] for stat in statistics_26]
    s1inho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    values_800 = [stat['s1_handover_in_success_rate'] for stat in statistics_800]
    s1inho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    regional_values_23 = [stat['s1_handover_in_success_rate'] for stat in regional_stat_23]
    regional_s1inho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    regional_values_26 = [stat['s1_handover_in_success_rate'] for stat in regional_stat_26]
    regional_s1inho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 's1_handover_in_success_rate').order_by('weeknum')
    regional_values_800 = [stat['s1_handover_in_success_rate'] for stat in regional_stat_800]
    regional_s1inho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #X2 OUT HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(s1_handover_in_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(s1_handover_in_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #X2 OUT HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_in_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_in_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_in_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_in_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #X2 OUT HO DATA PROCESSING
    s1inhocategorys = celldata_queryset.aggregate(
      Sum_inters1insucc=Sum('inters1insucc'), Sum_inters1inatt=Sum('inters1inatt'),
    )

    s1inhocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_inters1insucc=Sum('inters1insucc'), Sum_inters1inatt=Sum('inters1inatt'),
    )

    bands = [item['band'] for item in s1inhocategorysbyband]

    s1InHONominatecountbyBand = [item['Sum_inters1inatt'] for item in s1inhocategorysbyband]
    s1InHOdeNominatecountbyBand = [item['Sum_inters1insucc'] for item in s1inhocategorysbyband]
    Totals1InHONominate = sum(s1InHONominatecountbyBand)
    Totals1InHOdeNominate = sum(s1InHOdeNominatecountbyBand)
    Totals1InHONominate_byband = {
      'overall': {'Totals1InHONominate': Totals1InHONominate, 'Totals1InHOdeNominate': Totals1InHOdeNominate},
      'by_band': {}
    }
    if Totals1InHONominate > 0:
      s1InHOAttemptbyband = [value / Totals1InHONominate * 100 for value in s1InHONominatecountbyBand]
    else:
      s1InHOAttemptbyband = [0 for _ in s1InHONominatecountbyBand]
    Totals1InHONominate_byband['by_band'] = {'band': bands, 'ratio': s1InHOAttemptbyband, 'counts': s1InHONominatecountbyBand}

    s1inhofallbybandall = {
      'overall': {
        's1inhorate': (s1inhocategorys['Sum_inters1insucc'] / s1inhocategorys['Sum_inters1inatt']) * 100,
        'failcount': (s1inhocategorys['Sum_inters1inatt'] - s1inhocategorys['Sum_inters1insucc'])
      },
      'by_band': {}
    }
    s1inhofailcount = [(item['Sum_inters1inatt'] - item['Sum_inters1insucc']) for item in s1inhocategorysbyband]
    s1inhofailcounttotal = sum(s1inhofailcount)
    x2outhorate = [((item['Sum_inters1insucc'] / item['Sum_inters1inatt'])) * 100 for item in s1inhocategorysbyband
    ]
    if s1inhofailcounttotal > 0:
      failratebyband = [value / s1inhofailcounttotal * 100 for value in s1inhofailcount]
    else:
      failratebyband = [0 for _ in s1inhofailcount]
    s1inhofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': s1inhofailcount,
      'calldroprate': x2outhorate
    }

    s1inhobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    s1inhobyband_cluster_23 = s1inhobyband_cluster_23.annotate(
      s1insucc_sum=Sum('inters1outsucc'), s1inatt_sum=Sum('inters1outatt'),
    )
    s1inhobyband_cluster_23 = s1inhobyband_cluster_23.annotate(
      Sum_s1inhofail=F('s1inatt_sum') - F('s1insucc_sum')
    )
    s1inhobyband_cluster_23 = s1inhobyband_cluster_23.annotate(
        s1inhofailtotal=Coalesce(F('Sum_s1inhofail'), Value(0))
    )
    impact_clusters_23 = s1inhobyband_cluster_23.order_by('-s1inhofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 's1inhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['s1inhofailtotal'].append(cluster['s1inhofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    s1inhobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    s1inhobyband_cluster_26 = s1inhobyband_cluster_26.annotate(
      s1insucc_sum=Sum('inters1outsucc'), s1inatt_sum=Sum('inters1outatt'),
    )
    s1inhobyband_cluster_26 = s1inhobyband_cluster_26.annotate(
      Sum_s1inhofail=F('s1inatt_sum') - F('s1insucc_sum')
    )
    s1inhobyband_cluster_26 = s1inhobyband_cluster_26.annotate(
        s1inhofailtotal=Coalesce(F('Sum_s1inhofail'), Value(0))
    )
    impact_clusters_26 = s1inhobyband_cluster_26.order_by('-s1inhofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 's1inhofailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['s1inhofailtotal'].append(cluster['s1inhofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    s1inhobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    s1inhobyband_cluster_800 = s1inhobyband_cluster_800.annotate(
      s1insucc_sum=Sum('inters1outsucc'), s1inatt_sum=Sum('inters1outatt'),
    )
    s1inhobyband_cluster_800 = s1inhobyband_cluster_800.annotate(
      Sum_s1inhofail=F('s1inatt_sum') - F('s1insucc_sum')
    )
    s1inhobyband_cluster_800 = s1inhobyband_cluster_800.annotate(
        s1inhofailtotal=Coalesce(F('Sum_s1inhofail'), Value(0))
    )
    impact_clusters_800 = s1inhobyband_cluster_800.order_by('-s1inhofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 's1inhofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['s1inhofailtotal'].append(cluster['s1inhofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      's1inho_trend_all': s1inho_trend_all, 's1inho_trend_23': s1inho_trend_23, 's1inho_trend_26': s1inho_trend_26, 's1inho_trend_800': s1inho_trend_800,
      'regional_s1inho_trend_23': regional_s1inho_trend_23, 'regional_s1inho_trend_26': regional_s1inho_trend_26, 'regional_s1inho_trend_800': regional_s1inho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'Totals1InHONominate_byband': Totals1InHONominate_byband,
      's1inhofallbybandall': s1inhofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

class StatisticS1OutHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['s1_handover_out_success_rate'] for stat in statistics_all]
    s1outho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    values_23 = [stat['s1_handover_out_success_rate'] for stat in statistics_23]
    s1outho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    values_26 = [stat['s1_handover_out_success_rate'] for stat in statistics_26]
    s1outho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    values_800 = [stat['s1_handover_out_success_rate'] for stat in statistics_800]
    s1outho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    regional_values_23 = [stat['s1_handover_out_success_rate'] for stat in regional_stat_23]
    regional_s1outho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    regional_values_26 = [stat['s1_handover_out_success_rate'] for stat in regional_stat_26]
    regional_s1outho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 's1_handover_out_success_rate').order_by('weeknum')
    regional_values_800 = [stat['s1_handover_out_success_rate'] for stat in regional_stat_800]
    regional_s1outho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #X2 OUT HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(s1_handover_out_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(s1_handover_out_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #X2 OUT HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_out_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_out_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_out_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(s1_handover_out_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #X2 OUT HO DATA PROCESSING
    s1outhocategorys = celldata_queryset.aggregate(
      Sum_inters1outsucc=Sum('inters1outsucc'), Sum_inters1outatt=Sum('inters1outatt'),
    )

    s1outhocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_inters1outsucc=Sum('inters1outsucc'), Sum_inters1outatt=Sum('inters1outatt'),
    )

    bands = [item['band'] for item in s1outhocategorysbyband]

    s1OutHONominatecountbyBand = [item['Sum_inters1outatt'] for item in s1outhocategorysbyband]
    s1OutHOdeNominatecountbyBand = [item['Sum_inters1outsucc'] for item in s1outhocategorysbyband]
    Totals1OutHONominate = sum(s1OutHONominatecountbyBand)
    Totals1OutHOdeNominate = sum(s1OutHOdeNominatecountbyBand)
    Totals1OutHONominate_byband = {
      'overall': {'Totals1OutHONominate': Totals1OutHONominate, 'Totals1OutHOdeNominate': Totals1OutHOdeNominate},
      'by_band': {}
    }
    if Totals1OutHONominate > 0:
      s1OutHOAttemptbyband = [value / Totals1OutHONominate * 100 for value in s1OutHONominatecountbyBand]
    else:
      s1OutHOAttemptbyband = [0 for _ in s1OutHONominatecountbyBand]
    Totals1OutHONominate_byband['by_band'] = {'band': bands, 'ratio': s1OutHOAttemptbyband, 'counts': s1OutHONominatecountbyBand}

    s1outhofallbybandall = {
      'overall': {
        's1outhorate': (s1outhocategorys['Sum_inters1outsucc'] / s1outhocategorys['Sum_inters1outatt']) * 100,
        'failcount':(s1outhocategorys['Sum_inters1outatt'] - s1outhocategorys['Sum_inters1outsucc'])
      },
      'by_band': {}
    }
    s1outhofailcount = [(item['Sum_inters1outatt'] - item['Sum_inters1outsucc']) for item in s1outhocategorysbyband]
    s1outhofailcounttotal = sum(s1outhofailcount)
    x2outhorate = [((item['Sum_inters1outsucc'] / item['Sum_inters1outatt'])) * 100 for item in s1outhocategorysbyband
    ]
    if s1outhofailcounttotal > 0:
      failratebyband = [value / s1outhofailcounttotal * 100 for value in s1outhofailcount]
    else:
      failratebyband = [0 for _ in s1outhofailcount]
    s1outhofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': s1outhofailcount,
      'calldroprate': x2outhorate
    }

    s1outhobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    s1outhobyband_cluster_23 = s1outhobyband_cluster_23.annotate(
      s1outsucc_sum=Sum('inters1outsucc'), s1outatt_sum=Sum('inters1outatt'),
    )
    s1outhobyband_cluster_23 = s1outhobyband_cluster_23.annotate(
      Sum_s1outhofail=F('s1outatt_sum') - F('s1outsucc_sum')
    )
    s1outhobyband_cluster_23 = s1outhobyband_cluster_23.annotate(
        s1outhofailtotal=Coalesce(F('Sum_s1outhofail'), Value(0))
    )
    impact_clusters_23 = s1outhobyband_cluster_23.order_by('-s1outhofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 's1outhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['s1outhofailtotal'].append(cluster['s1outhofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    s1outhobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    s1outhobyband_cluster_26 = s1outhobyband_cluster_26.annotate(
      s1outsucc_sum=Sum('inters1outsucc'), s1outatt_sum=Sum('inters1outatt'),
    )
    s1outhobyband_cluster_26 = s1outhobyband_cluster_26.annotate(
      Sum_s1outhofail=F('s1outatt_sum') - F('s1outsucc_sum')
    )
    s1outhobyband_cluster_26 = s1outhobyband_cluster_26.annotate(
        s1outhofailtotal=Coalesce(F('Sum_s1outhofail'), Value(0))
    )
    impact_clusters_26 = s1outhobyband_cluster_26.order_by('-s1outhofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 's1outhofailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['s1outhofailtotal'].append(cluster['s1outhofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    s1outhobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    s1outhobyband_cluster_800 = s1outhobyband_cluster_800.annotate(
      s1outsucc_sum=Sum('inters1outsucc'), s1outatt_sum=Sum('inters1outatt'),
    )
    s1outhobyband_cluster_800 = s1outhobyband_cluster_800.annotate(
      Sum_s1outhofail=F('s1outatt_sum') - F('s1outsucc_sum')
    )
    s1outhobyband_cluster_800 = s1outhobyband_cluster_800.annotate(
        s1outhofailtotal=Coalesce(F('Sum_s1outhofail'), Value(0))
    )
    impact_clusters_800 = s1outhobyband_cluster_800.order_by('-s1outhofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 's1outhofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['s1outhofailtotal'].append(cluster['s1outhofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      's1outho_trend_all': s1outho_trend_all, 's1outho_trend_23': s1outho_trend_23, 's1outho_trend_26': s1outho_trend_26, 's1outho_trend_800': s1outho_trend_800,
      'regional_s1outho_trend_23': regional_s1outho_trend_23, 'regional_s1outho_trend_26': regional_s1outho_trend_26, 'regional_s1outho_trend_800': regional_s1outho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'Totals1OutHONominate_byband': Totals1OutHONominate_byband,
      's1outhofallbybandall': s1outhofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

  
class StatisticX2inHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['x2_handover_in_success_rate'] for stat in statistics_all]
    x2inho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    values_23 = [stat['x2_handover_in_success_rate'] for stat in statistics_23]
    x2inho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    values_26 = [stat['x2_handover_in_success_rate'] for stat in statistics_26]
    x2inho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    values_800 = [stat['x2_handover_in_success_rate'] for stat in statistics_800]
    x2inho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    regional_values_23 = [stat['x2_handover_in_success_rate'] for stat in regional_stat_23]
    regional_x2inho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    regional_values_26 = [stat['x2_handover_in_success_rate'] for stat in regional_stat_26]
    regional_x2inho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'x2_handover_in_success_rate').order_by('weeknum')
    regional_values_800 = [stat['x2_handover_in_success_rate'] for stat in regional_stat_800]
    regional_x2inho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #X2 OUT HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(x2_handover_in_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(x2_handover_in_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #X2 OUT HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_in_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_in_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_in_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_in_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #X2 OUT HO DATA PROCESSING
    x2inhocategorys = celldata_queryset.aggregate(
      Sum_interx2insucc=Sum('interx2insucc'), Sum_interx2inatt=Sum('interx2inatt'),
    )

    x2inhocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_interx2insucc=Sum('interx2insucc'), Sum_interx2inatt=Sum('interx2inatt'),
    )

    bands = [item['band'] for item in x2inhocategorysbyband]

    x2InHONominatecountbyBand = [item['Sum_interx2inatt'] for item in x2inhocategorysbyband]
    x2InHOdeNominatecountbyBand = [item['Sum_interx2insucc'] for item in x2inhocategorysbyband]
    Totalx2InHONominate = sum(x2InHONominatecountbyBand)
    Totalx2InHOdeNominate = sum(x2InHOdeNominatecountbyBand)
    Totalx2InHONominate_byband = {
      'overall': {'Totalx2InHONominate': Totalx2InHONominate, 'Totalx2InHOdeNominate': Totalx2InHOdeNominate},
      'by_band': {}
    }
    if Totalx2InHONominate > 0:
      x2InHOAttemptbyband = [value / Totalx2InHONominate * 100 for value in x2InHONominatecountbyBand]
    else:
      x2InHOAttemptbyband = [0 for _ in x2InHONominatecountbyBand]
    Totalx2InHONominate_byband['by_band'] = {'band': bands, 'ratio': x2InHOAttemptbyband, 'counts': x2InHONominatecountbyBand}

    x2inhofallbybandall = {
      'overall': {
        'x2inhorate': (x2inhocategorys['Sum_interx2insucc'] / x2inhocategorys['Sum_interx2inatt']) * 100,
        'failcount':(x2inhocategorys['Sum_interx2inatt'] - x2inhocategorys['Sum_interx2insucc'])
      },
      'by_band': {}
    }
    x2inhofailcount = [(item['Sum_interx2inatt'] - item['Sum_interx2insucc']) for item in x2inhocategorysbyband]
    x2inhofailcounttotal = sum(x2inhofailcount)
    x2outhorate = [((item['Sum_interx2insucc'] / item['Sum_interx2inatt'])) * 100 for item in x2inhocategorysbyband
    ]
    if x2inhofailcounttotal > 0:
      failratebyband = [value / x2inhofailcounttotal * 100 for value in x2inhofailcount]
    else:
      failratebyband = [0 for _ in x2inhofailcount]
    x2inhofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': x2inhofailcount,
      'calldroprate': x2outhorate
    }

    x2inhobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    x2inhobyband_cluster_23 = x2inhobyband_cluster_23.annotate(
      x2insucc_sum=Sum('interx2insucc'), x2outatt_sum=Sum('interx2inatt'),
    )
    x2inhobyband_cluster_23 = x2inhobyband_cluster_23.annotate(
      Sum_x2inhofail=F('x2outatt_sum') - F('x2insucc_sum')
    )
    x2inhobyband_cluster_23 = x2inhobyband_cluster_23.annotate(
        x2inhofailtotal=Coalesce(F('Sum_x2inhofail'), Value(0))
    )
    impact_clusters_23 = x2inhobyband_cluster_23.order_by('-x2inhofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'x2inhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['x2inhofailtotal'].append(cluster['x2inhofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    x2inhobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    x2inhobyband_cluster_26 = x2inhobyband_cluster_26.annotate(
      x2insucc_sum=Sum('interx2insucc'), x2outatt_sum=Sum('interx2inatt'),
    )
    x2inhobyband_cluster_26 = x2inhobyband_cluster_26.annotate(
      Sum_x2inhofail=F('x2outatt_sum') - F('x2insucc_sum')
    )
    x2inhobyband_cluster_26 = x2inhobyband_cluster_26.annotate(
        x2inhofailtotal=Coalesce(F('Sum_x2inhofail'), Value(0))
    )
    impact_clusters_26 = x2inhobyband_cluster_26.order_by('-x2inhofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'x2inhofailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['x2inhofailtotal'].append(cluster['x2inhofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    x2inhobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    x2inhobyband_cluster_800 = x2inhobyband_cluster_800.annotate(
      x2insucc_sum=Sum('interx2insucc'), x2outatt_sum=Sum('interx2inatt'),
    )
    x2inhobyband_cluster_800 = x2inhobyband_cluster_800.annotate(
      Sum_x2inhofail=F('x2outatt_sum') - F('x2insucc_sum')
    )
    x2inhobyband_cluster_800 = x2inhobyband_cluster_800.annotate(
        x2inhofailtotal=Coalesce(F('Sum_x2inhofail'), Value(0))
    )
    impact_clusters_800 = x2inhobyband_cluster_800.order_by('-x2inhofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'x2inhofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['x2inhofailtotal'].append(cluster['x2inhofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      'x2inho_trend_all': x2inho_trend_all, 'x2inho_trend_23': x2inho_trend_23, 'x2inho_trend_26': x2inho_trend_26, 'x2inho_trend_800': x2inho_trend_800,
      'regional_x2inho_trend_23': regional_x2inho_trend_23, 'regional_x2inho_trend_26': regional_x2inho_trend_26, 'regional_x2inho_trend_800': regional_x2inho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'Totalx2InHONominate_byband': Totalx2InHONominate_byband,
      'x2inhofallbybandall': x2inhofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

class StatisticX2OutHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['x2_handover_out_success_rate'] for stat in statistics_all]
    x2outho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    values_23 = [stat['x2_handover_out_success_rate'] for stat in statistics_23]
    x2outho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    values_26 = [stat['x2_handover_out_success_rate'] for stat in statistics_26]
    x2outho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    values_800 = [stat['x2_handover_out_success_rate'] for stat in statistics_800]
    x2outho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #X2 OUT HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    regional_values_23 = [stat['x2_handover_out_success_rate'] for stat in regional_stat_23]
    regional_x2outho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    regional_values_26 = [stat['x2_handover_out_success_rate'] for stat in regional_stat_26]
    regional_x2outho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'x2_handover_out_success_rate').order_by('weeknum')
    regional_values_800 = [stat['x2_handover_out_success_rate'] for stat in regional_stat_800]
    regional_x2outho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #X2 OUT HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(x2_handover_out_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(x2_handover_out_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #X2 OUT HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_out_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_out_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_out_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(x2_handover_out_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #X2 OUT HO DATA PROCESSING
    x2outhocategorys = celldata_queryset.aggregate(
      Sum_interx2outsucc=Sum('interx2outsucc'), Sum_interx2outatt=Sum('interx2outatt'),
    )

    x2outhocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_interx2outsucc=Sum('interx2outsucc'), Sum_interx2outatt=Sum('interx2outatt'),
    )

    bands = [item['band'] for item in x2outhocategorysbyband]

    x2OutHONominatecountbyBand = [item['Sum_interx2outatt'] for item in x2outhocategorysbyband]
    x2OutHOdeNominatecountbyBand = [item['Sum_interx2outsucc'] for item in x2outhocategorysbyband]
    Totalx2OutHONominate = sum(x2OutHONominatecountbyBand)
    Totalx2OutHOdeNominate = sum(x2OutHOdeNominatecountbyBand)
    Totalx2OutHONominate_byband = {
      'overall': {'Totalx2OutHONominate': Totalx2OutHONominate, 'Totalx2OutHOdeNominate': Totalx2OutHOdeNominate},
      'by_band': {}
    }
    if Totalx2OutHONominate > 0:
      x2OutHOAttemptbyband = [value / Totalx2OutHONominate * 100 for value in x2OutHONominatecountbyBand]
    else:
      x2OutHOAttemptbyband = [0 for _ in x2OutHONominatecountbyBand]
    Totalx2OutHONominate_byband['by_band'] = {'band': bands, 'ratio': x2OutHOAttemptbyband, 'counts': x2OutHONominatecountbyBand}

    x2outhofallbybandall = {
      'overall': {
        'x2outhorate': (x2outhocategorys['Sum_interx2outsucc'] / x2outhocategorys['Sum_interx2outatt']) * 100,
        'failcount':(x2outhocategorys['Sum_interx2outatt'] - x2outhocategorys['Sum_interx2outsucc'])
      },
      'by_band': {}
    }
    x2outhofailcount = [(item['Sum_interx2outatt'] - item['Sum_interx2outsucc']) for item in x2outhocategorysbyband]
    x2outhofailcounttotal = sum(x2outhofailcount)
    x2outhorate = [((item['Sum_interx2outsucc'] / item['Sum_interx2outatt'])) * 100 for item in x2outhocategorysbyband
    ]
    if x2outhofailcounttotal > 0:
      failratebyband = [value / x2outhofailcounttotal * 100 for value in x2outhofailcount]
    else:
      failratebyband = [0 for _ in x2outhofailcount]
    x2outhofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': x2outhofailcount,
      'calldroprate': x2outhorate
    }

    x2outhobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    x2outhobyband_cluster_23 = x2outhobyband_cluster_23.annotate(
      x2outsucc_sum=Sum('interx2outsucc'), x2outatt_sum=Sum('interx2outatt'),
    )
    x2outhobyband_cluster_23 = x2outhobyband_cluster_23.annotate(
      Sum_x2outhofail=F('x2outatt_sum') - F('x2outsucc_sum')
    )
    x2outhobyband_cluster_23 = x2outhobyband_cluster_23.annotate(
        x2outhofailtotal=Coalesce(F('Sum_x2outhofail'), Value(0))
    )
    impact_clusters_23 = x2outhobyband_cluster_23.order_by('-x2outhofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'x2outhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['x2outhofailtotal'].append(cluster['x2outhofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    x2outhobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    x2outhobyband_cluster_26 = x2outhobyband_cluster_26.annotate(
      x2outsucc_sum=Sum('interx2outsucc'), x2outatt_sum=Sum('interx2outatt'),
    )
    x2outhobyband_cluster_26 = x2outhobyband_cluster_26.annotate(
      Sum_x2outhofail=F('x2outatt_sum') - F('x2outsucc_sum')
    )
    x2outhobyband_cluster_26 = x2outhobyband_cluster_26.annotate(
        x2outhofailtotal=Coalesce(F('Sum_x2outhofail'), Value(0))
    )
    impact_clusters_23 = x2outhobyband_cluster_26.order_by('-x2outhofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'x2outhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['x2outhofailtotal'].append(cluster['x2outhofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    x2outhobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    x2outhobyband_cluster_800 = x2outhobyband_cluster_800.annotate(
      x2outsucc_sum=Sum('interx2outsucc'), x2outatt_sum=Sum('interx2outatt'),
    )
    x2outhobyband_cluster_800 = x2outhobyband_cluster_800.annotate(
      Sum_x2outhofail=F('x2outatt_sum') - F('x2outsucc_sum')
    )
    x2outhobyband_cluster_800 = x2outhobyband_cluster_800.annotate(
        x2outhofailtotal=Coalesce(F('Sum_x2outhofail'), Value(0))
    )
    impact_clusters_800 = x2outhobyband_cluster_800.order_by('-x2outhofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'x2outhofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['x2outhofailtotal'].append(cluster['x2outhofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      'x2outho_trend_all': x2outho_trend_all, 'x2outho_trend_23': x2outho_trend_23, 'x2outho_trend_26': x2outho_trend_26, 'x2outho_trend_800': x2outho_trend_800,
      'regional_x2outho_trend_23': regional_x2outho_trend_23, 'regional_x2outho_trend_26': regional_x2outho_trend_26, 'regional_x2outho_trend_800': regional_x2outho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'Totalx2OutHONominate_byband': Totalx2OutHONominate_byband,
      'x2outhofallbybandall': x2outhofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

  
class StatisticIntraHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)
    
    #INTRA HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['hosr_intra_frequency'] for stat in statistics_all]
    intrafreqho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    values_23 = [stat['hosr_intra_frequency'] for stat in statistics_23]
    intrafreqho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    values_26 = [stat['hosr_intra_frequency'] for stat in statistics_26]
    intrafreqho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    values_800 = [stat['hosr_intra_frequency'] for stat in statistics_800]
    intrafreqho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #INTRA HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    regional_values_23 = [stat['hosr_intra_frequency'] for stat in regional_stat_23]
    regional_intrafreqho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    regional_values_26 = [stat['hosr_intra_frequency'] for stat in regional_stat_26]
    regional_intrafreqho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'hosr_intra_frequency').order_by('weeknum')
    regional_values_800 = [stat['hosr_intra_frequency'] for stat in regional_stat_800]
    regional_intrafreqho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #INTER HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(hosr_intra_frequency__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(hosr_intra_frequency__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #INTER HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_intra_frequency__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_intra_frequency__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_intra_frequency__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_intra_frequency__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])
    
    #INTRA HO DATA PROCESSING
    intrahocategorys = celldata_queryset.aggregate(
      Sum_intrafreqoutsucc=Sum('intrafreqoutsucc'),
      Sum_intrafreqoutatt=Sum('intrafreqoutatt'),
    )

    intrahocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_intrafreqoutsucc=Sum('intrafreqoutsucc'),
      Sum_intrafreqoutatt=Sum('intrafreqoutatt'),
    )

    bands = [item['band'] for item in intrahocategorysbyband]

    IntraHONominatecountbyBand = [item['Sum_intrafreqoutatt'] for item in intrahocategorysbyband]
    IntraHOdeNominatecountbyBand = [item['Sum_intrafreqoutsucc'] for item in intrahocategorysbyband]
    TotalIntraHONominate = sum(IntraHONominatecountbyBand)
    TotalIntraHOdeNominate = sum(IntraHOdeNominatecountbyBand)
    TotalIntraHONominate_byband = {
      'overall': {'TotalIntraHONominate': TotalIntraHONominate, 'TotalIntraHOdeNominate': TotalIntraHOdeNominate},
      'by_band': {}
    }
    if TotalIntraHONominate > 0:
      intraHOAttemptbyband = [value / TotalIntraHONominate * 100 for value in IntraHONominatecountbyBand]
    else:
      intraHOAttemptbyband = [0 for _ in IntraHONominatecountbyBand]
    TotalIntraHONominate_byband['by_band'] = {'band': bands, 'ratio': intraHOAttemptbyband, 'counts': IntraHONominatecountbyBand}

    intrahofallbybandall = {
      'overall': {
        'intrafreqhorate': (intrahocategorys['Sum_intrafreqoutsucc'] / intrahocategorys['Sum_intrafreqoutatt']) * 100,
        'failcount':(intrahocategorys['Sum_intrafreqoutatt'] - intrahocategorys['Sum_intrafreqoutsucc'])
      },
      'by_band': {}
    }
    intrafreqhofailcount = [(item['Sum_intrafreqoutatt'] - item['Sum_intrafreqoutsucc']) for item in intrahocategorysbyband]
    intrafreqhofailcounttotal = sum(intrafreqhofailcount)
    intrafreqhorate = [((item['Sum_intrafreqoutsucc'] / item['Sum_intrafreqoutatt'])) * 100 for item in intrahocategorysbyband
    ]
    if intrafreqhofailcounttotal > 0:
      failratebyband = [value / intrafreqhofailcounttotal * 100 for value in intrafreqhofailcount]
    else:
      failratebyband = [0 for _ in intrafreqhofailcount]
    intrahofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': intrafreqhofailcount,
      'calldroprate': intrafreqhorate
    }

    intrahobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    intrahobyband_cluster_23 = intrahobyband_cluster_23.annotate(
      intrafreqoutsucc_sum=Sum('intrafreqoutsucc'),intrafreqoutatt_sum=Sum('intrafreqoutatt'),
    )
    intrahobyband_cluster_23 = intrahobyband_cluster_23.annotate(
      Sum_intrahofail=F('intrafreqoutatt_sum') - F('intrafreqoutsucc_sum')
    )
    intrahobyband_cluster_23 = intrahobyband_cluster_23.annotate(
        intrahofailtotal=Coalesce(F('Sum_intrahofail'), Value(0))
    )
    impact_clusters_23 = intrahobyband_cluster_23.order_by('-intrahofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'intrahofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['intrahofailtotal'].append(cluster['intrahofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    intrahobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    intrahobyband_cluster_26 = intrahobyband_cluster_26.annotate(
      intrafreqoutsucc_sum=Sum('intrafreqoutsucc'),intrafreqoutatt_sum=Sum('intrafreqoutatt'),
    )
    intrahobyband_cluster_26 = intrahobyband_cluster_26.annotate(
      Sum_intrahofail=F('intrafreqoutatt_sum') - F('intrafreqoutsucc_sum')
    )
    intrahobyband_cluster_26 = intrahobyband_cluster_26.annotate(
        intrahofailtotal=Coalesce(F('Sum_intrahofail'), Value(0))
    )
    impact_clusters_26 = intrahobyband_cluster_26.order_by('-intrahofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'intrahofailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['intrahofailtotal'].append(cluster['intrahofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    intrahobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    intrahobyband_cluster_800 = intrahobyband_cluster_800.annotate(
      intrafreqoutsucc_sum=Sum('intrafreqoutsucc'),intrafreqoutatt_sum=Sum('intrafreqoutatt'),
    )
    intrahobyband_cluster_800 = intrahobyband_cluster_800.annotate(
      Sum_intrahofail=F('intrafreqoutatt_sum') - F('intrafreqoutsucc_sum')
    )
    intrahobyband_cluster_800 = intrahobyband_cluster_800.annotate(
        intrahofailtotal=Coalesce(F('Sum_intrahofail'), Value(0))
    )
    impact_clusters_800 = intrahobyband_cluster_800.order_by('-intrahofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'intrahofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['intrahofailtotal'].append(cluster['intrahofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)

    return Response({
      'intrafreqho_trend_all': intrafreqho_trend_all, 'intrafreqho_trend_23': intrafreqho_trend_23, 'intrafreqho_trend_26': intrafreqho_trend_26, 'intrafreqho_trend_800': intrafreqho_trend_800,
      'regional_intrafreqho_trend_23': regional_intrafreqho_trend_23, 'regional_intrafreqho_trend_26': regional_intrafreqho_trend_26, 'regional_intrafreqho_trend_800': regional_intrafreqho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband, 
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'TotalIntraHONominate_byband': TotalIntraHONominate_byband,
      'intrahofallbybandall': intrahofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,

    })
  
class StatisticInterHO(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)
    
    #INTER HO CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['hosr_inter_frequency'] for stat in statistics_all]
    interfreqho_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    values_23 = [stat['hosr_inter_frequency'] for stat in statistics_23]
    interfreqho_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    values_26 = [stat['hosr_inter_frequency'] for stat in statistics_26]
    interfreqho_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    values_800 = [stat['hosr_inter_frequency'] for stat in statistics_800]
    interfreqho_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #INTER HO CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    regional_values_23 = [stat['hosr_inter_frequency'] for stat in regional_stat_23]
    regional_interfreqho_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    regional_values_26 = [stat['hosr_inter_frequency'] for stat in regional_stat_26]
    regional_interfreqho_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'hosr_inter_frequency').order_by('weeknum')
    regional_values_800 = [stat['hosr_inter_frequency'] for stat in regional_stat_800]
    regional_interfreqho_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #INTER HO CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(hosr_inter_frequency__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(hosr_inter_frequency__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #INTER HO SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_inter_frequency__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_inter_frequency__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_inter_frequency__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(hosr_inter_frequency__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #INTER HO DATA PROCESSING
    interhocategorys = celldata_queryset.aggregate(
      Sum_interfreqmeasgapoutsucc=Sum('interfreqmeasgapoutsucc'),
      Sum_interfreqnomeasgapoutsucc=Sum('interfreqnomeasgapoutsucc'),
      Sum_interfreqmeasgapoutatt=Sum('interfreqmeasgapoutatt'),
      Sum_interfreqnomeasgapoutatt=Sum('interfreqnomeasgapoutatt'),
    )

    interhocategorysbyband = celldata_queryset.values('band').annotate(
      Sum_interfreqmeasgapoutsucc=Sum('interfreqmeasgapoutsucc'),
      Sum_interfreqnomeasgapoutsucc=Sum('interfreqnomeasgapoutsucc'),
      Sum_interfreqmeasgapoutatt=Sum('interfreqmeasgapoutatt'),
      Sum_interfreqnomeasgapoutatt=Sum('interfreqnomeasgapoutatt'),
    )

    interhobybands = celldata_queryset.values('band').annotate(
      Sum_interfreqmeasgapoutsucc=Sum('interfreqmeasgapoutsucc'),
      Sum_interfreqnomeasgapoutsucc=Sum('interfreqnomeasgapoutsucc'),
      Sum_interfreqmeasgapoutatt=Sum('interfreqmeasgapoutatt'),
      Sum_interfreqnomeasgapoutatt=Sum('interfreqnomeasgapoutatt'),
    )

    bands = [item['band'] for item in interhobybands]

    InterHONominatecountbyBand = [item['Sum_interfreqmeasgapoutatt'] + item['Sum_interfreqnomeasgapoutatt'] for item in interhocategorysbyband]
    InterHOdeNominatecountbyBand = [item['Sum_interfreqmeasgapoutsucc'] + item['Sum_interfreqnomeasgapoutsucc'] for item in interhocategorysbyband]
    TotalInterHONominate = sum(InterHONominatecountbyBand)
    TotalInterHOdeNominate = sum(InterHOdeNominatecountbyBand)
    TotalInterHONominate_byband = {
      'overall': {'TotalInterHONominate': TotalInterHONominate, 'TotalInterHOdeNominate': TotalInterHOdeNominate},
      'by_band': {}
    }
    if TotalInterHONominate > 0:
      interHOAttemptbyband = [value / TotalInterHONominate * 100 for value in InterHONominatecountbyBand]
    else:
      interHOAttemptbyband = [0 for _ in InterHONominatecountbyBand]
    TotalInterHONominate_byband['by_band'] = {'band': bands, 'ratio': interHOAttemptbyband, 'counts': InterHONominatecountbyBand}

    interfreqmeasgapoutatt_byband = {
      'overall': {'interfreqmeasgapoutatt': interhocategorys['Sum_interfreqmeasgapoutatt']},
      'by_band': {}
    }
    interfreqmeasgapoutattValues = [item['Sum_interfreqmeasgapoutsucc'] for item in interhobybands]
    interfreqmeasgapoutattTotal = sum(interfreqmeasgapoutattValues)
    if interfreqmeasgapoutattTotal > 0:
      interfreqmeasgapoutattRatio = [value / interfreqmeasgapoutattTotal * 100 for value in interfreqmeasgapoutattValues]
    else:
      interfreqmeasgapoutattRatio = [0 for _ in interfreqmeasgapoutattValues]
    interfreqmeasgapoutatt_byband['by_band'] = {'band': bands, 'ratio': interfreqmeasgapoutattRatio, 'counts': interfreqmeasgapoutattValues}

    interfreqnomeasgapoutatt_byband = {
      'overall': {'interfreqnomeasgapoutatt': interhocategorys['Sum_interfreqnomeasgapoutatt']},
      'by_band': {}
    }
    interfreqnomeasgapoutattValues = [item['Sum_interfreqnomeasgapoutsucc'] for item in interhobybands]
    interfreqnomeasgapoutattTotal = sum(interfreqnomeasgapoutattValues)
    if interfreqnomeasgapoutattTotal > 0:
      interfreqnomeasgapoutattRatio = [value / interfreqnomeasgapoutattTotal * 100 for value in interfreqnomeasgapoutattValues]
    else:
      interfreqnomeasgapoutattRatio = [0 for _ in interfreqnomeasgapoutattValues]
    interfreqnomeasgapoutatt_byband['by_band'] = {'band': bands, 'ratio': interfreqnomeasgapoutattRatio, 'counts': interfreqnomeasgapoutattValues}

    interhofallbybandall = {
      'overall': {
        'interfreqhorate':(
          (interhocategorys['Sum_interfreqmeasgapoutsucc'] + 
          interhocategorys['Sum_interfreqnomeasgapoutsucc']) /
           (interhocategorys['Sum_interfreqmeasgapoutatt'] + 
           interhocategorys['Sum_interfreqnomeasgapoutatt'])) * 100,
        'failcount':((interhocategorys['Sum_interfreqmeasgapoutatt'] + interhocategorys['Sum_interfreqnomeasgapoutatt']) - 
                     (interhocategorys['Sum_interfreqmeasgapoutsucc'] + interhocategorys['Sum_interfreqnomeasgapoutsucc']))
      },
      'by_band': {}
    }
    interfreqhofailcount = [(item['Sum_interfreqmeasgapoutatt'] + item['Sum_interfreqnomeasgapoutatt']) - 
                    (item['Sum_interfreqmeasgapoutsucc'] + item['Sum_interfreqnomeasgapoutsucc'])  for item in interhocategorysbyband]
    interfreqhofailcounttotal = sum(interfreqhofailcount)
    interfreqhorate = [
      (
        (item['Sum_interfreqmeasgapoutsucc'] + item['Sum_interfreqnomeasgapoutsucc']) / 
        (item['Sum_interfreqmeasgapoutatt'] + item['Sum_interfreqnomeasgapoutatt'])
      ) * 100 for item in interhocategorysbyband
    ]
    if interfreqhofailcounttotal > 0:
      failratebyband = [value / interfreqhofailcounttotal * 100 for value in interfreqhofailcount]
    else:
      failratebyband = [0 for _ in interfreqhofailcount]
    interhofallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': interfreqhofailcount,
      'calldroprate': interfreqhorate
    }

    interhobyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    interhobyband_cluster_23 = interhobyband_cluster_23.annotate(
      interfreqmeasgapoutatt_sum=Sum('interfreqmeasgapoutatt'),
      interfreqnomeasgapoutatt_sum=Sum('interfreqnomeasgapoutatt'),
      interfreqmeasgapoutsucc_sum=Sum('interfreqmeasgapoutsucc'),
      interfreqnomeasgapoutsucc_sum=Sum('interfreqnomeasgapoutsucc')
    )
    interhobyband_cluster_23 = interhobyband_cluster_23.annotate(
      Sum_interhofail=F('interfreqmeasgapoutatt_sum') + F('interfreqnomeasgapoutatt_sum') -
                      F('interfreqmeasgapoutsucc_sum') - F('interfreqnomeasgapoutsucc_sum')
    )
    interhobyband_cluster_23 = interhobyband_cluster_23.annotate(
        interhofailtotal=Coalesce(F('Sum_interhofail'), Value(0))
    )
    impact_clusters_23 = interhobyband_cluster_23.order_by('-interhofailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'interhofailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['interhofailtotal'].append(cluster['interhofailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    interhobyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    interhobyband_cluster_26 = interhobyband_cluster_26.annotate(
      interfreqmeasgapoutatt_sum=Sum('interfreqmeasgapoutatt'),
      interfreqnomeasgapoutatt_sum=Sum('interfreqnomeasgapoutatt'),
      interfreqmeasgapoutsucc_sum=Sum('interfreqmeasgapoutsucc'),
      interfreqnomeasgapoutsucc_sum=Sum('interfreqnomeasgapoutsucc')
    )
    interhobyband_cluster_26 = interhobyband_cluster_26.annotate(
      Sum_interhofail=F('interfreqmeasgapoutatt_sum') + F('interfreqnomeasgapoutatt_sum') -
                      F('interfreqmeasgapoutsucc_sum') - F('interfreqnomeasgapoutsucc_sum')
    )
    interhobyband_cluster_26 = interhobyband_cluster_26.annotate(
        interhofailtotal=Coalesce(F('Sum_interhofail'), Value(0))
    )
    impact_clusters_26 = interhobyband_cluster_26.order_by('-interhofailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'interhofailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['interhofailtotal'].append(cluster['interhofailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    interhobyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    interhobyband_cluster_800 = interhobyband_cluster_800.annotate(
      interfreqmeasgapoutatt_sum=Sum('interfreqmeasgapoutatt'),
      interfreqnomeasgapoutatt_sum=Sum('interfreqnomeasgapoutatt'),
      interfreqmeasgapoutsucc_sum=Sum('interfreqmeasgapoutsucc'),
      interfreqnomeasgapoutsucc_sum=Sum('interfreqnomeasgapoutsucc')
    )
    interhobyband_cluster_800 = interhobyband_cluster_800.annotate(
      Sum_interhofail=F('interfreqmeasgapoutatt_sum') + F('interfreqnomeasgapoutatt_sum') -
                      F('interfreqmeasgapoutsucc_sum') - F('interfreqnomeasgapoutsucc_sum')
    )
    interhobyband_cluster_800 = interhobyband_cluster_800.annotate(
        interhofailtotal=Coalesce(F('Sum_interhofail'), Value(0))
    )
    impact_clusters_800 = interhobyband_cluster_800.order_by('-interhofailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'interhofailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['interhofailtotal'].append(cluster['interhofailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)

    return Response({
      'interfreqho_trend_all': interfreqho_trend_all, 'interfreqho_trend_23': interfreqho_trend_23, 'interfreqho_trend_26': interfreqho_trend_26, 'interfreqho_trend_800': interfreqho_trend_800,
      'regional_interfreqho_trend_23': regional_interfreqho_trend_23, 'regional_interfreqho_trend_26': regional_interfreqho_trend_26, 'regional_interfreqho_trend_800': regional_interfreqho_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband, 'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'TotalInterHONominate_byband': TotalInterHONominate_byband,
      'interfreqmeasgapoutatt_byband': interfreqmeasgapoutatt_byband, 'interfreqnomeasgapoutatt_byband': interfreqnomeasgapoutatt_byband,
      'interhofallbybandall': interhofallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800
    })

  
class StatisticCallDropGBR(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #CALL DROP SETUP CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['volte_call_drop_rate_erab_gbr'] for stat in statistics_all]
    calldrop_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    values_23 = [stat['volte_call_drop_rate_erab_gbr'] for stat in statistics_23]
    calldrop_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    values_26 = [stat['volte_call_drop_rate_erab_gbr'] for stat in statistics_26]
    calldrop_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    values_800 = [stat['volte_call_drop_rate_erab_gbr'] for stat in statistics_800]
    calldrop_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #CALL DROP SETUP CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    regional_values_23 = [stat['volte_call_drop_rate_erab_gbr'] for stat in regional_stat_23]
    regional_calldrop_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    regional_values_26 = [stat['volte_call_drop_rate_erab_gbr'] for stat in regional_stat_26]
    regional_calldrop_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'volte_call_drop_rate_erab_gbr').order_by('weeknum')
    regional_values_800 = [stat['volte_call_drop_rate_erab_gbr'] for stat in regional_stat_800]
    regional_calldrop_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #CALL DROP SETUP CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(volte_call_drop_rate_erab_gbr__gte=1, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(volte_call_drop_rate_erab_gbr__gte=1, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])
    
    #CALL DROP SETUP SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_call_drop_rate_erab_gbr__gte=1).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_call_drop_rate_erab_gbr__gte=1).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_call_drop_rate_erab_gbr__gte=1).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_call_drop_rate_erab_gbr__gte=1).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #CALL DROP SETUP DATA PROCESSING
    calldropcategorys = celldata_queryset.aggregate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci'),
      Sum_sumvolteestablnitsuccnbr=Sum('sumvolteestablnitsuccnbr'),
      Sum_sumvolteestabaddsuccnbr=Sum('sumvolteestabaddsuccnbr'),
      Sum_sumvolteerablncominghosuccnbr=Sum('sumvolteerablncominghosuccnbr'),
    )

    calldropcategorysbyband = celldata_queryset.values('band').annotate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci'),
      Sum_sumvolteestablnitsuccnbr=Sum('sumvolteestablnitsuccnbr'),
      Sum_sumvolteestabaddsuccnbr=Sum('sumvolteestabaddsuccnbr'),
      Sum_sumvolteerablncominghosuccnbr=Sum('sumvolteerablncominghosuccnbr'),
    )

    calldropbybands = celldata_queryset.values('band').annotate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci'),
      Sum_sumvolteestablnitsuccnbr=Sum('sumvolteestablnitsuccnbr'),
      Sum_sumvolteestabaddsuccnbr=Sum('sumvolteestabaddsuccnbr'),
      Sum_sumvolteerablncominghosuccnbr=Sum('sumvolteerablncominghosuccnbr'),
    )

    totalVoLTEcalldropNominate = {
      'Total': {calldropcategorys['Sum_sumvolteestablnitsuccnbr'] + 
                calldropcategorys['Sum_sumvolteestabaddsuccnbr'] + 
                calldropcategorys['Sum_sumvolteerablncominghosuccnbr']},
    }
    bands = [item['band'] for item in calldropbybands]

    calldropNominatecountbyBand = [item['Sum_sumvolteestablnitsuccnbr'] + item['Sum_sumvolteestabaddsuccnbr'] + item['Sum_sumvolteerablncominghosuccnbr'] for item in calldropcategorysbyband]
    TotalCallDropNominate = sum(calldropNominatecountbyBand)
    TotalVoLTECallDropNominate_byband = {
      'overall': {'TotalVoLTECallDropNominate': TotalCallDropNominate},
      'by_band': {}
    }
    if TotalCallDropNominate > 0:
      failratebyband = [value / TotalCallDropNominate * 100 for value in calldropNominatecountbyBand]
    else:
      failratebyband = [0 for _ in calldropNominatecountbyBand]
    TotalVoLTECallDropNominate_byband['by_band'] = {
      'band': bands, 
      'ratio': failratebyband, 
      'counts': calldropNominatecountbyBand,
      # 'calldroprate': calldroprate
    }

    calldropcoutbyband = {
      'overall': {'CallDropCount': calldropcategorys['Sum_sumvoltecalldropqci']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    calldropvalue = [item['Sum_sumvoltecalldropqci'] for item in calldropbybands]
    calldroptotal = sum(calldropvalue)
    if calldroptotal > 0:
      calldropratios = [value / calldroptotal * 100 for value in calldropvalue]
    else:
      calldropratios = [0 for _ in calldropvalue]
    calldropcoutbyband['by_band'] = {'band': bands, 'ratio': calldropratios, 'counts': calldropvalue}

    sumvolteestablnitsuccnbr_byband = {
      'overall': {'sumvolteestablnitsuccnbr': calldropcategorys['Sum_sumvolteestablnitsuccnbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    sumvolteestablnitsuccnbrValues = [item['Sum_sumvolteestablnitsuccnbr'] for item in calldropbybands]
    sumvolteestablnitsuccnbrTotal = sum(sumvolteestablnitsuccnbrValues)
    if sumvolteestablnitsuccnbrTotal > 0:
      sumvolteestablnitsuccnbrRatio = [value / sumvolteestablnitsuccnbrTotal * 100 for value in sumvolteestablnitsuccnbrValues]
    else:
      sumvolteestablnitsuccnbrRatio = [0 for _ in sumvolteestablnitsuccnbrValues]
    sumvolteestablnitsuccnbr_byband['by_band'] = {'band': bands, 'ratio': sumvolteestablnitsuccnbrRatio, 'counts': sumvolteestablnitsuccnbrValues}

    sumvolteestabaddsuccnbr_byband = {
      'overall': {'sumvolteestabaddsuccnbr': calldropcategorys['Sum_sumvolteestabaddsuccnbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    sumvolteestabaddsuccnbrValues = [item['Sum_sumvolteestabaddsuccnbr'] for item in calldropbybands]
    sumvolteestabaddsuccnbrTotal = sum(sumvolteestabaddsuccnbrValues)
    if sumvolteestabaddsuccnbrTotal > 0:
      sumvolteestabaddsuccnbrRatio = [value / sumvolteestabaddsuccnbrTotal * 100 for value in sumvolteestabaddsuccnbrValues]
    else:
      sumvolteestabaddsuccnbrRatio = [0 for _ in sumvolteestabaddsuccnbrValues]
    sumvolteestabaddsuccnbr_byband['by_band'] = {'band': bands, 'ratio': sumvolteestabaddsuccnbrRatio, 'counts': sumvolteestabaddsuccnbrValues}

    sumvolteerablncominghosuccnbr_byband = {
      'overall': {'sumvolteerablncominghosuccnbr': calldropcategorys['Sum_sumvolteerablncominghosuccnbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    sumvolteerablncominghosuccnbrValues = [item['Sum_sumvolteerablncominghosuccnbr'] for item in calldropbybands]
    sumvolteerablncominghosuccnbrTotal = sum(sumvolteerablncominghosuccnbrValues)
    if sumvolteerablncominghosuccnbrTotal > 0:
      sumvolteerablncominghosuccnbrRatio = [value / sumvolteerablncominghosuccnbrTotal * 100 for value in sumvolteerablncominghosuccnbrValues]
    else:
      sumvolteerablncominghosuccnbrRatio = [0 for _ in sumvolteerablncominghosuccnbrValues]
    sumvolteerablncominghosuccnbr_byband['by_band'] = {'band': bands, 'ratio': sumvolteerablncominghosuccnbrRatio, 'counts': sumvolteerablncominghosuccnbrValues}
    

    calldropbybandall = {
      'overall': {
        'calldroprate':(
          calldropcategorys['Sum_sumvoltecalldropqci'] / 
          (calldropcategorys['Sum_sumvolteestablnitsuccnbr'] + 
           calldropcategorys['Sum_sumvolteestabaddsuccnbr'] + 
           calldropcategorys['Sum_sumvolteerablncominghosuccnbr'])) * 100,
        'failcount':(calldropcategorys['Sum_sumvoltecalldropqci'])
      },
      'by_band': {}
    }
    calldropcount = [item['Sum_sumvoltecalldropqci'] for item in calldropcategorysbyband]
    calldropcounttotal = sum(calldropcount)
    calldroprate = [
      (
        ((item['Sum_sumvoltecalldropqci'] / 
        (item['Sum_sumvolteestablnitsuccnbr'] + 
         item['Sum_sumvolteestabaddsuccnbr'] + 
         item['Sum_sumvolteerablncominghosuccnbr'])))
      ) * 100 for item in calldropcategorysbyband
    ]
    if calldropcounttotal > 0:
      failratebyband = [value / calldropcounttotal * 100 for value in calldropcount]
    else:
      failratebyband = [0 for _ in calldropcount]
    calldropbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': calldropcount,
      'calldroprate': calldroprate
    }

    calldropbyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster').annotate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci')
    ).annotate(calldroptotal=Coalesce(Sum('sumvoltecalldropqci'), Value(0)))
    impact_clusters_23 = calldropbyband_cluster_23.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    calldropbyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster').annotate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci')
    ).annotate(calldroptotal=Coalesce(Sum('sumvoltecalldropqci'), Value(0)))
    impact_clusters_26 = calldropbyband_cluster_26.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    calldropbyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster').annotate(
      Sum_sumvoltecalldropqci=Sum('sumvoltecalldropqci')
    ).annotate(calldroptotal=Coalesce(Sum('sumvoltecalldropqci'), Value(0)))
    impact_clusters_800 = calldropbyband_cluster_800.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      'calldrop_trend_all': calldrop_trend_all, 'calldrop_trend_23': calldrop_trend_23, 'calldrop_trend_26': calldrop_trend_26, 'calldrop_trend_800': calldrop_trend_800,
      'regional_calldrop_trend_23': regional_calldrop_trend_23, 'regional_calldrop_trend_26': regional_calldrop_trend_26, 'regional_calldrop_trend_800': regional_calldrop_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband':fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'calldropcoutbyband': calldropcoutbyband, 
      'calldropbybandall': calldropbybandall, 'totalVoLTEcalldropNominate': totalVoLTEcalldropNominate, 'TotalVoLTECallDropNominate_byband': TotalVoLTECallDropNominate_byband,
      'sumvolteestablnitsuccnbr_byband': sumvolteestablnitsuccnbr_byband, 'sumvolteestabaddsuccnbr_byband': sumvolteestabaddsuccnbr_byband, 'sumvolteerablncominghosuccnbr_byband': sumvolteerablncominghosuccnbr_byband,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

class StatisticCallDropnGBR(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)
    
    #CALL DROP SETUP CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['call_drop_rate_erab_ngbr'] for stat in statistics_all]
    calldrop_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    values_23 = [stat['call_drop_rate_erab_ngbr'] for stat in statistics_23]
    calldrop_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    values_26 = [stat['call_drop_rate_erab_ngbr'] for stat in statistics_26]
    calldrop_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    values_800 = [stat['call_drop_rate_erab_ngbr'] for stat in statistics_800]
    calldrop_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #CALL DROP SETUP CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    regional_values_23 = [stat['call_drop_rate_erab_ngbr'] for stat in regional_stat_23]
    regional_calldrop_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    regional_values_26 = [stat['call_drop_rate_erab_ngbr'] for stat in regional_stat_26]
    regional_calldrop_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'call_drop_rate_erab_ngbr').order_by('weeknum')
    regional_values_800 = [stat['call_drop_rate_erab_ngbr'] for stat in regional_stat_800]
    regional_calldrop_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #CALL DROP SETUP CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(call_drop_rate_erab_ngbr__gte=1, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(call_drop_rate_erab_ngbr__gte=1, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])
    
    #CALL DROP SETUP SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(call_drop_rate_erab_ngbr__gte=1).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(call_drop_rate_erab_ngbr__gte=1).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(call_drop_rate_erab_ngbr__gte=1).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(call_drop_rate_erab_ngbr__gte=1).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])
    
    #CALL DROP SETUP DATA PROCESSING
    calldropcategorys = celldata_queryset.aggregate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
      Sum_establnitsuccnbr=Sum('establnitsuccnbr_qci59'),
      Sum_estabaddsuccnbr=Sum('estabaddsuccnbr_qci59'),
      Sum_interx2insucc=Sum('interx2insucc_qci59'),
      Sum_inters1insucc=Sum('inters1insucc_qci59'),
    )

    calldropcategorysbyband = celldata_queryset.values('band').annotate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
      Sum_establnitsuccnbr=Sum('establnitsuccnbr_qci59'),
      Sum_estabaddsuccnbr=Sum('estabaddsuccnbr_qci59'),
      Sum_interx2insucc=Sum('interx2insucc_qci59'),
      Sum_inters1insucc=Sum('inters1insucc_qci59'),
    )

    calldropbybands = celldata_queryset.values('band').annotate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59')
    )

    calldropbyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster').annotate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59')
    ).annotate(
      calldroptotal=Coalesce(
        Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59') +
        Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59') +
        Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59') +
        Sum('calldropqci_eccbradiolinkfailure_qci59') +
        Sum('calldropqci_eccbdspauditmaccallrelease_qci59') +
        Sum('calldropqci_eccbarqmaxretransmission_qci59') +
        Sum('calldropqci_eccbdspauditrlccallrelease_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59') +
        Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
        Value(0)
      )
    )
    impact_clusters_23 = calldropbyband_cluster_23.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    calldropbyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster').annotate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59')
    ).annotate(
      calldroptotal=Coalesce(
        Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59') +
        Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59') +
        Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59') +
        Sum('calldropqci_eccbradiolinkfailure_qci59') +
        Sum('calldropqci_eccbdspauditmaccallrelease_qci59') +
        Sum('calldropqci_eccbarqmaxretransmission_qci59') +
        Sum('calldropqci_eccbdspauditrlccallrelease_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59') +
        Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
        Value(0)
      )
    )
    impact_clusters_26 = calldropbyband_cluster_26.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    calldropbyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster').annotate(
      Sum_eccbdspauditrlcmaccallrelease=Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59'),
      Sum_eccbrcvresetrequestfromecmb=Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59'),
      Sum_eccbrcvcellreleaseindfromecmb=Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59'),
      Sum_eccbradiolinkfailure=Sum('calldropqci_eccbradiolinkfailure_qci59'),
      Sum_eccbdspauditmaccallrelease=Sum('calldropqci_eccbdspauditmaccallrelease_qci59'),
      Sum_eccbarqmaxretransmission=Sum('calldropqci_eccbarqmaxretransmission_qci59'),
      Sum_eccbdspauditrlccallrelease=Sum('calldropqci_eccbdspauditrlccallrelease_qci59'),
      Sum_eccbtmoutrrcconnectionreconfig=Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59'),
      Sum_eccbtmoutrrcconnectionrestablish=Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59'),
      Sum_eccbsisctpoutofsevice=Sum('calldropqci_eccbsisctpoutofsevice_qci59')
    ).annotate(
      calldroptotal=Coalesce(
        Sum('calldropqci_eccbdspauditrlcmaccallrelease_qci59') +
        Sum('calldropqci_eccbrcvresetrequestfromecmb_qci59') +
        Sum('calldropqci_eccbrcvcellreleaseindfromecmb_qci59') +
        Sum('calldropqci_eccbradiolinkfailure_qci59') +
        Sum('calldropqci_eccbdspauditmaccallrelease_qci59') +
        Sum('calldropqci_eccbarqmaxretransmission_qci59') +
        Sum('calldropqci_eccbdspauditrlccallrelease_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionreconfig_qci59') +
        Sum('calldropqci_eccbtmoutrrcconnectionrestablish_qci59') +
        Sum('calldropqci_eccbsisctpoutofsevice_qci59'),
        Value(0)
      )
    )
    impact_clusters_800 = calldropbyband_cluster_800.order_by('-calldroptotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'calldroptotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['calldroptotal'].append(cluster['calldroptotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)


    calldropcoutbyband = {
      'overall': {
        'CallDropCount': 
        calldropcategorys['Sum_eccbdspauditrlcmaccallrelease'] + 
        calldropcategorys['Sum_eccbrcvresetrequestfromecmb'] + 
        calldropcategorys['Sum_eccbrcvcellreleaseindfromecmb'] + 
        calldropcategorys['Sum_eccbradiolinkfailure'] + 
        calldropcategorys['Sum_eccbdspauditmaccallrelease'] +
        calldropcategorys['Sum_eccbarqmaxretransmission'] +
        calldropcategorys['Sum_eccbdspauditrlccallrelease'] +
        calldropcategorys['Sum_eccbtmoutrrcconnectionreconfig'] +
        calldropcategorys['Sum_eccbtmoutrrcconnectionrestablish'] +
        calldropcategorys['Sum_eccbsisctpoutofsevice']
      },
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    calldropvalue = [
      item['Sum_eccbdspauditrlcmaccallrelease'] + 
      item['Sum_eccbrcvresetrequestfromecmb'] +
      item['Sum_eccbrcvcellreleaseindfromecmb'] +
      item['Sum_eccbradiolinkfailure'] +
      item['Sum_eccbdspauditmaccallrelease'] +
      item['Sum_eccbarqmaxretransmission'] +
      item['Sum_eccbdspauditrlccallrelease'] +
      item['Sum_eccbtmoutrrcconnectionreconfig'] +
      item['Sum_eccbtmoutrrcconnectionrestablish'] +
      item['Sum_eccbsisctpoutofsevice'] for item in calldropbybands
    ]
    calldroptotal = sum(calldropvalue)
    if calldroptotal > 0:
      calldropratios = [value / calldroptotal * 100 for value in calldropvalue]
    else:
      calldropratios = [0 for _ in calldropvalue]
    calldropcoutbyband['by_band'] = {'band': bands, 'ratio': calldropratios, 'counts': calldropvalue}

    eccbdspauditrlcmaccallrelease_byband = {
      'overall': {'eccbdspauditrlcmaccallrelease': calldropcategorys['Sum_eccbdspauditrlcmaccallrelease']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbdspauditrlcmaccallreleaseValues = [item['Sum_eccbdspauditrlcmaccallrelease'] for item in calldropbybands]
    eccbdspauditrlcmaccallreleaseTotal = sum(eccbdspauditrlcmaccallreleaseValues)
    if eccbdspauditrlcmaccallreleaseTotal > 0:
      eccbdspauditrlcmaccallreleaseRatio = [value / eccbdspauditrlcmaccallreleaseTotal * 100 for value in eccbdspauditrlcmaccallreleaseValues]
    else:
      eccbdspauditrlcmaccallreleaseRatio = [0 for _ in eccbdspauditrlcmaccallreleaseValues]
    eccbdspauditrlcmaccallrelease_byband['by_band'] = {'band': bands, 'ratio': eccbdspauditrlcmaccallreleaseRatio, 'counts': eccbdspauditrlcmaccallreleaseValues}

    eccbrcvresetrequestfromecmb_byband = {
      'overall': {'eccbrcvresetrequestfromecmb': calldropcategorys['Sum_eccbrcvresetrequestfromecmb']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbrcvresetrequestfromecmbValues = [item['Sum_eccbrcvresetrequestfromecmb'] for item in calldropbybands]
    eccbrcvresetrequestfromecmbTotal = sum(eccbrcvresetrequestfromecmbValues)
    if eccbrcvresetrequestfromecmbTotal > 0:
      eccbrcvresetrequestfromecmbRatio = [value / eccbrcvresetrequestfromecmbTotal * 100 for value in eccbrcvresetrequestfromecmbValues]
    else:
      eccbrcvresetrequestfromecmbRatio = [0 for _ in eccbrcvresetrequestfromecmbValues]
    eccbrcvresetrequestfromecmb_byband['by_band'] = {'band': bands, 'ratio': eccbrcvresetrequestfromecmbRatio, 'counts': eccbrcvresetrequestfromecmbValues}

    eccbrcvcellreleaseindfromecmb_byband = {
      'overall': {'eccbrcvcellreleaseindfromecmb': calldropcategorys['Sum_eccbrcvcellreleaseindfromecmb']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbrcvcellreleaseindfromecmbValues = [item['Sum_eccbrcvcellreleaseindfromecmb'] for item in calldropbybands]
    eccbrcvcellreleaseindfromecmbTotal = sum(eccbrcvcellreleaseindfromecmbValues)
    if eccbrcvcellreleaseindfromecmbTotal > 0:
      eccbrcvcellreleaseindfromecmbRatio = [value / eccbrcvcellreleaseindfromecmbTotal * 100 for value in eccbrcvcellreleaseindfromecmbValues]
    else:
      eccbrcvcellreleaseindfromecmbRatio = [0 for _ in eccbrcvcellreleaseindfromecmbValues]
    eccbrcvcellreleaseindfromecmb_byband['by_band'] = {'band': bands, 'ratio': eccbrcvcellreleaseindfromecmbRatio, 'counts': eccbrcvcellreleaseindfromecmbValues}

    eccbradiolinkfailure_byband = {
      'overall': {'eccbradiolinkfailure': calldropcategorys['Sum_eccbradiolinkfailure']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbradiolinkfailureValues = [item['Sum_eccbradiolinkfailure'] for item in calldropbybands]
    eccbradiolinkfailureTotal = sum(eccbradiolinkfailureValues)
    if eccbradiolinkfailureTotal > 0:
      eccbradiolinkfailureRatio = [value / eccbradiolinkfailureTotal * 100 for value in eccbradiolinkfailureValues]
    else:
      eccbradiolinkfailureRatio = [0 for _ in eccbradiolinkfailureValues]
    eccbradiolinkfailure_byband['by_band'] = {'band': bands, 'ratio': eccbradiolinkfailureRatio, 'counts': eccbradiolinkfailureValues}

    eccbdspauditmaccallrelease_byband = {
      'overall': {'eccbdspauditmaccallrelease': calldropcategorys['Sum_eccbdspauditmaccallrelease']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbdspauditmaccallreleaseValues = [item['Sum_eccbdspauditmaccallrelease'] for item in calldropbybands]
    eccbdspauditmaccallreleaseTotal = sum(eccbdspauditmaccallreleaseValues)
    if eccbdspauditmaccallreleaseTotal > 0:
      eccbdspauditmaccallreleaseRatio = [value / eccbdspauditmaccallreleaseTotal * 100 for value in eccbdspauditmaccallreleaseValues]
    else:
      eccbdspauditmaccallreleaseRatio = [0 for _ in eccbdspauditmaccallreleaseValues]
    eccbdspauditmaccallrelease_byband['by_band'] = {'band': bands, 'ratio': eccbdspauditmaccallreleaseRatio, 'counts': eccbdspauditmaccallreleaseValues}

    eccbarqmaxretransmission_byband = {
      'overall': {'eccbarqmaxretransmission': calldropcategorys['Sum_eccbarqmaxretransmission']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbarqmaxretransmissionValues = [item['Sum_eccbarqmaxretransmission'] for item in calldropbybands]
    eccbarqmaxretransmissionTotal = sum(eccbarqmaxretransmissionValues)
    if eccbarqmaxretransmissionTotal > 0:
      eccbarqmaxretransmissionRatio = [value / eccbarqmaxretransmissionTotal * 100 for value in eccbarqmaxretransmissionValues]
    else:
      eccbarqmaxretransmissionRatio = [0 for _ in eccbarqmaxretransmissionValues]
    eccbarqmaxretransmission_byband['by_band'] = {'band': bands, 'ratio': eccbarqmaxretransmissionRatio, 'counts': eccbarqmaxretransmissionValues}

    eccbdspauditrlccallrelease_byband = {
      'overall': {'eccbdspauditrlccallrelease': calldropcategorys['Sum_eccbdspauditrlccallrelease']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbdspauditrlccallreleaseValues = [item['Sum_eccbdspauditrlccallrelease'] for item in calldropbybands]
    eccbdspauditrlccallreleaseTotal = sum(eccbdspauditrlccallreleaseValues)
    if eccbdspauditrlccallreleaseTotal > 0:
      eccbdspauditrlccallreleaseRatio = [value / eccbdspauditrlccallreleaseTotal * 100 for value in eccbdspauditrlccallreleaseValues]
    else:
      eccbdspauditrlccallreleaseRatio = [0 for _ in eccbdspauditrlccallreleaseValues]
    eccbdspauditrlccallrelease_byband['by_band'] = {'band': bands, 'ratio': eccbdspauditrlccallreleaseRatio, 'counts': eccbdspauditrlccallreleaseValues}

    eccbtmoutrrcconnectionreconfig_byband = {
      'overall': {'eccbtmoutrrcconnectionreconfig': calldropcategorys['Sum_eccbtmoutrrcconnectionreconfig']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbtmoutrrcconnectionreconfigValues = [item['Sum_eccbtmoutrrcconnectionreconfig'] for item in calldropbybands]
    eccbtmoutrrcconnectionreconfigTotal = sum(eccbtmoutrrcconnectionreconfigValues)
    if eccbtmoutrrcconnectionreconfigTotal > 0:
      eccbtmoutrrcconnectionreconfigRatio = [value / eccbtmoutrrcconnectionreconfigTotal * 100 for value in eccbtmoutrrcconnectionreconfigValues]
    else:
      eccbtmoutrrcconnectionreconfigRatio = [0 for _ in eccbtmoutrrcconnectionreconfigValues]
    eccbtmoutrrcconnectionreconfig_byband['by_band'] = {'band': bands, 'ratio': eccbtmoutrrcconnectionreconfigRatio, 'counts': eccbtmoutrrcconnectionreconfigValues}

    eccbtmoutrrcconnectionrestablish_byband = {
      'overall': {'eccbtmoutrrcconnectionrestablish': calldropcategorys['Sum_eccbtmoutrrcconnectionrestablish']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbtmoutrrcconnectionrestablishValues = [item['Sum_eccbtmoutrrcconnectionrestablish'] for item in calldropbybands]
    eccbtmoutrrcconnectionrestablishTotal = sum(eccbtmoutrrcconnectionrestablishValues)
    if eccbtmoutrrcconnectionrestablishTotal > 0:
      eccbtmoutrrcconnectionrestablishRatio = [value / eccbtmoutrrcconnectionrestablishTotal * 100 for value in eccbtmoutrrcconnectionrestablishValues]
    else:
      eccbtmoutrrcconnectionrestablishRatio = [0 for _ in eccbtmoutrrcconnectionrestablishValues]
    eccbtmoutrrcconnectionrestablish_byband['by_band'] = {'band': bands, 'ratio': eccbtmoutrrcconnectionrestablishRatio, 'counts': eccbtmoutrrcconnectionrestablishValues}

    eccbsisctpoutofsevice_byband = {
      'overall': {'eccbsisctpoutofsevice': calldropcategorys['Sum_eccbsisctpoutofsevice']},
      'by_band': {}
    }
    bands = [item['band'] for item in calldropbybands]
    eccbsisctpoutofseviceValues = [item['Sum_eccbsisctpoutofsevice'] for item in calldropbybands]
    eccbsisctpoutofseviceTotal = sum(eccbsisctpoutofseviceValues)
    if eccbsisctpoutofseviceTotal > 0:
      eccbsisctpoutofseviceRatio = [value / eccbsisctpoutofseviceTotal * 100 for value in eccbsisctpoutofseviceValues]
    else:
      eccbsisctpoutofseviceRatio = [0 for _ in eccbsisctpoutofseviceValues]
    eccbsisctpoutofsevice_byband['by_band'] = {'band': bands, 'ratio': eccbsisctpoutofseviceRatio, 'counts': eccbsisctpoutofseviceValues}
    
    calldropbybandall = {
      'overall': {
        'calldroprate':(
          (calldropcategorys['Sum_eccbdspauditrlcmaccallrelease'] + 
           calldropcategorys['Sum_eccbrcvresetrequestfromecmb'] + 
           calldropcategorys['Sum_eccbrcvcellreleaseindfromecmb'] + 
           calldropcategorys['Sum_eccbradiolinkfailure'] + 
           calldropcategorys['Sum_eccbdspauditmaccallrelease'] + 
           calldropcategorys['Sum_eccbarqmaxretransmission'] + 
           calldropcategorys['Sum_eccbdspauditrlccallrelease'] + 
           calldropcategorys['Sum_eccbtmoutrrcconnectionreconfig'] + 
           calldropcategorys['Sum_eccbtmoutrrcconnectionrestablish'] + 
           calldropcategorys['Sum_eccbsisctpoutofsevice']) / 
          (calldropcategorys['Sum_establnitsuccnbr'] + 
           calldropcategorys['Sum_estabaddsuccnbr'] + 
           calldropcategorys['Sum_interx2insucc'] + 
           calldropcategorys['Sum_inters1insucc'])) * 100,
        'failcount':(
          calldropcategorys['Sum_eccbdspauditrlcmaccallrelease'] + 
           calldropcategorys['Sum_eccbrcvresetrequestfromecmb'] + 
           calldropcategorys['Sum_eccbrcvcellreleaseindfromecmb'] + 
           calldropcategorys['Sum_eccbradiolinkfailure'] + 
           calldropcategorys['Sum_eccbdspauditmaccallrelease'] + 
           calldropcategorys['Sum_eccbarqmaxretransmission'] + 
           calldropcategorys['Sum_eccbdspauditrlccallrelease'] + 
           calldropcategorys['Sum_eccbtmoutrrcconnectionreconfig'] + 
           calldropcategorys['Sum_eccbtmoutrrcconnectionrestablish'] + 
           calldropcategorys['Sum_eccbsisctpoutofsevice']
        )
      },
      'by_band': {}
    }
    calldropcount = [
      (
        (item['Sum_eccbdspauditrlcmaccallrelease'] + 
        item['Sum_eccbrcvresetrequestfromecmb'] + 
        item['Sum_eccbrcvcellreleaseindfromecmb'] + 
        item['Sum_eccbradiolinkfailure'] +
        item['Sum_eccbdspauditmaccallrelease'] + 
        item['Sum_eccbarqmaxretransmission'] + 
        item['Sum_eccbdspauditrlccallrelease'] + 
        item['Sum_eccbtmoutrrcconnectionreconfig'] + 
        item['Sum_eccbtmoutrrcconnectionrestablish'] + 
        item['Sum_eccbsisctpoutofsevice'])) for item in calldropcategorysbyband
    ]
    calldropcounttotal = sum(calldropcount)
    calldroprate = [
      (
        (((item['Sum_eccbdspauditrlcmaccallrelease'] + 
          item['Sum_eccbrcvresetrequestfromecmb'] + 
          item['Sum_eccbrcvcellreleaseindfromecmb'] + 
          item['Sum_eccbradiolinkfailure'] + 
          item['Sum_eccbdspauditmaccallrelease'] + 
          item['Sum_eccbarqmaxretransmission'] + 
          item['Sum_eccbdspauditrlccallrelease'] + 
          item['Sum_eccbtmoutrrcconnectionreconfig'] + 
          item['Sum_eccbtmoutrrcconnectionrestablish'] + 
          item['Sum_eccbsisctpoutofsevice']) / 
        (item['Sum_establnitsuccnbr'] + 
         item['Sum_estabaddsuccnbr'] + 
         item['Sum_interx2insucc'] + 
         item['Sum_inters1insucc'])))
      ) * 100 for item in calldropcategorysbyband
    ]
    if calldropcounttotal > 0:
      failratebyband = [value / calldropcounttotal * 100 for value in calldropcount]
    else:
      failratebyband = [0 for _ in calldropcount]
    calldropbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': calldropcount,
      'calldroprate': calldroprate
    }

    return Response({
      'calldrop_trend_all': calldrop_trend_all, 'calldrop_trend_23': calldrop_trend_23, 'calldrop_trend_26': calldrop_trend_26, 'calldrop_trend_800': calldrop_trend_800,
      'regional_calldrop_trend_23': regional_calldrop_trend_23, 'regional_calldrop_trend_26': regional_calldrop_trend_26, 'regional_calldrop_trend_800': regional_calldrop_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband':fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'calldropcoutbyband': calldropcoutbyband, 
      'eccbdspauditrlcmaccallrelease_byband': eccbdspauditrlcmaccallrelease_byband, 'eccbrcvresetrequestfromecmb_byband': eccbrcvresetrequestfromecmb_byband,
      'eccbrcvcellreleaseindfromecmb_byband': eccbrcvcellreleaseindfromecmb_byband, 'eccbradiolinkfailure_byband': eccbradiolinkfailure_byband,
      'eccbdspauditmaccallrelease_byband': eccbdspauditmaccallrelease_byband, 'eccbarqmaxretransmission_byband': eccbarqmaxretransmission_byband,
      'eccbdspauditrlccallrelease_byband': eccbdspauditrlccallrelease_byband, 'eccbtmoutrrcconnectionreconfig_byband': eccbtmoutrrcconnectionreconfig_byband,
      'eccbtmoutrrcconnectionrestablish_byband': eccbtmoutrrcconnectionrestablish_byband, 'eccbsisctpoutofsevice_byband': eccbsisctpoutofsevice_byband,
      'calldropbybandall': calldropbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800
    })
    
    
class StatisticVoLTESetup(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)
    

    #VoLTE SETUP CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['volte_setup_success_rate_gbr'] for stat in statistics_all]
    voltesetup_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    values_23 = [stat['volte_setup_success_rate_gbr'] for stat in statistics_23]
    voltesetup_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    values_26 = [stat['volte_setup_success_rate_gbr'] for stat in statistics_26]
    voltesetup_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    values_800 = [stat['volte_setup_success_rate_gbr'] for stat in statistics_800]
    voltesetup_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #VoLTE SETUP CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    regional_values_23 = [stat['volte_setup_success_rate_gbr'] for stat in regional_stat_23]
    regional_voltesetup_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    regional_values_26 = [stat['volte_setup_success_rate_gbr'] for stat in regional_stat_26]
    regional_voltesetup_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'volte_setup_success_rate_gbr').order_by('weeknum')
    regional_values_800 = [stat['volte_setup_success_rate_gbr'] for stat in regional_stat_800]
    regional_voltesetup_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #VoLTE SETUP CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(volte_setup_success_rate_gbr__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(volte_setup_success_rate_gbr__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #VoLTE SETUP SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_setup_success_rate_gbr__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_setup_success_rate_gbr__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_setup_success_rate_gbr__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(volte_setup_success_rate_gbr__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])
    
    #VoLTE SETUP DATA PROCESSING
    volteattachcategorys = celldata_queryset.aggregate(
      Sum_EstablnitSuccNbr=Sum('establnitsuccnbr_qci1'),
      Sum_EstabAddSuccNbr=Sum('estabaddsuccnbr_qci1'),
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci1'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci1')
    )

    volteattachcategorysbybands = celldata_queryset.values('band').annotate(
      Sum_EstablnitSuccNbr=Sum('establnitsuccnbr_qci1'),
      Sum_EstabAddSuccNbr=Sum('estabaddsuccnbr_qci1'),
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci1'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci1')
    )

    volteattachbybands = celldata_queryset.values('band').annotate(
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci1'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci1')
    )

    volteattemptcoutbyband = {
      'overall': {'VoLTEAttempt': volteattachcategorys['Sum_EstablnitAttNbr'] + volteattachcategorys['Sum_EstabAddAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in volteattachbybands]
    volteconnectionvalues = [item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr'] for item in volteattachbybands]
    volteconnectiontotal = sum(volteconnectionvalues)
    if volteconnectiontotal > 0:
      erabconnectionratios = [value / volteconnectiontotal * 100 for value in volteconnectionvalues]
    else:
      erabconnectionratios = [0 for _ in volteconnectionvalues]
    volteattemptcoutbyband['by_band'] = {'band': bands, 'ratio': erabconnectionratios, 'counts': volteconnectionvalues}

    EstablnitAttNbr_byband = {
      'overall': {'EstablnitAttNbrAttempt': volteattachcategorys['Sum_EstablnitAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in volteattachbybands]
    EstablnitAttNbrValues = [item['Sum_EstablnitAttNbr'] for item in volteattachbybands]
    EstablnitAttNbrTotal = sum(EstablnitAttNbrValues)
    if EstablnitAttNbrTotal > 0:
      EstablnitAttNbrRatio = [value / EstablnitAttNbrTotal * 100 for value in EstablnitAttNbrValues]
    else:
      EstablnitAttNbrRatio = [0 for _ in EstablnitAttNbrValues]
    EstablnitAttNbr_byband['by_band'] = {'band': bands, 'ratio': EstablnitAttNbrRatio, 'counts': EstablnitAttNbrValues}

    EstabAddAttNbr_byband = {
      'overall': {'EstabAddAttNbrAttempt': volteattachcategorys['Sum_EstabAddAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in volteattachbybands]
    EstablnitAttNbrValues = [item['Sum_EstabAddAttNbr'] for item in volteattachbybands]
    EstablnitAttNbrTotal = sum(EstablnitAttNbrValues)
    if EstablnitAttNbrTotal > 0:
      EstablnitAttNbrRatio = [value / EstablnitAttNbrTotal * 100 for value in EstablnitAttNbrValues]
    else:
      EstablnitAttNbrRatio = [0 for _ in EstablnitAttNbrValues]
    EstabAddAttNbr_byband['by_band'] = {'band': bands, 'ratio': EstablnitAttNbrRatio, 'counts': EstablnitAttNbrValues}


    voltefailandsuccessbybandall = {
      'overall': {
        'successrate':((volteattachcategorys['Sum_EstablnitSuccNbr'] + volteattachcategorys['Sum_EstabAddSuccNbr']) / (volteattachcategorys['Sum_EstablnitAttNbr'] + volteattachcategorys['Sum_EstabAddAttNbr'])) * 100,
        'failcount':(volteattachcategorys['Sum_EstablnitAttNbr'] + volteattachcategorys['Sum_EstabAddAttNbr']) -  (volteattachcategorys['Sum_EstablnitSuccNbr'] + volteattachcategorys['Sum_EstabAddSuccNbr'])
      },
      'by_band': {}
    }
    voltefailcount = [((item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr']) - (item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddSuccNbr'])) for item in volteattachcategorysbybands]
    voltefailcounttotal = sum(voltefailcount)
    voltesuccessrate = [((item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddSuccNbr']) / (item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr'])) * 100 for item in volteattachcategorysbybands]
    if voltefailcounttotal > 0:
      failratebyband = [value / voltefailcounttotal * 100 for value in voltefailcount]
    else:
      failratebyband = [0 for _ in voltefailcount]
    voltefailandsuccessbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': voltefailcount,
      'erabsuccessrate': voltesuccessrate
    }
    
    return Response({
      'voltesetup_trend_all': voltesetup_trend_all, 'voltesetup_trend_23': voltesetup_trend_23, 'voltesetup_trend_26': voltesetup_trend_26, 'voltesetup_trend_800': voltesetup_trend_800,
      'regional_erabsetup_trend_23': regional_voltesetup_trend_23, 'regional_erabsetup_trend_26': regional_voltesetup_trend_26, 'regional_erabsetup_trend_800': regional_voltesetup_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband, 'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'volteattemptcoutbyband': volteattemptcoutbyband, 
      'EstablnitAttNbr_byband': EstablnitAttNbr_byband, 
      'EstabAddAttNbr_byband': EstabAddAttNbr_byband,
      'voltefailandsuccessbybandall': voltefailandsuccessbybandall
    })

class StatisticeRABSetup(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)
    
    #eRAB SETUP CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['erab_setup_success_rate_ngbr'] for stat in statistics_all]
    erabsetup_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    values_23 = [stat['erab_setup_success_rate_ngbr'] for stat in statistics_23]
    erabsetup_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    values_26 = [stat['erab_setup_success_rate_ngbr'] for stat in statistics_26]
    erabsetup_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    values_800 = [stat['erab_setup_success_rate_ngbr'] for stat in statistics_800]
    erabsetup_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #eRAB SETUP CALCULATEDRESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    regional_values_23 = [stat['erab_setup_success_rate_ngbr'] for stat in regional_stat_23]
    regional_erabsetup_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    regional_values_26 = [stat['erab_setup_success_rate_ngbr'] for stat in regional_stat_26]
    regional_erabsetup_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'erab_setup_success_rate_ngbr').order_by('weeknum')
    regional_values_800 = [stat['erab_setup_success_rate_ngbr'] for stat in regional_stat_800]
    regional_erabsetup_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #eRAB SETUP CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(erab_setup_success_rate_ngbr__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(erab_setup_success_rate_ngbr__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #eRAB SETUP SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(erab_setup_success_rate_ngbr__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(erab_setup_success_rate_ngbr__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(erab_setup_success_rate_ngbr__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(erab_setup_success_rate_ngbr__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #eRAB SETUP DATA PROCESSING
    erabattachcategorys = celldata_queryset.aggregate(
      Sum_EstablnitSuccNbr=Sum('establnitsuccnbr_qci59'),
      Sum_EstabAddSuccNbr=Sum('estabaddsuccnbr_qci59'),
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci59'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci59')
    )

    erabattachcategorysbybands = celldata_queryset.values('band').annotate(
      Sum_EstablnitSuccNbr=Sum('establnitsuccnbr_qci59'),
      Sum_EstabAddSuccNbr=Sum('estabaddsuccnbr_qci59'),
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci59'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci59')
    )

    erabattachbybands = celldata_queryset.values('band').annotate(
      Sum_EstablnitAttNbr=Sum('establnitattnbr_qci59'),
      Sum_EstabAddAttNbr=Sum('estabaddattnbr_qci59')
    )

    erabattemptcoutbyband = {
      'overall': {'eRABAttempt': erabattachcategorys['Sum_EstablnitAttNbr'] + erabattachcategorys['Sum_EstabAddAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in erabattachbybands]
    erabconnectionvalues = [item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr'] for item in erabattachbybands]
    erabconnectiontotal = sum(erabconnectionvalues)
    if erabconnectiontotal > 0:
      erabconnectionratios = [value / erabconnectiontotal * 100 for value in erabconnectionvalues]
    else:
      erabconnectionratios = [0 for _ in erabconnectionvalues]
    erabattemptcoutbyband['by_band'] = {'band': bands, 'ratio': erabconnectionratios, 'counts': erabconnectionvalues}

    EstablnitAttNbr_byband = {
      'overall': {'EstablnitAttNbrAttempt': erabattachcategorys['Sum_EstablnitAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in erabattachbybands]
    EstablnitAttNbrValues = [item['Sum_EstablnitAttNbr'] for item in erabattachbybands]
    EstablnitAttNbrTotal = sum(EstablnitAttNbrValues)
    if EstablnitAttNbrTotal > 0:
      EstablnitAttNbrRatio = [value / EstablnitAttNbrTotal * 100 for value in EstablnitAttNbrValues]
    else:
      EstablnitAttNbrRatio = [0 for _ in EstablnitAttNbrValues]
    EstablnitAttNbr_byband['by_band'] = {'band': bands, 'ratio': EstablnitAttNbrRatio, 'counts': EstablnitAttNbrValues}

    EstabAddAttNbr_byband = {
      'overall': {'EstabAddAttNbrAttempt': erabattachcategorys['Sum_EstabAddAttNbr']},
      'by_band': {}
    }
    bands = [item['band'] for item in erabattachbybands]
    EstablnitAttNbrValues = [item['Sum_EstabAddAttNbr'] for item in erabattachbybands]
    EstablnitAttNbrTotal = sum(EstablnitAttNbrValues)
    if EstablnitAttNbrTotal > 0:
      EstablnitAttNbrRatio = [value / EstablnitAttNbrTotal * 100 for value in EstablnitAttNbrValues]
    else:
      EstablnitAttNbrRatio = [0 for _ in EstablnitAttNbrValues]
    EstabAddAttNbr_byband['by_band'] = {'band': bands, 'ratio': EstablnitAttNbrRatio, 'counts': EstablnitAttNbrValues}


    erabfailandsuccessbybandall = {
      'overall': {
        'successrate':((erabattachcategorys['Sum_EstablnitSuccNbr'] + erabattachcategorys['Sum_EstabAddSuccNbr']) / (erabattachcategorys['Sum_EstablnitAttNbr'] + erabattachcategorys['Sum_EstabAddAttNbr'])) * 100,
        'failcount':(erabattachcategorys['Sum_EstablnitAttNbr'] + erabattachcategorys['Sum_EstabAddAttNbr']) -  (erabattachcategorys['Sum_EstablnitSuccNbr'] + erabattachcategorys['Sum_EstabAddSuccNbr'])
      },
      'by_band': {}
    }
    erabfailcount = [((item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr']) - (item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddSuccNbr'])) for item in erabattachcategorysbybands]
    erabfailcounttotal = sum(erabfailcount)
    erabsuccessrate = [((item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddSuccNbr']) / (item['Sum_EstablnitAttNbr'] + item['Sum_EstabAddAttNbr'])) * 100 for item in erabattachcategorysbybands]
    if erabfailcounttotal > 0:
      failratebyband = [value / erabfailcounttotal * 100 for value in erabfailcount]
    else:
      failratebyband = [0 for _ in erabfailcount]
    erabfailandsuccessbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': erabfailcount,
      'erabsuccessrate': erabsuccessrate
    }

    return Response({
      'erabsetup_trend_all': erabsetup_trend_all, 'erabsetup_trend_23': erabsetup_trend_23, 'erabsetup_trend_26': erabsetup_trend_26, 'erabsetup_trend_800': erabsetup_trend_800,
      'regional_erabsetup_trend_23': regional_erabsetup_trend_23, 'regional_erabsetup_trend_26': regional_erabsetup_trend_26, 'regional_erabsetup_trend_800': regional_erabsetup_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'erabattemptcoutbyband': erabattemptcoutbyband, 'EstablnitAttNbr_byband': EstablnitAttNbr_byband, 'EstabAddAttNbr_byband': EstabAddAttNbr_byband,
      'erabfailandsuccessbybandall': erabfailandsuccessbybandall,
    })

class StatisticRRCSetup(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #RRC SETUP CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['rrc_setup_success_rate'] for stat in statistics_all]
    rrcsetup_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    values_23 = [stat['rrc_setup_success_rate'] for stat in statistics_23]
    rrcsetup_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    values_26 = [stat['rrc_setup_success_rate'] for stat in statistics_26]
    rrcsetup_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    values_800 = [stat['rrc_setup_success_rate'] for stat in statistics_800]
    rrcsetup_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #RRC SETUP CALCULATEDRESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    regional_values_23 = [stat['rrc_setup_success_rate'] for stat in regional_stat_23]
    regional_rrcsetup_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    regional_values_26 = [stat['rrc_setup_success_rate'] for stat in regional_stat_26]
    regional_rrcsetup_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'rrc_setup_success_rate').order_by('weeknum')
    regional_values_800 = [stat['rrc_setup_success_rate'] for stat in regional_stat_800]
    regional_rrcsetup_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #RRC SETUP CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(rrc_setup_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(rrc_setup_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #RRC SETUP SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(rrc_setup_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(rrc_setup_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(rrc_setup_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(rrc_setup_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #RRC SETUP DATA PROCESSING
    rrcattachcategorys = celldata_queryset.aggregate(
      sum_connestabatt=Sum('connestabatt'),
      sum_connestabsucc=Sum('connestabsucc')
    )

    rrcattachcategorysbybands = celldata_queryset.values('band').annotate(
      sum_connestabatt=Sum('connestabatt'),
      sum_connestabsucc=Sum('connestabsucc')
    )

    rrcattachbybands = celldata_queryset.values('band').annotate(
      sum_ceonnestabatt=Sum('connestabatt')
    )

    rrcattemptcoutbyband = {
      'overall': {'RRCAttempt': rrcattachcategorys['sum_connestabatt']},
      'by_band': {}
    }
    bands = [item['band'] for item in rrcattachbybands]
    rrcconnectionvalues = [item['sum_ceonnestabatt'] for item in rrcattachbybands]
    rrcconnectiontotal = sum(rrcconnectionvalues)
    if rrcconnectiontotal > 0:
      rrcconnectionratios = [value / rrcconnectiontotal * 100 for value in rrcconnectionvalues]
    else:
      rrcconnectionratios = [0 for _ in rrcconnectionvalues]
    rrcattemptcoutbyband['by_band'] = {'band': bands, 'values': rrcconnectionratios, 'counts': rrcconnectionvalues}

    rrcconnectionsuccessrate = {
      'overall': {
        'ConnEstabAtt':(rrcattachcategorys['sum_connestabsucc'] / rrcattachcategorys['sum_connestabatt']) * 100,
      },
      'by_band': {}
    }
    rrcconnectionsuccessrateband = [item['band'] for item in rrcattachcategorysbybands]
    rrcconnectionsuccessratefailcount = [(item['sum_connestabatt'] - item['sum_connestabsucc']) for item in rrcattachcategorysbybands]
    rrcconnectionfailtotal = sum(rrcconnectionsuccessratefailcount)
    if rrcconnectionfailtotal > 0:
      rrcconnectionfailratio = [value / rrcconnectionfailtotal * 100 for value in rrcconnectionsuccessratefailcount]
    else:
      rrcconnectionfailratio = [0 for _ in rrcconnectionsuccessratefailcount]
    rrcconnectionsuccessraterate = [(item['sum_connestabsucc'] / item['sum_connestabatt']) * 100 for item in rrcattachcategorysbybands]
    rrcconnectionsuccessrate['by_band'] = {
      'band': rrcconnectionsuccessrateband, 
      'values': rrcconnectionsuccessraterate, 
      'failcount': rrcconnectionsuccessratefailcount,
      'failratio': rrcconnectionfailratio}

    return Response({
      'rrcsetup_trend_all': rrcsetup_trend_all,
      'rrcsetup_trend_23': rrcsetup_trend_23,
      'rrcsetup_trend_26': rrcsetup_trend_26,
      'rrcsetup_trend_800': rrcsetup_trend_800,
      'regional_rrcsetup_trend_23': regional_rrcsetup_trend_23,
      'regional_rrcsetup_trend_26': regional_rrcsetup_trend_26,
      'regional_rrcsetup_trend_800': regional_rrcsetup_trend_800,
      'rrcattemptcoutbyband': rrcattemptcoutbyband,
      'rrcconnectionsuccessrate': rrcconnectionsuccessrate,
      'fail_cluster_count_all': fail_cluster_count_all,
      'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all,
      'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all,
      'fail_cell_count_byband': fail_cell_count_byband
    })

class StatisticAttachSetup(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['attach_setup_success_rate'] for stat in statistics_all]
    attach_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    values_23 = [stat['attach_setup_success_rate'] for stat in statistics_23]
    attach_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    values_26 = [stat['attach_setup_success_rate'] for stat in statistics_26]
    attach_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    values_800 = [stat['attach_setup_success_rate'] for stat in statistics_800]
    attach_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #CELL AVAIL CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    regional_values_23 = [stat['attach_setup_success_rate'] for stat in regional_stat_23]
    regional_attach_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    regional_values_26 = [stat['attach_setup_success_rate'] for stat in regional_stat_26]
    regional_attach_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'attach_setup_success_rate').order_by('weeknum')
    regional_values_800 = [stat['attach_setup_success_rate'] for stat in regional_stat_800]
    regional_attach_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(attach_setup_success_rate__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(attach_setup_success_rate__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(attach_setup_success_rate__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(attach_setup_success_rate__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(attach_setup_success_rate__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(attach_setup_success_rate__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #DATA PROCESSING
    attachcategorys = celldata_queryset.aggregate(
      Sum_connestabsucc=Sum('connestabsucc'), Sum_connestabatt=Sum('connestabatt'), Sum_s1connestabsucc=Sum('s1connestabsucc'),
      Sum_s1connestabatt=Sum('s1connestabatt'), Sum_establnitsuccnbr=Sum('establnitsuccnbr'), Sum_establnitattnbr=Sum('establnitattnbr'),
    )

    attachcategorysbyband = celldata_queryset.values('band').annotate(
      Sum_connestabsucc=Sum('connestabsucc'), Sum_connestabatt=Sum('connestabatt'), Sum_s1connestabsucc=Sum('s1connestabsucc'),
      Sum_s1connestabatt=Sum('s1connestabatt'), Sum_establnitsuccnbr=Sum('establnitsuccnbr'), Sum_establnitattnbr=Sum('establnitattnbr'),
    )

    bands = [item['band'] for item in attachcategorysbyband]

    attachnominatebyband = {
      'overall': {
        'NominateTotal': (attachcategorys['Sum_connestabsucc'] + attachcategorys['Sum_s1connestabsucc'] + attachcategorys['Sum_establnitsuccnbr']),
        'deNomnateTotal': (attachcategorys['Sum_connestabatt'] + attachcategorys['Sum_s1connestabatt'] + attachcategorys['Sum_establnitattnbr']),
        'ConnEstabSucc': attachcategorys['Sum_connestabsucc'], 'ConnEstabAtt': attachcategorys['Sum_connestabatt'],
        'S1ConnEstabSucc': attachcategorys['Sum_s1connestabsucc'], 'S1ConnEstabAtt': attachcategorys['Sum_s1connestabatt'],
        'EstabInitSuccNBR': attachcategorys['Sum_establnitsuccnbr'], 'EstabInitAttNBR': attachcategorys['Sum_establnitattnbr']
        },
      'by_band': {}
    }
    attachnominate = [item['Sum_connestabatt'] + item['Sum_s1connestabatt'] + item['Sum_establnitattnbr'] for item in attachcategorysbyband]
    attachnominatetotal = sum(attachnominate)
    if attachnominatetotal > 0:
      attachratios = [value / attachnominatetotal * 100 for value in attachnominate]
    else:
      attachratios = [0 for _ in attachnominate]
    attachnominatebyband['by_band'] = {'band': bands, 'ratio': attachratios, 'counts': attachnominate}

    connestabbyband = {
      'overall': {
        'NominateTotal': attachcategorys['Sum_connestabsucc'],
        'deNomnateTotal': attachcategorys['Sum_connestabatt']
        },
      'by_band': {}
    }
    connestab = [item['Sum_connestabatt'] for item in attachcategorysbyband]
    connestabtotal = sum(connestab)
    if connestabtotal > 0:
      connestabratios = [value / connestabtotal * 100 for value in connestab]
    else:
      connestabratios = [0 for _ in connestab]
    connestabbyband['by_band'] = {'band': bands, 'ratio': connestabratios, 'counts': connestab}

    s1connestabbyband = {
      'overall': {
        'NominateTotal': attachcategorys['Sum_s1connestabsucc'],
        'deNomnateTotal': attachcategorys['Sum_s1connestabatt']
        },
      'by_band': {}
    }
    s1connestab = [item['Sum_s1connestabatt'] for item in attachcategorysbyband]
    s1connestabtotal = sum(s1connestab)
    if s1connestabtotal > 0:
      s1connestabratios = [value / s1connestabtotal * 100 for value in s1connestab]
    else:
      s1connestabratios = [0 for _ in s1connestab]
    s1connestabbyband['by_band'] = {'band': bands, 'ratio': s1connestabratios, 'counts': s1connestab}

    establnitbyband = {
      'overall': {
        'NominateTotal': attachcategorys['Sum_establnitsuccnbr'],
        'deNomnateTotal': attachcategorys['Sum_establnitattnbr']
        },
      'by_band': {}
    }
    establnit = [item['Sum_establnitattnbr'] for item in attachcategorysbyband]
    establnittotal = sum(establnit)
    if establnittotal > 0:
      establnitratios = [value / establnittotal * 100 for value in establnit]
    else:
      establnitratios = [0 for _ in establnit]
    establnitbyband['by_band'] = {'band': bands, 'ratio': establnitratios, 'counts': establnit}

    connestabyband = {
      'overall': {
        'NominateTotal': attachcategorys['Sum_connestabsucc'],
        'deNomnateTotal': attachcategorys['Sum_connestabatt']
        },
      'by_band': {}
    }
    connesta = [item['Sum_connestabatt'] for item in attachcategorysbyband]
    connestatotal = sum(connesta)
    if connestatotal > 0:
      connestaratios = [value / connestatotal * 100 for value in connesta]
    else:
      connestaratios = [0 for _ in connesta]
    connestabyband['by_band'] = {'band': bands, 'ratio': connestaratios, 'counts': connesta}
    

    attachfallbybandall = {
      'overall': {
        'attachrate': ((attachcategorys['Sum_connestabsucc'] / attachcategorys['Sum_connestabatt']) *
        (attachcategorys['Sum_s1connestabsucc'] / attachcategorys['Sum_s1connestabatt']) *
        (attachcategorys['Sum_establnitsuccnbr'] / attachcategorys['Sum_establnitattnbr'])) * 100,
        'failcount': (attachcategorys['Sum_connestabatt'] + attachcategorys['Sum_s1connestabatt'] + attachcategorys['Sum_establnitattnbr']) - 
        (attachcategorys['Sum_connestabsucc'] + attachcategorys['Sum_s1connestabsucc'] + attachcategorys['Sum_establnitsuccnbr'])
      },
      'by_band': {}
    }
    attachfailcount = [(item['Sum_connestabatt'] + item['Sum_establnitattnbr'] + item['Sum_establnitattnbr']) - 
      (item['Sum_connestabsucc'] + item['Sum_s1connestabsucc'] + item['Sum_establnitsuccnbr']) for item in attachcategorysbyband]
    attachfailcounttotal = sum(attachfailcount)
    attachrate = [((item['Sum_connestabsucc'] / item['Sum_connestabatt']) *
      (item['Sum_s1connestabsucc'] / item['Sum_s1connestabatt']) * 
      (item['Sum_establnitsuccnbr'] / item['Sum_establnitattnbr'])) * 100 for item in attachcategorysbyband]
    if attachfailcounttotal > 0:
      failratebyband = [value / attachfailcounttotal * 100 for value in attachfailcount]
    else:
      failratebyband = [0 for _ in attachfailcount]
    attachfallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': attachfailcount,
      'attachrate': attachrate
    }

    attachbyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    attachbyband_cluster_23 = attachbyband_cluster_23.annotate(
      SumConnEstabAtt=Sum('connestabatt'), SumS1ConnEstabAtt=Sum('s1connestabatt'), SumEstabInitAttNBR=Sum('establnitattnbr'),
      SumConnEstabSucc=Sum('connestabsucc'), SumS1ConnEstabSucc=Sum('s1connestabsucc'), SumEstabInitSuccNBR=Sum('establnitsuccnbr'),
    )
    attachbyband_cluster_23 = attachbyband_cluster_23.annotate(
      Sum_AttachFail=(F('SumConnEstabAtt') + F('SumS1ConnEstabAtt') + F('establnitattnbr')) - 
      (F('connestabsucc') + F('s1connestabsucc') + F('establnitsuccnbr'))
    )
    attachbyband_cluster_23 = attachbyband_cluster_23.annotate(
      attachfailtotal=Coalesce(F('Sum_AttachFail'), Value(0))
    )
    impact_clusters_23 = attachbyband_cluster_23.order_by('-attachfailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'attachfailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['attachfailtotal'].append(cluster['attachfailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    attachbyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    attachbyband_cluster_26 = attachbyband_cluster_26.annotate(
      SumConnEstabAtt=Sum('connestabatt'), SumS1ConnEstabAtt=Sum('s1connestabatt'), SumEstabInitAttNBR=Sum('establnitattnbr'),
      SumConnEstabSucc=Sum('connestabsucc'), SumS1ConnEstabSucc=Sum('s1connestabsucc'), SumEstabInitSuccNBR=Sum('establnitsuccnbr'),
    )
    attachbyband_cluster_26 = attachbyband_cluster_26.annotate(
      Sum_AttachFail=(F('SumConnEstabAtt') + F('SumS1ConnEstabAtt') + F('establnitattnbr')) - 
      (F('connestabsucc') + F('s1connestabsucc') + F('establnitsuccnbr'))
    )
    attachbyband_cluster_26 = attachbyband_cluster_26.annotate(
      attachfailtotal=Coalesce(F('Sum_AttachFail'), Value(0))
    )
    impact_clusters_26 = attachbyband_cluster_26.order_by('-attachfailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'attachfailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['attachfailtotal'].append(cluster['attachfailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    attachbyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    attachbyband_cluster_800 = attachbyband_cluster_800.annotate(
      SumConnEstabAtt=Sum('connestabatt'), SumS1ConnEstabAtt=Sum('s1connestabatt'), SumEstabInitAttNBR=Sum('establnitattnbr'),
      SumConnEstabSucc=Sum('connestabsucc'), SumS1ConnEstabSucc=Sum('s1connestabsucc'), SumEstabInitSuccNBR=Sum('establnitsuccnbr'),
    )
    attachbyband_cluster_800 = attachbyband_cluster_800.annotate(
      Sum_AttachFail=(F('SumConnEstabAtt') + F('SumS1ConnEstabAtt') + F('establnitattnbr')) - 
      (F('connestabsucc') + F('s1connestabsucc') + F('establnitsuccnbr'))
    )
    attachbyband_cluster_800 = attachbyband_cluster_800.annotate(
      attachfailtotal=Coalesce(F('Sum_AttachFail'), Value(0))
    )
    impact_clusters_800 = attachbyband_cluster_800.order_by('-attachfailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'attachfailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['attachfailtotal'].append(cluster['attachfailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      'attach_trend_all': attach_trend_all, 'attach_trend_23': attach_trend_23, 'attach_trend_26': attach_trend_26, 'attach_trend_800': attach_trend_800,
      'regional_attach_trend_23': regional_attach_trend_23, 'regional_attach_trend_26': regional_attach_trend_26, 'regional_attach_trend_800': regional_attach_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'attachnominatebyband': attachnominatebyband, 'connestabbyband': connestabbyband, 's1connestabbyband': s1connestabbyband, 'establnitbyband': establnitbyband,
      'attachfallbybandall': attachfallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

class StatisticCellAvailability(APIView):
  def get(self, request, *args, **kwargs):
    base_queryset = StatisticCalculated.objects.all()
    cell_queryset = Statistic.objects.all()
    celldata_queryset = StatisticData.objects.exclude(sitestatus='Dismantled').all()
    cluster_queryset = StatisticCalculatedCluster.objects.all()

    last_10week = (base_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:10])
    last_1week = (cluster_queryset.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1])

    cluster = request.query_params.get('cluster')
    band = request.query_params.get('band')
    region = request.query_params.get('region')

    #URL Query
    if band:
      celldata_queryset = celldata_queryset.filter(band=band)
    if region:
      celldata_queryset = celldata_queryset.filter(region__region=region)
      cluster_queryset = cluster_queryset.filter(region__region=region)
      cell_queryset = cell_queryset.filter(region__region=region)
    if cluster:
      celldata_queryset = celldata_queryset.filter(cluster=cluster)

    #CELL AVAIL CALCULATED RESULT PROCESSING FOR ALL
    statistics_all = base_queryset.filter(weeknum__in=last_10week, category='All', band='All').values('weeknum', 'cell_availability').order_by('weeknum')
    weeknums = [stat['weeknum'] for stat in statistics_all]
    values_all = [stat['cell_availability'] for stat in statistics_all]
    cellavail_trend_all = {'weeknums': weeknums, 'values': values_all}

    statistics_23 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.3G').values('weeknum', 'cell_availability').order_by('weeknum')
    values_23 = [stat['cell_availability'] for stat in statistics_23]
    cellavail_trend_23 = {'weeknums': weeknums, 'values': values_23}
    
    statistics_26 = base_queryset.filter(weeknum__in=last_10week, category='All', band='2.6G').values('weeknum', 'cell_availability').order_by('weeknum')
    values_26 = [stat['cell_availability'] for stat in statistics_26]
    cellavail_trend_26 = {'weeknums': weeknums, 'values': values_26}
    
    statistics_800 = base_queryset.filter(weeknum__in=last_10week, category='All', band='800M').values('weeknum', 'cell_availability').order_by('weeknum')
    values_800 = [stat['cell_availability'] for stat in statistics_800]
    cellavail_trend_800 = {'weeknums': weeknums, 'values': values_800}

    #CELL AVAIL CALCULATED RESULT PROCESSING FOR REGIONAL
    regional_stat_23 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.3G', region__region=region).values('weeknum', 'cell_availability').order_by('weeknum')
    regional_values_23 = [stat['cell_availability'] for stat in regional_stat_23]
    regional_cellavail_trend_23 = {'weeknums': weeknums, 'values': regional_values_23}

    regional_stat_26 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='2.6G', region__region=region).values('weeknum', 'cell_availability').order_by('weeknum')
    regional_values_26 = [stat['cell_availability'] for stat in regional_stat_26]
    regional_cellavail_trend_26 = {'weeknums': weeknums, 'values': regional_values_26}

    regional_stat_800 = base_queryset.filter(weeknum__in=last_10week, category='Region', band='800M', region__region=region).values('weeknum', 'cell_availability').order_by('weeknum')
    regional_values_800 = [stat['cell_availability'] for stat in regional_stat_800]
    regional_cellavail_trend_800 = {'weeknums': weeknums, 'values': regional_values_800}

    #CELL AVAIL CLUSTER PROCESSING
    fail_cluster_count_all = cluster_queryset.exclude(cluster='#N/A').filter(cell_availability__lt=99, weeknum=last_1week).values('cluster').count()
    fail_cluster_count_byband = {'band': [], 'count': []}
    cluster_count = cluster_queryset.exclude(cluster='#N/A').filter(cell_availability__lt=99, weeknum=last_1week).values('band').annotate(count=Count('cluster')).order_by('band')
    for item in cluster_count:
      fail_cluster_count_byband['band'].append(item['band'])
      fail_cluster_count_byband['count'].append(item['count'])

    #CELL AVAIL SITE PROCESSING
    fail_site_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(cell_availability__lt=99).values('sysid').distinct().count()
    fail_site_count_byband = {'band': [], 'count': []}
    site_count = cell_queryset.exclude(sitestatus='Dismantled').filter(cell_availability__lt=99).values('band').annotate(count=Count('sysid', distinct=True)).order_by('band')
    for item in site_count:
      fail_site_count_byband['band'].append(item['band'])
      fail_site_count_byband['count'].append(item['count'])
    
    fail_cell_count_all = cell_queryset.exclude(sitestatus='Dismantled').filter(cell_availability__lt=99).values('sysid').count()
    fail_cell_count_byband = {'band': [], 'count': []}
    cell_count = cell_queryset.exclude(sitestatus='Dismantled').filter(cell_availability__lt=99).values('band').annotate(count=Count('sysid')).order_by('band')
    for item in cell_count:
      fail_cell_count_byband['band'].append(item['band'])
      fail_cell_count_byband['count'].append(item['count'])

    #CELL AVAIL DATA PROCESSING
    cellavailcategorys = celldata_queryset.aggregate(
      Sum_cellunavailabletimedown=Sum('cellunavailabletimedown'), 
      Sum_cellunavailabletimelock=Sum('cellunavailabletimelock'), 
      Sum_cellavail_pmperiodtime=Sum('cellavail_pmperiodtime'),
    )

    cellavailcategorysbyband = celldata_queryset.values('band').annotate(
      Sum_cellunavailabletimedown=Sum('cellunavailabletimedown'), 
      Sum_cellunavailabletimelock=Sum('cellunavailabletimelock'), 
      Sum_cellavail_pmperiodtime=Sum('cellavail_pmperiodtime'),
    )

    bands = [item['band'] for item in cellavailcategorysbyband]

    cellavaildownbyband = {
      'overall': {
        'DownTime': cellavailcategorys['Sum_cellunavailabletimedown'], 
        'LockTime': cellavailcategorys['Sum_cellunavailabletimelock'],
        'OperateTime': cellavailcategorys['Sum_cellavail_pmperiodtime']
        },
      'by_band': {}
    }
    cellavailnominate = [item['Sum_cellunavailabletimedown'] - item['Sum_cellunavailabletimelock'] for item in cellavailcategorysbyband]
    cellavailnominatetotal = sum(cellavailnominate)
    if cellavailnominatetotal > 0:
      cellavailratios = [value / cellavailnominatetotal * 100 for value in cellavailnominate]
    else:
      cellavailratios = [0 for _ in cellavailnominate]
    cellavaildownbyband['by_band'] = {'band': bands, 'ratio': cellavailratios, 'counts': cellavailnominate}

    cellavailfallbybandall = {
      'overall': {
        's1inhorate': 1- ((cellavailcategorys['Sum_cellunavailabletimedown'] - cellavailcategorys['Sum_cellunavailabletimelock']) / cellavailcategorys['Sum_cellavail_pmperiodtime']) * 100,
        'failcount': (cellavailcategorys['Sum_cellunavailabletimedown'] - cellavailcategorys['Sum_cellunavailabletimelock'])
      },
      'by_band': {}
    }
    cellavailfailcount = [(item['Sum_cellunavailabletimedown'] - item['Sum_cellunavailabletimelock']) for item in cellavailcategorysbyband]
    cellavailfailcounttotal = sum(cellavailfailcount)
    cellavailrate = [(1 - ((item['Sum_cellunavailabletimedown'] - item['Sum_cellunavailabletimelock']) / item['Sum_cellavail_pmperiodtime'])) * 100 for item in cellavailcategorysbyband
    ]
    if cellavailfailcounttotal > 0:
      failratebyband = [value / cellavailfailcounttotal * 100 for value in cellavailfailcount]
    else:
      failratebyband = [0 for _ in cellavailfailcount]
    cellavailfallbybandall['by_band'] = {
      'band': bands, 
      'failratebyband': failratebyband, 
      'failcount': cellavailfailcount,
      'cellavailrate': cellavailrate
    }

    cellavailbyband_cluster_23 = celldata_queryset.filter(band='2.3GHz').values('band', 'cluster')
    cellavailbyband_cluster_23 = cellavailbyband_cluster_23.annotate(
      DownSum=Sum('cellunavailabletimedown'), LockSum=Sum('cellunavailabletimelock'),
    )
    cellavailbyband_cluster_23 = cellavailbyband_cluster_23.annotate(
      Sum_AvailTimeFail=F('DownSum') - F('LockSum')
    )
    cellavailbyband_cluster_23 = cellavailbyband_cluster_23.annotate(
      cellavailfailtotal=Coalesce(F('Sum_AvailTimeFail'), Value(0))
    )
    impact_clusters_23 = cellavailbyband_cluster_23.order_by('-cellavailfailtotal')[:5]
    top_impact_cluster_list_23 = defaultdict(lambda: {'cluster': [], 'cellavailfailtotal': []})
    for cluster in impact_clusters_23:
      band = cluster['band']
      top_impact_cluster_list_23[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_23[band]['cellavailfailtotal'].append(cluster['cellavailfailtotal'])
    top_impact_cluster_list_23 = dict(top_impact_cluster_list_23)

    cellavailbyband_cluster_26 = celldata_queryset.filter(band='2.6GHz').values('band', 'cluster')
    cellavailbyband_cluster_26 = cellavailbyband_cluster_26.annotate(
      DownSum=Sum('cellunavailabletimedown'), LockSum=Sum('cellunavailabletimelock'),
    )
    cellavailbyband_cluster_26 = cellavailbyband_cluster_26.annotate(
      Sum_AvailTimeFail=F('DownSum') - F('LockSum')
    )
    cellavailbyband_cluster_26 = cellavailbyband_cluster_26.annotate(
      cellavailfailtotal=Coalesce(F('Sum_AvailTimeFail'), Value(0))
    )
    impact_clusters_26 = cellavailbyband_cluster_26.order_by('-cellavailfailtotal')[:5]
    top_impact_cluster_list_26 = defaultdict(lambda: {'cluster': [], 'cellavailfailtotal': []})
    for cluster in impact_clusters_26:
      band = cluster['band']
      top_impact_cluster_list_26[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_26[band]['cellavailfailtotal'].append(cluster['cellavailfailtotal'])
    top_impact_cluster_list_26 = dict(top_impact_cluster_list_26)

    cellavailbyband_cluster_800 = celldata_queryset.filter(band='800M').values('band', 'cluster')
    cellavailbyband_cluster_800 = cellavailbyband_cluster_800.annotate(
      DownSum=Sum('cellunavailabletimedown'), LockSum=Sum('cellunavailabletimelock'),
    )
    cellavailbyband_cluster_800 = cellavailbyband_cluster_800.annotate(
      Sum_AvailTimeFail=F('DownSum') - F('LockSum')
    )
    cellavailbyband_cluster_800 = cellavailbyband_cluster_800.annotate(
      cellavailfailtotal=Coalesce(F('Sum_AvailTimeFail'), Value(0))
    )
    impact_clusters_800 = cellavailbyband_cluster_800.order_by('-cellavailfailtotal')[:5]
    top_impact_cluster_list_800 = defaultdict(lambda: {'cluster': [], 'cellavailfailtotal': []})
    for cluster in impact_clusters_800:
      band = cluster['band']
      top_impact_cluster_list_800[band]['cluster'].append(cluster['cluster'])
      top_impact_cluster_list_800[band]['cellavailfailtotal'].append(cluster['cellavailfailtotal'])
    top_impact_cluster_list_800 = dict(top_impact_cluster_list_800)
    
    return Response({
      'cellavail_trend_all': cellavail_trend_all, 'cellavail_trend_23': cellavail_trend_23, 'cellavail_trend_26': cellavail_trend_26, 'cellavail_trend_800': cellavail_trend_800,
      'regional_cellavail_trend_23': regional_cellavail_trend_23, 'regional_cellavail_trend_26': regional_cellavail_trend_26, 'regional_cellavail_trend_800': regional_cellavail_trend_800,
      'fail_cluster_count_all': fail_cluster_count_all, 'fail_cluster_count_byband': fail_cluster_count_byband,
      'fail_site_count_all': fail_site_count_all, 'fail_site_count_byband': fail_site_count_byband,
      'fail_cell_count_all': fail_cell_count_all, 'fail_cell_count_byband': fail_cell_count_byband,
      'cellavaildownbyband': cellavaildownbyband, 'cellavailfallbybandall': cellavailfallbybandall,
      'top_impact_cluster_list_23': top_impact_cluster_list_23, 'top_impact_cluster_list_26': top_impact_cluster_list_26, 'top_impact_cluster_list_800': top_impact_cluster_list_800,
    })

class StatisticCalClusterView(viewsets.ModelViewSet): 
  serializer_class = StatisticCalClusterSerializer
  queryset = StatisticCalculatedCluster.objects.all().order_by('cluster')
  filter_backends = [DjangoFilterBackend]
  filterset_class = StatisticCalClusterFilter

  def get_queryset(self):
    queryset = StatisticCalculatedCluster.objects.all().order_by('-weeknum')
    lastweeknum = queryset.first().weeknum if queryset.exists() else None
    print(lastweeknum)
    if lastweeknum:
      queryset = queryset.filter(weeknum=lastweeknum)
    field = self.request.query_params.get('field')
    if field:
      queryset = queryset.only('region', 'cluster', 'weeknum', 'band', field).order_by(field)
    return queryset

class FailCluster(ListAPIView):
  serializer_class = StatisticCalClusterSerializer
  pagination_class = CustomPagination

  def get(self, request, *args, **kwargs):
    self.lastweeknum = StatisticCalculatedCluster.objects.values_list('weeknum', flat=True).distinct().order_by('-weeknum')[:1]
    self.region_param = request.query_params.get('region')
    return super().get(request, *args, **kwargs)

  def get_queryset(self):
    field = self.request.query_params.get('field')
    band = self.request.query_params.get('band')

    filters = Q(weeknum=self.lastweeknum)

    if band:
      filters &= Q(band=band)
    if self.region_param:
      filters &= Q(region__region=self.region_param)

    if field:
      if field in ['ul_bler', 'dl_bler', 'call_drop_rate_erab_ngbr', 'volte_call_drop_rate_erab_gbr']:
        filters &= Q(**{f'{field}__gte': 1})
      else:
        filters &= Q(**{f'{field}__lt': 99})

    return StatisticCalculatedCluster.objects.filter(filters)

  def get_paginated_response(self, data):
    cluster_count = StatisticCalculatedCluster.objects.filter(weeknum=self.lastweeknum, region__region=self.region_param).values('band').annotate(total=Count('cluster'))
    cluster_total = {'band': [], 'count': []}
    for item in cluster_count:
      cluster_total['band'].append(item['band'])
      cluster_total['count'].append(item['total'])
        
    return self.paginator.get_paginated_response(data, cluster_total)

class FilterSamePCISitesAPIView(generics.ListAPIView):
  serializer_class = SiteLSMinfoPCIFilterSerializer
  queryset = SiteLSMinfo.objects.select_related('sitebasicinfo').filter(sitestatus='OnAir').all()
  pagination_class = LimitOffsetPagination

  def get_nearby_sites(self, lsmdata, lsmdata_queryset, radius):
    nearby_sites = []
    site = lsmdata.sitebasicinfo
    if site is None or site.lat is None or site.lon is None:
      return nearby_sites

    for other_lsmdata in lsmdata_queryset:
      other_site = other_lsmdata.sitebasicinfo
      if lsmdata.id != other_lsmdata.id and other_site and other_site.lat and other_site.lon:
        distance = haversine_distance(float(site.lat), float(site.lon), float(other_site.lat), float(other_site.lon))
        if distance <= radius:
          nearby_sites.append({
            'site': other_lsmdata,
            'distance': distance
          })
    return nearby_sites

  def get_filtered_results(self, lsmdata_queryset, radius):
    filtered_results = []
    for lsmdata in lsmdata_queryset:
      site = lsmdata.sitebasicinfo
      if site is None or site.lat is None or site.lon is None:
        continue

      same_freq_pci_sites = lsmdata_queryset.filter(earfcnul=lsmdata.earfcnul, pci=lsmdata.pci)
      nearby_sites = self.get_nearby_sites(lsmdata, same_freq_pci_sites, radius)

      if nearby_sites:  # 주변 사이트가 있는 경우에만 결과에 추가
        lsmdata_serialized = SiteLSMinfoPCIFilterSerializer(lsmdata).data
        filtered_results.append({
          'site': lsmdata_serialized,
          'nearby_sites': [{
            'site': SiteLSMinfoPCIFilterSerializer(nearby['site']).data,
            'distance': nearby['distance']
          } for nearby in nearby_sites],
          'frequency': lsmdata.earfcnul,
          'pci': lsmdata.pci
        })
    return filtered_results
  
  def get(self, request, *args, **kwargs):
    radius = float(request.query_params.get('radius', 10))
    sitebasicinfo = request.query_params.get('sitebasicinfo')
    try:
      distance = float(request.query_params.get('distance', radius))
    except (ValueError, TypeError):
      distance = radius
    earfcnul = float(request.query_params.get('earfcnul'))
    region = request.query_params.get('region')
    
    cache_key = f"filtered_results_radius_{radius}"
    filtered_results = cache.get(cache_key)

    if filtered_results is None:
      lsmdata_queryset = self.filter_queryset(self.get_queryset())
      filtered_results = self.get_filtered_results(lsmdata_queryset, radius)
      cache.set(cache_key, filtered_results, timeout=86400)  # 캐시 타임아웃은 1시간(3600초)
    
    filtered_data = [
      result for result in filtered_results
      if (
        not sitebasicinfo or sitebasicinfo == result['site']['sitebasicinfo']
      ) and (
        not region or region == result['site']['region']
      ) and (
        not distance or any(nearby['distance'] <= distance for nearby in result['nearby_sites'])
      ) and (
        not earfcnul or earfcnul == result['site']['earfcnul']
      )
    ]
      
    paginated_results = self.paginate_queryset(filtered_data)

    return self.get_paginated_response(paginated_results)

class SitePhyinfoUpdateView(APIView):
  def post(self, request):
    form_data = request.POST
    file = request.data.get('file')

    if file:
      allowed_extensions =['xlsx', 'csv']
      file_extension = file.name.split('.')[-1].lower()
      if file_extension not in allowed_extensions:
        return Response({'error': 'Invalid file format. Only .xlsx and .csv files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
      
      try:
        if file_extension == 'xlsx':
          df = pd.read_excel(file)
        elif file_extension == 'csv':
          df = pd.read_csv(file)
        
        required_columns = ['LTE_Site_ID', 'Port_Num', 'LTE_Sec_ID', 'Band', 'Antenna_Type', 'Height', 'Azimuth', 'M_Tilt', 'E_Tilt']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
          return Response({'error': f'Missing required columns: {", ".join(missing_columns)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        for _, row in df.iterrows():
          sitebasicinfo, _ = SiteBasicinfo.objects.get_or_create(siteid=row['LTE_Site_ID'])
          antenna_type, _ = AntennaType.objects.get_or_create(antennatype=row['Antenna_Type'])

          obj, created = SitePhyinfo.objects.update_or_create(
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
              'modified_by': 'System',
            }
          )

        return Response({'message': 'Data uploaded successfully'}, status=status.HTTP_200_OK)

      except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
      return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    


class AlarmDataViewSet(viewsets.ModelViewSet):
  queryset = AlarmData.objects.all().order_by('-alarmdate', 'sitebasicinfo')
  serializer_class = AlarmDataSerializer
  pagination_class = CustomLimitOffsetPagination

  @action(detail=False, methods=['POST'])
  def upload_file(self, request):
    file = request.FILES.get('file')
    if not file:
      return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    allowed_extensions = ['xlsx', 'csv']
    file_extension = file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
      return Response({'error': 'Invalid file format. Only xlsx and csv file are allowed'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
      if file_extension == 'xlsx':
        df = pd.read_excel(file)
      if file_extension == 'csv':
        df = pd.read_csv(file)

      required_columns = ['Site ID', 'Site Name', 'Folder', 'Alarm']
      missing_columns = [col for col in required_columns if col not in df.columns]
      if missing_columns:
        return Response({'error': f'Missing required columns: {", ".join(missing_columns)}'}, status=status.HTTP_400_BAD_REQUEST)
      
      with transaction.atomic():
        for _, row in df.iterrows():
          sitebasicinfo, _ = SiteBasicinfo.objects.get_or_create(siteid=row['Site ID'])
          AlarmData.objects.create(
            sitebasicinfo=sitebasicinfo,
            site_name=row['Site Name'],
            folder=row['Folder'],
            alarm=row['Alarm'],
            alarmdate=row['Alarm Date']
          )
      
      return Response({'message': 'Data uploaded successfully'}, status=status.HTTP_201_CREATED)
    except SiteBasicinfo.DoesNotExist:
      return Response({'error': f'SiteBasicinfo with id {row["Site ID"]} does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
      return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AlarmAPIView(APIView):
  def get(self, request):
    #get latest alarm date for each site
    latest_alarms = AlarmData.objects.filter(sitebasicinfo=OuterRef('pk')).order_by('-alarmdate').values('alarmdate')[:1]
    #prefetch related alarms for each site, order by alarmdate
    sites_with_alarms = SiteBasicinfo.objects.annotate(latest_alarm_date=Subquery(latest_alarms)).prefetch_related(
      Prefetch('alarmdata_set', queryset=AlarmData.objects.order_by('-alarmdate'), to_attr='recent_alarms')
    )

    result = []
    for site in sites_with_alarms:
      if not site.latest_alarm_date:
        continue

      def remove_whitespace(text):
        return ''.join(text.split())
      
      recent_alarms = [
        remove_whitespace(alarm.alarm)
        for alarm in site.recent_alarms
        if alarm.alarmdate == site.latest_alarm_date
      ]

      seen_alarms = set(recent_alarms)
      previous_alarms = []
      for alarm in site.recent_alarms:
        alarm_text_no_whitespace = remove_whitespace(alarm.alarm)
        if alarm.alarmdate != site.latest_alarm_date and alarm_text_no_whitespace not in seen_alarms:
          previous_alarms.append(alarm_text_no_whitespace)
          seen_alarms.add(alarm_text_no_whitespace)

      if not recent_alarms:
        continue

      first_alarm_date = min(alarm.alarmdate for alarm in site.recent_alarms)
      duration = (site.latest_alarm_date - first_alarm_date).days + 1

      result.append({
        'site_id': site.siteid,
        'site_name': site.sitename,
        'region': site.region.region if site.region else None,
        'state': site.state.state if site.state else None,
        'lat': float(site.lat) if site.lat else None,
        'lon': float(site.lon) if site.lon else None,
        'cluster': site.cluster.cluster if site.cluster else None,
        'contracttype': site.contracttype.contracttype if site.contracttype else None,
        'site_config': site.siteconfig.siteconfig if site.siteconfig else None,
        'alarms': {'recent': recent_alarms, 'previous': previous_alarms},
        'alarm_date': site.latest_alarm_date,
        'duration': duration
      })

    result.sort(key=lambda x: (x['duration'], x['alarm_date']), reverse=True)

    return Response(result)
  

