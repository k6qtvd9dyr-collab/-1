import os
import telebot
import requests
import sqlite3
import threading
import time
from bs4 import BeautifulSoup

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не установлен!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# База данных
def init_db():
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            filters TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_ads (
            ad_id TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

# Категории Kufar
CATEGORIES = {
    'ноутбуки': 'https://www.kufar.by/l/r?cat=17010&sort=lst.d',
    'телефоны': 'https://www.kufar.by/l/r?cat=16010&sort=lst.d', 
    'авто': 'https://www.kufar.by/l/r?cat=1410&sort=lst.d',
    'квартиры': 'https://www.kufar.by/l/r?cat=1010&sort=lst.d'
}

# Парсинг объявлений
def get_ads(category_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(category_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        ads = []
        # Ищем карточки объявлений (селектор может меняться)
        items = soup.find_all('section', class_=lambda x: x and 'styles_card' in x)
        
        for item in items[:10]:  # Первые 10 объявлений
            try:
                title_elem = item.find('h3')
                price_elem = item.find('p')
                link_elem = item.find('a', href=True)
                
                if title_elem and price_elem and link_elem:
                    title = title_elem.text.strip()
                    price = price_elem.text.strip()
                    link = 'https://www.kufar.by' + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href']
                    
                    ads.append({
                        'title': title,
                        'price': price,
                        'link': link,
                        'id': link.split('/')[-1]
                    })
            except:
                continue
                
        return ads
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return []

# Проверка новых объявлений
def check_ads():
    while True:
        try:
            conn = sqlite3.connect('ads.db')
            cursor = conn.cursor()
            
            # Получаем всех пользователей
            cursor.execute('SELECT user_id, filters FROM users')
            users = cursor.fetchall()
            
            for user_id, filters_str in users:
                if not filters_str:
                    continue
                    
                # Простая система фильтров
                filters = filters_str.split('|')
                category = filters[0] if len(filters) > 0 else 'ноутбуки'
                
                if category in CATEGORIES:
                    ads = get_ads(CATEGORIES[category])
                    
                    for ad in ads:
                        # Проверяем, не видели ли уже это объявление
                        cursor.execute('SELECT 1 FROM seen_ads WHERE ad_id = ?', (ad['id'],))
                        if not cursor.fetchone():
                            # Новое объявление!
                            message = f"🏷️ {ad['title']}\n💰 {ad['price']}\n🔗 {ad['link']}"
                            try:
                                bot.send_message(user_id, message)
                                # Сохраняем как просмотренное
                                cursor.execute('INSERT INTO seen_ads (ad_id) VALUES (?)', (ad['id'],))
                                conn.commit()
                                time.sleep(1)  # Пауза между сообщениями
                            except Exception as e:
                                print(f"Ошибка отправки: {e}")
            
            conn.close()
            time.sleep(60)  # Ждем 1 минуту
            
        except Exception as e:
            print(f"Ошибка в check_ads: {e}")
            time.sleep(60)

# Команды бота
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    
    text = """
🤖 Привет! Я бот OGUREC для мониторинга Kufar.

Доступные команды:
/start - начать работу
/categories - выбрать категорию
/my_filters - мои настройки
/help - помощь

Бот будет присылать новые объявления каждую минуту!
    """
    bot.send_message(user_id, text)

@bot.message_handler(commands=['categories'])
def categories(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES.keys():
        keyboard.add(telebot.types.KeyboardButton(category))
    
    bot.send_message(message.chat.id, "📁 Выберите категорию:", reply_markup=keyboard)

@bot.message_handler(commands=['my_filters'])
def my_filters(message):
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT filters FROM users WHERE user_id = ?', (message.chat.id,))
    result = cursor.fetchone()
    conn.close()
    
    filters = result[0] if result else 'не установлены'
    bot.send_message(message.chat.id, f"📊 Ваши фильтры: {filters}")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = """
📖 Помощь по боту OGUREC:

1. Нажмите /categories чтобы выбрать категорию
2. Бот автоматически начнет присылать новые объявления
3. Обновление происходит каждую минуту

Доступные категории:
• ноутбуки
• телефоны  
• авто
• квартиры
    """
    bot.send_message(message.chat.id, text)

# Обработка выбора категории
@bot.message_handler(func=lambda message: message.text in CATEGORIES.keys())
def handle_category(message):
    user_id = message.chat.id
    category = message.text
    
    conn = sqlite3.connect('ads.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET filters = ? WHERE user_id = ?', (category, user_id))
    conn.commit()
    conn.close()
    
    # Убираем клавиатуру
    remove_keyboard = telebot.types.ReplyKeyboardRemove()
    bot.send_message(user_id, f"✅ Категория '{category}' установлена! Бот начнет присылать новые объявления.", 
                    reply_markup=remove_keyboard)

# Запуск мониторинга в отдельном потоке
def start_monitoring():
    monitor_thread = threading.Thread(target=check_ads, daemon=True)
    monitor_thread.start()

if __name__ == '__main__':
    print("🚀 Запуск бота OGUREC...")
    init_db()
    start_monitoring()
    print("✅ Бот запущен! Мониторинг активен.")
    bot.polling(none_stop=True)
