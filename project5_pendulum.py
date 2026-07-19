# project5_pendulum.py
import tkinter as tk
import numpy as np
import time
from threading import Thread

class Pendulum:
    def __init__(self):
        self.theta = 0.1
        self.omega = 0
        self.length = 1.0
        self.g = 9.8
        self.dt = 0.01
        self.force = 0
        self.damping = 0.1
    
    def update(self, force):
        self.force = force
        alpha = -(self.g/self.length) * np.sin(self.theta) - self.damping * self.omega + force
        self.omega += alpha * self.dt
        self.theta += self.omega * self.dt
        return self.theta

class Controller:
    def __init__(self):
        self.Kp = 10.0
        self.Kd = 5.0
        self.setpoint = 0
    
    def control(self, theta, omega):
        error = self.setpoint - theta
        return self.Kp * error - self.Kd * omega

class PendulumGUI:
    def __init__(self):
        self.pendulum = Pendulum()
        self.controller = Controller()
        self.root = tk.Tk()
        self.root.title("Inverted Pendulum")
        self.root.geometry("600x700")
        self.root.configure(bg='#2c3e50')
        
        self.running = True
        self.auto_mode = True
        self.force = 0
        
        self._create_widgets()
        self.update()
        
        self.thread = Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _create_widgets(self):
        tk.Label(self.root, text="Inverted Pendulum Simulator", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=5)
        
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg='white')
        self.canvas.pack(pady=10)
        
        # Controls
        ctrl = tk.Frame(self.root, bg='#2c3e50')
        ctrl.pack(pady=10)
        
        self.auto_btn = tk.Button(ctrl, text="Auto Control", bg='#2ecc71', fg='white',
                                 command=self.toggle_mode, width=12)
        self.auto_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = tk.Button(ctrl, text="Pause", bg='#e67e22', fg='white',
                                  command=self.toggle_pause, width=12)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl, text="Reset", bg='#e74c3c', fg='white',
                 command=self.reset, width=12).pack(side=tk.LEFT, padx=5)
        
        # Manual control
        manual = tk.Frame(self.root, bg='#2c3e50')
        manual.pack(pady=5)
        
        tk.Label(manual, text="Force:", bg='#2c3e50', fg='white').pack(side=tk.LEFT)
        self.force_var = tk.StringVar(value="0")
        ttk.Spinbox(manual, from_=-10, to=10, textvariable=self.force_var, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(manual, text="Apply", bg='#3498db', fg='white',
                 command=self.apply_force).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status = tk.Label(self.root, text="", bg='#2c3e50', fg='white', font=('Consolas', 10))
        self.status.pack(pady=5)
    
    def _loop(self):
        while True:
            if self.running:
                if self.auto_mode:
                    force = self.controller.control(self.pendulum.theta, self.pendulum.omega)
                else:
                    force = self.force
                self.pendulum.update(force)
            time.sleep(self.pendulum.dt)
    
    def draw(self):
        self.canvas.delete("all")
        cx, cy = 200, 300
        length = 150
        
        # Cart
        x = cx + self.pendulum.theta * 50
        self.canvas.create_rectangle(x-20, cy-10, x+20, cy+10, fill='#3498db')
        
        # Pendulum
        end_x = cx + self.pendulum.theta * 50 + length * np.sin(self.pendulum.theta)
        end_y = cy - length * np.cos(self.pendulum.theta)
        self.canvas.create_line(cx + self.pendulum.theta * 50, cy, end_x, end_y, 
                               width=3, fill='#e74c3c')
        
        # Mass
        self.canvas.create_oval(end_x-10, end_y-10, end_x+10, end_y+10, fill='#e74c3c')
        
        # Info
        angle = np.degrees(self.pendulum.theta)
        self.canvas.create_text(cx, 30, text=f"Angle: {angle:.1f}°", font=('Arial', 12))
        
        # Ground
        self.canvas.create_line(50, cy+10, 350, cy+10, fill='black', width=2)
    
    def update_status(self):
        mode = "Auto" if self.auto_mode else "Manual"
        s = f"Mode: {mode}  |  Angle: {np.degrees(self.pendulum.theta):.1f}°  |  Force: {self.pendulum.force:.2f}"
        self.status.config(text=s)
    
    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        self.auto_btn.config(text="Auto Control" if self.auto_mode else "Manual",
                            bg='#2ecc71' if self.auto_mode else '#e67e22')
    
    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.config(text="Resume" if not self.running else "Pause",
                             bg='#27ae60' if not self.running else '#e67e22')
    
    def apply_force(self):
        try:
            self.force = float(self.force_var.get())
            self.auto_mode = False
            self.auto_btn.config(text="Manual", bg='#e67e22')
        except:
            pass
    
    def reset(self):
        self.pendulum.theta = 0.1
        self.pendulum.omega = 0
        self.running = True
        self.pause_btn.config(text="Pause", bg='#e67e22')
    
    def update(self):
        if self.running:
            self.draw()
            self.update_status()
        self.root.after(50, self.update)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    PendulumGUI().run()