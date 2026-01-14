import csv
import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import json
import io
import pygame
import os

# ---- VOICEVOX 設定 ----
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 3

def speak_zundamon(text):
    try:
        res1 = requests.post(f"{VOICEVOX_URL}/audio_query", params={"text": text, "speaker": SPEAKER_ID})
        query = res1.json()
        res2 = requests.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": SPEAKER_ID}, data=json.dumps(query))
        audio_data = io.BytesIO(res2.content)
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"VOICEVOXエラー: {e}")

pygame.mixer.init()

class ZundamonTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("ずんだもん作業タイマー")
        self.root.geometry("450x700")
        self.tasks = []
        self.current_csv = ""
        self.is_voice_enabled = tk.BooleanVar(value=True)
        self.after_id = None
        self.show_mode_selection()

    def stop_timer(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def show_mode_selection(self):
        self.stop_timer()
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="モードを選択するのだ", font=("MS Gothic", 16, "bold"), pady=20).pack()
        csv_files = sorted([f for f in os.listdir('.') if f.endswith('.csv')])
        for file in csv_files:
            btn = tk.Button(self.root, text=file.replace(".csv", ""), font=("MS Gothic", 12),
                            width=20, pady=10, command=lambda f=file: self.start_timer(f))
            btn.pack(pady=5)
        tk.Button(self.root, text="＋ 新規モード作成", command=self.create_new_mode, bg="#e7f3ff").pack(pady=20)

    def create_new_mode(self):
        name = simpledialog.askstring("新規作成", "モード名を入力してね")
        if name:
            filename = f"{name}.csv"
            if not os.path.exists(filename):
                with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["time", "text", "voice"])
                    writer.writerow(["21:00", "夜勤開始", "夜勤開始なのだ！頑張るのだ！"])
            self.show_mode_selection()

    def start_timer(self, filename):
        self.current_csv = filename
        self.load_tasks()
        self.setup_main_ui()
        self.update()

    def load_tasks(self):
        self.tasks = []
        try:
            with open(self.current_csv, newline="", encoding="utf-8-sig") as f:
                # DictReaderではなく、あえて普通のreaderで読み込むのだ
                reader = csv.reader(f)
                header = next(reader) # 1行目（ヘッダー）を飛ばす
                
                now_dt = datetime.datetime.now()
                last_dt = None
                
                for row in reader:
                    if len(row) < 2: continue # 空行対策
                    
                    time_str = row[0] # 1列目：時間
                    display_text = row[1] # 2列目：タスク名
                    # 3列目があればそれを、なければタスク名をセリフにするのだ
                    voice_text = row[2] if len(row) >= 3 and row[2] else f"{display_text}の時間なのだ"
                    
                    t_parts = list(map(int, time_str.split(':')))
                    dt = now_dt.replace(hour=t_parts[0], minute=t_parts[1], second=0, microsecond=0)
                    
                    if last_dt and dt < last_dt:
                        dt += datetime.timedelta(days=1)
                    last_dt = dt
                    
                    self.tasks.append({
                        "time": time_str, "text": display_text, "voice": voice_text,
                        "dt": dt, "done": tk.BooleanVar(value=False),
                        "alerted": dt <= now_dt, "checkbox": None 
                    })
        except Exception as e:
            messagebox.showerror("エラー", f"CSVの形式がおかしい可能性があるのだ: {e}")
            self.show_mode_selection()

    def setup_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.clock_label = tk.Label(self.root, text="", font=("MS Gothic", 24, "bold"), fg="#333")
        self.clock_label.pack(pady=10)
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=20)
        tk.Button(top_frame, text="← 戻る", command=self.show_mode_selection).pack(side="left")
        tk.Checkbutton(top_frame, text="ずんだもんの声 ON", variable=self.is_voice_enabled, fg="#28a745").pack(side="right")
        self.next_label = tk.Label(self.root, text="", font=("MS Gothic", 11, "bold"))
        self.next_label.pack(pady=5)
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(pady=5, padx=20, fill="both", expand=True)
        self.line_height = 40
        self.canvas_width = 25
        self.canvas_height = max(40, len(self.tasks) * self.line_height)
        self.bar_canvas = tk.Canvas(self.main_frame, width=self.canvas_width, height=self.canvas_height, bg="#f0f0f0")
        self.bar_canvas.pack(side="left", anchor="n")
        self.bar = self.bar_canvas.create_rectangle(0, 0, self.canvas_width, 0, fill="#28a745", outline="")
        self.task_frame = tk.Frame(self.main_frame)
        self.task_frame.pack(side="left", fill="both", expand=True)
        for t in self.tasks:
            row_f = tk.Frame(self.task_frame, height=self.line_height)
            row_f.pack(fill="x")
            row_f.pack_propagate(False)
            cb = tk.Checkbutton(row_f, text=f'{t["time"]} {t["text"]}', variable=t["done"], font=("MS Gothic", 11),
                                command=lambda item=t: self.on_check(item))
            cb.pack(side="left")
            t["checkbox"] = cb
            if t["alerted"]: cb.config(fg="gray")

    def on_check(self, task):
        task["checkbox"].config(fg="gray" if task["done"].get() else "black")

    def update(self):
        if not hasattr(self, 'clock_label') or not self.clock_label.winfo_exists(): return
        now = datetime.datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M:%S"))
        for t in self.tasks:
            if not t["done"].get() and not t["alerted"] and now >= t["dt"]:
                if self.is_voice_enabled.get():
                    speak_zundamon(t["voice"]) # ここで確実に row[2] の内容を喋るのだ！
                t["alerted"] = True
                t["checkbox"].config(fg="gray")
        upcoming = [t for t in self.tasks if not t["done"].get() and t["dt"] > now]
        if upcoming:
            diff = upcoming[0]["dt"] - now
            m, s = divmod(int(diff.total_seconds()), 60)
            self.next_label.config(text=f"次：{upcoming[0]['text']} まで {m}分 {s}秒", fg="#0056b3")
        else:
            self.next_label.config(text="全タスク完了なのだ！", fg="#d9534f")
        if self.tasks:
            total_h = self.canvas_height
            if now <= self.tasks[0]["dt"]: cur_h = self.line_height / 2
            elif now >= self.tasks[-1]["dt"]: cur_h = total_h
            else:
                for i in range(len(self.tasks)-1):
                    s_dt, e_dt = self.tasks[i]["dt"], self.tasks[i+1]["dt"]
                    if s_dt <= now < e_dt:
                        ratio = (now - s_dt).total_seconds() / (e_dt - s_dt).total_seconds()
                        cur_h = (i * self.line_height) + (self.line_height / 2) + (self.line_height * ratio)
                        break
                else: cur_h = total_h
            self.bar_canvas.coords(self.bar, 0, 0, self.canvas_width, cur_h)
        self.after_id = self.root.after(1000, self.update)

if __name__ == "__main__":
    root = tk.Tk()
    app = ZundamonTimer(root)
    root.mainloop()