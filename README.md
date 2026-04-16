# TutorBot 

Telegram-бот для управления учебными процессами.


---

##  Описание
Бот помогает преподавателям и студентам:
- Организовывать расписание
- Отслеживать задания
- Получать уведомления
- Управлять группами пользователей

---

##  Быстрый старт

### Требования
- Python 3.9+
- PostgreSQL 12+
- Telegram API-токен (получите у [@BotFather](https://t.me/BotFather))

### Установка
```bash
git clone https://github.com/bogdnnx/TutorBot.git
cd TutorBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

 Настройка
Создайте файл .env
---
```
TOKEN=ваш_токен_бота
DB_URL=postgresql+asyncpg://user:password@localhost:5432/bot
TUTORS_LIST=123456789,987654321  # ID преподавателей через запятую
```
---
 Запуск
Ручной режим
```
source venv/bin/activate
python3 app.py
```
---
Запуск как службы (systemd)
```
sudo systemctl start tutorbot
sudo systemctl status tutorbot
```

---

## Администрирование

Только пользователи из TUTORS_LIST могут выполнять действия репетитора

Логирование
Логи хранятся в /tutor_logs
