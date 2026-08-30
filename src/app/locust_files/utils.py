"""
工具函数模块
提供：日志管理、数据生成、报告生成等
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import matplotlib.pyplot as plt
from faker import Faker

# 初始化 Faker
fake = Faker('zh_CN')

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_dir: 日志目录
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    # 创建日志目录
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger('PerformanceTest')
    logger.setLevel(logging.DEBUG)
    
    # 文件处理器 - INFO级别
    log_file = Path(log_dir) / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def generate_test_data(count: int = 100) -> List[Dict[str, Any]]:
    """
    生成测试数据
    
    Args:
        count: 生成数量
        
    Returns:
        List[Dict]: 测试数据列表
    """
    data = []
    for _ in range(count):
        data.append({
            "name": fake.name(),
            "student_id": fake.unique.random_number(digits=10),
            "age": fake.random_int(min=18, max=25),
            "email": fake.email(),
            "phone": fake.phone_number()
        })
    return data

def generate_report(stats: Dict[str, Any], report_dir: str = "reports") -> str:
    """
    生成测试报告
    
    Args:
        stats: 统计数据
        report_dir: 报告目录
        
    Returns:
        str: 报告文件路径
    """
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path(report_dir) / f"report_{timestamp}.html"
    
    # 生成HTML报告
    html_content = generate_html_report(stats)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(report_file)

def generate_html_report(stats: Dict[str, Any]) -> str:
    """
    生成HTML报告内容
    
    Args:
        stats: 统计数据
        
    Returns:
        str: HTML内容
    """
    total = stats.get('total', {})
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>性能测试报告</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #667eea; }}
            .stat-label {{ color: #666; font-size: 14px; }}
            .stat-value {{ color: #333; font-size: 24px; font-weight: bold; margin-top: 5px; }}
            .success {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
            .danger {{ color: #dc3545; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #667eea; color: white; }}
            tr:hover {{ background: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 性能测试报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">总请求数</div>
                    <div class="stat-value">{total.get('num_requests', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">失败请求数</div>
                    <div class="stat-value">{total.get('num_failures', 0)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">成功率</div>
                    <div class="stat-value">{total.get('success_rate', 0):.2f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">平均响应时间</div>
                    <div class="stat-value">{total.get('avg_response_time', 0):.2f}ms</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">95% 响应时间</div>
                    <div class="stat-value">{total.get('p95_response_time', 0):.2f}ms</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">吞吐量 (RPS)</div>
                    <div class="stat-value">{total.get('rps', 0):.2f}</div>
                </div>
            </div>
            
            <h2>📋 各接口详情</h2>
            <table>
                <thead>
                    <tr>
                        <th>接口</th>
                        <th>请求数</th>
                        <th>失败数</th>
                        <th>平均响应(ms)</th>
                        <th>95%响应(ms)</th>
                        <th>失败率</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for name, stat in stats.get('entries', {}).items():
        failure_rate = (stat.get('num_failures', 0) / stat.get('num_requests', 1)) * 100
        html += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{stat.get('num_requests', 0)}</td>
                        <td>{stat.get('num_failures', 0)}</td>
                        <td>{stat.get('avg_response_time', 0):.2f}</td>
                        <td>{stat.get('p95_response_time', 0):.2f}</td>
                        <td class="{'success' if failure_rate < 1 else 'warning' if failure_rate < 5 else 'danger'}">{failure_rate:.2f}%</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
            
            <h2>📈 性能建议</h2>
            <ul>
    """
    
    # 性能建议
    avg_response = total.get('avg_response_time', 0)
    failure_rate = total.get('failure_rate', 0)
    
    if avg_response < 200:
        html += "<li>✅ 响应时间优秀 (&lt;200ms)</li>"
    elif avg_response < 500:
        html += "<li>⚠️ 响应时间可接受 (200-500ms)，建议优化</li>"
    else:
        html += "<li>❌ 响应时间过长 (&gt;500ms)，需要重点优化</li>"
    
    if failure_rate < 0.5:
        html += "<li>✅ 错误率极低 (&lt;0.5%)，系统稳定</li>"
    elif failure_rate < 1:
        html += "<li>⚠️ 错误率可接受 (0.5%-1%)，建议监控</li>"
    else:
        html += "<li>❌ 错误率过高 (&gt;1%)，需要排查问题</li>"
    
    html += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

def convert_to_dataframe(results_file: str) -> pd.DataFrame:
    """
    将Locust结果转换为DataFrame
    
    Args:
        results_file: CSV文件路径
        
    Returns:
        pd.DataFrame: 数据框
    """
    try:
        df = pd.read_csv(results_file)
        return df
    except Exception as e:
        logging.error(f"转换数据失败: {e}")
        return pd.DataFrame()

def get_logger() -> logging.Logger:
    """
    获取全局日志器
    
    Returns:
        logging.Logger: 日志器实例
    """
    return setup_logging()