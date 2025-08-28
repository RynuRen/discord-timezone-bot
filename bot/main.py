import time
import subprocess
import sys
from datetime import datetime, timedelta
import os
import pytz

try:
    from .utils import setup_logging, check_discord_token
except ImportError:
    # 직접 실행될 때를 위한 대체 import
    from utils import setup_logging, check_discord_token

# 로깅 설정
logger = setup_logging("discord_main")


def run_bot():
    """봇을 실행하는 함수"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[TIME] 봇 실행 시작: {current_time}")

    try:
        # 환경변수 확인
        try:
            check_discord_token()
        except ValueError as e:
            logger.error(f"[ERROR] {e}")
            return False

        # 봇 실행 - 모듈로 실행
        result = subprocess.run(
            [sys.executable, "-m", "bot.bot"],
            capture_output=True,
            text=True,
            timeout=60,  # 타임아웃 증가
            cwd=os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),  # 프로젝트 루트
        )

        if result.returncode == 0:
            logger.info("[SUCCESS] 봇이 성공적으로 실행되었습니다")

            # stdout 출력 (봇의 로그)
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        logger.info(f"  [BOT] {line.strip()}")

            return True
        else:
            logger.error(f"[FAIL] 봇 실행 실패 (exit code: {result.returncode})")

            # stderr 출력
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n"):
                    if line.strip():
                        logger.error(f"  [ERROR] {line.strip()}")

            return False

    except subprocess.TimeoutExpired:
        logger.error("[TIMEOUT] 봇 실행이 타임아웃되었습니다 (60초)")
        return False
    except FileNotFoundError:
        logger.error("[ERROR] Python 인터프리터를 찾을 수 없습니다")
        return False
    except Exception as e:
        logger.error(f"[ERROR] 예상치 못한 오류 발생: {e}")
        return False


def job_wrapper():
    """스케줄 작업 래퍼 함수"""
    now = datetime.now(pytz.timezone("Asia/Seoul"))

    # 한국 시간 기준 22:00 ~ 06:59 사이에는 실행하지 않음
    if now.hour >= 22 or now.hour < 7:
        logger.info(
            f"[SKIP] 현재 시간({now.strftime('%H:%M')})이 업데이트 제외 시간이므로 건너뜁니다"
        )
        logger.info("[WAIT] 다음 실행까지 대기 중...")
        print("-" * 50)
        return

    minute = now.minute
    logger.info(f"[START] 스케줄 작업 시작 (현재 시간: {minute}분)")

    success = run_bot()

    if success:
        logger.info("[COMPLETE] 스케줄 작업 완료")
    else:
        logger.warning("[WARNING] 스케줄 작업 중 오류 발생")

    logger.info("[WAIT] 다음 실행까지 대기 중...")
    print("-" * 50)  # 구분선


def calculate_next_run_time():
    """다음 10분 단위 실행 시간을 계산"""
    now = datetime.now()
    current_minute = now.minute

    # 다음 10분 단위 계산 (0, 10, 20, 30, 40, 50)
    next_minute = ((current_minute // 10) + 1) * 10

    if next_minute >= 60:
        # 다음 시간의 0분
        next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        # 같은 시간의 다음 10분 단위
        next_run = now.replace(minute=next_minute, second=0, microsecond=0)

    return next_run


def wait_until_next_scheduled_time():
    """다음 10분 단위까지 대기"""
    next_run = calculate_next_run_time()
    now = datetime.now()
    wait_seconds = (next_run - now).total_seconds()

    logger.info(
        f"[SCHEDULE] 다음 실행 예정 시간: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"[WAIT] {wait_seconds:.0f}초 후에 실행됩니다")

    if wait_seconds > 0:
        time.sleep(wait_seconds)


def main():
    """메인 스케줄러 함수"""
    logger.info("[INIT] Discord 타임존 봇 스케줄러를 시작합니다")
    logger.info("[SCHEDULE] 정각 10분 단위로 실행됩니다 (0, 10, 20, 30, 40, 50분)")
    logger.info("[SCHEDULE] 단, 한국시간 기준 22:00~06:59 사이에는 실행되지 않습니다")
    logger.info("[SCHEDULE] 휴일/주말은 각 채널별로 개별 처리됩니다")

    # 현재 시간대 정보 출력
    current_time = datetime.now()
    logger.info(
        f"[TIMEZONE] 현재 시스템 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    logger.info(f"[TIMEZONE] 시간대: {os.getenv('TZ', 'Unknown')}")

    # 환경변수 확인
    try:
        check_discord_token()
    except ValueError as e:
        logger.error(f"[ERROR] {e}")
        logger.error("[HELP] .env 파일을 생성하거나 환경변수를 설정해주세요")
        sys.exit(1)

    # 현재 시간이 10분 단위인지 확인
    current_minute = datetime.now().minute
    if current_minute % 10 == 0:
        logger.info("[IMMEDIATE] 현재가 정각 10분 단위입니다. 즉시 실행합니다...")
        job_wrapper()
    else:
        logger.info(
            f"[WAIT] 현재 시간: {current_minute}분 - 다음 10분 단위까지 대기합니다"
        )

    # 메인 루프 - 정각 10분 단위로 실행
    try:
        while True:
            # 다음 10분 단위까지 대기
            wait_until_next_scheduled_time()

            # 정확한 시간에 실행
            job_wrapper()

    except KeyboardInterrupt:
        logger.info("[STOP] 사용자에 의해 스케줄러가 중지되었습니다")
    except Exception as e:
        logger.error(f"[ERROR] 스케줄러 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
