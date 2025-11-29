import os
import random
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
import requests

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
POKISKKINO_API_KEY = "ZCKVZ3E-SAK4SYM-G9FA85M-7DA9YGK"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MovieBot:
    def __init__(self):
        self.base_url = "https://api.poiskkino.dev"
        self.api_version = "v1.4"
        self.use_api = True
        self.headers = {"X-API-KEY": POKISKKINO_API_KEY}
        
    def safe_api_request(self, endpoint, params=None):
        """Безопасный запрос к API ПоискКино с обработкой ошибок"""
        try:
            url = f"{self.base_url}/{self.api_version}/{endpoint}"
            logger.info(f"Отправка запроса к ПоискКино API: {url}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к ПоискКино API")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка подключения к ПоискКино API: {e}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка от ПоискКино API: {e}")
            if response.status_code == 401:
                logger.error("Неверный API ключ для ПоискКино")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка API запроса: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None
    
    def get_random_movie(self):
        """Получение случайного фильма из ПоискКино API"""
        data = self.safe_api_request("movie/random")
        if data and isinstance(data, dict):
            return data
        return None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start - показывает приветствие"""
        await self.show_welcome_message(update, context)

    async def show_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать приветственное сообщение при первом заходе"""
        keyboard = [
            [InlineKeyboardButton("🎬 Получить случайный фильм", callback_data='random')],
            [InlineKeyboardButton("ℹ️ О боте", callback_data='about')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🎭 Добро пожаловать в киносоветник!\n\n"
            "🤖 <b>О боте:</b>\n"
            "• 🎬 Получайте случайные фильмы из обширной базы\n"
            "• 📡 Используется актуальная база ПоискКино API\n"
            "• 🇷🇺 Работает в России\n"
            "• ⚡ Быстрый поиск фильмов\n\n"
            "Нажмите кнопку ниже, чтобы получить случайный фильм:"
        )
        
        # Отправляем новое сообщение
        if update.message:
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    async def handle_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'random':
            await self.send_random_movie(update, context)
        elif query.data == 'about':
            await self.show_about(update, context)
        elif query.data == 'back_to_main':
            await self.show_welcome_message(update, context)

    async def show_about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о боте"""
        about_text = (
            "🤖 <b>О боте</b>\n\n"
            "📡 <b>Источник данных:</b> ПоискКино API\n"
            "🎯 <b>Функции:</b>\n"
            "• 🎬 Случайные фильмы\n\n"
            "💡 <b>Особенности:</b>\n"
            "• Работает в России 🇷🇺\n"
            "• Актуальная база фильмов\n"
            "• Подробная информация о фильмах\n"
            "• Быстрый поиск"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎬 Получить фильм", callback_data='random')],
            [InlineKeyboardButton("🔙 На главную", callback_data='back_to_main')]
        ]
        
        await self.send_new_message(update, context, about_text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    async def send_new_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None, parse_mode=None):
        """Универсальная функция отправки нового сообщения"""
        try:
            if hasattr(update, 'callback_query') and update.callback_query:
                return await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                return await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            try:
                if hasattr(update, 'callback_query') and update.callback_query:
                    return await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=reply_markup
                    )
                else:
                    return await update.message.reply_text(
                        text=text,
                        reply_markup=reply_markup
                    )
            except Exception as e2:
                logger.error(f"Критическая ошибка при отправке сообщения: {e2}")
                return None

    async def send_movie_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, movie):
        """Отправка информации о фильме"""
        if not movie:
            await self.send_error_message(update, context)
            return

        # Извлекаем данные из ответа ПоискКино API
        title = movie.get('name', 'Неизвестно')
        original_title = movie.get('alternativeName', '')
        rating = movie.get('rating', {}).get('kp', 0)
        overview = movie.get('description', 'Описание отсутствует')
        year = movie.get('year', 'Неизвестно')
        runtime = movie.get('movieLength', 'N/A')
        
        # Жанры
        genres_data = movie.get('genres', [])
        genres = ", ".join([g.get('name', '') for g in genres_data]) if genres_data else 'Неизвестно'
        
        # Страны
        countries_data = movie.get('countries', [])
        countries = ", ".join([c.get('name', '') for c in countries_data]) if countries_data else 'Неизвестно'
        
        # Дополнительная информация
        age_rating = movie.get('ageRating', 'Неизвестно')
        movie_type = movie.get('type', '')
        type_translation = {
            'movie': 'Фильм',
            'tv-series': 'Сериал',
            'cartoon': 'Мультфильм',
            'anime': 'Аниме'
        }
        type_text = type_translation.get(movie_type, movie_type)

        # Форматируем сообщение
        message_parts = [
            f"🎬 <b>{title}</b>",
            f"📝 <i>{original_title}</i>" if original_title and original_title != title else "",
            f"📺 Тип: <b>{type_text}</b>" if type_text else "",
            f"⭐ Рейтинг КП: <b>{rating}/10</b>",
            f"⏱ Время: <b>{runtime} мин</b>" if runtime != 'N/A' else "",
            f"🎭 Жанры: <b>{genres}</b>",
            f"🌍 Страны: <b>{countries}</b>",
            f"📅 Год: <b>{year}</b>",
            f"🔞 Возрастной рейтинг: <b>{age_rating}+</b>" if age_rating and age_rating != 'null' else "",
            "",
            f"📖 <b>Описание:</b>\n{overview}"
        ]
        
        message = "\n".join([part for part in message_parts if part])

        # Создаем клавиатуру с действиями
        keyboard = [
            [InlineKeyboardButton("🎲 Другой случайный фильм", callback_data='random')],
            [InlineKeyboardButton("🔙 На главную", callback_data='back_to_main')]
        ]

        # Пытаемся отправить постер, если есть
        poster_url = None
        if movie.get('poster') and movie.get('poster', {}).get('url'):
            poster_url = movie['poster']['url']
        
        try:
            if poster_url:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=poster_url,
                    caption=message,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await self.send_new_message(
                    update, 
                    context, 
                    message, 
                    InlineKeyboardMarkup(keyboard), 
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке информации о фильме: {e}")
            await self.send_new_message(
                update, 
                context, 
                message, 
                InlineKeyboardMarkup(keyboard), 
                parse_mode='HTML'
            )

    async def send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, custom_message=None):
        """Отправка сообщения об ошибке"""
        error_text = custom_message or (
            "❌ Произошла ошибка при получении информации о фильмах.\n\n"
            "Возможные причины:\n"
            "• Проблемы с интернет-соединением\n"
            "• Временная недоступность базы фильмов\n\n"
            "Пожалуйста, попробуйте позже."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data='random')],
            [InlineKeyboardButton("🔙 На главную", callback_data='back_to_main')]
        ]
        
        await self.send_new_message(update, context, error_text, InlineKeyboardMarkup(keyboard))

    async def send_random_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка случайного фильма"""
        search_message = await self.send_new_message(update, context, "🎲 Ищу случайный фильм...")
        
        await asyncio.sleep(0.5)
        
        movie = self.get_random_movie()
        if movie:
            await self.send_movie_info(update, context, movie)
        else:
            await self.send_error_message(update, context)

    async def handle_first_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка первого сообщения - показывает приветствие"""
        await self.show_welcome_message(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_chat:
        try:
            error_message = (
                "❌ Произошла непредвиденная ошибка. "
                "Пожалуйста, попробуйте позже или начните заново."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("Не найден BOT_TOKEN в переменных окружения!")
        return
    
    movie_bot = MovieBot()
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", movie_bot.start))
    
    # Обработчики callback-запросов
    app.add_handler(CallbackQueryHandler(movie_bot.handle_button, pattern='^(random|about|back_to_main)$'))
    
    # Обработчик первого сообщения - показывает приветствие автоматически
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, movie_bot.handle_first_message), group=0)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе с ПоискКино API!")
    app.run_polling()

if __name__ == "__main__":
    main()