#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RRC 協議追蹤捕獲工具
此腳本用於捕獲 gNB 的 RRC 協議追蹤並轉換為 JSON 格式
"""

import os
import sys
import time
import signal
import subprocess
import json
import argparse
import re
from datetime import datetime
import pcap
import struct
import binascii
from rrc_utils import parse_rrc_log

class RRCTraceCapture:
    def __init__(self, output_dir="/home/ubuntu/rrc_traces"):
        self.output_dir = output_dir
        self.pcap_files = {
            "enb1_mac": "/home/ubuntu/enb1_mac.pcap",
            "enb1_s1ap": "/home/ubuntu/enb1_s1ap.pcap",
            "enb2_mac": "/home/ubuntu/enb2_mac.pcap",
            "enb2_s1ap": "/home/ubuntu/enb2_s1ap.pcap",
            "ue1_mac": "/home/ubuntu/ue1_mac.pcap",
            "ue1_nas": "/home/ubuntu/ue1_nas.pcap",
            "ue2_mac": "/home/ubuntu/ue2_mac.pcap",
            "ue2_nas": "/home/ubuntu/ue2_nas.pcap",
            "ue3_mac": "/home/ubuntu/ue3_mac.pcap",
            "ue3_nas": "/home/ubuntu/ue3_nas.pcap"
        }
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 設置信號處理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """處理終止信號"""
        print("\n接收到終止信號，正在退出...")
        sys.exit(0)
    
    def extract_rrc_messages(self, pcap_file, output_json):
        """從 PCAP 文件中提取 RRC 消息並轉換為 JSON 格式"""
        print(f"從 {pcap_file} 提取 RRC 消息...")
        
        if not os.path.exists(pcap_file):
            print(f"錯誤: PCAP 文件 {pcap_file} 不存在")
            return False
        
        # 使用 tshark 提取 RRC 消息
        tshark_cmd = [
            "tshark", "-r", pcap_file,
            "-Y", "lte-rrc",
            "-T", "json"
        ]
        
        try:
            result = subprocess.run(tshark_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"錯誤: tshark 命令失敗: {result.stderr}")
                return False
            
            # 解析 JSON 輸出
            rrc_messages = json.loads(result.stdout)
            
            # 寫入 JSON 文件
            with open(output_json, 'w') as f:
                json.dump(rrc_messages, f, indent=2)
            
            print(f"已將 RRC 消息保存到 {output_json}")
            return True
            
        except Exception as e:
            print(f"提取 RRC 消息時發生錯誤: {e}")
            return False
    
    def parse_pcap_manually(self, pcap_file, output_json):
        """手動解析 PCAP 文件以提取 RRC 消息"""
        print(f"手動解析 {pcap_file} 以提取 RRC 消息...")
        
        if not os.path.exists(pcap_file):
            print(f"錯誤: PCAP 文件 {pcap_file} 不存在")
            return False
        
        try:
            # 打開 PCAP 文件
            p = pcap.pcap(pcap_file)
            
            rrc_messages = []
            
            # 遍歷每個數據包
            for timestamp, packet in p:
                # 檢查是否為 LTE-RRC 數據包
                # 這裡需要根據實際的數據包格式進行解析
                # 由於 LTE-RRC 解析比較複雜，這裡只提供一個簡化的示例
                
                # 假設 MAC LTE 數據包的特定標記
                if b'LTE-RRC' in packet or b'RRC' in packet:
                    # 提取 RRC 消息
                    rrc_message = {
                        "timestamp": timestamp,
                        "data": binascii.hexlify(packet).decode('utf-8'),
                        "type": "RRC"
                    }
                    
                    # 嘗試識別 RRC 消息類型
                    if b'Setup' in packet:
                        rrc_message["message_type"] = "RRC Setup"
                    elif b'Reconfig' in packet:
                        rrc_message["message_type"] = "RRC Reconfiguration"
                    elif b'Handover' in packet:
                        rrc_message["message_type"] = "Handover Command"
                    
                    rrc_messages.append(rrc_message)
            
            # 寫入 JSON 文件
            with open(output_json, 'w') as f:
                json.dump(rrc_messages, f, indent=2)
            
            print(f"已將 RRC 消息保存到 {output_json}")
            return True
            
        except Exception as e:
            print(f"解析 PCAP 文件時發生錯誤: {e}")
            return False
    
    def extract_logs(self, log_file, output_json):
        """從日誌文件中提取 RRC 相關信息"""
        print(f"從 {log_file} 提取 RRC 相關信息...")
        
        if not os.path.exists(log_file):
            print(f"錯誤: 日誌文件 {log_file} 不存在")
            return False
        
        try:
            messages = parse_rrc_log(log_file)

            # 將解析結果轉換為更通用的格式
            rrc_logs = [
                {
                    "timestamp": m.get("timestamp"),
                    "message": m.get("content"),
                    "direction": m.get("direction")
                }
                for m in messages
            ]

            with open(output_json, 'w') as f:
                json.dump(rrc_logs, f, indent=2)
            
            print(f"已將 RRC 日誌信息保存到 {output_json}")
            return True
            
        except Exception as e:
            print(f"提取日誌信息時發生錯誤: {e}")
            return False
    
    def install_dependencies(self):
        """安裝必要的依賴項"""
        print("安裝必要的依賴項...")
        
        try:
            # 安裝 tshark
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "tshark", "python3-pypcap"], check=True)
            print("依賴項安裝完成")
            return True
        except Exception as e:
            print(f"安裝依賴項時發生錯誤: {e}")
            return False
    
    def capture_all_traces(self):
        """捕獲所有 RRC 協議追蹤"""
        print("開始捕獲所有 RRC 協議追蹤...")
        
        # 安裝依賴項
        if not self.install_dependencies():
            print("無法安裝必要的依賴項，退出")
            return False
        
        # 處理 PCAP 文件
        for name, pcap_file in self.pcap_files.items():
            if os.path.exists(pcap_file):
                output_json = os.path.join(self.output_dir, f"{name}_rrc.json")
                
                # 嘗試使用 tshark 提取 RRC 消息
                if not self.extract_rrc_messages(pcap_file, output_json):
                    # 如果 tshark 失敗，嘗試手動解析
                    self.parse_pcap_manually(pcap_file, output_json)
        
        # 處理日誌文件
        log_files = [
            "/home/ubuntu/enb1.log",
            "/home/ubuntu/enb2.log",
            "/home/ubuntu/ue1.log",
            "/home/ubuntu/ue2.log",
            "/home/ubuntu/ue3.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                base_name = os.path.basename(log_file).split('.')[0]
                output_json = os.path.join(self.output_dir, f"{base_name}_log_rrc.json")
                self.extract_logs(log_file, output_json)
        
        # 合併移動事件和 RRC 追蹤
        self.merge_mobility_and_rrc()
        
        print("RRC 協議追蹤捕獲完成")
        return True
    
    def merge_mobility_and_rrc(self):
        """合併移動事件和 RRC 追蹤"""
        print("合併移動事件和 RRC 追蹤...")
        
        mobility_file = "/home/ubuntu/mobility_events.json"
        if not os.path.exists(mobility_file):
            print(f"錯誤: 移動事件文件 {mobility_file} 不存在")
            return False
        
        try:
            # 讀取移動事件
            with open(mobility_file, 'r') as f:
                mobility_events = json.load(f)
            
            # 收集所有 RRC 追蹤
            rrc_traces = {}
            for filename in os.listdir(self.output_dir):
                if filename.endswith("_rrc.json") or filename.endswith("_log_rrc.json"):
                    file_path = os.path.join(self.output_dir, filename)
                    with open(file_path, 'r') as f:
                        rrc_traces[filename] = json.load(f)
            
            # 合併數據
            merged_data = {
                "mobility_events": mobility_events,
                "rrc_traces": rrc_traces
            }
            
            # 寫入合併文件
            merged_file = os.path.join(self.output_dir, "merged_rrc_mobility.json")
            with open(merged_file, 'w') as f:
                json.dump(merged_data, f, indent=2)
            
            print(f"已將移動事件和 RRC 追蹤合併到 {merged_file}")
            return True
            
        except Exception as e:
            print(f"合併數據時發生錯誤: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="RRC 協議追蹤捕獲工具")
    parser.add_argument("--output-dir", default="/home/ubuntu/rrc_traces", help="輸出目錄")
    args = parser.parse_args()
    
    capture = RRCTraceCapture(output_dir=args.output_dir)
    capture.capture_all_traces()

if __name__ == "__main__":
    main()
