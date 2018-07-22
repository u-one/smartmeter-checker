#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import sys
import serial
import time

class EchonetLiteClient:
    def __init__(self, serialport, baudrate):
        print("serialport={}, baudrate={}".format(serialport, baudrate))
        self.ser = serial.Serial(serialport, baudrate, timeout=1)
        self.scan_results = {}

    def send(self, command):
        self.ser.write(command.encode())
        print(self.ser.readline())
        print(self.ser.readline())
        print(self.ser.readline(), end="\n")

    def ver(self):
        command = "SKVER\r\n"
        self.send(command)

    #Bルート認証パスワード設定
    def set_pw(self, password):
        command = "SKSETPWD C " + password + "\r\n"
        self.send(command)

    # Bルート認証ID設定
    def set_id(self, id):
        command = "SKSETRBID " + id + "\r\n"
        self.send(command)

    def scan(self):
        duration = 6;   # スキャン時間

        while not b"Channel" in self.scan_results:
            command = "SKSCAN 2 FFFFFFFF " + str(duration) + " 0 \r\n"
            self.ser.write(command.encode())
            scan_end = False
            while not scan_end:
                line = self.ser.readline()
                print(line)

                if line.startswith(b"EVENT 22"):
                    scan_end = True
                    pass
                elif line.startswith(b"  "):
                    cols = line.strip().split(b':')
                    self.scan_results[cols[0]] = cols[1]
            duration+=1
            if duration > 8 and not b"Channel" in self.scan_results:
                # 引数としては14まで指定できるが、7で失敗したらそれ以上は無駄らしい
                print("scan failed")
                sys.exit()

    def set_channel(self):
        # スキャン結果からChannelを設定。
        command = "SKSREG S2 " + self.scan_results[b"Channel"].decode() + "\r\n"
        self.send(command)

    def set_panid(self):
        # スキャン結果からPan IDを設定
        command = "SKSREG S3 " + self.scan_results[b"Pan ID"].decode() + "\r\n"
        self.send(command)

    def translate_address(self):
        # MACアドレス(64bit)をIPV6リンクローカルアドレスに変換
        command = "SKLL64 " + self.scan_results[b"Addr"].decode() + "\r\n"
        self.ser.write(command.encode())
        print(self.ser.readline(), end="") # エコーバック
        self.ipv6Addr = self.ser.readline().strip().decode()
        print(self.ipv6Addr)

    def start_join(self):
        # PANA 接続シーケンスを開始します。
        command = "SKJOIN " + self.ipv6Addr + "\r\n"
        self.ser.write(command.encode())
        print(self.ser.readline(), end="\n") # エコーバック↲
        print(self.ser.readline(), end="\n") # OKが来るはず（チェック無し）↲

    def wait_join(self):
        # PANA 接続完了待ち（10行ぐらいなんか返してくる）
        connected = False
        while not connected:
            line = self.ser.readline()
            print(line, end="\n")
            if line.startswith(b"EVENT 24") :
                print("join failed")
                sys.exit()
            elif line.startswith(b"EVENT 25") :
                connected = True

    def read_instane_list(self):
        self.ser.timeout = 2
        # スマートメーターがインスタンスリスト通知を投げてくる
        # (ECHONET-Lite_Ver.1.12_02.pdf p.4-16)
        print(self.ser.readline(), end="\n") #無視

    def build_frame(self):
        # ECHONET Lite フレーム作成
        # 　参考資料
        # 　・ECHONET-Lite_Ver.1.12_02.pdf (以下 EL)
        # 　・Appendix_H.pdf (以下 AppH)
        frame = ""
        frame += "\x10\x81"      # EHD (参考:EL p.3-2)
        frame += "\x00\x01"      # TID (参考:EL p.3-3)
        # ここから EDATA
        frame += "\x05\xFF\x01"  # SEOJ (参考:EL p.3-3 AppH p.3-408～)
        frame += "\x02\x88\x01"  # DEOJ (参考:EL p.3-3 AppH p.3-274～)
        frame += "\x62"          # ESV(62:プロパティ値読み出し要求) (参考:EL p.3-5)
        frame += "\x01"          # OPC(1個)(参考:EL p.3-7)
        frame += "\xE7"          # EPC(参考:EL p.3-7 AppH p.3-275)
        frame += "\x00"          # PDC(参考:EL p.3-9)
        return frame

    def getValue(self):
        frame = self.build_frame()
        command = "SKSENDTO 1 {0} 0E1A 1 {1:04X} {2}".format(self.ipv6Addr, len(frame), frame)
        self.ser.write(command.encode())
        print(self.ser.readline(), end="\n") # エコーバック
        print(self.ser.readline(), end="\n") # EVENT 21 が来るはず（チェック無し）
        print(self.ser.readline(), end="\n") # OKが来るはず（チェック無し）
        line = self.ser.readline()         # ERXUDPが来るはず
        print(line, end="\n")

        if line.startswith(b"ERXUDP"):
            cols = line.strip().split(' ')
            res = cols[8]  # UDP受信データ部分
            #tid = res[4:4+4];
            seoj = res[8:8+6]
            #deoj = res[14,14+6]
            ESV = res[20:20+2]
            #OPC = res[22,22+2]
            if seoj == "028801" and ESV == "72":
                # スマートメーター(028801)から来た応答(72)なら
                EPC = res[24:24+2]
                if EPC == "E7":
                    # 内容が瞬時電力計測値(E7)だったら
                    hexPower = line[-8:]    # 最後の4バイト（16進数で8文字）が瞬時電力計測値
                    intPower = int(hexPower, 16)
                    print(u"瞬時電力計測値:{0}[W]\n".format(intPower))


def parse_args():
    parser = argparse.ArgumentParser()
    # 必須
    parser.add_argument("b_route_id", help="Bルート認証ID")
    parser.add_argument("b_route_password", help="Bルート認証パスワード")
    # 任意
    parser.add_argument("--serialport", help="optional")
    parser.add_argument("--baudrate", help="optional")
    return parser.parse_args()

serialport = '/dev/ttyUSB0'  # linux
#serialport = 'COM1' # windows
#serialport = '/dev/cu.usbserial-XXXXX'    # mac
baudrate = 115200

def main():
    args = parse_args()
    if hasattr(args, 'serialport'):
        serialport = args.serialport
    if hasattr(args, 'baudrate'):
        baudrate = args.baudrate

    client = EchonetLiteClient(serialport, baudrate)
    client.ver()
    client.set_id(args.b_route_id)
    client.set_pw(args.b_route_password)
    client.scan()
    client.set_channel()
    client.set_panid()
    client.translate_address()
    client.start_join()
    client.wait_join()
    client.read_instane_list()
    client.getValue()

if __name__ == '__main__':
    main()
