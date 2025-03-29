from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.utils import platform
from kivy.network.urlrequest import UrlRequest

import os
import re
import traceback
import urllib.parse
import threading


# 안드로이드와 데스크톱 환경 구분
is_android = platform == 'android'

# 안드로이드에서는 특정 모듈 import 시도
if is_android:
    try:
        from android.permissions import request_permissions, Permission
    except ImportError:
        # 권한 요청 기능 없음 - 무시
        pass

# requests와 BeautifulSoup 사용 가능 여부 체크
try:
    import requests
    import bs4
    from bs4 import BeautifulSoup
    USE_REQUESTS = True
    USE_BS4 = True
except ImportError:
    USE_REQUESTS = False
    USE_BS4 = False


class SimpleNaverScraper:
    def __init__(self, callback=None):
        self.base_url = 'https://finance.naver.com'
        self.list_url = f'{self.base_url}/research/company_list.naver'
        self.callback = callback
        self.is_running = False
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
        }
    
    def log_message(self, message):
        """로그 메시지를 콜백에 전달"""
        if self.callback:
            self.callback(message)
    
    def on_success(self, req, result):
        """URL 요청 성공 시 콜백"""
        try:
            try:
                # 문자열 인코딩 처리
                text = result.decode('euc-kr', errors='replace')
            except (UnicodeDecodeError, AttributeError):
                # 이미 문자열인 경우
                text = str(result)
                
            self.log_message("데이터 수신 완료, 파싱 시작")
            reports = self.parse_report_list(text)
            
            if reports:
                self.log_message(f"총 {len(reports)}개의 리포트를 찾았습니다")
            else:
                self.log_message("리포트를 찾지 못했습니다")
                
            if hasattr(self, 'result_callback') and self.result_callback:
                self.result_callback(reports)
        except Exception as e:
            self.log_message(f"결과 처리 오류: {str(e)}")
            if hasattr(self, 'result_callback') and self.result_callback:
                self.result_callback([])
    
    def on_error(self, req, error):
        """URL 요청 에러 시 콜백"""
        self.log_message(f"네트워크 오류: {error}")
        if hasattr(self, 'result_callback') and self.result_callback:
            self.result_callback([])
    
    def on_failure(self, req, result):
        """URL 요청 실패 시 콜백"""
        self.log_message(f"요청 실패: 상태코드 {req.resp_status}")
        if hasattr(self, 'result_callback') and self.result_callback:
            self.result_callback([])
    
    def get_page_with_kivy(self, page_num=1, callback=None):
        """Kivy의 UrlRequest 사용하여 페이지 요청"""
        self.result_callback = callback
        try:
            params = {'page': page_num}
            url = f"{self.list_url}?{urllib.parse.urlencode(params)}"
            
            self.log_message(f"URL 요청 시작: {url}")
            
            req = UrlRequest(
                url,
                on_success=self.on_success,
                on_error=self.on_error,
                on_failure=self.on_failure,
                req_headers=self.headers,
                verify=False  # SSL 검증 우회 (개발용)
            )
        except Exception as e:
            self.log_message(f"페이지 요청 오류: {str(e)}")
            if callback:
                callback([])
    
    def get_page_with_requests(self, page_num=1):
        """requests 라이브러리로 페이지 요청"""
        try:
            params = {'page': page_num}
            self.log_message(f"requests로 URL 요청 시작")
            
            response = requests.get(
                self.list_url,
                params=params,
                headers=self.headers,
                timeout=10,
                verify=False  # SSL 검증 우회 (개발용)
            )
            response.raise_for_status()
            
            # 인코딩 처리
            try:
                response.encoding = 'euc-kr'
                return response.text
            except UnicodeDecodeError:
                self.log_message("인코딩 오류, 기본값 사용")
                return response.content.decode('utf-8', errors='replace')
                
        except Exception as e:
            self.log_message(f"페이지 가져오기 오류: {str(e)}")
            return ""
    
    def parse_with_bs4(self, html_content):
        """BeautifulSoup으로 HTML 파싱"""
        try:
            # html.parser 사용
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 메인 테이블 찾기
            table = soup.find('table', {'class': 'type_1'})
            if not table:
                self.log_message("테이블을 찾을 수 없습니다")
                return []
            
            reports = []
            rows = table.find_all('tr')[2:]  # 헤더 및 빈 행 제외
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) != 6:  # 구분선 또는 빈 행
                    continue
                
                # 분할선 제외
                if 'colspan' in cells[0].attrs and cells[0]['colspan'] == '6':
                    continue
                
                try:
                    # 종목 정보
                    stock_link = cells[0].find('a')
                    if not stock_link:
                        continue
                    
                    stock_name = stock_link.text.strip()
                    
                    # 리포트 제목
                    report_link = cells[1].find('a')
                    report_title = report_link.text.strip() if report_link else "제목 없음"
                    
                    # 증권사
                    securities_firm = cells[2].text.strip()
                    
                    # 날짜
                    date_str = cells[4].text.strip()
                    
                    # 정보 저장
                    report = {
                        'stock_name': stock_name,
                        'title': report_title,
                        'securities_firm': securities_firm,
                        'date': date_str
                    }
                    reports.append(report)
                except Exception as e:
                    self.log_message(f"행 파싱 오류: {str(e)}")
                    continue
            
            return reports
        except Exception as e:
            self.log_message(f"BS4 파싱 오류: {str(e)}")
            return []
    
    def parse_with_regex(self, html_content):
        """정규식으로 HTML 파싱"""
        reports = []
        
        try:
            # 테이블 찾기
            table_pattern = r'<table class="type_1".*?>(.*?)</table>'
            table_match = re.search(table_pattern, html_content, re.DOTALL)
            
            if not table_match:
                self.log_message("테이블을 찾을 수 없습니다")
                return []
            
            table_content = table_match.group(1)
            
            # TR 추출
            tr_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(tr_pattern, table_content, re.DOTALL)
            
            # 처음 2개 행은 헤더이므로 건너뜀
            rows = rows[2:] if len(rows) > 2 else []
            
            for row in rows:
                try:
                    # TD 추출
                    td_pattern = r'<td[^>]*>(.*?)</td>'
                    cells = re.findall(td_pattern, row, re.DOTALL)
                    
                    if len(cells) != 6:
                        continue  # 올바른 형식의 행이 아님
                    
                    # 종목명 추출
                    stock_pattern = r'<a[^>]*>(.*?)</a>'
                    stock_match = re.search(stock_pattern, cells[0], re.DOTALL)
                    if not stock_match:
                        continue
                    
                    stock_name = stock_match.group(1).strip()
                    
                    # 제목 추출
                    title_match = re.search(stock_pattern, cells[1], re.DOTALL)
                    report_title = title_match.group(1).strip() if title_match else "제목 없음"
                    
                    # 증권사 추출
                    securities_firm = re.sub(r'<[^>]*>', '', cells[2]).strip()
                    
                    # 날짜 추출
                    date_str = re.sub(r'<[^>]*>', '', cells[4]).strip()
                    
                    # 정보 저장
                    report = {
                        'stock_name': stock_name,
                        'title': report_title,
                        'securities_firm': securities_firm,
                        'date': date_str
                    }
                    reports.append(report)
                except Exception as e:
                    self.log_message(f"행 파싱 오류: {str(e)}")
                    continue
            
            return reports
        except Exception as e:
            self.log_message(f"정규식 파싱 오류: {str(e)}")
            return []
    
    def parse_report_list(self, html_content):
        """환경에 따라 적절한 파싱 방법 선택"""
        if USE_BS4:
            self.log_message("BeautifulSoup으로 파싱 시도")
            return self.parse_with_bs4(html_content)
        else:
            self.log_message("정규식으로 파싱 시도")
            return self.parse_with_regex(html_content)
    
    def get_today_reports(self, callback=None):
        """오늘의 리포트 가져오기 - 환경에 맞는 방법 사용"""
        try:
            self.log_message("네이버 금융에 연결 중...")
            
            if is_android or not USE_REQUESTS:
                # 안드로이드에서는 Kivy의 UrlRequest 사용
                self.log_message("Kivy UrlRequest 사용")
                self.get_page_with_kivy(1, callback=callback)
            else:
                # 데스크톱에서는 requests 사용 가능하면 사용
                self.log_message("requests 라이브러리 사용")
                html = self.get_page_with_requests(1)
                
                if not html:
                    self.log_message("데이터를 가져오지 못했습니다")
                    if callback:
                        callback([])
                    return []
                    
                self.log_message("리포트 목록 파싱 중...")
                reports = self.parse_report_list(html)
                
                if reports:
                    self.log_message(f"총 {len(reports)}개의 리포트를 찾았습니다")
                else:
                    self.log_message("리포트를 찾지 못했습니다")
                    
                if callback:
                    callback(reports)
                    
                return reports
        except Exception as e:
            self.log_message(f"오류 발생: {str(e)}")
            if callback:
                callback([])
            return []


class NaverFinanceUI(BoxLayout):
    """네이버 금융 UI"""
    def __init__(self, **kwargs):
        super(NaverFinanceUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # 안드로이드에서 권한 요청
        if is_android:
            try:
                request_permissions([Permission.INTERNET])
            except:
                pass
        
        # 스크래퍼 생성
        self.scraper = SimpleNaverScraper(callback=self.update_log)
        self.reports = []
        
        # 타이틀
        self.add_widget(Label(
            text='네이버 금융 리포트 스크래퍼',
            size_hint_y=None,
            height=dp(50),
            font_size='20sp'
        ))
        
        # 환경 정보
        env_info = "실행 환경: "
        if is_android:
            env_info += "안드로이드"
        else:
            env_info += "데스크톱"
            
        env_info += f" | requests: {'사용 가능' if USE_REQUESTS else '사용 불가'}"
        env_info += f" | BeautifulSoup: {'사용 가능' if USE_BS4 else '사용 불가'}"
        
        self.add_widget(Label(
            text=env_info,
            size_hint_y=None,
            height=dp(30),
            font_size='12sp'
        ))
        
        # 로그 영역
        log_label = Label(text='실행 로그:', halign='left', size_hint_y=None, height=dp(30))
        self.add_widget(log_label)
        
        log_scroll = ScrollView(size_hint_y=0.6)
        self.log_text = Label(
            text='앱이 시작되었습니다',
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        self.log_text.bind(width=lambda *x: self.log_text.setter('text_size')(self.log_text, (self.log_text.width, None)))
        self.log_text.bind(texture_size=self.log_text.setter('size'))
        log_scroll.add_widget(self.log_text)
        self.add_widget(log_scroll)
        
        # 검색 버튼
        button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        self.fetch_button = Button(text='오늘의 리포트 가져오기')
        self.fetch_button.bind(on_release=self.fetch_reports)
        button_layout.add_widget(self.fetch_button)
        
        self.add_widget(button_layout)
        
        # 결과 영역
        self.results_label = Label(
            text='검색 결과가 여기에 표시됩니다',
            size_hint_y=None,
            height=dp(40)
        )
        self.add_widget(self.results_label)
        
        # 결과 스크롤 영역
        self.results_scroll = ScrollView(size_hint_y=0.4)
        self.results_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.results_box.bind(minimum_height=self.results_box.setter('height'))
        self.results_scroll.add_widget(self.results_box)
        self.add_widget(self.results_scroll)
    
    def update_log(self, message):
        """로그 메시지를 UI에 업데이트"""
        def update_log_ui(dt):
            current_text = self.log_text.text
            if len(current_text) > 2000:  # 로그 크기 제한
                current_text = current_text[-1500:]
            self.log_text.text = f"{current_text}\n{message}"
        Clock.schedule_once(update_log_ui, 0)
    
    def fetch_reports(self, instance):
        """리포트 가져오기"""
        self.fetch_button.disabled = True
        self.update_log("리포트 가져오기 시작...")
        
        # 결과 영역 초기화
        self.results_box.clear_widgets()
        
        # 비동기 콜백
        def handle_reports(reports):
            self.reports = reports
            Clock.schedule_once(lambda dt: self.display_results(), 0)
            Clock.schedule_once(lambda dt: self.enable_button(), 0)
        
        # 네트워크 요청 시작
        self.scraper.get_today_reports(callback=handle_reports)
    
    def enable_button(self):
        """버튼 활성화"""
        self.fetch_button.disabled = False
    
    def display_results(self):
        """결과 표시"""
        if not self.reports:
            self.results_label.text = "검색 결과가 없습니다"
            return
            
        self.results_label.text = f"총 {len(self.reports)}개의 리포트"
        
        # 결과 영역 업데이트
        self.results_box.clear_widgets()
        
        for report in self.reports:
            # 리포트 정보 라벨
            text = f"[b]{report['stock_name']}[/b] - {report['title']}\n"
            text += f"{report['securities_firm']} | {report['date']}"
            
            item = Label(
                text=text,
                markup=True,
                size_hint_y=None,
                height=dp(60),
                text_size=(Window.width - dp(20), None),
                halign='left',
                valign='middle'
            )
            self.results_box.add_widget(item)


class SimpleNaverFinanceApp(App):
    """네이버 금융 앱"""
    def __init__(self, **kwargs):
        super(SimpleNaverFinanceApp, self).__init__(**kwargs)
        # 글로벌 예외 핸들러 추가
        import sys
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.global_exception_handler
    
    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """글로벌 예외 처리"""
        error_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"치명적 오류: {error_text}")
        
        # 팝업으로 오류 표시
        def show_error_popup(dt):
            content = BoxLayout(orientation='vertical', padding=10)
            content.add_widget(Label(
                text='오류 발생',
                font_size='18sp',
                size_hint_y=None,
                height=dp(40)
            ))
            content.add_widget(Label(
                text=str(exc_value),
                font_size='14sp',
                halign='left',
                valign='top',
                text_size=(Window.width - dp(40), None)
            ))
            popup = Popup(
                title='오류',
                content=content,
                size_hint=(0.9, 0.5)
            )
            popup.open()
        
        # UI 스레드에서 팝업 표시
        if hasattr(self, 'root') and self.root:
            Clock.schedule_once(show_error_popup, 0)
        
        # 원래 예외 핸들러 호출
        self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def build(self):
        try:
            return NaverFinanceUI()
        except Exception as e:
            # 오류 화면
            error_layout = BoxLayout(orientation='vertical', padding=10)
            error_layout.add_widget(Label(
                text='앱 초기화 오류',
                font_size='18sp'
            ))
            error_layout.add_widget(Label(
                text=str(e),
                font_size='14sp'
            ))
            return error_layout


if __name__ == '__main__':
    try:
        SimpleNaverFinanceApp().run()
    except Exception as e:
        print(f"치명적 오류: {str(e)}")
        print(traceback.format_exc())
