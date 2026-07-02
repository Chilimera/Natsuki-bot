import os
import random
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import telebot
import requests
from bs4 import BeautifulSoup


BOT_TOKEN = os.environ.get('bot_token', None)

FILEPATH1 = "data\\tsundere_neko_chat.txt"
FILEPATH2 = "data\\dataset.txt"
FILEPATH3 = "data\\Delvig_Anton.txt"
FILEPATH4 = "data\\War_And_World.txt"
FILEPATH5 = "data\\Dialogues.txt"

FILEPATH = FILEPATH5

bot = telebot.TeleBot(BOT_TOKEN)
questions = []
answers = []

def load_data(filepath):
    global questions, answers
    questions = []
    answers = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = f.read()
            pairs = data.split('\n\n')

            for i in range(0, len(pairs) - 1, 2):
                question = pairs[i].strip()
                answer_str = pairs[i + 1].strip()
                answer_list = [a.strip() for a in answer_str.split('|')]

                if question and answer_list:
                    questions.append(question)
                    answers.append(answer_list)
                else:
                    print(f"Предупреждение: Пропущена пара вопрос-ответ из-за пустых значений.")

    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text

def find_fuzzy_match(question, cutoff=40):
    question = preprocess_text(question)
    processed_questions = [preprocess_text(q) for q in questions]

    scores = []
    for i, processed_q in enumerate(processed_questions):
        score1 = fuzz.ratio(question, processed_q)
        score2 = fuzz.partial_ratio(question, processed_q)
        score3 = fuzz.token_sort_ratio(question, processed_q)
        score4 = fuzz.token_set_ratio(question, processed_q)

        combined_score = (score1 * 0.1 + score2 * 0.4 + score3 * 0.2 + score4 * 0.3)

        scores.append((i, questions[i], combined_score))

    scores.sort(key=lambda x: x[2], reverse=True)

    if scores:
        best_index = scores[0][0]
        best_score = scores[0][2]
        best_match = questions[best_index]

        if best_score >= cutoff:
            return random.choice(answers[best_index])

    return None

def get_random_emotion(response):
    if "бака" in response.lower() or "глупый" in response.lower():
        emotions = ["*надувается*", "*отворачивается*", "*фыркает*"]
        return " " + random.choice(emotions)
    elif random.random() < 0.1:
        emotions = ["*краснеет*", "*тихо мурлычет*", "*застенчиво улыбается*", "*недовольно вздыхает*"]
        return " " + random.choice(emotions)
    return ""

def get_google_image_url(query):
    try:
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        headers = {'User-Agent': 'Mozilla/5.0'}
        proxies = {
            'http': None,
            'https': None,
        }
        try:
            response = requests.get(search_url, headers=headers, proxies=proxies)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')

            if len(img_tags) > 1:
                img_url = img_tags[1].get('data-src') or img_tags[1].get('data-iurl') or img_tags[1]['src']
                return img_url
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к Google: {e}")
            return None


    except Exception as e:
        print(f"Ошибка при обработке ответа Google: {e}")
        return None

def send_image_from_query(chat_id, query):
    image_url = get_google_image_url(query)

    if image_url:
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()

            bot.send_photo(chat_id, image_url)

        except requests.exceptions.RequestException as e:
            bot.send_message(chat_id, f"Ошибка при скачивании картинки: {e}")
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(chat_id, f"Ошибка при отправке картинки: {e}")
        except Exception as e:
            bot.send_message(chat_id, f"Произошла ошибка: {e}")
    else:
        bot.send_message(chat_id, "Не удалось найти картинку по запросу.")

def extract_query(text):
    text = text.strip()
    if text.lower().startswith("покажи"):
        text = text[len("покажи"):].strip()
        print("Image Request: ", text)
        print("-----------------------------------")
        return text
    elif text.lower().startswith("скинь"):
        text = text[len("скинь"):].strip()
        print("Image Request: ", text)
        print("-----------------------------------")
        return text
    else:
        return None

# --- ОБРАБОТЧИКИ TELEGRAM ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Хмпф! И чего это ты пишешь? Не то чтобы я ждала сообщения, или что-то в этом роде!")

@bot.message_handler(commands=['tomato'])
def tomato(message):
    with open('img\\tomato.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)

@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def echo_all(message):
    if message.reply_to_message.from_user.id == 7556863360:
        user_input = message.text

        image_query = extract_query(user_input)

        if image_query:
            send_image_from_query(message.chat.id, image_query)

        elif message.text == "@Sqwityr":
            with open('img\\face.png', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)

        else:
            response = find_fuzzy_match(user_input)

            if response is None:
                response = "Я не понимаю. Спроси что-нибудь другое, бака!"

            emotion = get_random_emotion(response)
            response += emotion

            bot.reply_to(message, response)
            print(message.text, "     |     ", response)
            print("-----------------------------------")

if __name__ == '__main__':
    if os.path.exists(FILEPATH):
        load_data(FILEPATH)
        print("База данных загружена.")
    else:
        print(f"Ошибка: Файл {FILEPATH} не найден.")
        exit()

    print("Бот запущен. Для остановки нажмите Ctrl+C")
    bot.infinity_polling()
