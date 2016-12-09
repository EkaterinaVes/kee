# -*- coding: utf-8 -*-
import config
import telebot
import requests
from bs4 import BeautifulSoup
from datetime import datetime

bot = telebot.TeleBot(config.token)


def get_page(group, week=''):
    if week:
        week = str(week) + '/'
    url = '{domain}/{group}/{week}/raspisanie_zanyatiy_{group}.htm'.format(
        domain='http://www.ifmo.ru/ru/schedule/0', 
        week=week, 
        group=group)
    response = requests.get(url)
    web_page = response.text
    return web_page

di = {'monday': '1day', 'tuesday':'2day','wednesday':'3day','thursday': '4day','friday': '5day', 'saturday':'6day', 'sunday': '7day'}
we = {'even': 1,'odd': 2}

def get_schedule(web_page, day_of_week):
    soup = BeautifulSoup(web_page, "html5lib")
    # Получаем таблицу с расписанием на понедельник
    schedule_table = soup.find("table", attrs={"id": day_of_week})
    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.span.text for room in locations_list]

    # Название дисциплин и имена преподавателей
    lessons_list1 = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list1 = [lesson.text.split('\n\n') for lesson in lessons_list1]
    lessons_list1 = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list1]
    lessons_list2 = []
    lessons_list = []
    for i in range(len(lessons_list1)):
        lessons_list2.append(lessons_list1[i].replace('\t', ''))
        lessons_list.append(lessons_list2[i].replace('\n', ''))

    rooms_list = schedule_table.find_all("td", attrs={"class": "room"})
    rooms_list = [room.dd.text for room in rooms_list]
    return times_list, locations_list, lessons_list, rooms_list


def what_week(week, day_w):
    if week % 2 == 0:week = 1
    else: week = 2
    if day_w == '7day': 
        day_w = '1day'
        if week == 1: week = 2
        else: week = 1
    return week


@bot.message_handler(commands=['monday','tuesday','wednesday','thursday','friday','saturday'])
def get_day(message):
    day,week, group = message.text.split()
    for key in di.keys():
        if key == day:
            day = di.get(key)
    print(day)
    for key in we.keys():
        if week == key:
            num_week = we.get(key)
    web_page = get_page(group,num_week)
    times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, day)
    resp = ''
    for time, location, lession, room in zip(times_lst, locations_lst, lessons_lst, rooms_lst):
        resp += '<b>{}</b>, {}, {},{}\n'.format(time, room, location, lession)

    bot.send_message(message.chat.id, resp, parse_mode='HTML')



@bot.message_handler(commands=['nearlesson'])

def get_near_lesson(message):
    _, group = message.text.split()
    n = datetime.today()
    n = datetime.isocalendar(n)
    time = str(datetime.time(datetime.now()))[0:5]
    hour_now = int(time[:2])
    minute_now = int(time[3:])
    day_w = str(n[2]) + 'day'
    print(day_w)
    week = what_week(n[1], day_w)
    web_page = get_page(group, week)
    if day_w == '7day':
        times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, '1day')
        resp='<b>{}</b>, {}, {},{}\n'.format(times_lst[0], rooms_lst[0], locations_lst[0], lessons_lst[0])
    times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, day_w)
    times_hour = []
    times_minute = []
    for i in range(len(times_lst)):
        t=times_lst[i][:5]
        if t[-1] == '-': 
            t=t[:-1]
        h ,m = t.split(':')
        times_hour.append(int(h))
        times_minute.append(int(m))
    for k in range(len(times_hour)):
        if hour_now < times_hour[k]:
            resp = '<b>{}</b>, {}, {},{}\n'.format(times_lst[k], rooms_lst[k], locations_lst[k], lessons_lst[k])
            break
        if hour_now == times_hour[k]:
            if minute_now <= times_minute[k]:
                resp = '<b>{}</b>, {}, {},{}\n'.format(times_lst[k], rooms_lst[k], locations_lst[k], lessons_lst[k])
                break
    if hour_now>times_hour[-1]:
        if day_w == '6day':
            times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, '1day')
            resp='<b>{}</b>, {}, {},{}\n'.format(times_lst[0], rooms_lst[0], locations_lst[0], lessons_lst[0])
        else:
            times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, '{}day'.format(int(day_w[0])+1))
            resp='<b>{}</b>, {}, {},{}\n'.format(times_lst[0], rooms_lst[0], locations_lst[0], lessons_lst[0])
    bot.send_message(message.chat.id, resp, parse_mode='HTML')

@bot.message_handler(commands=['tomorrow'])

def get_tomorrow(message):
    _, group = message.text.split()
    n = datetime.today()
    n = datetime.isocalendar(n)
    day_w = str(n[2]+1) + 'day'
    week = what_week(n[1], day_w)
    web_page = get_page(group, week)
    times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, day_w)
    resp = ''
    for time, location, lession, room in zip(times_lst, locations_lst, lessons_lst, rooms_lst):
        resp += '<b>{}</b>, {}, {},{}\n'.format(time, room, location, lession)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')

@bot.message_handler(commands=['all'])
def get_all_week(message):
    _,week, group = message.text.split()
    for key in we.keys():
        if week == key:
            num_week = we.get(key)
    web_page = get_page(group,num_week)
    resp = ''
    for i in range(1,7):
        day = str(i)+'day'
        times_lst, locations_lst, lessons_lst, rooms_lst = get_schedule(web_page, day)
        #di = {'monday': '1day', 'tuesday':'2day','Wednesday':'3day','Thursday': '4day','Friday': '5day', 'Saturday':'6day'}
        for key in di.keys():
            if di.get(key) == day:
                day = key
        resp += '\n\n'+day+'\n'
        for time, location, lession, room in zip(times_lst, locations_lst, lessons_lst, rooms_lst):
            resp += '<b>{}</b>, {}, {},{}\n'.format(time, room, location, lession)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')

if __name__ == '__main__':
    bot.polling(none_stop=True)