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
from tronpy import Tron
from tronpy.providers import HTTPProvider

# from tronpy.providers import HTTPProvider

# ######################################################################################
# Load basic variable
# ######################################################################################

start_time = time.time()

load_dotenv()
API_KEY = os.getenv('API_KEY')
TELE_CHAT_ID = os.getenv('TELE_CHAT_ID')
# TELE_CHAT_ID = os.getenv('TELE_TEST_CHAT_ID')

# ######################################################################################
# Build core function
# ######################################################################################

def connectRPX():
    global bot
    global web3
    global web3Bsc
    global web3Poly
    global web3Tron

    web3 = Web3(Web3.HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/h46tf7QGoc6jpx8nO0GrGoB6MumXB-u1"))
    web3Bsc = Web3(Web3.HTTPProvider("https://rpc.ankr.com/bsc"))
    web3Poly = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/3xrrqeRSaeafPT1HHuyhDgvCg6ZYDONy"))
    web3Tron = Tron(HTTPProvider(api_key=["4f00d781-181a-414e-80fe-ec682fd1df72"]))

    bot = telebot.TeleBot(API_KEY)
    print(web3.isConnected())
    print(web3Bsc.isConnected())
    print(web3Poly.isConnected())
    # print(web3Tron.is_address(str('TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')))

def loadContract():
    global fxContract
    global pundiXContract
    global purseContract
    global usdtEthereumContract
    global usdtPolyContract
    global usdtTronContract

    # Load token abi data
    full_path = os.getcwd()
    erc20Json = open(full_path+'/abis/'+'fx.json')      
    erc20Abi = json.load(erc20Json)                 

    # Token address
    FX_ETH = '0x8c15Ef5b4B21951d50E53E4fbdA8298FFAD25057'
    PUNDIX_ETH = '0x0FD10b9899882a6f2fcb5c371E17e70FdEe00C38'
    PURSE_BSC = '0x29a63F4B209C29B4DC47f06FFA896F32667DAD2C'
    USDT_ETH = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
    USDT_POLY = '0xc2132D05D31c914a87C6611C10748AEb04B58e8F'
    USDT_TRON = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'

    fxContract = web3.eth.contract(address=FX_ETH, abi=erc20Abi["abi"])
    pundiXContract = web3.eth.contract(address=PUNDIX_ETH, abi=erc20Abi["abi"])
    purseContract = web3Bsc.eth.contract(address=PURSE_BSC, abi=erc20Abi["abi"])
    usdtEthereumContract = web3.eth.contract(address=USDT_ETH, abi=erc20Abi["abi"])
    usdtPolyContract = web3Poly.eth.contract(address=USDT_POLY, abi=erc20Abi["abi"])
    usdtTronContract = web3Tron.get_contract(USDT_TRON)

def queryData():
    global totalSupplyFX
    global ethereumFXTSupply
    global ethereumLockedPundiX
    global ethereumLockedUSDT
    global polygonLockedUSDT
    global tronLockedUSDT

    global fxCoreLockedFx
    global fxCorePundiXSupply
    global fxCoreBlockHeight
    global fxCorePolyUSDTSupply
    global fxCoreTronUSDTSupply
    global fxCoreEthereumUSDTSupply

    # Bridge Address
    FxBridgeLogic_Ethereum = '0x6f1D09Fed11115d65E1071CD2109eDb300D80A27'
    FxBridgeLogic_Polygon = '0x4052eA614c5a96631C546d8B8d323a7C3D9ABb69'
    FxBridgeLogic_Tron = 'TKLDunqAynYcXRktcYHqncp3R6nJeEXLd5'

    supplyResponse = requests.get("https://fx-rest.functionx.io/cosmos/bank/v1beta1/supply")
    lockedFundResponse = requests.get("https://fx-rest.functionx.io/cosmos/bank/v1beta1/balances/fx16n3lc7cywa68mg50qhp847034w88pntquxjmcz")
    latestBlockResponse = requests.get("https://fx-rest.functionx.io/cosmos/base/tendermint/v1beta1/blocks/latest")
    supplyResponse = supplyResponse.json()
    lockedFundResponse = lockedFundResponse.json()
    latestBlockResponseJson = latestBlockResponse.json()

    totalSupplyFX = fxContract.functions.totalSupply().call(block_identifier= 'latest')
    ethereumLockedPundiX = pundiXContract.functions.balanceOf(FxBridgeLogic_Ethereum).call(block_identifier= 'latest')
    ethereumLockedUSDT = usdtEthereumContract.functions.balanceOf(FxBridgeLogic_Ethereum).call(block_identifier= 'latest')
    polygonLockedUSDT = usdtPolyContract.functions.balanceOf(FxBridgeLogic_Polygon).call(block_identifier= 'latest')
    tronLockedUSDT = usdtTronContract.functions.balanceOf(FxBridgeLogic_Tron)

    ethereumFXTSupply = int(totalSupplyFX)
    ethereumLockedPundiX = int(ethereumLockedPundiX)
    ethereumLockedUSDT = int(ethereumLockedUSDT)
    polygonLockedUSDT = int(polygonLockedUSDT)

    fxCoreBlockHeight = latestBlockResponseJson["block"]["header"]["height"]
    fxCoreLockedFx = int(lockedFundResponse["balances"][0]["amount"])

    for x in supplyResponse["supply"]:
        if x["denom"] == "eth0x0FD10b9899882a6f2fcb5c371E17e70FdEe00C38":
            fxCorePundiXSupply = int(x["amount"])
        elif x["denom"] == "polygon0xc2132D05D31c914a87C6611C10748AEb04B58e8F":
            fxCorePolyUSDTSupply = int(x["amount"])
        elif x["denom"] == "tronTR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t":
            fxCoreTronUSDTSupply = int(x["amount"])
        elif x["denom"] == "eth0xdAC17F958D2ee523a2206206994597C13D831ec7":
            fxCoreEthereumUSDTSupply = int(x["amount"])

def buildTelebotMsg():
    global msgResponse
    global overallResult
    
    # FunctionX token
    if ((fxCoreLockedFx > ethereumFXTSupply)):
        fxResult = "Normal"
        fxDescription = "FxCore_Locked_Fx > Ethereum_FX_T.Supply"
        fxDiffAmount = abs(fxCoreLockedFx-ethereumFXTSupply)
    elif fxCoreLockedFx < ethereumFXTSupply:
        fxResult = "Warning"
        fxDescription = "FxCore_Locked_Fx < Ethereum_FX_T.Supply"
        fxDiffAmount = abs(fxCoreLockedFx - ethereumFXTSupply)
    else:
        fxResult = "Normal"
        fxDescription = "Both side Equal"
        fxDiffAmount = abs(fxCoreLockedFx - ethereumFXTSupply)

    # PundiX token
    if ((ethereumLockedPundiX > fxCorePundiXSupply)):
        pundixResult = "Normal"
        pundixDescription = "Ethereum_Locked_PundiX > FxCore_PundiX_T.Supply"
        pundixDiffAmount = abs(ethereumLockedPundiX-fxCorePundiXSupply)
    elif ethereumLockedPundiX < fxCorePundiXSupply:
        pundixResult = "Warning"
        pundixDescription = "Ethereum_Locked_PundiX < FxCore_PundiX_T.Supply"
        pundixDiffAmount = abs(ethereumLockedPundiX-fxCorePundiXSupply)
    else:
        pundixResult = "Normal"
        pundixDescription = "Both side Equal"
        pundixDiffAmount = abs(ethereumLockedPundiX-fxCorePundiXSupply)

    # Polygon_USDT token
    if ((polygonLockedUSDT > fxCorePolyUSDTSupply)):
        polyUSDTResult = "Normal"
        polyUSDTDescription = "Polygon_Locked_USDT > FxCore_USDT_T.Supply"
        polyUSDTDiffAmount = abs(polygonLockedUSDT-fxCorePolyUSDTSupply)
    elif polygonLockedUSDT < fxCorePolyUSDTSupply:
        polyUSDTResult = "Warning"
        polyUSDTDescription = "Polygon_Locked_USDT < FxCore_USDT_T.Supply"
        polyUSDTDiffAmount = abs(polygonLockedUSDT-fxCorePolyUSDTSupply)
    else:
        polyUSDTResult = "Normal"
        polyUSDTDescription = "Both side Equal"
        polyUSDTDiffAmount = abs(polygonLockedUSDT-fxCorePolyUSDTSupply)

    # Tron_USDT token
    if ((tronLockedUSDT > fxCoreTronUSDTSupply)):
        tronUSDTResult = "Normal"
        tronUSDTDescription = "Tron_Locked_USDT > Tron_USDT_T.Supply"
        tronUSDTDiffAmount = abs(tronLockedUSDT-fxCoreTronUSDTSupply)
    elif tronLockedUSDT < fxCoreTronUSDTSupply:
        tronUSDTResult = "Warning"
        tronUSDTDescription = "Tron_Locked_USDT < Tron_USDT_T.Supply"
        tronUSDTDiffAmount = abs(tronLockedUSDT-fxCoreTronUSDTSupply)
    else:
        tronUSDTResult = "Normal"
        tronUSDTDescription = "Both side Equal"
        tronUSDTDiffAmount = abs(tronLockedUSDT-fxCoreTronUSDTSupply)

    # Ethereum_USDT token
    if ((ethereumLockedUSDT > fxCoreEthereumUSDTSupply)):
        ethereumUSDTResult = "Normal"
        ethereumUSDTDescription = "Ethereum_Locked_USDT > Ethereum_USDT_T.Supply"
        ethereumUSDTDiffAmount = abs(ethereumLockedUSDT-fxCoreEthereumUSDTSupply)
    elif ethereumLockedUSDT < fxCoreEthereumUSDTSupply:
        ethereumUSDTResult = "Warning"
        ethereumUSDTDescription = "Ethereum_Locked_USDT < Ethereum_USDT_T.Supply"
        ethereumUSDTDiffAmount = abs(ethereumLockedUSDT-fxCoreEthereumUSDTSupply)
    else:
        ethereumUSDTResult = "Normal"
        ethereumUSDTDescription = "Both side Equal"
        ethereumUSDTDiffAmount = abs(ethereumLockedUSDT-fxCoreEthereumUSDTSupply)

    #### Build result msg ####
    if pundixResult == 'Normal' and fxResult == 'Normal' and polyUSDTResult == 'Normal' and tronUSDTResult == 'Normal' and ethereumUSDTResult == 'Normal':
        overallResult = "All Normal"
    else:
        overallResult = "Warning"

    rows0 = [fxCoreLockedFx,fxCorePundiXSupply,fxCoreEthereumUSDTSupply,fxCorePolyUSDTSupply,fxCoreTronUSDTSupply]
    rows1 = [ethereumFXTSupply,ethereumLockedPundiX,ethereumLockedUSDT,polygonLockedUSDT,tronLockedUSDT]
    msgResponse = "~~~ FxCore Bridge Daily Report ~~~\n\n"

    msgResponse += f"FxCore Bridge health: {overallResult}\n\n"
    msgResponse += f"FxCore Block Height: {fxCoreBlockHeight}\n\n"

    msgResponse += "~~~~ FX ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {int(web3.fromWei(rows0[0], 'ether'))}\n"
    msgResponse += f"{'Ethereum:'.ljust(17)} {int(web3.fromWei(rows1[0], 'ether'))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {fxResult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {fxDescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(fxDiffAmount, 'ether')}\n\n"

    msgResponse += "~~~~ PUNDIX ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {int(web3.fromWei(rows0[1], 'ether'))}\n"
    msgResponse += f"{'Ethereum:'.ljust(17)} {int(web3.fromWei(rows1[1], 'ether'))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {pundixResult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {pundixDescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(pundixDiffAmount, 'ether')}\n\n"
    
    msgResponse += "~~~~ ETH-USDT ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {'{:.3f}'.format(float(web3.fromWei(rows0[2], 'mwei')))}\n"
    msgResponse += f"{'Ethereum:'.ljust(17)} {'{:.3f}'.format(float(web3.fromWei(rows1[2], 'mwei')))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {ethereumUSDTResult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {ethereumUSDTDescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(ethereumUSDTDiffAmount, 'mwei')}\n\n"

    msgResponse += "~~~~ POLY-USDT ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {'{:.3f}'.format(float(web3.fromWei(rows0[3], 'mwei')))}\n"
    msgResponse += f"{'Polygon:'.ljust(19)} {'{:.3f}'.format(float(web3.fromWei(rows1[3], 'mwei')))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {polyUSDTResult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {polyUSDTDescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(polyUSDTDiffAmount, 'mwei')}\n\n"

    msgResponse += "~~~~ TRON-USDT ~~~~\n"
    msgResponse += f"{'FxCore:'.ljust(20)} {'{:.3f}'.format(float(web3.fromWei(rows0[4], 'mwei')))}\n"
    msgResponse += f"{'Tron:'.ljust(22)} {'{:.3f}'.format(float(web3.fromWei(rows1[4], 'mwei')))}\n"
    msgResponse += f"{'Status:'.ljust(21)} {tronUSDTResult}\n"
    msgResponse += f"{'Description:'.ljust(17)} {tronUSDTDescription}\n"
    msgResponse += f"{'Diff_Amount:'.ljust(15)} {web3.fromWei(tronUSDTDiffAmount, 'mwei')}\n\n"

    if pundixResult != 'Normal' or fxResult != 'Normal' or polyUSDTResult != 'Normal' or tronUSDTResult != 'Normal':
        bot.send_message(TELE_CHAT_ID, msgResponse)

def sentTeleReport():
    bot.send_message(TELE_CHAT_ID, msgResponse)



# ######################################################################################
# Build flow function
# ######################################################################################

def minCheck():
    try:
        queryData()
    except Exception as e:
        print("minCheck Error happen")
        logging.error(e)
    else:
        buildTelebotMsg()

def dailyReport():
    try:
        queryData()
    except Exception as e:
        print("dailyReport Error happen")
        logging.error(e)
    else:
        buildTelebotMsg()
        sentTeleReport()

def listenTeleMsg():
    try:
        @bot.message_handler(commands=['data'])
        def echo_all(message):
            bot.reply_to(message, "Data is loading, please wait for a few sec...")
            dailyReport()
        bot.infinity_polling()
    except Exception as e:
        print("listenTele Error")
        logging.error(e)
        main()

# ######################################################################################
# Build schedule function
# ######################################################################################

def scheduleDailyReport():
    schedule.every().minutes.do(minCheck)
    schedule.every().day.at("07:00").do(dailyReport)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ********************
# Main function
# ********************

def main():
    connectRPX()
    loadContract()
    queryData()
    buildTelebotMsg()

    print("--- %s seconds ---" % (time.time() - start_time))
    listenTeleMsg()

if __name__ == "__main__":     # __name__ is a built-in variable in Python which evaluates to the name of the current module.
    main()
