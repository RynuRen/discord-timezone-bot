import discord
import sys

try:
    from .utils import setup_logging, check_discord_token
    from .updater import update_channel_names
except ImportError:
    # 직접 실행될 때를 위한 대체 import
    from utils import setup_logging, check_discord_token
    from updater import update_channel_names

# 로깅 설정
logger = setup_logging("discord_timezone_bot")

try:
    TOKEN = check_discord_token()
except ValueError as e:
    logger.error(f"[ERROR] {e}")
    sys.exit(1)

intents = discord.Intents.default()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    logger.info(f"[LOGIN] 봇이 {client.user}로 로그인했습니다")
    logger.info(f"[CONNECT] {len(client.guilds)}개 서버에 연결되었습니다")

    # 채널 업데이트 실행
    await update_channel_names(client)

    logger.info("[DONE] 봇 작업 완료, 연결을 종료합니다")
    await client.close()


@client.event
async def on_error(event, *args, **kwargs):
    logger.error(f"[ERROR] Discord 이벤트 오류 발생: {event}", exc_info=True)


if __name__ == "__main__":
    try:
        logger.info("[INIT] Discord 타임존 봇을 시작합니다...")
        client.run(TOKEN)
    except discord.LoginFailure:
        logger.error("[LOGINF] Discord 토큰이 잘못되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"[ERROR] 봇 실행 중 오류 발생: {e}")
        sys.exit(1)
