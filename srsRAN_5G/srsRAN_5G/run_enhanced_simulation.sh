#!/bin/bash
#!/home/eezim/workspace/srsRAN_5G/.venv/bin/python
# 主脚本：運行增強型 5G 網絡模擬並收集/分析結果

# --- 配置 ---
CONFIG_DIR="/home/eezim/workspace/srsRAN_5G/enhanced_srsran_configs"
OUTPUT_DIR="/home/eezim/workspace/srsRAN_5G/simulation_results"
METRICS_DIR="/home/eezim/workspace/srsRAN_5G/performance_metrics"
MOBILITY_DIR="/home/eezim/workspace/srsRAN_5G/mobility_data"
RRC_ANALYSIS_DIR="/home/eezim/workspace/srsRAN_5G/rrc_analysis"
SIMULATION_DURATION=120 # 秒
TIME_STEP=1.0          # 秒
CHANNEL_MODEL="simplified" # 或 "external"

# --- 清理舊數據 (可選) ---
echo "Cleaning up previous results..."
rm -rf "$OUTPUT_DIR" "$METRICS_DIR" "$MOBILITY_DIR" "$RRC_ANALYSIS_DIR"
mkdir -p "$OUTPUT_DIR" "$METRICS_DIR" "$MOBILITY_DIR" "$RRC_ANALYSIS_DIR"

# --- 步驟 1: 啟動核心網 (EPC) ---
echo "Starting EPC..."
sudo srsepc "$CONFIG_DIR/epc/epc.conf" \
    --mme.log.filename "$OUTPUT_DIR/mme.log" \
    --hss.log.filename "$OUTPUT_DIR/hss.log" \
    --spgw.log.filename "$OUTPUT_DIR/spgw.log" \
    > "$OUTPUT_DIR/epc_stdout.log" 2>&1 &
EPC_PID=$!
sleep 5  # 等待 EPC 啟動

# --- 步驟 2: 啟動 gNB ---
echo "Starting gNBs..."
for i in {1..4}; do
    echo "  gNB$i..."
    sudo srsenb "$CONFIG_DIR/gnb/gnb$i.conf" \
        --log.filename "$OUTPUT_DIR/gnb$i.log" \
        --rf.device_name=zmq \
        --rf.device_args="tx_port=tcp://127.0.0.1:210$((i-1))0,rx_port=tcp://127.0.0.1:210$((i-1))1,id=gnb$i,base_srate=23.04e6" \
        > "$OUTPUT_DIR/gnb${i}_stdout.log" 2>&1 &
    GNB_PIDS[$i]=$!
done
sleep 10  # 等待 gNB 啟動並連接到 EPC

# --- 步驟 3: 運行 UE 移動和連接模擬 ---
echo "Starting UE mobility simulation..."
sudo python3 /home/eezim/workspace/srsRAN_5G/enhanced_ue_mobility_controller_v2.py \
    --config-dir "$CONFIG_DIR" \
    --duration "$SIMULATION_DURATION" \
    --time-step "$TIME_STEP" \
    --channel-model "$CHANNEL_MODEL"

# --- 步驟 4: 停止 gNB 和 EPC ---
echo "Stopping gNBs and EPC..."
for pid in "${GNB_PIDS[@]}"; do
    sudo kill "$pid" 2>/dev/null || true
done
sudo kill "$EPC_PID" 2>/dev/null || true
sleep 5
sudo pkill srsenb || true
sudo pkill srsepc || true

# --- 步驟 5: 收集和分析性能指標 ---
echo "Collecting and analyzing performance metrics..."
LOG_FILES=""
for i in {1..4}; do
    LOG_FILES+=" $OUTPUT_DIR/gnb$i.log"
done
for i in {1..6}; do
    LOG_FILES+=" /home/eezim/workspace/srsRAN_5G/ue$i.log"
done

python3 /home/eezim/workspace/srsRAN_5G/enhanced_performance_metrics_collector.py \
    --log $LOG_FILES \
    --output-dir "$METRICS_DIR"

# --- 步驟 6: 分析 RRC 追蹤 (假設 PCAP 文件已生成) ---
echo "Analyzing RRC traces..."
PCAP_FILES=$(find "$OUTPUT_DIR" -name "*.pcap")
if [ -n "$PCAP_FILES" ]; then
    python3 /home/eezim/workspace/srsRAN_5G/enhanced_rrc_trace_analyzer.py \
        --pcap $PCAP_FILES \
        --log $LOG_FILES \
        --output-dir "$RRC_ANALYSIS_DIR"
else
    echo "Warning: No PCAP files found for RRC analysis."
fi

# --- 步驟 7: 啟動可視化儀表板 (可選) ---
echo "Starting visualization dashboard (optional)..."
echo "Run manually:"
echo "  cd /home/eezim/workspace/srsRAN_5G"
echo "  python3 enhanced_visualization_dashboard.py"
# 或者使用 nohup/background 模式：
# nohup python3 /home/eezim/workspace/srsRAN_5G/enhanced_visualization_dashboard.py > "$OUTPUT_DIR/dashboard.log" 2>&1 &
# echo "Dashboard PID: $! (訪問 http://<your-ip>:8050 )"

echo "Enhanced simulation and analysis complete."
echo "Results saved in:"
echo "- Simulation Logs: $OUTPUT_DIR"
echo "- Mobility Data: $MOBILITY_DIR"
echo "- Performance Metrics: $METRICS_DIR"
echo "- RRC Analysis: $RRC_ANALYSIS_DIR"
