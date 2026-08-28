"""
여러 페이지에서 공통으로 쓰는 함수 모음
"""

import re
import streamlit as st
import yfinance as yf
import pandas as pd
import os
from deep_translator import GoogleTranslator

# 회사명 -> 야후파이낸스 티커 매핑 (자주 조회되는 코스피/코스닥 종목 위주)
# 목록에 없는 종목은 페이지에서 티커를 직접 입력하면 됩니다.
KR_TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "POSCO홀딩스": "005490.KS",
    "LG화학": "051910.KS",
    "삼성SDI": "006400.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "현대모비스": "012330.KS",
    "삼성물산": "028260.KS",
    "한화솔루션": "009830.KS",
    "SK이노베이션": "096770.KS",
    "두산에너빌리티": "034020.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "카카오뱅크": "323410.KS",
    "LG전자": "066570.KS",
    "삼성생명": "032830.KS",
    "하나금융지주": "086790.KS",
    "한국전력": "015760.KS",
    "현대건설": "000720.KS",
    "롯데케미칼": "011170.KS",
    "S-Oil": "010950.KS",
    "우리금융지주": "316140.KS",
    "KT&G": "033780.KS",
    "아모레퍼시픽": "090430.KS",
    "넷마블": "251270.KS",
    "HMM": "011200.KS",
    "대한항공": "003490.KS",
    "LG디스플레이": "034220.KS",
    "SK텔레콤": "017670.KS",
    "KT": "030200.KS",
    "하이브": "352820.KS",
    "엔씨소프트": "036570.KS",
    "크래프톤": "259960.KS",
    "펄어비스": "263750.KQ",
    "카카오게임즈": "293490.KQ",
    "알테오젠": "196170.KQ",
    "에스엠": "041510.KQ",
    "카카오페이": "377300.KS",
    # ETF (연금저축/IRP 계좌에서 많이 담는 종목 위주)
    "KODEX 200": "069500.KS",
    "TIGER 200": "102110.KS",
    "KODEX 코스닥150": "229200.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "KODEX 미국나스닥100": "379810.KS",
    "TIGER 미국S&P500": "360750.KS",
    "KODEX 미국S&P500": "379800.KS",
    "KODEX 골드선물(H)": "132030.KS",
    "TIGER 차이나전기차SOLACTIVE": "371460.KS",
    "KODEX 2차전지산업": "305720.KS",
    "TIGER TOP10": "292150.KS",
    "TIGER코리아TOP10": "292150.KS",  # "TIGER TOP10"의 정식 명칭
    "KBSTAR 200": "148020.KS",
    "KODEX 반도체": "091160.KS",
    "KODEX 단기채권": "153130.KS",
    "KODEX 종합채권(AA-이상)액티브": "273130.KS",
    "TIGER 미국배당다우존스": "458730.KS",
    "TIGER Fn반도체TOP10": "396500.KS",
    "KODEX AI전력핵심설비": "487240.KS",
    "TIGER 미국필라델피아반도체나스닥": "381180.KS",
    "TIGER K방산&우주": "463250.KS",
    "KIWOOM 미국양자컴퓨팅": "498270.KS",
    "KODEX 자동차": "091180.KS",
    "KODEX 미국AI전력핵심인프라": "487230.KS",

    # --- KRX300 구성종목 (2026-08 기준, 사용자 제공 공식 자료) ---
    # 뒤에 나오는 항목이 앞선 항목보다 우선 적용되므로,
    # 이 목록이 위에서 수기로 등록한 종목과 겹치면 최신 KRX300 기준 코드로 덮어씁니다.
    "하이트진로": "000080.KS",
    "유한양행": "000100.KS",
    "CJ대한통운": "000120.KS",
    "두산": "000150.KS",
    "DL": "000210.KS",
    "한국앤컴퍼니": "000240.KS",
    "삼천당제약": "000250.KS",
    "기아": "000270.KS",
    "SK하이닉스": "000660.KS",
    "영풍": "000670.KS",
    "현대건설": "000720.KS",
    "삼성화재": "000810.KS",
    "한화": "000880.KS",
    "DB하이텍": "000990.KS",
    "CJ": "001040.KS",
    "세아베스틸지주": "001430.KS",
    "대한전선": "001440.KS",
    "현대해상": "001450.KS",
    "신영증권": "001720.KS",
    "오리온홀딩스": "001800.KS",
    "KCC": "002380.KS",
    "아모레퍼시픽홀딩스": "002790.KS",
    "삼양식품": "003230.KS",
    "하림지주": "003380.KS",
    "대한항공": "003490.KS",
    "한화투자증권": "003530.KS",
    "대신증권": "003540.KS",
    "LG": "003550.KS",
    "포스코퓨처엠": "003670.KS",
    "코리안리": "003690.KS",
    "롯데정밀화학": "004000.KS",
    "현대제철": "004020.KS",
    "신세계": "004170.KS",
    "농심": "004370.KS",
    "롯데지주": "004990.KS",
    "코스모신소재": "005070.KS",
    "동진쎄미켐": "005290.KS",
    "롯데칠성": "005300.KS",
    "현대차": "005380.KS",
    "POSCO홀딩스": "005490.KS",
    "DB손해보험": "005830.KS",
    "에스엘": "005850.KS",
    "삼성전자": "005930.KS",
    "NH투자증권": "005940.KS",
    "동원산업": "006040.KS",
    "SK디스커버리": "006120.KS",
    "LS": "006260.KS",
    "녹십자": "006280.KS",
    "GS건설": "006360.KS",
    "삼성SDI": "006400.KS",
    "미래에셋증권": "006800.KS",
    "GS리테일": "007070.KS",
    "DN오토모티브": "007340.KS",
    "네이처셀": "007390.KS",
    "이수페타시스": "007660.KS",
    "코리아써키트": "007810.KS",
    "호텔신라": "008770.KS",
    "한미사이언스": "008930.KS",
    "삼성전기": "009150.KS",
    "한올바이오파마": "009420.KS",
    "HD한국조선해양": "009540.KS",
    "한화솔루션": "009830.KS",
    "영원무역홀딩스": "009970.KS",
    "OCI홀딩스": "010060.KS",
    "LS ELECTRIC": "010120.KS",
    "고려아연": "010130.KS",
    "삼성중공업": "010140.KS",
    "S-Oil": "010950.KS",
    "LG이노텍": "011070.KS",
    "롯데케미칼": "011170.KS",
    "HMM": "011200.KS",
    "현대위아": "011210.KS",
    "금호석유화학": "011780.KS",
    "SKC": "011790.KS",
    "현대모비스": "012330.KS",
    "한화에어로스페이스": "012450.KS",
    "삼성에피스홀딩스": "0126Z0.KS",
    "한솔케미칼": "014680.KS",
    "한국전력": "015760.KS",
    "삼성증권": "016360.KS",
    "현대사료": "016790.KS",
    "SK텔레콤": "017670.KS",
    "현대엘리베이터": "017800.KS",
    "한국카본": "017960.KS",
    "삼성에스디에스": "018260.KS",
    "SK가스": "018670.KS",
    "한온시스템": "018880.KS",
    "롯데에너지머티리얼즈": "020150.KS",
    "코웨이": "021240.KS",
    "포스코DX": "022100.KS",
    "롯데쇼핑": "023530.KS",
    "기업은행": "024110.KS",
    "삼성E&A": "028050.KS",
    "삼성물산": "028260.KS",
    "HLB": "028300.KS",
    "팬오션": "028670.KS",
    "삼성카드": "029780.KS",
    "제일기획": "030000.KS",
    "KT": "030200.KS",
    "원익홀딩스": "030530.KS",
    "서울보증보험": "031210.KS",
    "피에스케이홀딩스": "031980.KS",
    "롯데관광개발": "032350.KS",
    "LG유플러스": "032640.KS",
    "우리기술": "032820.KS",
    "삼성생명": "032830.KS",
    "KT&G": "033780.KS",
    "두산에너빌리티": "034020.KS",
    "LG디스플레이": "034220.KS",
    "파라다이스": "034230.KS",
    "SK": "034730.KS",
    "강원랜드": "035250.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "CJ ENM": "035760.KS",
    "JYP Ent.": "035900.KS",
    "한국가스공사": "036460.KS",
    "SFA반도체": "036540.KS",
    "NC": "036570.KS",
    "솔브레인홀딩스": "036830.KS",
    "주성엔지니어링": "036930.KS",
    "삼표시멘트": "038500.KS",
    "이오테크닉스": "039030.KS",
    "오스코텍": "039200.KS",
    "키움증권": "039490.KS",
    "에스엠": "041510.KS",
    "한화오션": "042660.KS",
    "한미반도체": "042700.KS",
    "성호전자": "043260.KS",
    "대우건설": "047040.KS",
    "포스코인터내셔널": "047050.KS",
    "한국항공우주": "047810.KS",
    "한전KPS": "051600.KS",
    "LG생활건강": "051900.KS",
    "LG화학": "051910.KS",
    "한전기술": "052690.KS",
    "신한지주": "055550.KS",
    "리노공업": "058470.KS",
    "에스피지": "058610.KS",
    "LS마린솔루션": "060370.KS",
    "산일전기": "062040.KS",
    "현대로템": "064350.KS",
    "LG씨엔에스": "064400.KS",
    "티씨케이": "064760.KS",
    "신성델타테크": "065350.KS",
    "LG전자": "066570.KS",
    "엘앤에프": "066970.KS",
    "하나마이크론": "067310.KS",
    "셀트리온": "068270.KS",
    "셀트리온제약": "068760.KS",
    "대웅제약": "069620.KS",
    "현대백화점": "069960.KS",
    "한국금융지주": "071050.KS",
    "HD현대마린엔진": "071970.KS",
    "금호타이어": "073240.KS",
    "세진중공업": "075580.KS",
    "STX엔진": "077970.KS",
    "대주전자재료": "078600.KS",
    "GS": "078930.KS",
    "LIG디펜스앤에어로스페이스": "079550.KS",
    "제주반도체": "080220.KS",
    "미스토홀딩스": "081660.KS",
    "젬백스": "082270.KS",
    "한화엔진": "082740.KS",
    "비츠로셀": "082920.KS",
    "비에이치아이": "083650.KS",
    "유진테크": "084370.KS",
    "미래에셋생명": "085620.KS",
    "차바이오텍": "085660.KS",
    "현대글로비스": "086280.KS",
    "에코프로": "086520.KS",
    "하나금융지주": "086790.KS",
    "펩트론": "087010.KS",
    "한화생명": "088350.KS",
    "테크윙": "089030.KS",
    "아모레퍼시픽": "090430.KS",
    "휴림로봇": "090710.KS",
    "ISC": "095340.KS",
    "테스": "095610.KS",
    "씨젠": "096530.KS",
    "SK이노베이션": "096770.KS",
    "HJ중공업": "097230.KS",
    "CJ제일제당": "097950.KS",
    "고영": "098460.KS",
    "쎄트렉아이": "099320.KS",
    "SK오션플랜트": "100090.KS",
    "미래에셋벤처투자": "100790.KS",
    "에스앤에스텍": "101490.KS",
    "풍산": "103140.KS",
    "일진전기": "103590.KS",
    "KB금융": "105560.KS",
    "로보티즈": "108490.KS",
    "영원무역": "111770.KS",
    "씨에스윈드": "112610.KS",
    "큐리언트": "115180.KS",
    "코오롱인더": "120110.KS",
    "와이지엔터테인먼트": "122870.KS",
    "한미약품": "128940.KS",
    "두산테스나": "131970.KS",
    "피엔티": "137400.KS",
    "메리츠금융지주": "138040.KS",
    "BNK금융지주": "138930.KS",
    "iM금융지주": "139130.KS",
    "이마트": "139480.KS",
    "파크시스템스": "140860.KS",
    "리가켐바이오": "141080.KS",
    "휴젤": "145020.KS",
    "한국타이어앤테크놀로지": "161390.KS",
    "필옵틱스": "161580.KS",
    "한국콜마": "161890.KS",
    "하나머티리얼즈": "166090.KS",
    "앱클론": "174900.KS",
    "JB금융지주": "175330.KS",
    "서진시스템": "178320.KS",
    "한진칼": "180640.KS",
    "코미코": "183300.KS",
    "코스맥스": "192820.KS",
    "HK이노엔": "195940.KS",
    "알테오젠": "196170.KS",
    "HL만도": "204320.KS",
    "삼성바이오로직스": "207940.KS",
    "덕산네오룩스": "213420.KS",
    "클래시스": "214150.KS",
    "케어젠": "214370.KS",
    "파마리서치": "214450.KS",
    "RFHIC": "218410.KS",
    "심텍": "222800.KS",
    "올릭스": "226950.KS",
    "LS에코에너지": "229640.KS",
    "와이씨": "232140.KS",
    "에스티팜": "237690.KS",
    "원익IPS": "240810.KS",
    "두산밥캣": "241560.KS",
    "에코프로비엠": "247540.KS",
    "일동제약": "249420.KS",
    "넷마블": "251270.KS",
    "스튜디오드래곤": "253450.KS",
    "실리콘투": "257720.KS",
    "크래프톤": "259960.KS",
    "펄어비스": "263750.KS",
    "HD현대": "267250.KS",
    "HD현대일렉트릭": "267260.KS",
    "HD건설기계": "267270.KS",
    "오리온": "271560.KS",
    "한화시스템": "272210.KS",
    "레인보우로보틱스": "277810.KS",
    "에이피알": "278470.KS",
    "레이크머티리얼즈": "281740.KS",
    "BGF리테일": "282330.KS",
    "SK케미칼": "285130.KS",
    "엘앤씨바이오": "290650.KS",
    "카카오게임즈": "293490.KS",
    "효성티앤씨": "298020.KS",
    "효성중공업": "298040.KS",
    "HS효성첨단소재": "298050.KS",
    "에이비엘바이오": "298380.KS",
    "SK바이오사이언스": "302440.KS",
    "현대오토에버": "307950.KS",
    "보로노이": "310210.KS",
    "우리금융지주": "316140.KS",
    "현대무벡스": "319400.KS",
    "피에스케이": "319660.KS",
    "HD현대에너지솔루션": "322000.KS",
    "태성": "323280.KS",
    "카카오뱅크": "323410.KS",
    "SK바이오팜": "326030.KS",
    "루닛": "328130.KS",
    "HD현대중공업": "329180.KS",
    "두산퓨얼셀": "336260.KS",
    "스피어": "347700.KS",
    "디앤디파마텍": "347850.KS",
    "엔켐": "348370.KS",
    "하이브": "352820.KS",
    "대덕전자": "353200.KS",
    "솔브레인": "357780.KS",
    "지아이이노베이션": "358570.KS",
    "LG에너지솔루션": "373220.KS",
    "DL이앤씨": "375500.KS",
    "카카오페이": "377300.KS",
    "F&F": "383220.KS",
    "유일로보틱스": "388720.KS",
    "에이프릴바이오": "397030.KS",
    "SK스퀘어": "402340.KS",
    "HPSP": "403870.KS",
    "LS머트리얼즈": "417200.KS",
    "삼현": "437730.KS",
    "대한조선": "439260.KS",
    "HD현대마린솔루션": "443060.KS",
    "큐리옥스바이오시스템즈": "445680.KS",
    "에코프로머티": "450080.KS",
    "두산로보틱스": "454910.KS",
    "이수스페셜티케미컬": "457190.KS",
    "씨어스": "458870.KS",
    "SK이터닉스": "475150.KS",
    "달바글로벌": "483650.KS",
    "한화비전": "489790.KS",
    "로킷헬스케어": "376900.KQ",
    "지투지바이오": "456160.KQ",
    "클로봇": "466100.KQ",
    "오름테라퓨틱": "475830.KQ",

    # --- 테마종목 메뉴용 추가 종목 ---
    "가온전선": "000500.KS",
    "신일전자": "002700.KS",
    "천보": "278280.KQ",
    "나노신소재": "121600.KQ",
    "솔루스첨단소재": "336370.KS",
    "쏠리드": "050890.KQ",
    "케이엠더블유": "032500.KQ",
    "제주은행": "006220.KS",
    "한국기업평가": "034950.KQ",
    "NICE디앤비": "130580.KQ",
    "뉴로메카": "348340.KQ",
    "삼양사": "145990.KS",
    "노바렉스": "194700.KQ",
    "콜마비앤에이치": "200130.KQ",
    "코스메카코리아": "241710.KQ",
    "신대양제지": "016590.KS",
    "디어유": "376300.KQ",
    "삼화콘덴서": "001820.KQ",
    "대한광통신": "010170.KS",
    # 별칭 (다른 이름으로도 검색되도록)
    "현대자동차": "005380.KS",  # = 현대차
    "LIG넥스원": "079550.KS",  # = LIG디펜스앤에어로스페이스 (개명)
    "코리아서키트": "007810.KS",  # = 코리아써키트
}

# 테마종목 메뉴: 한국 섹터별 관심종목 (회사명 기준, KR_TICKERS로 티커 변환)
KR_SECTOR_STOCKS = {
    "반도체": ["SK하이닉스", "삼성전자", "SK스퀘어", "한미반도체", "DB하이텍", "원익IPS", "유진테크", "테스",
             "한솔케미칼", "LG이노텍", "삼성전기", "LG전자", "삼화콘덴서", "대한광통신", "코리아서키트"],
    "전력설비/원자력": ["두산에너빌리티", "LS ELECTRIC", "HD현대일렉트릭", "효성중공업", "한국전력", "LS",
                   "대한전선", "가온전선", "신일전자", "일진전기", "한전기술", "우리기술"],
    "제약/바이오": ["삼성바이오로직스", "SK바이오사이언스", "셀트리온", "휴젤", "한미약품", "알테오젠"],
    "자동차": ["현대자동차", "기아", "현대모비스", "HL만도", "현대위아", "한국타이어앤테크놀로지"],
    "2차전지": ["삼성SDI", "LG에너지솔루션", "SK이노베이션", "에코프로", "에코프로비엠", "POSCO홀딩스",
              "RFHIC", "나노신소재", "포스코퓨처엠", "엘앤에프", "천보", "롯데에너지머티리얼즈",
              "솔루스첨단소재", "SKC"],
    "통신": ["SK텔레콤", "KT", "LG유플러스", "쏠리드", "케이엠더블유"],
    "금융": ["신한지주", "KB금융", "하나금융지주", "우리금융지주", "기업은행", "제주은행", "BNK금융지주",
            "JB금융지주", "카카오뱅크", "카카오페이", "NAVER", "삼성카드", "NICE디앤비", "한국기업평가"],
    "증권": ["미래에셋증권", "키움증권", "삼성증권", "한국금융지주", "NH투자증권"],
    "로봇": ["레인보우로보틱스", "두산로보틱스", "로보티즈", "에스피지", "뉴로메카", "두산"],
    "우주방산/원자력": ["한화에어로스페이스", "한국항공우주", "LIG넥스원", "한화시스템", "한화"],
    "식료건강": ["삼양식품", "농심", "오리온", "CJ제일제당", "삼양사", "노바렉스", "한국콜마",
              "콜마비앤에이치", "코스맥스", "코스메카코리아"],
    "기타": ["신대양제지", "디어유", "포스코인터내셔널"],
}

# 테마종목 메뉴: 미국 섹터별 관심종목 (티커 기준)
US_SECTOR_STOCKS = {
    "AI플랫폼/서비스": ["GOOG", "MSFT", "AMZN", "AAPL", "META", "DELL", "PLTR", "ORCL", "ANET", "IREN", "APP", "FLEX"],
    "반도체": ["NVDA", "TSM", "AVGO", "SKHY", "MU", "SNDK", "STX", "WDC", "ARM", "AMD", "INTC", "QCOM",
             "ASML", "NXPI", "SNPS", "LRCX", "TXN", "MRVL", "AMAT", "KLAC", "TER", "MPWR", "AAOI", "CRDO",
             "CLS", "ON"],
    "금융/증권/보험": ["JPM", "MS", "BNY", "STT", "AMP", "V", "BAC", "PYPL", "HOOD", "IBKR", "GLD", "SLV",
                   "TLT", "XLF", "ACGL"],
    "자율주행/우주/UAM/에너지": ["TSLA", "TPR", "SPCX", "HWM", "JOBY", "UBER", "RKLB", "LMND", "ABNB", "SMR",
                          "XOM", "MPC", "VLO", "PSX", "DVN", "CVX", "COP", "EOG", "KMI", "TRGP"],
    "전력인프라/광통신/신재생": ["CEG", "NEE", "ETR", "VST", "CAT", "GE", "PWR", "FIX", "JBL", "VRT", "ETN",
                          "NVTS", "GEV", "COHR", "LITE", "CIEN", "CSCO", "GLW", "CMI", "FSLR", "BE",
                          "PLUG", "FCEL"],
    "바이오/헬스케어": ["LLY", "ISRG", "TEM", "MCK", "CRSP", "PTGX", "SYK", "MRNA", "TMO", "UNH", "AFL",
                   "COR", "PFE", "DXCM", "BIIB", "JNJ", "ILMN", "ABBV", "NVS", "INMD"],
    "소비/부동산/스포츠/엔터": ["NFLX", "DIS", "COST", "SPG", "ROST", "LULU", "MELI", "WMT", "CASY", "CMG",
                        "KO", "PEP", "DPZ", "MCD", "OTLY", "EQIX", "O", "PLD", "CTVA", "TKO"],
    "경영지원/장비렌탈/건설/엔지니어링": ["URI", "IRM", "EME"],
    "철강/재료/원자재/농업": ["STLD", "CF"],
    "교통/수송/여행/숙박/철도": ["CSX", "UBER", "ABNB", "MAR", "TRV", "HLT", "WAB"],
    "보안/양자": ["CRWD", "PANW", "ZS", "CRDO", "FTNT", "NTAP", "DDOG", "QUBT", "RGTI", "QBTS", "IONQ"],
}


# 띄어쓰기를 무시하고 검색하기 위한 보조 딕셔너리 (예: "TIGER반도체TOP10" == "TIGER Fn반도체TOP10")
_KR_TICKERS_NO_SPACE = {name.replace(" ", ""): code for name, code in KR_TICKERS.items()}

def resolve_kr_ticker(user_input):
    """회사명 또는 종목코드를 받아 야후파이낸스 티커로 변환하는 함수 (띄어쓰기 무시)"""
    text = user_input.strip()

    if text in KR_TICKERS:
        return KR_TICKERS[text]

    if text.replace(" ", "") in _KR_TICKERS_NO_SPACE:
        return _KR_TICKERS_NO_SPACE[text.replace(" ", "")]

    if text.upper().endswith((".KS", ".KQ")):
        return text.upper()

    if text.isdigit() and len(text) == 6:
        return f"{text}.KS"  # 코스피로 우선 시도, 안되면 페이지에서 .KQ로 다시 입력 안내

    return None


def resolve_ticker(user_input):
    """회사명/종목코드/티커 등 무엇을 입력하든 야후파이낸스 티커로 변환하는 함수 (미국 종목도 그대로 통과, 띄어쓰기 무시)"""
    text = str(user_input).strip()

    if text in KR_TICKERS:
        return KR_TICKERS[text]

    if text.replace(" ", "") in _KR_TICKERS_NO_SPACE:
        return _KR_TICKERS_NO_SPACE[text.replace(" ", "")]

    if text.upper().endswith((".KS", ".KQ")):
        return text.upper()

    if text.isdigit() and len(text) == 6:
        return f"{text}.KS"

    return text.upper()  # AAPL, NVDA 등 미국 티커는 그대로 사용


def is_korean_ticker(ticker):
    """.KS(코스피), .KQ(코스닥)로 끝나면 원화 종목으로 판단"""
    return ticker.upper().endswith((".KS", ".KQ"))


def get_price(ticker):
    """종목의 최근 종가를 받아오는 함수"""
    hist = yf.Ticker(ticker).history(period="1d")
    if hist.empty:
        return None
    return hist["Close"].iloc[-1]


def get_price_with_day_change(ticker):
    """종목의 현재가와 '오늘(전일 대비) 변동률(%)'을 함께 구하는 함수.
    장이 아직 안 끝나서 최근 캔들이 빈 값(NaN)으로 들어오는 경우가 있어(특히 한국 종목),
    여유있게 5일치를 받아 빈 값을 제거한 뒤 마지막 두 값만 사용한다."""
    hist = yf.Ticker(ticker).history(period="5d")
    if hist.empty:
        return None, None

    closes = hist["Close"].dropna()
    if closes.empty:
        return None, None

    price = closes.iloc[-1]

    if len(closes) >= 2 and closes.iloc[-2]:
        prev_close = closes.iloc[-2]
        day_change_pct = (price - prev_close) / prev_close * 100
    else:
        day_change_pct = None

    return price, day_change_pct


def get_usdkrw_rate():
    """달러->원화 환율을 받아오는 함수"""
    hist = yf.Ticker("KRW=X").history(period="1d")
    if hist.empty:
        return None
    return hist["Close"].iloc[-1]


# 미국 대형/중형주 스캔용 유니버스 (S&P500 전체는 아니고, 자주 거래되는 주요 종목 위주)
US_STOCK_UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY",
    "AVGO", "JPM", "V", "UNH", "XOM", "MA", "HD", "PG", "COST", "JNJ",
    "MRK", "ABBV", "CVX", "WMT", "BAC", "KO", "PEP", "ADBE", "CRM", "NFLX",
    "AMD", "TMO", "MCD", "CSCO", "ABT", "ACN", "LIN", "DIS", "WFC", "DHR",
    "TXN", "PM", "INTU", "VZ", "CMCSA", "IBM", "GE", "CAT", "NOW", "AMGN",
    "UNP", "HON", "LOW", "SPGI", "BA", "RTX", "NEE", "ELV", "PFE", "INTC",
    "AMAT", "GS", "DE", "ISRG", "BLK", "SYK", "BKNG", "MDT", "LMT", "ADP",
    "T", "SBUX", "GILD", "MMC", "PLD", "TJX", "VRTX", "MO", "CB", "C",
    "ADI", "SCHW", "PANW", "ETN", "REGN", "CI", "SO", "ZTS", "BSX", "MU",
    "LRCX", "KLAC", "SNPS", "CDNS", "ORCL", "QCOM", "UBER", "PYPL", "SHOP", "PLTR",
    "COIN", "SOFI", "RIVN", "LCID",
]


def get_kr_code_to_name_map():
    """티커코드 -> 회사명 역매핑 (KR_TICKERS에 이름이 여러 개인 코드는 먼저 등록된 이름을 사용)"""
    code_to_name = {}
    for name, code in KR_TICKERS.items():
        if code not in code_to_name:
            code_to_name[code] = name
    return code_to_name


@st.cache_data(ttl=1800, show_spinner=False)
def scan_momentum(tickers, ascending=False, top_n=20, period="3mo"):
    """여러 종목을 한 번에 받아서 RSI 기준 상위/하위 N개를 찾는 함수.
    ascending=False면 RSI가 높은(급등/모멘텀 강한) 순, True면 낮은(눌림목/과매도) 순."""
    unique_tickers = list(dict.fromkeys(tickers))  # 중복 제거, 순서 유지
    data = yf.download(unique_tickers, period=period, interval="1d", group_by="ticker", threads=True, progress=False)

    rows = []
    for ticker in unique_tickers:
        try:
            close = data[ticker]["Close"].dropna()
        except (KeyError, TypeError):
            continue
        if len(close) < 15:
            continue

        rsi_series = calculate_rsi(close)
        rsi_value = rsi_series.iloc[-1]
        if pd.isna(rsi_value):
            continue

        price = close.iloc[-1]
        prev_close = close.iloc[-2]
        day_change_pct = (price - prev_close) / prev_close * 100 if prev_close else None

        rows.append({
            "티커": ticker,
            "현재가": price,
            "RSI(14)": rsi_value,
            "오늘 변동률(%)": day_change_pct,
        })

    result_df = pd.DataFrame(rows)
    if result_df.empty:
        return result_df
    return result_df.sort_values("RSI(14)", ascending=ascending).head(top_n).reset_index(drop=True)


def calculate_period_returns(close_series):
    """5일/1개월/6개월/1년/5년 변동률(%)을 계산하는 함수. 데이터가 부족한 기간은 None."""
    close_series = close_series.dropna()
    if close_series.empty:
        return {"5일": None, "1개월": None, "6개월": None, "1년": None, "5년": None}

    current = close_series.iloc[-1]
    periods = {"5일": 5, "1개월": 21, "6개월": 126, "1년": 252, "5년": 1260}
    result = {}
    for label, days in periods.items():
        # 보유 데이터가 원하는 기간보다 짧으면(신규상장 등) 가장 오래된 데이터를 기준으로 계산
        idx = min(days, len(close_series) - 1)
        if idx <= 0:
            result[label] = None
            continue
        past = close_series.iloc[-idx - 1]
        result[label] = (current - past) / past * 100 if past else None
    return result


def has_korean(text):
    """문자열에 한글이 포함되어 있는지 확인하는 함수"""
    return bool(re.search(r"[가-힣]", text or ""))


@st.cache_data(ttl=86400, show_spinner=False)
def translate_to_korean(text):
    """영어 등 외국어 뉴스 제목을 한글로 번역하는 함수. 실패하면 None을 돌려줌 (원문만 표시)"""
    if not text or has_korean(text):
        return None
    try:
        return GoogleTranslator(source="auto", target="ko").translate(text)
    except Exception:
        return None


def calculate_rsi(close_series, period=14):
    """RSI(상대강도지수)를 계산하는 함수. 70 이상이면 과열(인기 많음), 30 이하면 과매도로 흔히 해석함"""
    delta = close_series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_naver_worldstock_url(ticker_symbol, exchange):
    """미국 종목의 네이버 해외증시 페이지 URL을 만드는 함수 (나스닥은 .O 접미사, 뉴욕은 접미사 없음)"""
    nasdaq_exchanges = {"NMS", "NGM", "NCM", "NASDAQ"}
    suffix = ".O" if exchange in nasdaq_exchanges else ""
    return f"https://m.stock.naver.com/worldstock/stock/{ticker_symbol}{suffix}/total"


def _clean_text_value(value):
    if pd.isna(value):
        return ""
    text = str(value)
    if text.endswith(".0") and text[:-2].lstrip("-").isdigit():
        text = text[:-2]  # 계좌번호 같은 숫자형 텍스트가 709390542901.0 처럼 되는 것 방지
    return text


def coerce_text_columns(df, columns):
    """숫자처럼 보이거나 비어있는 값 때문에 열이 숫자형(float)으로 잘못 인식되는 문제를 막기 위해 문자열로 강제 변환하는 함수"""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(_clean_text_value)
    return df


def load_portfolio(file_path):
    """보유종목 CSV를 불러오는 함수. 미국/한국/연금저축 등 파일별로 따로 관리합니다."""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if "순서" not in df.columns:
            df["순서"] = range(1, len(df) + 1)
        df = coerce_text_columns(df, ["티커", "구분", "금융기관"])
        return df.sort_values("순서").reset_index(drop=True)
    return pd.DataFrame({"순서": [], "티커": [], "보유수량": [], "매입가": []})


def save_portfolio(df, file_path):
    df.to_csv(file_path, index=False)


def add_live_price_columns(df):
    """입력 표에 '현재가'/'오늘 변동률(%)' 열을 매입가 바로 뒤에 추가한 표시 전용 DataFrame을 돌려주는 함수.
    이 결과는 화면에 보여주기만 하고, 저장할 때는 이 두 열을 빼고 저장해야 함."""
    prices = []
    changes = []

    for _, row in df.iterrows():
        ticker_input = str(row.get("티커", "")).strip()
        if not ticker_input:
            prices.append(None)
            changes.append(None)
            continue

        ticker = resolve_ticker(ticker_input)
        price, change = get_price_with_day_change(ticker)

        if price is None and ticker.endswith(".KS"):
            alt_ticker = ticker.replace(".KS", ".KQ")
            price, change = get_price_with_day_change(alt_ticker)

        prices.append(price)
        changes.append(change)

    display_df = df.copy()
    display_df["현재가"] = prices
    display_df["오늘 변동률(%)"] = changes

    columns = list(df.columns)
    insert_at = columns.index("매입가") + 1 if "매입가" in columns else len(columns)
    new_order = columns[:insert_at] + ["현재가", "오늘 변동률(%)"] + columns[insert_at:]
    return display_df[new_order]


def get_portfolio_total_krw(file_path, rate):
    """해당 보유종목 파일의 총 평가액(원화 환산)만 빠르게 구하는 함수"""
    df = load_portfolio(file_path)
    _, total_krw, _ = compute_portfolio_rows(df, rate)
    return total_krw


def get_portfolio_native_currency_totals_from_df(df):
    """포트폴리오 DataFrame에서 통화별 '원래 금액' 합계를 구하는 함수 (환율 변환 없이 달러는 달러대로, 원화는 원화대로)"""
    totals = {"KRW": 0.0, "USD": 0.0}

    for _, row in df.iterrows():
        ticker_input = str(row["티커"]).strip()
        qty = row["보유수량"]
        if not ticker_input or qty in (None, 0) or pd.isna(qty):
            continue

        ticker = resolve_ticker(ticker_input)
        price = get_price(ticker)

        if price is None and ticker.endswith(".KS"):
            alt_ticker = ticker.replace(".KS", ".KQ")
            alt_price = get_price(alt_ticker)
            if alt_price is not None:
                ticker, price = alt_ticker, alt_price

        if price is None:
            continue

        value = price * qty
        currency = "KRW" if is_korean_ticker(ticker) else "USD"
        totals[currency] += value

    return totals


def get_portfolio_native_currency_totals(file_path, rate):
    """포트폴리오 파일에서 통화별 '원래 금액' 합계를 구하는 함수 (다른 페이지에서 저장된 값을 가져올 때 사용)"""
    df = load_portfolio(file_path)
    return get_portfolio_native_currency_totals_from_df(df)


def get_deposit_native_currency_totals_from_df(df):
    """예수금 DataFrame에서 통화별 '원래 금액' 합계를 구하는 함수 (환율 변환 없이 달러는 달러대로, 원화는 원화대로)"""
    totals = {"KRW": 0.0, "USD": 0.0}

    for _, row in df.iterrows():
        currency = str(row["통화"]).strip().upper()
        amount = row["예수금"]
        if amount in (None, 0) or pd.isna(amount):
            continue
        if currency in totals:
            totals[currency] += amount

    return totals


def get_deposit_native_currency_totals(file_path):
    """예수금 파일에서 통화별 '원래 금액' 합계를 구하는 함수 (다른 페이지에서 저장된 값을 가져올 때 사용)"""
    df = load_deposits(file_path)
    return get_deposit_native_currency_totals_from_df(df)


def style_negative_returns(rows_df):
    """수익률/오늘 변동률이 음수(-)면 빨간색 글씨로 표시하는 스타일을 입힌 DataFrame(Styler)을 돌려주는 함수"""
    target_cols = [col for col in ["수익률", "오늘 변동률(%)"] if col in rows_df.columns]
    if not target_cols:
        return rows_df

    def _color(value):
        if isinstance(value, str) and value.startswith("-"):
            return "color: red"
        return ""

    return rows_df.style.map(_color, subset=target_cols)


def get_portfolio_group_totals(file_path, rate, group_col):
    """보유종목 파일을 group_col 값별로 나눠서 각각의 총 평가액(원화 환산)을 구하는 함수"""
    df = load_portfolio(file_path)
    if group_col not in df.columns:
        return {}
    totals = {}
    for group_value, group_df in df.groupby(group_col):
        _, total_krw, _ = compute_portfolio_rows(group_df, rate)
        totals[group_value] = total_krw
    return totals


def compute_portfolio_rows(portfolio_df, rate):
    """보유 주식 각 종목의 평가액/원화환산액/수익률을 계산해서 리스트로 돌려주는 함수.
    반환값은 (rows, total_krw, total_profit). total_profit은 각 종목의 통화 그대로 합산한 평가손익 합계이므로,
    한 포트폴리오 안에 여러 통화가 섞여 있으면 의미가 없어짐 (지금은 미국/한국/연금저축이 각각 단일 통화라 안전)."""
    rows = []
    total_krw = 0.0
    total_profit = 0.0
    has_cost = "매입가" in portfolio_df.columns

    for _, row in portfolio_df.iterrows():
        ticker_input = str(row["티커"]).strip()
        qty = row["보유수량"]
        if not ticker_input or qty in (None, 0):
            continue

        ticker = resolve_ticker(ticker_input)  # 회사명("삼성전자")이나 종목코드("005930")도 인식
        price, day_change_pct = get_price_with_day_change(ticker)

        # 코스피(.KS)로 시도했는데 못 찾으면 코스닥(.KQ)으로 재시도
        if price is None and ticker.endswith(".KS"):
            alt_ticker = ticker.replace(".KS", ".KQ")
            alt_price, alt_day_change_pct = get_price_with_day_change(alt_ticker)
            if alt_price is not None:
                ticker, price, day_change_pct = alt_ticker, alt_price, alt_day_change_pct

        if price is None:
            rows.append({"티커": ticker_input, "보유수량": f"{qty:,.0f}", "현재가": "조회 실패", "평가액": "-", "원화환산액": "-"})
            continue

        value = price * qty
        krw_currency = is_korean_ticker(ticker)

        if krw_currency:
            krw_value = value
        elif rate is not None:
            krw_value = value * rate
        else:
            krw_value = None

        if krw_value is not None:
            total_krw += krw_value

        result = {
            "티커": ticker_input,
            "종목코드": ticker,
            "보유수량": f"{qty:,.0f}",
            "통화": "KRW" if krw_currency else "USD",
        }

        amount_fmt = "{:,.0f}" if krw_currency else "{:,.2f}"  # 원화는 소수점 없이, 달러는 소수점 유지

        # 매입가 (수량 옆에 바로 이어서 표시)
        cost_price = row["매입가"] if has_cost else None
        has_valid_cost = has_cost and cost_price not in (None, 0) and not pd.isna(cost_price)
        result["매입가"] = amount_fmt.format(cost_price) if has_valid_cost else "-"

        # 현재가 + 오늘(전일 대비) 변동률
        result["현재가"] = amount_fmt.format(price)
        result["오늘 변동률(%)"] = f"{day_change_pct:+.2f}%" if day_change_pct is not None else "-"

        # 매입가 대비 평가손익/수익률
        if has_valid_cost:
            cost_basis = cost_price * qty
            profit = value - cost_basis
            return_pct = profit / cost_basis * 100
            total_profit += profit
            result["평가손익"] = amount_fmt.format(profit)
            result["수익률"] = f"{return_pct:+.2f}%"
        elif has_cost:
            result["평가손익"] = "-"
            result["수익률"] = "-"

        result["평가액"] = amount_fmt.format(value)
        result["원화환산액"] = f"{krw_value:,.0f}" if krw_value is not None else "-"

        rows.append(result)

    return rows, total_krw, total_profit


def compute_position_weights(portfolio_df, rate, other_portfolio_total_krw=0.0):
    """포트폴리오의 종목별 투자비중/평가비중/전체비중(%)을 계산하는 함수.
    compute_portfolio_rows와 완전히 동일한 순서로 행을 건너뛰므로, 반환된 리스트를 rows 리스트와 그대로 나란히 붙일 수 있음.
    같은 종목(티커 입력값 기준)이 여러 줄에 걸쳐 있으면(예: 계좌 여러 개) 합산한 뒤 각 줄에 동일한 비중을 부여함.
    - 투자비중: 이 종목 매입원가 합 / 이 포트폴리오 전체 매입원가 합
    - 평가비중: 이 종목 평가액(원화환산) 합 / 이 포트폴리오 전체 평가액(원화환산) 합
    - 전체비중: 이 종목 평가액(원화환산) 합 / (이 포트폴리오 전체 평가액 + other_portfolio_total_krw)
    """
    has_cost = "매입가" in portfolio_df.columns
    raw_rows = []

    for _, row in portfolio_df.iterrows():
        ticker_input = str(row["티커"]).strip()
        qty = row["보유수량"]
        if not ticker_input or qty in (None, 0):
            continue

        ticker = resolve_ticker(ticker_input)
        price = get_price(ticker)
        if price is None and ticker.endswith(".KS"):
            alt_ticker = ticker.replace(".KS", ".KQ")
            alt_price = get_price(alt_ticker)
            if alt_price is not None:
                ticker, price = alt_ticker, alt_price

        if price is None:
            raw_rows.append({"key": ticker_input, "cost_krw": None, "value_krw": None})
            continue

        value = price * qty
        krw_currency = is_korean_ticker(ticker)
        value_krw = value if krw_currency else (value * rate if rate is not None else None)

        cost_krw = None
        if has_cost:
            cost_price = row["매입가"]
            if cost_price not in (None, 0) and not pd.isna(cost_price):
                cost_basis = cost_price * qty
                cost_krw = cost_basis if krw_currency else (cost_basis * rate if rate is not None else None)

        raw_rows.append({"key": ticker_input, "cost_krw": cost_krw, "value_krw": value_krw})

    total_cost = sum(r["cost_krw"] for r in raw_rows if r["cost_krw"] is not None)
    total_value = sum(r["value_krw"] for r in raw_rows if r["value_krw"] is not None)
    combined_total_value = total_value + other_portfolio_total_krw

    combined_cost = {}
    combined_value = {}
    for r in raw_rows:
        if r["cost_krw"] is not None:
            combined_cost[r["key"]] = combined_cost.get(r["key"], 0.0) + r["cost_krw"]
        if r["value_krw"] is not None:
            combined_value[r["key"]] = combined_value.get(r["key"], 0.0) + r["value_krw"]

    results = []
    for r in raw_rows:
        invest_pct = (combined_cost[r["key"]] / total_cost * 100) if total_cost and r["cost_krw"] is not None else None
        eval_pct = (combined_value[r["key"]] / total_value * 100) if total_value and r["value_krw"] is not None else None
        overall_pct = (
            combined_value[r["key"]] / combined_total_value * 100
            if combined_total_value and r["value_krw"] is not None
            else None
        )
        results.append({
            "투자비중": f"{invest_pct:.2f}%" if invest_pct is not None else "-",
            "평가비중": f"{eval_pct:.2f}%" if eval_pct is not None else "-",
            "전체비중": f"{overall_pct:.2f}%" if overall_pct is not None else "-",
        })

    return results


def load_deposits(file_path):
    """예수금(계좌별 현금) CSV를 불러오는 함수"""
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if "순서" not in df.columns:
            df["순서"] = range(1, len(df) + 1)
        df = coerce_text_columns(df, ["증권회사", "계좌번호", "통화"])
        return df.sort_values("순서").reset_index(drop=True)
    return pd.DataFrame({"순서": [], "증권회사": [], "계좌번호": [], "통화": [], "예수금": []})


def save_deposits(df, file_path):
    df.to_csv(file_path, index=False)


def compute_deposit_rows(deposits_df, rate):
    """계좌별 예수금의 원화환산액을 계산해서 리스트로 돌려주는 함수"""
    rows = []
    total_krw = 0.0

    for _, row in deposits_df.iterrows():
        broker = str(row["증권회사"]).strip()
        account_no = str(row["계좌번호"]).strip()
        currency = str(row["통화"]).strip().upper()
        amount = row["예수금"]
        if not broker or amount in (None, 0) or pd.isna(amount):
            continue

        if currency == "KRW":
            krw_value = amount
        elif rate is not None:
            krw_value = amount * rate
        else:
            krw_value = None

        if krw_value is not None:
            total_krw += krw_value

        amount_fmt = "{:,.0f}" if currency == "KRW" else "{:,.2f}"
        rows.append({
            "증권회사": broker,
            "계좌번호": account_no,
            "통화": currency,
            "예수금": amount_fmt.format(amount),
            "원화환산액": f"{krw_value:,.0f}" if krw_value is not None else "-",
        })

    return rows, total_krw


def get_deposit_total_krw(file_path, rate):
    """예수금 파일의 총액(원화 환산)만 빠르게 구하는 함수"""
    df = load_deposits(file_path)
    _, total_krw = compute_deposit_rows(df, rate)
    return total_krw
