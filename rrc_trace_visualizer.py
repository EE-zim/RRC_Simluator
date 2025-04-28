#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RRC 追蹤結果可視化工具
此腳本用於生成 RRC 追蹤結果的互動式可視化
"""

import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

class RRCTraceVisualizer:
    def __init__(self, analysis_dir="/home/ubuntu/rrc_analysis", output_dir="/home/ubuntu/rrc_visualization"):
        self.analysis_dir = analysis_dir
        self.output_dir = output_dir
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_analysis_data(self):
        """載入分析結果數據"""
        analysis_file = os.path.join(self.analysis_dir, "rrc_analysis.json")
        
        if not os.path.exists(analysis_file):
            print(f"錯誤: 分析結果文件 {analysis_file} 不存在")
            return None
        
        try:
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
            return analysis_data
        except Exception as e:
            print(f"載入分析結果時發生錯誤: {e}")
            return None
    
    def create_interactive_mobility_chart(self, analysis_data):
        """創建互動式移動事件圖表"""
        if not analysis_data:
            return
        
        print("創建互動式移動事件圖表...")
        
        # 提取移動事件類型分佈數據
        event_types = list(analysis_data["mobility_events_by_type"].keys())
        event_counts = list(analysis_data["mobility_events_by_type"].values())
        
        # 創建互動式條形圖
        fig = px.bar(
            x=event_types, 
            y=event_counts,
            labels={'x': '事件類型', 'y': '數量'},
            title='移動事件類型分佈',
            color=event_types,
            text=event_counts
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=100)
        )
        
        # 保存為 HTML 文件
        output_file = os.path.join(self.output_dir, "interactive_mobility_events.html")
        fig.write_html(output_file)
        print(f"互動式移動事件圖表已保存到 {output_file}")
    
    def create_interactive_rrc_chart(self, analysis_data):
        """創建互動式 RRC 消息圖表"""
        if not analysis_data:
            return
        
        print("創建互動式 RRC 消息圖表...")
        
        # 提取 RRC 消息類型分佈數據
        message_types = list(analysis_data["rrc_messages_by_type"].keys())
        message_counts = list(analysis_data["rrc_messages_by_type"].values())
        
        # 創建互動式條形圖
        fig = px.bar(
            x=message_types, 
            y=message_counts,
            labels={'x': '消息類型', 'y': '數量'},
            title='RRC 消息類型分佈',
            color=message_types,
            text=message_counts
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=100)
        )
        
        # 保存為 HTML 文件
        output_file = os.path.join(self.output_dir, "interactive_rrc_messages.html")
        fig.write_html(output_file)
        print(f"互動式 RRC 消息圖表已保存到 {output_file}")
    
    def create_interactive_handover_chart(self, analysis_data):
        """創建互動式 Handover 分析圖表"""
        if not analysis_data or not analysis_data["handover_analysis"]:
            return
        
        print("創建互動式 Handover 分析圖表...")
        
        # 提取 Handover 數據
        handover_data = pd.DataFrame(analysis_data["handover_analysis"])
        
        # 創建 Handover 路徑標籤
        handover_data['path'] = handover_data.apply(lambda row: f"gNB{row['from_gnb']} → gNB{row['to_gnb']}", axis=1)
        
        # 計算每個路徑的 Handover 次數
        path_counts = handover_data['path'].value_counts().reset_index()
        path_counts.columns = ['path', 'count']
        
        # 創建互動式條形圖
        fig = px.bar(
            path_counts,
            x='path',
            y='count',
            labels={'path': 'Handover 路徑', 'count': '次數'},
            title='Handover 分析',
            color='path',
            text='count'
        )
        
        fig.update_layout(
            autosize=True,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # 保存為 HTML 文件
        output_file = os.path.join(self.output_dir, "interactive_handover_analysis.html")
        fig.write_html(output_file)
        print(f"互動式 Handover 分析圖表已保存到 {output_file}")
    
    def create_interactive_ue_timeline(self, analysis_data):
        """創建互動式 UE 連接時間線"""
        if not analysis_data or not analysis_data["ue_connection_analysis"]:
            return
        
        print("創建互動式 UE 連接時間線...")
        
        # 創建 Gantt 圖數據
        gantt_data = []
        
        for ue_data in analysis_data["ue_connection_analysis"]:
            ue_id = ue_data["ue_id"]
            events = ue_data["events"]
            
            for i in range(0, len(events), 2):
                if i + 1 < len(events):
                    if events[i]["event_type"] == "UE_START" and events[i+1]["event_type"] == "UE_STOP":
                        start_time = datetime.strptime(events[i]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
                        end_time = datetime.strptime(events[i+1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
                        
                        gantt_data.append({
                            "Task": f"UE{ue_id}",
                            "Start": start_time,
                            "Finish": end_time,
                            "Status": "Connected"
                        })
        
        if gantt_data:
            df = pd.DataFrame(gantt_data)
            
            # 創建互動式 Gantt 圖
            fig = px.timeline(
                df, 
                x_start="Start", 
                x_end="Finish", 
                y="Task",
                color="Status",
                title="UE 連接時間線"
            )
            
            fig.update_layout(
                autosize=True,
                margin=dict(l=50, r=50, t=80, b=50),
                xaxis_title="時間",
                yaxis_title="UE"
            )
            
            # 保存為 HTML 文件
            output_file = os.path.join(self.output_dir, "interactive_ue_timeline.html")
            fig.write_html(output_file)
            print(f"互動式 UE 連接時間線已保存到 {output_file}")
    
    def create_interactive_dashboard(self, analysis_data):
        """創建互動式儀表板"""
        if not analysis_data:
            return
        
        print("創建互動式儀表板...")
        
        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "移動事件類型分佈", 
                "RRC 消息類型分佈",
                "Handover 分析",
                "UE 連接狀態"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "pie"}]
            ]
        )
        
        # 1. 移動事件類型分佈
        event_types = list(analysis_data["mobility_events_by_type"].keys())
        event_counts = list(analysis_data["mobility_events_by_type"].values())
        
        fig.add_trace(
            go.Bar(
                x=event_types,
                y=event_counts,
                name="移動事件",
                marker_color='rgb(55, 83, 109)',
                text=event_counts
            ),
            row=1, col=1
        )
        
        # 2. RRC 消息類型分佈
        message_types = list(analysis_data["rrc_messages_by_type"].keys())
        message_counts = list(analysis_data["rrc_messages_by_type"].values())
        
        fig.add_trace(
            go.Bar(
                x=message_types,
                y=message_counts,
                name="RRC 消息",
                marker_color='rgb(26, 118, 255)',
                text=message_counts
            ),
            row=1, col=2
        )
        
        # 3. Handover 分析
        if analysis_data["handover_analysis"]:
            handover_data = pd.DataFrame(analysis_data["handover_analysis"])
            handover_data['path'] = handover_data.apply(lambda row: f"gNB{row['from_gnb']} → gNB{row['to_gnb']}", axis=1)
            path_counts = handover_data['path'].value_counts().reset_index()
            path_counts.columns = ['path', 'count']
            
            fig.add_trace(
                go.Bar(
                    x=path_counts['path'],
                    y=path_counts['count'],
                    name="Handover",
                    marker_color='rgb(204, 204, 0)',
                    text=path_counts['count']
                ),
                row=2, col=1
            )
        
        # 4. UE 連接狀態
        ue_status = {"Connected": 0, "Disconnected": 0}
        for ue_data in analysis_data["ue_connection_analysis"]:
            events = ue_data["events"]
            for event in events:
                if event["event_type"] == "UE_START":
                    ue_status["Connected"] += 1
                elif event["event_type"] == "UE_STOP":
                    ue_status["Disconnected"] += 1
        
        fig.add_trace(
            go.Pie(
                labels=list(ue_status.keys()),
                values=list(ue_status.values()),
                name="UE 狀態",
                marker_colors=['rgb(0, 204, 150)', 'rgb(255, 102, 102)']
            ),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            title_text="5G 網路 RRC 協議追蹤分析儀表板",
            autosize=True,
            height=800,
            showlegend=False,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        # 更新 x 軸標籤角度
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        fig.update_xaxes(tickangle=-45, row=1, col=2)
        fig.update_xaxes(tickangle=-45, row=2, col=1)
        
        # 保存為 HTML 文件
        output_file = os.path.join(self.output_dir, "interactive_dashboard.html")
        fig.write_html(output_file)
        print(f"互動式儀表板已保存到 {output_file}")
    
    def create_index_page(self):
        """創建索引頁面"""
        print("創建索引頁面...")
        
        html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>5G 網路 RRC 協議追蹤分析</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #2980b9;
            margin-top: 30px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .card h3 {
            margin-top: 0;
            color: #3498db;
        }
        .card p {
            margin-bottom: 15px;
        }
        .card a {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .card a:hover {
            background-color: #2980b9;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            font-size: 0.9em;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>5G 網路 RRC 協議追蹤分析</h1>
        
        <div class="card">
            <h3>儀表板</h3>
            <p>綜合性儀表板，顯示所有關鍵指標和分析結果。</p>
            <a href="interactive_dashboard.html" target="_blank">查看儀表板</a>
        </div>
        
        <h2>詳細分析</h2>
        
        <div class="card">
            <h3>移動事件分析</h3>
            <p>分析 UE 移動事件的類型分佈，包括進入/離開 gNB 和 handover 事件。</p>
            <a href="interactive_mobility_events.html" target="_blank">查看移動事件分析</a>
        </div>
        
        <div class="card">
            <h3>RRC 消息分析</h3>
            <p>分析 RRC 協議消息的類型分佈，包括 Setup、Reconfiguration 等消息。</p>
            <a href="interactive_rrc_messages.html" target="_blank">查看 RRC 消息分析</a>
        </div>
        
        <div class="card">
            <h3>Handover 分析</h3>
            <p>分析 UE 在不同 gNB 之間的 handover 情況。</p>
            <a href="interactive_handover_analysis.html" target="_blank">查看 Handover 分析</a>
        </div>
        
        <div class="card">
            <h3>UE 連接時間線</h3>
            <p>顯示 UE 連接狀態隨時間的變化。</p>
            <a href="interactive_ue_timeline.html" target="_blank">查看 UE 連接時間線</a>
        </div>
        
        <h2>報告</h2>
        
        <div class="card">
            <h3>分析報告</h3>
            <p>詳細的 RRC 協議追蹤分析報告，包括結論和建議。</p>
            <a href="../rrc_analysis/rrc_analysis_report.md" target="_blank">查看分析報告</a>
        </div>
        
        <div class="footer">
            <p>© 2025 5G 網路 RRC 協議追蹤分析</p>
        </div>
    </div>
</body>
</html>
"""
        
        # 保存為 HTML 文件
        output_file = os.path.join(self.output_dir, "index.html")
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"索引頁面已保存到 {output_file}")
    
    def run_visualization(self):
        """運行完整可視化流程"""
        print("開始 RRC 追蹤結果可視化...")
        
        # 安裝必要的依賴項
        self.install_dependencies()
        
        # 載入分析數據
        analysis_data = self.load_analysis_data()
        if not analysis_data:
            print("無法載入分析數據，可視化終止")
            return False
        
        # 創建互動式圖表
        self.create_interactive_mobility_chart(analysis_data)
        self.create_interactive_rrc_chart(analysis_data)
        self.create_interactive_handover_chart(analysis_data)
        self.create_interactive_ue_timeline(analysis_data)
        self.create_interactive_dashboard(analysis_data)
        
        # 創建索引頁面
        self.create_index_page()
        
        print("RRC 追蹤結果可視化完成")
        return True
    
    def install_dependencies(self):
        """安裝必要的依賴項"""
        print("安裝必要的依賴項...")
        
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "plotly", "pandas", "numpy", "matplotlib"], check=True)
            print("依賴項安裝完成")
            return True
        except Exception as e:
            print(f"安裝依賴項時發生錯誤: {e}")
            print("繼續使用已安裝的依賴項...")
            return False

def main():
    parser = argparse.ArgumentParser(description="RRC 追蹤結果可視化工具")
    parser.add_argument("--analysis-dir", default="/home/ubuntu/rrc_analysis", help="分析結果目錄")
    parser.add_argument("--output-dir", default="/home/ubuntu/rrc_visualization", help="可視化輸出目錄")
    args = parser.parse_args()
    
    visualizer = RRCTraceVisualizer(analysis_dir=args.analysis_dir, output_dir=args.output_dir)
    visualizer.run_visualization()

if __name__ == "__main__":
    main()
