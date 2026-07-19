import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from threading import Thread
from dataclasses import dataclass
from enum import Enum
from typing import List
from collections import deque


class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"


@dataclass
class Person:
    id: int
    current_floor: int
    target_floor: int
    waiting_time: float = 0.0


class Floor:
    def __init__(self, num): self.num = num; self.waiting = []

    def add(self, p): self.waiting.append(p)

    def remove(self, p):
        if p in self.waiting: self.waiting.remove(p)

    @property
    def count(self): return len(self.waiting)


class Elevator:
    def __init__(self, id, capacity=8):
        self.id = id
        self.current_floor = 0
        self.targets = []
        self.passengers = []
        self.capacity = capacity
        self.is_moving = False
        self.direction = Direction.IDLE
        self.is_open = True
        self.served = 0
        self.total_wait = 0.0

    def add_passenger(self, p):
        if len(self.passengers) < self.capacity:
            self.passengers.append(p)
            if p.target_floor not in self.targets:
                self.targets.append(p.target_floor)
            return True
        return False

    def remove_passenger(self, p):
        if p in self.passengers:
            self.passengers.remove(p)
            if p.target_floor in self.targets:
                self.targets.remove(p.target_floor)

    def update(self, dt):
        for p in self.passengers:
            p.waiting_time += dt

        if not self.targets:
            self.is_moving = False
            self.direction = Direction.IDLE
            self.is_open = True
            return

        if self.direction in [Direction.UP, Direction.IDLE]:
            self.targets.sort()
            self.direction = Direction.UP
        else:
            self.targets.sort(reverse=True)
            self.direction = Direction.DOWN

        next_floor = self.targets[0]
        if self.current_floor < next_floor:
            self.current_floor += 1
            self.is_moving, self.is_open = True, False
        elif self.current_floor > next_floor:
            self.current_floor -= 1
            self.is_moving, self.is_open = True, False
        else:
            self.targets.pop(0)
            self.is_moving, self.is_open = False, True
            for p in self.passengers[:]:
                if p.target_floor == self.current_floor:
                    self.served += 1
                    self.total_wait += p.waiting_time
                    self.remove_passenger(p)

    def add_request(self, floor):
        if floor not in self.targets:
            self.targets.append(floor)


class Building:
    def __init__(self, a=6):
        self.total_floors = 10 * a
        self.floors = [Floor(i) for i in range(self.total_floors)]
        self.elevators = [Elevator(i, 8) for i in range(3)]
        self.person_id = 0
        self.time = 0
        self.requests = 0
        self.completed = 0

    def call_elevator(self, floor, target):
        if floor == target or floor < 0 or floor >= self.total_floors or target < 0 or target >= self.total_floors:
            return False
        person = Person(self.person_id, floor, target)
        self.person_id += 1
        self.floors[floor].add(person)
        self.requests += 1

        best = self._find_best_elevator(floor, target)
        if best:
            best.add_request(floor)
            return True
        return False

    def _find_best_elevator(self, floor, target):
        best, best_score = None, float('inf')
        for e in self.elevators:
            if e.direction == Direction.IDLE:
                score = abs(e.current_floor - floor)
            elif e.direction == Direction.UP:
                score = floor - e.current_floor if floor >= e.current_floor else (
                                                                                             self.total_floors - e.current_floor) + floor
            else:
                score = e.current_floor - floor if floor <= e.current_floor else e.current_floor + (
                            self.total_floors - floor)
            # Fixed: استفاده از len(e.passengers) به جای e.passenger_count
            score += abs(floor - target) + len(e.passengers) * 1.5
            if score < best_score:
                best_score, best = score, e
        return best

    def update(self, dt=0.1):
        self.time += dt
        for e in self.elevators:
            e.update(dt)
            if e.is_open and not e.is_moving:
                floor = self.floors[e.current_floor]
                for p in floor.waiting[:]:
                    if e.add_passenger(p):
                        floor.remove(p)
                        self.completed += 1

    def get_stats(self):
        waiting = sum(f.count for f in self.floors)
        passengers = sum(len(e.passengers) for e in self.elevators)
        total_served = sum(e.served for e in self.elevators)
        avg_wait = sum(e.total_wait for e in self.elevators) / max(total_served, 1)
        return {'requests': self.requests, 'completed': self.completed,
                'waiting': waiting, 'passengers': passengers,
                'avg_wait': avg_wait, 'total': waiting + passengers}


class ElevatorGUI:
    def __init__(self):
        self.a = 6
        self.building = Building(self.a)
        self.total_floors = self.building.total_floors

        self.root = tk.Tk()
        self.root.title(f"Smart Elevator Simulator - {self.total_floors} Floors (a={self.a})")
        self.root.geometry("850x750")
        self.root.configure(bg='#f0f0f0')

        self._create_widgets()
        self.running = True
        self.update()

        self.thread = Thread(target=self._sim_loop)
        self.thread.daemon = True
        self.thread.start()

    def _create_widgets(self):
        # Title
        tk.Label(self.root, text=f"Smart Elevator Simulator - {self.total_floors} Floors (a={self.a})",
                 font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(fill=tk.X, pady=5)

        # Main frames
        main = tk.Frame(self.root, bg='#f0f0f0')
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        right = tk.Frame(main, bg='#f0f0f0', width=300)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        left = tk.Frame(main, bg='#f0f0f0')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas
        canvas_frame = tk.Frame(left)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas = tk.Canvas(canvas_frame, bg='white', width=550, height=600,
                                highlightthickness=2, highlightbackground='#bdc3c7')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas_height = max(400, self.total_floors * 10 + 50)
        self.canvas.configure(scrollregion=(0, 0, 550, self.canvas_height))

        # Controls
        ctrl = tk.LabelFrame(right, text="Control", font=('Arial', 11, 'bold'),
                             bg='#f0f0f0', padx=10, pady=10)
        ctrl.pack(fill=tk.X, pady=5)

        tk.Label(ctrl, text="From:", bg='#f0f0f0').pack()
        self.from_floor = tk.StringVar(value="0")
        ttk.Spinbox(ctrl, from_=0, to=self.total_floors - 1, textvariable=self.from_floor, width=10).pack(pady=2)

        tk.Label(ctrl, text="To:", bg='#f0f0f0').pack()
        self.to_floor = tk.StringVar(value=str(min(5, self.total_floors - 1)))
        ttk.Spinbox(ctrl, from_=0, to=self.total_floors - 1, textvariable=self.to_floor, width=10).pack(pady=2)

        tk.Button(ctrl, text="Call", bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                  command=self.call_elevator, padx=20, pady=5).pack(pady=10)

        btn_frame = tk.Frame(ctrl, bg='#f0f0f0')
        btn_frame.pack()
        self.pause_btn = tk.Button(btn_frame, text="Pause", bg='#e67e22', fg='white',
                                   font=('Arial', 10, 'bold'), command=self.toggle_pause, width=10)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", bg='#e74c3c', fg='white',
                  font=('Arial', 10, 'bold'), command=self.reset, width=10).pack(side=tk.LEFT, padx=5)

        self.auto_var = tk.BooleanVar()
        tk.Checkbutton(ctrl, text="Auto", variable=self.auto_var, bg='#f0f0f0').pack(pady=5)

        # Status
        status = tk.LabelFrame(right, text="Status", font=('Arial', 11, 'bold'),
                               bg='#f0f0f0', padx=10, pady=10)
        status.pack(fill=tk.X, pady=5)
        self.status_labels = []
        for i in range(3):
            lbl = tk.Label(status, text=f"E{i + 1}: Floor 0 | Pass: 0/8", bg='#f0f0f0', font=('Consolas', 9))
            lbl.pack(anchor=tk.W, pady=1)
            self.status_labels.append(lbl)
        self.waiting_lbl = tk.Label(status, text="Waiting: 0", bg='#f0f0f0', font=('Consolas', 9))
        self.waiting_lbl.pack(anchor=tk.W, pady=1)
        self.time_lbl = tk.Label(status, text="Time: 0.0s", bg='#f0f0f0', font=('Consolas', 9))
        self.time_lbl.pack(anchor=tk.W, pady=1)

        # Stats
        stats = tk.LabelFrame(right, text="Statistics", font=('Arial', 11, 'bold'),
                              bg='#f0f0f0', padx=10, pady=10)
        stats.pack(fill=tk.X, pady=5)
        self.stats_lbls = []
        for text in ["Requests: 0", "Completed: 0", "Avg Wait: 0.0s", "Total: 0"]:
            lbl = tk.Label(stats, text=text, bg='#f0f0f0', font=('Consolas', 9))
            lbl.pack(anchor=tk.W, pady=1)
            self.stats_lbls.append(lbl)

    def _sim_loop(self):
        while True:
            if self.running:
                if self.auto_var.get() and random.random() < 0.05:
                    f, t = random.randint(0, self.total_floors - 1), random.randint(0, self.total_floors - 1)
                    if f != t:
                        self.building.call_elevator(f, t)
                self.building.update()
            time.sleep(0.1)

    def draw(self):
        self.canvas.delete("all")
        h, fh = self.canvas_height, min(12, (self.canvas_height - 50) // self.total_floors)
        sy = 20

        self.canvas.create_rectangle(50, 10, 500, h - 10, fill='#ecf0f1', outline='#bdc3c7', width=2)

        for i in range(self.total_floors):
            y = sy + (self.total_floors - 1 - i) * fh
            self.canvas.create_rectangle(70, y, 480, y + fh - 1,
                                         fill='#ffffff' if i % 2 == 0 else '#f8f9fa', outline='#95a5a6')
            if i % 5 == 0 or i == self.total_floors - 1:
                self.canvas.create_text(55, y + fh / 2 - 2, text=str(i), font=('Arial', 6, 'bold'))
            if self.building.floors[i].count > 0:
                for j in range(min(self.building.floors[i].count, 3)):
                    self.canvas.create_oval(80 + j * 10 - 3, y + fh / 2 - 3, 80 + j * 10 + 3, y + fh / 2 + 3,
                                            fill='#e74c3c')
                if self.building.floors[i].count > 3:
                    self.canvas.create_text(80 + 30, y + fh / 2, text=f"+{self.building.floors[i].count - 3}",
                                            font=('Arial', 5))

        ew = min(50, 400 // len(self.building.elevators) - 10)
        for idx, e in enumerate(self.building.elevators):
            y = sy + (self.total_floors - 1 - e.current_floor) * fh
            x = 70 + (idx + 1) * (400 // (len(self.building.elevators) + 1)) - ew // 2
            color = '#3498db' if not e.is_open else '#2ecc71'
            self.canvas.create_rectangle(x, y + 2, x + ew, y + fh - 2, fill=color, outline='#2980b9', width=1)
            self.canvas.create_text(x + ew / 2, y + 8, text=f"E{e.id + 1}", font=('Arial', 5, 'bold'), fill='white')
            self.canvas.create_text(x + ew / 2, y + fh - 6, text=f"P{len(e.passengers)}", font=('Arial', 5),
                                    fill='white')
            if e.direction != Direction.IDLE:
                self.canvas.create_text(x + ew / 2, y + fh / 2, text="▲" if e.direction == Direction.UP else "▼",
                                        font=('Arial', 8), fill='white')
            color = '#2ecc71' if e.is_open else '#e74c3c'
            self.canvas.create_rectangle(x + 2, y + 2, x + 12, y + 8, fill=color, outline='white')
            self.canvas.create_text(x + 7, y + 5, text="O" if e.is_open else "C", font=('Arial', 4, 'bold'),
                                    fill='white')

    def update_status(self):
        for i, e in enumerate(self.building.elevators):
            self.status_labels[i].config(
                text=f"E{i + 1}: Floor {e.current_floor} | Pass: {len(e.passengers)}/8 | {'Open' if e.is_open else 'Closed'}")
        self.waiting_lbl.config(text=f"Waiting: {sum(f.count for f in self.building.floors)}")
        self.time_lbl.config(text=f"Time: {self.building.time:.1f}s")

        s = self.building.get_stats()
        self.stats_lbls[0].config(text=f"Requests: {s['requests']}")
        self.stats_lbls[1].config(text=f"Completed: {s['completed']}")
        self.stats_lbls[2].config(text=f"Avg Wait: {s['avg_wait']:.1f}s")
        self.stats_lbls[3].config(text=f"Total: {s['total']}")

    def call_elevator(self):
        try:
            f, t = int(self.from_floor.get()), int(self.to_floor.get())
            if f == t:
                messagebox.showwarning("Error", "Same floor!")
                return
            if self.building.call_elevator(f, t):
                messagebox.showinfo("Success", f"Called from {f} to {t}")
            else:
                messagebox.showwarning("Error", "Cannot call!")
        except:
            messagebox.showwarning("Error", "Invalid input!")

    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.config(text="Resume" if not self.running else "Pause",
                              bg='#27ae60' if not self.running else '#e67e22')

    def reset(self):
        if messagebox.askyesno("Confirm", "Reset?"):
            self.building = Building(self.a)
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
    ElevatorGUI().run()