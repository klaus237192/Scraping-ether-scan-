from multiprocessing import Process

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ActionChains
import pandas as pd
import re
from config import BASE_URL
from asyncio import sleep
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--force-dark-mode")
chrome_options.add_argument("--start-maximized")


async def startScraping(COIN_CONTRACTS, INPUT_VALUE, wallet_collection):
    wallets = [[] for j in range(len(COIN_CONTRACTS))]
    outputs = [[] for j in range(len(COIN_CONTRACTS))]
    wallets_for_outputs = [[] for j in range(len(COIN_CONTRACTS))]
    try:
        driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, )
        actions=ActionChains(driver)

        for j, coin_contract in enumerate(COIN_CONTRACTS):
            existing_wallet_address_count=0
            existing_state=True
            previous_count=0
            try:
                wallet_document=await wallet_collection.find_one({"coin_contract":coin_contract})
                if wallet_document is None:
                    existing_state=False
                else:
                    existing_wallet_address_count=len(wallet_document["wallet_addresses"])
                    previous_count=existing_wallet_address_count
                    if int(INPUT_VALUE) >= existing_wallet_address_count:
                        wallets_for_outputs[j]=wallet_document["wallet_addresses"]
                    else:
                        wallets_for_outputs[j]=wallet_document["wallet_addresses"][:int(INPUT_VALUE)]
            except Exception as e:
                existing_state=False
                print(e)
            remained_count=int(INPUT_VALUE)-existing_wallet_address_count
            print("--------------------->remained_count\n", remained_count)
            if remained_count <= 0:
                continue
            driver.get(f"{BASE_URL}/dex?q={coin_contract}#transactions")
            await sleep(0.1)
            driver.execute_script("window.scrollBy(0,5000)")
            await sleep(2)
            try:
                txs_frame=driver.find_element(By.ID,"txnsiframe")
                driver.switch_to.frame(txs_frame)
            except Exception as e:
                print("Finding the txs frame...")
            try:
                driver.find_element(By.ID,"ddlRecordsPerPage").click()
                actions.send_keys(Keys.DOWN).perform()
                actions.send_keys(Keys.DOWN).perform()
                actions.send_keys(Keys.ENTER).perform()
                await sleep(1)
            except Exception as e:
                print("Finding the count element...")
            try:
                pagination_element=driver.find_element(By.CSS_SELECTOR,"ul.pagination.pagination-sm.mb-0")
                pagination_element.find_elements(By.TAG_NAME,"li")[4].click()
                await sleep(1)
            except Exception as e:
                print("Moving to the final page...")
            count=0
            complete_state=False
            while True:
                try:
                    trade_elements=driver.find_element(By.TAG_NAME,"tbody").find_elements(By.TAG_NAME,"tr")
                    print(len(trade_elements))
                    list_board=driver.current_window_handle
                except Exception as e:
                    print("Finding the trade elements...")
                count_for_scrolling=0
                for trade_element in trade_elements:
                    method=""
                    try:
                        method=trade_element.find_elements(By.TAG_NAME,"td")[5].text
                    except Exception as e:
                        print(e)
                    if existing_wallet_address_count == 0:
                        if method=="Buy":
                            try:
                                hash_element=trade_element.find_elements(By.TAG_NAME,"td")[1]
                                actions.key_down(Keys.CONTROL).perform()
                                hash_element.click()
                                actions.key_up(Keys.CONTROL).perform()
                            except Exception as e:
                                print("Finding the hash element...")
                            try:
                                trade_page=driver.window_handles[-1]
                                driver.switch_to.window(trade_page)
                                await sleep(1)
                                wallet_address=driver.find_elements(By.CSS_SELECTOR, "a.js-clipboard.link-secondary")[1]
                                print(f"{count}----->",wallet_address.get_attribute("data-clipboard-text"))
                            except Exception as e:
                                print("Moving to the transaction page...")
                            wallets[j].append(wallet_address.get_attribute("data-clipboard-text"))
                            wallets_for_outputs[j].append(wallet_address.get_attribute("data-clipboard-text"))
                            driver.close()
                            try:
                                driver.switch_to.window(list_board)
                                driver.execute_script("window.scrollBy(0,47)")
                                await sleep(0.05)
                                driver.switch_to.frame(txs_frame)
                            except Exception as e:
                                print("Scroll downing...")
                            count+=1
                            if count==remained_count:
                                complete_state=True
                                break
                        else:
                            try:
                                driver.switch_to.default_content()
                                driver.execute_script("window.scrollBy(0,47)")
                                await sleep(0.05)
                                driver.switch_to.frame(txs_frame)
                            except Exception as e:
                                print("Scrolling downing")
                    else:
                        if method == "Buy":
                            existing_wallet_address_count-=1
                            print("existing_wallet_address_count----->",existing_wallet_address_count)
                        count_for_scrolling+=1
                        if existing_wallet_address_count == 0:
                            driver.switch_to.default_content()
                            scroll_amount=count_for_scrolling*47
                            driver.execute_script(f"window.scrollBy(0,{scroll_amount})")
                            await sleep(1)
                            driver.switch_to.frame(txs_frame)
                # await sleep(1)            
                if complete_state==True:
                    break
                try:
                    driver.switch_to.default_content()
                    driver.execute_script("window.scrollBy(0,-5000)")
                    print("----------------------------------------------------------------")
                    await sleep(1)
                    driver.switch_to.frame(txs_frame)
                    pagination_element=driver.find_element(By.CSS_SELECTOR,"ul.pagination.pagination-sm.mb-0")
                    pagination_element.find_elements(By.TAG_NAME,"li")[1].click()
                    await sleep(1)

                except Exception as e:
                    print("Clicking the previous page button...")
            if existing_state == False:
                try:
                    wallet_document=await wallet_collection.find_one({"coin_contract":coin_contract})
                    if wallet_document is not None:
                        if len(wallet_document) <= len(wallets[j]):
                            await wallet_collection.update_one({"coin_contract":coin_contract}, {"$set":{"wallet_addresses":wallets[j]}})
                    else:
                        await wallet_collection.insert_one({"coin_contract":coin_contract, "wallet_addresses":wallets[j]})
                except Exception as e:
                    print("Error occured while database updating")
            else:
                wallet_document=await wallet_collection.find_one({"coin_contract":coin_contract})
                current_count=len(wallet_document["wallet_addresses"])
                diff=current_count-previous_count
                if diff<len(wallets[j]):
                    await wallet_collection.update_one({"coin_contract":coin_contract},{"$push": {"wallet_addresses": {"$each": wallets[j][diff:]}}})
            driver.switch_to.default_content()
        updated_wallets=[]
        for row in wallets_for_outputs:
            unique_row=list(set(row))
            print("--------------------->The each length of removed array\n",len(unique_row))
            updated_wallets.append(unique_row)

        added_updated_wallets=[element for sublist in updated_wallets for element in sublist]
        print("--------------------->The length of added_updated_wallets\n",len(added_updated_wallets))
        unique_added_updated_wallets=list(set(added_updated_wallets))
        print("--------------------->The length of unique_added_updated_wallets\n",len(unique_added_updated_wallets))
        for unique_wallet in unique_added_updated_wallets:
            count=0
            for wallets_array in updated_wallets:
                if unique_wallet in wallets_array:
                    count+=1
            outputs[count-1].append(unique_wallet)
        results=""
        with open("results.txt","a") as file:
            title="***************************Coin contracts used for getting results******************************\n"
            for coin_contract in COIN_CONTRACTS:
                title+=coin_contract+","
            title+="\n"
            title+=f"******************************Results for {int(INPUT_VALUE)} wallet addresses**********************************\n"
            file.write(title)
            for i in range(len(COIN_CONTRACTS)-1):
                file.write(f"-------------------->Bought {i+2}/{len(COIN_CONTRACTS)} coins<---------------------\n")
                results+=f"-------------------->Bought {i+2}/{len(COIN_CONTRACTS)} coins<---------------------\n"
                for result in outputs[i+1]:
                    file.write(result+"\n")
                    results+=result+"\n"
            file.write("\n\n\n\n\n")
        driver.close()
        return results
    except Exception as e:
        driver.close()
        return "Something went wrong, please try again later"