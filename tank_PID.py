import tkinter as tk
from tkinter import ttk, messagebox
import time
from threading import Thread


class Tank:
    def __init__(self, max_level=300):
        self.max_level = max_level
        self.level = 120
        self.inflow = 0
        self.outflow = 10
        self.dt = 0.1

    def update(self, inflow):
        self.inflow = inflow
        self.level += (self.inflow - self.outflow) * self.dt
        self.level = max(0, min(self.max_level, self.level))
        return self.level


class Controller:
    def __init__(self, setpoint=150):
        self.setpoint = setpoint
        self.type = 'onoff'
        self.Kp = 2.0
        self.Ki = 0.3
        self.Kd = 0.1
        self.integral = 0
        self.prev_error = 0

    def control(self, level, dt):
        error = self.setpoint - level

        if self.type == 'onoff':
            if error > 5:
                return 18
            elif error < -5:
                return 0
            return 8 if error > 0 else 0

        else:
            self.integral += error * dt
            derivative = (error - self.prev_error) / dt if dt > 0 else 0
            output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
            self.prev_error = error
            return max(0, min(20, output))


class TankGUI:
    def __init__(self):
        self.max_level = 300
        self.tank = Tank(self.max_level)
        self.controller = Controller(150)
        self.root = tk.Tk()
        self.root.title(f"Water Tank - {self.max_level}L")
        self.root.geometry("700x750")
        self.root.configure(bg='#2c3e50')

        self.time = 0
        self.history = []
        self.running = True
        self.dt = 0.1

        self._create_widgets()
        self.update()
        self.thread = Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def _create_widgets(self):
        tk.Label(self.root, text=f"Water Tank Level Control - {self.max_level}L",
                 font=('Arial', 14, 'bold'), bg='#2c3e50', fg='white').pack(pady=5)

        main = tk.Frame(self.root, bg='#2c3e50')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg='#2c3e50')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, width=250, height=350, bg='white')
        self.canvas.pack(pady=5)

        self.graph = tk.Canvas(left, width=380, height=220, bg='white')
        self.graph.pack(pady=5)
        self.graph.create_text(190, 12, text="Level History", font=('Arial', 10, 'bold'))

        right = tk.Frame(main, bg='#2c3e50', width=280)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        info = tk.LabelFrame(right, text="Tank Info", font=('Arial', 10, 'bold'),
                             bg='#2c3e50', fg='white', padx=10, pady=10)
        info.pack(fill=tk.X, pady=5)
        tk.Label(info, text=f"Max Level: {self.max_level}L", bg='#2c3e50', fg='white').pack(anchor=tk.W)
        tk.Label(info, text="Outflow: 10 L/s", bg='#2c3e50', fg='white').pack(anchor=tk.W)

        ctrl_frame = tk.LabelFrame(right, text="Controller", font=('Arial', 10, 'bold'),
                                   bg='#2c3e50', fg='white', padx=10, pady=10)
        ctrl_frame.pack(fill=tk.X, pady=5)

        tk.Label(ctrl_frame, text="Type:", bg='#2c3e50', fg='white').pack()
        self.ctrl_type = tk.StringVar(value="onoff")
        ttk.Combobox(ctrl_frame, textvariable=self.ctrl_type,
                     values=['onoff', 'pid'], width=12).pack(pady=5)
        tk.Button(ctrl_frame, text="Apply", bg='#3498db', fg='white',
                  command=self.apply_controller).pack(pady=5)

        tk.Label(ctrl_frame, text="Setpoint:", bg='#2c3e50', fg='white').pack()
        self.setpoint_var = tk.StringVar(value="150")
        ttk.Spinbox(ctrl_frame, from_=10, to=290,
                    textvariable=self.setpoint_var, width=12).pack(pady=5)
        tk.Button(ctrl_frame, text="Set", bg='#3498db', fg='white',
                  command=self.set_setpoint).pack(pady=5)

        inflow_frame = tk.LabelFrame(right, text="Manual Control", font=('Arial', 10, 'bold'),
                                     bg='#2c3e50', fg='white', padx=10, pady=10)
        inflow_frame.pack(fill=tk.X, pady=5)

        tk.Label(inflow_frame, text="Inflow:", bg='#2c3e50', fg='white').pack()
        self.inflow_var = tk.StringVar(value="0")
        ttk.Spinbox(inflow_frame, from_=0, to=20, textvariable=self.inflow_var, width=12).pack(pady=5)
        tk.Button(inflow_frame, text="Apply", bg='#2ecc71', fg='white',
                  command=self.set_inflow).pack(pady=5)

        self.auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(right, text="Auto Control", variable=self.auto_var,
                       bg='#2c3e50', fg='white', selectcolor='#2c3e50').pack(pady=5)

        btn_frame = tk.Frame(right, bg='#2c3e50')
        btn_frame.pack(pady=10)
        self.pause_btn = tk.Button(btn_frame, text="Pause", bg='#e67e22', fg='white',
                                   command=self.toggle, width=8)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", bg='#e74c3c', fg='white',
                  command=self.reset, width=8).pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(right, text="", bg='#2c3e50', fg='white', font=('Consolas', 10))
        self.status.pack(pady=5)

    def _loop(self):
        while True:
            if self.running:
                if self.auto_var.get():
                    inflow = self.controller.control(self.tank.level, self.dt)
                else:
                    try:
                        inflow = float(self.inflow_var.get())
                    except:
                        inflow = 0

                self.tank.update(inflow)
                self.time += self.dt
                self.history.append(self.tank.level)
                if len(self.history) > 150:
                    self.history.pop(0)
            time.sleep(self.dt)

    def draw_tank(self):
        self.canvas.delete("all")
        x, y = 75, 30
        tank_w, tank_h = 100, 280

        self.canvas.create_rectangle(x, y, x + tank_w, y + tank_h, outline='black', width=2)

        level_ratio = self.tank.level / self.tank.max_level
        water_h = level_ratio * tank_h
        water_y = y + tank_h - water_h
        self.canvas.create_rectangle(x + 2, water_y, x + tank_w - 2, y + tank_h - 2, fill='#3498db')

        self.canvas.create_text(x + tank_w / 2, y + tank_h + 20,
                                text=f"Level: {self.tank.level:.1f}L", font=('Arial', 10, 'bold'))
        self.canvas.create_text(x + tank_w / 2, y + tank_h + 40,
                                text=f"Inflow: {self.tank.inflow:.1f}", font=('Arial', 9))
        self.canvas.create_text(x + tank_w / 2, y + tank_h + 55,
                                text=f"Outflow: {self.tank.outflow:.1f}", font=('Arial', 9))

        for i in range(0, self.max_level + 1, 50):
            ly = y + tank_h - (i / self.max_level * tank_h)
            if ly > y and ly < y + tank_h:
                self.canvas.create_line(x - 5, ly, x, ly, fill='gray')
                self.canvas.create_text(x - 15, ly, text=str(i), font=('Arial', 6))

        self.canvas.create_text(x - 15, y, text=str(self.max_level), font=('Arial', 6))

        sp_ratio = self.controller.setpoint / self.tank.max_level
        sp_y = y + tank_h - (sp_ratio * tank_h)
        self.canvas.create_line(x - 10, sp_y, x + tank_w + 10, sp_y, fill='red', dash=(5, 5), width=2)
        self.canvas.create_text(x + tank_w + 15, sp_y, text="SP", fill='red', font=('Arial', 8, 'bold'))

    def draw_graph(self):
        self.graph.delete("all")
        self.graph.create_text(190, 12, text="Level History", font=('Arial', 10, 'bold'))

        if len(self.history) < 2:
            return

        w, h = 380, 220
        margin = 45
        graph_w = w - 2 * margin
        graph_h = h - 2 * margin - 10

        self.graph.create_line(margin, h - margin, w - margin, h - margin, fill='black')
        self.graph.create_line(margin, h - margin, margin, 15, fill='black')

        for i in range(0, self.max_level + 1, 50):
            y = h - margin - (i / self.max_level * graph_h)
            if y > 15 and y < h - margin:
                self.graph.create_line(margin - 5, y, margin, y, fill='gray')
                self.graph.create_text(margin - 10, y, text=str(i), font=('Arial', 6))

        points = []
        for i, val in enumerate(self.history):
            x = margin + (i / len(self.history)) * graph_w
            y = h - margin - (val / self.max_level) * graph_h
            points.append((x, y))

        for i in range(len(points) - 1):
            self.graph.create_line(points[i][0], points[i][1],
                                   points[i + 1][0], points[i + 1][1],
                                   fill='blue', width=2)

        sp_ratio = self.controller.setpoint / self.tank.max_level
        sp_y = h - margin - (sp_ratio * graph_h)
        self.graph.create_line(margin, sp_y, w - margin, sp_y, fill='red', dash=(5, 5), width=2)
        self.graph.create_text(w - margin - 5, sp_y - 5, text="SP", fill='red', font=('Arial', 8))

        self.graph.create_text(margin, h - 5, text="Time", font=('Arial', 8))
        self.graph.create_text(12, 15, text="Level", font=('Arial', 8))

    def update_status(self):
        ctrl = self.controller.type.upper()
        s = f"Ctrl: {ctrl}  |  Level: {self.tank.level:.1f}/{self.max_level}  |  Inflow: {self.tank.inflow:.1f}"
        self.status.config(text=s)

    def apply_controller(self):
        self.controller.type = self.ctrl_type.get()
        self.controller.integral = 0
        self.controller.prev_error = 0

    def set_setpoint(self):
        try:
            sp = float(self.setpoint_var.get())
            if 10 <= sp <= 290:
                self.controller.setpoint = sp
                messagebox.showinfo("OK", f"Setpoint set to {sp}")
            else:
                messagebox.showwarning("Error", "Setpoint must be 10-290")
        except:
            messagebox.showwarning("Error", "Invalid input!")

    def set_inflow(self):
        try:
            inflow = float(self.inflow_var.get())
            if 0 <= inflow <= 20:
                self.auto_var.set(False)
                messagebox.showinfo("OK", f"Manual inflow set to {inflow}")
            else:
                messagebox.showwarning("Error", "Inflow must be 0-20")
        except:
            messagebox.showwarning("Error", "Invalid input!")

    def toggle(self):
        self.running = not self.running
        self.pause_btn.config(text="Resume" if not self.running else "Pause",
                              bg='#27ae60' if not self.running else '#e67e22')

    def reset(self):
        if messagebox.askyesno("Confirm", "Reset?"):
            self.tank = Tank(self.max_level)
            self.controller = Controller(150)
            self.time = 0
            self.history = []
            self.running = True
            self.pause_btn.config(text="Pause", bg='#e67e22')

    def update(self):
        if self.running:
            self.draw_tank()
            self.draw_graph()
            self.update_status()
        self.root.after(200, self.update)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    TankGUI().run()