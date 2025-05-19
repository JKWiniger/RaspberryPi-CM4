import os, re
import socket, sys, time
import spidev as SPI
import xgoscreen.LCD_2inch as LCD_2inch
from xgolib import XGO
from PIL import Image, ImageDraw, ImageFont
import threading
import json, base64
import subprocess
import pyaudio
import wave
import numpy as np
from scipy import fftpack
from datetime import datetime
from key import Button,language
import requests
from audio import start_recording 
from language_recognize import test_one 
from doubao import model_output
import logging
la=language()
SPLASH_COLOR = (15, 21, 46)
FONT_PATH = "/home/pi/model/msyh.ttc"
FONT_SIZE = 20
DOG_PORT = '/dev/ttyAMA0'
DOG_VERSION = "xgomini"
TEST_NETWORK_URL = "http://www.baidu.com"

ACTION_MAP = {
    "Dance": (23, 6),
    "Pushups": (21, 8),
    "Pee": (11, 7),
    "Stretch": (14, 10),
    "Pray": (19, 3),
    "Chickenhead": (20, 9),
    "Lookforfood": (17, 4),
    "Grabdownwards": (130, 10),
    "Wave": (15, 6),
    "Beg": (17, 3)
}
import pyaudio
from auto_platform import AudiostreamSource
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
class DogController:
    def __init__(self):

        self.display = LCD_2inch.LCD_2inch()
        self.display.Init()
        
        self.splash = Image.new("RGB", (self.display.height, self.display.width), SPLASH_COLOR)
        self.draw = ImageDraw.Draw(self.splash)
        self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        
        self.dog = XGO(port=DOG_PORT, version=DOG_VERSION)
        self.button = Button()
        self.audio_stream = None
        self.stream_a = None
        self.p = None
        
        # 启动按键检测线程
        self._start_button_thread()

    def _start_button_thread(self):
        def check_button():
            while True:
                if self.button.press_b():
                    try:
                        self.audio_stream.stop()
                        logging.warning('audio_stream kill')
                    except Exception as e:
                        logging.warning(e)
                    try:
                        self.stream_a.stop_stream()
                        self.stream_a.close()
                        logging.warning("stream_a kill")
                    except Exception as e:
                        logging.warning(e)
                    try:
                        self.p.terminate()
                        logging.warning("p terminate")
                    except:
                        pass
                    print("B键按下, 退出程序")
                    os._exit(0)
                time.sleep(0.1)
        
        thread = threading.Thread(target=check_button, daemon=True)
        thread.start()

    def show_message(self, text, color=(255, 255, 255)):
        self.draw.rectangle((0, 0, self.display.height, self.display.width), fill=SPLASH_COLOR)
        self.draw.text((80, 100), text, fill=color, font=self.font)
        self.display.ShowImage(self.splash)

    def execute_action(self, action_name):
        if action_name in ACTION_MAP:
            action_id, duration = ACTION_MAP[action_name]
            self.dog.action(action_id)
            time.sleep(duration)
            return True
        return False

    def check_network(self):
        try:
            requests.get(TEST_NETWORK_URL, timeout=2)
            print("Net is connection")
            return True
        except:
            print("Net is unconnection")
            return False
            

    def run(self):
        if not self.check_network():
            print("网络未连接")
            if la=="cn":
              self.show_message("网络未连接", color=(255, 0, 0))
            else:
              self.show_message("Network not connected", color=(255, 0, 0))
            return
        if la=="cn":
          self.show_message("正在启动，请稍后", color=(255, 255, 255))
        else:
          self.show_message("Starting up...", color=(255, 255, 255))
        while True:
            try:
                self.p = pyaudio.PyAudio()
                self.stream_a = self.p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                )
                self.audio_stream = AudiostreamSource()
                logging.warning('音频初始化完成')
                start_recording(self.p, self.stream_a, self.audio_stream)
                logging.warning("录音结束")
                content = test_one()
                
                if not content:
                    print("录音出错")
                    continue
                
                print("识别内容:", content)
                
                action_results = model_output(content=content)
                
                action_executed = False
                for action_name, action_value in zip(ACTION_MAP.keys(), action_results):
                    if int(action_value) == 1:
                        print(f"执行动作: {action_name}")
                        self.execute_action(action_name)
                        action_executed = True
                        break
                
                if not action_executed:
                    if la=="cn":
                      self.show_message("未识别指令")
                    else:
                      self.show_message("Unrecognized command")
                    print("未识别指令")
                    self.dog.reset()
                
                time.sleep(1)

            except KeyboardInterrupt:
                print("程序终止")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                continue

if __name__ == "__main__":
    controller = DogController()
    controller.run()
