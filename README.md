# 5G Network Simulation and RRC Protocol Tracing Based on srsRAN

This document details how to use srsRAN to set up a simulated 5G network environment, including a core network, two gNBs, and three UEs, and capture RRC protocol traces.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/EE-zim/nrRRC_Simulator)

## 1. Project Overview

This project accomplishes the following:

1. Establishes a simulated 5G network using srsRAN 4G
2. Configures one core network (EPC), two base stations (gNBs), and three user equipment (UEs)
3. Simulates UEs entering/leaving gNB coverage and handover scenarios
4. Captures RRC protocol traces from the base stations
5. Analyzes and visualizes the RRC trace results

## 2. Environment Setup

### 2.1 Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libfftw3-dev libmbedtls-dev libboost-program-options-dev libconfig++-dev libsctp-dev libzmq3-dev
```

### 2.2 Get srsRAN Code

```bash
git clone https://github.com/srsran/srsRAN_4G.git
```

### 2.3 Build srsRAN

```bash
cd srsRAN_4G
mkdir build
cd build
cmake .. -DENABLE_ZEROMQ=ON
make -j$(nproc)
```

## 3. Network Configuration

### 3.1 Core Network (EPC) Configuration

The EPC configuration file is located at `/home/ubuntu/srsran_configs/epc/epc.conf`, with main settings including:

- MME (Mobility Management Entity) configuration
- HSS (Home Subscriber Server) configuration
- SPGW (Serving and PDN Gateway) configuration
- User database configuration

The user database file `/home/ubuntu/srsran_configs/epc/user_db.csv` includes the identities of the three UEs:

```
001010123456781,milenage,00112233445566778899aabbccddeeff,353490069873311,1
001010123456782,milenage,00112233445566778899aabbccddeeff,353490069873312,1
001010123456783,milenage,00112233445566778899aabbccddeeff,353490069873313,1
```

### 3.2 Base Station (gNB) Configuration

We configured two gNBs, each using different frequencies and IDs:

#### gNB1 Configuration (`/home/ubuntu/srsran_configs/enb/enb1.conf`):

- enb_id = 0x19B
- dl_earfcn = 3350
- ZeroMQ ports: tcp://*:2000 (send), tcp://localhost:2001 (receive)
- PCAP capture and logging enabled

#### gNB2 Configuration (`/home/ubuntu/srsran_configs/enb/enb2.conf`):

- enb_id = 0x19C
- dl_earfcn = 3400
- ZeroMQ ports: tcp://*:2100 (send), tcp://localhost:2101 (receive)
- PCAP capture and logging enabled

### 3.3 User Equipment (UE) Configuration

We configured three UEs, each with different IMSI, IMEI, and channel models:

#### UE1 Configuration (`/home/ubuntu/srsran_configs/ue/ue1.conf`):

- IMSI: 001010123456781
- IMEI: 353490069873311
- Connects to gNB1 (dl_earfcn = 3350)
- Uses EPA5 fading model (low-speed movement)
- PCAP capture enabled at MAC and NAS layers

#### UE2 Configuration (`/home/ubuntu/srsran_configs/ue/ue2.conf`):

- IMSI: 001010123456782
- IMEI: 353490069873312
- Connects to gNB2 (dl_earfcn = 3400)
- Uses EVA70 fading model (medium-speed movement)
- PCAP capture enabled at MAC and NAS layers

#### UE3 Configuration (`/home/ubuntu/srsran_configs/ue/ue3.conf`):

- IMSI: 001010123456783
- IMEI: 353490069873313
- Initially connects to gNB1 (dl_earfcn = 3350)
- Uses ETU300 fading model (high-speed movement)
- Radio link failure simulation enabled
- PCAP capture enabled at MAC and NAS layers

## 4. UE Mobility Scenario Implementation

We implemented three types of UE mobility scenarios:

1. UE entering/leaving gNB coverage: simulates UE power-on/off or moving out of coverage
2. Handover between two gNBs: simulates UE moving from one cell to another
3. Multiple UEs connecting and switching simultaneously: simulates a complex network environment

These scenarios are managed by the `ue_mobility_controller.py` script, which controls UE startup, shutdown, and handovers.

### 4.1 UE Mobility Controller

The `ue_mobility_controller.py` script provides the following features:

- Start/stop EPC, gNBs, and UEs
- Trigger UE handovers between gNBs
- Log mobility events to a JSON file
- Clean up resources

### 4.2 Random Behavior Generation TO DO

UE behaviors and channel variations are generated randomly, including:

- Channel fading models: EPA5, EVA70, ETU300 
- Delay simulation: varying delay cycles and max/min delays
- Radio link failure simulation: random connect/disconnect timings

Interfaces are reserved for future integration with more sophisticated system simulations.

## 5. RRC Protocol Trace Capture

### 5.1 Trace Capture Tool

The `rrc_trace_capture.py` script implements:

- Extracting RRC messages from PCAP files
- Extracting RRC-related information from logs
- Merging all data into a JSON output

### 5.2 Trace Analysis Tool

The `rrc_trace_analyzer.py` script implements:

- Analyzing the correlation between mobility events and RRC messages
- Generating mobility event distribution charts
- Generating RRC message type distribution charts
- Analyzing handover processes
- Creating UE connection timelines
- Producing detailed analysis reports

### 5.3 Trace Visualization Tool TO DO

The `rrc_trace_visualizer.py` script implements:

- Creating interactive mobility event charts
- Creating interactive RRC message charts
- Creating interactive handover analysis charts
- Creating UE connection timelines
- Building a comprehensive dashboard
- Generating an index page

## 6. Running the Simulation

### 6.1 Run Full Simulation

Use the `run_simulation.sh` script to run the full simulation and analysis process:

```bash
./run_simulation.sh
```

The script will sequentially:

1. Run UE mobility scenario simulations
2. Capture RRC protocol traces
3. Analyze RRC trace results

### 6.2 Viewing Results

Simulation results are saved in:

- RRC trace results: `/home/ubuntu/rrc_traces`
- Analysis reports and charts: `/home/ubuntu/rrc_analysis`
- Interactive visualizations: `/home/ubuntu/rrc_visualization`

You can open `/home/ubuntu/rrc_visualization/index.html` in a browser to view the interactive dashboard and visualizations.

## 7. Key Findings

From the RRC protocol trace analysis, we identified the following:

1. RRC protocol plays a critical role during UE entry/exit and handover
2. RRC message exchanges during handover ensure continuous service for UEs
3. Different mobility scenarios trigger different types of RRC messages
4. Channel conditions (fading models, delays) significantly impact RRC message exchanges
5. Radio link failures lead to RRC reconnections, increasing network load

## 8. Recommendations

Based on our analysis, we recommend:

1. Optimizing the RRC protocol to reduce handover delays
2. Enhancing RRC reconnection mechanisms to improve network reliability
3. Further studying RRC performance under high-mobility scenarios
4. Adjusting RRC parameters in real deployments based on mobility scenarios

## 9. Future Work

This project provides a basic simulation framework. Future extensions may include:

1. Implementing more complex UE mobility models
2. Integrating real geographic and building distribution data
3. Simulating more gNBs and UEs
4. Analyzing the impact of RRC protocol on network performance
5. Researching new RRC features in 5G NR

## 10. References

1. srsRAN Documentation: https://docs.srsran.com/
2. 3GPP TS 36.331: RRC Protocol Specification
3. 3GPP TS 36.133: E-UTRA Requirements and Test Specifications
4. 3GPP TS 38.331: NR RRC Protocol Specification
