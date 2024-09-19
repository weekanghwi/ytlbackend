from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from . import views

router = DefaultRouter()
router.register(r'clusters', ClusterViewSet)
router.register(r'sitephyinfo', SitePhyinfoViewSet)
router.register(r'sitelsminfo', SiteLSMinfoViewSet)
router.register(r'siteretinfo', SiteRETinfoViewSet)
router.register(r'sitetxinfo', SiteTXinfoViewSet)
router.register(r'btsmanager', BTSManagerViewSet)
router.register(r'sitebasicinfo', SitebasicinfoViewSet)
router.register(r'pendingcreatesitebasicinfo', PendingCreateSitebasicinfoView)
router.register(r'material', MaterialViewSet)
router.register(r'do', DOViewSet)
router.register(r'install', InstallViewSet)
router.register(r'ssv', SSVViewSet)
router.register(r'optimization', OptimizationViewSet)
router.register(r'optreview', OPTReviewViewSet)
router.register(r'certification', CertificationViewSet)
router.register(r'alltable', AllRelateTableViewSet)
router.register(r'testresult', TestResultViewSet)
router.register(r'statistic', StatisticView)
router.register(r'statisticdata', StatisticDataView)
router.register(r'statisticcalculated', StatisticCalculatedView)
router.register(r'statisticcalcluster', StatisticCalClusterView)
router.register(r'alarmdata', AlarmDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('region/', RegionListAPIView.as_view(), name='region'),
    path('state/', StateListAPIView.as_view(), name='state'),
    path('contracttype/', ContractTypeListAPIView.as_view(), name='contracttype'),
    path('siteconfig/', SiteConfigListAPIView.as_view(), name='siteconfig'),
    path('antennatype/', AntennaTypeListAPIView.as_view(), name='antennatype'),
    path('subcon/', SubconListAPIView.as_view(), name='subcon'),
    path('coicapprovestatus/', COICapproveStatusListAPIView.as_view(), name='coicapprovestatus'),
    path('ssvissue/', SSVIssueListAPIView.as_view(), name='ssvissue'),
    path('opttype/', OPTTypeListAPIView.as_view(), name='opttype'),
    path('optissue/', OPTIssueListAPIView.as_view(), name='optissue'),
    path('pic/', PICListAPIView.as_view(), name='pic'),
    path('optreviewstatus/', OPTReviewStatusAPIView.as_view(), name='optreviewstatus'),
    path('pacapprovestatus/', PACApproveStatusListAPIView.as_view(), name='pacapprovestatus'),
    path('facapprovestatus/', FACApproveStatusListAPIView.as_view(), name='facapprovestatus'),

    #Report csv export
    path('fddmastertracker/', FDDMasterTrackerCSV.as_view(), name='fddmastertracker'),
    path('fddmastertracker2/', Export_FDDMasterTracker_csv, name="fddmastertracker2"),
    path('integrationstatus/', FDDIntegrationTrackerCSV.as_view(), name='integrationstatus'),
    path('integrationstatus2/', Export_FDD_Integrate_tracker_csv, name='integrationstatus2'),

    #Statistic
    path('weeklyreport/', WeeklyReportAPIView.as_view(), name='weeklyreport'),
    path('lsmstatistic/', LSMStatisticAPIView.as_view(), name='lsmstatistic'),
    path('statisticapi/', StatisticAPIView.as_view(), name='lsmstatistic'),
    path('statisticnonpage/', StatisticNonPageAPIView.as_view(), name='statisticnonpage'),
    path('statisticpaged/', StatisticPagedAPIView.as_view(), name='statisticpaged'),
    path('statisticsummary/', StatisticSummaryAPIView.as_view(), name='statisticsummary'),
    path('statisticcalculatedchart/', StatisticCalculatedTrendAPIView.as_view(), name='statisticcalculatedchart'),
    path('statisticweekly/', StatisticWeeklyAPIView.as_view(), name='statisticweekly'),
    path('statisticdatacluster/', StatisticClusterbaseView.as_view(), name='statisticdatacluster'),
    path('failclusterinfo/', FailCluster.as_view(), name='failclusterinfo'),
    # Statistic items detail
    path('filteredcluster/', FilteredStatisticData.as_view(), name='filteredcluster'),
    path('cellavail/', StatisticCellAvailability.as_view(), name='cellavail'),
    path('attachsetup/', StatisticAttachSetup.as_view(), name='attachsetup'),
    path('rrcsetup/', StatisticRRCSetup.as_view(), name='rrcsetup'),
    path('erabsetup/', StatisticeRABSetup.as_view(), name='erabsetup'),
    path('voltesetup/', StatisticVoLTESetup.as_view(), name='voltesetup'),
    path('calldropngbr/', StatisticCallDropnGBR.as_view(), name='calldropngbr'),
    path('calldropgbr/', StatisticCallDropGBR.as_view(), name='calldropgbr'),
    path('intraho/', StatisticIntraHO.as_view(), name='intraho'),
    path('interho/', StatisticInterHO.as_view(), name='interho'),
    path('x2outho/', StatisticX2OutHO.as_view(), name='x2outho'),
    path('x2inho/', StatisticX2inHO.as_view(), name='x2inho'),
    path('s1outho/', StatisticS1OutHO.as_view(), name='s1outho'),
    path('s1inho/', StatisticS1InHO.as_view(), name='s1inho'),

    #SITEPHYINFO UPDATE
    path('sitephyinfo_update/', SitePhyinfoUpdateView.as_view(), name='sitephyinfo_update'),


    #BTS Manager
    path('btsmanager_kml/', BTSManager_KML, name='btsmanager_kml'),
    path('export_btsmanager/', Export_btsmanager_csv, name='export_btsmanager'),

    #Non pagination api
    path('nonpagesitebasicinfo/', NonpageSitebasicinfoListAPIView.as_view(), name='nonpagesitebasicinfo'),
    path('nonpagebtsmanager/', NonPageBTSManagerListAPIView.as_view(), name='nonpagebtsmanager'),

    #Register & Login Logout
    path('register_/', RegisterView_.as_view(), name='register_'),
    path('login_/', LoginView_.as_view(), name='login_'),
    path('logout_/', LogoutView_.as_view(), name='logout_'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),



    #Same PCI filter
    path('samepcifilter_sites/', FilterSamePCISitesAPIView.as_view(), name='same_pci_filter_sites'),

    #Site Alarm
    path('alarms/', AlarmAPIView.as_view(), name='alarm-api'),

    #HeatMap
    path('prbdlheatmap/', StatisticDataHeatmapView.as_view(), name='prbdl_heatmap')
]