from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
import os
import datetime
import csv
import requests
import json
import threading
import time

# 폰트 설정
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fonts', 'NanumGothic.ttf')
if os.path.exists(FONT_PATH):
    LabelBase.register(name='NanumGothic', fn_regular=FONT_PATH)
    print("폰트 등록 성공!")

class NaverPlaceSearchApp(App):
    def build(self):
        # 메인 레이아웃
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 앱 타이틀
        title = Label(text='네이버 장소검색', font_size=24, size_hint=(1, None), height=50, font_name='NanumGothic')
        self.main_layout.add_widget(title)
        
        # 검색창 레이아웃 - 높이를 90으로 증가시켰습니다
        search_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=90, spacing=10)
        self.search_input = TextInput(
            hint_text='검색어 입력 (예: 인천 여성의류)', 
            multiline=False, 
            font_name='NanumGothic',
            font_size=40,  # 폰트 크기 더 증가
            size_hint=(0.8, 1),  # 검색창의 너비 비율을 70%에서 80%로 증가
            padding=[15, 15, 15, 15]  # 내부 패딩 더 추가
        )
        search_button = Button(
            text='검색', 
            font_name='NanumGothic',
            font_size=40,  # 폰트 크기 더 증가
            size_hint=(0.2, 1),  # 버튼 너비 비율을 30%에서 20%로 감소
            background_color=(0.2, 0.6, 1, 1)  # 버튼 색상 변경
        )
        search_button.bind(on_press=self.start_search)
        
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(search_button)
        self.main_layout.add_widget(search_layout)
        
        # 상태 표시 레이블
        self.status_label = Label(
            text='준비됨',
            font_name='NanumGothic',
            font_size=25,  # 폰트 크기 더 증가
            size_hint=(1, None),
            height=50,  # 높이 더 증가
            halign='left',
            text_size=(Window.width - 20, None)
        )
        self.main_layout.add_widget(self.status_label)
        
        # 결과 표시 영역 (스크롤 가능)
        scroll_view = ScrollView(size_hint=(1, 1))
        self.result_label = Label(
            text='검색 결과가 여기에 표시됩니다',
            font_name='NanumGothic',
            font_size=35,  # 폰트 크기 더 증가
            size_hint_y=None,
            text_size=(Window.width - 30, None),
            halign='left'
        )
        # 텍스트 길이에 따라 Label 높이 자동 조정
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        scroll_view.add_widget(self.result_label)
        self.main_layout.add_widget(scroll_view)
        
        # CSV 저장 경로를 표시하는 레이블 추가
        self.filepath_label = Label(
            text='',
            font_name='NanumGothic',
            font_size=25,
            size_hint=(1, None),
            height=50,
            halign='left',
            valign='middle',
            text_size=(Window.width - 20, None),
            color=(0.2, 0.6, 0.2, 1)  # 초록색 계열로 설정
        )
        self.main_layout.add_widget(self.filepath_label)
        
        # 하단 버튼 레이아웃
        button_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=80, spacing=10)
        
        # CSV 저장 버튼
        self.save_button = Button(
            text='CSV로 저장 (엑셀파일로 저장)',
            font_name='NanumGothic',
            font_size=40,  # 폰트 크기 더 증가
            disabled=True,
            background_color=(0.2, 0.8, 0.2, 1)  # 버튼 색상 변경
        )
        self.save_button.bind(on_press=self.save_to_csv)
        
        button_layout.add_widget(self.save_button)
        self.main_layout.add_widget(button_layout)
        
        # 검색 결과 저장용 변수
        self.search_results = []
        self.tot_cnt = 0
        
        return self.main_layout
    
    def start_search(self, instance):
        # 검색어 확인
        query = self.search_input.text.strip()
        if not query:
            self.status_label.text = '검색어를 입력하세요'
            return
        
        # 상태 업데이트
        self.status_label.text = f"'{query}' 검색 중..."
        self.save_button.disabled = True
        self.search_results = []
        self.tot_cnt = 0
        
        # 별도 스레드에서 검색 실행 (UI 차단 방지)
        threading.Thread(target=self.perform_search, args=(query,)).start()
    
    # JSON 데이터 시작 인덱스 증가 함수 (70개씩)
    def increment_start(self, json_data):
        for item in json_data:
            if 'variables' in item and 'input' in item['variables']:
                item['variables']['input']['start'] += item['variables']['input']['display']
        return json_data
    
    # JSON 데이터 시작 인덱스 증가 함수 (1개씩)
    def increment_start_1(self, json_data):
        for item in json_data:
            if 'variables' in item and 'input' in item['variables']:
                item['variables']['input']['start'] += 1
        return json_data
    
    # JSON 데이터 표시 개수 1로 설정 함수
    def increment_display_1(self, json_data):
        for item in json_data:
            if 'variables' in item and 'input' in item['variables']:
                item['variables']['input']['display'] = 1
        return json_data
    
    def perform_search(self, query):
        try:
            # 원본 코드의 쿠키와 헤더, JSON 구조 완전히 복제
            cookies = {
                'NAC': 'PrBGBgQwSXUS',
                'NNB': 'MRZ252EC5DHWO',
                'ASID': 'b6dc330e00000195871ef27f0000004c',
                'nid_inf': '2017734210',
                'NID_JKL': '8HCgQA3s3JrIwZMPq4e7CxMmOrnPP3YvJmPfLXBQNpU=',
                'NACT': '1',
                'recent': '%EC%98%81%EC%A2%85%EB%8F%84%20%EC%9D%8C%EC%8B%9D%EC%A0%90',
                'page_uid': 'i94oqwqVN8VssCOpuxhssssssjl-260536',
                'SRT30': '1741843172',
                'SRT5': '1741843172',
                'BUC': 'yZjAqF7RBFEnaGVy4B5POJXICU1RCF3V0fRJY-FGwVM=',
            }

            headers = {
                'accept': '*/*',
                'accept-language': 'ko',
                'content-type': 'application/json',
                'origin': 'https://pcmap.place.naver.com',
                'priority': 'u=1, i',
                'referer': 'https://pcmap.place.naver.com/place/list?query=%EC%9D%B8%EC%B2%9C%20%EC%97%AC%EC%84%B1%EC%9D%98%EB%A5%98&x=126.70515099999591&y=37.455942000003404&clientX=126.531534&clientY=37.494249&bounds=126.3268093251881%3B37.01587223459563%3B127.09722558495474%3B37.88259928051234&display=70&ts=1741843946713&additionalHeight=76&locale=ko&mapUrl=https%3A%2F%2Fmap.naver.com%2Fp%2Fsearch%2F%EC%9D%B8%EC%B2%9C%20%EC%97%AC%EC%84%B1%EC%9D%98%EB%A5%98',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'x-wtm-graphql': 'eyJhcmciOiLsnbjsspwg7Jes7ISx7J2Y66WYIiwidHlwZSI6InBsYWNlIiwic291cmNlIjoicGxhY2UifQ',
            }

            # 원본과 동일한 전체 JSON 데이터 구조와 GraphQL 쿼리
            json_data = [
                {
                    'operationName': 'getPlacesList',
                    'variables': {
                        'useReverseGeocode': True,
                        'input': {
                            'query': query,
                            'start': 1,
                            'display': 70,
                            'adult': False,
                            'spq': False,
                            'queryRank': '',
                            'x': '126.70515099999591',
                            'y': '37.455942000003404',
                            'deviceType': 'pcmap',
                            'bounds': '126.3268093251881;37.01587223459563;127.09722558495474;37.88259928051234',
                        },
                        'isNmap': True,
                        'isBounds': True,
                        'reverseGeocodingInput': {
                            'x': '126.531534',
                            'y': '37.494249',
                        },
                    },
                    'query': 'query getPlacesList($input: PlacesInput, $isNmap: Boolean!, $isBounds: Boolean!, $reverseGeocodingInput: ReverseGeocodingInput, $useReverseGeocode: Boolean = false) {\n  businesses: places(input: $input) {\n    total\n    items {\n      id\n      name\n      normalizedName\n      category\n      detailCid {\n        c0\n        c1\n        c2\n        c3\n        __typename\n      }\n      categoryCodeList\n      dbType\n      distance\n      roadAddress\n      address\n      fullAddress\n      commonAddress\n      bookingUrl\n      phone\n      virtualPhone\n      businessHours\n      daysOff\n      imageUrl\n      imageCount\n      x\n      y\n      poiInfo {\n        polyline {\n          shapeKey {\n            id\n            name\n            version\n            __typename\n          }\n          boundary {\n            minX\n            minY\n            maxX\n            maxY\n            __typename\n          }\n          details {\n            totalDistance\n            arrivalAddress\n            departureAddress\n            __typename\n          }\n          __typename\n        }\n        polygon {\n          shapeKey {\n            id\n            name\n            version\n            __typename\n          }\n          boundary {\n            minX\n            minY\n            maxX\n            maxY\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      subwayId\n      markerId @include(if: $isNmap)\n      markerLabel @include(if: $isNmap) {\n        text\n        style\n        stylePreset\n        __typename\n      }\n      imageMarker @include(if: $isNmap) {\n        marker\n        markerSelected\n        __typename\n      }\n      oilPrice @include(if: $isNmap) {\n        gasoline\n        diesel\n        lpg\n        __typename\n      }\n      isPublicGas\n      isDelivery\n      isTableOrder\n      isPreOrder\n      isTakeOut\n      isCvsDelivery\n      hasBooking\n      naverBookingCategory\n      bookingDisplayName\n      bookingBusinessId\n      bookingVisitId\n      bookingPickupId\n      baemin {\n        businessHours {\n          deliveryTime {\n            start\n            end\n            __typename\n          }\n          closeDate {\n            start\n            end\n            __typename\n          }\n          temporaryCloseDate {\n            start\n            end\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      yogiyo {\n        businessHours {\n          actualDeliveryTime {\n            start\n            end\n            __typename\n          }\n          bizHours {\n            start\n            end\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      isPollingStation\n      hasNPay\n      talktalkUrl\n      visitorReviewCount\n      visitorReviewScore\n      blogCafeReviewCount\n      bookingReviewCount\n      streetPanorama {\n        id\n        pan\n        tilt\n        lat\n        lon\n        __typename\n      }\n      naverBookingHubId\n      bookingHubUrl\n      bookingHubButtonName\n      newOpening\n      newBusinessHours {\n        status\n        description\n        dayOff\n        dayOffDescription\n        __typename\n      }\n      coupon {\n        total\n        promotions {\n          promotionSeq\n          couponSeq\n          conditionType\n          image {\n            url\n            __typename\n          }\n          title\n          description\n          type\n          couponUseType\n          __typename\n        }\n        __typename\n      }\n      mid\n      hasMobilePhoneNumber\n      hiking {\n        distance\n        startName\n        endName\n        __typename\n      }\n      __typename\n    }\n    optionsForMap @include(if: $isBounds) {\n      ...OptionsForMap\n      displayCorrectAnswer\n      correctAnswerPlaceId\n      __typename\n    }\n    searchGuide {\n      queryResults {\n        regions {\n          displayTitle\n          query\n          region {\n            rcode\n            __typename\n          }\n          __typename\n        }\n        isBusinessName\n        __typename\n      }\n      queryIndex\n      types\n      __typename\n    }\n    queryString\n    siteSort\n    __typename\n  }\n  reverseGeocodingAddr(input: $reverseGeocodingInput) @include(if: $useReverseGeocode) {\n    ...ReverseGeocodingAddr\n    __typename\n  }\n}\n\nfragment OptionsForMap on OptionsForMap {\n  maxZoom\n  minZoom\n  includeMyLocation\n  maxIncludePoiCount\n  center\n  spotId\n  keepMapBounds\n  __typename\n}\n\nfragment ReverseGeocodingAddr on ReverseGeocodingResult {\n  rcode\n  region\n  __typename\n}',
                },
            ]

            # 원본 코드와 유사하게 페이징 처리 구현
            page = 1
            total_count = 0
            total_items = 0  # 전체 검색 결과 수를 저장할 변수
            
            
            # 첫 번째 단계: 70개씩 조회
            while True:
                # 상태 업데이트
                Clock.schedule_once(lambda dt, p=page, tc=self.tot_cnt: 
                    self.update_status(f"검색 중... (페이지 {p}, 현재 {tc}개)"), 0)
                
                # API 요청
                response = requests.post(
                    'https://pcmap-api.place.naver.com/graphql',
                    cookies=cookies,
                    headers=headers,
                    json=json_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data[0]['data']['businesses']['items']
                    
                    if page == 1:
                        total_items = data[0]['data']['businesses']['total']
                        # 첫 페이지 결과에서 총 아이템 수를
                    
                    # 결과가 없으면 반복 종료
                    if len(items) < 1:
                        break
                    
                    # 결과 처리
                    for item in items:
                        status = ""
                        description = ""
                        day_off = ""
                        day_off_description = ""
                        
                        # newBusinessHours 정보 추출
                        if 'newBusinessHours' in item and item['newBusinessHours']:
                            if 'status' in item['newBusinessHours']:
                                status = item['newBusinessHours']['status']
                            if 'description' in item['newBusinessHours']:
                                description = item['newBusinessHours']['description']
                            if 'dayOff' in item['newBusinessHours'] and item['newBusinessHours']['dayOff']:
                                day_off = item['newBusinessHours']['dayOff']
                            if 'dayOffDescription' in item['newBusinessHours'] and item['newBusinessHours']['dayOffDescription']:
                                day_off_description = item['newBusinessHours']['dayOffDescription']
                        
                        # 결과 데이터 저장
                        self.search_results.append({
                            'id': item['id'],
                            'name': item['name'],
                            'category': item.get('category', ''),
                            'address': item.get('roadAddress', ''),
                            'phone': item.get('phone', ''),
                            'status': status,
                            'hours': description,
                            'day_off': day_off,
                            'day_off_desc': day_off_description
                        })
                    
                    self.tot_cnt += len(items)
                    
                    # 진행 상황 업데이트
                    Clock.schedule_once(lambda dt, tc=self.tot_cnt, tt=total_items: 
                        self.update_status(f"검색 중... ({tc}/{tt}개)"), 0)
                    
                    page += 1
                    
                    # 다음 페이지 설정
                    json_data = self.increment_start(json_data)
                    time.sleep(0.5)  # 속도 제한 방지
                else:
                    # API 오류 처리
                    Clock.schedule_once(lambda dt:
                        self.update_status(f"API 오류: HTTP {response.status_code}"), 0)
                    break
            
            # 두 번째 단계: 1개씩 조회 (남은 결과가 있는 경우)
            if self.tot_cnt < total_items:
                # display 값을 1로 설정
                json_data = self.increment_display_1(json_data)
                
                while True:
                    # 상태 업데이트
                    Clock.schedule_once(lambda dt, p=page, tc=self.tot_cnt: 
                        self.update_status(f"나머지 검색 중... (페이지 {p}, 현재 {tc}개)"), 0)
                    
                    # API 요청
                    response = requests.post(
                        'https://pcmap-api.place.naver.com/graphql',
                        cookies=cookies,
                        headers=headers,
                        json=json_data
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data[0]['data']['businesses']['items']
                        
                        # 결과가 없으면 반복 종료
                        if len(items) < 1:
                            break
                        
                        # 결과 처리
                        for item in items:
                            status = ""
                            description = ""
                            day_off = ""
                            day_off_description = ""
                            
                            # newBusinessHours 정보 추출
                            if 'newBusinessHours' in item and item['newBusinessHours']:
                                if 'status' in item['newBusinessHours']:
                                    status = item['newBusinessHours']['status']
                                if 'description' in item['newBusinessHours']:
                                    description = item['newBusinessHours']['description']
                                if 'dayOff' in item['newBusinessHours'] and item['newBusinessHours']['dayOff']:
                                    day_off = item['newBusinessHours']['dayOff']
                                if 'dayOffDescription' in item['newBusinessHours'] and item['newBusinessHours']['dayOffDescription']:
                                    day_off_description = item['newBusinessHours']['dayOffDescription']
                            
                            # 결과 데이터 저장
                            self.search_results.append({
                                'id': item['id'],
                                'name': item['name'],
                                'category': item.get('category', ''),
                                'address': item.get('roadAddress', ''),
                                'phone': item.get('phone', ''),
                                'status': status,
                                'hours': description,
                                'day_off': day_off,
                                'day_off_desc': day_off_description
                            })
                        
                        self.tot_cnt += len(items)
                        
                        # 진행 상황 업데이트
                        Clock.schedule_once(lambda dt, tc=self.tot_cnt, tt=total_items: 
                            self.update_status(f"검색 중... ({tc}/{tt}개)"), 0)
                        
                        page += 1
                        
                        # 다음 아이템 설정 (1씩 증가)
                        json_data = self.increment_start_1(json_data)
                    else:
                        # API 오류 처리
                        Clock.schedule_once(lambda dt:
                            self.update_status(f"API 오류: HTTP {response.status_code}"), 0)
                        break
            
            # 검색 결과 생성
            result_text = f"'{query}'에 대한 검색 결과 총 {total_items}개 중 {self.tot_cnt}개 조회됨\n\n"
            
            # 무조건 70건은 표시되게 수정 (결과가 70개 미만인 경우에는 모든 결과 표시)
            display_limit = min(70, len(self.search_results))
            
            for i in range(display_limit):
                item = self.search_results[i]
                result_text += f"{i+1}. {item['name']} ({item['category']})\n"
                result_text += f"   주소: {item['address']}\n"
                result_text += f"   전화: {item['phone']}\n"
                
                if item['status']:
                    result_text += f"   상태: {item['status']}\n"
                if item['hours']:
                    result_text += f"   영업시간: {item['hours']}\n"
                if item['day_off']:
                    result_text += f"   휴무일: {item['day_off']}\n"
                
                result_text += "\n"
            
            if display_limit < len(self.search_results):
                result_text += f"...외 {len(self.search_results) - display_limit}개 더 있음 (CSV로 저장하면 모든 결과를 확인할 수 있습니다)"
            
            # 최종 결과 업데이트
            Clock.schedule_once(lambda dt: self.update_results(
                result_text, 
                f"'{query}' 검색 완료: 총 {self.tot_cnt}개 결과"
            ), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_results(
                f"오류 발생: {str(e)}", 
                "검색 실패"
            ), 0)
    
    def update_status(self, status_text):
        """검색 상태를 업데이트합니다."""
        self.status_label.text = status_text
    
    def update_results(self, result_text, status_text):
        """검색 결과를 업데이트합니다."""
        self.result_label.text = result_text
        self.status_label.text = status_text
        
        # 결과가 있으면 저장 버튼 활성화
        self.save_button.disabled = len(self.search_results) == 0
        
        # 검색 시작 시 파일 경로 레이블 초기화
        self.filepath_label.text = ""
    
    def update_filepath(self, filepath_text):
        """파일 경로 정보를 업데이트합니다."""
        self.filepath_label.text = filepath_text
    
    def save_to_csv(self, instance):
        if not self.search_results:
            self.status_label.text = "저장할 결과가 없습니다"
            return
        
        try:
            # 파일명에 타임스탬프 추가
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            query = self.search_input.text.strip().replace(' ', '_')
            
            # 안드로이드인 경우 Download 폴더에 저장
            if platform == 'android':
                try:
                    # 안드로이드의 외부 저장소 경로 가져오기
                    from android.storage import primary_external_storage_path
                    file_path = os.path.join(primary_external_storage_path(), 'Download', f"{query}_{timestamp}.csv")
                except:
                    # 예외 발생 시 기본 경로 사용
                    file_path = f"/storage/emulated/0/Download/{query}_{timestamp}.csv"
            else:
                # 데스크톱에서는 현재 작업 디렉토리에 저장
                file_path = os.path.join(os.getcwd(), f"{query}_{timestamp}.csv")
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 헤더 작성
                writer.writerow([
                    '순번', 'ID', '업체명', '카테고리', '주소', '전화번호', 
                    '영업상태', '영업시간', '휴무일', '휴무일설명'
                ])
                
                # 데이터 작성
                for i, item in enumerate(self.search_results, 1):
                    writer.writerow([
                        i,
                        item['id'],
                        item['name'],
                        item['category'],
                        item['address'],
                        item['phone'],
                        item['status'],
                        item['hours'],
                        item['day_off'],
                        item.get('day_off_desc', '')
                    ])
            
            self.status_label.text = f"CSV 파일 저장 완료"
            # 파일 경로를 별도 레이블에 표시
            Clock.schedule_once(lambda dt: self.update_filepath(f"저장 위치: {file_path}"), 0)
        except Exception as e:
            self.status_label.text = f"파일 저장 오류: {str(e)}"
            # 에러 발생 시 파일 경로 레이블 초기화
            self.filepath_label.text = ""
        
if __name__ == '__main__':
    NaverPlaceSearchApp().run()