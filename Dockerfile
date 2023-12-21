# Используйте официальный образ Python
FROM python:3.12

# Устанавливаем рабочую директорию в /Project
WORKDIR /Project

# Копируем зависимости и устанавливаем их
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем содержимое текущей директории в контейнер в /Project
COPY . /Project

# Указываем порт, который будет использоваться приложением
EXPOSE 5000

# Команда, которая будет выполнена при запуске контейнера
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "5000"]


