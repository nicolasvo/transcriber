FROM python:3.7

WORKDIR /app
COPY . .

RUN apt update
RUN apt install -y ffmpeg
RUN pip install pipenv
RUN pipenv install --system

ENTRYPOINT ["python"]
CMD ["app/bot.py"]
