import subprocess
import sys
import time
from datetime import datetime
import os
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from .utils import setup_logging, check_discord_token
    from .updater import calculate_next_update_time, is_off_day
except ImportError:
    # 직접 실행될 때를 위한 대체 import
    from utils import setup_logging, check_discord_token
    from updater import calculate_next_update_time, is_off_day

# 로깅 설정
logger = setup_logging("discord_main")


def run_bot():
    """봇을 실행하는 함수"""
    start_time = time.time()
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
            timeout=30,  # 타임아웃 단축 (빠른 실패)
            cwd=os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),  # 프로젝트 루트
        )

        if result.returncode == 0:
            execution_time = time.time() - start_time
            logger.info(
                f"[SUCCESS] 봇이 성공적으로 실행되었습니다 (실행시간: {execution_time:.2f}초)"
            )

            # 성능 경고
            if execution_time > 20:
                logger.warning(
                    f"[PERFORMANCE] 실행 시간이 길어지고 있습니다: {execution_time:.2f}초"
                )
            elif execution_time > 10:
                logger.info(f"[PERFORMANCE] 실행 시간: {execution_time:.2f}초")

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
        logger.error("[TIMEOUT] 봇 실행이 타임아웃되었습니다 (30초)")
        return False
    except FileNotFoundError:
        logger.error("[ERROR] Python 인터프리터를 찾을 수 없습니다")
        return False
    except Exception as e:
        logger.error(f"[ERROR] 예상치 못한 오류 발생: {e}")
        return False


def run_bot_night_mode():
    """야간 모드용 봇 실행 함수"""
    start_time = time.time()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[NIGHT_TIME] 야간 모드 봇 실행 시작: {current_time}")

    try:
        # 환경변수 확인
        try:
            check_discord_token()
        except ValueError as e:
            logger.error(f"[ERROR] {e}")
            return False

        # 야간 모드 봇 실행 - 특별한 환경변수로 구분
        env = os.environ.copy()
        env["NIGHT_MODE"] = "true"  # 야간 모드 플래그 설정

        result = subprocess.run(
            [sys.executable, "-m", "bot.bot"],
            capture_output=True,
            text=True,
            timeout=30,  # 타임아웃 단축 (빠른 실패)
            env=env,  # 환경변수 전달
            cwd=os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),  # 프로젝트 루트
        )

        if result.returncode == 0:
            execution_time = time.time() - start_time
            logger.info(
                f"[SUCCESS] 야간 모드 봇이 성공적으로 실행되었습니다 (실행시간: {execution_time:.2f}초)"
            )

            # 성능 경고
            if execution_time > 20:
                logger.warning(
                    f"[PERFORMANCE] 야간 모드 실행 시간이 길어지고 있습니다: {execution_time:.2f}초"
                )
            elif execution_time > 10:
                logger.info(
                    f"[PERFORMANCE] 야간 모드 실행 시간: {execution_time:.2f}초"
                )

            # stdout 출력 (봇의 로그)
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        logger.info(f"  [NIGHT_BOT] {line.strip()}")

            return True
        else:
            logger.error(
                f"[FAIL] 야간 모드 봇 실행 실패 (exit code: {result.returncode})"
            )

            # stderr 출력
            if result.stderr.strip():
                for line in result.stderr.strip().split("\n"):
                    if line.strip():
                        logger.error(f"  [ERROR] {line.strip()}")

            return False

    except subprocess.TimeoutExpired:
        logger.error("[TIMEOUT] 야간 모드 봇 실행이 타임아웃되었습니다 (30초)")
        return False
    except FileNotFoundError:
        logger.error("[ERROR] Python 인터프리터를 찾을 수 없습니다")
        return False
    except Exception as e:
        logger.error(f"[ERROR] 야간 모드 봇 실행 중 예상치 못한 오류 발생: {e}")
        return False


def job_wrapper():
    """스케줄 작업 래퍼 함수"""
    now = datetime.now(pytz.timezone("Asia/Seoul"))
    current_hour = now.hour
    current_minute = now.minute

    # 특별 처리: 22:00에는 야간 모드로 전환
    if current_hour == 22 and current_minute == 0:
        logger.info("[NIGHT_MODE] 22:00 - 야간 모드로 전환합니다")
        success = run_bot_night_mode()
        if success:
            logger.info("[COMPLETE] 야간 모드 전환 완료")
        else:
            logger.warning("[WARNING] 야간 모드 전환 중 오류 발생")
        logger.info("[WAIT] 다음 실행까지 대기 중...")
        print("-" * 50)
        return

    # 특별 처리: 07:00에는 정상 모드로 복구
    if current_hour == 7 and current_minute == 0:
        logger.info("[MORNING_MODE] 07:00 - 정상 모드로 복구합니다")
        minute = now.minute
        logger.info(f"[START] 스케줄 작업 시작 (현재 시간: {minute}분)")
        success = run_bot()
        if success:
            logger.info("[COMPLETE] 정상 모드 복구 완료")
        else:
            logger.warning("[WARNING] 정상 모드 복구 중 오류 발생")
        logger.info("[WAIT] 다음 실행까지 대기 중...")
        print("-" * 50)
        return

    # 한국 시간 기준 22:01 ~ 06:59 사이에는 실행하지 않음
    if (
        (current_hour == 22 and current_minute > 0)
        or (current_hour > 22)
        or current_hour < 7
    ):
        logger.info(
            f"[SKIP] 현재 시간({now.strftime('%H:%M')})이 야간 시간이므로 건너뜁니다"
        )
        logger.info("[WAIT] 다음 실행까지 대기 중...")
        print("-" * 50)
        return

    # 점진적 개선: 실제 업데이트가 필요한 시점인지 체크
    try:
        next_update_time = calculate_next_update_time(now)
        time_until_update = (next_update_time - now).total_seconds()

        # 평일 업무시간(07:00-21:50)에는 정확히 10분 단위로 실행해야 함
        # 두 지역 중 하나라도 평일이면 업데이트 필요
        seoul_is_off_day = is_off_day(now.date(), "SEOUL")
        hcmc_is_off_day = is_off_day(now.date(), "HCMC")

        # 두 지역 중 하나라도 평일이면 업무시간으로 간주
        is_workday_hours = (
            7 <= current_hour <= 21
            and not (seoul_is_off_day and hcmc_is_off_day)  # 둘 다 휴일이 아닌 경우
        )

        # 평일 업무시간이면 5분 기준 무시하고 실행
        if is_workday_hours:
            logger.info(f"[WORKDAY] 업무시간 - 정확한 시간 업데이트를 위해 실행")
            logger.info(
                f"[DEBUG] 서울 휴일: {seoul_is_off_day}, 베트남 휴일: {hcmc_is_off_day}"
            )
            logger.info(
                f"[DEBUG] 다음 업데이트 예정: {next_update_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        # 평일 업무시간이 아니면 5분 기준 효율성 체크
        elif time_until_update > 300:  # 5분 = 300초
            logger.info(
                f"[EFFICIENCY] 다음 업데이트까지 {time_until_update / 60:.1f}분 남음 - 실행 스킵"
            )
            logger.info(
                f"[NEXT_UPDATE] 다음 업데이트 예정: {next_update_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            logger.info(
                f"[DEBUG] 서울 휴일: {seoul_is_off_day}, 베트남 휴일: {hcmc_is_off_day}"
            )
            logger.info("[WAIT] 다음 실행까지 대기 중...")
            print("-" * 50)
            return
        else:
            logger.info(
                f"[EFFICIENCY] 다음 업데이트까지 {time_until_update / 60:.1f}분 - 실행 필요"
            )
            logger.info(
                f"[DEBUG] 서울 휴일: {seoul_is_off_day}, 베트남 휴일: {hcmc_is_off_day}"
            )
            logger.info(
                f"[DEBUG] 다음 업데이트 예정: {next_update_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
    except Exception as e:
        logger.warning(f"[WARNING] 업데이트 시점 계산 실패: {e} - 기본 로직으로 진행")

    minute = now.minute
    logger.info(f"[START] 스케줄 작업 시작 (현재 시간: {minute}분)")

    success = run_bot()

    if success:
        logger.info("[COMPLETE] 스케줄 작업 완료")
    else:
        logger.warning("[WARNING] 스케줄 작업 중 오류 발생")

    logger.info("[WAIT] 다음 실행까지 대기 중...")
    print("-" * 50)  # 구분선


# APScheduler 사용으로 대체하여 제거됨


def main():
    """메인 스케줄러 함수 - APScheduler 사용"""
    logger.info("[INIT] Discord 타임존 봇 스케줄러를 시작합니다 (APScheduler)")
    logger.info(
        "[SCHEDULE] 업무 시간(07:00-21:50): 정각 10분 단위로 실행 (0, 10, 20, 30, 40, 50분)"
    )
    logger.info("[SCHEDULE] 야간 모드(22:00): 수면 상태로 전환")
    logger.info("[SCHEDULE] 정상 모드(07:00): 시간 표시로 복구")
    logger.info("[SCHEDULE] 휴일/주말은 각 채널별로 개별 처리됩니다")

    # 현재 시간대 정보 출력
    current_time = datetime.now()
    kst = pytz.timezone("Asia/Seoul")
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

    # APScheduler 설정
    scheduler = BlockingScheduler(timezone=kst)

    # 일반 업무 시간 (07:00-21:50) - 매 10분마다 실행
    normal_trigger = CronTrigger(
        minute="0,10,20,30,40,50",
        hour="7-21",  # 07시부터 21시까지만
        second=0,
        timezone=kst,
    )

    # 야간 모드 전환 (22:00 정확히)
    night_trigger = CronTrigger(
        minute="0",
        hour="22",  # 22시 정확히
        second=0,
        timezone=kst,
    )

    # 정상 모드 복구 (07:00 정확히) - 별도 잡으로 처리하지 않고 normal_trigger가 처리

    scheduler.add_job(
        job_wrapper,
        trigger=normal_trigger,
        id="discord_bot_normal",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=180,  # 3분으로 증가
    )

    scheduler.add_job(
        job_wrapper,
        trigger=night_trigger,
        id="discord_bot_night",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=180,  # 3분으로 증가
    )

    # 현재 시간에 따른 즉시 실행 처리
    current_time = datetime.now(kst)
    current_hour = current_time.hour
    current_minute = current_time.minute

    # 봇 초기 실행 시 무조건 한번 업데이트 (사용자 요구사항)
    logger.info(
        f"[IMMEDIATE] 봇 초기 실행 - 현재 상태로 무조건 업데이트합니다 ({current_time.strftime('%H:%M')})"
    )

    # 야간 시간대는 야간 모드로, 그 외는 일반 모드로 업데이트
    if (
        (current_hour == 22 and current_minute > 0)
        or (current_hour > 22)
        or current_hour < 7
    ):
        logger.info("[IMMEDIATE] 야간 시간대 - 야간 모드로 업데이트")
        success = run_bot_night_mode()
    else:
        logger.info("[IMMEDIATE] 일반 시간대 - 일반 모드로 업데이트")
        success = run_bot()

    if success:
        logger.info("[IMMEDIATE] 초기 업데이트 완료")
    else:
        logger.warning("[IMMEDIATE] 초기 업데이트 실패")

    logger.info("[IMMEDIATE] 이제 스케줄러로 전환하여 효율성 체크가 적용됩니다")
    print("-" * 50)

    try:
        logger.info("[SCHEDULER] APScheduler 시작...")
        logger.info(
            "[SCHEDULER] 업무 시간: 매 10분마다, 야간 전환: 22:00, 정상 복구: 07:00"
        )
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("[STOP] 사용자에 의해 스케줄러가 중지되었습니다")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"[ERROR] 스케줄러 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
