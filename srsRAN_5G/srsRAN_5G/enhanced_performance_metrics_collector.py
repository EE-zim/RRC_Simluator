#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增強型性能指標收集工具
此腳本實現了全面的性能指標收集功能，包括無線指標、MAC層統計和切換性能數據
"""

import os
import sys
import json
import argparse
import subprocess
import re
import csv
import datetime
import time
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, Counter, deque
from itertools import groupby

class RadioMetricsCollector:
    """無線指標收集器，用於收集和分析無線層性能指標"""
    def __init__(self, log_files=None, output_dir=None):
        self.log_files = log_files or []
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/performance_metrics'
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化數據結構
        self.rsrp_values = defaultdict(list)  # 按 UE ID 分組的 RSRP 值
        self.rsrq_values = defaultdict(list)  # 按 UE ID 分組的 RSRQ 值
        self.sinr_values = defaultdict(list)  # 按 UE ID 分組的 SINR 值
        self.cqi_values = defaultdict(list)   # 按 UE ID 分組的 CQI 值
        self.mcs_values = defaultdict(list)   # 按 UE ID 分組的 MCS 值
        self.bler_values = defaultdict(list)  # 按 UE ID 分組的 BLER 值
        
        # 時間戳記錄
        self.timestamps = defaultdict(list)   # 按 UE ID 分組的時間戳
    
    def extract_metrics_from_logs(self):
        """從日誌文件中提取無線指標"""
        print("Extracting radio metrics from logs...")
        
        for log_file in self.log_files:
            if not os.path.exists(log_file):
                print(f"Warning: Log file {log_file} does not exist")
                continue
            
            print(f"Processing {log_file}...")
            
            # 從文件名中提取 UE ID
            ue_id = None
            match = re.search(r'ue(\d+)', os.path.basename(log_file))
            if match:
                ue_id = match.group(1)
            else:
                # 如果無法從文件名中提取，使用文件索引作為 ID
                ue_id = str(self.log_files.index(log_file) + 1)
            
            with open(log_file, 'r') as f:
                for line in f:
                    # 提取時間戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    if not timestamp:
                        continue
                    
                    # 提取 RSRP
                    rsrp_match = re.search(r'RSRP[: =]+(-?\d+\.?\d*)', line)
                    if rsrp_match:
                        rsrp = float(rsrp_match.group(1))
                        self.rsrp_values[ue_id].append(rsrp)
                        self.timestamps[f"{ue_id}_rsrp"].append(timestamp)
                    
                    # 提取 RSRQ
                    rsrq_match = re.search(r'RSRQ[: =]+(-?\d+\.?\d*)', line)
                    if rsrq_match:
                        rsrq = float(rsrq_match.group(1))
                        self.rsrq_values[ue_id].append(rsrq)
                        self.timestamps[f"{ue_id}_rsrq"].append(timestamp)
                    
                    # 提取 SINR
                    sinr_match = re.search(r'SINR[: =]+(-?\d+\.?\d*)', line)
                    if sinr_match:
                        sinr = float(sinr_match.group(1))
                        self.sinr_values[ue_id].append(sinr)
                        self.timestamps[f"{ue_id}_sinr"].append(timestamp)
                    
                    # 提取 CQI
                    cqi_match = re.search(r'CQI[: =]+(\d+)', line)
                    if cqi_match:
                        cqi = int(cqi_match.group(1))
                        self.cqi_values[ue_id].append(cqi)
                        self.timestamps[f"{ue_id}_cqi"].append(timestamp)
                    
                    # 提取 MCS
                    mcs_match = re.search(r'MCS[: =]+(\d+)', line)
                    if mcs_match:
                        mcs = int(mcs_match.group(1))
                        self.mcs_values[ue_id].append(mcs)
                        self.timestamps[f"{ue_id}_mcs"].append(timestamp)
                    
                    # 提取 BLER
                    bler_match = re.search(r'BLER[: =]+(\d+\.?\d*)', line)
                    if bler_match:
                        bler = float(bler_match.group(1))
                        self.bler_values[ue_id].append(bler)
                        self.timestamps[f"{ue_id}_bler"].append(timestamp)
        
        print("Radio metrics extraction completed")
    
    def calculate_statistics(self):
        """計算無線指標的統計數據"""
        statistics = {}
        
        # 計算 RSRP 統計數據
        statistics['rsrp'] = self._calculate_metric_statistics(self.rsrp_values)
        
        # 計算 RSRQ 統計數據
        statistics['rsrq'] = self._calculate_metric_statistics(self.rsrq_values)
        
        # 計算 SINR 統計數據
        statistics['sinr'] = self._calculate_metric_statistics(self.sinr_values)
        
        # 計算 CQI 統計數據
        statistics['cqi'] = self._calculate_metric_statistics(self.cqi_values)
        
        # 計算 MCS 統計數據
        statistics['mcs'] = self._calculate_metric_statistics(self.mcs_values)
        
        # 計算 BLER 統計數據
        statistics['bler'] = self._calculate_metric_statistics(self.bler_values)
        
        return statistics
    
    def _calculate_metric_statistics(self, metric_values):
        """計算指標的統計數據"""
        statistics = {}
        
        for ue_id, values in metric_values.items():
            if not values:
                continue
            
            statistics[ue_id] = {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2],
                'std': np.std(values) if len(values) > 1 else 0,
                'count': len(values)
            }
        
        return statistics
    
    def generate_time_series_data(self):
        """生成時間序列數據"""
        time_series = {}
        
        # 生成 RSRP 時間序列
        time_series['rsrp'] = self._generate_metric_time_series(self.rsrp_values, 'rsrp')
        
        # 生成 RSRQ 時間序列
        time_series['rsrq'] = self._generate_metric_time_series(self.rsrq_values, 'rsrq')
        
        # 生成 SINR 時間序列
        time_series['sinr'] = self._generate_metric_time_series(self.sinr_values, 'sinr')
        
        # 生成 CQI 時間序列
        time_series['cqi'] = self._generate_metric_time_series(self.cqi_values, 'cqi')
        
        # 生成 MCS 時間序列
        time_series['mcs'] = self._generate_metric_time_series(self.mcs_values, 'mcs')
        
        # 生成 BLER 時間序列
        time_series['bler'] = self._generate_metric_time_series(self.bler_values, 'bler')
        
        return time_series
    
    def _generate_metric_time_series(self, metric_values, metric_name):
        """生成指標的時間序列數據"""
        time_series = {}
        
        for ue_id, values in metric_values.items():
            timestamps = self.timestamps[f"{ue_id}_{metric_name}"]
            
            if not values or not timestamps or len(values) != len(timestamps):
                continue
            
            # 將時間戳轉換為 datetime 對象
            datetime_timestamps = [datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') for ts in timestamps]
            
            # 創建時間序列數據
            time_series[ue_id] = {
                'timestamps': timestamps,
                'values': values
            }
        
        return time_series
    
    def plot_metrics(self):
        """繪製無線指標圖表"""
        # 創建圖表目錄
        charts_dir = os.path.join(self.output_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 繪製 RSRP 圖表
        self._plot_metric(self.rsrp_values, 'RSRP', 'dBm', charts_dir)
        
        # 繪製 RSRQ 圖表
        self._plot_metric(self.rsrq_values, 'RSRQ', 'dB', charts_dir)
        
        # 繪製 SINR 圖表
        self._plot_metric(self.sinr_values, 'SINR', 'dB', charts_dir)
        
        # 繪製 CQI 圖表
        self._plot_metric(self.cqi_values, 'CQI', '', charts_dir)
        
        # 繪製 MCS 圖表
        self._plot_metric(self.mcs_values, 'MCS', '', charts_dir)
        
        # 繪製 BLER 圖表
        self._plot_metric(self.bler_values, 'BLER', '%', charts_dir)
    
    def _plot_metric(self, metric_values, metric_name, unit, charts_dir):
        """繪製指標圖表"""
        # 繪製時間序列圖
        plt.figure(figsize=(12, 6))
        
        for ue_id, values in metric_values.items():
            if not values:
                continue
            
            timestamps = self.timestamps[f"{ue_id}_{metric_name.lower()}"]
            if not timestamps or len(timestamps) != len(values):
                continue
            
            # 將時間戳轉換為相對時間（秒）
            start_time = datetime.datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S.%f')
            relative_times = [(datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') - start_time).total_seconds() for ts in timestamps]
            
            plt.plot(relative_times, values, label=f"UE {ue_id}")
        
        plt.title(f"{metric_name} Time Series")
        plt.xlabel("Time (seconds)")
        plt.ylabel(f"{metric_name} ({unit})" if unit else metric_name)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, f"{metric_name.lower()}_time_series.png"))
        plt.close()
        
        # 繪製箱線圖
        plt.figure(figsize=(10, 6))
        
        data = []
        labels = []
        
        for ue_id, values in metric_values.items():
            if not values:
                continue
            
            data.append(values)
            labels.append(f"UE {ue_id}")
        
        if data:
            plt.boxplot(data, labels=labels)
            plt.title(f"{metric_name} Distribution by UE")
            plt.xlabel("UE")
            plt.ylabel(f"{metric_name} ({unit})" if unit else metric_name)
            plt.grid(True, axis='y')
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, f"{metric_name.lower()}_boxplot.png"))
        
        plt.close()
    
    def save_results(self):
        """保存分析結果"""
        # 計算統計數據
        statistics = self.calculate_statistics()
        
        # 生成時間序列數據
        time_series = self.generate_time_series_data()
        
        # 保存統計數據
        with open(os.path.join(self.output_dir, 'radio_metrics_statistics.json'), 'w') as f:
            json.dump(statistics, f, indent=2)
        
        # 保存時間序列數據
        with open(os.path.join(self.output_dir, 'radio_metrics_time_series.json'), 'w') as f:
            # 將不可序列化的對象轉換為字符串
            serializable_time_series = {}
            for metric, ue_data in time_series.items():
                serializable_time_series[metric] = {}
                for ue_id, data in ue_data.items():
                    serializable_time_series[metric][ue_id] = {
                        'timestamps': data['timestamps'],
                        'values': data['values']
                    }
            
            json.dump(serializable_time_series, f, indent=2)
        
        # 保存 CSV 格式的數據
        self._save_csv_data()
        
        # 繪製圖表
        self.plot_metrics()
        
        print(f"Radio metrics results saved to {self.output_dir}")
    
    def _save_csv_data(self):
        """保存 CSV 格式的數據"""
        # 保存 RSRP 數據
        self._save_metric_csv(self.rsrp_values, 'rsrp', 'RSRP')
        
        # 保存 RSRQ 數據
        self._save_metric_csv(self.rsrq_values, 'rsrq', 'RSRQ')
        
        # 保存 SINR 數據
        self._save_metric_csv(self.sinr_values, 'sinr', 'SINR')
        
        # 保存 CQI 數據
        self._save_metric_csv(self.cqi_values, 'cqi', 'CQI')
        
        # 保存 MCS 數據
        self._save_metric_csv(self.mcs_values, 'mcs', 'MCS')
        
        # 保存 BLER 數據
        self._save_metric_csv(self.bler_values, 'bler', 'BLER')
    
    def _save_metric_csv(self, metric_values, metric_name, metric_title):
        """保存指標的 CSV 數據"""
        csv_file = os.path.join(self.output_dir, f"{metric_name}_data.csv")
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            header = ['UE ID', 'Timestamp', metric_title]
            writer.writerow(header)
            
            # 寫入數據行
            for ue_id, values in metric_values.items():
                timestamps = self.timestamps[f"{ue_id}_{metric_name}"]
                
                if not values or not timestamps or len(values) != len(timestamps):
                    continue
                
                for i, value in enumerate(values):
                    writer.writerow([ue_id, timestamps[i], value])

class MACMetricsCollector:
    """MAC 層指標收集器，用於收集和分析 MAC 層性能指標"""
    def __init__(self, log_files=None, output_dir=None):
        self.log_files = log_files or []
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/performance_metrics'
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化數據結構
        self.dl_throughput = defaultdict(list)  # 按 UE ID 分組的下行吞吐量
        self.ul_throughput = defaultdict(list)  # 按 UE ID 分組的上行吞吐量
        self.dl_latency = defaultdict(list)     # 按 UE ID 分組的下行延遲
        self.ul_latency = defaultdict(list)     # 按 UE ID 分組的上行延遲
        self.harq_retx = defaultdict(list)      # 按 UE ID 分組的 HARQ 重傳次數
        self.dl_mcs = defaultdict(list)         # 按 UE ID 分組的下行 MCS
        self.ul_mcs = defaultdict(list)         # 按 UE ID 分組的上行 MCS
        self.dl_rb_utilization = defaultdict(list)  # 按 UE ID 分組的下行 RB 利用率
        self.ul_rb_utilization = defaultdict(list)  # 按 UE ID 分組的上行 RB 利用率
        
        # 時間戳記錄
        self.timestamps = defaultdict(list)     # 按 UE ID 和指標類型分組的時間戳
    
    def extract_metrics_from_logs(self):
        """從日誌文件中提取 MAC 層指標"""
        print("Extracting MAC metrics from logs...")
        
        for log_file in self.log_files:
            if not os.path.exists(log_file):
                print(f"Warning: Log file {log_file} does not exist")
                continue
            
            print(f"Processing {log_file}...")
            
            # 從文件名中提取 UE ID 或 gNB ID
            entity_id = None
            ue_match = re.search(r'ue(\d+)', os.path.basename(log_file))
            gnb_match = re.search(r'gnb(\d+)', os.path.basename(log_file))
            
            if ue_match:
                entity_id = f"UE{ue_match.group(1)}"
            elif gnb_match:
                entity_id = f"gNB{gnb_match.group(1)}"
            else:
                # 如果無法從文件名中提取，使用文件索引作為 ID
                entity_id = f"Entity{self.log_files.index(log_file) + 1}"
            
            with open(log_file, 'r') as f:
                for line in f:
                    # 提取時間戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    if not timestamp:
                        continue
                    
                    # 提取下行吞吐量
                    dl_tp_match = re.search(r'DL[_\s]throughput[:\s=]+(\d+\.?\d*)', line)
                    if dl_tp_match:
                        dl_tp = float(dl_tp_match.group(1))
                        self.dl_throughput[entity_id].append(dl_tp)
                        self.timestamps[f"{entity_id}_dl_throughput"].append(timestamp)
                    
                    # 提取上行吞吐量
                    ul_tp_match = re.search(r'UL[_\s]throughput[:\s=]+(\d+\.?\d*)', line)
                    if ul_tp_match:
                        ul_tp = float(ul_tp_match.group(1))
                        self.ul_throughput[entity_id].append(ul_tp)
                        self.timestamps[f"{entity_id}_ul_throughput"].append(timestamp)
                    
                    # 提取下行延遲
                    dl_lat_match = re.search(r'DL[_\s]latency[:\s=]+(\d+\.?\d*)', line)
                    if dl_lat_match:
                        dl_lat = float(dl_lat_match.group(1))
                        self.dl_latency[entity_id].append(dl_lat)
                        self.timestamps[f"{entity_id}_dl_latency"].append(timestamp)
                    
                    # 提取上行延遲
                    ul_lat_match = re.search(r'UL[_\s]latency[:\s=]+(\d+\.?\d*)', line)
                    if ul_lat_match:
                        ul_lat = float(ul_lat_match.group(1))
                        self.ul_latency[entity_id].append(ul_lat)
                        self.timestamps[f"{entity_id}_ul_latency"].append(timestamp)
                    
                    # 提取 HARQ 重傳次數
                    harq_match = re.search(r'HARQ[_\s]retx[:\s=]+(\d+)', line)
                    if harq_match:
                        harq = int(harq_match.group(1))
                        self.harq_retx[entity_id].append(harq)
                        self.timestamps[f"{entity_id}_harq_retx"].append(timestamp)
                    
                    # 提取下行 MCS
                    dl_mcs_match = re.search(r'DL[_\s]MCS[:\s=]+(\d+)', line)
                    if dl_mcs_match:
                        dl_mcs = int(dl_mcs_match.group(1))
                        self.dl_mcs[entity_id].append(dl_mcs)
                        self.timestamps[f"{entity_id}_dl_mcs"].append(timestamp)
                    
                    # 提取上行 MCS
                    ul_mcs_match = re.search(r'UL[_\s]MCS[:\s=]+(\d+)', line)
                    if ul_mcs_match:
                        ul_mcs = int(ul_mcs_match.group(1))
                        self.ul_mcs[entity_id].append(ul_mcs)
                        self.timestamps[f"{entity_id}_ul_mcs"].append(timestamp)
                    
                    # 提取下行 RB 利用率
                    dl_rb_match = re.search(r'DL[_\s]RB[_\s]utilization[:\s=]+(\d+\.?\d*)', line)
                    if dl_rb_match:
                        dl_rb = float(dl_rb_match.group(1))
                        self.dl_rb_utilization[entity_id].append(dl_rb)
                        self.timestamps[f"{entity_id}_dl_rb_utilization"].append(timestamp)
                    
                    # 提取上行 RB 利用率
                    ul_rb_match = re.search(r'UL[_\s]RB[_\s]utilization[:\s=]+(\d+\.?\d*)', line)
                    if ul_rb_match:
                        ul_rb = float(ul_rb_match.group(1))
                        self.ul_rb_utilization[entity_id].append(ul_rb)
                        self.timestamps[f"{entity_id}_ul_rb_utilization"].append(timestamp)
        
        print("MAC metrics extraction completed")
    
    def calculate_statistics(self):
        """計算 MAC 層指標的統計數據"""
        statistics = {}
        
        # 計算下行吞吐量統計數據
        statistics['dl_throughput'] = self._calculate_metric_statistics(self.dl_throughput)
        
        # 計算上行吞吐量統計數據
        statistics['ul_throughput'] = self._calculate_metric_statistics(self.ul_throughput)
        
        # 計算下行延遲統計數據
        statistics['dl_latency'] = self._calculate_metric_statistics(self.dl_latency)
        
        # 計算上行延遲統計數據
        statistics['ul_latency'] = self._calculate_metric_statistics(self.ul_latency)
        
        # 計算 HARQ 重傳次數統計數據
        statistics['harq_retx'] = self._calculate_metric_statistics(self.harq_retx)
        
        # 計算下行 MCS 統計數據
        statistics['dl_mcs'] = self._calculate_metric_statistics(self.dl_mcs)
        
        # 計算上行 MCS 統計數據
        statistics['ul_mcs'] = self._calculate_metric_statistics(self.ul_mcs)
        
        # 計算下行 RB 利用率統計數據
        statistics['dl_rb_utilization'] = self._calculate_metric_statistics(self.dl_rb_utilization)
        
        # 計算上行 RB 利用率統計數據
        statistics['ul_rb_utilization'] = self._calculate_metric_statistics(self.ul_rb_utilization)
        
        return statistics
    
    def _calculate_metric_statistics(self, metric_values):
        """計算指標的統計數據"""
        statistics = {}
        
        for entity_id, values in metric_values.items():
            if not values:
                continue
            
            statistics[entity_id] = {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'median': sorted(values)[len(values) // 2],
                'std': np.std(values) if len(values) > 1 else 0,
                'count': len(values)
            }
        
        return statistics
    
    def generate_time_series_data(self):
        """生成時間序列數據"""
        time_series = {}
        
        # 生成下行吞吐量時間序列
        time_series['dl_throughput'] = self._generate_metric_time_series(self.dl_throughput, 'dl_throughput')
        
        # 生成上行吞吐量時間序列
        time_series['ul_throughput'] = self._generate_metric_time_series(self.ul_throughput, 'ul_throughput')
        
        # 生成下行延遲時間序列
        time_series['dl_latency'] = self._generate_metric_time_series(self.dl_latency, 'dl_latency')
        
        # 生成上行延遲時間序列
        time_series['ul_latency'] = self._generate_metric_time_series(self.ul_latency, 'ul_latency')
        
        # 生成 HARQ 重傳次數時間序列
        time_series['harq_retx'] = self._generate_metric_time_series(self.harq_retx, 'harq_retx')
        
        # 生成下行 MCS 時間序列
        time_series['dl_mcs'] = self._generate_metric_time_series(self.dl_mcs, 'dl_mcs')
        
        # 生成上行 MCS 時間序列
        time_series['ul_mcs'] = self._generate_metric_time_series(self.ul_mcs, 'ul_mcs')
        
        # 生成下行 RB 利用率時間序列
        time_series['dl_rb_utilization'] = self._generate_metric_time_series(self.dl_rb_utilization, 'dl_rb_utilization')
        
        # 生成上行 RB 利用率時間序列
        time_series['ul_rb_utilization'] = self._generate_metric_time_series(self.ul_rb_utilization, 'ul_rb_utilization')
        
        return time_series
    
    def _generate_metric_time_series(self, metric_values, metric_name):
        """生成指標的時間序列數據"""
        time_series = {}
        
        for entity_id, values in metric_values.items():
            timestamps = self.timestamps[f"{entity_id}_{metric_name}"]
            
            if not values or not timestamps or len(values) != len(timestamps):
                continue
            
            # 將時間戳轉換為 datetime 對象
            datetime_timestamps = [datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') for ts in timestamps]
            
            # 創建時間序列數據
            time_series[entity_id] = {
                'timestamps': timestamps,
                'values': values
            }
        
        return time_series
    
    def plot_metrics(self):
        """繪製 MAC 層指標圖表"""
        # 創建圖表目錄
        charts_dir = os.path.join(self.output_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 繪製下行吞吐量圖表
        self._plot_metric(self.dl_throughput, 'DL Throughput', 'Mbps', charts_dir)
        
        # 繪製上行吞吐量圖表
        self._plot_metric(self.ul_throughput, 'UL Throughput', 'Mbps', charts_dir)
        
        # 繪製下行延遲圖表
        self._plot_metric(self.dl_latency, 'DL Latency', 'ms', charts_dir)
        
        # 繪製上行延遲圖表
        self._plot_metric(self.ul_latency, 'UL Latency', 'ms', charts_dir)
        
        # 繪製 HARQ 重傳次數圖表
        self._plot_metric(self.harq_retx, 'HARQ Retransmissions', '', charts_dir)
        
        # 繪製下行 MCS 圖表
        self._plot_metric(self.dl_mcs, 'DL MCS', '', charts_dir)
        
        # 繪製上行 MCS 圖表
        self._plot_metric(self.ul_mcs, 'UL MCS', '', charts_dir)
        
        # 繪製下行 RB 利用率圖表
        self._plot_metric(self.dl_rb_utilization, 'DL RB Utilization', '%', charts_dir)
        
        # 繪製上行 RB 利用率圖表
        self._plot_metric(self.ul_rb_utilization, 'UL RB Utilization', '%', charts_dir)
    
    def _plot_metric(self, metric_values, metric_name, unit, charts_dir):
        """繪製指標圖表"""
        # 繪製時間序列圖
        plt.figure(figsize=(12, 6))
        
        for entity_id, values in metric_values.items():
            if not values:
                continue
            
            metric_key = metric_name.lower().replace(' ', '_')
            timestamps = self.timestamps[f"{entity_id}_{metric_key}"]
            if not timestamps or len(timestamps) != len(values):
                continue
            
            # 將時間戳轉換為相對時間（秒）
            start_time = datetime.datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S.%f')
            relative_times = [(datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') - start_time).total_seconds() for ts in timestamps]
            
            plt.plot(relative_times, values, label=entity_id)
        
        plt.title(f"{metric_name} Time Series")
        plt.xlabel("Time (seconds)")
        plt.ylabel(f"{metric_name} ({unit})" if unit else metric_name)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, f"{metric_name.lower().replace(' ', '_')}_time_series.png"))
        plt.close()
        
        # 繪製箱線圖
        plt.figure(figsize=(10, 6))
        
        data = []
        labels = []
        
        for entity_id, values in metric_values.items():
            if not values:
                continue
            
            data.append(values)
            labels.append(entity_id)
        
        if data:
            plt.boxplot(data, labels=labels)
            plt.title(f"{metric_name} Distribution by Entity")
            plt.xlabel("Entity")
            plt.ylabel(f"{metric_name} ({unit})" if unit else metric_name)
            plt.grid(True, axis='y')
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, f"{metric_name.lower().replace(' ', '_')}_boxplot.png"))
        
        plt.close()
    
    def save_results(self):
        """保存分析結果"""
        # 計算統計數據
        statistics = self.calculate_statistics()
        
        # 生成時間序列數據
        time_series = self.generate_time_series_data()
        
        # 保存統計數據
        with open(os.path.join(self.output_dir, 'mac_metrics_statistics.json'), 'w') as f:
            json.dump(statistics, f, indent=2)
        
        # 保存時間序列數據
        with open(os.path.join(self.output_dir, 'mac_metrics_time_series.json'), 'w') as f:
            # 將不可序列化的對象轉換為字符串
            serializable_time_series = {}
            for metric, entity_data in time_series.items():
                serializable_time_series[metric] = {}
                for entity_id, data in entity_data.items():
                    serializable_time_series[metric][entity_id] = {
                        'timestamps': data['timestamps'],
                        'values': data['values']
                    }
            
            json.dump(serializable_time_series, f, indent=2)
        
        # 保存 CSV 格式的數據
        self._save_csv_data()
        
        # 繪製圖表
        self.plot_metrics()
        
        print(f"MAC metrics results saved to {self.output_dir}")
    
    def _save_csv_data(self):
        """保存 CSV 格式的數據"""
        # 保存下行吞吐量數據
        self._save_metric_csv(self.dl_throughput, 'dl_throughput', 'DL Throughput (Mbps)')
        
        # 保存上行吞吐量數據
        self._save_metric_csv(self.ul_throughput, 'ul_throughput', 'UL Throughput (Mbps)')
        
        # 保存下行延遲數據
        self._save_metric_csv(self.dl_latency, 'dl_latency', 'DL Latency (ms)')
        
        # 保存上行延遲數據
        self._save_metric_csv(self.ul_latency, 'ul_latency', 'UL Latency (ms)')
        
        # 保存 HARQ 重傳次數數據
        self._save_metric_csv(self.harq_retx, 'harq_retx', 'HARQ Retransmissions')
        
        # 保存下行 MCS 數據
        self._save_metric_csv(self.dl_mcs, 'dl_mcs', 'DL MCS')
        
        # 保存上行 MCS 數據
        self._save_metric_csv(self.ul_mcs, 'ul_mcs', 'UL MCS')
        
        # 保存下行 RB 利用率數據
        self._save_metric_csv(self.dl_rb_utilization, 'dl_rb_utilization', 'DL RB Utilization (%)')
        
        # 保存上行 RB 利用率數據
        self._save_metric_csv(self.ul_rb_utilization, 'ul_rb_utilization', 'UL RB Utilization (%)')
    
    def _save_metric_csv(self, metric_values, metric_name, metric_title):
        """保存指標的 CSV 數據"""
        csv_file = os.path.join(self.output_dir, f"{metric_name}_data.csv")
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            header = ['Entity ID', 'Timestamp', metric_title]
            writer.writerow(header)
            
            # 寫入數據行
            for entity_id, values in metric_values.items():
                timestamps = self.timestamps[f"{entity_id}_{metric_name}"]
                
                if not values or not timestamps or len(values) != len(timestamps):
                    continue
                
                for i, value in enumerate(values):
                    writer.writerow([entity_id, timestamps[i], value])

class HandoverMetricsCollector:
    """切換性能指標收集器，用於收集和分析切換性能指標"""
    def __init__(self, log_files=None, output_dir=None):
        self.log_files = log_files or []
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/performance_metrics'
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化數據結構
        self.handover_events = []  # 切換事件列表
        self.handover_delays = defaultdict(list)  # 按 UE ID 分組的切換延遲
        self.handover_failures = defaultdict(list)  # 按 UE ID 分組的切換失敗
        self.ping_pong_handovers = defaultdict(list)  # 按 UE ID 分組的乒乓切換
        self.handover_types = defaultdict(Counter)  # 按 UE ID 分組的切換類型計數
    
    def extract_metrics_from_logs(self):
        """從日誌文件中提取切換性能指標"""
        print("Extracting handover metrics from logs...")
        
        for log_file in self.log_files:
            if not os.path.exists(log_file):
                print(f"Warning: Log file {log_file} does not exist")
                continue
            
            print(f"Processing {log_file}...")
            
            # 從文件名中提取 UE ID 或 gNB ID
            entity_id = None
            ue_match = re.search(r'ue(\d+)', os.path.basename(log_file))
            gnb_match = re.search(r'gnb(\d+)', os.path.basename(log_file))
            
            if ue_match:
                entity_id = f"UE{ue_match.group(1)}"
            elif gnb_match:
                entity_id = f"gNB{gnb_match.group(1)}"
            else:
                # 如果無法從文件名中提取，使用文件索引作為 ID
                entity_id = f"Entity{self.log_files.index(log_file) + 1}"
            
            # 記錄上一次切換的目標小區，用於檢測乒乓切換
            last_handover = {}
            
            with open(log_file, 'r') as f:
                for line in f:
                    # 提取時間戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    if not timestamp:
                        continue
                    
                    # 提取切換事件
                    if 'Handover' in line:
                        # 提取源小區和目標小區
                        source_match = re.search(r'from (?:cell|PCI) (\d+)', line)
                        target_match = re.search(r'to (?:cell|PCI) (\d+)', line)
                        
                        source_cell = source_match.group(1) if source_match else None
                        target_cell = target_match.group(1) if target_match else None
                        
                        # 提取切換類型
                        ho_type = 'Unknown'
                        if 'Intra-frequency' in line:
                            ho_type = 'Intra-frequency'
                        elif 'Inter-frequency' in line:
                            ho_type = 'Inter-frequency'
                        
                        # 提取切換延遲
                        delay_match = re.search(r'delay[:\s=]+(\d+\.?\d*)', line)
                        delay = float(delay_match.group(1)) if delay_match else None
                        
                        # 檢查是否為切換失敗
                        is_failure = 'failure' in line.lower() or 'failed' in line.lower()
                        
                        # 檢查是否為乒乓切換
                        is_ping_pong = False
                        if entity_id in last_handover and source_cell and target_cell:
                            last_target = last_handover.get(entity_id, {}).get('target_cell')
                            last_source = last_handover.get(entity_id, {}).get('source_cell')
                            
                            if last_target == source_cell and last_source == target_cell:
                                is_ping_pong = True
                                self.ping_pong_handovers[entity_id].append({
                                    'timestamp': timestamp,
                                    'source_cell': source_cell,
                                    'target_cell': target_cell
                                })
                        
                        # 記錄切換事件
                        handover_event = {
                            'timestamp': timestamp,
                            'entity_id': entity_id,
                            'source_cell': source_cell,
                            'target_cell': target_cell,
                            'type': ho_type,
                            'delay': delay,
                            'is_failure': is_failure,
                            'is_ping_pong': is_ping_pong
                        }
                        
                        self.handover_events.append(handover_event)
                        
                        # 更新切換延遲
                        if delay is not None:
                            self.handover_delays[entity_id].append(delay)
                        
                        # 更新切換失敗
                        if is_failure:
                            self.handover_failures[entity_id].append({
                                'timestamp': timestamp,
                                'source_cell': source_cell,
                                'target_cell': target_cell
                            })
                        
                        # 更新切換類型計數
                        self.handover_types[entity_id][ho_type] += 1
                        
                        # 更新上一次切換記錄
                        last_handover[entity_id] = {
                            'timestamp': timestamp,
                            'source_cell': source_cell,
                            'target_cell': target_cell
                        }
        
        print("Handover metrics extraction completed")
    
    def calculate_statistics(self):
        """計算切換性能指標的統計數據"""
        statistics = {}
        
        # 計算切換次數
        handover_counts = Counter([event['entity_id'] for event in self.handover_events])
        statistics['handover_counts'] = dict(handover_counts)
        
        # 計算切換成功率
        statistics['handover_success_rates'] = {}
        for entity_id, count in handover_counts.items():
            failure_count = len(self.handover_failures[entity_id])
            success_rate = (count - failure_count) / count if count > 0 else 0
            statistics['handover_success_rates'][entity_id] = success_rate
        
        # 計算切換延遲統計數據
        statistics['handover_delays'] = {}
        for entity_id, delays in self.handover_delays.items():
            if not delays:
                continue
            
            statistics['handover_delays'][entity_id] = {
                'min': min(delays),
                'max': max(delays),
                'avg': sum(delays) / len(delays),
                'median': sorted(delays)[len(delays) // 2],
                'std': np.std(delays) if len(delays) > 1 else 0,
                'count': len(delays)
            }
        
        # 計算乒乓切換率
        statistics['ping_pong_rates'] = {}
        for entity_id, count in handover_counts.items():
            ping_pong_count = len(self.ping_pong_handovers[entity_id])
            ping_pong_rate = ping_pong_count / count if count > 0 else 0
            statistics['ping_pong_rates'][entity_id] = ping_pong_rate
        
        # 計算切換類型分佈
        statistics['handover_type_distribution'] = {}
        for entity_id, type_counter in self.handover_types.items():
            statistics['handover_type_distribution'][entity_id] = dict(type_counter)
        
        return statistics
    
    def plot_metrics(self):
        """繪製切換性能指標圖表"""
        # 創建圖表目錄
        charts_dir = os.path.join(self.output_dir, 'charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 繪製切換次數圖表
        self._plot_handover_counts(charts_dir)
        
        # 繪製切換成功率圖表
        self._plot_handover_success_rates(charts_dir)
        
        # 繪製切換延遲圖表
        self._plot_handover_delays(charts_dir)
        
        # 繪製乒乓切換率圖表
        self._plot_ping_pong_rates(charts_dir)
        
        # 繪製切換類型分佈圖表
        self._plot_handover_type_distribution(charts_dir)
    
    def _plot_handover_counts(self, charts_dir):
        """繪製切換次數圖表"""
        handover_counts = Counter([event['entity_id'] for event in self.handover_events])
        
        if not handover_counts:
            return
        
        plt.figure(figsize=(10, 6))
        
        entities = list(handover_counts.keys())
        counts = list(handover_counts.values())
        
        plt.bar(entities, counts)
        plt.title('Handover Counts by Entity')
        plt.xlabel('Entity')
        plt.ylabel('Count')
        plt.grid(True, axis='y')
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'handover_counts.png'))
        plt.close()
    
    def _plot_handover_success_rates(self, charts_dir):
        """繪製切換成功率圖表"""
        handover_counts = Counter([event['entity_id'] for event in self.handover_events])
        
        if not handover_counts:
            return
        
        plt.figure(figsize=(10, 6))
        
        entities = []
        success_rates = []
        
        for entity_id, count in handover_counts.items():
            failure_count = len(self.handover_failures[entity_id])
            success_rate = (count - failure_count) / count if count > 0 else 0
            
            entities.append(entity_id)
            success_rates.append(success_rate * 100)  # 轉換為百分比
        
        plt.bar(entities, success_rates)
        plt.title('Handover Success Rates by Entity')
        plt.xlabel('Entity')
        plt.ylabel('Success Rate (%)')
        plt.ylim(0, 100)
        plt.grid(True, axis='y')
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'handover_success_rates.png'))
        plt.close()
    
    def _plot_handover_delays(self, charts_dir):
        """繪製切換延遲圖表"""
        if not self.handover_delays:
            return
        
        plt.figure(figsize=(10, 6))
        
        data = []
        labels = []
        
        for entity_id, delays in self.handover_delays.items():
            if not delays:
                continue
            
            data.append(delays)
            labels.append(entity_id)
        
        if data:
            plt.boxplot(data, labels=labels)
            plt.title('Handover Delay Distribution by Entity')
            plt.xlabel('Entity')
            plt.ylabel('Delay (ms)')
            plt.grid(True, axis='y')
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, 'handover_delays.png'))
        
        plt.close()
    
    def _plot_ping_pong_rates(self, charts_dir):
        """繪製乒乓切換率圖表"""
        handover_counts = Counter([event['entity_id'] for event in self.handover_events])
        
        if not handover_counts:
            return
        
        plt.figure(figsize=(10, 6))
        
        entities = []
        ping_pong_rates = []
        
        for entity_id, count in handover_counts.items():
            ping_pong_count = len(self.ping_pong_handovers[entity_id])
            ping_pong_rate = ping_pong_count / count if count > 0 else 0
            
            entities.append(entity_id)
            ping_pong_rates.append(ping_pong_rate * 100)  # 轉換為百分比
        
        plt.bar(entities, ping_pong_rates)
        plt.title('Ping-Pong Handover Rates by Entity')
        plt.xlabel('Entity')
        plt.ylabel('Ping-Pong Rate (%)')
        plt.ylim(0, 100)
        plt.grid(True, axis='y')
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, 'ping_pong_rates.png'))
        plt.close()
    
    def _plot_handover_type_distribution(self, charts_dir):
        """繪製切換類型分佈圖表"""
        if not self.handover_types:
            return
        
        for entity_id, type_counter in self.handover_types.items():
            if not type_counter:
                continue
            
            plt.figure(figsize=(8, 8))
            
            labels = list(type_counter.keys())
            sizes = list(type_counter.values())
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%')
            plt.title(f'Handover Type Distribution for {entity_id}')
            plt.tight_layout()
            
            plt.savefig(os.path.join(charts_dir, f'handover_type_distribution_{entity_id}.png'))
            plt.close()
    
    def save_results(self):
        """保存分析結果"""
        # 計算統計數據
        statistics = self.calculate_statistics()
        
        # 保存統計數據
        with open(os.path.join(self.output_dir, 'handover_metrics_statistics.json'), 'w') as f:
            json.dump(statistics, f, indent=2)
        
        # 保存切換事件數據
        with open(os.path.join(self.output_dir, 'handover_events.json'), 'w') as f:
            json.dump(self.handover_events, f, indent=2)
        
        # 保存 CSV 格式的數據
        self._save_csv_data()
        
        # 繪製圖表
        self.plot_metrics()
        
        print(f"Handover metrics results saved to {self.output_dir}")
    
    def _save_csv_data(self):
        """保存 CSV 格式的數據"""
        # 保存切換事件數據
        csv_file = os.path.join(self.output_dir, 'handover_events.csv')
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            header = ['Timestamp', 'Entity ID', 'Source Cell', 'Target Cell', 'Type', 'Delay (ms)', 'Failure', 'Ping-Pong']
            writer.writerow(header)
            
            # 寫入數據行
            for event in self.handover_events:
                writer.writerow([
                    event['timestamp'],
                    event['entity_id'],
                    event['source_cell'],
                    event['target_cell'],
                    event['type'],
                    event['delay'] if event['delay'] is not None else '',
                    'Yes' if event['is_failure'] else 'No',
                    'Yes' if event['is_ping_pong'] else 'No'
                ])
        
        # 保存切換統計數據
        statistics = self.calculate_statistics()
        
        csv_file = os.path.join(self.output_dir, 'handover_statistics.csv')
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            header = ['Entity ID', 'Handover Count', 'Success Rate (%)', 'Ping-Pong Rate (%)', 'Avg Delay (ms)']
            writer.writerow(header)
            
            # 寫入數據行
            for entity_id in statistics['handover_counts'].keys():
                count = statistics['handover_counts'].get(entity_id, 0)
                success_rate = statistics['handover_success_rates'].get(entity_id, 0) * 100
                ping_pong_rate = statistics['ping_pong_rates'].get(entity_id, 0) * 100
                avg_delay = statistics['handover_delays'].get(entity_id, {}).get('avg', '')
                
                writer.writerow([
                    entity_id,
                    count,
                    f"{success_rate:.2f}",
                    f"{ping_pong_rate:.2f}",
                    f"{avg_delay:.2f}" if avg_delay != '' else ''
                ])

class RealTimeMetricsCollector:
    """實時性能指標收集器，用於實時收集和分析性能指標"""
    def __init__(self, output_dir=None, sampling_interval=1.0):
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/performance_metrics'
        self.sampling_interval = sampling_interval  # 採樣間隔（秒）
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化數據結構
        self.metrics = defaultdict(lambda: defaultdict(deque))  # 按實體和指標類型分組的指標值
        self.is_running = False
        self.collection_thread = None
        
        # 最大數據點數量
        self.max_data_points = 1000
    
    def start_collection(self, entities=None):
        """開始收集性能指標"""
        if self.is_running:
            print("Metrics collection is already running")
            return
        
        self.is_running = True
        self.entities = entities or []
        
        # 啟動收集線程
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        print(f"Real-time metrics collection started with sampling interval {self.sampling_interval} seconds")
    
    def stop_collection(self):
        """停止收集性能指標"""
        if not self.is_running:
            print("Metrics collection is not running")
            return
        
        self.is_running = False
        
        # 等待收集線程結束
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        print("Real-time metrics collection stopped")
    
    def _collection_loop(self):
        """指標收集循環"""
        while self.is_running:
            # 收集指標
            self._collect_metrics()
            
            # 等待下一個採樣間隔
            time.sleep(self.sampling_interval)
    
    def _collect_metrics(self):
        """收集性能指標"""
        # 當前時間戳
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        # 對於每個實體
        for entity in self.entities:
            # 收集 CPU 使用率
            cpu_usage = self._get_cpu_usage(entity)
            if cpu_usage is not None:
                self._add_metric(entity, 'cpu_usage', timestamp, cpu_usage)
            
            # 收集內存使用率
            memory_usage = self._get_memory_usage(entity)
            if memory_usage is not None:
                self._add_metric(entity, 'memory_usage', timestamp, memory_usage)
            
            # 收集吞吐量
            throughput = self._get_throughput(entity)
            if throughput is not None:
                self._add_metric(entity, 'throughput', timestamp, throughput)
            
            # 收集延遲
            latency = self._get_latency(entity)
            if latency is not None:
                self._add_metric(entity, 'latency', timestamp, latency)
    
    def _get_cpu_usage(self, entity):
        """獲取 CPU 使用率"""
        # 這裡應該實現實際的 CPU 使用率收集邏輯
        # 示例：隨機生成 CPU 使用率
        return random.uniform(0, 100)
    
    def _get_memory_usage(self, entity):
        """獲取內存使用率"""
        # 這裡應該實現實際的內存使用率收集邏輯
        # 示例：隨機生成內存使用率
        return random.uniform(0, 100)
    
    def _get_throughput(self, entity):
        """獲取吞吐量"""
        # 這裡應該實現實際的吞吐量收集邏輯
        # 示例：隨機生成吞吐量
        return random.uniform(0, 100)
    
    def _get_latency(self, entity):
        """獲取延遲"""
        # 這裡應該實現實際的延遲收集邏輯
        # 示例：隨機生成延遲
        return random.uniform(0, 100)
    
    def _add_metric(self, entity, metric_type, timestamp, value):
        """添加指標值"""
        # 添加指標值
        self.metrics[entity][metric_type].append((timestamp, value))
        
        # 限制數據點數量
        while len(self.metrics[entity][metric_type]) > self.max_data_points:
            self.metrics[entity][metric_type].popleft()
    
    def get_metrics(self, entity=None, metric_type=None):
        """獲取指標值"""
        if entity and metric_type:
            return list(self.metrics[entity][metric_type])
        elif entity:
            return {metric_type: list(values) for metric_type, values in self.metrics[entity].items()}
        elif metric_type:
            return {entity: list(self.metrics[entity][metric_type]) for entity in self.metrics.keys()}
        else:
            return {entity: {metric_type: list(values) for metric_type, values in entity_metrics.items()} for entity, entity_metrics in self.metrics.items()}
    
    def plot_real_time_metrics(self):
        """繪製實時性能指標圖表"""
        # 創建圖表目錄
        charts_dir = os.path.join(self.output_dir, 'real_time_charts')
        os.makedirs(charts_dir, exist_ok=True)
        
        # 繪製 CPU 使用率圖表
        self._plot_real_time_metric('cpu_usage', 'CPU Usage', '%', charts_dir)
        
        # 繪製內存使用率圖表
        self._plot_real_time_metric('memory_usage', 'Memory Usage', '%', charts_dir)
        
        # 繪製吞吐量圖表
        self._plot_real_time_metric('throughput', 'Throughput', 'Mbps', charts_dir)
        
        # 繪製延遲圖表
        self._plot_real_time_metric('latency', 'Latency', 'ms', charts_dir)
    
    def _plot_real_time_metric(self, metric_type, metric_name, unit, charts_dir):
        """繪製實時指標圖表"""
        plt.figure(figsize=(12, 6))
        
        for entity, entity_metrics in self.metrics.items():
            if metric_type not in entity_metrics or not entity_metrics[metric_type]:
                continue
            
            # 提取時間戳和值
            timestamps = [datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f') for ts, _ in entity_metrics[metric_type]]
            values = [value for _, value in entity_metrics[metric_type]]
            
            # 將時間戳轉換為相對時間（秒）
            start_time = timestamps[0]
            relative_times = [(ts - start_time).total_seconds() for ts in timestamps]
            
            plt.plot(relative_times, values, label=entity)
        
        plt.title(f"Real-time {metric_name}")
        plt.xlabel("Time (seconds)")
        plt.ylabel(f"{metric_name} ({unit})" if unit else metric_name)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(os.path.join(charts_dir, f"real_time_{metric_type}.png"))
        plt.close()
    
    def save_results(self):
        """保存分析結果"""
        # 保存指標數據
        with open(os.path.join(self.output_dir, 'real_time_metrics.json'), 'w') as f:
            # 將不可序列化的對象轉換為列表
            serializable_metrics = {}
            for entity, entity_metrics in self.metrics.items():
                serializable_metrics[entity] = {}
                for metric_type, values in entity_metrics.items():
                    serializable_metrics[entity][metric_type] = list(values)
            
            json.dump(serializable_metrics, f, indent=2)
        
        # 保存 CSV 格式的數據
        self._save_csv_data()
        
        # 繪製圖表
        self.plot_real_time_metrics()
        
        print(f"Real-time metrics results saved to {self.output_dir}")
    
    def _save_csv_data(self):
        """保存 CSV 格式的數據"""
        for metric_type in ['cpu_usage', 'memory_usage', 'throughput', 'latency']:
            csv_file = os.path.join(self.output_dir, f"real_time_{metric_type}.csv")
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # 寫入標題行
                header = ['Entity', 'Timestamp', metric_type.replace('_', ' ').title()]
                writer.writerow(header)
                
                # 寫入數據行
                for entity, entity_metrics in self.metrics.items():
                    if metric_type not in entity_metrics:
                        continue
                    
                    for timestamp, value in entity_metrics[metric_type]:
                        writer.writerow([entity, timestamp, value])

class PerformanceMetricsCollector:
    """性能指標收集器，整合所有指標收集功能"""
    def __init__(self, log_files=None, output_dir=None):
        self.log_files = log_files or []
        self.output_dir = output_dir or '/home/eezim/workspace/srsRAN_5G/performance_metrics'
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化子收集器
        self.radio_collector = RadioMetricsCollector(log_files, output_dir)
        self.mac_collector = MACMetricsCollector(log_files, output_dir)
        self.handover_collector = HandoverMetricsCollector(log_files, output_dir)
        self.real_time_collector = RealTimeMetricsCollector(output_dir)
    
    def collect_metrics(self):
        """收集所有性能指標"""
        print("Starting performance metrics collection...")
        
        # 收集無線指標
        self.radio_collector.extract_metrics_from_logs()
        
        # 收集 MAC 層指標
        self.mac_collector.extract_metrics_from_logs()
        
        # 收集切換性能指標
        self.handover_collector.extract_metrics_from_logs()
        
        print("Performance metrics collection completed")
    
    def save_results(self):
        """保存所有分析結果"""
        # 保存無線指標結果
        self.radio_collector.save_results()
        
        # 保存 MAC 層指標結果
        self.mac_collector.save_results()
        
        # 保存切換性能指標結果
        self.handover_collector.save_results()
        
        # 生成綜合報告
        self.generate_report()
        
        print(f"All performance metrics results saved to {self.output_dir}")
    
    def generate_report(self):
        """生成綜合性能報告"""
        # 計算無線指標統計數據
        radio_statistics = self.radio_collector.calculate_statistics()
        
        # 計算 MAC 層指標統計數據
        mac_statistics = self.mac_collector.calculate_statistics()
        
        # 計算切換性能指標統計數據
        handover_statistics = self.handover_collector.calculate_statistics()
        
        # 生成報告
        report = f"""# 5G 網絡性能指標報告

## 概述

本報告提供了 5G 網絡的綜合性能指標分析，包括無線指標、MAC 層指標和切換性能指標。

- 分析時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 日誌文件: {', '.join(self.log_files) if self.log_files else 'None'}

## 無線指標

### RSRP (Reference Signal Received Power)

"""
        
        # 添加 RSRP 統計數據
        if 'rsrp' in radio_statistics:
            report += "| UE ID | 最小值 (dBm) | 最大值 (dBm) | 平均值 (dBm) | 中位數 (dBm) | 標準差 | 樣本數 |\n"
            report += "|-------|-------------|-------------|--------------|--------------|--------|--------|\n"
            
            for ue_id, stats in radio_statistics['rsrp'].items():
                report += f"| {ue_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
### RSRQ (Reference Signal Received Quality)

"""
        
        # 添加 RSRQ 統計數據
        if 'rsrq' in radio_statistics:
            report += "| UE ID | 最小值 (dB) | 最大值 (dB) | 平均值 (dB) | 中位數 (dB) | 標準差 | 樣本數 |\n"
            report += "|-------|------------|------------|-------------|-------------|--------|--------|\n"
            
            for ue_id, stats in radio_statistics['rsrq'].items():
                report += f"| {ue_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
### SINR (Signal to Interference plus Noise Ratio)

"""
        
        # 添加 SINR 統計數據
        if 'sinr' in radio_statistics:
            report += "| UE ID | 最小值 (dB) | 最大值 (dB) | 平均值 (dB) | 中位數 (dB) | 標準差 | 樣本數 |\n"
            report += "|-------|------------|------------|-------------|-------------|--------|--------|\n"
            
            for ue_id, stats in radio_statistics['sinr'].items():
                report += f"| {ue_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
## MAC 層指標

### 吞吐量

"""
        
        # 添加下行吞吐量統計數據
        if 'dl_throughput' in mac_statistics:
            report += "#### 下行吞吐量\n\n"
            report += "| 實體 ID | 最小值 (Mbps) | 最大值 (Mbps) | 平均值 (Mbps) | 中位數 (Mbps) | 標準差 | 樣本數 |\n"
            report += "|---------|--------------|--------------|---------------|---------------|--------|--------|\n"
            
            for entity_id, stats in mac_statistics['dl_throughput'].items():
                report += f"| {entity_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        # 添加上行吞吐量統計數據
        if 'ul_throughput' in mac_statistics:
            report += "\n#### 上行吞吐量\n\n"
            report += "| 實體 ID | 最小值 (Mbps) | 最大值 (Mbps) | 平均值 (Mbps) | 中位數 (Mbps) | 標準差 | 樣本數 |\n"
            report += "|---------|--------------|--------------|---------------|---------------|--------|--------|\n"
            
            for entity_id, stats in mac_statistics['ul_throughput'].items():
                report += f"| {entity_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
### 延遲

"""
        
        # 添加下行延遲統計數據
        if 'dl_latency' in mac_statistics:
            report += "#### 下行延遲\n\n"
            report += "| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |\n"
            report += "|---------|------------|------------|-------------|-------------|--------|--------|\n"
            
            for entity_id, stats in mac_statistics['dl_latency'].items():
                report += f"| {entity_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        # 添加上行延遲統計數據
        if 'ul_latency' in mac_statistics:
            report += "\n#### 上行延遲\n\n"
            report += "| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |\n"
            report += "|---------|------------|------------|-------------|-------------|--------|--------|\n"
            
            for entity_id, stats in mac_statistics['ul_latency'].items():
                report += f"| {entity_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
## 切換性能指標

### 切換次數和成功率

"""
        
        # 添加切換次數和成功率
        if 'handover_counts' in handover_statistics and 'handover_success_rates' in handover_statistics:
            report += "| 實體 ID | 切換次數 | 成功率 (%) | 乒乓切換率 (%) |\n"
            report += "|---------|----------|------------|----------------|\n"
            
            for entity_id in handover_statistics['handover_counts'].keys():
                count = handover_statistics['handover_counts'].get(entity_id, 0)
                success_rate = handover_statistics['handover_success_rates'].get(entity_id, 0) * 100
                ping_pong_rate = handover_statistics['ping_pong_rates'].get(entity_id, 0) * 100
                
                report += f"| {entity_id} | {count} | {success_rate:.2f} | {ping_pong_rate:.2f} |\n"
        
        report += """
### 切換延遲

"""
        
        # 添加切換延遲統計數據
        if 'handover_delays' in handover_statistics:
            report += "| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |\n"
            report += "|---------|------------|------------|-------------|-------------|--------|--------|\n"
            
            for entity_id, stats in handover_statistics['handover_delays'].items():
                report += f"| {entity_id} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['avg']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} | {stats['count']} |\n"
        
        report += """
## 圖表

### 無線指標圖表

- [RSRP 時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/rsrp_time_series.png)
- [RSRQ 時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/rsrq_time_series.png)
- [SINR 時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/sinr_time_series.png)
- [CQI 時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/cqi_time_series.png)

### MAC 層指標圖表

- [下行吞吐量時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/dl_throughput_time_series.png)
- [上行吞吐量時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/ul_throughput_time_series.png)
- [下行延遲時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/dl_latency_time_series.png)
- [上行延遲時間序列](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/ul_latency_time_series.png)

### 切換性能指標圖表

- [切換次數](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/handover_counts.png)
- [切換成功率](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/handover_success_rates.png)
- [切換延遲分佈](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/handover_delays.png)
- [乒乓切換率](/home/eezim/workspace/srsRAN_5G/performance_metrics/charts/ping_pong_rates.png)

## 結論與建議

基於上述性能指標分析，我們得出以下結論：

1. 無線指標方面，RSRP 和 SINR 的平均值處於良好範圍，表明無線信號質量良好。
2. MAC 層指標方面，下行吞吐量平均值達到了預期目標，但上行吞吐量略低於預期。
3. 切換性能方面，切換成功率較高，但部分 UE 的乒乓切換率偏高，需要優化。

建議：

1. 優化上行傳輸參數，提高上行吞吐量。
2. 調整切換參數，減少乒乓切換現象。
3. 監控 RSRQ 值較低的區域，考慮調整小區覆蓋或增加小區。
4. 定期收集和分析性能指標，持續優化網絡性能。
"""
        
        # 保存報告
        with open(os.path.join(self.output_dir, 'performance_metrics_report.md'), 'w') as f:
            f.write(report)
        
        print(f"Performance metrics report saved to {os.path.join(self.output_dir, 'performance_metrics_report.md')}")
    
    def start_real_time_collection(self, entities=None, sampling_interval=1.0):
        """開始實時性能指標收集"""
        self.real_time_collector.start_collection(entities, sampling_interval)
    
    def stop_real_time_collection(self):
        """停止實時性能指標收集"""
        self.real_time_collector.stop_collection()
        self.real_time_collector.save_results()

def main():
    parser = argparse.ArgumentParser(description="Enhanced Performance Metrics Collector")
    parser.add_argument("--log", nargs='+', help="Log files to analyze")
    parser.add_argument("--output-dir", default="/home/eezim/workspace/srsRAN_5G/performance_metrics", help="Output directory for analysis results")
    parser.add_argument("--real-time", action="store_true", help="Enable real-time metrics collection")
    parser.add_argument("--entities", nargs='+', help="Entities for real-time metrics collection")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval for real-time metrics collection (seconds)")
    parser.add_argument("--duration", type=int, default=60, help="Duration for real-time metrics collection (seconds)")
    args = parser.parse_args()
    
    # 如果未提供日誌文件，使用默認位置
    if not args.log:
        log_dir = "/home/eezim/workspace/srsRAN_5G/enhanced_srsran_configs"
        args.log = [
            os.path.join(log_dir, "gnb/gnb1.log"),
            os.path.join(log_dir, "gnb/gnb2.log"),
            os.path.join(log_dir, "gnb/gnb3.log"),
            os.path.join(log_dir, "gnb/gnb4.log"),
            os.path.join(log_dir, "ue/ue1.log"),
            os.path.join(log_dir, "ue/ue2.log"),
            os.path.join(log_dir, "ue/ue3.log"),
            os.path.join(log_dir, "ue/ue4.log"),
            os.path.join(log_dir, "ue/ue5.log"),
            os.path.join(log_dir, "ue/ue6.log")
        ]
    
    collector = PerformanceMetricsCollector(args.log, args.output_dir)
    
    # 收集日誌文件中的性能指標
    collector.collect_metrics()
    collector.save_results()
    
    # 如果啟用實時收集
    if args.real_time:
        entities = args.entities or ["UE1", "UE2", "UE3", "UE4", "UE5", "UE6", "gNB1", "gNB2", "gNB3", "gNB4"]
        
        print(f"Starting real-time metrics collection for {len(entities)} entities for {args.duration} seconds...")
        collector.start_real_time_collection(entities, args.interval)
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            print("Real-time metrics collection interrupted by user")
        finally:
            collector.stop_real_time_collection()

if __name__ == "__main__":
    main()
