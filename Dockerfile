# Use a imagem base oficial do Python (slim para ser leve no Raspberry Pi)
FROM python:3.13-slim

# Instala o gerenciador de pacotes uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de dependência do projeto
COPY pyproject.toml uv.lock ./

# Sincroniza as dependências do projeto usando uv
RUN uv sync --frozen --no-cache

# Copia todo o restante do código fonte do projeto
COPY . .

# Expõe a porta do servidor
EXPOSE 7777

# Executa o servidor de desenvolvimento do Django na porta 7777
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:7777"]
