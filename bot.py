import asyncio 
import logging
from aiogram import Bot,Dispatcher,types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode,BotCommand
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3

logging.basicConfig(level=logging.INFO)

bot_key=""

linkpars="https://rust.facepunch.com"
linknews= linkpars+"/news"

loop = asyncio.get_event_loop()
bot= Bot(token=bot_key,loop=loop)
dp=Dispatcher(bot)

dp.middleware.setup(LoggingMiddleware())
def psr():
    respons= requests.get(linknews)
    if respons.status_code==200:
        Soup= BeautifulSoup(respons.text,"html.parser")
        pall=Soup.find_all(class_="blog-post-body")
        newslist=[]

        for i in pall[:3]:
            link=urljoin(linkpars,i.find_previous('a',href=True)["href"])
            title=i.find("h1").text.strip()
            desc=i.find("p").text.strip()
            newslist.append({"title":title,"link":link,"desc":desc})   
            return newslist
    else:
        logging.error("ошибка при открытии сылки",respons.status_code)

        return []
async def sendnews(msg:types.Message):
    newslist=psr()
    if not newslist: 
        await msg.answer("к сожелению нету новстей(")
        return
    for i in newslist:
        text = f"<b>{i['title']}</b>\n{i['desc']}\n<a href='{i['link']}'>Докладніше</a>"
        await msg.answer(text,parse_mode=ParseMode.HTML)
@dp.message_handler(commands=["news"])
async def news(msg:types.Message):
    await sendnews(msg)

@dp.message_handler(commands=["help","start"])
async def help(msg:types.Message):
    await msg.reply("привет я бот по новостям и информации по игре rust напиши /news для  получения новостей ")

def create_table():
    conn= sqlite3.connect("items.db")
    cursor=conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS items(
                   id INTEGER primary key,
                   name VARCHAR (255),
                   type VARCHAR (255),
                   desc VARCHAR (255)
    )""")
    conn.commit()
    conn.close()
def add_item(name,type,desc):
    conn= sqlite3.connect("items.db")
    cursor=conn.cursor()
    cursor.execute("""INSERT INTO items (name, type, desc)VALUES(?,?,?)""",(name,type,desc))
    conn.commit()
    conn.close()
def get_item(name):
    conn= sqlite3.connect("items.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT * FROM items WHERE name = ? """,(name,))
    item=cursor.fetchone()
    conn.close()
    return item
def get_items():
    conn= sqlite3.connect("items.db")
    cursor=conn.cursor()
    cursor.execute("""SELECT * FROM items""")
    items=cursor.fetchall()
    conn.close()
    return items
async def send_info(msg:types.Message):
    name=msg.get_args()
    info=get_item(name)
    if info:
        respons= f"<b>{info[1]}</b>\n\n<b>Type:</b> {info[2]}\n\n{info[3]}"
    else:
        respons="предмет не найден"
    await msg.reply (respons,parse_mode=ParseMode.HTML)

@dp.message_handler(commands=["item"])
async def item(msg:types.Message):
    await  send_info(msg)

@dp.message_handler(commands=["addd_item"])
async def addd_item(msg:types.Message):
    info=msg.get_args().split(",")
    if len(info)==3:
        name,type,desc=info
        add_item(name.strip(),type.strip(),desc.strip())
        await msg.reply("успешно добавленно")
    else: 
        await msg.reply("не правильный формат ")

@dp.message_handler(commands=["all_items"])
async def all_items(msg:types.Message):
    items=get_items()
    if items:
        respons="все предметы:\n"
        for weapon in items:
            respons += f"<b>{weapon[1]}</b>\nType: {weapon[2]}\nDescription: {weapon[3]}\n\n"
    else:
        respons="предметы не найдены добавьте их или ожидайте обновления"
    await msg.reply(respons,parse_mode=ParseMode.HTML)

@dp.message_handler(commands=["delete_item"])
async def delete_item(msg:types.Message):
    name=msg.get_args()
    info= get_item(name)
    if info:
        conn=sqlite3.connect("items.db")
        cursor=conn.cursor()
        cursor.execute("DELETE FROM items WHERE name=?",(name,))
        conn.commit()
        conn.close()
        await msg.reply("предмет(ы) успешно удален(ны)!")
    else:
        await msg.reply("не удалось удалить предмет(ы)")

@dp.message_handler(commands=["update_item"])
async def update_item(msg:types.Message): 
    info=msg.get_args().split(",")
    if len(info)==3:
        name,type,desc=info
        item=get_item(name.strip())
        if item:
            conn=sqlite3.connect("items.db")
            cursor=conn.cursor()
            cursor.execute("UPDATE items SET type=?,desc=? WHERE name=?",(type.strip(),desc.strip(),name.strip()))
            conn.commit()
            conn.close()
            await msg.reply("предмет успешно изменен")
        else:
            await msg.reply("неудалось изменить предмет повторите попытку")
    else:
        await msg.reply("напишите в формате: имя,тип,описание")

def deletetype_item(type):
    conn=sqlite3.connect("items.db")
    cursor=conn.cursor()
    cursor.execute("""DELETE FROM items WHERE type=?""",(type,))
    conn.commit()
    conn.close()

@dp.message_handler(commands=["deletype_item"])
async def deletype_item(msg:types.Message): 
    info=msg.get_args().strip()
    deletetype_item(info)
    await msg.reply("предметы с этим типом успешно удаленны!")


async def set_bot_commands(dp):
    commands=[
        BotCommand(command="/all_items",description="выводит все предметы")
    ]
    await dp.bot.set_my_commands(commands)
if __name__ == "__main__":
    loop.run_until_complete(set_bot_commands(dp))
    loop.run_until_complete(dp.start_polling())