import subprocess
import threading
import sys
import time
from typing import Any, Optional
import datetime
import color
import os
import shutil
import main_likes
import yaml
import argparse

parser = argparse.ArgumentParser(description='Lofter爬虫启动器')
parser.add_argument('--refresh', default=0)
parser.add_argument('--proxies',default=0)

args = parser.parse_args()
refresh = bool(int(args.refresh))  # 是否刷新喜欢总数
proxies_or_not = bool(int(args.proxies))  # 是否使用代理

def load_config(target:str) -> Any:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        try:
            result = config[target]
        except KeyError:
            return None
    return result


def path_check(path: str) -> Optional[str]:
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        new_path = f'{path}/{main_likes.get_time().replace(":","-").replace(" ","_").split(".")[0]}'
        os.makedirs(new_path)

        return new_path
    except TypeError:
        raise RuntimeError('路径设置错误，请检查config.yaml.')

cl=color.Color()

cert = load_config('cert')
start_position = load_config('start')
end_position = load_config('end')
blogname = load_config('blogname')

def get_range(start, end):
    if not load_config('amount'):  # 初始化：喜欢总数
        favorites_amount = main_likes.get_favorites_amount(main_likes.get_list(0, blogname=blogname, cert=cert))  # 若需要代理，在这里调整proxies
        yaml_data = {"amount": favorites_amount,
                     'time': time.time()}
        with open('config.yaml', 'a', encoding='utf-8') as f:
            f.write('\n')
            yaml.dump(data=yaml_data, stream=f, allow_unicode=True)
    else:
        current_time = time.time()
        if  current_time - load_config('time') >= 43200 or refresh:
            favorites_amount = main_likes.get_favorites_amount(main_likes.get_list(0, blogname=blogname, cert=cert))  # 若需要代理，在这里调整proxies
            with open('config.yaml', 'r', encoding='utf-8') as f:
                _data = yaml.load(f, Loader=yaml.FullLoader)
                _data['amount'] = favorites_amount
                _data['time'] = time.time()
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(data=_data, stream=f, allow_unicode=True)
        else:
            favorites_amount = load_config('amount')
    if end is None:
        end = favorites_amount // 18

    elif favorites_amount // 18 < end:
        end = favorites_amount // 18
        print(f"{cl.get_colour("YELLOW")}结束位置超过喜欢列表长度，已自动调整为最大值。{cl.reset()}")

    if start is None:
        start = 0
        print(f"{cl.get_colour("YELLOW")}起始位置未填，已自动调整为0。{cl.reset()}")

    return [start, end]


# --- 配置区 ---
# 1. 要运行的工作脚本文件名
WORKER_SCRIPT = "main_likes.py"

# 2. 限制同时运行的最大进程数
MAX_CONCURRENT_PROCESSES = 3

# 3. 你想要运行的总次数
TOTAL_RUNS : list = get_range(start_position, end_position)

# 4. 设置路径
CHECK_FOLDER = path_check(load_config('path'))

# --- 配置区结束 ---

def get_platform_command(script_name, run_index):
    """
    根据不同的操作系统生成用于在新终端中运行脚本的命令。
    """
    # 将运行序号作为命令行参数传递给 worker.py
    python_command = f'python {script_name} -n {run_index} --path {CHECK_FOLDER} --proxies {1 if proxies_or_not else 0}'  # 代理开关

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
        # gnome-terminal:
        return ["gnome-terminal", "--", "bash", "-c", f"{python_command}; exec bash"]
        # 如果想让窗口执行完后自动关闭，使用下面的命令
        # return ["gnome-terminal", "--", "bash", "-c", f"{python_command}; exit"]

    else:
        raise NotImplementedError(f"不支持的操作系统: {sys.platform}")


def run_worker_in_new_terminal(semaphore, run_index, run_times: int):
    """
    一个线程的目标函数，用于获取信号量、启动子进程并等待其完成。
    """
    with semaphore:  # with语句会自动处理acquire和release
        print(f"[启动器] 正在分配资源给第 {run_times} 次运行（范围{run_index * 18 + 1}-{run_index * 18 + 18}）...")

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