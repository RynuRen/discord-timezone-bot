FROM python:3.12-slim

# 타임존 설정을 위한 패키지 설치
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# KST 타임존 설정
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트 파일 복사 (상위 디렉토리에서)
COPY pyproject.toml uv.lock ./
COPY bot/ ./bot/

# uv로 의존성 설치
RUN uv sync --frozen --no-cache

# 환경 변수 설정
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# 스크립트 실행
CMD ["python", "-m", "bot.main"]