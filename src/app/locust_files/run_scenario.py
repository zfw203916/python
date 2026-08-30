#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
性能测试场景执行器

功能特点：
1. ✅ 多场景管理
2. ✅ 交互式菜单
3. ✅ 自动生成报告
4. ✅ 环境检查
5. ✅ 日志记录

使用方式：
1. 交互式: python run_scenario.py
2. 直接运行: python run_scenario.py smoke
3. 列出场景: python run_scenario.py list
"""

import subprocess
import yaml
import sys
import os
from datetime import datetime
import time
import requests
from pathlib import Path
from utils import get_logger, setup_logging

# 获取日志器
logger = get_logger()

# ==================== 配置 ====================
class Config:
    """执行器配置"""
    
    # 配置文件
    SCENARIOS_FILE = 'scenarios.yaml'
    
    # 测试脚本
    TEST_SCRIPT_BASIC = 'locustfile.py'
    TEST_SCRIPT_ADVANCED = 'locustfile_advanced.py'
    
    # 目标服务
    TARGET_HOST = 'http://localhost:5003'
    
    # 目录
    REPORT_DIR = '../reports'
    LOG_DIR = '../logs'
    
    @classmethod
    def ensure_dirs(cls):
        """确保目录存在"""
        Path(cls.REPORT_DIR).mkdir(parents=True, exist_ok=True)
        Path(cls.LOG_DIR).mkdir(parents=True, exist_ok=True)

# ==================== 工具函数 ====================
def check_service(host: str = Config.TARGET_HOST, timeout: int = 5) -> bool:
    """
    检查目标服务是否运行
    
    Args:
        host: 服务地址
        timeout: 超时时间
        
    Returns:
        bool: 服务是否正常
    """
    try:
        response = requests.get(host, timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"❌ 服务检查失败: {e}")
        return False

def wait_for_service(host: str = Config.TARGET_HOST, max_attempts: int = 10) -> bool:
    """
    等待服务启动
    
    Args:
        host: 服务地址
        max_attempts: 最大尝试次数
        
    Returns:
        bool: 服务是否就绪
    """
    logger.info(f"⏳ 等待服务启动: {host}")
    for attempt in range(max_attempts):
        if check_service(host):
            logger.info("✅ 服务已就绪")
            return True
        logger.info(f"   等待中... ({attempt + 1}/{max_attempts})")
        time.sleep(2)
    logger.error("❌ 服务启动超时")
    return False

def load_scenarios(config_file: str = Config.SCENARIOS_FILE) -> dict:
    """
    加载场景配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        dict: 场景配置
    """
    if not os.path.exists(config_file):
        # 创建默认配置
        default_config = {
            'scenarios': {
                'smoke': {
                    'users': 10,
                    'spawn_rate': 5,
                    'run_time': '1m',
                    'description': '冒烟测试 - 快速验证系统基本功能'
                },
                'load': {
                    'users': 100,
                    'spawn_rate': 10,
                    'run_time': '5m',
                    'description': '负载测试 - 模拟正常业务负载'
                },
                'stress': {
                    'users': 500,
                    'spawn_rate': 50,
                    'run_time': '10m',
                    'description': '压力测试 - 测试系统极限'
                },
                'spike': {
                    'users': 1000,
                    'spawn_rate': 100,
                    'run_time': '5m',
                    'description': '尖刺测试 - 模拟突发流量'
                },
                'endurance': {
                    'users': 50,
                    'spawn_rate': 5,
                    'run_time': '30m',
                    'description': '耐力测试 - 长时间稳定性验证'
                },
                'soak': {
                    'users': 30,
                    'spawn_rate': 3,
                    'run_time': '60m',
                    'description': '浸泡测试 - 极限稳定性验证'
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"✅ 已创建默认配置文件: {config_file}")
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ 加载配置文件失败: {e}")
        sys.exit(1)

def run_scenario(
    scenario_name: str,
    config_file: str = Config.SCENARIOS_FILE,
    test_script: str = Config.TEST_SCRIPT_BASIC,
    debug: bool = False,
    wait_service: bool = True
) -> bool:
    """
    执行测试场景
    
    Args:
        scenario_name: 场景名称
        config_file: 配置文件
        test_script: 测试脚本
        debug: 调试模式
        wait_service: 是否等待服务
        
    Returns:
        bool: 是否成功
    """
    # 加载配置
    config = load_scenarios(config_file)
    
    if scenario_name not in config['scenarios']:
        logger.error(f"❌ 场景 '{scenario_name}' 不存在")
        logger.info(f"📋 可用场景: {', '.join(list(config['scenarios'].keys()))}")
        return False
    
    scenario = config['scenarios'][scenario_name]
    
    # 检查服务
    if wait_service and not wait_for_service():
        return False
    
    # 打印测试信息
    logger.info("=" * 80)
    logger.info(f"🚀 执行场景: {scenario_name}")
    logger.info(f"📝 描述: {scenario['description']}")
    logger.info(f"📄 测试脚本: {test_script}")
    logger.info(f"👥 并发用户数: {scenario['users']}")
    logger.info(f"📈 启动速率: {scenario['spawn_rate']} 用户/秒")
    logger.info(f"⏱️  运行时间: {scenario['run_time']}")
    logger.info("=" * 80)
    
    # 生成报告文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_report = os.path.join(Config.REPORT_DIR, f"report_{scenario_name}_{timestamp}.html")
    csv_prefix = os.path.join(Config.REPORT_DIR, f"results_{scenario_name}_{timestamp}")
    
    # 构建命令
    cmd = [
        'locust',
        '-f', test_script,
        '--host', Config.TARGET_HOST,
        '--headless',
        '-u', str(scenario['users']),
        '-r', str(scenario['spawn_rate']),
        '--run-time', scenario['run_time'],
        '--html', html_report,
        '--csv', csv_prefix,
        '--loglevel', 'INFO'
    ]
    
    if debug:
        cmd.append('--loglevel')
        cmd.append('DEBUG')
        # 移除HTML生成（加速）
        if '--html' in cmd:
            idx = cmd.index('--html')
            cmd = cmd[:idx] + cmd[idx+2:]
    
    logger.info(f"📌 执行命令: {' '.join(cmd)}\n")
    
    try:
        # 执行测试
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info("📊 测试进行中... (按 Ctrl+C 停止)\n")
        print("-" * 80)
        
        # 实时输出日志
        for line in process.stdout:
            print(line, end='')
        
        # 等待完成
        return_code = process.wait()
        
        if return_code == 0:
            logger.info("\n" + "=" * 80)
            logger.info("✅ 测试完成！")
            logger.info(f"📊 HTML报告: {html_report}")
            logger.info(f"📊 CSV数据: {csv_prefix}*.csv")
            logger.info("=" * 80)
            return True
        else:
            logger.error(f"\n❌ 测试失败，返回码: {return_code}")
            return False
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  收到中断信号，正在停止测试...")
        try:
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            logger.info("✅ 测试已停止")
        except Exception as e:
            logger.error(f"停止测试失败: {e}")
        return False
    except Exception as e:
        logger.error(f"\n❌ 执行出错: {e}")
        return False

def list_scenarios(config_file: str = Config.SCENARIOS_FILE):
    """
    列出所有可用场景
    
    Args:
        config_file: 配置文件
    """
    config = load_scenarios(config_file)
    
    logger.info("\n📋 可用的测试场景:")
    print("-" * 70)
    print(f"{'场景名称':<15} {'描述':<35} {'用户数':<10} {'运行时间'}")
    print("-" * 70)
    
    for name, scenario in config['scenarios'].items():
        print(f"{name:<15} {scenario['description']:<35} "
              f"{scenario['users']:<10} {scenario['run_time']}")
    print("-" * 70)

def interactive_mode():
    """交互式模式"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 学生管理系统 - 性能测试工具")
    logger.info("=" * 60)
    
    # 检查服务
    if not check_service():
        logger.warning("⚠️  服务未运行，请先启动服务: python app.py")
        start = input("\n是否尝试启动服务? (y/n): ").strip().lower()
        if start == 'y':
            # 尝试启动服务
            try:
                subprocess.Popen(
                    ['python', '../clients/studentmange/app.py'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("⏳ 正在启动服务...")
                time.sleep(3)
                if wait_for_service():
                    logger.info("✅ 服务启动成功")
                else:
                    logger.error("❌ 服务启动失败，请手动启动")
                    return
            except Exception as e:
                logger.error(f"❌ 启动服务失败: {e}")
                return
        else:
            logger.info("请手动启动服务后重新运行")
            return
    
    while True:
        logger.info("\n" + "-" * 60)
        logger.info("请选择操作:")
        logger.info("  1. 📋 列出所有场景")
        logger.info("  2. 🚀 执行场景 (基础脚本)")
        logger.info("  3. 🚀 执行场景 (高级脚本)")
        logger.info("  4. 🔄 执行所有场景")
        logger.info("  5. 🌐 Web UI 模式")
        logger.info("  6. 📊 查看报告")
        logger.info("  7. 🚪 退出")
        logger.info("-" * 60)
        
        choice = input("\n请输入选项 (1-7): ").strip()
        
        if choice == '1':
            list_scenarios()
        elif choice == '2':
            scenario = input("请输入场景名称 (如: smoke): ").strip()
            if scenario:
                run_scenario(scenario, test_script=Config.TEST_SCRIPT_BASIC)
        elif choice == '3':
            scenario = input("请输入场景名称 (如: load): ").strip()
            if scenario:
                run_scenario(scenario, test_script=Config.TEST_SCRIPT_ADVANCED)
        elif choice == '4':
            config = load_scenarios()
            logger.info("🔄 开始执行所有场景...")
            for name in config['scenarios'].keys():
                logger.info(f"\n{'=' * 60}")
                logger.info(f"执行场景: {name}")
                run_scenario(name, test_script=Config.TEST_SCRIPT_BASIC, wait_service=False)
                logger.info(f"{'=' * 60}")
        elif choice == '5':
            logger.info("\n🌐 启动 Web UI 模式...")
            logger.info("访问: http://localhost:8089")
            cmd = ['locust', '-f', Config.TEST_SCRIPT_BASIC, '--host', Config.TARGET_HOST]
            subprocess.run(cmd)
        elif choice == '6':
            # 列出报告
            report_dir = Path(Config.REPORT_DIR)
            if report_dir.exists():
                reports = sorted(report_dir.glob("*.html"), key=os.path.getmtime, reverse=True)
                if reports:
                    logger.info("\n📊 最近的报告:")
                    for i, report in enumerate(reports[:5], 1):
                        print(f"  {i}. {report.name}")
                    idx = input("\n选择报告查看 (输入数字): ").strip()
                    if idx.isdigit() and 1 <= int(idx) <= len(reports):
                        import webbrowser
                        webbrowser.open(str(reports[int(idx)-1]))
                else:
                    logger.info("📂 暂无报告")
            else:
                logger.info("📂 报告目录不存在")
        elif choice == '7':
            logger.info("👋 再见！")
            break
        else:
            logger.info("❌ 无效选项，请重新选择")

# ==================== 主入口 ====================
if __name__ == "__main__":
    # 确保目录存在
    Config.ensure_dirs()
    
    # 如果没有参数，进入交互模式
    if len(sys.argv) < 2:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            logger.info("\n\n👋 再见！")
    else:
        # 解析命令行参数
        command = sys.argv[1]
        debug = '--debug' in sys.argv
        
        if command == 'list':
            list_scenarios()
        elif command in ['smoke', 'load', 'stress', 'spike', 'endurance', 'soak']:
            # 使用高级脚本
            use_advanced = '--advanced' in sys.argv
            test_script = Config.TEST_SCRIPT_ADVANCED if use_advanced else Config.TEST_SCRIPT_BASIC
            run_scenario(command, test_script=test_script, debug=debug)
        else:
            logger.info(f"❌ 未知命令: {command}")
            logger.info("使用方式:")
            logger.info("  python run_scenario.py              # 交互式模式")
            logger.info("  python run_scenario.py list         # 列出所有场景")
            logger.info("  python run_scenario.py smoke        # 执行冒烟测试")
            logger.info("  python run_scenario.py load         # 执行负载测试")
            logger.info("  python run_scenario.py stress       # 执行压力测试")
            logger.info("  python run_scenario.py spike        # 执行尖刺测试")
            logger.info("  python run_scenario.py endurance    # 执行耐力测试")
            logger.info("  python run_scenario.py soak         # 执行浸泡测试")
            logger.info("  python run_scenario.py smoke --advanced  # 使用高级脚本")
            logger.info("  python run_scenario.py smoke --debug     # 调试模式")