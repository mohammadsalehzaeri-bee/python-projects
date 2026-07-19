# project6_metro.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
from threading import Thread
from collections import deque

class Passenger:
    def __init__(self, id):
        self.id = id
        self.has_card = True
        self.entered = False
        self.balance = random.randint(10000, 50000)

class Card:
    def __init__(self, passenger):
        self.passenger = passenger
        self.balance = passenger.balance
        self.valid = True
    
    def deduct(self, amount=1000):
        if self.balance >= amount and self.valid:
            self.balance -= amount
            self.passenger.balance = self.balance
            return True
        return False

class Gate:
    def __init__(self, gate_id):
        self.id = gate_id
        self.is_open = False
        self.passenger = None
        self.sensor_active = False
        self.status = "IDLE"
    
    def open(self):
        self.is_open = True
        self.status = "OPEN"
    
    def close(self):
        self.is_open = False
        self.status = "CLOSED"
    
    def process(self, passenger):
        if passenger.has_card:
            card = Card(passenger)
            if card.deduct(1000):
                self.passenger = passenger
                self.open()
                time.sleep(0.5)
                passenger.entered = True
                self.close()
                return True
        return False

class MetroGateGUI:
    def __init__(self):
        self.gates = [Gate(0), Gate(1), Gate(2)]
        self.queue = deque()
        self.passenger_id = 0
        self.total_passengers = 0
        self.served = 0
        
        self.root = tk.Tk()
        self.root.title("Metro Gate Simulator")
        self.root.geometry("700x600")
        self.root.configure(bg='#2c3e50')
        
        self.running = True
        self._create_widgets()
        self.update()
        
        self.thread = Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _create_widgets(self):
        tk.Label(self.root, text="Metro Gate Simulator", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=5)
        
        # Canvas
        self.canvas = tk.Canvas(self.root, width=650, height=350, bg='white')
        self.canvas.pack(pady=10)
        
        # Controls
        ctrl = tk.Frame(self.root, bg='#2c3e50')
        ctrl.pack(pady=5)
        
        tk.Button(ctrl, text="Add Passenger", bg='#3498db', fg='white',
                 command=self.add_passenger, width=15).pack(side=tk.LEFT, padx=5)
        
        self.auto_var = tk.BooleanVar()
        tk.Checkbutton(ctrl, text="Auto Add", variable=self.auto_var,
                      bg='#2c3e50', fg='white', selectcolor='#2c3e50').pack(side=tk.LEFT, padx=10)
        
        self.pause_btn = tk.Button(ctrl, text="Pause", bg='#e67e22', fg='white',
                                  command=self.toggle, width=10)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(ctrl, text="Reset", bg='#e74c3c', fg='white',
                 command=self.reset, width=10).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status = tk.Label(self.root, text="", bg='#2c3e50', fg='white', font=('Consolas', 10))
        self.status.pack(pady=5)
        
        self.queue_label = tk.Label(self.root, text="Queue: 0", bg='#2c3e50', fg='white', font=('Consolas', 10))
        self.queue_label.pack()
    
    def _loop(self):
        while True:
            if self.running:
                # Auto add passengers
                if self.auto_var.get() and random.random() < 0.1:
                    self.add_passenger()
                
                # Process queue
                if self.queue and self.gates:
                    passenger = self.queue.popleft()
                    for gate in self.gates:
                        if not gate.is_open:
                            if gate.process(passenger):
                                self.served += 1
                                break
            time.sleep(0.1)
    
    def draw(self):
        self.canvas.delete("all")
        y = 100
        
        for i, gate in enumerate(self.gates):
            x = 100 + i * 180
            
            # Gate
            color = '#2ecc71' if gate.is_open else '#e74c3c'
            self.canvas.create_rectangle(x, y, x+80, y+120, fill=color, outline='black')
            self.canvas.create_text(x+40, y+20, text=f"Gate {gate.id+1}", font=('Arial', 10, 'bold'))
            self.canvas.create_text(x+40, y+40, text=gate.status, font=('Arial', 8))
            
            # Passenger
            if gate.passenger:
                self.canvas.create_text(x+40, y+80, text=f"P{gate.passenger.id}", font=('Arial', 9))
            
            # Sensor
            if gate.sensor_active:
                self.canvas.create_oval(x+30, y+140, x+50, y+160, fill='#f1c40f')
    
    def update_status(self):
        total = len(self.queue)
        self.queue_label.config(text=f"Queue: {total}  |  Served: {self.served}  |  Total: {self.total_passengers}")
    
    def add_passenger(self):
        p = Passenger(self.passenger_id)
        self.passenger_id += 1
        self.total_passengers += 1
        self.queue.append(p)
        return p
    
    def toggle(self):
        self.running = not self.running
        self.pause_btn.config(text="Resume" if not self.running else "Pause",
                             bg='#27ae60' if not self.running else '#e67e22')
    
    def reset(self):
        if messagebox.askyesno("Confirm", "Reset?"):
            self.gates = [Gate(0), Gate(1), Gate(2)]
            self.queue = deque()
            self.passenger_id = 0
            self.total_passengers = 0
            self.served = 0
            self.running = True
            self.pause_btn.config(text="Pause", bg='#e67e22')
    
    def update(self):
        if self.running:
            self.draw()
            self.update_status()
        self.root.after(100, self.update)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    MetroGateGUI().run()