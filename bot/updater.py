import discord
import holidays
from datetime import datetime
import pytz

try:
    from .utils import setup_logging
except ImportError:
    from utils import setup_logging

# 로깅 설정
logger = setup_logging("discord_updater")

# 채널 설정
CHANNELS = {
    "SEOUL": {
        "id": 1384147639293055036,
        "tz": "Asia/Seoul",
        "emoji": "🇰🇷",
        "name": "서울",
    },
    "HCMC": {
        "id": 1384147698747445401,
        "tz": "Asia/Ho_Chi_Minh",
        "emoji": "🇻🇳",
        "name": "호치민",
    },
}

KR_HOLIDAYS = holidays.KR()
VN_HOLIDAYS = holidays.VN()

# 한국 공휴일별 이모지 매핑
KR_HOLIDAY_EMOJIS = {
    # 국경일/기념일 - 국기 사용
    "현충일": "🇰🇷",  # Memorial Day
    "광복절": "🇰🇷",  # Liberation Day
    "삼일절": "🇰🇷",  # Independence Movement Day
    "제헌절": "🇰🇷",  # Constitution Day
    "개천절": "🇰🇷",  # National Foundation Day
    "한글날": "🇰🇷",  # Hangeul Day
    # 설날 관련 - 복주머니
    "설날": "🧧",  # Seollal (Lunar New Year)
    "설날 전날": "🧧",
    "설날 다음날": "🧧",
    "설날 대체 휴일": "🧧",
    # 신정 관련 - 파티/축하
    "신정": "🎉",  # New Year's Day
    "신정연휴": "🎉",
    # 특별한 날들
    "어린이날": "🎈",  # Children's Day
    "부처님오신날": "🙏",  # Buddha's Birthday
    "추석": "🌕",  # Chuseok (Korean Thanksgiving)
    "추석 전날": "🌕",
    "추석 다음날": "🌕",
    "추석 대체 휴일": "🌕",
    "기독탄신일": "🎄",  # Christmas Day
    # 선거/정치 관련
    "국회의원 선거일": "🗳️",  # Election Day
    "대통령선거": "🗳️",
    "지방선거": "🗳️",
}

# 베트남 공휴일별 이모지 매핑
VN_HOLIDAY_EMOJIS = {
    # 신정
    "Tết Dương lịch": "🎉",  # New Year's Day
    # 구정/설날 (Tết Nguyên Đán)
    "29 Tết": "🧧",
    "Giao thừa Tết Nguyên Đán": "🧧",
    "Tết Nguyên Đán": "🧧",
    "Mùng hai Tết Nguyên Đán": "🧧",
    "Mùng ba Tết Nguyên Đán": "🧧",
    "Mùng bốn Tết Nguyên Đán": "🧧",
    "Mùng năm Tết Nguyên Đán": "🧧",
    # 국가 기념일
    "Ngày Giỗ Tổ Hùng Vương": "🇻🇳",  # Hung Kings' Commemoration Day
    "Ngày Chiến thắng": "🇻🇳",  # Victory Day
    "Quốc khánh": "🇻🇳",  # National Day
    # 노동절
    "Ngày Quốc tế Lao động": "👷",  # International Workers' Day
}

# 딕셔너리에 없는 공휴일을 위한 기본 이모지
DEFAULT_HOLIDAY_EMOJI = "🗓️"

# 긴 공휴일명 축약 매핑
HOLIDAY_SHORT_NAMES = {
    # 베트남 설날 관련 축약
    "Giao thừa Tết Nguyên Đán": "Tết Eve",
    "Mùng hai Tết Nguyên Đán": "Tết Day2",
    "Mùng ba Tết Nguyên Đán": "Tết Day3",
    "Mùng bốn Tết Nguyên Đán": "Tết Day4",
    "Mùng năm Tết Nguyên Đán": "Tết Day5",
    "Ngày Giỗ Tổ Hùng Vương": "Hùng Vương",
    "Ngày Quốc tế Lao động": "Labor Day",
    # 한국 공휴일 축약
    "국회의원 선거일": "선거일",
    "설날 대체 휴일": "설날 대체",
    "추석 대체 휴일": "추석 대체",
}


def is_off_day(date, country):
    """주말 또는 공휴일 여부 확인"""
    weekday = date.weekday()

    if weekday >= 5:  # 토요일(5), 일요일(6)
        return True

    if country == "SEOUL":
        return date in KR_HOLIDAYS
    elif country == "HCMC":
        return date in VN_HOLIDAYS

    return False


def get_holiday_info(date, country):
    """공휴일 정보 반환 (공휴일명, 이모지)"""
    weekday = date.weekday()

    # 주말 처리
    if weekday == 5:  # 토요일
        return "토요일", "🌤️"
    elif weekday == 6:  # 일요일
        return "일요일", "☀️"

    # 공휴일 처리
    if country == "SEOUL":
        if date in KR_HOLIDAYS:
            holiday_name = KR_HOLIDAYS[date]
            # 축약된 이름이 있으면 사용, 없으면 원래 이름 사용
            display_name = HOLIDAY_SHORT_NAMES.get(holiday_name, holiday_name)
            emoji = KR_HOLIDAY_EMOJIS.get(holiday_name, DEFAULT_HOLIDAY_EMOJI)
            return display_name, emoji
    elif country == "HCMC":
        if date in VN_HOLIDAYS:
            holiday_name = VN_HOLIDAYS[date]
            # 축약된 이름이 있으면 사용, 없으면 원래 이름 사용
            display_name = HOLIDAY_SHORT_NAMES.get(holiday_name, holiday_name)
            emoji = VN_HOLIDAY_EMOJIS.get(holiday_name, DEFAULT_HOLIDAY_EMOJI)
            return display_name, emoji

    return None, None


def get_availability_status(now, country):
    """연락 가능 상태에 따른 이모지 반환 (평일 전용)"""
    hour = now.hour
    minute = now.minute

    if country == "SEOUL":
        # 한국 시간 기준
        if (
            (9 < hour < 11)
            or (hour == 9 and minute >= 30)
            or (hour == 11 and minute < 30)
        ):  # 9:30-11:29 업무
            return "💼"  # 연락 가능
        elif (hour == 11 and minute >= 30) or (
            hour == 12 and minute < 30
        ):  # 11:30-12:29 점심
            return "🍜"  # 점심 시간 (연락 불가)
        elif (
            (12 < hour < 18)
            or (hour == 12 and minute >= 30)
            or (hour == 18 and minute < 30)
        ):  # 12:30-18:29 업무
            return "💼"  # 연락 가능
        elif hour > 18 or (hour == 18 and minute >= 30):  # 18:30 이후 퇴근
            return "🏠"  # 퇴근 후 (연락 불가)
        else:
            return "🏠"  # 출근 전 (연락 불가)
    else:  # HCMC
        # 베트남 시간 기준
        if (8 < hour < 12) or (hour == 8 and minute >= 30):  # 8:30-11:59 업무
            return "💼"  # 연락 가능
        elif hour == 12 or (hour == 13 and minute < 30):  # 12:00-13:29 점심
            return "🍜"  # 점심 시간 (연락 불가)
        elif (
            (13 < hour < 17)
            or (hour == 13 and minute >= 30)
            or (hour == 17 and minute < 30)
        ):  # 13:30-17:29 업무
            return "💼"  # 연락 가능
        elif hour > 17 or (hour == 17 and minute >= 30):  # 17:30 이후 퇴근
            return "🏠"  # 퇴근 후 (연락 불가)
        else:
            return "🏠"  # 출근 전 (연락 불가)


async def update_channel_names(client_instance):
    """모든 채널의 이름을 현재 시간으로 업데이트"""
    updated_count = 0

    for name, info in CHANNELS.items():
        try:
            channel = client_instance.get_channel(info["id"])
            if not channel:
                logger.warning(
                    f"[WARNING] 채널을 찾을 수 없습니다 (ID: {info['id']}, {info['name']})"
                )
                continue

            # 길드 채널인지 확인 (DM 채널 제외)
            if not isinstance(
                channel,
                (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel),
            ):
                logger.warning(
                    f"[WARNING] 지원하지 않는 채널 타입입니다 (ID: {info['id']}, {info['name']})"
                )
                continue

            # 현재 시간 계산
            tz = pytz.timezone(info["tz"])
            now = datetime.now(tz)

            # 휴일/주말 체크
            holiday_name, holiday_emoji = get_holiday_info(now.date(), name)
            if holiday_name:
                # 휴일/주말인 경우 - 공휴일명과 해당 이모지 사용
                time_str = holiday_name
                status_emoji = holiday_emoji
                logger.info(
                    f"[HOLIDAY] {info['name']} - {holiday_name} ({holiday_emoji})"
                )
            else:
                # 평일인 경우 - 시간과 업무 상태 이모지 사용
                time_str = now.strftime("%H：%M")
                status_emoji = get_availability_status(now, name)

            new_name = f"{info['emoji']}∥{time_str} {status_emoji}"

            # 채널 이름이 이미 같다면 스킵
            if channel.name == new_name:
                logger.debug(
                    f"[SKIP] {info['name']} 채널 이름이 이미 최신입니다: {new_name}"
                )
                continue

            # 채널 이름 업데이트
            await channel.edit(name=new_name)
            logger.info(
                f"[SUCCESS] {info['name']} 채널 업데이트: {channel.name} -> {new_name}"
            )
            updated_count += 1

        except discord.Forbidden:
            logger.error(
                f"[FORBIDDEN] {info['name']} 채널 수정 권한이 없습니다 (ID: {info['id']})"
            )
        except discord.NotFound:
            logger.error(
                f"[NOTFOUND] {info['name']} 채널을 찾을 수 없습니다 (ID: {info['id']})"
            )
        except Exception as e:
            logger.error(f"[ERROR] {info['name']} 채널 업데이트 실패: {e}")

    if updated_count == 0:
        logger.info("[INFO] 업데이트가 필요한 채널이 없습니다")
    else:
        logger.info(f"[COMPLETE] 총 {updated_count}개 채널이 업데이트되었습니다")

    return updated_count
