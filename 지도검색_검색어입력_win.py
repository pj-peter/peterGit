import requests
import os
import json
import csv
from datetime import datetime
import time

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
    # 'cookie': 'NAC=PrBGBgQwSXUS; NNB=MRZ252EC5DHWO; ASID=b6dc330e00000195871ef27f0000004c; nid_inf=2017734210; NID_JKL=8HCgQA3s3JrIwZMPq4e7CxMmOrnPP3YvJmPfLXBQNpU=; NACT=1; recent=%EC%98%81%EC%A2%85%EB%8F%84%20%EC%9D%8C%EC%8B%9D%EC%A0%90; page_uid=i94oqwqVN8VssCOpuxhssssssjl-260536; SRT30=1741843172; SRT5=1741843172; BUC=yZjAqF7RBFEnaGVy4B5POJXICU1RCF3V0fRJY-FGwVM=',
}

json_data = [
    {
        'operationName': 'getPlacesList',
        'variables': {
            'useReverseGeocode': True,
            'input': {
                'query': '인천 여성의류',
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


tot_cnt = 0

def increment_start(json_data):
    for item in json_data:
        if 'variables' in item and 'input' in item['variables']:
            item['variables']['input']['start'] += item['variables']['input']['display']
    return json_data

def increment_start_1(json_data):
    for item in json_data:
        if 'variables' in item and 'input' in item['variables']:
            item['variables']['input']['start'] += 1
    return json_data

def increment_display_1(json_data):
    for item in json_data:
        if 'variables' in item and 'input' in item['variables']:
            item['variables']['input']['display'] = 1
    return json_data

def get_query_value(json_data):
    for data in json_data:
        if 'variables' in data and 'input' in data['variables']:
            return data['variables']['input']['query']
    return None

def response_json(json_data):
    global tot_cnt
    response = requests.post('https://pcmap-api.place.naver.com/graphql', cookies=cookies, headers=headers, json=json_data)
    
    print("START : ", json_data[0]['variables']['input']['start'])
    
    query_value = get_query_value(json_data)
    if query_value:
        query_value = query_value.replace(' ', '_')
        filename = f"{query_value}_{datetime.now().strftime('%Y%m%d')}.csv"
    else:
        filename = f"임시_{datetime.now().strftime('%Y%m%d')}.csv"
        
    # 파일 이름 생성
    #filename = f"여성의류_{datetime.now().strftime('%Y%m%d')}.csv"   

    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # 헤더 작성
        if not file_exists:        
            writer.writerow([
                '순번',
                'ID',
                '업체명',
                '카테고리',
                '주소',
                '전화',
                '영업상태',
                '영업시간',
                '휴무일',
                '휴무일설명'
                ])
            
        # 응답 확인
        if response.status_code == 200:
            try:

                data = response.json()
                # 검색 결과 총 개수 출력
                #total_results = data[0]['data']['businesses']['total']
                #print(f"총 검색 결과: {total_results}개")
            
                # 검색 결과 아이템 처리
                items = data[0]['data']['businesses']['items']
                print(f"현재 페이지 결과: {len(items)}개")
            
                if len(items) < 1:
                    return -1
                
                status = ""
                description = ""
                day_off = ""
                day_off_description = ""
            
                # 각 아이템 정보 출력
                for i, item in enumerate(items, 1):
                    #print(f"\n{i}. {item['name']} ({item['category']})")
                    #print(f"   주소: {item['roadAddress']}")
                    #print(f"   전화: {item['phone']}")

                    # newBusinessHours status 정보 출력
                    if 'newBusinessHours' in item and item['newBusinessHours']:
                        if 'status' in item['newBusinessHours']:
                            status = item['newBusinessHours']['status']
                            #print(f"   영업상태: {item['newBusinessHours']['status']}")
                        if 'description' in item['newBusinessHours']:
                            description = item['newBusinessHours']['description']
                            #print(f"   영업시간: {item['newBusinessHours']['description']}")
                        if 'dayOff' in item['newBusinessHours'] and item['newBusinessHours']['dayOff']:
                            day_off = item['newBusinessHours']['dayOff']
                            #print(f"   휴무일: {item['newBusinessHours']['dayOff']}")
                        if 'dayOffDescription' in item['newBusinessHours'] and item['newBusinessHours']['dayOffDescription']:
                            day_off_description = item['newBusinessHours']['dayOffDescription']
                            #print(f"   휴무일 설명: {item['newBusinessHours']['dayOffDescription']}")
                    #else:
                    #    print("   영업시간 정보 없음")
                        

                    tot_cnt += 1    

                    # CSV 파일 작성
                    writer.writerow([
                            tot_cnt,
                            item['id'],
                            item['name'],
                            item['category'],
                            item['roadAddress'],
                            item['phone'],
                            status,
                            description,
                            day_off,
                            day_off_description
                        ])                               

            except Exception as e:
                print(f"응답 처리 중 오류 발생: {e}")
                print(response.text)
                return -1
        else:
            print(f"API 요청 실패: {response.status_code}")
            print(response.text)
            return -1

    print(f"\nCSV 파일이 성공적으로 저장되었습니다: {filename}")
    
    return 1


def update_query(json_data, search_name):
    for data in json_data:
        if 'variables' in data and 'input' in data['variables']:
            data['variables']['input']['query'] = search_name
    return json_data

def main():
    global tot_cnt
    page = 1
    json_data_tmp = []

    # 사용 예시
    search_name = input("검색어를 입력하세요(ex: 인천 여성의류, 강남구 서초동 여성의류): ")
    updated_json_data = update_query(json_data, search_name)

    if 1:
        while True:
            json_data_tmp = json_data
            liRtn = response_json(json_data_tmp)

            print("page : ", page, "현재 건수 : ", tot_cnt)
            
            #if page > 5:
            #    break
            page += 1

            if liRtn < 0:
                break
            
            json_data_tmp = increment_start(json_data)
            time.sleep(0.5)

        # 위에서 70건씩 조회 하다가 마지막에 남은건수가 70건이 안되면 조회가 안되는 현상으로 1건씩 조회하는 로직 추가함
        increment_display_1(json_data)
        while True:
            json_data_tmp = json_data
            liRtn = response_json(json_data_tmp)
            
            if liRtn < 0:
                break

            print("page : ", page, "현재 건수 : ", tot_cnt)

            json_data_tmp = increment_start_1(json_data)

        print("조회완료 총건수 : ", tot_cnt)
    
    if 0:
        liRtn = response_json(json_data)
        print("page : ", page, "현재 건수 : ", tot_cnt)

    print("END : ", json_data[0]['variables']['input']['query'])
    
    
    return

# 함수 실행
if __name__ == "__main__":
    main()