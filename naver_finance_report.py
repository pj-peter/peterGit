import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re
from datetime import datetime, timedelta
from tqdm import tqdm

class NaverFinanceScraper:
    def __init__(self, download_path='reports'):
        self.base_url = 'https://finance.naver.com'
        self.list_url = f'{self.base_url}/research/company_list.naver'
        self.download_path = download_path
        self.cookies = {
            'NACT': '1',
            'NNB': 'MRZ252EC5DHWO',
            'ASID': 'b6dc330e00000195871ef27f0000004c',
            'NAC': 'ovZiBgg1nJUR',
            'summary_item_type': 'recent',
            'page_uid': 'i+v25wqVOswssgonOu8ssssstvl-349206',
            'SRT30': '1742972092',
            'SRT5': '1742972092',
            'JSESSIONID': '04613B02D6737FDCA6B209248802A346',
            'BUC': 'FNWyEgzum5tVWZxHNNjboKAaQZAksB18OxP8WLIIrrE=',
        }
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'priority': 'u=0, i',
            'referer': 'https://finance.naver.com/research/company_list.naver',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        }
        
        # 다운로드 폴더 생성
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
    
    def get_page(self, page_num=1):
        """특정 페이지의 종목분석 리포트 목록을 가져옵니다."""
        params = {'page': page_num}
        response = requests.get(
            self.list_url,
            params=params,
            cookies=self.cookies,
            headers=self.headers
        )
        response.raise_for_status()  # HTTP 에러 체크
        response.encoding = 'euc-kr'  # 네이버 금융은 euc-kr 인코딩 사용
        return response.text
    
    def parse_report_list(self, html_content):
        """HTML에서 종목분석 리포트 목록을 파싱합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 메인 테이블 찾기
        table = soup.find('table', {'class': 'type_1'})
        if not table:
            return []
        
        reports = []
        # 테이블 행 찾기 (첫 번째 행은 헤더, 두 번째 행은 빈 행)
        rows = table.find_all('tr')[2:]
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) != 6:  # 구분선이나 빈 행 스킵
                continue
            
            # 스타일 속성이 있는지 확인하여 컬럼 구분선 등을 제외
            if 'colspan' in cells[0].attrs and cells[0]['colspan'] == '6':
                continue
            
            # 데이터 추출
            try:
                stock_link = cells[0].find('a')
                if not stock_link:
                    continue
                
                stock_code = re.search(r'code=(\d+)', stock_link['href']).group(1)
                stock_name = stock_link.text.strip()
                
                report_link = cells[1].find('a')
                report_title = report_link.text.strip() if report_link else ""
                # 올바른 URL 형식으로 구성
                if report_link:
                    href = report_link['href']
                    # href가 /로 시작하는지 확인
                    if not href.startswith('/'):
                        href = f"/research/{href}"
                    report_url = f"{self.base_url}{href}"
                else:
                    report_url = ""
                
                securities_firm = cells[2].text.strip()
                
                # PDF 링크
                pdf_link = cells[3].find('a')
                pdf_url = pdf_link['href'] if pdf_link else ""
                
                # 날짜와 조회수
                date_str = cells[4].text.strip()
                views = cells[5].text.strip()
                
                # 데이터 저장
                report = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'title': report_title,
                    'report_url': report_url,
                    'securities_firm': securities_firm,
                    'pdf_url': pdf_url,
                    'date': date_str,
                    'views': views
                }
                reports.append(report)
            except Exception as e:
                print(f"행 파싱 중 오류 발생: {e}")
                continue
        
        return reports
    
    def get_total_pages(self, html_content):
        """전체 페이지 수를 추출합니다."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 마지막 페이지 링크 찾기
        last_page_link = soup.select('table.Nnavi td.pgRR a')
        if last_page_link:
            href = last_page_link[0]['href']
            match = re.search(r'page=(\d+)', href)
            if match:
                return int(match.group(1))
        
        return 1  # 기본값
    
    def download_pdf(self, pdf_url, filename):
        """PDF 파일을 다운로드합니다."""
        try:
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            file_path = os.path.join(self.download_path, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"PDF 다운로드 중 오류 발생: {e}")
            return False
    
    def get_report_content(self, report_url):
        """리포트 상세 페이지의 내용을 가져옵니다."""
        try:
            response = requests.get(
                report_url,
                cookies=self.cookies,
                headers=self.headers
            )
            response.raise_for_status()
            response.encoding = 'euc-kr'  # 네이버 금융은 euc-kr 인코딩 사용
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 본문 내용 추출 (네이버 금융 리포트 페이지 구조에 맞게 조정)
            content_div = soup.select_one('.view_cnt')
            if content_div:
                # HTML 태그 제거하고 텍스트만 추출
                content_text = content_div.get_text(strip=True)
                return content_text
            else:
                return "본문 내용을 찾을 수 없습니다."
        except Exception as e:
            print(f"리포트 내용 가져오기 실패: {e}")
            return f"오류 발생: {str(e)}"
            
    def scrape_reports(self, start_page=1, end_page=None, download_pdfs=False, date_range=1, target_stock_name=None, content_filter=None):
        """지정된 페이지 범위의 리포트를 스크랩합니다.
        
        Args:
            start_page (int): 시작 페이지 번호
            end_page (int, optional): 종료 페이지 번호. None이면 전체 페이지 스크랩
            download_pdfs (bool): PDF 파일 다운로드 여부
            date_range (int): 조회할 일 수 (기본값: 1, 오늘만)
            target_stock_name (str): 대상 종목명 (None이면 모든 종목 처리)
            content_filter (str): 본문 내용 필터 (None이면 필터링 없음)
        """
        # 첫 페이지로 전체 페이지 수 확인
        first_page_html = self.get_page(start_page)
        total_pages = self.get_total_pages(first_page_html)
        
        if end_page is None or end_page > total_pages:
            end_page = total_pages
        
        print(f"총 {total_pages} 페이지 중 {start_page}부터 {end_page}까지 스크랩합니다.")
        
        # 조회 날짜 범위 계산
        today = datetime.now()
        target_dates = []
        
        for i in range(date_range):
            # i일 전 날짜 계산
            target_date = today - timedelta(days=i)
            # 네이버 금융 형식(YY.MM.DD)으로 변환
            date_str = target_date.strftime('%y.%m.%d')
            target_dates.append(date_str)
            
        date_range_text = "오늘" if date_range == 1 else f"오늘부터 {date_range}일치"
        print(f"{date_range_text} 리포트를 수집합니다. 대상 날짜: {', '.join(target_dates)}")
            
        if target_stock_name:
            print(f"'{target_stock_name}' 종목에 대한 리포트만 수집합니다.")
        else:
            print("모든 종목의 리포트를 수집합니다.")
            
        if content_filter:
            print(f"본문에 '{content_filter}'가 포함된 리포트만 수집합니다.")
        
        all_reports = []
        
        # 페이지별 스크랩
        for page in range(start_page, end_page + 1):
            print(f"페이지 {page}/{end_page} 처리 중...")
            if page > start_page:  # 첫 페이지는 이미 가져왔음
                page_html = self.get_page(page)
            else:
                page_html = first_page_html
            
            reports = self.parse_report_list(page_html)
            
            # 날짜 범위 필터링
            reports = [report for report in reports if report['date'] in target_dates]
            
            # 이전 페이지에서 대상 날짜가 없으면 중단 (페이지가 날짜순으로 정렬되어 있다고 가정)
            oldest_date = target_dates[-1] if target_dates else None
            if not reports and page > 1 and oldest_date and any(report['date'] < oldest_date for report in self.parse_report_list(page_html)):
                print(f"페이지 {page}에서 더 이상 대상 날짜의 리포트가 없습니다. 스크래핑을 중단합니다.")
                break
            
            # 대상 종목 필터링 (필요한 경우)
            filtered_reports = []
            for report in reports:
                # 대상 종목이 지정되었고 종목명이 일치하지 않으면 건너뜀
                if target_stock_name and report['stock_name'] != target_stock_name:
                    continue
                
                # 리포트 본문 가져오기
                #print(f"\n'{report['stock_name']}' 종목의 '{report['title']}' ({report['date']}) 리포트 내용 조회 중...")
                report_content = self.get_report_content(report['report_url'])
                report['content'] = report_content
                
                # 본문 내용 필터링 (필요한 경우)
                if content_filter and content_filter not in report_content:
                    #print(f"필터 조건 '{content_filter}'에 맞지 않아 제외됩니다.")
                    continue
                    
                if content_filter and content_filter in report_content:
                    print(f"\n'{report['stock_name']}' 종목의 '{report['title']}' ({report['date']}) 리포트 내용 조회")
                    print(f"필터 조건 '{content_filter}'가 본문에서 발견되었습니다.")
                
                filtered_reports.append(report)
                time.sleep(1)  # 상세 페이지 조회 후 대기
            
            all_reports.extend(filtered_reports)
            
            # 서버 부하 방지를 위한 대기
            time.sleep(1)
        
        # DataFrame 생성
        df = pd.DataFrame(all_reports)
        
        # PDF 다운로드 옵션
        
        if download_pdfs and not df.empty:
            print(f"\n총 {len(df)} 개의 PDF 파일을 다운로드합니다.")
            
            for i, row in tqdm(df.iterrows(), total=len(df), desc="PDF 다운로드 중"):
                if row['pdf_url']:
                    # 파일명 생성: 날짜_종목코드_증권사_제목.pdf
                    date_str = row['date'].replace('.', '')
                    filename = f"{date_str}_{row['stock_code']}_{row['securities_firm']}_{row['title']}.pdf"
                    # 파일명에 사용할 수 없는 문자 제거
                    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                    # 긴 파일명 처리
                    if len(filename) > 200:
                        filename = filename[:190] + '.pdf'
                    
                    success = self.download_pdf(row['pdf_url'], filename)
                    if not success:
                        print(f"다운로드 실패: {row['title']}")
                    
                    # 서버 부하 방지를 위한 대기
                    time.sleep(0.5)
        
        
        return df

# 사용 예시
if __name__ == "__main__":
    scraper = NaverFinanceScraper(download_path='naver_reports')
    
    # 사용자 입력 받기
    stock_input = input("종목명을 입력하세요 (0 입력 시 전체 종목 조회): ")
    content_filter = input("본문 필터링할 내용을 입력하세요 (입력하지 않으면 필터링 없음): ")
    date_range_input = input("조회할 날짜 범위를 입력하세요 (1: 오늘만, 5: 5일치 등): ")
    
    # 옵션 설정
    start_page = 1
    end_page = 10  # None으로 설정하면 모든 페이지 스크랩
    download_pdfs = True  # PDF 파일 다운로드 여부 (주석 처리됨)
    
    # 날짜 범위 설정
    try:
        date_range = int(date_range_input)
        if date_range < 1:
            date_range = 1
            print("날짜 범위는 최소 1일 이상이어야 합니다. 1일로 설정합니다.")
    except ValueError:
        date_range = 1
        print("유효한 숫자가 아닙니다. 기본값 1일로 설정합니다.")
    
    # 입력값에 따라 종목 설정
    if stock_input == "0":
        target_stock_name = None  # 전체 종목 조회
    else:
        target_stock_name = stock_input  # 특정 종목만 조회
        
    # 필터링 설정
    if not content_filter.strip():
        content_filter = None  # 필터링 없음
    
    # 스크랩 실행
    df = scraper.scrape_reports(start_page, end_page, download_pdfs, date_range, target_stock_name, content_filter)
    
    # 결과가 없는 경우 처리
    if df.empty:
        date_range_text = "오늘" if date_range == 1 else f"최근 {date_range}일간"
        
        if target_stock_name and content_filter:
            print(f"{date_range_text} 등록된 '{target_stock_name}' 종목의 리포트 중 '{content_filter}'가 포함된 리포트가 없습니다.")
        elif target_stock_name:
            print(f"{date_range_text} 등록된 '{target_stock_name}' 종목의 리포트가 없습니다.")
        elif content_filter:
            print(f"{date_range_text} 등록된 리포트 중 '{content_filter}'가 포함된 리포트가 없습니다.")
        else:
            print(f"{date_range_text} 등록된 리포트가 없습니다.")
    else:
        # 결과 저장
        today = datetime.now().strftime('%Y%m%d')
        # 파일명 생성
        filename_parts = ['naver_finance']
        if target_stock_name:
            filename_parts.append(target_stock_name)
        if content_filter:
            filter_safe = content_filter.replace(' ', '_').replace('/', '_')[:30]  # 파일명에 안전한 형식으로 변환 및 길이 제한
            filename_parts.append(f"filter_{filter_safe}")
        if date_range > 1:
            filename_parts.append(f"{date_range}days")
        filename_parts.append(f"reports_{today}")
        
        csv_filename = f"{'_'.join(filename_parts)}.csv"
            
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 결과 메시지 생성
        date_range_text = "오늘" if date_range == 1 else f"최근 {date_range}일간"
        result_msg = f"\n스크랩 완료! {date_range_text} 등록된 총 {len(df)}개의 "
        if target_stock_name:
            result_msg += f"'{target_stock_name}' 종목의 "
        if content_filter:
            result_msg += f"'{content_filter}'가 포함된 "
        result_msg += f"리포트 정보를 {csv_filename}에 저장했습니다."
        
        print(result_msg)
        
        '''
        # 첫 번째 리포트 내용 미리보기 (있는 경우)
        if len(df) > 0 and 'content' in df.columns:
            print("\n첫 번째 리포트 내용 미리보기 (첫 200자):")
            content = df.iloc[0]['content']
            print(content[:200] + "..." if len(content) > 200 else content)'
        '''