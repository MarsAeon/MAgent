#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IdeaArchitect 生产启动脚本（非交互）
- 如果存在 dist/ 则直接启动 Python/Eel 后端加载生产前端
- 如果不存在 dist/ 则尝试构建（需要 Node.js + npm）
- 构建完成后启动应用

使用方式：
    python start_production.py
或在 package.json 中：
    npm run prod
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import socket

ROOT = Path(__file__).parent
DIST = ROOT / "dist"


def run(cmd, cwd=None, check=True, env=None):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd or ROOT, check=check, env=env)


def _which_executable(name: str):
    """跨平台解析可执行文件。优先避免 .ps1，Windows 下尝试 .cmd/.bat/.exe。"""
    candidates = [name]
    if os.name == 'nt':
        base = name
        exts = [".cmd", ".exe", ".bat", ""]
        candidates = [base + ext for ext in exts]
    # 去重并保持顺序
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


def ensure_python_deps():
    try:
        import eel  # noqa: F401
        import pydantic  # noqa: F401
        import dotenv  # noqa: F401
        print("✓ Python 依赖已就绪")
        return True
    except Exception as e:
        print("⚠ Python 依赖缺失:", e)
        print("→ 正在尝试安装 Python 依赖...")
        run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True


def ensure_dist():
    if DIST.exists() and any(DIST.iterdir()):
        print("✓ 已检测到 dist/ 生产构建")
        return True

    print("→ 未检测到 dist/，准备执行前端构建...")
    pm_name, pm_path = resolve_package_manager()
    if not pm_name:
        # 调试输出，帮助定位 PATH/PATHEXT 问题
        try:
            print("调试信息: PATH:", os.environ.get('PATH', ''))
            print("调试信息: PATHEXT:", os.environ.get('PATHEXT', ''))
            print("调试信息: which npm=", shutil.which('npm'))
            print("调试信息: which npm.cmd=", shutil.which('npm.cmd'))
            print("调试信息: which pnpm=", shutil.which('pnpm'))
            print("调试信息: which yarn=", shutil.which('yarn'))
            print("调试信息: which bun=", shutil.which('bun'))
        except Exception:
            pass
        print("✗ 未找到可用包管理器（npm/pnpm/yarn/bun），且缺少 dist/。请先安装 Node.js（https://nodejs.org/），或手动执行：\n   1) 安装依赖：npm install\n   2) 构建前端：npm run build")
        return False

    # 安装依赖
    node_modules = ROOT / 'node_modules'
    try:
        if node_modules.exists():
            # 已存在 node_modules，避免使用 npm ci 删除导致 Windows 文件锁 EPERM
            run([pm_path, "install"])  # 适用于 npm/pnpm/yarn/bun
        else:
            if pm_name == 'npm' and (ROOT / "package-lock.json").exists():
                try:
                    run([pm_path, "ci"])  # 纯净安装
                except subprocess.CalledProcessError:
                    print("⚠ npm ci 失败，尝试使用 npm install 作为回退...")
                    run([pm_path, "install"])  # 回退
            else:
                run([pm_path, "install"])  # 适用于 npm/pnpm/yarn/bun
    except subprocess.CalledProcessError as e:
        print("✗ 依赖安装失败：", e)
        return False

    # 构建
    if pm_name == 'yarn':
        run([pm_path, "build"])  # yarn build
    else:
        run([pm_path, "run", "build"])  # npm/pnpm/bun
    return DIST.exists() and any(DIST.iterdir())


def start_app():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    def is_port_free(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                return s.connect_ex((host, port)) != 0
            except Exception:
                return False

    # 读取现有端口（默认 8000），若被占用则寻找可用端口
    host = env.get("EEL_HOST", "localhost")
    try:
        current_port = int(env.get("EEL_PORT", "8000"))
    except ValueError:
        current_port = 8000

    if not is_port_free(host, current_port):
        # 寻找 8001-8100 的第一个可用端口
        for p in range(8001, 8101):
            if is_port_free(host, p):
                print(f"⚠ 端口 {current_port} 被占用，切换到可用端口 {p}")
                env["EEL_PORT"] = str(p)
                break

    # 直接使用 subprocess.run 以便传入 env
    subprocess.run([sys.executable, "main.py"], check=True, cwd=ROOT, env=env)


if __name__ == "__main__":
    print("==================================================")
    print("IdeaArchitect 生产启动")
    print("==================================================")
    if not ensure_python_deps():
        sys.exit(1)
    if not ensure_dist():
        sys.exit(2)
    start_app()

