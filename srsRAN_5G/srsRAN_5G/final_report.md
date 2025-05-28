# srsRAN 5G 模擬項目增強報告

## 1. 項目概述

基於您提供的報告和要求，我們對原有的 srsRAN 5G 網路模擬項目進行了全面的增強。本次改進旨在創建一個更真實、功能更豐富、可擴展性更強的模擬環境，用於研究 UE 移動性、切換行為和 RRC 協議。

主要改進包括：

*   **擴展的網路拓撲**：增加了 gNB 和 UE 的數量，模擬更複雜的異構網路場景。
*   **增強的 UE 移動模型**：引入了多種更真實的移動模式。
*   **深入的 RRC 分析**：實現了對 RRC 消息內容和序列的詳細分析。
*   **全面的性能指標收集**：收集了無線、MAC 層和切換等多維度性能指標。
*   **互動式可視化儀表板**：開發了基於 Web 的儀表板，用於直觀展示和分析數據。
*   **可擴展的信道模型接口**：為未來集成更高級的信道仿真工具（如 Sionna）預留了接口。

## 2. 主要改進詳情

### 2.1 網路配置增強 (步驟 002)

*   **網路規模擴大**：模擬網路從原來的 1 CN, 2 gNB, 3 UE 擴展到 **1 CN, 4 gNB (2 宏基站, 2 微基站), 6 UE**。
*   **異構網路場景**：引入了宏基站和微基站，具有不同的發射功率和頻率，模擬更真實的網路部署。
*   **配置文件更新**：所有相關的 EPC, gNB, UE 配置文件已更新並存儲在 `/home/ubuntu/enhanced_srsran_configs/` 目錄下，支持新的網路拓撲和 UE 類型。
*   **用戶數據庫擴展**：`/home/ubuntu/enhanced_srsran_configs/epc/user_db.csv` 已更新，包含所有 6 個 UE 的信息。

### 2.2 UE 移動模型改進 (步驟 003)

*   **實現多種移動模式**：在 `enhanced_ue_mobility_controller_v2.py` 中實現了更豐富的移動模型，包括：
    *   `static`：靜止用戶
    *   `random_walk`：隨機行走（帶邊界反彈）
    *   `directed`：定向移動（帶邊界環繞）
    *   `trajectory`：沿預定軌跡移動
    *   `group`：跟隨指定中心 UE 移動
*   **參數化配置**：每個 UE 可以獨立配置其移動類型和速度。
*   **軌跡記錄**：控制器會記錄所有 UE 的移動軌跡，保存在 `/home/ubuntu/mobility_data/ue_trajectories.json`。

### 2.3 RRC 追蹤分析擴展 (步驟 004)

*   **深度協議分析**：`enhanced_rrc_trace_analyzer.py` 腳本實現了更深入的 RRC 協議分析功能：
    *   **ASN.1 解析 (集成)**：能夠解析 RRC 消息的 ASN.1 結構 (需要安裝相關庫並配置解析器)。
    *   **關鍵參數提取**：提取 RRC 消息中的關鍵參數，如 `RRCSetup`, `RRCReconfiguration`, `HandoverCommand` 等消息的詳細內容。
    *   **序列分析**：分析 RRC 過程（如連接建立、切換）的消息序列，識別異常或錯誤序列。
    *   **性能關聯**：將 RRC 事件與其他性能指標（如無線質量、切換延遲）進行關聯分析。
*   **輸出格式**：分析結果以 JSON 格式輸出，並生成詳細的 Markdown 報告，存儲在 `/home/ubuntu/rrc_analysis/`。

### 2.4 性能指標收集 (步驟 005)

*   **多維度指標收集**：`enhanced_performance_metrics_collector.py` 腳本實現了全面的性能指標收集：
    *   **無線指標**：RSRP, RSRQ, SINR, CQI, BLER 等。
    *   **MAC 層指標**：上下行吞吐量、延遲、HARQ 重傳次數、MCS、RB 利用率等。
    *   **切換性能指標**：切換次數、成功率、失敗原因、切換延遲、乒乓切換率、切換類型分佈等。
*   **數據來源**：從 srsRAN 組件生成的日誌文件中提取指標數據。
*   **結果輸出**：
    *   統計數據 (JSON): `/home/ubuntu/performance_metrics/`
    *   時間序列數據 (JSON): `/home/ubuntu/performance_metrics/`
    *   原始數據 (CSV): `/home/ubuntu/performance_metrics/`
    *   圖表 (PNG): `/home/ubuntu/performance_metrics/charts/`
    *   綜合報告 (Markdown): `/home/ubuntu/performance_metrics/performance_metrics_report.md`
*   **實時收集 (可選)**：腳本還包含一個 `RealTimeMetricsCollector` 類，用於實時監控系統指標 (CPU, 內存等)，但需要進一步實現與 srsRAN 組件的接口。

### 2.5 可視化增強 (步驟 006)

*   **互動式儀表板**：開發了 `enhanced_visualization_dashboard.py`，使用 Dash 和 Plotly 創建了一個基於 Web 的互動式儀表板。
*   **功能**：
    *   多選項卡界面：無線指標、MAC 指標、切換性能。
    *   實體選擇器：允許用戶選擇特定的 UE 或 gNB 進行查看。
    *   時間範圍選擇器 (待完善)：允許用戶選擇特定的時間段。
    *   多種圖表類型：時間序列圖、箱線圖、柱狀圖、餅圖、時間線圖等。
    *   互動性：懸停提示、縮放、平移等。
*   **訪問方式**：儀表板可在模擬結束後手動運行，並通過瀏覽器訪問。

### 2.6 為未來開發準備接口 (步驟 007)

*   **可擴展信道模型接口**：在 `enhanced_ue_mobility_controller_v2.py` 中定義了 `ChannelModel` 抽象基類，將信道計算邏輯與移動控制器解耦。
*   **實現**：
    *   `SimplifiedChannelModel`：提供了基於路徑損耗和簡單衰落的基礎實現。
    *   `ExternalChannelModelPlaceholder`：**關鍵接口**，作為接入外部真實信道仿真工具（如 **Sionna**）的佔位符。用戶需要根據所選仿真工具的 API 來實現此類的具體邏輯。
*   **靈活性**：`NetworkSimulator` 接受一個 `ChannelModel` 對象作為參數，允許在啟動模擬時輕鬆切換不同的信道模型。
*   **未來集成**：用戶可以創建自己的 `ChannelModel` 子類，實現與特定信道模擬器的交互，然後將其實例傳遞給 `NetworkSimulator`。

## 3. 如何使用

### 3.1 環境準備

*   確保已按照之前的步驟編譯安裝了 srsRAN 4G (包含 srsUE, srsENB, srsEPC)，並啟用了 ZeroMQ。
*   確保已安裝 Python 依賴：`dash`, `pandas`, `plotly`, `numpy`, `matplotlib`。
    ```bash
    pip3 install dash pandas plotly numpy matplotlib
    ```
*   確保腳本具有執行權限：
    ```bash
    chmod +x /home/ubuntu/enhanced_ue_mobility_controller_v2.py
    chmod +x /home/ubuntu/enhanced_performance_metrics_collector.py
    chmod +x /home/ubuntu/enhanced_rrc_trace_analyzer.py
    chmod +x /home/ubuntu/enhanced_visualization_dashboard.py
    chmod +x /home/ubuntu/run_enhanced_simulation.sh
    ```
*   **重要**：由於需要管理網絡命名空間和啟動 srsRAN 組件，主腳本 `run_enhanced_simulation.sh` 和移動控制器 `enhanced_ue_mobility_controller_v2.py` 中的部分命令需要 `sudo` 權限。請確保以適當權限運行，或配置 `sudo` 以允許無密碼執行特定命令。

### 3.2 運行模擬與分析

*   執行主腳本：
    ```bash
    sudo /home/ubuntu/run_enhanced_simulation.sh
    ```
*   腳本將自動執行以下步驟：
    1.  清理舊數據。
    2.  啟動 EPC。
    3.  啟動 4 個 gNB。
    4.  運行 UE 移動模擬（默認 120 秒，使用簡化信道模型）。
    5.  停止 gNB 和 EPC。
    6.  收集並分析性能指標。
    7.  分析 RRC 追蹤（如果找到 PCAP 文件）。

### 3.3 查看結果

*   **模擬日誌**：`/home/ubuntu/simulation_results/` (包含 EPC, gNB 的日誌)
*   **UE 日誌**：`/home/ubuntu/ueX.log` (X 為 UE 編號)
*   **移動數據**：`/home/ubuntu/mobility_data/` (包含 UE 軌跡、事件日誌、RSRP 日誌)
*   **性能指標分析**：`/home/ubuntu/performance_metrics/` (包含 JSON, CSV, PNG 圖表和 Markdown 報告)
*   **RRC 分析**：`/home/ubuntu/rrc_analysis/` (包含 JSON 結果和 Markdown 報告)

### 3.4 運行互動式儀表板

*   模擬和分析完成後，手動啟動儀表板：
    ```bash
    python3 /home/ubuntu/enhanced_visualization_dashboard.py
    ```
*   儀表板將在 `http://<沙盒IP>:8050` 上運行。您需要使用 `deploy_expose_port` 工具將 8050 端口暴露出來，然後通過提供的公共 URL 訪問。

## 4. 文件列表

*   `/home/ubuntu/enhanced_srsran_configs/`: 增強後的網路配置文件目錄。
*   `/home/ubuntu/enhanced_ue_mobility_controller_v2.py`: 增強的 UE 移動控制器 (含信道模型接口)。
*   `/home/ubuntu/enhanced_performance_metrics_collector.py`: 性能指標收集與分析工具。
*   `/home/ubuntu/enhanced_rrc_trace_analyzer.py`: RRC 追蹤分析工具。
*   `/home/ubuntu/enhanced_visualization_dashboard.py`: 互動式可視化儀表板。
*   `/home/ubuntu/run_enhanced_simulation.sh`: 運行完整模擬和分析的主腳本。
*   `/home/ubuntu/final_report.md`: 本報告。

## 5. 未來工作 (接口利用)

要利用為第八階段準備的接口（集成真實信道仿真）：

1.  選擇一個信道仿真工具（如 Sionna）。
2.  創建一個新的 Python 類，繼承自 `enhanced_ue_mobility_controller_v2.py` 中的 `ChannelModel`。
3.  在該子類中實現 `calculate_rsrp`, `calculate_sinr`, `is_in_coverage` 方法，調用所選仿真工具的 API 來獲取信道信息。
4.  修改 `run_enhanced_simulation.sh` 或直接調用 `NetworkSimulator` 時，將 `--channel-model` 參數設置為 `external`，並確保 `NetworkSimulator` 實例化時傳遞的是您實現的外部信道模型類的實例。

## 6. 結論

本次項目增強成功地實現了更複雜、更真實、功能更全面的 5G 網路模擬環境。通過引入多樣化的移動模型、深入的協議分析、全面的性能監控和互動式可視化，為研究 5G 網路中的移動性管理和 RRC 協議行為提供了強大的工具。同時，預留的信道模型接口為未來集成更高級的仿真工具奠定了基礎。
