# 基於 srsRAN 的 5G 網路模擬與 RRC 協議追蹤

本文檔詳細說明了如何使用 srsRAN 建立模擬 5G 網路環境，包含一個核心網、兩個 gNB 和三個 UE，並捕獲 RRC 協議追蹤。

## 1. 項目概述

本項目實現了以下功能：

1. 使用 srsRAN 4G 建立模擬 5G 網路環境
2. 配置一個核心網 (EPC)、兩個基站 (gNB) 和三個用戶設備 (UE)
3. 模擬 UE 進入/離開 gNB 和 handover 場景
4. 捕獲基站的 RRC 協議追蹤
5. 分析並可視化 RRC 追蹤結果

## 2. 環境設置

### 2.1 安裝依賴項

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev libzmq3-dev
```

### 2.2 獲取 srsRAN 代碼

```bash
git clone https://github.com/srsran/srsRAN_4G.git
```

### 2.3 編譯 srsRAN

```bash
cd srsRAN_4G
mkdir build
cd build
cmake .. -DENABLE_ZEROMQ=ON
make -j$(nproc)
```

## 3. 網路配置

### 3.1 核心網 (EPC) 配置

EPC 配置文件位於 `/home/ubuntu/srsran_configs/epc/epc.conf`，主要設置包括：

- MME (Mobility Management Entity) 配置
- HSS (Home Subscriber Server) 配置
- SPGW (Serving and PDN Gateway) 配置
- 用戶數據庫配置

用戶數據庫文件 `/home/ubuntu/srsran_configs/epc/user_db.csv` 包含三個 UE 的身份信息：

```
001010123456781,milenage,00112233445566778899aabbccddeeff,353490069873311,1
001010123456782,milenage,00112233445566778899aabbccddeeff,353490069873312,1
001010123456783,milenage,00112233445566778899aabbccddeeff,353490069873313,1
```

### 3.2 基站 (gNB) 配置

我們配置了兩個 gNB，分別使用不同的頻率和 ID：

#### gNB1 配置 (`/home/ubuntu/srsran_configs/enb/enb1.conf`)：

- enb_id = 0x19B
- dl_earfcn = 3350
- ZeroMQ 端口：tcp://*:2000 (發送)，tcp://localhost:2001 (接收)
- 啟用 PCAP 捕獲和日誌記錄

#### gNB2 配置 (`/home/ubuntu/srsran_configs/enb/enb2.conf`)：

- enb_id = 0x19C
- dl_earfcn = 3400
- ZeroMQ 端口：tcp://*:2100 (發送)，tcp://localhost:2101 (接收)
- 啟用 PCAP 捕獲和日誌記錄

### 3.3 用戶設備 (UE) 配置

我們配置了三個 UE，每個 UE 使用不同的 IMSI、IMEI 和信道模型：

#### UE1 配置 (`/home/ubuntu/srsran_configs/ue/ue1.conf`)：

- IMSI: 001010123456781
- IMEI: 353490069873311
- 連接到 gNB1 (dl_earfcn = 3350)
- 使用 EPA5 衰落模型（低速移動）
- 啟用 MAC 和 NAS 層 PCAP 捕獲

#### UE2 配置 (`/home/ubuntu/srsran_configs/ue/ue2.conf`)：

- IMSI: 001010123456782
- IMEI: 353490069873312
- 連接到 gNB2 (dl_earfcn = 3400)
- 使用 EVA70 衰落模型（中速移動）
- 啟用 MAC 和 NAS 層 PCAP 捕獲

#### UE3 配置 (`/home/ubuntu/srsran_configs/ue/ue3.conf`)：

- IMSI: 001010123456783
- IMEI: 353490069873313
- 初始連接到 gNB1 (dl_earfcn = 3350)
- 使用 ETU300 衰落模型（高速移動）
- 啟用無線電鏈路故障模擬
- 啟用 MAC 和 NAS 層 PCAP 捕獲

## 4. UE 移動場景實現

我們實現了三種 UE 移動場景：

1. UE 進入/離開 gNB：模擬 UE 開機/關機或移出覆蓋範圍
2. UE 在兩個 gNB 之間 handover：模擬 UE 從一個小區移動到另一個小區
3. 多個 UE 同時連接和切換：模擬複雜的網路環境

這些場景通過 `ue_mobility_controller.py` 腳本實現，該腳本控制 UE 的啟動、停止和 handover。

### 4.1 UE 移動控制器

`ue_mobility_controller.py` 腳本實現了以下功能：

- 啟動/停止 EPC、gNB 和 UE
- 觸發 UE 從一個 gNB 切換到另一個 gNB
- 記錄移動事件到 JSON 文件
- 清理資源

### 4.2 隨機行為生成

UE 的行為和信道變化使用隨機生成器實現，包括：

- 信道衰落模型：EPA5、EVA70、ETU300
- 延遲模擬：不同的延遲週期和最大/最小延遲
- 無線電鏈路故障模擬：隨機的連接/斷開時間

這些模型保留了接口，以便未來接入更好的系統性仿真。

## 5. RRC 協議追蹤捕獲

### 5.1 追蹤捕獲工具

`rrc_trace_capture.py` 腳本實現了以下功能：

- 從 PCAP 文件中提取 RRC 消息
- 從日誌文件中提取 RRC 相關信息
- 將所有數據合併為 JSON 格式輸出

### 5.2 追蹤分析工具

`rrc_trace_analyzer.py` 腳本實現了以下功能：

- 分析移動事件和 RRC 消息的關聯性
- 生成移動事件類型分佈圖
- 生成 RRC 消息類型分佈圖
- 分析 handover 過程
- 生成 UE 連接時間線
- 生成詳細的分析報告

### 5.3 追蹤可視化工具

`rrc_trace_visualizer.py` 腳本實現了以下功能：

- 創建互動式移動事件圖表
- 創建互動式 RRC 消息圖表
- 創建互動式 Handover 分析圖表
- 創建互動式 UE 連接時間線
- 創建綜合性儀表板
- 生成索引頁面

## 6. 運行模擬

### 6.1 運行完整模擬

使用 `run_simulation.sh` 腳本運行完整的模擬和分析流程：

```bash
./run_simulation.sh
```

這個腳本會依次執行以下步驟：

1. 運行 UE 移動場景模擬
2. 捕獲 RRC 協議追蹤
3. 分析 RRC 追蹤結果

### 6.2 查看結果

模擬結果保存在以下目錄：

- RRC 追蹤結果：`/home/ubuntu/rrc_traces`
- 分析報告和圖表：`/home/ubuntu/rrc_analysis`
- 互動式可視化：`/home/ubuntu/rrc_visualization`

可以通過瀏覽器打開 `/home/ubuntu/rrc_visualization/index.html` 查看互動式儀表板和可視化結果。

## 7. 主要發現

通過分析 RRC 協議追蹤結果，我們得出以下主要發現：

1. RRC 協議在 UE 進入/離開 gNB 和 handover 過程中起著關鍵作用
2. Handover 過程中的 RRC 消息交換確保了 UE 的連續性服務
3. 不同的移動場景會觸發不同類型的 RRC 消息
4. 信道條件（如衰落模型和延遲）對 RRC 消息的交換有顯著影響
5. 無線電鏈路故障會導致 RRC 連接重建，增加網路負擔

## 8. 建議

基於我們的分析結果，我們提出以下建議：

1. 優化 RRC 協議以減少 handover 延遲
2. 增強 RRC 連接重建機制以提高網路可靠性
3. 進一步研究 RRC 協議在高速移動場景中的表現
4. 考慮在實際部署中根據不同的移動場景調整 RRC 參數

## 9. 未來工作

本項目為基礎模擬，未來可以在以下方面進行擴展：

1. 實現更複雜的 UE 移動模型
2. 集成真實的地理信息和建築物分佈
3. 模擬更多的 gNB 和 UE
4. 分析 RRC 協議對網路性能的影響
5. 研究 5G NR 中的新 RRC 功能

## 10. 參考資料

1. srsRAN 文檔：https://docs.srsran.com/
2. 3GPP TS 36.331：RRC 協議規範
3. 3GPP TS 36.133：E-UTRA 要求測試規範
4. 3GPP TS 38.331：NR RRC 協議規範
