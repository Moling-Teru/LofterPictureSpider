import subprocess
import threading
import sys
import time
from typing import Any
import datetime
import color
import os
import shutil

def load_config(target:str) -> Any:
    import yaml

    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        result = config[target]

    return result


def check_folder(tag: str) -> str:
    import os

    if not os.path.exists('contents'):
        os.makedirs('contents')

    if not os.path.exists(f'contents/tag-{tag}'):
        os.makedirs(f'contents/tag-{tag}')

    path=f'contents/tag-{tag}/{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
    if not os.path.exists(path):
        os.makedirs(path)

    shutil.copy('config.yaml', f'{path}/config.yaml')

    return path

cl = color.Color()
# --- 配置区 ---
# 1. 要运行的工作脚本文件名
WORKER_SCRIPT = "Amain.py"

# 2. 限制同时运行的最大进程数
MAX_CONCURRENT_PROCESSES = 3

# 3. 你想要运行的总次数
TOTAL_RUNS : list = load_config('turn')

# 4. 设置路径
CHECK_FOLDER = check_folder(load_config('tag'))

# --- 配置区结束 ---

def get_platform_command(script_name, run_index):
    """
    根据不同的操作系统生成用于在新终端中运行脚本的命令。
    """
    # 将运行序号作为命令行参数传递给 worker.py
    python_command = f'python {script_name} --offset {run_index} --path {CHECK_FOLDER} --proxies 0'  # 代理开关

    if sys.platform == "win32":
        # Windows系统: 使用 'start /wait' 命令在新 cmd 窗口中运行
        # 'start /wait' 会等待新窗口的进程结束后才返回
        # 'cmd /c' 表示执行完命令后关闭窗口
        return {
            "command": python_command,
            "flags": subprocess.CREATE_NEW_CONSOLE
        }

    elif sys.platform == "darwin":
        # macOS系统: 使用 AppleScript 来告诉终端(Terminal.app)执行新命令
        # 这会为每个进程打开一个新的终端标签页或窗口
        osascript_command = f'tell application "Terminal" to do script "cd {os.getcwd()}; {python_command}; exit"'
        return ["osascript", "-e", osascript_command]

    elif sys.platform.startswith("linux"):
        # Linux系统: 常见的终端是 gnome-terminal, konsole, xterm等
        # 注意：你可能需要根据你使用的终端修改此命令
        # gnome-terminal:
        return ["gnome-terminal", "--", "bash", "-c", f"{python_command}; exec bash"]
        # 如果想让窗口执行完后自动关闭，使用下面的命令
        # return ["gnome-terminal", "--", "bash", "-c", f"{python_command}; exit"]
        # xterm:
        # return ["xterm", "-e", f"bash -c '{python_command}; read -p \"Press Enter to close...\"'"]

    else:
        raise NotImplementedError(f"不支持的操作系统: {sys.platform}")


def run_worker_in_new_terminal(semaphore, run_index, run_times: int):
    """
    一个线程的目标函数，用于获取信号量、启动子进程并等待其完成。
    """
    with semaphore:  # with语句会自动处理acquire和release
        print(f"[启动器] 正在分配资源给第 {run_times} 次运行（范围{run_index * 10 + 1}-{run_index * 10 + 10}）...")

        try:
            platform_config = get_platform_command(WORKER_SCRIPT, run_index)

            command = platform_config.get("command")
            flags = platform_config.get("flags", 0)  # 默认为0，即无特殊标志

            # 在Windows上，creationflags=flags 会被使用
            # 在其他系统上，这个参数会被忽略
            if command is not None:
                process = subprocess.Popen(command, creationflags=flags)

                process.wait()

                print(f"[启动器] 第 {run_times} 次运行已完成，资源已释放。")

            else:
                raise RuntimeError("无法获取平台特定的命令配置。")

        except Exception as e:
            print(f"[启动器] 运行第 {run_times} 次时出错: {e}")


def main_launcher():
    """
    启动器的主函数。
    """
    # 创建一个信号量(Semaphore)，它的计数器初始值为并发数限制
    # 每当一个线程想运行时，必须先从信号量中'acquire'一个许可
    # 当运行结束后，线程必须'release'这个许可，让其他等待的线程可以运行
    semaphore = threading.Semaphore(MAX_CONCURRENT_PROCESSES)
    
    threads = []
    run_times = 0
    print(f"准备开始 {TOTAL_RUNS} 次运行，最大并发数: {MAX_CONCURRENT_PROCESSES}")
    
    for i in range(TOTAL_RUNS[0], TOTAL_RUNS[1]):
        # 为每一次运行创建一个管理线程
        # 这个线程的工作就是启动worker进程并等待它结束
        run_times += 1
        thread = threading.Thread(target=run_worker_in_new_terminal, args=(semaphore, i, run_times))
        threads.append(thread)
        thread.start()
        time.sleep(1) # 短暂间隔，避免瞬间启动大量线程

    # 等待所有管理线程执行完毕
    for thread in threads:
        thread.join()
        
    print("\n所有运行任务均已完成！")


if __name__ == "__main__":
    start_time = time.time()
    main_launcher()
    end_time = time.time()
    print(f"{cl.get_colour('YELLOW')}总耗时: {end_time - start_time:.3f}秒")
    print(f"图片保存路径: {CHECK_FOLDER}{cl.reset()}")