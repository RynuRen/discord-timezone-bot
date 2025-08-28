import logging
import sys
import os


def setup_logging(logger_name: str) -> logging.Logger:
    """공통 로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(logger_name)


def check_discord_token() -> str:
    """Discord 토큰 환경변수 확인 및 반환"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN 환경변수가 설정되지 않았습니다!")
    return token
