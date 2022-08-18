import json
from web3 import Web3
from web3.logs import STRICT, IGNORE, DISCARD, WARN
from typing import List
from multiprocessing import Process, pool
from math import *
# import pandas as pd
import requests
from ast import literal_eval
import time
import decimal
import schedule
import os
from dotenv import load_dotenv
import urllib.parse 
import telebot
import logging

start_time = time.time()

load_dotenv()
API_KEY = os.getenv('API_KEY')
FX_RPC = os.getenv('FX_RPC')
bot = telebot.TeleBot(API_KEY)

def connectRPX():
    #Connect Ethereum node 
    # web3 = Web3(Web3.HTTPProvider("https://eth-mainnet.functionx.io"))
    global web3
    web3 = Web3(Web3.HTTPProvider(FX_RPC))
    # print(web3.isConnected())

def queryData():
    global totalSupplyFX
    global totalSupplyPundiX
    global fxCoreLockedFx
    global ethereumFXTSupply
    global ethereumLockedPundiX
    global fxCorePundiXSupply
    global fxCoreBlockHeight

    # Load token abi data
    full_path = os.getcwd()
    erc20Json = open(full_path+'/abis/'+'fx.json')      
    erc20Abi = json.load(erc20Json)                 

    # Load contract address
    FX_ETH = '0x8c15Ef5b4B21951d50E53E4fbdA8298FFAD25057'
    PUNDIX_ETH = '0x0FD10b9899882a6f2fcb5c371E17e70FdEe00C38'
    PURSE_BSC = '0x29a63F4B209C29B4DC47f06FFA896F32667DAD2C'
    FxBridgeLogic = '0x6f1D09Fed11115d65E1071CD2109eDb300D80A27'

    fxContract = web3.eth.contract(address=FX_ETH, abi=erc20Abi["abi"])
    pundiXContract = web3.eth.contract(address=PUNDIX_ETH, abi=erc20Abi["abi"])

    supplyResponse = requests.get("https://fx-rest.functionx.io/cosmos/bank/v1beta1/supply")
    lockedFundResponse = requests.get("https://fx-rest.functionx.io/cosmos/bank/v1beta1/balances/fx16n3lc7cywa68mg50qhp847034w88pntquxjmcz")
    latestBlockResponse = requests.get("https://fx-rest.functionx.io/cosmos/base/tendermint/v1beta1/blocks/latest")
    supplyResponse = supplyResponse.json()
    lockedFundResponse = lockedFundResponse.json()
    latestBlockResponseJson = latestBlockResponse.json()

    totalSupplyFX = fxContract.functions.totalSupply().call(block_identifier= 'latest')
    totalSupplyPundiX = pundiXContract.functions.totalSupply().call(block_identifier= 'latest')
    ethereumLockedPundiX = pundiXContract.functions.balanceOf(FxBridgeLogic).call(block_identifier= 'latest')
    
    fxCoreLockedFx = int(lockedFundResponse["balances"][0]["amount"])
    ethereumFXTSupply = int(totalSupplyFX)
    ethereumLockedPundiX = int(ethereumLockedPundiX)
    fxCorePundiXSupply = int(supplyResponse["supply"][1]["amount"])
    fxCoreBlockHeight = latestBlockResponseJson["block"]["header"]["height"]


def buildTelebotMsg():
    global msgResponse

    if ((fxCoreLockedFx > ethereumFXTSupply)):
        fxresult = "Normal"
        fxdescription = "FxCore_Locked_Fx > Ethereum_FX_T.Supply"
        fxdiffAmount = fxCoreLockedFx-ethereumFXTSupply
    elif fxCoreLockedFx < ethereumFXTSupply:
        fxresult = "Warning"
        fxdescription = "FxCore_Locked_Fx < Ethereum_FX_T.Supply"
        fxdiffAmount = fxCoreLockedFx - ethereumFXTSupply
    else:
        fxresult = "Normal"
        fxdescription = "Both side Equal"
        fxdiffAmount = fxCoreLockedFx - ethereumFXTSupply

    if ((ethereumLockedPundiX > fxCorePundiXSupply)):
        pundixresult = "Normal"
        pundixdescription = "Ethereum_Locked_PundiX > FxCore_PundiX_T.Supply"
        pundixdiffAmount = ethereumLockedPundiX-fxCorePundiXSupply
    elif ethereumLockedPundiX < fxCorePundiXSupply:
        pundixresult = "Warning"
        pundixdescription = "Ethereum_Locked_PundiX < FxCore_PundiX_T.Supply"
        pundixdiffAmount = ethereumLockedPundiX-fxCorePundiXSupply
    else:
        pundixresult = "Normal"
        pundixdescription = "Both side Equal"
        pundixdiffAmount = ethereumLockedPundiX-fxCorePundiXSupply

    rows0 = [fxCoreLockedFx,fxCorePundiXSupply]
    rows1 = [ethereumFXTSupply,ethereumLockedPundiX] 
    msgResponse = "~~~ Fx Bridge Daily Report ~~~\n\n"

    msgResponse += f"FxCore Block Height: {fxCoreBlockHeight}\n\n"

    msgResponse += "~~~~ FX ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {int(web3.fromWei(rows0[0], 'ether'))}\n"
    msgResponse += f"{'Ethereum:'.ljust(17)} {int(web3.fromWei(rows1[0], 'ether'))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {fxresult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {fxdescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(fxdiffAmount, 'ether')}\n\n"

    msgResponse += "~~~~ PUNDIX ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {int(web3.fromWei(rows0[1], 'ether'))}\n"
    msgResponse += f"{'Ethereum:'.ljust(17)} {int(web3.fromWei(rows1[1], 'ether'))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {pundixresult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {pundixdescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(pundixdiffAmount, 'ether')}\n"
    
    if pundixresult != 'Normal' or fxresult != 'Normal' :
        bot.send_message('-743912527', msgResponse)

def sentTeleReport():
    bot.send_message('-743912527', msgResponse)



# ######################################################################################

def minCheck():
    try:
        queryData()
    except Exception as e:
        print("Query report Error happen")
        print (e.message, e.args)
        logging.error(e.message)
    else:
        buildTelebotMsg()

def dailyReport():
    try:
        queryData()
    except Exception as e:
        print("Query report Error happen")
        print (e.message, e.args)
        logging.error(e.message)
    else:
        buildTelebotMsg()
        sentTeleReport()

def listenTeleMsg():
    connectRPX()
    try:
        @bot.message_handler(commands=['data'])
        # @bot.message_handler(func=lambda message: True)
        def echo_all(message):
            bot.reply_to(message, "Here comes the latest data...")
            dailyReport()
        bot.infinity_polling()
    except Exception as e:
        print("listenTele Error")
        print (e.message, e.args)
        logging.error(e.message)

def checkReport():
    try:
        queryData()
    except Exception as e:
        print("Query report Error happen")
        print (e.message, e.args)
        logging.error(e.message)
    else:
        buildTelebotMsg()
        sentTeleReport()

def scheduleDailyReport():
    connectRPX()
    schedule.every().minutes.do(minCheck)
    schedule.every().day.at("07:00").do(dailyReport)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    processes = []
    connectRPX()
    queryData()
    buildTelebotMsg()
    sentTeleReport()

    print("--- %s seconds ---" % (time.time() - start_time))
    
    # Multiprocess start
    p = Process(target=scheduleDailyReport)
    p.start()
    processes.append(p)
    p = Process(target=listenTeleMsg)
    p.start()
    
    for p in processes:
        p.join()

if __name__ == "__main__":     # __name__ is a built-in variable in Python which evaluates to the name of the current module.
    main()









# Error:
# 1)raise HTTPError(http_error_msg, response=self)
#   -requests.exceptions.HTTPError: 503 Server Error: Service Temporarily Unavailable for url: https://rpc.ankr.com/eth