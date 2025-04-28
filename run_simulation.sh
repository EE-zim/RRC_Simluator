#!/bin/bash
# 執行模擬網路和捕獲RRC追蹤的主腳本

echo "開始執行5G網路模擬和RRC追蹤捕獲..."

# 創建必要的目錄
mkdir -p /home/ubuntu/rrc_traces
mkdir -p /home/ubuntu/rrc_analysis

# 步驟1: 執行UE移動場景模擬
echo "步驟1: 執行UE移動場景模擬..."
python3 /home/ubuntu/ue_mobility_controller.py

# 步驟2: 捕獲RRC協議追蹤
echo "步驟2: 捕獲RRC協議追蹤..."
python3 /home/ubuntu/rrc_trace_capture.py

# 步驟3: 分析RRC追蹤結果
echo "步驟3: 分析RRC追蹤結果..."
python3 /home/ubuntu/rrc_trace_analyzer.py

echo "模擬和分析完成！"
echo "RRC追蹤結果保存在 /home/ubuntu/rrc_traces 目錄"
echo "分析報告和圖表保存在 /home/ubuntu/rrc_analysis 目錄"
