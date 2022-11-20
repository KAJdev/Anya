# Anya
A bunch of stuff I need in a bot

## .env
```env
TOKEN=""
MONGO=""
DB_NAME=""
```

## Running
install python 3.10 + pip + venv

install tesseract if you want OCR commands.

### Linux
```bash
python3.10 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python3.10 main.py
```


### Windows
```batch
python3.10 -m venv venv
```

```batch
.\venv\Scripts\activate
```

```batch
pip install -r requirements.txt
```

```bash
python3.10 main.py
```

git push dokku-local main:master
