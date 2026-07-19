import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from threading import Thread
from enum import Enum
from collections import deque

class State(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2

class Intersection:
    def __init__(self):
        self.lanes = {d: deque() for d in ['N','S','E','W']}
        self.lights = {d: State.RED for d in ['N','S','E','W']}
        self.active = 'N'
        self.lights['N'] = State.GREEN
        self.timer = 0
        self.car_id = 0
        self.passed = 0
        self.total_wait = 0
        self.time = 0
        
    def add_car(self, d):
        if len(self.lanes[d]) < 10:
            self.lanes[d].append([self.car_id, self.time, 0])
            self.car_id += 1
            return True
        return False
    
    def update(self):
        self.time += 0.1
        self.timer += 0.1
        
        if self.timer >= 5:
            self.timer = 0
            if self.lights[self.active] == State.GREEN:
                self.lights[self.active] = State.YELLOW
            elif self.lights[self.active] == State.YELLOW:
                self.lights[self.active] = State.RED
                dirs = ['N','E','S','W']
                idx = dirs.index(self.active)
                for i in range(1,5):
                    nxt = dirs[(idx+i)%4]
                    if self.lanes[nxt]:
                        self.active = nxt
                        self.lights[nxt] = State.GREEN
                        break
                else:
                    self.active = dirs[(idx+1)%4]
                    self.lights[self.active] = State.GREEN
        
        if self.lights[self.active] == State.GREEN and self.lanes[self.active]:
            car = self.lanes[self.active].popleft()
            car[2] = self.time - car[1]
            self.total_wait += car[2]
            self.passed += 1

class TrafficGUI:
    def __init__(self):
        self.inter = Intersection()
        self.root = tk.Tk()
        self.root.title("Traffic Light")
        self.root.geometry("550x600")
        self.root.configure(bg='#2c3e50')
        
        tk.Label(self.root, text="Traffic Light Simulator", font=('Arial',14,'bold'),
                bg='#2c3e50', fg='white').pack(pady=5)
        
        self.canvas = tk.Canvas(self.root, width=450, height=350, bg='#34495e')
        self.canvas.pack(pady=10)
        
        f = tk.Frame(self.root, bg='#2c3e50')
        f.pack(pady=5)
        
        tk.Label(f, text="Dir:", bg='#2c3e50', fg='white').pack(side=tk.LEFT)
        self.dir = tk.StringVar(value="N")
        ttk.Combobox(f, textvariable=self.dir, values=['N','S','E','W'], width=5).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="Add", bg='#3498db', fg='white', command=self.add_car).pack(side=tk.LEFT, padx=5)
        self.pause_btn = tk.Button(f, text="Pause", bg='#e67e22', fg='white', command=self.toggle, width=6)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="Reset", bg='#e74c3c', fg='white', command=self.reset, width=6).pack(side=tk.LEFT, padx=5)
        
        self.auto = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Auto Add", variable=self.auto, bg='#2c3e50', fg='white',
                      selectcolor='#2c3e50').pack()
        
        self.status = tk.Label(self.root, text="", bg='#2c3e50', fg='white', font=('Consolas',10))
        self.status.pack(pady=5)
        
        self.running = True
        self.update()
        self.thread = Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _loop(self):
        while True:
            if self.running:
                if self.auto.get() and random.random() < 0.06:
                    self.inter.add_car(random.choice(['N','S','E','W']))
                self.inter.update()
            time.sleep(0.1)
    
    def draw(self):
        self.canvas.delete("all")
        cx, cy = 225, 175
        w = 70
        
        self.canvas.create_rectangle(cx-w/2,0,cx+w/2,350,fill='#7f8c8d')
        self.canvas.create_rectangle(0,cy-w/2,450,cy+w/2,fill='#7f8c8d')
        self.canvas.create_rectangle(cx-w/2,cy-w/2,cx+w/2,cy+w/2,fill='#2c3e50')
        
        pos = {'N':(cx,cy-w/2-25), 'S':(cx,cy+w/2+25), 
               'E':(cx+w/2+25,cy), 'W':(cx-w/2-25,cy)}
        colors = {'N':(0,-1), 'S':(0,1), 'E':(1,0), 'W':(-1,0)}
        
        for d, p in pos.items():
            light = self.inter.lights[d]
            c = '#e74c3c' if light == State.RED else '#f1c40f' if light == State.YELLOW else '#2ecc71'
            
            self.canvas.create_rectangle(p[0]-8,p[1]-15,p[0]+8,p[1]+15,fill='black')
            for i,state in enumerate([State.RED, State.YELLOW, State.GREEN]):
                y = p[1]-9 + i*10
                fill = c if light == state else '#444'
                self.canvas.create_oval(p[0]-4,y-4,p[0]+4,y+4,fill=fill)
            
            # FIX: استفاده از list() برای deque
            lane = list(self.inter.lanes[d])[:5]
            for i, car in enumerate(lane):
                if d == 'N':
                    x = cx - w/4 + (i%2)*w/2
                    y = cy - w/2 - 12 - i*8
                elif d == 'S':
                    x = cx - w/4 + (i%2)*w/2
                    y = cy + w/2 + 12 + i*8
                elif d == 'E':
                    x = cx + w/2 + 12 + i*8
                    y = cy - w/4 + (i%2)*w/2
                else:
                    x = cx - w/2 - 12 - i*8
                    y = cy - w/4 + (i%2)*w/2
                self.canvas.create_rectangle(x-4,y-3,x+4,y+3,fill='#3498db')
            
            self.canvas.create_text(p[0], p[1]+30 if d in ['N','S'] else p[0]+30 if d=='E' else p[0]-30,
                                  text=f"{d}\n{len(self.inter.lanes[d])}", fill=c, font=('Arial',7,'bold'))
    
    def update_status(self):
        s = f"Passed: {self.inter.passed}  |  Avg Wait: {self.inter.total_wait/max(self.inter.passed,1):.1f}s"
        self.status.config(text=s)
    
    def add_car(self):
        d = self.dir.get()
        if d in ['N','S','E','W']:
            if self.inter.add_car(d):
                messagebox.showinfo("OK", f"Car added to {d}")
            else:
                messagebox.showwarning("Full", "Lane full!")
    
    def toggle(self):
        self.running = not self.running
        self.pause_btn.config(text="Resume" if not self.running else "Pause",
                             bg='#27ae60' if not self.running else '#e67e22')
    
    def reset(self):
        if messagebox.askyesno("Confirm", "Reset?"):
            self.inter = Intersection()
            self.running = True
            self.pause_btn.config(text="Pause", bg='#e67e22')
    
    def update(self):
        if self.running:
            self.draw()
            self.update_status()
        self.root.after(500, self.update)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    TrafficGUI().run()