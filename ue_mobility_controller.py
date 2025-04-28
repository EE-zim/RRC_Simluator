#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UE 移動場景控制器
此腳本用於模擬 UE 的移動場景，包括進入/離開 gNB 和 handover
"""

import os
import sys
import time
import signal
import subprocess
import random
import json
import argparse
from datetime import datetime

class UEMobilityController:
    def __init__(self, config_dir="/home/ubuntu/srsran_configs"):
        self.config_dir = config_dir
        self.epc_process = None
        self.gnb_processes = {}
        self.ue_processes = {}
        self.running = True
        self.log_file = open("/home/ubuntu/mobility_events.json", "w")
        self.log_file.write("[\n")
        self.first_log = True
        
        # 設置信號處理器，以便在腳本終止時清理資源
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log_event(self, event_type, details):
        """記錄移動事件到 JSON 文件"""
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "event_type": event_type,
            "details": details
        }
        
        if not self.first_log:
            self.log_file.write(",\n")
        else:
            self.first_log = False
            
        self.log_file.write(json.dumps(event, indent=2))
        self.log_file.flush()
    
    def start_epc(self):
        """啟動 EPC (核心網)"""
        print("啟動 EPC (核心網)...")
        epc_cmd = [
            "/home/ubuntu/srsRAN_4G/build/srsepc/src/srsepc",
            "--config.file=/home/ubuntu/srsran_configs/epc/epc.conf"
        ]
        self.epc_process = subprocess.Popen(epc_cmd)
        time.sleep(2)  # 等待 EPC 啟動
        self.log_event("EPC_START", {"process_id": self.epc_process.pid})
        print("EPC 已啟動，PID:", self.epc_process.pid)
    
    def start_gnb(self, gnb_id):
        """啟動指定的 gNB"""
        print(f"啟動 gNB{gnb_id}...")
        gnb_cmd = [
            "/home/ubuntu/srsRAN_4G/build/srsenb/src/srsenb",
            f"--config.file=/home/ubuntu/srsran_configs/enb/enb{gnb_id}.conf"
        ]
        self.gnb_processes[gnb_id] = subprocess.Popen(gnb_cmd)
        time.sleep(2)  # 等待 gNB 啟動
        self.log_event("GNB_START", {"gnb_id": gnb_id, "process_id": self.gnb_processes[gnb_id].pid})
        print(f"gNB{gnb_id} 已啟動，PID:", self.gnb_processes[gnb_id].pid)
    
    def start_ue(self, ue_id):
        """啟動指定的 UE"""
        if ue_id in self.ue_processes and self.ue_processes[ue_id] is not None:
            print(f"UE{ue_id} 已經在運行")
            return
            
        print(f"啟動 UE{ue_id}...")
        ue_cmd = [
            "/home/ubuntu/srsRAN_4G/build/srsue/src/srsue",
            f"--config.file=/home/ubuntu/srsran_configs/ue/ue{ue_id}.conf"
        ]
        self.ue_processes[ue_id] = subprocess.Popen(ue_cmd)
        time.sleep(2)  # 等待 UE 啟動
        self.log_event("UE_START", {"ue_id": ue_id, "process_id": self.ue_processes[ue_id].pid})
        print(f"UE{ue_id} 已啟動，PID:", self.ue_processes[ue_id].pid)
    
    def stop_ue(self, ue_id):
        """停止指定的 UE"""
        if ue_id not in self.ue_processes or self.ue_processes[ue_id] is None:
            print(f"UE{ue_id} 未運行")
            return
            
        print(f"停止 UE{ue_id}...")
        self.ue_processes[ue_id].terminate()
        self.ue_processes[ue_id].wait()
        self.log_event("UE_STOP", {"ue_id": ue_id})
        print(f"UE{ue_id} 已停止")
        self.ue_processes[ue_id] = None
    
    def trigger_handover(self, ue_id, from_gnb, to_gnb):
        """觸發 UE 從一個 gNB 切換到另一個 gNB"""
        print(f"觸發 UE{ue_id} 從 gNB{from_gnb} 切換到 gNB{to_gnb}...")
        
        # 在實際場景中，handover 是由網路根據信號強度自動觸發的
        # 在我們的模擬中，我們通過重新啟動 UE 並連接到不同的 gNB 來模擬 handover
        self.stop_ue(ue_id)
        
        # 修改 UE 配置以連接到新的 gNB
        self.update_ue_config(ue_id, to_gnb)
        
        # 重新啟動 UE
        time.sleep(1)
        self.start_ue(ue_id)
        
        self.log_event("HANDOVER", {
            "ue_id": ue_id,
            "from_gnb": from_gnb,
            "to_gnb": to_gnb
        })
        print(f"UE{ue_id} 已從 gNB{from_gnb} 切換到 gNB{to_gnb}")
    
    def update_ue_config(self, ue_id, gnb_id):
        """更新 UE 配置以連接到指定的 gNB"""
        config_file = f"/home/ubuntu/srsran_configs/ue/ue{ue_id}.conf"
        
        # 讀取配置文件
        with open(config_file, 'r') as f:
            config = f.read()
        
        # 根據 gNB ID 更新 EARFCN
        earfcn = "3350" if gnb_id == 1 else "3400"
        
        # 更新 ZeroMQ 端口
        rx_port = "2000" if gnb_id == 1 else "2100"
        
        # 更新配置
        config = self.replace_config_value(config, "dl_earfcn", earfcn)
        config = self.replace_config_value(config, "device_args", f"tx_port=tcp://*:2{ue_id}01,rx_port=tcp://localhost:{rx_port},id=ue{ue_id},base_srate=23.04e6")
        
        # 寫回配置文件
        with open(config_file, 'w') as f:
            f.write(config)
    
    def replace_config_value(self, config, key, value):
        """在配置文件中替換指定鍵的值"""
        import re
        pattern = rf"^{key}\s*=.*$"
        replacement = f"{key} = {value}"
        return re.sub(pattern, replacement, config, flags=re.MULTILINE)
    
    def run_mobility_scenario(self):
        """運行移動場景模擬"""
        try:
            # 啟動核心網和基站
            self.start_epc()
            self.start_gnb(1)
            self.start_gnb(2)
            
            # 等待網路穩定
            print("等待網路穩定...")
            time.sleep(5)
            
            # 場景 1: UE 進入/離開 gNB
            print("\n=== 場景 1: UE 進入/離開 gNB ===")
            self.start_ue(1)  # UE1 連接到 gNB1
            time.sleep(20)    # 保持連接 20 秒
            self.stop_ue(1)   # UE1 離開網路
            time.sleep(10)    # 等待 10 秒
            self.start_ue(1)  # UE1 重新連接到 gNB1
            time.sleep(15)    # 保持連接 15 秒
            
            # 場景 2: UE 在兩個 gNB 之間 handover
            print("\n=== 場景 2: UE 在兩個 gNB 之間 handover ===")
            self.start_ue(2)  # UE2 連接到 gNB2
            time.sleep(20)    # 保持連接 20 秒
            
            # UE3 將在兩個 gNB 之間切換
            self.start_ue(3)  # UE3 初始連接到 gNB1
            time.sleep(15)    # 保持連接 15 秒
            
            # 觸發 UE3 從 gNB1 到 gNB2 的 handover
            self.trigger_handover(3, 1, 2)
            time.sleep(20)    # 保持連接 20 秒
            
            # 觸發 UE3 從 gNB2 回到 gNB1 的 handover
            self.trigger_handover(3, 2, 1)
            time.sleep(15)    # 保持連接 15 秒
            
            # 場景 3: 多個 UE 同時連接和切換
            print("\n=== 場景 3: 多個 UE 同時連接和切換 ===")
            # 確保所有 UE 都在運行
            if 1 not in self.ue_processes or self.ue_processes[1] is None:
                self.start_ue(1)
            if 2 not in self.ue_processes or self.ue_processes[2] is None:
                self.start_ue(2)
            if 3 not in self.ue_processes or self.ue_processes[3] is None:
                self.start_ue(3)
            
            time.sleep(10)  # 所有 UE 同時連接 10 秒
            
            # UE2 從 gNB2 切換到 gNB1
            self.trigger_handover(2, 2, 1)
            time.sleep(15)  # 保持連接 15 秒
            
            # UE1 從 gNB1 切換到 gNB2
            self.trigger_handover(1, 1, 2)
            time.sleep(15)  # 保持連接 15 秒
            
            print("\n所有移動場景已完成")
            
        except Exception as e:
            print(f"運行移動場景時發生錯誤: {e}")
        finally:
            self.cleanup()
    
    def signal_handler(self, sig, frame):
        """處理終止信號"""
        print("\n接收到終止信號，正在清理資源...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """清理所有資源"""
        print("清理資源...")
        
        # 停止所有 UE
        for ue_id in list(self.ue_processes.keys()):
            if self.ue_processes[ue_id] is not None:
                self.stop_ue(ue_id)
        
        # 停止所有 gNB
        for gnb_id, process in list(self.gnb_processes.items()):
            if process is not None:
                print(f"停止 gNB{gnb_id}...")
                process.terminate()
                process.wait()
                self.log_event("GNB_STOP", {"gnb_id": gnb_id})
                print(f"gNB{gnb_id} 已停止")
        
        # 停止 EPC
        if self.epc_process is not None:
            print("停止 EPC...")
            self.epc_process.terminate()
            self.epc_process.wait()
            self.log_event("EPC_STOP", {})
            print("EPC 已停止")
        
        # 關閉日誌文件
        self.log_file.write("\n]")
        self.log_file.close()
        
        print("所有資源已清理完畢")

def main():
    parser = argparse.ArgumentParser(description="UE 移動場景控制器")
    parser.add_argument("--config-dir", default="/home/ubuntu/srsran_configs", help="配置文件目錄")
    args = parser.parse_args()
    
    controller = UEMobilityController(config_dir=args.config_dir)
    controller.run_mobility_scenario()

if __name__ == "__main__":
    main()
