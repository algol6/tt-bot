# Teletubbies Bot

## Configuration

Create .env file with following value:
```
DISCORD_ACTIVITY = "text on the bot while on"
DATABASE_URI = "database-uri"
DISCORD_TOKEN = "discord-token"
SMMO_TOKEN = "smmo-token"
```

Configure custom reward or requirements in `config.ini`

## Installation & running

### MacOS / Linux
`python -m venv .venv`

`source venv/bin/activate` - required every time to run.

`pip install -r requirements.txt`

`python main.py` - run the bot


### Windows
`python -m venv venv`

`./venv/bin/activate.bat` - required every time to run

`pip install -r requirements.txt`

`python main.py` - run the bot 