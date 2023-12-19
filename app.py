from telebot.async_telebot import AsyncTeleBot
import telebot
import re
import asyncio
from scraper import startScraping
import time
from dotenv import load_dotenv
import os
from db import add_admin
from db import is_paid_user
from db import connect_db
load_dotenv()
bot=None

MONGO_URL=os.getenv("MONGO_URL")

try:
    bot = AsyncTeleBot("6660186278:AAHHvTb5RJ97R4rQt435aUuXSAIzhMV2dgw")
except Exception as e:
    print("There is no channel with that token")
wallet_collection=None
@bot.message_handler(commands=['start'])
async def start_command(message):
    try:
        USERNAME=message.from_user.username
        is_paid=await is_paid_user(MONGO_URL,USERNAME)
        print(is_paid)
        if is_paid:
            await bot.send_message(
                message.chat.id,
                'Welcome to this channel. From now on, You can\n' +
                'get the wallet addresses according to the coin\n' +
                'contracts and input value.Please send me the coin\n' +
                'addresses and the number of wallet addresses you\n' +
                'want to analyze separating by commas.'
            )
            await bot.send_message(
                message.chat.id,
                'For example\n' +
                '0x8390a1da07e376ef7add4be859ba74fb83aa02d5,0x62d0a8458ed7719fdaf978fe5929c6d342b0bfce,0xa0dd6dd7775e93eb842db0aa142c9c581031ed3b,30'
            )
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            button = telebot.types.InlineKeyboardButton("Contact with owner", url="telegram.me/dreaming150")
            keyboard.add(button)
            await bot.send_message(
                message.chat.id,
                'Welcome to this channel. To use this channel,\n' +
                'please contact and pay to the owner.',
                reply_markup=keyboard
            )
    except Exception as e:
        print(e)
@bot.message_handler(func=lambda message: True)
async def send_results(message):
    try:
        coin_contracts = message.text.split(",")
        valid_coin_addresses = []
        INPUT_VALUE = 0
        is_validate = True
        USERNAME=message.from_user.username
        is_paid=await is_paid_user(MONGO_URL,USERNAME)
        if is_paid:
            for i, coin_contract in enumerate(coin_contracts):
                coin_contract = re.sub(r'\s', '', coin_contract)
                if i != len(coin_contracts) - 1:
                    valid_coin_addresses.append(coin_contract)
                    if coin_contract.startswith("0x") and len(coin_contract) == 42:
                        continue
                    else:
                        is_validate = False
                        break
                else:
                    if coin_contract.isdigit():
                        INPUT_VALUE = int(coin_contract)
                        continue
                    else:
                        is_validate = False

            if is_validate:
                await bot.reply_to(message, "Please wait...")
                results =await startScraping(valid_coin_addresses, INPUT_VALUE, wallet_collection)
                if results != "":
                    await bot.reply_to(message, results)
                else:
                    await bot.reply_to(message,"You must input at least one address")
            else:
                await bot.reply_to(message, "Something went wrong, please input again")
        else:
            keyboard = telebot.types.InlineKeyboardMarkup()
            button = telebot.types.InlineKeyboardButton("Contact with owner", url="telegram.me/dreaming150")
            keyboard.add(button)
            await bot.send_message(
                message.chat.id,
                'Welcome to this channel. To use this channel,\n' +
                'please contact and pay to the owner.',
                reply_markup=keyboard
            )
    except Exception as e:
        print(e)
        

if __name__ == "__main__":
    try:
        MONGO_URL=os.getenv('MONGO_URL')
        print("connecting to database synchronizly...")
        add_admin(MONGO_URL)
        print("Admin was added to database")
        print("Connection was closed")
        print("connecting to database asynchronizly...")
        wallet_collection=connect_db(MONGO_URL)
        print("Mongodb connected")
    except Exception as e:
        print("Failed to connect to database")
    # loop=asyncio.get_event_loop()
    # loop.create_task(bot.polling())
    # loop.run_forever()
    asyncio.run(bot.polling())