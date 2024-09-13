import telebot
from datetime import datetime
import sqlite3

bot = telebot.TeleBot("Ваш токен телеграмм")

# Функция для создания базы данных, если она еще не создана
def create_db():
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       lastname TEXT NOT NULL,
                       firstname TEXT NOT NULL,
                       middlename TEXT NOT NULL,
                       birthdate DATE NOT NULL,
                       visit_date TEXT NOT NULL)''')  # Сохраняем дату визита как строку
    conn.commit()
    conn.close()

# Создаем базу данных при запуске
create_db()

# Функция для добавления пациента в базу данных
def add_patient_to_db(lastname, firstname, middlename, birthdate):
    visit_date = datetime.now().date().strftime("%Y-%m-%d")  # Преобразуем дату в строку
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO patients (lastname, firstname, middlename, birthdate, visit_date)
                      VALUES (?, ?, ?, ?, ?)''', (lastname, firstname, middlename, birthdate, visit_date))
    conn.commit()
    conn.close()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("Добавить пациента")
    btn2 = telebot.types.KeyboardButton("Пациенты за сегодня")
    markup.add(btn1, btn2)
    btn3 = telebot.types.KeyboardButton("Количество пациентов за неделю")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

# Переменные для временного хранения данных пациента
patient_data = {}

# Добавление пациента
@bot.message_handler(func=lambda message: message.text == "Добавить пациента")
def add_patient(message):
    bot.send_message(message.chat.id, "Введите фамилию пациента:")
    bot.register_next_step_handler(message, process_lastname)

def process_lastname(message):
    lastname = message.text
    if not lastname.isalpha():
        bot.send_message(message.chat.id, "Некорректная фамилия. Используйте только буквы.")
        return
    patient_data['lastname'] = lastname
    bot.send_message(message.chat.id, "Введите имя пациента:")
    bot.register_next_step_handler(message, process_firstname)

def process_firstname(message):
    firstname = message.text
    if not firstname.isalpha():
        bot.send_message(message.chat.id, "Некорректное имя. Используйте только буквы.")
        return
    patient_data['firstname'] = firstname
    bot.send_message(message.chat.id, "Введите отчество пациента:")
    bot.register_next_step_handler(message, process_middlename)

def process_middlename(message):
    middlename = message.text
    if not middlename.isalpha():
        bot.send_message(message.chat.id, "Некорректное отчество. Используйте только буквы.")
        return
    patient_data['middlename'] = middlename
    bot.send_message(message.chat.id, "Введите дату рождения пациента (YYYY-MM-DD):")
    bot.register_next_step_handler(message, process_birthdate)

def process_birthdate(message):
    try:
        birthdate = datetime.strptime(message.text, "%Y-%m-%d")
        age = (datetime.now() - birthdate).days // 365
        if age > 100:
            bot.send_message(message.chat.id, "Возраст должен быть меньше 100 лет.")
            return
        patient_data['birthdate'] = birthdate
        add_patient_to_db(patient_data['lastname'], patient_data['firstname'], patient_data['middlename'], patient_data['birthdate'])
        bot.send_message(message.chat.id, f"Пациент {patient_data['lastname']} {patient_data['firstname']} {patient_data['middlename']} успешно добавлен!")
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный формат даты. Введите в формате YYYY-MM-DD.")

# Пациенты за сегодня
@bot.message_handler(func=lambda message: message.text == "Пациенты за сегодня")
def todays_patients(message):
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")  # Преобразуем текущую дату в строку
    cursor.execute("SELECT lastname, firstname, middlename FROM patients WHERE visit_date = ?", (today,))
    patients = cursor.fetchall()
    if patients:
        response = "Пациенты за сегодня:\n" + "\n".join([f"{p[0]} {p[1]} {p[2]}" for p in patients])
    else:
        response = "Сегодня пациентов не было."

# Пациенты за каждый день недели
@bot.message_handler(func=lambda message: message.text == "Количество пациентов за неделю")
def patients_per_weekday(message):
    conn = sqlite3.connect('patients.db')
    cursor = conn.cursor()

    # Запрос всех дат посещений из базы данных
    cursor.execute("SELECT visit_date FROM patients")
    patients = cursor.fetchall()

    # Создаем словарь для подсчета пациентов по дням недели
    weekdays = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг', 4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
    weekday_counts = {day: 0 for day in weekdays.values()}

    # Проходим по всем пациентам и считаем количество по дням недели
    for patient in patients:
        visit_date = datetime.strptime(patient[0], "%Y-%m-%d")
        weekday = visit_date.weekday()  # Получаем номер дня недели (0 - понедельник, 6 - воскресенье)
        weekday_name = weekdays[weekday]
        weekday_counts[weekday_name] += 1

    # Формируем ответ
    response = "Количество пациентов за каждый день недели:\n"
    for day, count in weekday_counts.items():
        response += f"{day}: {count}\n"

    # Отправляем ответ и закрываем соединение с базой данных
    bot.send_message(message.chat.id, response)
    conn.close()
bot.polling()
