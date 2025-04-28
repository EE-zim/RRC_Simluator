#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RRC 追蹤結果分析工具
此腳本用於分析 RRC 協議追蹤結果並生成報告
"""

import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np

class RRCTraceAnalyzer:
    def __init__(self, traces_dir="/home/ubuntu/rrc_traces", output_dir="/home/ubuntu/rrc_analysis"):
        self.traces_dir = traces_dir
        self.output_dir = output_dir
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_merged_data(self):
        """載入合併的移動事件和 RRC 追蹤數據"""
        merged_file = os.path.join(self.traces_dir, "merged_rrc_mobility.json")
        
        if not os.path.exists(merged_file):
            print(f"錯誤: 合併數據文件 {merged_file} 不存在")
            return None
        
        try:
            with open(merged_file, 'r') as f:
                merged_data = json.load(f)
            return merged_data
        except Exception as e:
            print(f"載入合併數據時發生錯誤: {e}")
            return None
    
    def analyze_rrc_messages(self, merged_data):
        """分析 RRC 消息"""
        if not merged_data:
            return
        
        print("分析 RRC 消息...")
        
        # 提取移動事件
        mobility_events = merged_data.get("mobility_events", [])
        
        # 提取 RRC 追蹤
        rrc_traces = merged_data.get("rrc_traces", {})
        
        # 分析結果
        analysis = {
            "total_mobility_events": len(mobility_events),
            "mobility_events_by_type": {},
            "total_rrc_messages": 0,
            "rrc_messages_by_type": {},
            "handover_analysis": [],
            "ue_connection_analysis": []
        }
        
        # 分析移動事件
        for event in mobility_events:
            event_type = event.get("event_type", "unknown")
            if event_type not in analysis["mobility_events_by_type"]:
                analysis["mobility_events_by_type"][event_type] = 0
            analysis["mobility_events_by_type"][event_type] += 1
            
            # 特別分析 handover 事件
            if event_type == "HANDOVER":
                details = event.get("details", {})
                analysis["handover_analysis"].append({
                    "timestamp": event.get("timestamp"),
                    "ue_id": details.get("ue_id"),
                    "from_gnb": details.get("from_gnb"),
                    "to_gnb": details.get("to_gnb")
                })
        
        # 分析 RRC 消息
        for trace_name, trace_data in rrc_traces.items():
            if isinstance(trace_data, list):
                analysis["total_rrc_messages"] += len(trace_data)
                
                for message in trace_data:
                    message_type = message.get("message_type", "unknown")
                    if message_type not in analysis["rrc_messages_by_type"]:
                        analysis["rrc_messages_by_type"][message_type] = 0
                    analysis["rrc_messages_by_type"][message_type] += 1
        
        # 分析 UE 連接情況
        ue_events = {}
        for event in mobility_events:
            event_type = event.get("event_type", "")
            details = event.get("details", {})
            timestamp = event.get("timestamp", "")
            
            if event_type in ["UE_START", "UE_STOP"]:
                ue_id = details.get("ue_id")
                if ue_id:
                    if ue_id not in ue_events:
                        ue_events[ue_id] = []
                    ue_events[ue_id].append({
                        "timestamp": timestamp,
                        "event_type": event_type,
                        "process_id": details.get("process_id", "")
                    })
        
        for ue_id, events in ue_events.items():
            analysis["ue_connection_analysis"].append({
                "ue_id": ue_id,
                "events": sorted(events, key=lambda x: x["timestamp"])
            })
        
        # 保存分析結果
        analysis_file = os.path.join(self.output_dir, "rrc_analysis.json")
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"分析結果已保存到 {analysis_file}")
        return analysis
    
    def generate_visualizations(self, analysis):
        """生成可視化圖表"""
        if not analysis:
            return
        
        print("生成可視化圖表...")
        
        # 1. 移動事件類型分佈圖
        plt.figure(figsize=(10, 6))
        event_types = list(analysis["mobility_events_by_type"].keys())
        event_counts = list(analysis["mobility_events_by_type"].values())
        plt.bar(event_types, event_counts)
        plt.title('移動事件類型分佈')
        plt.xlabel('事件類型')
        plt.ylabel('數量')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "mobility_events_distribution.png"))
        plt.close()
        
        # 2. RRC 消息類型分佈圖
        plt.figure(figsize=(12, 6))
        message_types = list(analysis["rrc_messages_by_type"].keys())
        message_counts = list(analysis["rrc_messages_by_type"].values())
        plt.bar(message_types, message_counts)
        plt.title('RRC 消息類型分佈')
        plt.xlabel('消息類型')
        plt.ylabel('數量')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "rrc_messages_distribution.png"))
        plt.close()
        
        # 3. Handover 分析圖
        if analysis["handover_analysis"]:
            handover_data = pd.DataFrame(analysis["handover_analysis"])
            plt.figure(figsize=(10, 6))
            handover_counts = handover_data.groupby(['from_gnb', 'to_gnb']).size().reset_index(name='count')
            
            # 創建標籤
            labels = [f"gNB{row['from_gnb']} → gNB{row['to_gnb']}" for _, row in handover_counts.iterrows()]
            plt.bar(labels, handover_counts['count'])
            plt.title('Handover 分析')
            plt.xlabel('Handover 路徑')
            plt.ylabel('數量')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "handover_analysis.png"))
            plt.close()
        
        # 4. UE 連接時間線
        if analysis["ue_connection_analysis"]:
            plt.figure(figsize=(12, 8))
            
            for i, ue_data in enumerate(analysis["ue_connection_analysis"]):
                ue_id = ue_data["ue_id"]
                events = ue_data["events"]
                
                # 創建時間線
                y_pos = i
                for j, event in enumerate(events):
                    if event["event_type"] == "UE_START":
                        start_time = datetime.strptime(event["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
                        
                        # 檢查是否有對應的停止事件
                        if j + 1 < len(events) and events[j + 1]["event_type"] == "UE_STOP":
                            end_time = datetime.strptime(events[j + 1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
                        else:
                            # 如果沒有停止事件，使用最後一個事件的時間
                            end_time = datetime.strptime(events[-1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
                        
                        # 繪製連接時間段
                        plt.plot([start_time, end_time], [y_pos, y_pos], 'g-', linewidth=4)
                        plt.text(start_time, y_pos + 0.1, "連接", fontsize=8)
            
            plt.yticks(range(len(analysis["ue_connection_analysis"])), [f"UE{ue_data['ue_id']}" for ue_data in analysis["ue_connection_analysis"]])
            plt.title('UE 連接時間線')
            plt.xlabel('時間')
            plt.ylabel('UE')
            plt.grid(True, axis='x')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "ue_connection_timeline.png"))
            plt.close()
        
        print(f"可視化圖表已保存到 {self.output_dir}")
    
    def generate_report(self, analysis):
        """生成分析報告"""
        if not analysis:
            return
        
        print("生成分析報告...")
        
        report = f"""# RRC 協議追蹤分析報告

## 概述

本報告分析了 5G 網路模擬環境中的 RRC 協議追蹤結果。

## 移動事件分析

總移動事件數: {analysis["total_mobility_events"]}

移動事件類型分佈:
"""
        
        for event_type, count in analysis["mobility_events_by_type"].items():
            report += f"- {event_type}: {count}\n"
        
        report += f"""
## RRC 消息分析

總 RRC 消息數: {analysis["total_rrc_messages"]}

RRC 消息類型分佈:
"""
        
        for message_type, count in analysis["rrc_messages_by_type"].items():
            report += f"- {message_type}: {count}\n"
        
        report += """
## Handover 分析
"""
        
        if analysis["handover_analysis"]:
            for handover in analysis["handover_analysis"]:
                report += f"- 時間: {handover['timestamp']}, UE{handover['ue_id']} 從 gNB{handover['from_gnb']} 切換到 gNB{handover['to_gnb']}\n"
        else:
            report += "無 Handover 事件\n"
        
        report += """
## UE 連接分析
"""
        
        for ue_data in analysis["ue_connection_analysis"]:
            report += f"### UE{ue_data['ue_id']}\n"
            for event in ue_data["events"]:
                report += f"- {event['timestamp']}: {event['event_type']}\n"
        
        report += """
## 圖表

以下圖表提供了移動事件和 RRC 消息的可視化分析:

1. [移動事件類型分佈](mobility_events_distribution.png)
2. [RRC 消息類型分佈](rrc_messages_distribution.png)
3. [Handover 分析](handover_analysis.png)
4. [UE 連接時間線](ue_connection_timeline.png)

## 結論

根據分析結果，我們可以得出以下結論:

1. RRC 協議在 UE 進入/離開 gNB 和 handover 過程中起著關鍵作用
2. Handover 過程中的 RRC 消息交換確保了 UE 的連續性服務
3. 不同的移動場景會觸發不同類型的 RRC 消息

## 建議

1. 優化 RRC 協議以減少 handover 延遲
2. 增強 RRC 連接重建機制以提高網路可靠性
3. 進一步研究 RRC 協議在高速移動場景中的表現
"""
        
        # 保存報告
        report_file = os.path.join(self.output_dir, "rrc_analysis_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"分析報告已保存到 {report_file}")
    
    def run_analysis(self):
        """運行完整分析流程"""
        print("開始 RRC 追蹤結果分析...")
        
        # 載入數據
        merged_data = self.load_merged_data()
        if not merged_data:
            print("無法載入數據，分析終止")
            return False
        
        # 分析 RRC 消息
        analysis = self.analyze_rrc_messages(merged_data)
        if not analysis:
            print("分析 RRC 消息失敗，分析終止")
            return False
        
        # 生成可視化圖表
        self.generate_visualizations(analysis)
        
        # 生成報告
        self.generate_report(analysis)
        
        print("RRC 追蹤結果分析完成")
        return True

def main():
    parser = argparse.ArgumentParser(description="RRC 追蹤結果分析工具")
    parser.add_argument("--traces-dir", default="/home/ubuntu/rrc_traces", help="RRC 追蹤數據目錄")
    parser.add_argument("--output-dir", default="/home/ubuntu/rrc_analysis", help="分析結果輸出目錄")
    args = parser.parse_args()
    
    analyzer = RRCTraceAnalyzer(traces_dir=args.traces_dir, output_dir=args.output_dir)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
