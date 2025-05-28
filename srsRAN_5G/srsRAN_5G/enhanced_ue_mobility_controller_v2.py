#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced UE mobility controller implementing realistic movement models and a pluggable channel model interface.
"""
import os
import sys
import time
import json
import random
import math
import argparse
import subprocess
import threading
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from channel_models import (
    Position,
    ChannelModel,
    SimplifiedChannelModel,
    ExternalChannelModelPlaceholder,
)

# --- 網絡實體類 --- 

class GNB:
    """基站類，表示網絡中的一個 gNB"""
    def __init__(self, gnb_id, position, frequency, power):
        self.gnb_id = gnb_id
        self.position = position
        self.frequency = frequency  # MHz
        self.power = power  # dBm
        # self.coverage_radius = coverage_radius # 移除固定的覆蓋半徑，由信道模型決定
        self.connected_ues = []
    
    # 移除 calculate_rsrp 和 is_in_coverage，這些由信道模型處理
    # def calculate_rsrp(self, ue_position):
    # def is_in_coverage(self, ue_position):
    
    def __str__(self):
        return f"gNB{self.gnb_id} at {self.position}, freq={self.frequency}MHz, power={self.power}dBm"

class UE:
    """用戶設備類，表示網絡中的一個 UE"""
    def __init__(self, ue_id, initial_position, mobility_type, speed, config_file):
        self.ue_id = ue_id
        self.position = initial_position
        self.mobility_type = mobility_type  # 'static', 'random_walk', 'directed', 'trajectory', 'group'
        self.speed = speed  # meters per second
        self.config_file = config_file
        self.connected_gnb = None
        self.process = None
        self.is_running = False
        self.trajectory = []  # 記錄移動軌跡
        self.record_position()
        
        # 移動參數
        self.direction = random.uniform(0, 2 * math.pi)  # 隨機初始方向（弧度）
        self.direction_change_prob = 0.2  # 改變方向的概率
        self.stop_prob = 0.05  # 停止移動的概率
        self.resume_prob = 0.1  # 恢復移動的概率
        self.is_moving = True
        
        # 軌跡移動的路徑點
        self.waypoints = []
        self.current_waypoint_index = 0
        
        # 群組移動的參數
        self.group_center = None
        self.group_offset = Position(random.uniform(-20, 20), random.uniform(-20, 20))
    
    def record_position(self):
        """記錄當前位置到軌跡"""
        self.trajectory.append((self.position.x, self.position.y, time.time()))
    
    def set_waypoints(self, waypoints):
        """設置軌跡移動的路徑點"""
        self.waypoints = waypoints
        self.current_waypoint_index = 0
    
    def set_group_center(self, center_ue):
        """設置群組移動的中心 UE"""
        self.group_center = center_ue
    
    def move(self, time_step, boundary):
        """根據移動模型移動 UE"""
        if not self.is_moving:
            # 有一定概率恢復移動
            if random.random() < self.resume_prob:
                self.is_moving = True
            else:
                self.record_position()
                return
        
        # 有一定概率停止移動
        if random.random() < self.stop_prob:
            self.is_moving = False
            self.record_position()
            return
        
        # 根據不同的移動模型計算新位置
        if self.mobility_type == 'static':
            # 靜止用戶不移動
            pass
        
        elif self.mobility_type == 'random_walk':
            # 隨機行走模型
            # 有一定概率改變方向
            if random.random() < self.direction_change_prob:
                self.direction = random.uniform(0, 2 * math.pi)
            
            # 計算移動距離
            distance = self.speed * time_step
            
            # 計算新位置
            new_x = self.position.x + distance * math.cos(self.direction)
            new_y = self.position.y + distance * math.sin(self.direction)
            
            # 檢查邊界 (反彈)
            if new_x < 0:
                new_x = -new_x
                self.direction = math.pi - self.direction
            elif new_x > boundary[0]:
                new_x = 2 * boundary[0] - new_x
                self.direction = math.pi - self.direction
                
            if new_y < 0:
                new_y = -new_y
                self.direction = -self.direction
            elif new_y > boundary[1]:
                new_y = 2 * boundary[1] - new_y
                self.direction = -self.direction
            
            self.direction = self.direction % (2 * math.pi) # 確保方向在 [0, 2pi)
            self.position.x = new_x
            self.position.y = new_y
        
        elif self.mobility_type == 'directed':
            # 定向移動模型
            # 計算移動距離
            distance = self.speed * time_step
            
            # 計算新位置
            new_x = self.position.x + distance * math.cos(self.direction)
            new_y = self.position.y + distance * math.sin(self.direction)
            
            # 檢查邊界 (環繞)
            new_x = new_x % boundary[0]
            new_y = new_y % boundary[1]
            
            self.position.x = new_x
            self.position.y = new_y
        
        elif self.mobility_type == 'trajectory':
            # 軌跡移動模型
            if not self.waypoints:
                return
            
            # 獲取當前目標路徑點
            target = self.waypoints[self.current_waypoint_index]
            target_pos = Position(target[0], target[1])
            
            # 計算到目標的距離
            distance_to_target = self.position.distance_to(target_pos)
            
            # 計算移動距離
            move_distance = self.speed * time_step
            
            if move_distance >= distance_to_target:
                # 到達當前路徑點
                self.position.x = target_pos.x
                self.position.y = target_pos.y
                
                # 移動到下一個路徑點
                self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
            else:
                # 計算移動方向
                direction = math.atan2(target_pos.y - self.position.y, target_pos.x - self.position.x)
                
                # 計算新位置
                self.position.x += move_distance * math.cos(direction)
                self.position.y += move_distance * math.sin(direction)
        
        elif self.mobility_type == 'group':
            # 群組移動模型
            if not self.group_center:
                return
            
            # 獲取群組中心位置
            center_pos = self.group_center.position
            
            # 計算相對於中心的目標位置
            target_x = center_pos.x + self.group_offset.x
            target_y = center_pos.y + self.group_offset.y
            
            # 計算到目標的距離和方向
            dx = target_x - self.position.x
            dy = target_y - self.position.y
            distance_to_target = math.sqrt(dx*dx + dy*dy)
            
            if distance_to_target > 0:
                direction = math.atan2(dy, dx)
                
                # 計算移動距離
                move_distance = min(self.speed * time_step, distance_to_target)
                
                # 計算新位置
                self.position.x += move_distance * math.cos(direction)
                self.position.y += move_distance * math.sin(direction)
        
        # 記錄位置
        self.record_position()
    
    def start(self, network_namespace):
        """啟動 UE 進程"""
        if self.is_running:
            return
        
        # 創建網絡命名空間（如果不存在）
        try:
            subprocess.run(['sudo', 'ip', 'netns', 'add', network_namespace], check=False, capture_output=True)
        except Exception as e:
            print(f"Error creating netns {network_namespace}: {e}")
            # 可能已經存在，繼續嘗試
            pass
        
        # 啟動 UE 進程
        # 注意：srsUE 可能需要 root 權限或特定能力來創建 TUN 接口
        # 使用 sudo 或調整權限
        cmd = ['sudo', 'ip', 'netns', 'exec', network_namespace, '/usr/local/bin/srsue', self.config_file]
        log_file_path = f"/home/eezim/workspace/srsRAN_5G/ue{self.ue_id}.log"
        try:
            with open(log_file_path, 'w') as log_file:
                self.process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
            self.is_running = True
            print(f"UE{self.ue_id} started with config {self.config_file}, logging to {log_file_path}")
        except Exception as e:
             print(f"Error starting UE{self.ue_id}: {e}")
             self.is_running = False

    def stop(self):
        """停止 UE 進程"""
        if not self.is_running:
            return
        
        # 停止 UE 進程
        if self.process:
            try:
                # 使用 sudo 殺死進程
                subprocess.run(['sudo', 'kill', str(self.process.pid)], check=False)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                subprocess.run(['sudo', 'kill', '-9', str(self.process.pid)], check=False)
            except Exception as e:
                print(f"Error stopping UE{self.ue_id} process: {e}")
            finally:
                 self.process = None
        
        self.is_running = False
        print(f"UE{self.ue_id} stopped")
        
        # 清理網絡命名空間
        network_namespace = f"ue{self.ue_id}"
        try:
            subprocess.run(['sudo', 'ip', 'netns', 'delete', network_namespace], check=False, capture_output=True)
        except Exception as e:
            print(f"Error deleting netns {network_namespace}: {e}")

    def connect_to_gnb(self, gnb):
        """連接到指定的 gNB"""
        if self.connected_gnb == gnb:
            return
        
        # 斷開與當前 gNB 的連接
        if self.connected_gnb:
            if self in self.connected_gnb.connected_ues:
                 self.connected_gnb.connected_ues.remove(self)
        
        # 連接到新的 gNB
        self.connected_gnb = gnb
        if gnb and self not in gnb.connected_ues:
             gnb.connected_ues.append(self)
        
        if gnb:
            print(f"UE{self.ue_id} connected to gNB{gnb.gnb_id}")
        else:
            print(f"UE{self.ue_id} disconnected")

    def __str__(self):
        mobility = self.mobility_type.replace('_', ' ').title()
        return f"UE{self.ue_id} at {self.position}, {mobility}, speed={self.speed}m/s"

# --- 網絡模擬器 --- 

class NetworkSimulator:
    """網絡模擬器，管理 gNB 和 UE，並模擬它們的行為"""
    def __init__(self, config_dir, simulation_area=(1000, 1000), channel_model: ChannelModel = SimplifiedChannelModel()):
        self.config_dir = config_dir
        self.simulation_area = simulation_area  # meters
        self.gnbs = []
        self.ues = []
        self.time_step = 1.0  # seconds
        self.simulation_time = 0.0  # seconds
        self.is_running = False
        self.event_log = []
        self.rsrp_log = []
        self.channel_model = channel_model # 使用注入的信道模型
        
        # 創建輸出目錄
        self.output_dir = '/home/eezim/workspace/srsRAN_5G/mobility_data'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def setup_network(self):
        """設置網絡拓撲，創建 gNB 和 UE"""
        # 創建 gNB (移除 coverage_radius)
        self.gnbs = [
            GNB(1, Position(250, 250), 3350, 43),
            GNB(2, Position(750, 250), 3400, 43),
            GNB(3, Position(250, 750), 3450, 40),
            GNB(4, Position(750, 750), 3500, 40)
        ]
        
        # 創建 UE
        self.ues = [
            UE(1, Position(250, 250), 'static', 0, os.path.join(self.config_dir, 'ue/ue1.conf')),
            UE(2, Position(750, 250), 'random_walk', 1.4, os.path.join(self.config_dir, 'ue/ue2.conf')),
            UE(3, Position(250, 750), 'directed', 5.0, os.path.join(self.config_dir, 'ue/ue3.conf')),
            UE(4, Position(750, 750), 'trajectory', 16.7, os.path.join(self.config_dir, 'ue/ue4.conf')),
            UE(5, Position(730, 230), 'group', 1.2, os.path.join(self.config_dir, 'ue/ue5.conf')),
            UE(6, Position(500, 500), 'random_walk', 0.8, os.path.join(self.config_dir, 'ue/ue6.conf'))
        ]
        
        # 設置 UE4 的軌跡
        waypoints = [(750, 750), (750, 250), (250, 250), (250, 750), (750, 750)]
        self.ues[3].set_waypoints(waypoints)
        
        # 設置 UE5 的群組中心
        self.ues[4].set_group_center(self.ues[1])
        
        # 初始連接 (使用信道模型)
        for ue in self.ues:
            best_gnb = None
            best_rsrp = -float('inf')
            
            for gnb in self.gnbs:
                rsrp = self.channel_model.calculate_rsrp(gnb, ue.position)
                if rsrp > best_rsrp and self.channel_model.is_in_coverage(gnb, ue.position):
                    best_rsrp = rsrp
                    best_gnb = gnb
            
            if best_gnb:
                ue.connect_to_gnb(best_gnb)
                self.log_event(f"UE{ue.ue_id} initially connected to gNB{best_gnb.gnb_id} with RSRP {best_rsrp:.2f} dBm")
            else:
                self.log_event(f"UE{ue.ue_id} could not find initial serving gNB")

    def log_event(self, message):
        """記錄事件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        event = {
            "timestamp": timestamp,
            "simulation_time": self.simulation_time,
            "message": message
        }
        self.event_log.append(event)
        print(f"[{timestamp}] {message}")
    
    def log_rsrp(self, ue, gnb, rsrp):
        """記錄 RSRP 測量"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "simulation_time": self.simulation_time,
            "ue_id": ue.ue_id,
            "gnb_id": gnb.gnb_id,
            "rsrp": rsrp
        }
        self.rsrp_log.append(entry)
    
    def update_connections(self):
        """更新 UE 與 gNB 的連接 (使用信道模型)"""
        handover_threshold = -105 # RSRP 閾值觸發切換測量
        a3_offset = 3  # dB, A3 事件偏移
        coverage_threshold = -110 # dBm, 最低覆蓋 RSRP

        for ue in self.ues:
            # 計算當前連接的 RSRP
            current_rsrp = -float('inf')
            if ue.connected_gnb:
                current_rsrp = self.channel_model.calculate_rsrp(ue.connected_gnb, ue.position)
                self.log_rsrp(ue, ue.connected_gnb, current_rsrp)
            
            # 計算所有 gNB 的 RSRP
            rsrp_measurements = []
            for gnb in self.gnbs:
                 rsrp = self.channel_model.calculate_rsrp(gnb, ue.position)
                 if gnb != ue.connected_gnb:
                     self.log_rsrp(ue, gnb, rsrp)
                 # 只有當 RSRP 高於某個閾值時才考慮作為潛在目標
                 if rsrp > handover_threshold:
                     rsrp_measurements.append((gnb, rsrp))
            
            # 檢查是否需要切換
            best_candidate_gnb = None
            best_candidate_rsrp = -float('inf')

            if rsrp_measurements:
                # 找出最佳的候選 gNB (排除當前服務 gNB)
                potential_targets = [(gnb, rsrp) for gnb, rsrp in rsrp_measurements if gnb != ue.connected_gnb]
                if potential_targets:
                    best_candidate_gnb, best_candidate_rsrp = max(potential_targets, key=lambda x: x[1])
            
            # 判斷切換條件
            perform_handover = False
            if best_candidate_gnb:
                 # A3 事件: 鄰區 RSRP > 服務小區 RSRP + 偏移
                 if best_candidate_rsrp > current_rsrp + a3_offset:
                     perform_handover = True
                 # A2 事件觸發的 A4/A5: 服務小區 RSRP 低於閾值，且鄰區 RSRP 高於某閾值
                 elif current_rsrp < handover_threshold and best_candidate_rsrp > handover_threshold:
                     perform_handover = True
            
            if perform_handover:
                 old_gnb_id = ue.connected_gnb.gnb_id if ue.connected_gnb else "None"
                 ue.connect_to_gnb(best_candidate_gnb)
                 self.log_event(f"Handover: UE{ue.ue_id} from gNB{old_gnb_id} to gNB{best_candidate_gnb.gnb_id}, RSRP: {current_rsrp:.2f} -> {best_candidate_rsrp:.2f} dBm")
            
            # 檢查是否脫網 (基於覆蓋閾值)
            if ue.connected_gnb and not self.channel_model.is_in_coverage(ue.connected_gnb, ue.position, threshold=coverage_threshold):
                old_gnb_id = ue.connected_gnb.gnb_id
                self.log_event(f"UE{ue.ue_id} out of coverage from gNB{old_gnb_id} (RSRP {current_rsrp:.2f} < {coverage_threshold} dBm)")
                ue.connect_to_gnb(None) # 斷開連接
                # 嘗試重新連接到其他基站
                best_reconnect_gnb = None
                best_reconnect_rsrp = -float('inf')
                for gnb in self.gnbs:
                    rsrp = self.channel_model.calculate_rsrp(gnb, ue.position)
                    if rsrp > best_reconnect_rsrp and self.channel_model.is_in_coverage(gnb, ue.position, threshold=coverage_threshold):
                        best_reconnect_rsrp = rsrp
                        best_reconnect_gnb = gnb
                if best_reconnect_gnb:
                    ue.connect_to_gnb(best_reconnect_gnb)
                    self.log_event(f"UE{ue.ue_id} reconnected to gNB{best_reconnect_gnb.gnb_id} with RSRP {best_reconnect_rsrp:.2f} dBm")
                else:
                    self.log_event(f"UE{ue.ue_id} could not find a suitable gNB to reconnect")

    def generate_random_events(self):
        """生成隨機事件，例如 UE 啟動/停止"""
        start_prob = 0.01 # 每個時間步啟動一個停止的 UE 的概率
        stop_prob = 0.005 # 每個時間步停止一個運行的 UE 的概率

        for ue in self.ues:
            if not ue.is_running and random.random() < start_prob:
                network_namespace = f"ue{ue.ue_id}"
                ue.start(network_namespace)
                self.log_event(f"Random Event: UE{ue.ue_id} started")
            elif ue.is_running and random.random() < stop_prob:
                ue.stop()
                self.log_event(f"Random Event: UE{ue.ue_id} stopped")

    def start_simulation(self, duration=300):
        """啟動模擬"""
        if self.is_running:
            return
        
        self.is_running = True
        self.simulation_time = 0.0
        
        # 設置網絡
        self.setup_network()
        
        # 啟動所有 UE
        for ue in self.ues:
            network_namespace = f"ue{ue.ue_id}"
            ue.start(network_namespace)
        
        self.log_event(f"Simulation started with {self.channel_model.__class__.__name__}")
        
        # 模擬循環
        try:
            while self.is_running and self.simulation_time < duration:
                start_step_time = time.time()
                
                # 移動 UE
                for ue in self.ues:
                    ue.move(self.time_step, self.simulation_area)
                
                # 更新連接
                self.update_connections()
                
                # 隨機事件
                self.generate_random_events()
                
                # 更新模擬時間
                self.simulation_time += self.time_step
                
                # 每 10 秒保存一次數據
                if int(self.simulation_time) % 10 == 0:
                    self.save_data()
                
                # 控制模擬速度，確保每個時間步大致等於 time_step
                end_step_time = time.time()
                elapsed_time = end_step_time - start_step_time
                sleep_time = self.time_step - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            self.log_event("Simulation interrupted by user")
        
        finally:
            self.stop_simulation()

    def stop_simulation(self):
        """停止模擬"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.log_event("Stopping simulation...")
        
        # 停止所有 UE
        for ue in self.ues:
            ue.stop()
        
        # 保存最終數據
        self.save_data()
        
        self.log_event("Simulation stopped")

    def save_data(self):
        """保存模擬數據（軌跡、事件、RSRP）"""
        # 保存 UE 軌跡
        trajectories = {}
        for ue in self.ues:
            trajectories[f"UE{ue.ue_id}"] = ue.trajectory
        with open(os.path.join(self.output_dir, "ue_trajectories.json"), "w") as f:
            json.dump(trajectories, f, indent=2)
            
        # 保存事件日誌
        with open(os.path.join(self.output_dir, "simulation_events.json"), "w") as f:
            json.dump(self.event_log, f, indent=2)
            
        # 保存 RSRP 日誌
        with open(os.path.join(self.output_dir, "rsrp_log.json"), "w") as f:
            json.dump(self.rsrp_log, f, indent=2)
            
        print(f"Simulation data saved to {self.output_dir}")

    def plot_network(self):
        """繪製網絡拓撲和 UE 軌跡"""
        plt.figure(figsize=(10, 10))
        
        # 繪製 gNB
        for gnb in self.gnbs:
            plt.scatter(
            gnb.position.x,
            gnb.position.y,
            marker='^',
            s=200,
            c='red',
            label=f"gNB{gnb.gnb_id}"
        )
            # 繪製理論覆蓋範圍 (使用簡化模型計算半徑)
            # coverage_radius = gnb.coverage_radius # 移除
            # circle = plt.Circle((gnb.position.x, gnb.position.y), coverage_radius, color='red', fill=False, linestyle='--')
            # plt.gca().add_patch(circle)
        
        # 繪製 UE 軌跡
        colors = plt.cm.viridis(np.linspace(0, 1, len(self.ues)))
        for i, ue in enumerate(self.ues):
            if ue.trajectory:
                x_coords = [pos[0] for pos in ue.trajectory]
                y_coords = [pos[1] for pos in ue.trajectory]
                plt.plot(
                    x_coords,
                    y_coords,
                    marker='.',
                    linestyle='-',
                    markersize=2,
                    color=colors[i],
                    label=f"UE{ue.ue_id}"
                )
        
        plt.title("Network Topology and UE Trajectories")
        plt.xlabel("X Coordinate (m)")
        plt.ylabel("Y Coordinate (m)")
        plt.xlim(0, self.simulation_area[0])
        plt.ylim(0, self.simulation_area[1])
        plt.grid(True)
        plt.legend()
        plt.gca().set_aspect('equal', adjustable='box')
        
        plt.savefig(os.path.join(self.output_dir, "network_topology.png"))
        plt.close()
        print(f"Network topology plot saved to {self.output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced UE Mobility Controller with Channel Model Interface")
    parser.add_argument("--config-dir", default="/home/eezim/workspace/srsRAN_5G/enhanced_srsran_configs", help="Directory containing UE/gNB config files")
    parser.add_argument("--duration", type=int, default=120, help="Simulation duration in seconds")
    parser.add_argument("--time-step", type=float, default=1.0, help="Simulation time step in seconds")
    parser.add_argument("--channel-model", choices=["simplified", "external"], default="simplified", help="Channel model to use")
    args = parser.parse_args()

    # 選擇信道模型
    if args.channel_model == "external":
        # 在這裡實例化並配置外部信道模型 API
        # external_api = YourExternalSimulatorAPI()
        # channel_model = ExternalChannelModelPlaceholder(external_api)
        channel_model = ExternalChannelModelPlaceholder() # 使用佔位符
    else:
        channel_model = SimplifiedChannelModel()

    simulator = NetworkSimulator(args.config_dir, channel_model=channel_model)
    simulator.time_step = args.time_step
    
    try:
        simulator.start_simulation(duration=args.duration)
    finally:
        # 確保模擬停止並保存數據
        if simulator.is_running:
            simulator.stop_simulation()
        # 繪製網絡圖
        simulator.plot_network()

if __name__ == "__main__":
    # 確保以 root 權限運行，因為需要操作網絡命名空間
    if os.geteuid() != 0:
        print("Warning: This script might need root privileges to manage network namespaces.")
        # 可以選擇退出或繼續
        # sys.exit("Please run as root or using sudo.")
    main()
