import discord
import logging
from datetime import datetime
import pytz
import os
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('discord_timezone_bot')

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    logger.error("[ERROR] DISCORD_BOT_TOKEN 환경변수가 설정되지 않았습니다!")
    sys.exit(1)

# 채널 설정
CHANNELS = {
    "SEOUL": {"id": 1384147639293055036, "tz": "Asia/Seoul", "emoji": "🇰🇷", "name": "서울"},
    "HCMC": {"id": 1384147698747445401, "tz": "Asia/Ho_Chi_Minh", "emoji": "🇻🇳", "name": "호치민"},
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def update_channel_names():
    """모든 채널의 이름을 현재 시간으로 업데이트"""
    updated_count = 0
    
    for name, info in CHANNELS.items():
        try:
            channel = client.get_channel(info["id"])
            if not channel:
                logger.warning(f"[WARNING] 채널을 찾을 수 없습니다 (ID: {info['id']}, {info['name']})")
                continue
            
            # 길드 채널인지 확인 (DM 채널 제외)
            if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
                logger.warning(f"[WARNING] 지원하지 않는 채널 타입입니다 (ID: {info['id']}, {info['name']})")
                continue
                
            # 현재 시간 계산
            tz = pytz.timezone(info["tz"])
            now = datetime.now(tz)
            time_str = now.strftime("%H：%M")
            new_name = f"{info['emoji']}∥{time_str}"
            
            # 채널 이름이 이미 같다면 스킵
            if channel.name == new_name:
                logger.debug(f"[SKIP] {info['name']} 채널 이름이 이미 최신입니다: {new_name}")
                continue
            
            # 채널 이름 업데이트
            await channel.edit(name=new_name)
            logger.info(f"[SUCCESS] {info['name']} 채널 업데이트: {channel.name} -> {new_name}")
            updated_count += 1
            
        except discord.Forbidden:
            logger.error(f"[FORBIDDEN] {info['name']} 채널 수정 권한이 없습니다 (ID: {info['id']})")
        except discord.NotFound:
            logger.error(f"[NOTFOUND] {info['name']} 채널을 찾을 수 없습니다 (ID: {info['id']})")
        except Exception as e:
            logger.error(f"[ERROR] {info['name']} 채널 업데이트 실패: {e}")
    
    if updated_count == 0:
        logger.info("[INFO] 업데이트가 필요한 채널이 없습니다")
    else:
        logger.info(f"[COMPLETE] 총 {updated_count}개 채널이 업데이트되었습니다")

@client.event
async def on_ready():
    logger.info(f"[LOGIN] 봇이 {client.user}로 로그인했습니다")
    logger.info(f"[CONNECT] {len(client.guilds)}개 서버에 연결되었습니다")
    
    # 채널 업데이트 실행
    await update_channel_names()
    
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
