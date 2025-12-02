#!/usr/bin/env python3
# 近似比例计算器.py

# ============================================================================
# 用户配置区（修改以下参数可自定义脚本行为）

# 【MAX_DENOMINATOR】搜索范围上限（分母最大值）
# 该参数决定算法在寻找近似比例时的搜索范围：
# - 数值越大：可能找到更精确的比例，但计算时间会增加；
# - 数值越小：计算更快，但可能错过更优解。
# 修改该数值，还可以让程序输出“比项更小”的结果，或者“误差更小”的结果。
# 注意：当输入数值极大或极小时，此限制可能导致触发"极限模式"：
# - 极限模式下，算法会将比例中较小的数值锁定为1，并计算另一个数值。
# 类型：整数，必须 ≥ 1,不建议超过十万或小于10。
MAX_DENOMINATOR = 64

# 【SINGLE_DIGIT_THRESHOLD】一位数比例误差阈值
# 当找到的一位数比例（如3:4、5:7等）的误差小于此值时，会优先显示。
# 控制"一位数比例优先"功能的触发条件：
# - 数值越大：越容易触发“一位数比例优先”功能，更可能看到简洁的比例；
# - 数值越小：更严格，只有误差极小时才优先显示一位数比例。
# - 设为0：可禁用此功能，完全按误差排序；
# - 设为1：几乎总是触发，可能显示误差较大的一位数比例。
# - 类型：小数，范围 0-1
SINGLE_DIGIT_THRESHOLD = 0.01

# ============================================================================

# ---------- 配置项防呆验证 ----------
# 该段代码在启动时自动检查用户配置，确保参数合法
# 若发现错误，将自动应用默认值并弹出非阻塞提示
_default_MAX_DENOMINATOR = 64
_default_THRESHOLD = 0.01
_config_warnings = []  # 收集所有配置错误信息

# 验证 MAX_DENOMINATOR
if not isinstance(MAX_DENOMINATOR, int):
    MAX_DENOMINATOR = _default_MAX_DENOMINATOR
    _config_warnings.append(f'检测到"MAX_DENOMINATOR"变量有误，已重置变量为{MAX_DENOMINATOR}。')
elif MAX_DENOMINATOR < 1:
    MAX_DENOMINATOR = _default_MAX_DENOMINATOR
    _config_warnings.append(f'检测到"MAX_DENOMINATOR"变量有误，已重置变量为{MAX_DENOMINATOR}。')

# 验证 SINGLE_DIGIT_THRESHOLD
try:
    _threshold_value = float(SINGLE_DIGIT_THRESHOLD)
    if not (0 <= _threshold_value <= 1):
        SINGLE_DIGIT_THRESHOLD = _default_THRESHOLD
        _config_warnings.append(f'检测到"SINGLE_DIGIT_THRESHOLD"变量有误，已重置变量为{SINGLE_DIGIT_THRESHOLD}。')
    else:
        SINGLE_DIGIT_THRESHOLD = _threshold_value
except (ValueError, TypeError):
    SINGLE_DIGIT_THRESHOLD = _default_THRESHOLD
    _config_warnings.append(f'检测到"SINGLE_DIGIT_THRESHOLD"变量有误，已重置变量为{SINGLE_DIGIT_THRESHOLD}。')

# ============================================================================

import sys
import math
import platform
import argparse

# ---------- 命令行模式检测 ----------
USE_CLI = False
if "--cli" in sys.argv:
    USE_CLI = True

# ---------- 1. Tk 检测 ----------
if not USE_CLI:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ModuleNotFoundError:
        sys_name = platform.system()
        
        # 系统专属提示信息
        print("\n" + "=" * 55)
        print("图形界面提示")
        print("=" * 55)
        
        if sys_name == "Windows":
            print("您的Python环境缺少Tkinter模块，无法启动图形界面。")
            print("\n修复方法：")
            print("  1. 重新运行Python安装程序")
            print("  2. 勾选 'tcl/tk' 或 '图形界面组件' 选项")
            print("  3. 完成安装后重新运行本脚本")
        elif sys_name == "Darwin":  # macOS
            print("您的Python环境缺少Tkinter模块，无法启动图形界面。")
            print("\n修复方法：")
            print("  在终端执行：brew install python-tk@3")
        elif sys_name == "Linux":
            print("您的Python环境缺少Tkinter模块，无法启动图形界面。")
            print("\n修复方法：")
            print("  Debian/Ubuntu系统：sudo apt install python3-tk")
            print("  RHEL/CentOS系统：sudo yum install python3-tkinter")
        else:
            print("您的系统未检测到Tkinter模块。")
            print("该脚本支持使用Tkinter生成图形界面。")
            print("请查阅您的系统文档安装相应的Python Tkinter包（如有）。")
        
        # 统一CLI介绍
        print("\n" + "-" * 55)
        print("已进入命令行模式")
        print("-" * 55)
        print("使用方法：")
        print("  • 输入两个数字，用空格或冒号分隔（如：16 9 或 16:9）")
        print("  • 输入 'q' 或 'quit' 退出程序")
        print("  • 下次可直接使用参数启动： --cli")
        
        if _config_warnings:
            print("\n配置修正提示：")
            for w in _config_warnings:
                print(f"  ⚠ {w}")
        
        print("-" * 55 + "\n")
        
        # 进入CLI模式
        USE_CLI = True

# ---------- 2. 核心算法 ----------
# ？？？？（ ？？？？？？？ ？？？？）
EE_msg_codes = [20320, 26159, 22312, 25214, 66, 85, 71, 21527, 65292, 20146, 29233, 30340, 65311]
EE_msg = ''.join(chr(c) for c in EE_msg_codes)

def format_error(err):
    """格式化误差显示（CLI和GUI共用）"""
    if err < 1e-16:
        return "=0"
    elif err < 1e-8:
        return "<0.00000001"
    else:
        return f"≈{err:.8f}"

def approximate_top5(a: int, b: int):
    """返回 (mode, top5_list)"""
    target = a / b
    candidates = []
    single_digit_candidates = []

    # 收集正常候选
    for den in range(1, MAX_DENOMINATOR + 1):
        num = round(target * den)
        if num == 0:
            continue
        if math.gcd(num, den) != 1:
            continue
            
        err = abs(num / den - target)
        candidates.append((num, den, err))
        
        # 筛选一位数比例
        if 1 <= num <= 9 and 1 <= den <= 9:
            single_digit_candidates.append((num, den, err))

    # ========== 极限模式：找不到任何候选时的处理 ==========
    if not candidates:
        # 比例<1：锁定分子为1，分母 = round(b/a)
        if a < b:
            extreme_den = max(1, round(b / a))
            extreme_err = abs(1/extreme_den - target)
            return "limit_small", [(1, extreme_den, extreme_err)]
        # 比例>1：锁定分母为1，分子 = round(a/b)
        else:
            extreme_num = max(1, round(a / b))
            extreme_err = abs(extreme_num/1 - target)
            return "limit_large", [(extreme_num, 1, extreme_err)]

    # 按误差排序
    candidates.sort(key=lambda x: x[2])
    
    # 如果没有一位数候选，直接返回前5个
    if not single_digit_candidates:
        return None, candidates[:5]
    
    # 找到误差最小的一位数比例
    single_digit_candidates.sort(key=lambda x: x[2])
    best_single_digit = single_digit_candidates[0]
    
    # 判断是否需要特殊处理：误差在阈值内且不是全局最优
    if best_single_digit[2] < SINGLE_DIGIT_THRESHOLD:
        # 检查它是否是全局最优（分子分母完全相同）
        is_global_best = False
        if candidates and best_single_digit[0] == candidates[0][0] and best_single_digit[1] == candidates[0][1]:
            is_global_best = True
        
        if not is_global_best:
            return best_single_digit, candidates[:5]
    
    return None, candidates[:5]

# ---------- 3. 命令行模式 ----------
def run_cli_mode():
    """命令行交互模式"""
    print("\n" + "=" * 50)
    print("近似比例计算器 - 命令行模式")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n【输入】比例（q退出）> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['q', 'quit']:
                print("\n【退出】感谢使用，再见！")
                break
            
            # 解析输入（支持空格和冒号分隔）
            if ':' in user_input:
                parts = user_input.split(':')
            else:
                parts = user_input.split()
                
            if len(parts) != 2:
                print(" 格式错误，请输入两个正整数")
                continue
                
            a_str, b_str = parts
            
            if not a_str.isdigit() or not b_str.isdigit():
                print(" 请输入有效的正整数")
                continue
                
            a, b = int(a_str), int(b_str)
            
            if a <= 0 or b <= 0:
                print(" 请输入正整数（大于0）")
                continue
            
            # 调用核心算法
            mode, top5 = approximate_top5(a, b)
            
            # ？？？？？？？？
            if (a == 1 and b > MAX_DENOMINATOR) or (b == 1 and a > MAX_DENOMINATOR):
                if a == 1:
                    print(f"\n【结果】近似比例1【1:{b}】")
                else:
                    print(f"\n【结果】近似比例1【{a}:1】")
                print("       误差=0")
                print()
                print(f" {EE_msg}")  # ？？？？
                continue
            
            # 正常结果输出
            print("\n" + "-" * 45)
            
            # 处理极限模式
            if mode == "limit_small" or mode == "limit_large":
                num, den, err = top5[0]
                err_str = format_error(err)
                print(f" 特殊比例【{num}:{den}】")
                print(f"     误差{err_str}")
                print()
                print("   警告：超出常规搜索范围。")
                print("   因此，程序将较小值设为1，")
                print("   据此计算最优的近似比例。")
                print()
                print("   注意：可能不是最近似的值。")
            elif mode:  # 一位数比例优先
                num, den, err = mode
                err_str = format_error(err)
                print(f" 一位数比例【{num}:{den}】\n     误差{err_str}")
                print("-" * 45)
            
            # 显示前5个比例（极限模式下已处理）
            if mode not in ["limit_small", "limit_large"]:
                for i, (num, den, err) in enumerate(top5[:5], 1):
                    err_str = format_error(err)
                    print(f" 近似比例{i}【{num}:{den}】\n     误差{err_str}")
            
            print("-" * 45)
            
        except KeyboardInterrupt:
            print("\n\n【退出】检测到中断，程序退出。")
            sys.exit(0)
        except Exception as e:
            print(f"\n 发生错误: {str(e)}")

# ---------- 4. GUI 逻辑 ----------
if not USE_CLI:
    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("近似比例计算器")
            self.resizable(True, True)
            self.attributes("-topmost", True)

            # 输入区（使用grid布局确保两列等比例缩放）
            frm_in = ttk.Frame(self)
            frm_in.pack(pady=8, fill="x", padx=8)
            frm_in.grid_columnconfigure(0, weight=1)  # 第一列可伸缩
            frm_in.grid_columnconfigure(2, weight=1)  # 第二列可伸缩
            
            self.var_a = tk.StringVar()
            self.var_b = tk.StringVar()
            
            # 验证函数：只允许输入数字
            vcmd = (self.register(self.validate_input), '%P')
            
            # 文本框1
            self.entry_a = ttk.Entry(frm_in, textvariable=self.var_a, width=8, 
                                     validate='key', validatecommand=vcmd)
            self.entry_a.grid(row=0, column=0, sticky="ew", padx=2)
            
            # 冒号始终居中（固定列，不伸缩）
            ttk.Label(frm_in, text="：", width=2, anchor="center").grid(row=0, column=1, padx=2)
            
            # 文本框2
            self.entry_b = ttk.Entry(frm_in, textvariable=self.var_b, width=8,
                                     validate='key', validatecommand=vcmd)
            self.entry_b.grid(row=0, column=2, sticky="ew", padx=2)

            # 按钮（整行填充）
            ttk.Button(self, text="运算", command=self.calc).pack(fill="x", padx=8, pady=8)

            # 文本展示区
            self.text = tk.Text(self, width=27, height=12, wrap="word")
            self.text.pack(fill="both", expand=True, padx=8, pady=8)

            # 绑定Enter键
            self.bind_all('<Return>', self.on_enter)

            # Windows下尝试最小化控制台
            self.minimize_console()

            # 显示非阻塞配置警告
            if _config_warnings:
                self.show_nonblocking_warning()

        def validate_input(self, value):
            """只允许输入空或数字"""
            if value == "" or value.isdigit():
                return True
            return False

        def on_enter(self, event=None):
            """Enter键智能处理"""
            a = self.var_a.get().strip()
            b = self.var_b.get().strip()
            
            if not a and not b:
                self.entry_a.focus()
            elif not a:
                self.entry_a.focus()
            elif not b:
                self.entry_b.focus()
            else:
                self.calc()

        def show_nonblocking_warning(self):
            """显示非阻塞配置警告弹窗，包含三个趣味关闭按钮"""
            warn_window = tk.Toplevel(self)
            warn_window.title("配置项自动修正")
            warn_window.geometry("420x220")
            warn_window.resizable(False, False)
            
            # 设置为非模态（不阻塞主窗口）
            warn_window.transient(self)  # 设为临时窗口
            
            # 添加消息
            msg_frame = ttk.Frame(warn_window, padding=15)
            msg_frame.pack(fill="both", expand=True)
            
            ttk.Label(msg_frame, text="检测到以下配置问题，已自动修正：", 
                     font=("", 10, "bold")).pack(anchor="w", pady=(0, 10))
            
            # 显示所有警告信息
            for warning in _config_warnings:
                ttk.Label(msg_frame, text=f"• {warning}", wraplength=380).pack(anchor="w", pady=2)
            
            # 添加三个趣味关闭按钮（左中右对齐）
            btn_frame = ttk.Frame(warn_window)
            btn_frame.pack(pady=15, padx=15, fill="x")
            
            ttk.Button(btn_frame, text="啊？", command=warn_window.destroy).pack(side="left")
            ttk.Button(btn_frame, text="啊？？", command=warn_window.destroy).pack(side="left", expand=True)
            ttk.Button(btn_frame, text="啊？？？", command=warn_window.destroy).pack(side="right")

        def calc(self):
            try:
                a_str = self.var_a.get().strip()
                b_str = self.var_b.get().strip()
                
                # 检查是否为空
                if not a_str or not b_str:
                    self.text.delete("1.0", "end")
                    self.text.insert("end", "请输入两个正整数")
                    return
                
                a = int(a_str)
                b = int(b_str)
                
                # 检查是否为正整数
                if a <= 0 or b <= 0:
                    self.text.delete("1.0", "end")
                    self.text.insert("end", "请输入正整数（大于0）")
                    return
                    
                # ========== ？？？？（？？？？？？？？？？？） ==========
                # ？？？？：？？？？？，？？？？？ > ？？？？？？？？？？？？？？？？？？？
                mode, top5 = approximate_top5(a, b)
                if (a == 1 and b > MAX_DENOMINATOR) or (b == 1 and a > MAX_DENOMINATOR):
                    lines = []
                    if a == 1:
                        lines.append(f"近似比例1【1:{b}】")
                    else:
                        lines.append(f"近似比例1【{a}:1】")
                    lines.append("     误差=0")
                    lines.append("")
                    lines.append(EE_msg)
                    self.text.delete("1.0", "end")
                    self.text.insert("end", "\n".join(lines))
                    return
                    
            except ValueError:
                self.text.delete("1.0", "end")
                self.text.insert("end", "请输入有效的正整数")
                return

            lines = []
            
            # 处理极限模式
            if mode == "limit_small":
                num, den, err = top5[0]
                err_str = format_error(err)
                lines.append(f"特殊比例【{num}:{den}】")
                lines.append(f"     误差{err_str}")
                lines.append("")
                lines.append("⚠警告：超出常规搜索范围。")
                lines.append("因此，程序将较小值设为1，")
                lines.append("据此计算最优的近似比例。")
                lines.append("")
                lines.append("注意：可能不是最近似的值。")
            elif mode == "limit_large":
                num, den, err = top5[0]
                err_str = format_error(err)
                lines.append(f"特殊比例【{num}:{den}】")
                lines.append(f"     误差{err_str}")
                lines.append("")
                lines.append("⚠警告：超出常规搜索范围。")
                lines.append("因此，程序将较小值设为1，")
                lines.append("据此计算最优的近似比例。")
                lines.append("")
                lines.append("注意：可能不是最近似的值。")
            elif mode:  # 一位数比例优先
                num, den, err = mode
                err_str = format_error(err)
                lines.append(f"一位数比例【{num}:{den}】\n     误差{err_str}")
                lines.append("——————————")
            
            # 显示前5个比例（极限模式下已处理，不再重复）
            if mode not in ["limit_small", "limit_large"]:
                for i, (num, den, err) in enumerate(top5[:5], 1):
                    err_str = format_error(err)
                    lines.append(f"近似比例{i}【{num}:{den}】\n     误差{err_str}")
            
            self.text.delete("1.0", "end")
            self.text.insert("end", "\n".join(lines))

        def minimize_console(self):
            """Windows下自动最小化CMD窗口"""
            if platform.system() == "Windows":
                try:
                    import ctypes
                    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                    if hwnd:
                        ctypes.windll.user32.ShowWindow(hwnd, 6)  # 6 = SW_MINIMIZE
                except Exception:
                    pass

# ---------- 5. 入口 ----------
if __name__ == "__main__":
    if USE_CLI:
        run_cli_mode()
    else:
        App().mainloop()