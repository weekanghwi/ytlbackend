function convertToGeoJson(apiResponse) {
  return {
    type: 'FeatureCollection',
    features: apiResponse.map(item => {
      return {
        type: 'Feature',
        geometry: item.polygon,
        properties: {
          id: item.id,
          cluster: item.cluster
        }
      }
    })
  }
}

// 함수 정의: 지도 초기화 로직
function initializeMap() {
  // django.jQuery가 사용 가능한지 확인
  if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
    (function($){
      // DOM이 로드되면 실행
      $(document).ready(function() {
        // 지도 엘리먼트 찾기
        var mapElement = document.getElementById('id_polygon_map');
        console.log(mapElement)
        if (mapElement) {
          var map = L.map('id_polygon_map').setView([3.180941, 101.695946], 15)
          // AJAX 호출로 서버에서 클러스터 데이터를 불러옵니다.
          $.ajax({
            url: 'http://10.24.8.120:8000/api/clusters/',  // 클러스터 정보를 제공하는 API 주소
            type: 'GET',
            success: function(response) {
              // 불러온 클러스터 데이터를 지도에 추가
              var geoJSONdata = convertToGeoJson(response);
              console.log(geoJSONdata)
              var clusterLayer = L.geoJSON(geoJSONdata);
              clusterLayer.addTo(map);
            },
            error: function(error) {
              console.log("Error fetching clusters:", error);
            }
          });
        }
      });
    })(django.jQuery);
  } else {
    // django.jQuery가 사용 가능해질 때까지 대기
    setTimeout(initializeMap, 100);
  }
}

// 스크립트 로딩이 완료되면 initializeMap 함수를 호출
initializeMap();
