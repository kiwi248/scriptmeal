"""
WeatherRecipeAgent
──────────────────
특정 음식명 없이 조건·상황 기반으로 레시피를 요청할 때 처리합니다.

흐름:
  1. 기상청 초단기실황 API로 현재 기온·날씨 조회
  2. 현재 날짜·시간·월 정보 결합
  3. 시스템 프롬프트 동적 생성
  4. LLM 호출 → 제철 재료 + 날씨 맞춤 다이어트 레시피 생성
"""

import os
import math
import requests
from datetime import datetime, timedelta
from openai import OpenAI

KMA_API_KEY = os.environ.get("KMA_API_KEY", "")
DEFAULT_LAT = 37.5665   # 서울 위도
DEFAULT_LON = 126.9780  # 서울 경도


class WeatherRecipeAgent:
    def __init__(self, client: OpenAI, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON):
        self.client = client
        self.lat = lat
        self.lon = lon

    def run(self, user_query: str, chat_history: list[dict]) -> str:
        temp, weather = self._fetch_weather()
        system_prompt = self._build_prompt(temp, weather)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *chat_history[-6:],
                {"role": "user", "content": user_query},
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content or "레시피를 불러오는 데 실패했습니다."

    @staticmethod
    def _latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
        """위경도 → 기상청 격자(nx, ny) 변환 (Lambert Conformal Conic)"""
        RE, GRID = 6371.00877, 5.0
        SLAT1, SLAT2 = 30.0, 60.0
        OLON, OLAT = 126.0, 38.0
        XO, YO = 43, 136
        D = math.pi / 180.0
        re = RE / GRID
        sn = math.log(
            math.cos(SLAT1 * D) / math.cos(SLAT2 * D)
        ) / math.log(
            math.tan(math.pi * 0.25 + SLAT2 * D * 0.5) /
            math.tan(math.pi * 0.25 + SLAT1 * D * 0.5)
        )
        sf = math.tan(math.pi * 0.25 + SLAT1 * D * 0.5) ** sn * math.cos(SLAT1 * D) / sn
        ro = re * sf / math.tan(math.pi * 0.25 + OLAT * D * 0.5) ** sn
        ra = re * sf / math.tan(math.pi * 0.25 + lat * D * 0.5) ** sn
        theta = lon * D - OLON * D
        if theta > math.pi:
            theta -= 2 * math.pi
        if theta < -math.pi:
            theta += 2 * math.pi
        nx = int(ra * math.sin(theta * sn) + XO + 0.5)
        ny = int(ro - ra * math.cos(theta * sn) + YO + 0.5)
        return nx, ny

    def _fetch_weather(self) -> tuple[float, str]:
        """기상청 초단기실황 API 호출 → (기온, 날씨문자열) 반환"""
        now = datetime.now()
        if now.minute < 10:
            now -= timedelta(hours=1)

        nx, ny = self._latlon_to_grid(self.lat, self.lon)

        try:
            res = requests.get(
                "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst",
                params={
                    "serviceKey": KMA_API_KEY,
                    "numOfRows": 10, "pageNo": 1, "dataType": "JSON",
                    "base_date": now.strftime("%Y%m%d"),
                    "base_time": now.strftime("%H00"),
                    "nx": nx, "ny": ny,
                },
                timeout=10,
            ).json()

            obs = {
                item["category"]: item["obsrValue"]
                for item in res["response"]["body"]["items"]["item"]
            }
            temp = float(obs.get("T1H", 20))
            pty = obs.get("PTY", "0")
            weather = {
                "0": "맑음", "1": "비", "2": "비/눈", "3": "눈",
                "5": "빗방울", "6": "빗방울/눈", "7": "눈날림",
            }.get(pty, "맑음")

        except Exception as e:
            print(f"[WeatherRecipeAgent] 날씨 API 오류: {e} → 기본값 사용")
            temp, weather = 20.0, "맑음"

        return temp, weather

    @staticmethod
    def _build_prompt(temp: float, weather: str) -> str:
        now = datetime.now()
        return f"""지금은 {now.strftime('%Y년 %m월 %d일 %H:%M')}이고
현재 날씨는 {weather}, 기온은 {temp}°C입니다.

위 상황을 반영해서 다이어트에 좋은 메뉴를 추천하고 간단한 레시피를 알려주세요.
- {now.month}월 대한민국 제철 재료 활용
- 날씨·기온에 맞게 (비/눈이면 따뜻한 국물 요리, 30°C 이상이면 시원한 음식)
- 현재 시간대에 적합한 식사량
- 칼로리 포함
- 레시피는 단계별로 상세하게"""
