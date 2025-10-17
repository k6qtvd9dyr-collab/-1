# OGUREC - Бот для Kufar

Простой Telegram бот для мониторинга новых объявлений на Kufar.

## Быстрый запуск на Railway

### 1. Создайте бота в Telegram
- Найдите @BotFather в Telegram
- Отправьте `/newbot`
- Введите имя: `OgurecKufarBot`
- Получите токен

### 2. Разверните на Railway
1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Создайте репозиторий с файлами проекта
4. Подключите репозиторий к Railway
5. В настройках проекта добавьте переменную:
   - Name: `BOT_TOKEN`
   - Value: `ваш_токен_бота`

### 3. Используйте бота
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Отправьте `/categories` и выберите категорию
4. Получайте новые объявления каждую минуту!

## Локальный запуск
```bash
# Установите зависимости
pip install -r requirements.txt

# Создайте файл .env с токеном
echo "BOT_TOKEN=ваш_токен" > .env

# Запустите бота
python bot.py
