#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能测试实时监控器 - 改进版
支持自动检测 Locust 是否运行
"""

import requests
import time
import json
import sys
import argparse
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class PerformanceMonitor:
    """
    性能监控器 - 改进版
    """
    
    def __init__(self, locust_host: str = 'http://localhost:8089'):
        self.locust_host = locust_host
        self.stats_url = f"{locust_host}/stats/requests"
        self.history = []
        self.is_running = False
        
    def check_locust(self) -> bool:
        """
        检查 Locust 是否运行
        
        Returns:
            bool: Locust 是否运行
        """
        try:
            response = requests.get(f"{self.locust_host}/", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def wait_for_locust(self, max_attempts: int = 30) -> bool:
        """
        等待 Locust 启动
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            bool: Locust 是否就绪
        """
        print("\n⏳ 等待 Locust 启动...")
        for attempt in range(max_attempts):
            if self.check_locust():
                print("✅ Locust 已就绪")
                return True
            print(f"   等待中... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
        return False
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """获取实时统计数据"""
        try:
            response = requests.get(self.stats_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    def start_locust_webui(self, test_file: str = 'locustfile.py'):
        """
        启动 Locust Web UI
        
        Args:
            test_file: 测试脚本文件
        """
        print(f"\n🚀 启动 Locust Web UI...")
        print(f"📄 测试脚本: {test_file}")
        print(f"🌐 访问地址: http://localhost:8089")
        print("=" * 60)
        
        try:
            # 在后台启动 Locust
            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    ['start', 'cmd', '/k', 'locust', '-f', test_file, '--host', 'http://localhost:5003'],
                    shell=True
                )
            else:  # Linux/Mac
                subprocess.Popen(
                    ['gnome-terminal', '--', 'locust', '-f', test_file, '--host', 'http://localhost:5003']
                    if os.system('which gnome-terminal > /dev/null 2>&1') == 0
                    else ['osascript', '-e', f'tell app "Terminal" to do script "locust -f {test_file} --host http://localhost:5003"']
                    if os.name == 'posix'
                    else ['locust', '-f', test_file, '--host', 'http://localhost:5003'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            print(f"⚠️ 自动启动失败，请手动运行: locust -f {test_file} --host=http://localhost:5003")
            print(f"错误: {e}")
        
        # 等待启动
        if self.wait_for_locust():
            print("\n✅ Locust 已启动，请在浏览器中配置测试参数")
            print("1. 设置用户数 (Number of users)")
            print("2. 设置启动速率 (Spawn rate)")
            print("3. 点击 Start swarming 开始测试")
            print("=" * 60)
        else:
            print("\n❌ Locust 启动超时，请手动启动")
            print(f"命令: locust -f {test_file} --host=http://localhost:5003")
    
    def monitor(self, interval: int = 2, duration: Optional[int] = None, auto_start: bool = False):
        """
        持续监控
        
        Args:
            interval: 刷新间隔（秒）
            duration: 监控持续时间（秒）
            auto_start: 是否自动启动 Locust
        """
        # 检查 Locust 是否运行
        if not self.check_locust():
            print("\n⚠️ Locust 未运行")
            
            if auto_start:
                self.start_locust_webui()
            else:
                print("\n请先启动 Locust:")
                print("  locust -f locustfile.py --host=http://localhost:5003")
                print("\n或者使用 run_scenario.py 启动测试")
                start = input("\n是否自动启动 Locust? (y/n): ").strip().lower()
                if start == 'y':
                    self.start_locust_webui()
                else:
                    print("请手动启动后重新运行")
                    return
        
        # 等待测试开始
        print("\n⏳ 等待测试开始...")
        while True:
            stats = self.get_stats()
            if stats and stats.get('stats', [{}])[0].get('num_requests', 0) > 0:
                print("✅ 测试已开始")
                break
            print("   等待中... (请确保在 Web UI 中点击了 Start swarming)")
            time.sleep(3)
        
        # 开始监控
        print("\n" + "=" * 90)
        print("📊 性能测试实时监控")
        print("=" * 90)
        print(f"🔄 刷新间隔: {interval}秒")
        print(f"📍 Locust地址: {self.locust_host}")
        print("-" * 90)
        
        # 表头
        print(f"{'时间':<20} {'总请求':<10} {'失败':<10} {'成功率':<10} "
              f"{'平均响应(ms)':<15} {'95%响应(ms)':<15} {'RPS':<10} {'状态'}")
        print("-" * 90)
        
        start_time = time.time()
        last_requests = 0
        
        try:
            while True:
                # 检查是否超时
                if duration and (time.time() - start_time) > duration:
                    break
                
                stats = self.get_stats()
                if stats:
                    # 解析数据
                    total = stats.get('stats', [{}])[0]
                    num_requests = total.get('num_requests', 0)
                    num_failures = total.get('num_failures', 0)
                    success_rate = ((num_requests - num_failures) / num_requests * 100) if num_requests > 0 else 100
                    avg_response = total.get('avg_response_time', 0)
                    p95_response = total.get('current_response_time_percentile_95', 0)
                    rps = total.get('current_rps', 0)
                    
                    # 计算增量 RPS
                    if last_requests > 0:
                        delta_rps = (num_requests - last_requests) / interval
                    else:
                        delta_rps = 0
                    last_requests = num_requests
                    
                    # 状态判断
                    if success_rate > 99:
                        status = "✅ 优秀"
                    elif success_rate > 95:
                        status = "⚠️ 良好"
                    else:
                        status = "❌ 需关注"
                    
                    # 格式化输出
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"{timestamp:<20} {num_requests:<10} {num_failures:<10} "
                          f"{success_rate:>6.2f}%   "
                          f"{avg_response:>10.2f}   {p95_response:>10.2f}   "
                          f"{delta_rps:>6.2f}    {status}")
                    
                    # 保存历史
                    self.history.append({
                        'timestamp': timestamp,
                        'num_requests': num_requests,
                        'num_failures': num_failures,
                        'success_rate': success_rate,
                        'avg_response': avg_response,
                        'p95_response': p95_response,
                        'rps': delta_rps
                    })
                    
                    # 检查告警
                    self._check_alerts(total)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  监控停止")
            self._print_summary()
    
    def _check_alerts(self, stats: Dict[str, Any]):
        """检查性能告警"""
        num_requests = stats.get('num_requests', 0)
        if num_requests == 0:
            return
        
        num_failures = stats.get('num_failures', 0)
        failure_rate = num_failures / num_requests * 100
        
        avg_response = stats.get('avg_response_time', 0)
        
        # 告警阈值
        if failure_rate > 5:
            print(f"🚨 [严重] 失败率过高: {failure_rate:.2f}%")
        elif failure_rate > 1:
            print(f"⚠️ [警告] 失败率偏高: {failure_rate:.2f}%")
        
        if avg_response > 1000:
            print(f"🚨 [严重] 响应时间过长: {avg_response:.2f}ms")
        elif avg_response > 500:
            print(f"⚠️ [警告] 响应时间偏长: {avg_response:.2f}ms")
    
    def _print_summary(self):
        """打印监控摘要"""
        if not self.history:
            return
        
        print("\n" + "=" * 70)
        print("📊 监控摘要")
        print("=" * 70)
        
        # 计算统计数据
        first = self.history[0]
        last = self.history[-1]
        
        total_requests = last['num_requests'] - first['num_requests']
        total_failures = last['num_failures'] - first['num_failures']
        success_rate = ((total_requests - total_failures) / total_requests * 100) if total_requests > 0 else 0
        
        avg_response = sum(h['avg_response'] for h in self.history) / len(self.history)
        max_rps = max(h['rps'] for h in self.history)
        
        print(f"  总请求数: {total_requests:,}")
        print(f"  失败请求数: {total_failures:,}")
        print(f"  成功率: {success_rate:.2f}%")
        print(f"  平均响应时间: {avg_response:.2f}ms")
        print(f"  最大吞吐量: {max_rps:.2f} RPS")
        print("=" * 70)
    
    def export_data(self, filename: str = 'monitor_data.json'):
        """导出监控数据"""
        if not self.history:
            print("⚠️ 没有数据可导出")
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            print(f"✅ 数据已导出: {filename}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='性能测试监控器')
    parser.add_argument('--host', default='http://localhost:8089', help='Locust Web UI地址')
    parser.add_argument('--interval', type=int, default=2, help='刷新间隔（秒）')
    parser.add_argument('--duration', type=int, help='监控持续时间（秒）')
    parser.add_argument('--export', help='导出数据文件')
    parser.add_argument('--auto-start', action='store_true', help='自动启动 Locust')
    parser.add_argument('--test-file', default='locustfile.py', help='测试脚本文件')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.host)
    
    try:
        monitor.monitor(
            interval=args.interval,
            duration=args.duration,
            auto_start=args.auto_start
        )
        
        if args.export:
            monitor.export_data(args.export)
    except KeyboardInterrupt:
        print("\n👋 再见！")

if __name__ == "__main__":
    main()