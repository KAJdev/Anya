FROM python:3.10.4

WORKDIR /

RUN apt update && apt install -y libsm6 libxext6
RUN apt-get -y install tesseract-ocr

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]