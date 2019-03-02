#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import serial
import codecs

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


#b'EVENT 20 FE80:0000:0000:0000:021D:1291:0000:0574 0\r\n'
#b'EPANDESC\r\n'
#b'  Channel:33\r\n'
#b'  Channel Page:09\r\n'
#b'  Pan ID:12A4\r\n'
#b'  Addr:001C6400030C12A4\r\n'
#b'  LQI:98\r\n'
#b'  Side:0\r\n'
#b'  PairID:0112CE67\r\n'


    def scan(self):
        duration = 4;   # スキャン時間

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
        print("wait_join")
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
        print("read_instane_list")
        self.ser.timeout = 2
        # スマートメーターがインスタンスリスト通知を投げてくる
        # (ECHONET-Lite_Ver.1.12_02.pdf p.4-16)
        print(self.ser.readline(), end="\n") #無視
        print(self.ser.readline(), end="\n") #無視

    def build_frame(self):
        # ECHONET Lite フレーム作成
        # 　参考資料
        # 　・ECHONET-Lite_Ver.1.12_02.pdf (以下 EL)
        # 　・Appendix_H.pdf (以下 AppH)
        frame = b"\x10\x81"      # EHD (参考:EL p.3-2)
        frame += b"\x00\x01"      # TID (参考:EL p.3-3)
        # ここから EDATA
        frame += b"\x05\xFF\x01"  # SEOJ (参考:EL p.3-3 AppH p.3-408～)
        frame += b"\x02\x88\x01"  # DEOJ (参考:EL p.3-3 AppH p.3-274～)
        frame += b"\x62"          # ESV(62:プロパティ値読み出し要求) (参考:EL p.3-5)
        frame += b"\x01"          # OPC(1個)(参考:EL p.3-7)
        frame += b"\xE7"          # EPC(参考:EL p.3-7 AppH p.3-275)
        frame += b"\x00"          # PDC(参考:EL p.3-9)
        #b'\x10\xc2\x81\x00\x01\x05\xc3\xbf\x01\x02\xc2\x88\x01b\x01\xc3\xa7\x00'
        #frame = bytes.fromhex('1081000105FF010288016201E700')

        return frame

    def handle_ERXUDP(self, line):
        print("handle_ERXUDP")
        cols = line.strip().split(b' ')
        res = cols[9]  # UDP受信データ部分
        print(res)
        #tid = res[2:2+2];
        seoj = res[4:4+3]
        #deoj = res[7,7+3]
        ESV = res[10:10+1]
        #OPC = res[22,22+2]
        print(b"seoj:" + seoj)
        print(b"ESV:" + ESV)
        if seoj == b"\x02\x88\x01" and ESV == b"\x72":
            # スマートメーター(028801)から来た応答(72)なら
            EPC = res[12:12+1]
            if EPC == b"\xE7":
                # 内容が瞬時電力計測値(E7)だったら
                hexPower = res[-4:]    # 最後の4バイト（16進数で8文字）が瞬時電力計測値
                print(b"hexPower:" + hexPower)
                temp = hexPower[0] << 24
                temp = temp + hexPower[1] << 16
                temp = temp + hexPower[2] << 8
                temp = temp + hexPower[3]
                print(u"瞬時電力計測値:{0}[W]\n".format(temp))
                return True
        return False


    def getValue(self):
        print("getValue")
        frame = self.build_frame()
        print("frame len:{0}".format(str(len(frame))))
        print("frame:{0}".format(codecs.encode(frame, 'hex_codec')))
        # そのままframeをformatしてencodeすると意図しない形式になってハマる
        temp_command = "SKSENDTO 1 {0} 0E1A 1 0 {1:04X} ".format(self.ipv6Addr, len(frame))
        command = temp_command.encode() + frame + b"\r\n"
        # b"hoge" がpython2同等らしい
        self.ser.write(command)

        while True:
            #print(self.ser.readline(), end="\n") # エコーバック
            #print(self.ser.readline(), end="\n") # EVENT 21 が来るはず（チェック無し）
            #print(self.ser.readline(), end="\n") # OKが来るはず（チェック無し）
            line = self.ser.readline()         # ERXUDPが来るはず
            print(line, end="\n")

            if line.startswith(b"ERXUDP"):
                res = self.handle_ERXUDP(line)
                if res:
                    return

    def close(self):
        self.ser.write(b"SKTERM\r\n")
        print(self.ser.readline(), end="") # エコーバック
        print(self.ser.readline())
        self.ser.close()

    def connect(self, id, password):
        self.set_id(id)
        self.set_pw(password)
        self.scan()
        self.translate_address()
        self.set_channel()
        self.set_panid()
        self.start_join()
        self.wait_join()
        self.read_instane_list()

