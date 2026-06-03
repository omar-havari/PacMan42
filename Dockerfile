FROM python:3.14-slim

WORKDIR /short_demo_pacman

RUN apt-get update && apt-get install -y \
    gcc \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY flake8_dependencies.txt .
COPY pygame_dependencies.txt .
RUN pip install -r flake8_dependencies.txt
RUN pip install -r pygame_dependencies.txt

COPY . .

CMD ["python", "main_menu_UI.py"]
