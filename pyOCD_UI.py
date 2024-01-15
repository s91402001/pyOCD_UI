import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import subprocess
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
import threading

class PyOCDGUI:
    def __init__(self, root):
        self.root = root
        root.title("PyOCD GUI")

        # 初始化固件文件路径为空
        self.firmware_path = None

        # 获取目标名称
        self.targets = self.get_pyocd_targets()

        # 创建带有搜索功能的下拉式菜单
        self.target_var = tk.StringVar()
        self.target_menu = ttk.Combobox(root, textvariable=self.target_var, values=self.targets)

        # 选择固件文件按钮
        self.select_file_button = tk.Button(root, text="Select Firmware File", command=self.select_firmware_file)

        # 烧录按钮
        self.program_button = tk.Button(root, text="Program Firmware", command=self.program_firmware)

        # 绑定输入事件来更新下拉列表
        self.target_menu.bind('<KeyRelease>', self.update_dropdown)

        # 连接按钮
        #self.connect_button = tk.Button(root, text="Connect to Target", command=self.connect_to_target)
        

        # 信息显示
        self.info_label = tk.Label(root, text="")
        
        
        self.target_menu.grid(column=1, row=0)
        #self.connect_button.grid(column=1, row=0)
        self.select_file_button.grid(column=1, row=1)
        self.program_button.grid(column=2, row=1)
        self.info_label.grid(column=1, row=2)

    # 其他方法...
    def get_pyocd_targets(self):
        try:
            # 运行pyocd命令获取目标列表
            result = subprocess.run(["pyocd", "list", "--targets"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Failed to execute pyocd. Make sure it is installed and added to PATH.")
            
            # 分析命令输出
            lines = result.stdout.splitlines()
            
            # 提取每行的第一个字段
            return [line.split()[0] for line in lines if line and not line.startswith("Available")]
        except Exception as e:
            return [f"Error: {str(e)}"]
    def update_dropdown(self, event):
        # 过滤出与输入匹配的选项
        value = event.widget.get().lower()
        filtered_data = [item for item in self.targets if value in item.lower()]
        event.widget.config(values=filtered_data if filtered_data else self.targets)
    def select_firmware_file(self):
        self.firmware_path = filedialog.askopenfilename(
            title="Select Firmware File",
            filetypes=(("Binary files", "*.bin"), ("All files", "*.*"))
        )
        if self.firmware_path:
            self.info_label.config(text=f"Selected File: {self.firmware_path}")
        else:
            self.info_label.config(text="No file selected.")

    def program_firmware(self):
        if not self.firmware_path:
            self.info_label.config(text="No firmware file selected.")
            return

        target_name = self.target_var.get()
        if not target_name:
            self.info_label.config(text="No target selected.")
            return

        self.info_label.config(text="Start Upload...")
        # 在新线程中启动烧录过程
        threading.Thread(target=self.perform_firmware_programming, args=(target_name,)).start()

    def perform_firmware_programming(self, target_name):
        try:
            with ConnectHelper.session_with_chosen_probe(target_override=target_name) as session:
                session.open()
                programmer = FileProgrammer(session)
                programmer.program(self.firmware_path)
                self.update_label(f"Successfully programmed {self.firmware_path} to {target_name}")
        except Exception as e:
            self.update_label(f"Programming error: {str(e)}")

    def update_label(self, text):
        # 在主线程中更新标签
        if self.info_label.winfo_exists():
            self.info_label.config(text=text)

    def connect_to_target(self):
        target_name = self.target_var.get()
        if target_name:
            self.info_label.config(text=f"Connecting to {target_name}...")
            try:
                # 连接到选中的目标
                with ConnectHelper.session_with_chosen_probe(target_override=target_name) as session:
                    session.open()
                    self.info_label.config(text=f"Connected to {target_name}")
            except Exception as e:  # 更一般的异常捕获
                self.info_label.config(text=f"Error: {str(e)}")
        else:
            self.info_label.config(text="Please select a target.")
# 其他方法...
if __name__ == "__main__":
    root = tk.Tk()
    gui = PyOCDGUI(root)
    root.mainloop()