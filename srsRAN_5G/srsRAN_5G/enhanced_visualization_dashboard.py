#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive dashboard built with Dash and Plotly to visualize 5G network performance metrics.
"""
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
import json
import datetime
from data_utils import load_json_data, load_csv_data

# --- 數據準備 ---

METRICS_DIR = "/home/eezim/workspace/srsRAN_5G/performance_metrics"

# 加載無線指標數據
radio_stats = load_json_data(os.path.join(METRICS_DIR, "radio_metrics_statistics.json"))
radio_ts = load_json_data(os.path.join(METRICS_DIR, "radio_metrics_time_series.json"))
rsrp_df = load_csv_data(os.path.join(METRICS_DIR, "rsrp_data.csv"))
rsrq_df = load_csv_data(os.path.join(METRICS_DIR, "rsrq_data.csv"))
sinr_df = load_csv_data(os.path.join(METRICS_DIR, "sinr_data.csv"))
cqi_df = load_csv_data(os.path.join(METRICS_DIR, "cqi_data.csv"))
bler_df = load_csv_data(os.path.join(METRICS_DIR, "bler_data.csv"))

# 加載 MAC 指標數據
mac_stats = load_json_data(os.path.join(METRICS_DIR, "mac_metrics_statistics.json"))
mac_ts = load_json_data(os.path.join(METRICS_DIR, "mac_metrics_time_series.json"))
dl_tp_df = load_csv_data(os.path.join(METRICS_DIR, "dl_throughput_data.csv"))
ul_tp_df = load_csv_data(os.path.join(METRICS_DIR, "ul_throughput_data.csv"))
dl_lat_df = load_csv_data(os.path.join(METRICS_DIR, "dl_latency_data.csv"))
ul_lat_df = load_csv_data(os.path.join(METRICS_DIR, "ul_latency_data.csv"))

# 加載切換指標數據
handover_stats = load_json_data(os.path.join(METRICS_DIR, "handover_metrics_statistics.json"))
handover_events_df = load_csv_data(os.path.join(METRICS_DIR, "handover_events.csv"))

# 獲取可用的 UE 和 gNB 列表
all_ues = set()
all_gnbs = set()

if radio_ts:
    for metric_data in radio_ts.values():
        all_ues.update(metric_data.keys())

if mac_ts:
    for metric_data in mac_ts.values():
        for entity_id in metric_data.keys():
            if entity_id.startswith("UE"):
                all_ues.add(entity_id)
            elif entity_id.startswith("gNB"):
                all_gnbs.add(entity_id)

if handover_stats and 'handover_counts' in handover_stats:
    for entity_id in handover_stats['handover_counts'].keys():
        if entity_id.startswith("UE"):
            all_ues.add(entity_id)
        elif entity_id.startswith("gNB"):
            all_gnbs.add(entity_id)

# 排序並轉換為列表
all_ues = sorted(list(all_ues))
all_gnbs = sorted(list(all_gnbs))
all_entities = sorted(list(all_ues) + list(all_gnbs))

# --- Dash 應用程序初始化 ---

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "5G Network Performance Dashboard"

# --- 應用程序佈局 ---

app.layout = html.Div([
    html.H1("5G 網絡性能指標儀表板"),
    
    html.Div([
        html.Label("選擇實體 (UE/gNB):"),
        dcc.Dropdown(
            id='entity-selector',
            options=[{'label': entity, 'value': entity} for entity in all_entities],
            value=all_entities if all_entities else [], # 默認選擇所有實體
            multi=True
        ),
    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
    
    html.Div([
        html.Label("選擇時間範圍:"),
        dcc.DatePickerRange(
            id='date-picker-range',
            # 根據數據設置初始日期範圍 (如果數據可用)
            # start_date=...,
            # end_date=...,
            display_format='YYYY-MM-DD'
        ),
    ], style={'width': '48%', 'display': 'inline-block'}),
    
    dcc.Tabs(id="tabs-main", value='tab-radio', children=[
        dcc.Tab(label='無線指標', value='tab-radio'),
        dcc.Tab(label='MAC 層指標', value='tab-mac'),
        dcc.Tab(label='切換性能', value='tab-handover'),
    ]),
    html.Div(id='tabs-content')
])

# --- 無線指標選項卡佈局 ---

radio_tab_layout = html.Div([
    html.H3("無線指標"),
    html.Div([
        html.Div([dcc.Graph(id='rsrp-time-series')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='rsrq-time-series')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    html.Div([
        html.Div([dcc.Graph(id='sinr-time-series')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='cqi-time-series')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    html.Div([
        html.Div([dcc.Graph(id='bler-time-series')], style={'width': '49%', 'display': 'inline-block'}),
        # 可以添加更多圖表，例如箱線圖
    ]),
])

# --- MAC 層指標選項卡佈局 ---

mac_tab_layout = html.Div([
    html.H3("MAC 層指標"),
    html.Div([
        html.Div([dcc.Graph(id='dl-throughput-time-series')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='ul-throughput-time-series')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    html.Div([
        html.Div([dcc.Graph(id='dl-latency-time-series')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='ul-latency-time-series')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    # 可以添加更多圖表，例如 RB 利用率、MCS 等
])

# --- 切換性能選項卡佈局 ---

handover_tab_layout = html.Div([
    html.H3("切換性能"),
    html.Div([
        html.Div([dcc.Graph(id='handover-counts-bar')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='handover-success-rate-bar')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    html.Div([
        html.Div([dcc.Graph(id='handover-delay-boxplot')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='ping-pong-rate-bar')], style={'width': '49%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    html.Div([dcc.Graph(id='handover-events-timeline')]), # 切換事件時間線
])

# --- 回調函數：渲染選項卡內容 ---

@app.callback(Output('tabs-content', 'children'),
              Input('tabs-main', 'value'))
def render_tab_content(tab):
    if tab == 'tab-radio':
        return radio_tab_layout
    elif tab == 'tab-mac':
        return mac_tab_layout
    elif tab == 'tab-handover':
        return handover_tab_layout
    return html.Div() # 默認返回空 Div

# --- 回調函數：更新無線指標圖表 ---

def create_time_series_figure(df, selected_entities, y_col, title, y_label):
    """創建時間序列圖的通用函數"""
    fig = go.Figure()
    if df is not None and not df.empty and selected_entities:
        # 確保 Timestamp 列是 datetime 類型
        if 'Timestamp' in df.columns:
            try:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
                df = df.dropna(subset=['Timestamp'])
            except Exception as e:
                print(f"Error converting Timestamp column: {e}")
                return fig # 返回空圖
        else:
            return fig # 返回空圖
        
        # 根據實體 ID 列名（可能是 UE ID 或 Entity ID）進行過濾
        id_col = 'UE ID' if 'UE ID' in df.columns else 'Entity ID' if 'Entity ID' in df.columns else None
        
        if id_col:
            filtered_df = df[df[id_col].isin(selected_entities)]
            
            for entity in selected_entities:
                entity_df = filtered_df[filtered_df[id_col] == entity].sort_values('Timestamp')
                if not entity_df.empty:
                    fig.add_trace(go.Scatter(x=entity_df['Timestamp'], y=entity_df[y_col], mode='lines+markers', name=entity))
        
    fig.update_layout(
        title=title,
        xaxis_title="時間",
        yaxis_title=y_label,
        legend_title="實體 ID",
        hovermode="x unified"
    )
    return fig

@app.callback(
    Output('rsrp-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_rsrp_chart(selected_entities):
    return create_time_series_figure(rsrp_df, selected_entities, 'RSRP', 'RSRP 時間序列', 'RSRP (dBm)')

@app.callback(
    Output('rsrq-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_rsrq_chart(selected_entities):
    return create_time_series_figure(rsrq_df, selected_entities, 'RSRQ', 'RSRQ 時間序列', 'RSRQ (dB)')

@app.callback(
    Output('sinr-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_sinr_chart(selected_entities):
    return create_time_series_figure(sinr_df, selected_entities, 'SINR', 'SINR 時間序列', 'SINR (dB)')

@app.callback(
    Output('cqi-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_cqi_chart(selected_entities):
    return create_time_series_figure(cqi_df, selected_entities, 'CQI', 'CQI 時間序列', 'CQI')

@app.callback(
    Output('bler-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_bler_chart(selected_entities):
    return create_time_series_figure(bler_df, selected_entities, 'BLER', 'BLER 時間序列', 'BLER (%)')

# --- 回調函數：更新 MAC 指標圖表 ---

@app.callback(
    Output('dl-throughput-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_dl_throughput_chart(selected_entities):
    return create_time_series_figure(dl_tp_df, selected_entities, 'DL Throughput (Mbps)', '下行吞吐量時間序列', '吞吐量 (Mbps)')

@app.callback(
    Output('ul-throughput-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_ul_throughput_chart(selected_entities):
    return create_time_series_figure(ul_tp_df, selected_entities, 'UL Throughput (Mbps)', '上行吞吐量時間序列', '吞吐量 (Mbps)')

@app.callback(
    Output('dl-latency-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_dl_latency_chart(selected_entities):
    return create_time_series_figure(dl_lat_df, selected_entities, 'DL Latency (ms)', '下行延遲時間序列', '延遲 (ms)')

@app.callback(
    Output('ul-latency-time-series', 'figure'),
    Input('entity-selector', 'value')
)
def update_ul_latency_chart(selected_entities):
    return create_time_series_figure(ul_lat_df, selected_entities, 'UL Latency (ms)', '上行延遲時間序列', '延遲 (ms)')

# --- 回調函數：更新切換性能圖表 ---

@app.callback(
    Output('handover-counts-bar', 'figure'),
    Input('entity-selector', 'value')
)
def update_handover_counts_chart(selected_entities):
    fig = go.Figure()
    if handover_stats and 'handover_counts' in handover_stats and selected_entities:
        counts = {entity: handover_stats['handover_counts'].get(entity, 0) for entity in selected_entities}
        if counts:
            fig.add_trace(go.Bar(x=list(counts.keys()), y=list(counts.values())))
    fig.update_layout(title="切換次數", xaxis_title="實體 ID", yaxis_title="次數")
    return fig

@app.callback(
    Output('handover-success-rate-bar', 'figure'),
    Input('entity-selector', 'value')
)
def update_handover_success_rate_chart(selected_entities):
    fig = go.Figure()
    if handover_stats and 'handover_success_rates' in handover_stats and selected_entities:
        rates = {entity: handover_stats['handover_success_rates'].get(entity, 0) * 100 for entity in selected_entities}
        if rates:
            fig.add_trace(go.Bar(x=list(rates.keys()), y=list(rates.values())))
    fig.update_layout(title="切換成功率", xaxis_title="實體 ID", yaxis_title="成功率 (%)", yaxis_range=[0, 100])
    return fig

@app.callback(
    Output('handover-delay-boxplot', 'figure'),
    Input('entity-selector', 'value')
)
def update_handover_delay_chart(selected_entities):
    fig = go.Figure()
    if handover_stats and 'handover_delays' in handover_stats and selected_entities:
        for entity in selected_entities:
            delays = handover_stats['handover_delays'].get(entity, {}).get('values', []) # 假設 JSON 中有 'values'
            # 如果 JSON 中沒有 'values'，嘗試從 handover_events_df 中提取
            if not delays and handover_events_df is not None:
                 entity_events = handover_events_df[handover_events_df['Entity ID'] == entity]
                 delays = entity_events['Delay (ms)'].dropna().tolist()
            
            if delays:
                fig.add_trace(go.Box(y=delays, name=entity))
    fig.update_layout(title="切換延遲分佈", xaxis_title="實體 ID", yaxis_title="延遲 (ms)")
    return fig

@app.callback(
    Output('ping-pong-rate-bar', 'figure'),
    Input('entity-selector', 'value')
)
def update_ping_pong_rate_chart(selected_entities):
    fig = go.Figure()
    if handover_stats and 'ping_pong_rates' in handover_stats and selected_entities:
        rates = {entity: handover_stats['ping_pong_rates'].get(entity, 0) * 100 for entity in selected_entities}
        if rates:
            fig.add_trace(go.Bar(x=list(rates.keys()), y=list(rates.values())))
    fig.update_layout(title="乒乓切換率", xaxis_title="實體 ID", yaxis_title="比率 (%)", yaxis_range=[0, 100])
    return fig

@app.callback(
    Output('handover-events-timeline', 'figure'),
    Input('entity-selector', 'value')
)
def update_handover_timeline(selected_entities):
    fig = go.Figure()
    if handover_events_df is not None and not handover_events_df.empty and selected_entities:
        try:
            handover_events_df['Timestamp'] = pd.to_datetime(handover_events_df['Timestamp'], errors='coerce')
            filtered_df = handover_events_df[handover_events_df['Entity ID'].isin(selected_entities)].dropna(subset=['Timestamp'])
            
            # 創建時間線圖 (使用 Scatter 模擬)
            fig = px.timeline(filtered_df,
                              x_start="Timestamp", 
                              x_end="Timestamp", # 點事件，開始和結束相同
                              y="Entity ID", 
                              color="Type", # 按切換類型著色
                              hover_data=["Source Cell", "Target Cell", "Delay (ms)", "Failure", "Ping-Pong"],
                              title="切換事件時間線")
            
            # 調整佈局使點更明顯
            fig.update_traces(marker=dict(size=10, symbol='circle')) 
            fig.update_layout(xaxis_title="時間")

        except Exception as e:
            print(f"Error creating handover timeline: {e}")
            # 返回空圖
            fig = go.Figure()
            fig.update_layout(title="切換事件時間線 (數據錯誤)")
            
    else:
        fig.update_layout(title="切換事件時間線 (無數據)")
        
    return fig

# --- 運行應用程序 ---

if __name__ == '__main__':
    # 運行 Dash 應用程序，監聽所有接口的 8050 端口
    # 使用 debug=True 進行開發調試，生產環境應設為 False
    app.run_server(debug=False, host='0.0.0.0', port=8050)
