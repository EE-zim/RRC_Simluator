# 5G 網絡性能指標報告

## 概述

本報告提供了 5G 網絡的綜合性能指標分析，包括無線指標、MAC 層指標和切換性能指標。

- 分析時間: 2025-04-29 11:15:28
- 日誌文件: /home/eezim/workspace/srsRAN_5G/simulation_results/gnb1.log, /home/eezim/workspace/srsRAN_5G/simulation_results/gnb2.log, /home/eezim/workspace/srsRAN_5G/simulation_results/gnb3.log, /home/eezim/workspace/srsRAN_5G/simulation_results/gnb4.log, /home/eezim/workspace/srsRAN_5G/ue1.log, /home/eezim/workspace/srsRAN_5G/ue2.log, /home/eezim/workspace/srsRAN_5G/ue3.log, /home/eezim/workspace/srsRAN_5G/ue4.log, /home/eezim/workspace/srsRAN_5G/ue5.log, /home/eezim/workspace/srsRAN_5G/ue6.log

## 無線指標

### RSRP (Reference Signal Received Power)

| UE ID | 最小值 (dBm) | 最大值 (dBm) | 平均值 (dBm) | 中位數 (dBm) | 標準差 | 樣本數 |
|-------|-------------|-------------|--------------|--------------|--------|--------|

### RSRQ (Reference Signal Received Quality)

| UE ID | 最小值 (dB) | 最大值 (dB) | 平均值 (dB) | 中位數 (dB) | 標準差 | 樣本數 |
|-------|------------|------------|-------------|-------------|--------|--------|

### SINR (Signal to Interference plus Noise Ratio)

| UE ID | 最小值 (dB) | 最大值 (dB) | 平均值 (dB) | 中位數 (dB) | 標準差 | 樣本數 |
|-------|------------|------------|-------------|-------------|--------|--------|

## MAC 層指標

### 吞吐量

#### 下行吞吐量

| 實體 ID | 最小值 (Mbps) | 最大值 (Mbps) | 平均值 (Mbps) | 中位數 (Mbps) | 標準差 | 樣本數 |
|---------|--------------|--------------|---------------|---------------|--------|--------|

#### 上行吞吐量

| 實體 ID | 最小值 (Mbps) | 最大值 (Mbps) | 平均值 (Mbps) | 中位數 (Mbps) | 標準差 | 樣本數 |
|---------|--------------|--------------|---------------|---------------|--------|--------|

### 延遲

#### 下行延遲

| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |
|---------|------------|------------|-------------|-------------|--------|--------|

#### 上行延遲

| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |
|---------|------------|------------|-------------|-------------|--------|--------|

## 切換性能指標

### 切換次數和成功率

| 實體 ID | 切換次數 | 成功率 (%) | 乒乓切換率 (%) |
|---------|----------|------------|----------------|

### 切換延遲

| 實體 ID | 最小值 (ms) | 最大值 (ms) | 平均值 (ms) | 中位數 (ms) | 標準差 | 樣本數 |
|---------|------------|------------|-------------|-------------|--------|--------|

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
