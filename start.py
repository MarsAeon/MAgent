#!/usr/bin/env python3
"""
IdeaArchitect 启动脚本
自动构建前端并启动应用
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def check_node_installed():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js 已安装: {result.stdout.strip()}")
            return True
        else:
            print("✗ Node.js 未安装")
            return False
    except FileNotFoundError:
        print("✗ Node.js 未安装")
        return False

def check_python_deps():
    """检查Python依赖"""
    try:
        import eel
        import pydantic
        import loguru
        print("✓ Python 依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ Python 依赖缺失: {e}")
        return False

def install_python_deps():
    """安装Python依赖"""
    print("正在安装Python依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✓ Python 依赖安装完成")
        return True
    except subprocess.CalledProcessError:
        print("✗ Python 依赖安装失败")
        return False

def _which_executable(name: str):
    """跨平台解析可执行文件。优先避免 .ps1，Windows 下尝试 .cmd/.bat/.exe。"""
    # 明确排除 .ps1
    candidates = [name]
    if os.name == 'nt':
        base = name
        exts = [".cmd", ".exe", ".bat", ""]
        candidates = [base + ext for ext in exts]
    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    for c in ordered:
        p = shutil.which(c)
        if p and not p.lower().endswith('.ps1'):
            return p
    return None

def resolve_package_manager():
    """解析可用的包管理器，优先顺序：npm > pnpm > yarn > bun。
    返回 (pm_name, pm_path) 或 (None, None)
    """
    for name in ['npm', 'pnpm', 'yarn', 'bun']:
        p = _which_executable(name)
        if p:
            return name, p
    return None, None

def check_npm_available():
    """保持向后兼容：检查是否至少有一个包管理器可用，并特别打印 npm 状态。"""
    npm_path = _which_executable('npm')
    if npm_path:
        try:
            result = subprocess.run([npm_path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ npm 可用: {result.stdout.strip()}")
                return True
        except Exception:
            pass
    print("✗ npm 命令未找到")
    return False

def install_node_deps(pm_name: str, pm_path: str):
    """安装前端依赖，支持 npm/pnpm/yarn/bun。"""
    print("正在安装Node.js依赖...")
    try:
        if pm_name == 'npm':
            cmd = [pm_path, 'install']
        elif pm_name == 'pnpm':
            cmd = [pm_path, 'install']
        elif pm_name == 'yarn':
            cmd = [pm_path, 'install']
        elif pm_name == 'bun':
            cmd = [pm_path, 'install']
        else:
            cmd = [pm_path, 'install']
        subprocess.run(cmd, check=True)
        print("✓ Node.js 依赖安装完成")
        return True
    except FileNotFoundError:
        print("✗ 包管理器命令未找到，请检查 Node.js 安装和 PATH 配置")
        return False
    except subprocess.CalledProcessError:
        print("✗ Node.js 依赖安装失败")
        return False

def build_frontend(pm_name: str, pm_path: str):
    """构建前端，支持 npm/pnpm/yarn/bun。"""
    print("正在构建前端...")
    try:
        if pm_name == 'yarn':
            cmd = [pm_path, 'build']
        else:
            cmd = [pm_path, 'run', 'build']
        subprocess.run(cmd, check=True)
        print("✓ 前端构建完成")
        return True
    except FileNotFoundError:
        print("✗ 包管理器命令未找到，无法构建前端")
        return False
    except subprocess.CalledProcessError:
        print("✗ 前端构建失败")
        return False

def start_dev_server(pm_name: str, pm_path: str):
    """启动开发服务器"""
    print("正在启动开发服务器...")
    try:
        if pm_name == 'yarn':
            cmd = [pm_path, 'dev']
        else:
            cmd = [pm_path, 'run', 'dev']
        # 在后台启动Vite开发服务器
        dev_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 等待开发服务器启动
        time.sleep(3)

        if dev_process.poll() is None:
            print("✓ 开发服务器已启动")
            return dev_process
        else:
            print("✗ 开发服务器启动失败")
            return None
    except FileNotFoundError:
        print("✗ 包管理器命令未找到，无法启动开发服务器")
        return None
    except Exception as e:
        print(f"✗ 启动开发服务器失败: {e}")
        return None

def start_python_app():
    """启动Python应用"""
    print("正在启动Python应用...")
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()

        subprocess.run([sys.executable, 'main.py'], check=True, env=env)
    except KeyboardInterrupt:
        print("\n应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"✗ Python应用启动失败: {e}")

def start_python_only():
    """仅启动Python后端（不依赖前端）"""
    print("正在启动纯Python模式...")
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        env['IDEAARCHITECT_MODE'] = 'python_only'  # 标记为纯Python模式

        subprocess.run([sys.executable, 'main.py'], check=True, env=env)
    except KeyboardInterrupt:
        print("\n应用已停止")
    except subprocess.CalledProcessError as e:
        print(f"✗ Python应用启动失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("IdeaArchitect 启动脚本")
    print("=" * 50)

    # 检查环境
    print("\n1. 检查环境...")

    node_available = check_node_installed()
    # 解析包管理器（即使 npm 不可用，也尝试 pnpm/yarn/bun）
    pm_name, pm_path = resolve_package_manager() if node_available else (None, None)
    npm_available = check_npm_available() if node_available else False

    if not check_python_deps():
        if not install_python_deps():
            return

    # 根据环境提供不同的启动选项
    print("\n2. 选择运行模式:")

    if node_available and pm_name is not None:
        print("1. 开发模式 (使用Vite开发服务器)")
        print("2. 生产模式 (构建后运行)")
        print("3. 纯Python模式 (仅后端，无前端界面)")

        choice = input("请选择 (1/2/3): ").strip()

        if choice == "1":
            # 开发模式
            print("\n3. 检查Node.js依赖...")
            if not Path('node_modules').exists():
                if not install_node_deps(pm_name, pm_path):
                    print("依赖安装失败，切换到纯Python模式")
                    start_python_only()
                    return
            else:
                print("✓ Node.js 依赖已存在")

            print("\n4. 启动开发模式...")
            dev_process = start_dev_server(pm_name, pm_path)
            if dev_process:
                try:
                    print("正在启动Python后端...")
                    start_python_app()
                finally:
                    # 清理开发服务器
                    if dev_process and dev_process.poll() is None:
                        dev_process.terminate()
                        print("开发服务器已停止")
            else:
                print("开发服务器启动失败，切换到纯Python模式")
                start_python_only()

        elif choice == "2":
            # 生产模式
            print("\n3. 检查Node.js依赖...")
            if not Path('node_modules').exists():
                if not install_node_deps(pm_name, pm_path):
                    print("依赖安装失败，切换到纯Python模式")
                    start_python_only()
                    return

            print("\n4. 构建前端...")
            if not build_frontend(pm_name, pm_path):
                print("前端构建失败，切换到纯Python模式")
                start_python_only()
                return

            print("\n5. 启动应用...")
            start_python_app()

        elif choice == "3":
            # 纯Python模式
            start_python_only()

        else:
            print("无效选择")

    else:
        print("检测到Node.js或npm不可用")
        print("1. 纯Python模式 (仅后端，无前端界面)")
        print("2. 退出并安装Node.js")

        choice = input("请选择 (1/2): ").strip()

        if choice == "1":
            start_python_only()
        elif choice == "2":
            print("请安装Node.js: https://nodejs.org/")
            print("安装后重新运行此脚本")
        else:
            print("无效选择")

if __name__ == "__main__":
    main()
