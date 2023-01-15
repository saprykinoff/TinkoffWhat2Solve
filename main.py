import requests, os, pickle, sys
import telebot, logging, config, time
import traceback

if sys.platform== 'linux' or sys.platform== 'linux2':
    import ctypes
    from ctypes.util import find_library
    libc = ctypes.CDLL(find_library('c'))
    name = config.process_name.encode('ascii')
    libc.prctl(15, ctypes.c_char_p(name), 0, 0, 0)

params = dict() #хранит параметры полььзователя
proxyDict = { #я хз, там было написано вставьте несколько прокси, ну я и вставил
          'http'  : "http://190.93.246.26:80",
          'https'  : "http://84.17.51.234:3128",
        }

def get_logger(name):
    # я просто скопистил вроде. Суть в том, чтобы настроить вывод логгера
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if config.isdebug else logging.INFO)
    ti = time.ctime().replace(":", " ").replace("  ", " ")
    ti = ti.split(" ")
    ti = "_".join(ti[1:3])

    fh = logging.FileHandler( "/logs_" + ti + ".log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s-%(levelname)s  %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

bot = telebot.TeleBot(config.token, parse_mode='Markdown') # подключаемя к боту
log = get_logger("MainBot") # подключаемся к логгеру
log.info('Begin initialize bot')
log.info('This bot is working in ' + ('debug' if config.isdebug else 'release') + ' mode')


def save_params(user_id): # сохраняет параметры (оно просто берет и закидывает в файл дикт так, как питон в битах его видит)
    path = config.paths['user_saves'] + "/%s" % user_id
    with open(path + '/data.dat', "wb") as f:
        pickle.dump(params, f)
        log.info("Save params for " + str(user_id))


def set_params(user_id): # подгружаем пользователя
    global params
    path = config.paths['user_saves'] + "/%s" % user_id # указываем путь для папки чела (имя папки такое же как id в телеге)
    datapath = path + '/data.dat'
    if (not os.path.exists(path)): # если такой папки нет
        print("create directory for %s" % user_id)
        log.info("create directory for %s" % user_id)
        os.mkdir(path) # создадим
    if (not os.path.exists(datapath)):
        with open(datapath, "wb") as f:
            pickle.dump(config.default_param, f) # сразу запишем туда дефолтное значение
    try:
        with open(datapath, "rb") as f:
            params = pickle.load(f) # пытаемся подгрузить
            log.info("Successful get data: {0}".format(user_id))
    except Exception as exc:
        # опять ошибки
        params = config.default_param
        print("Unsuccessful get data: {0}".format(user_id))
        log.error("Unsuccessful get data: {0}".format(user_id))
        print(exc)
        log.error(exc)
        bot.send_message(user_id, "Что-то не так -- Невозможно подгрузить данные пользователя")



def calc(user_id): # считаем задачи для чела
    log.debug("Begin calc for " + str(user_id))
    set_params(user_id) # подгружаем пользователя
    tasks = dict() # дикт задач
    #if (params.get('id', -1) == -1): return [] # если не установлен  id
    if (params.get('name', -1) == -1): return [] # если не установлен  id
    #for table_link in config.table_links:
    for gid in params.get('groups', []):
        for table_link in config.table_links_dict.get(gid, ''):
            table = requests.get(table_link, proxyDict).json() # делаем запрос на табличку
            # 300iq способ получать tinkoff id на табличку
            tid = -1
            for user in table['users']:
                if (user['name'] == params.get('name', '<Тебя нет в табличке>')):
                    tid = user['id'] # если имена совпали
                    break
            if tid == -1:
                # bot.send_message(user_id, "Тебя нет в табличке. Введи `/start <Имя из таблицы>`")
                continue #return
            for contest in table['contests']: # перебираем контест
                for p_id, participant in contest['users'].items(): # перебираем p_id - id чела, participant - список задач (соре за название, там говно было сначала)
                    for task in range(len(participant)): # переберем  таску
                         if (participant[task]['score'] or participant[task]['verdict'] == 'PR'): # если сдана || пендинг ревью
                            task_name = '[' + gid + ']' + contest['title'] + ': ' + contest['problems'][task]['long'] + ' (' + contest['problems'][task]['short'] + ')' # формируем название задачи
                            if (tasks.get(task_name, 0) == 0): tasks[task_name] = 0 # нужно, тк если ты попытаешься получить значение, не сущестующее в мапе, получишь RE
                            if (str(p_id) == str(tid)): #str(params['id'])): # если мы сдали, то скажем, что ее сдало -1000 человек(как флаг)
                                tasks[task_name] = -100000
                            tasks[task_name] += 1
    tasks_ = []
    for k, v in tasks.items():
        if (v < 0): v = -1 # если флаг, то говорим -1
        tasks_.append([v, k])
    tasks_.sort() # сортим по количеству задач
    tasks_.reverse() # реверсаем, чтобы шло по убыванию
    log.debug("End calc for " + str(user_id))
    return tasks_


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id,
                     "Что порешать? -- бот, который помогает выбрать задачу для решения из тех, которые уже кто-то сдал.\n"
                     + "Поддерживает все параллели 2020-21, большинство 2019-20 и часть 2018-19 из-за недоступности данных на сервере.\n"
                     + "Чтобы открыть справку, напиши /help\n"
                     + "`/start <имя>` найдет тебя в таблице по имени, которое ты указал. Указывай именно так, как в таблице, иначе не будет работать. Ищет по всем таблицам, потому будет тормозить.\n"
                     + "`/get <N>` выдаст `N` лучших задач.\n"
                     + "`/get_count` выдвст число решенных задач.\n"
                     + "`/list_groups` выведет доступные группы. Пример группы: `bp20s`, `bp` --- параллель, `20` --- год начала, `s` --- весна (`f` --- осень)\n"
                     + "`/set_groups` позволяет установить текущий набор групп.\n"
                     + "`/get_groups` выдаст список групп для текущего аккаунта.\n"
                     + "`/debug_get` выведет твой id в телеге и текущее имя в табличке.\n"
                     + "`/info` выведет логи разработчика.\n"
                     + "@developerxyz поддерживает этого бота.\n"
                     + ("Это __отладочная__ версия бота" if config.isdebug else "Это __стабильная__ версия бота") + "\n"
                     + "Версия ２０２１年５月１８日")


@bot.message_handler(commands=['get'])
def ask_best_task(message): #вывод задачек
    user_id = message.chat.id
    log.debug("Begin /get for " + str(user_id))
    try:
        set_params(user_id) # подгружаем чела
        if params.get('name', '') == '':
            text = 'Сначала найди себя в табличке!'
        else:
            tasks = calc(user_id) # считаем для него лучшие задачи
            subst = message.text[len("/get"):] # берем n из сообщения
            if (len(subst) == 0):
                n = 1
                # это если не указано ничего
            else:
                n = int(subst)
            if n <= 0:
                text = "Для того, чтобы узнать число решенных задач, вызови команду `/get_count`"
            else:
                n = min(n, len(tasks))
                n = max(n, 0)
                # приводим в диапозон
                if (len(tasks) == 0): # если что-тоне так
                    text = "Очень тебя жаль. Сначала найди себя в табличке"
                else:
                    while (tasks[n - 1][0] == -1): # отбрасываем ррешенные задачи
                        n -= 1
                        if (n == 0):
                            break
                    if (n == 0): # чел гений, все сдал
                        # TODO приделать ему список рандомных задач
                        text = "Да ты крут, решил(а) все задачи, которые кто-то сдавал. А теперь решай оставшиеся!"
                        # text = "Да ты крут, вообще все сдал. おめでとうございます！"
                    # Этот случай теперь бесполезен
                    #elif n < 0:
                    #    # чел крут, он ввел 0
                    #    text = "Ты решил(а) {0} задач.".format(-n)
                    else:
                        # собственно вывод таблички
                        text_list = ["Топ {0} задач:```\n".format(n)]
                        for i in range(n):
                            if i % 20 == 0 and i != 0:
                                text_list.append("```\n")
                            text_list[-1] += ("%s"%tasks[i][1]).ljust(80, '-') + str(tasks[i][0]) + '\n'
                            if (i + 1) % 20 == 0:
                                text_list[-1] += "```\n"
                        if text_list[-1][-2] != '`':
                            text_list[-1] += "```\n"
        if "text_list" in locals():
            for t in text_list:
                bot.send_message(user_id, t)
        else:
            bot.send_message(user_id, text)
    except Exception as exc:
        # это тоже для дебага, но хостинг не дает(
        e = sys.exc_info()[0]
        print("Error: %s"%e)
        log.error("Error: %s"%e)
        print(traceback.format_exc())
        log.error(traceback.format_exc())
        bot.send_message(user_id, "Что-то пошло не так, нельзя получить список задач.")
    log.debug("End /get for " + str(user_id))


@bot.message_handler(commands=['get_count'])
def ask_best_task_2(message):
    user_id = message.chat.id
    log.debug("Begin /get_count for " + str(user_id))
    try:
        set_params(user_id) # подгружаем чела
        tasks = calc(user_id) # считаем для него лучшие задачи
        n = len(tasks)
        while (n != 0 and tasks[n - 1][0] == -1): # отбрасываем ррешенные задачи
            n -= 1

        text = "Ты решил(а) {0} задач.".format(len(tasks) - n)
        bot.send_message(user_id, text)
    except:
        # это тоже для дебага, но хостинг не дает(
        e = sys.exc_info()[0]
        print("Error: %s"%e)
        log.error("Error: %s"%e)
        print(traceback.format_exc())
        log.error(traceback.format_exc())
        bot.send_message(user_id, "Что-то пошло не так, нельзя получить список задач.")
    log.debug("End /get_count for " + str(user_id))


@bot.message_handler(commands=['debug_get'])
def ask_id(message): # узнать свое id (чисто дебагерская хрень)
    user_id = message.chat.id
    log.debug("Begin /debug_get for " + str(user_id))
    set_params(user_id)
    bot.send_message(user_id, "大丈夫です。telegram id = {0}, table name = {1}".format(message.chat.id, params.get('name', '<Сначала найди себя в табличке!>')))
    log.debug("End /debug_get for " + str(user_id))


# TODO у нас не ссылка, а список ссылок. И вообще, для каждого пользователя своя (ну или определить группу, в которой он и использовать predefined)
#@bot.message_handler(commands=['change_table_link'])
#def change_table_link(message): # это типа если другие параллели захотят, можно просто изменить ссылку запроса
#    user_id = message.chat.id
#    set_params(user_id)
#    new_link = message.text[len('/change_table_link '):]
#    if ('change_table_link' in params['permission']): # если есть права
#        bot.send_message(user_id, "new_link = %s" %new_link) # меняем ссылку
#        print("{0} change table link to {1}".format(user_id, new_link))
#        config.table_link = new_link
#    else:
#        bot.send_message(user_id, "You have no rights")


@bot.message_handler(commands=['set_groups'])
def set_groups(message):
    user_id = message.chat.id
    log.debug("Begin /set_groups for " + str(user_id))
    set_params(user_id)
    grp = message.text[len('/set_groups '):]
    grps = grp.split()
    grps2 = []
    for el in grps:
        if config.table_links_dict.get(el, -1) != -1:
            grps2.append(el)
    params['groups'] = grps2
    save_params(user_id) # сохраняем в файл(но получается, что оно сбрасывается каждые 24 часа)
    bot.send_message(user_id, "Новый список групп = " + str(grps2))
    log.debug("End /set_groups for " + str(user_id))


@bot.message_handler(commands=['list_groups'])
def list_groups(message):
    user_id = message.chat.id
    log.debug("In /list_groups")
    bot.send_message(user_id, "Доступные группы:\n" + '\n'.join(config.groups))


@bot.message_handler(commands=['get_groups'])
def get_groups(message):
    user_id = message.chat.id
    set_params(user_id)
    log.debug("In /get_groups for " + str(user_id))
    bot.send_message(user_id, "Группы этого аккаунта:\n" + '\n'.join(params.get('groups', ['(их нет)'])))


# TODO Искать параллели автоматически!
@bot.message_handler(commands=['start'])
def find_id(message): # ищет чела по фамилии
    user_id = message.chat.id
    log.debug("Begin /start for " + str(user_id))
    set_params(user_id)
    # table = requests.get(config.table_link, proxyDict).json() # делаем запрос на табличку
    name = message.text[len('/start '):] # 300iq способ определить параметр, который нам передали)
    if not name: # если имя пустое, то вывести справку
        log.debug("End /start for " + str(user_id) + " -- empty name specified")
        show_help(message)
        return
    bot.send_message(user_id, 'Идет поиск по таблицам... 少々お待ちください. Команды, вызванные до окончания поиска могут отрабатывать неправильно или вообще не выполняться.')
    grps2 = []
    for gid in config.groups:
        for table_link in config.table_links_dict.get(gid, ''):
            try:
                table = requests.get(table_link, proxyDict).json() # делаем запрос на табличку
            except:
                e = sys.exc_info()[0]
                print("Error: %s"%e)
                log.error("Error: %s"%e)
                print(traceback.format_exc())
                log.error(traceback.format_exc())
                print('[' + gid + '], ' + table_link)
                log.error('[' + gid + '], ' + table_link)
            # 300iq способ получать tinkoff id на табличку
            for user in table['users']:
                if (user['name'] == name):
                    grps2.append(gid)
                    break
    grps2 = list(set(grps2))
    if not grps2:
        log.debug("End /start for " + str(user_id) + " -- not found")
        bot.send_message(user_id, "Поиск закончен. Тебя нет в табличке. Введи `/start <Имя из таблицы>`. Настройки не изменены.")
        return
    params['name'] = name
    params['groups'] = grps2
    bot.send_message(user_id, "Поиск закончен. id = `%s` установлен, все ок\n"%name + "Автоопределен список групп: " + str(grps2))
    save_params(user_id) # сохраняем в файл(но получается, что оно сбрасывается каждые 24 часа)
    log.debug("End /start for " + str(user_id))


# TODO разобраться....
@bot.message_handler(commands=['info'])
def show_info(message):# ну короче я хотел сделать, чтобы можно было всем отправить рассылку об обновлении бота
    f = open("info.txt", "r", encoding="utf-8")
    s = f.read()
    bot.send_message(message.chat.id, s)

@bot.message_handler(commands=['reboot'])
def reboot(message):
    user_id = message.chat.id
    if user_id not in config.admins: return
    bot.send_message(user_id, "Перезапуск бота. Бот заработает ~5 секунд")
    log.info("Bot have rebooted by %s" % user_id)
    os.system("python3 " + config.paths['reboot_script'])


# К этому моменту мы подгрузили все, что надо для бота и теперь запускаем его.
log.info('End initialize bot. Start polling')
bot.polling()
log.info('Stop polling')
