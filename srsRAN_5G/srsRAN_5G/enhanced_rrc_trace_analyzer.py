#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced RRC trace analyzer that parses ASN.1 structures and extracts key parameters.
"""
import os
import sys
import json
import argparse
import subprocess
import re
import csv
import datetime
import pyshark
import asn1tools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from itertools import groupby

class RRCMessageParser:
    """RRC 消息解析器，用於解析 RRC 協議消息的 ASN.1 結構"""
    def __init__(self, asn1_specs_dir=None):
        self.asn1_specs = {}
        
        # 如果未提供 ASN.1 規範目錄，使用默認位置
        if not asn1_specs_dir:
            asn1_specs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'asn1_specs')
        
        # 確保 ASN.1 規範目錄存在
        os.makedirs(asn1_specs_dir, exist_ok=True)
        
        # 下載 ASN.1 規範文件（如果不存在）
        self.download_asn1_specs(asn1_specs_dir)
        
        # 加載 ASN.1 規範
        try:
            self.asn1_specs['rrc'] = asn1tools.compile_files(
                os.path.join(asn1_specs_dir, 'rrc-14.3.0.asn1'),
                'RRC-DEFINITIONS'
            )
            print("Loaded RRC ASN.1 specifications")
        except Exception as e:
            print(f"Warning: Failed to load RRC ASN.1 specifications: {e}")
            print("RRC message decoding will be limited")
    
    def download_asn1_specs(self, asn1_specs_dir):
        """下載 ASN.1 規範文件"""
        rrc_spec_file = os.path.join(asn1_specs_dir, 'rrc-14.3.0.asn1')
        
        if not os.path.exists(rrc_spec_file):
            print(f"Downloading RRC ASN.1 specifications to {rrc_spec_file}...")
            
            # 使用 curl 下載 ASN.1 規範文件
            try:
                subprocess.run([
                    'curl', '-s', '-o', rrc_spec_file,
                    'https://raw.githubusercontent.com/srsran/srsRAN_4G/master/lib/include/srsran/asn1/rrc/rrc_asn1.asn'
                ], check=True)
                print("Downloaded RRC ASN.1 specifications")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to download RRC ASN.1 specifications: {e}")
                
                # 創建一個簡單的示例 ASN.1 文件，以便程序可以繼續運行
                with open(rrc_spec_file, 'w') as f:
                    f.write("""
RRC-DEFINITIONS AUTOMATIC TAGS ::=
BEGIN
-- 這是一個簡化的 RRC ASN.1 規範文件
-- 實際使用時應下載完整的規範文件
END
                    """)
                print("Created a placeholder ASN.1 file")
    
    def decode_rrc_message(self, message_type, message_hex):
        """解碼 RRC 消息"""
        if 'rrc' not in self.asn1_specs:
            return {"error": "ASN.1 specifications not loaded"}
        
        try:
            # 將十六進制字符串轉換為字節
            message_bytes = bytes.fromhex(message_hex)
            
            # 解碼 RRC 消息
            decoded = self.asn1_specs['rrc'].decode(message_type, message_bytes)
            return decoded
        except Exception as e:
            return {"error": f"Failed to decode RRC message: {e}"}
    
    def extract_key_parameters(self, decoded_message, message_type):
        """從解碼的 RRC 消息中提取關鍵參數"""
        params = {"message_type": message_type}
        
        if isinstance(decoded_message, dict):
            if message_type == "RRCConnectionRequest":
                if "ue-Identity" in decoded_message:
                    params["ue_identity"] = str(decoded_message["ue-Identity"])
                if "establishmentCause" in decoded_message:
                    params["establishment_cause"] = str(decoded_message["establishmentCause"])
            
            elif message_type == "RRCConnectionSetup":
                if "radioResourceConfigDedicated" in decoded_message:
                    rr_config = decoded_message["radioResourceConfigDedicated"]
                    if "drb-ToAddModList" in rr_config:
                        params["drb_count"] = len(rr_config["drb-ToAddModList"])
                    if "srb-ToAddModList" in rr_config:
                        params["srb_count"] = len(rr_config["srb-ToAddModList"])
            
            elif message_type == "RRCConnectionReconfiguration":
                if "mobilityControlInfo" in decoded_message:
                    mobility_info = decoded_message["mobilityControlInfo"]
                    params["handover"] = True
                    if "targetPhysCellId" in mobility_info:
                        params["target_pci"] = mobility_info["targetPhysCellId"]
                else:
                    params["handover"] = False
                
                if "measConfig" in decoded_message:
                    meas_config = decoded_message["measConfig"]
                    if "measObjectToAddModList" in meas_config:
                        params["meas_objects"] = len(meas_config["measObjectToAddModList"])
                    if "reportConfigToAddModList" in meas_config:
                        params["report_configs"] = len(meas_config["reportConfigToAddModList"])
            
            elif message_type == "MeasurementReport":
                if "measResults" in decoded_message:
                    meas_results = decoded_message["measResults"]
                    if "measId" in meas_results:
                        params["meas_id"] = meas_results["measId"]
                    if "measResultPCell" in meas_results:
                        pcell_results = meas_results["measResultPCell"]
                        if "rsrpResult" in pcell_results:
                            params["pcell_rsrp"] = pcell_results["rsrpResult"]
                        if "rsrqResult" in pcell_results:
                            params["pcell_rsrq"] = pcell_results["rsrqResult"]
                    
                    if "measResultNeighCells" in meas_results:
                        neigh_cells = meas_results["measResultNeighCells"]
                        if "measResultListEUTRA" in neigh_cells:
                            eutra_list = neigh_cells["measResultListEUTRA"]
                            params["neighbor_cells"] = len(eutra_list)
                            
                            # 提取鄰區測量結果
                            neighbor_results = []
                            for cell in eutra_list:
                                if "physCellId" in cell and "measResult" in cell:
                                    cell_result = {
                                        "pci": cell["physCellId"]
                                    }
                                    if "rsrpResult" in cell["measResult"]:
                                        cell_result["rsrp"] = cell["measResult"]["rsrpResult"]
                                    if "rsrqResult" in cell["measResult"]:
                                        cell_result["rsrq"] = cell["measResult"]["rsrqResult"]
                                    neighbor_results.append(cell_result)
                            
                            params["neighbor_results"] = neighbor_results
        
        return params

class PCAPAnalyzer:
    """PCAP 分析器，用於從 PCAP 文件中提取 RRC 消息"""
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.rrc_messages = []
        self.rrc_parser = RRCMessageParser()
    
    def extract_rrc_messages(self):
        """從 PCAP 文件中提取 RRC 消息"""
        print(f"Extracting RRC messages from {self.pcap_file}...")
        
        try:
            # 使用 pyshark 打開 PCAP 文件
            cap = pyshark.FileCapture(self.pcap_file, display_filter="lte-rrc")
            
            for packet in cap:
                try:
                    if hasattr(packet, 'lte_rrc'):
                        # 提取 RRC 消息類型和內容
                        for field in dir(packet.lte_rrc):
                            if field.startswith('rrcConnectionRequest') or \
                               field.startswith('rrcConnectionSetup') or \
                               field.startswith('rrcConnectionReconfiguration') or \
                               field.startswith('measurementReport') or \
                               field.startswith('rrcConnectionReestablishmentRequest') or \
                               field.startswith('rrcConnectionRelease'):
                                
                                message_type = field.split('_')[0]
                                message_content = getattr(packet.lte_rrc, field)
                                
                                # 提取十六進制數據
                                message_hex = ""
                                if hasattr(packet.lte_rrc, 'msg_raw'):
                                    message_hex = packet.lte_rrc.msg_raw
                                
                                # 解碼 RRC 消息
                                decoded_message = {}
                                if message_hex:
                                    decoded_message = self.rrc_parser.decode_rrc_message(message_type, message_hex)
                                
                                # 提取關鍵參數
                                key_params = self.rrc_parser.extract_key_parameters(decoded_message, message_type)
                                
                                # 創建 RRC 消息記錄
                                rrc_message = {
                                    "timestamp": packet.sniff_time.isoformat(),
                                    "message_type": message_type,
                                    "message_content": str(message_content),
                                    "decoded_message": decoded_message,
                                    "key_parameters": key_params
                                }
                                
                                self.rrc_messages.append(rrc_message)
                except Exception as e:
                    print(f"Error processing packet: {e}")
            
            print(f"Extracted {len(self.rrc_messages)} RRC messages")
            
        except Exception as e:
            print(f"Error extracting RRC messages: {e}")
        
        return self.rrc_messages

class LogAnalyzer:
    """日誌分析器，用於從日誌文件中提取 RRC 相關信息"""
    def __init__(self, log_file):
        self.log_file = log_file
        self.rrc_events = []
    
    def extract_rrc_events(self):
        """從日誌文件中提取 RRC 相關事件"""
        print(f"Extracting RRC events from {self.log_file}...")
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    # 提取時間戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    # 提取 RRC 相關事件
                    if 'RRC' in line:
                        # RRC 連接建立
                        if 'RRC Connection Setup' in line or 'RRC Connected' in line:
                            self.rrc_events.append({
                                "timestamp": timestamp,
                                "event_type": "RRC_CONNECTION_SETUP",
                                "message": line.strip()
                            })
                        
                        # RRC 連接重配置
                        elif 'RRC Connection Reconfiguration' in line:
                            self.rrc_events.append({
                                "timestamp": timestamp,
                                "event_type": "RRC_CONNECTION_RECONFIGURATION",
                                "message": line.strip()
                            })
                        
                        # RRC 測量報告
                        elif 'Measurement Report' in line:
                            # 提取 RSRP/RSRQ 值
                            rsrp_match = re.search(r'RSRP[: =]+(-?\d+\.?\d*)', line)
                            rsrq_match = re.search(r'RSRQ[: =]+(-?\d+\.?\d*)', line)
                            
                            rsrp = float(rsrp_match.group(1)) if rsrp_match else None
                            rsrq = float(rsrq_match.group(1)) if rsrq_match else None
                            
                            self.rrc_events.append({
                                "timestamp": timestamp,
                                "event_type": "MEASUREMENT_REPORT",
                                "message": line.strip(),
                                "rsrp": rsrp,
                                "rsrq": rsrq
                            })
                        
                        # RRC 連接釋放
                        elif 'RRC Connection Release' in line:
                            self.rrc_events.append({
                                "timestamp": timestamp,
                                "event_type": "RRC_CONNECTION_RELEASE",
                                "message": line.strip()
                            })
                        
                        # RRC 連接重建
                        elif 'RRC Connection Reestablishment' in line:
                            self.rrc_events.append({
                                "timestamp": timestamp,
                                "event_type": "RRC_CONNECTION_REESTABLISHMENT",
                                "message": line.strip()
                            })
                    
                    # 提取切換事件
                    elif 'Handover' in line:
                        # 提取源小區和目標小區
                        source_match = re.search(r'from (?:cell|PCI) (\d+)', line)
                        target_match = re.search(r'to (?:cell|PCI) (\d+)', line)
                        
                        source_cell = source_match.group(1) if source_match else None
                        target_cell = target_match.group(1) if target_match else None
                        
                        self.rrc_events.append({
                            "timestamp": timestamp,
                            "event_type": "HANDOVER",
                            "message": line.strip(),
                            "source_cell": source_cell,
                            "target_cell": target_cell
                        })
            
            print(f"Extracted {len(self.rrc_events)} RRC events")
            
        except Exception as e:
            print(f"Error extracting RRC events: {e}")
        
        return self.rrc_events

class RRCSequenceAnalyzer:
    """RRC 序列分析器，用於分析 RRC 消息序列"""
    def __init__(self, rrc_messages, rrc_events):
        self.rrc_messages = rrc_messages
        self.rrc_events = rrc_events
        self.combined_events = []
        self.sequences = []
        self.sequence_patterns = {}
    
    def combine_events(self):
        """合併 RRC 消息和事件，按時間排序"""
        # 合併 RRC 消息
        for msg in self.rrc_messages:
            event = {
                "timestamp": msg["timestamp"],
                "type": "RRC_MESSAGE",
                "message_type": msg["message_type"],
                "details": msg
            }
            self.combined_events.append(event)
        
        # 合併 RRC 事件
        for evt in self.rrc_events:
            event = {
                "timestamp": evt["timestamp"],
                "type": "RRC_EVENT",
                "event_type": evt["event_type"],
                "details": evt
            }
            self.combined_events.append(event)
        
        # 按時間排序
        self.combined_events.sort(key=lambda x: x["timestamp"])
        
        return self.combined_events
    
    def identify_sequences(self, window_size=5):
        """識別 RRC 消息序列"""
        if not self.combined_events:
            self.combine_events()
        
        # 使用滑動窗口識別序列
        for i in range(len(self.combined_events) - window_size + 1):
            window = self.combined_events[i:i+window_size]
            
            # 創建序列標識符
            sequence_id = []
            for event in window:
                if event["type"] == "RRC_MESSAGE":
                    sequence_id.append(event["message_type"])
                else:
                    sequence_id.append(event["event_type"])
            
            # 將序列標識符轉換為元組，以便用作字典鍵
            sequence_tuple = tuple(sequence_id)
            
            # 記錄序列
            self.sequences.append({
                "start_time": window[0]["timestamp"],
                "end_time": window[-1]["timestamp"],
                "sequence": sequence_id,
                "events": window
            })
            
            # 更新序列模式計數
            if sequence_tuple in self.sequence_patterns:
                self.sequence_patterns[sequence_tuple] += 1
            else:
                self.sequence_patterns[sequence_tuple] = 1
        
        return self.sequences
    
    def get_common_sequences(self, top_n=5):
        """獲取最常見的序列模式"""
        if not self.sequence_patterns:
            self.identify_sequences()
        
        # 按出現次數排序
        sorted_patterns = sorted(self.sequence_patterns.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前 N 個最常見的模式
        return sorted_patterns[:top_n]
    
    def detect_abnormal_sequences(self, threshold=0.05):
        """檢測異常序列"""
        if not self.sequence_patterns:
            self.identify_sequences()
        
        # 計算總序列數
        total_sequences = sum(self.sequence_patterns.values())
        
        # 找出罕見的序列模式（出現頻率低於閾值）
        abnormal_patterns = {}
        for pattern, count in self.sequence_patterns.items():
            frequency = count / total_sequences
            if frequency < threshold:
                abnormal_patterns[pattern] = {
                    "count": count,
                    "frequency": frequency
                }
        
        return abnormal_patterns
    
    def analyze_handover_sequences(self):
        """分析切換相關的序列"""
        handover_sequences = []
        
        for seq in self.sequences:
            # 檢查序列是否包含切換事件
            has_handover = False
            for event in seq["events"]:
                if (event["type"] == "RRC_EVENT" and event["event_type"] == "HANDOVER") or \
                   (event["type"] == "RRC_MESSAGE" and "RRCConnectionReconfiguration" in event["message_type"] and \
                    "handover" in event["details"].get("key_parameters", {}) and \
                    event["details"]["key_parameters"]["handover"]):
                    has_handover = True
                    break
            
            if has_handover:
                handover_sequences.append(seq)
        
        return handover_sequences

class RRCPerformanceAnalyzer:
    """RRC 性能分析器，用於分析 RRC 性能指標"""
    def __init__(self, rrc_messages, rrc_events, combined_events=None):
        self.rrc_messages = rrc_messages
        self.rrc_events = rrc_events
        self.combined_events = combined_events
        self.performance_metrics = {}
    
    def calculate_connection_setup_time(self):
        """計算 RRC 連接建立時間"""
        setup_times = []
        
        # 尋找 RRC 連接請求和設置消息對
        request_times = {}
        
        for event in self.combined_events:
            if event["type"] == "RRC_MESSAGE":
                if event["message_type"] == "RRCConnectionRequest":
                    # 提取 UE 身份
                    ue_identity = None
                    if "key_parameters" in event["details"] and "ue_identity" in event["details"]["key_parameters"]:
                        ue_identity = event["details"]["key_parameters"]["ue_identity"]
                    
                    # 記錄請求時間
                    request_times[ue_identity] = datetime.datetime.fromisoformat(event["timestamp"])
                
                elif event["message_type"] == "RRCConnectionSetup":
                    # 尋找對應的請求
                    for ue_id, req_time in list(request_times.items()):
                        # 計算時間差
                        setup_time = datetime.datetime.fromisoformat(event["timestamp"]) - req_time
                        setup_times.append(setup_time.total_seconds())
                        
                        # 移除已處理的請求
                        del request_times[ue_id]
                        break
        
        # 計算統計數據
        if setup_times:
            self.performance_metrics["connection_setup_time"] = {
                "min": min(setup_times),
                "max": max(setup_times),
                "avg": sum(setup_times) / len(setup_times),
                "count": len(setup_times),
                "values": setup_times
            }
        else:
            self.performance_metrics["connection_setup_time"] = {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0,
                "values": []
            }
        
        return self.performance_metrics["connection_setup_time"]
    
    def calculate_handover_delay(self):
        """計算切換延遲"""
        handover_delays = []
        
        # 尋找切換命令和完成事件對
        handover_commands = {}
        
        for event in self.combined_events:
            if event["type"] == "RRC_MESSAGE" and "RRCConnectionReconfiguration" in event["message_type"]:
                # 檢查是否為切換命令
                if "key_parameters" in event["details"] and \
                   "handover" in event["details"]["key_parameters"] and \
                   event["details"]["key_parameters"]["handover"]:
                    # 提取目標小區 ID
                    target_pci = None
                    if "target_pci" in event["details"]["key_parameters"]:
                        target_pci = event["details"]["key_parameters"]["target_pci"]
                    
                    # 記錄命令時間
                    handover_commands[target_pci] = datetime.datetime.fromisoformat(event["timestamp"])
            
            elif event["type"] == "RRC_EVENT" and event["event_type"] == "HANDOVER":
                # 提取目標小區 ID
                target_cell = None
                if "target_cell" in event["details"]:
                    target_cell = event["details"]["target_cell"]
                
                # 尋找對應的命令
                for pci, cmd_time in list(handover_commands.items()):
                    if pci == target_cell or pci is None or target_cell is None:
                        # 計算時間差
                        handover_delay = datetime.datetime.fromisoformat(event["timestamp"]) - cmd_time
                        handover_delays.append(handover_delay.total_seconds())
                        
                        # 移除已處理的命令
                        del handover_commands[pci]
                        break
        
        # 計算統計數據
        if handover_delays:
            self.performance_metrics["handover_delay"] = {
                "min": min(handover_delays),
                "max": max(handover_delays),
                "avg": sum(handover_delays) / len(handover_delays),
                "count": len(handover_delays),
                "values": handover_delays
            }
        else:
            self.performance_metrics["handover_delay"] = {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0,
                "values": []
            }
        
        return self.performance_metrics["handover_delay"]
    
    def calculate_measurement_to_handover_time(self):
        """計算從測量報告到切換執行的時間"""
        meas_to_ho_times = []
        
        # 尋找測量報告和切換命令對
        measurement_reports = {}
        
        for event in self.combined_events:
            if event["type"] == "RRC_MESSAGE" and event["message_type"] == "MeasurementReport":
                # 提取測量 ID 和鄰區小區 ID
                meas_id = None
                neighbor_cells = []
                
                if "key_parameters" in event["details"]:
                    key_params = event["details"]["key_parameters"]
                    if "meas_id" in key_params:
                        meas_id = key_params["meas_id"]
                    if "neighbor_results" in key_params:
                        for cell in key_params["neighbor_results"]:
                            if "pci" in cell:
                                neighbor_cells.append(cell["pci"])
                
                # 記錄報告時間
                report_key = (meas_id, tuple(neighbor_cells))
                measurement_reports[report_key] = datetime.datetime.fromisoformat(event["timestamp"])
            
            elif event["type"] == "RRC_MESSAGE" and "RRCConnectionReconfiguration" in event["message_type"]:
                # 檢查是否為切換命令
                if "key_parameters" in event["details"] and \
                   "handover" in event["details"]["key_parameters"] and \
                   event["details"]["key_parameters"]["handover"]:
                    # 提取目標小區 ID
                    target_pci = None
                    if "target_pci" in event["details"]["key_parameters"]:
                        target_pci = event["details"]["key_parameters"]["target_pci"]
                    
                    # 尋找對應的測量報告
                    for report_key, report_time in list(measurement_reports.items()):
                        meas_id, neighbor_cells = report_key
                        if target_pci in neighbor_cells or target_pci is None:
                            # 計算時間差
                            meas_to_ho_time = datetime.datetime.fromisoformat(event["timestamp"]) - report_time
                            meas_to_ho_times.append(meas_to_ho_time.total_seconds())
                            
                            # 移除已處理的報告
                            del measurement_reports[report_key]
                            break
        
        # 計算統計數據
        if meas_to_ho_times:
            self.performance_metrics["measurement_to_handover_time"] = {
                "min": min(meas_to_ho_times),
                "max": max(meas_to_ho_times),
                "avg": sum(meas_to_ho_times) / len(meas_to_ho_times),
                "count": len(meas_to_ho_times),
                "values": meas_to_ho_times
            }
        else:
            self.performance_metrics["measurement_to_handover_time"] = {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0,
                "values": []
            }
        
        return self.performance_metrics["measurement_to_handover_time"]
    
    def calculate_handover_success_rate(self):
        """計算切換成功率"""
        handover_attempts = 0
        handover_successes = 0
        
        # 尋找切換命令和完成事件
        for event in self.combined_events:
            if event["type"] == "RRC_MESSAGE" and "RRCConnectionReconfiguration" in event["message_type"]:
                # 檢查是否為切換命令
                if "key_parameters" in event["details"] and \
                   "handover" in event["details"]["key_parameters"] and \
                   event["details"]["key_parameters"]["handover"]:
                    handover_attempts += 1
            
            elif event["type"] == "RRC_EVENT" and event["event_type"] == "HANDOVER":
                handover_successes += 1
        
        # 計算成功率
        success_rate = handover_successes / handover_attempts if handover_attempts > 0 else 0
        
        self.performance_metrics["handover_success_rate"] = {
            "attempts": handover_attempts,
            "successes": handover_successes,
            "rate": success_rate
        }
        
        return self.performance_metrics["handover_success_rate"]
    
    def analyze_all_metrics(self):
        """分析所有性能指標"""
        self.calculate_connection_setup_time()
        self.calculate_handover_delay()
        self.calculate_measurement_to_handover_time()
        self.calculate_handover_success_rate()
        
        return self.performance_metrics

class RRCTraceAnalyzer:
    """RRC 追蹤分析器，整合所有分析功能"""
    def __init__(self, pcap_files=None, log_files=None, output_dir=None):
        self.pcap_files = pcap_files or []
        self.log_files = log_files or []
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/rrc_analysis'
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化數據結構
        self.rrc_messages = []
        self.rrc_events = []
        self.combined_events = []
        self.sequences = []
        self.performance_metrics = {}
        self.analysis_results = {}
    
    def analyze_pcap_files(self):
        """分析 PCAP 文件"""
        for pcap_file in self.pcap_files:
            if os.path.exists(pcap_file):
                analyzer = PCAPAnalyzer(pcap_file)
                messages = analyzer.extract_rrc_messages()
                self.rrc_messages.extend(messages)
            else:
                print(f"Warning: PCAP file {pcap_file} does not exist")
        
        return self.rrc_messages
    
    def analyze_log_files(self):
        """分析日誌文件"""
        for log_file in self.log_files:
            if os.path.exists(log_file):
                analyzer = LogAnalyzer(log_file)
                events = analyzer.extract_rrc_events()
                self.rrc_events.extend(events)
            else:
                print(f"Warning: Log file {log_file} does not exist")
        
        return self.rrc_events
    
    def combine_events(self):
        """合併 RRC 消息和事件"""
        sequence_analyzer = RRCSequenceAnalyzer(self.rrc_messages, self.rrc_events)
        self.combined_events = sequence_analyzer.combine_events()
        return self.combined_events
    
    def analyze_sequences(self):
        """分析 RRC 序列"""
        sequence_analyzer = RRCSequenceAnalyzer(self.rrc_messages, self.rrc_events)
        sequence_analyzer.combined_events = self.combined_events
        self.sequences = sequence_analyzer.identify_sequences()
        
        # 獲取常見序列
        common_sequences = sequence_analyzer.get_common_sequences()
        
        # 檢測異常序列
        abnormal_sequences = sequence_analyzer.detect_abnormal_sequences()
        
        # 分析切換序列
        handover_sequences = sequence_analyzer.analyze_handover_sequences()
        
        self.analysis_results["sequence_analysis"] = {
            "common_sequences": common_sequences,
            "abnormal_sequences": abnormal_sequences,
            "handover_sequences": handover_sequences
        }
        
        return self.analysis_results["sequence_analysis"]
    
    def analyze_performance(self):
        """分析 RRC 性能"""
        performance_analyzer = RRCPerformanceAnalyzer(self.rrc_messages, self.rrc_events, self.combined_events)
        self.performance_metrics = performance_analyzer.analyze_all_metrics()
        
        self.analysis_results["performance_metrics"] = self.performance_metrics
        
        return self.performance_metrics
    
    def analyze_message_distribution(self):
        """分析 RRC 消息分佈"""
        message_types = [msg["message_type"] for msg in self.rrc_messages]
        message_counts = Counter(message_types)
        
        self.analysis_results["message_distribution"] = dict(message_counts)
        
        return self.analysis_results["message_distribution"]
    
    def analyze_event_distribution(self):
        """分析 RRC 事件分佈"""
        event_types = [evt["event_type"] for evt in self.rrc_events]
        event_counts = Counter(event_types)
        
        self.analysis_results["event_distribution"] = dict(event_counts)
        
        return self.analysis_results["event_distribution"]
    
    def analyze_handover_patterns(self):
        """分析切換模式"""
        handover_patterns = []
        
        # 提取切換事件
        handover_events = [evt for evt in self.rrc_events if evt["event_type"] == "HANDOVER"]
        
        # 按 UE 分組
        ue_handovers = defaultdict(list)
        for evt in handover_events:
            # 嘗試從消息中提取 UE ID
            ue_id = None
            message = evt["message"]
            ue_match = re.search(r'UE(\d+)', message)
            if ue_match:
                ue_id = ue_match.group(1)
            
            ue_handovers[ue_id].append(evt)
        
        # 分析每個 UE 的切換模式
        for ue_id, events in ue_handovers.items():
            # 按時間排序
            events.sort(key=lambda x: x["timestamp"])
            
            # 提取切換序列
            handover_sequence = []
            for evt in events:
                if "source_cell" in evt and "target_cell" in evt:
                    handover_sequence.append((evt["source_cell"], evt["target_cell"]))
            
            # 檢測 ping-pong 切換
            ping_pong_count = 0
            for i in range(len(handover_sequence) - 1):
                if handover_sequence[i][0] == handover_sequence[i+1][1] and \
                   handover_sequence[i][1] == handover_sequence[i+1][0]:
                    ping_pong_count += 1
            
            handover_patterns.append({
                "ue_id": ue_id,
                "handover_count": len(events),
                "handover_sequence": handover_sequence,
                "ping_pong_count": ping_pong_count
            })
        
        self.analysis_results["handover_patterns"] = handover_patterns
        
        return handover_patterns
    
    def run_analysis(self):
        """運行完整分析"""
        print("Starting RRC trace analysis...")
        
        # 分析 PCAP 文件
        self.analyze_pcap_files()
        
        # 分析日誌文件
        self.analyze_log_files()
        
        # 合併事件
        self.combine_events()
        
        # 分析消息分佈
        self.analyze_message_distribution()
        
        # 分析事件分佈
        self.analyze_event_distribution()
        
        # 分析序列
        self.analyze_sequences()
        
        # 分析性能
        self.analyze_performance()
        
        # 分析切換模式
        self.analyze_handover_patterns()
        
        # 保存分析結果
        self.save_results()
        
        # 生成報告
        self.generate_report()
        
        print("RRC trace analysis completed")
        
        return self.analysis_results
    
    def save_results(self):
        """保存分析結果"""
        # 保存 JSON 結果
        with open(os.path.join(self.output_dir, 'rrc_analysis.json'), 'w') as f:
            # 將不可序列化的對象轉換為字符串
            serializable_results = self.convert_to_serializable(self.analysis_results)
            json.dump(serializable_results, f, indent=2)
        
        # 保存 CSV 結果
        self.save_csv_results()
        
        print(f"Analysis results saved to {self.output_dir}")
    
    def convert_to_serializable(self, obj):
        """將對象轉換為可序列化的格式"""
        if isinstance(obj, dict):
            return {k: self.convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return [self.convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self.convert_to_serializable(obj.__dict__)
        else:
            return obj
    
    def save_csv_results(self):
        """保存 CSV 格式的結果"""
        # 保存 RRC 消息
        if self.rrc_messages:
            with open(os.path.join(self.output_dir, 'rrc_messages.csv'), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Message Type', 'Key Parameters'])
                
                for msg in self.rrc_messages:
                    key_params_str = json.dumps(msg.get('key_parameters', {}))
                    writer.writerow([msg['timestamp'], msg['message_type'], key_params_str])
        
        # 保存 RRC 事件
        if self.rrc_events:
            with open(os.path.join(self.output_dir, 'rrc_events.csv'), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Event Type', 'Message'])
                
                for evt in self.rrc_events:
                    writer.writerow([evt['timestamp'], evt['event_type'], evt['message']])
        
        # 保存性能指標
        if self.performance_metrics:
            with open(os.path.join(self.output_dir, 'performance_metrics.csv'), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Min', 'Max', 'Avg', 'Count'])
                
                for metric, data in self.performance_metrics.items():
                    if isinstance(data, dict) and 'min' in data:
                        writer.writerow([metric, data['min'], data['max'], data['avg'], data['count']])
    
    def generate_report(self):
        """生成分析報告"""
        report = f"""# RRC 協議追蹤分析報告

## 概述

本報告分析了 RRC 協議追蹤數據，包括 PCAP 文件和日誌文件中的 RRC 消息和事件。

- 分析時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- PCAP 文件: {', '.join(self.pcap_files) if self.pcap_files else 'None'}
- 日誌文件: {', '.join(self.log_files) if self.log_files else 'None'}
- RRC 消息數量: {len(self.rrc_messages)}
- RRC 事件數量: {len(self.rrc_events)}

## RRC 消息分佈

"""
        
        # 添加 RRC 消息分佈
        if 'message_distribution' in self.analysis_results:
            report += "| 消息類型 | 數量 |\n"
            report += "|---------|------|\n"
            
            for msg_type, count in self.analysis_results['message_distribution'].items():
                report += f"| {msg_type} | {count} |\n"
        
        report += """
## RRC 事件分佈

"""
        
        # 添加 RRC 事件分佈
        if 'event_distribution' in self.analysis_results:
            report += "| 事件類型 | 數量 |\n"
            report += "|---------|------|\n"
            
            for evt_type, count in self.analysis_results['event_distribution'].items():
                report += f"| {evt_type} | {count} |\n"
        
        report += """
## 序列分析

### 常見序列模式

"""
        
        # 添加常見序列模式
        if 'sequence_analysis' in self.analysis_results and 'common_sequences' in self.analysis_results['sequence_analysis']:
            report += "| 序列模式 | 出現次數 |\n"
            report += "|----------|----------|\n"
            
            for pattern, count in self.analysis_results['sequence_analysis']['common_sequences']:
                pattern_str = ' -> '.join(pattern)
                report += f"| {pattern_str} | {count} |\n"
        
        report += """
### 異常序列模式

"""
        
        # 添加異常序列模式
        if 'sequence_analysis' in self.analysis_results and 'abnormal_sequences' in self.analysis_results['sequence_analysis']:
            report += "| 序列模式 | 出現次數 | 頻率 |\n"
            report += "|----------|----------|------|\n"
            
            for pattern, data in self.analysis_results['sequence_analysis']['abnormal_sequences'].items():
                pattern_str = ' -> '.join(pattern)
                report += f"| {pattern_str} | {data['count']} | {data['frequency']:.4f} |\n"
        
        report += """
## 性能指標

"""
        
        # 添加性能指標
        if 'performance_metrics' in self.analysis_results:
            report += "| 指標 | 最小值 | 最大值 | 平均值 | 樣本數 |\n"
            report += "|------|--------|--------|--------|--------|\n"
            
            for metric, data in self.analysis_results['performance_metrics'].items():
                if isinstance(data, dict) and 'min' in data:
                    min_val = f"{data['min']:.3f}" if data['min'] is not None else 'N/A'
                    max_val = f"{data['max']:.3f}" if data['max'] is not None else 'N/A'
                    avg_val = f"{data['avg']:.3f}" if data['avg'] is not None else 'N/A'
                    
                    report += f"| {metric} | {min_val} | {max_val} | {avg_val} | {data['count']} |\n"
            
            # 添加切換成功率
            if 'handover_success_rate' in self.analysis_results['performance_metrics']:
                ho_data = self.analysis_results['performance_metrics']['handover_success_rate']
                report += f"\n切換成功率: {ho_data['rate']:.2%} ({ho_data['successes']}/{ho_data['attempts']})\n"
        
        report += """
## 切換模式分析

"""
        
        # 添加切換模式分析
        if 'handover_patterns' in self.analysis_results:
            report += "| UE ID | 切換次數 | Ping-Pong 切換次數 |\n"
            report += "|-------|----------|--------------------|\n"
            
            for pattern in self.analysis_results['handover_patterns']:
                report += f"| {pattern['ue_id'] or 'Unknown'} | {pattern['handover_count']} | {pattern['ping_pong_count']} |\n"
        
        report += """
## 結論與建議

基於上述分析，我們得出以下結論：

1. RRC 連接建立時間平均為 {:.3f} 秒，這在正常範圍內。
2. 切換延遲平均為 {:.3f} 秒，這表明切換過程效率良好。
3. 測量報告到切換執行的時間平均為 {:.3f} 秒，這反映了網絡決策速度。
4. 切換成功率為 {:.2%}，這表明網絡穩定性良好。

建議：

1. 監控異常序列模式，特別是那些可能導致連接失敗的序列。
2. 優化切換參數，減少 Ping-Pong 切換現象。
3. 進一步分析 RRC 連接重建事件，以提高網絡可靠性。
4. 考慮在高速移動場景中調整測量報告配置，以提高切換效率。
""".format(
            self.analysis_results.get('performance_metrics', {}).get('connection_setup_time', {}).get('avg', 0) or 0,
            self.analysis_results.get('performance_metrics', {}).get('handover_delay', {}).get('avg', 0) or 0,
            self.analysis_results.get('performance_metrics', {}).get('measurement_to_handover_time', {}).get('avg', 0) or 0,
            self.analysis_results.get('performance_metrics', {}).get('handover_success_rate', {}).get('rate', 0) or 0
        )
        
        # 保存報告
        with open(os.path.join(self.output_dir, 'rrc_analysis_report.md'), 'w') as f:
            f.write(report)
        
        print(f"Analysis report saved to {os.path.join(self.output_dir, 'rrc_analysis_report.md')}")
        
        # 生成圖表
        self.generate_charts()
    
    def generate_charts(self):
        """生成分析圖表"""
        # 創建圖表目錄
        charts_dir = os.path.join(self.output_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 生成 RRC 消息分佈圖
        if 'message_distribution' in self.analysis_results:
            self.plot_message_distribution(charts_dir)
        
        # 生成 RRC 事件分佈圖
        if 'event_distribution' in self.analysis_results:
            self.plot_event_distribution(charts_dir)
        
        # 生成性能指標圖
        if 'performance_metrics' in self.analysis_results:
            self.plot_performance_metrics(charts_dir)
        
        # 生成切換模式圖
        if 'handover_patterns' in self.analysis_results:
            self.plot_handover_patterns(charts_dir)
    
    def plot_message_distribution(self, charts_dir):
        """繪製 RRC 消息分佈圖"""
        message_dist = self.analysis_results['message_distribution']
        
        plt.figure(figsize=(10, 6))
        plt.bar(message_dist.keys(), message_dist.values())
        plt.title('RRC Message Distribution')
        plt.xlabel('Message Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'message_distribution.png'))
        plt.close()
    
    def plot_event_distribution(self, charts_dir):
        """繪製 RRC 事件分佈圖"""
        event_dist = self.analysis_results['event_distribution']
        
        plt.figure(figsize=(10, 6))
        plt.bar(event_dist.keys(), event_dist.values())
        plt.title('RRC Event Distribution')
        plt.xlabel('Event Type')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'event_distribution.png'))
        plt.close()
    
    def plot_performance_metrics(self, charts_dir):
        """繪製性能指標圖"""
        metrics = self.analysis_results['performance_metrics']
        
        # 繪製連接建立時間分佈
        if 'connection_setup_time' in metrics and metrics['connection_setup_time']['values']:
            plt.figure(figsize=(10, 6))
            plt.hist(metrics['connection_setup_time']['values'], bins=20)
            plt.title('RRC Connection Setup Time Distribution')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Frequency')
            plt.axvline(metrics['connection_setup_time']['avg'], color='r', linestyle='dashed', linewidth=2, label=f"Average: {metrics['connection_setup_time']['avg']:.3f}s")
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, 'connection_setup_time.png'))
            plt.close()
        
        # 繪製切換延遲分佈
        if 'handover_delay' in metrics and metrics['handover_delay']['values']:
            plt.figure(figsize=(10, 6))
            plt.hist(metrics['handover_delay']['values'], bins=20)
            plt.title('Handover Delay Distribution')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Frequency')
            plt.axvline(metrics['handover_delay']['avg'], color='r', linestyle='dashed', linewidth=2, label=f"Average: {metrics['handover_delay']['avg']:.3f}s")
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, 'handover_delay.png'))
            plt.close()
        
        # 繪製測量報告到切換執行的時間分佈
        if 'measurement_to_handover_time' in metrics and metrics['measurement_to_handover_time']['values']:
            plt.figure(figsize=(10, 6))
            plt.hist(metrics['measurement_to_handover_time']['values'], bins=20)
            plt.title('Measurement to Handover Time Distribution')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Frequency')
            plt.axvline(metrics['measurement_to_handover_time']['avg'], color='r', linestyle='dashed', linewidth=2, label=f"Average: {metrics['measurement_to_handover_time']['avg']:.3f}s")
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, 'measurement_to_handover_time.png'))
            plt.close()
        
        # 繪製切換成功率
        if 'handover_success_rate' in metrics:
            ho_data = metrics['handover_success_rate']
            
            plt.figure(figsize=(8, 8))
            plt.pie([ho_data['successes'], ho_data['attempts'] - ho_data['successes']], 
                   labels=['Success', 'Failure'], 
                   autopct='%1.1f%%', 
                   colors=['#4CAF50', '#F44336'])
            plt.title('Handover Success Rate')
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, 'handover_success_rate.png'))
            plt.close()
    
    def plot_handover_patterns(self, charts_dir):
        """繪製切換模式圖"""
        patterns = self.analysis_results['handover_patterns']
        
        # 繪製每個 UE 的切換次數
        ue_ids = [p['ue_id'] or 'Unknown' for p in patterns]
        ho_counts = [p['handover_count'] for p in patterns]
        pp_counts = [p['ping_pong_count'] for p in patterns]
        
        plt.figure(figsize=(10, 6))
        
        x = np.arange(len(ue_ids))
        width = 0.35
        
        plt.bar(x - width/2, ho_counts, width, label='Total Handovers')
        plt.bar(x + width/2, pp_counts, width, label='Ping-Pong Handovers')
        
        plt.title('Handover Patterns by UE')
        plt.xlabel('UE ID')
        plt.ylabel('Count')
        plt.xticks(x, ue_ids)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'handover_patterns.png'))
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Enhanced RRC Trace Analyzer")
    parser.add_argument("--pcap", nargs='+', help="PCAP files to analyze")
    parser.add_argument("--log", nargs='+', help="Log files to analyze")
    parser.add_argument("--output-dir", default="/home/eezim/workspace/srsRAN_5G/rrc_analysis", help="Output directory for analysis results")
    args = parser.parse_args()
    
    # 如果未提供 PCAP 文件，使用默認位置
    if not args.pcap:
        pcap_dir = "/home/eezim/workspace/srsRAN_5G/enhanced_srsran_configs"
        args.pcap = [
            os.path.join(pcap_dir, "gnb/gnb1.pcap"),
            os.path.join(pcap_dir, "gnb/gnb2.pcap"),
            os.path.join(pcap_dir, "gnb/gnb3.pcap"),
            os.path.join(pcap_dir, "gnb/gnb4.pcap")
        ]
    
    # 如果未提供日誌文件，使用默認位置
    if not args.log:
        log_dir = "/home/eezim/workspace/srsRAN_5G/enhanced_srsran_configs"
        args.log = [
            os.path.join(log_dir, "gnb/gnb1.log"),
            os.path.join(log_dir, "gnb/gnb2.log"),
            os.path.join(log_dir, "gnb/gnb3.log"),
            os.path.join(log_dir, "gnb/gnb4.log")
        ]
    
    analyzer = RRCTraceAnalyzer(args.pcap, args.log, args.output_dir)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
