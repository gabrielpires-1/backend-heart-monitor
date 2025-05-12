FROM python:3.12-alpine

ARG APP_NAME=fastAPI-Embarcados
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY . .

# Instalando as dependências do sistema
RUN apk update && apk add --no-cache \
    gcc \
    postgresql-dev \
    pipx && \
    echo $PATH && \
    pipx install poetry && \
    poetry install --no-root

# Expondo a porta 8000
EXPOSE 8000

# Comando para rodar o aplicativo
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]