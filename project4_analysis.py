# project4_analysis.py
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class TransferFunction:
    def __init__(self, K=1, zeta=0.5, omega=1):
        self.K = K
        self.zeta = zeta
        self.omega = omega
    
    def step_response(self, t):
        if self.zeta < 1:  # Underdamped
            wd = self.omega * np.sqrt(1 - self.zeta**2)
            theta = np.arctan2(wd, self.zeta * self.omega)
            y = self.K * (1 - (1/np.sqrt(1-self.zeta**2)) * np.exp(-self.zeta*self.omega*t) * 
                         np.cos(wd*t - theta))
        elif self.zeta == 1:  # Critically damped
            y = self.K * (1 - np.exp(-self.omega*t) * (1 + self.omega*t))
        else:  # Overdamped
            s1 = -self.zeta*self.omega + self.omega*np.sqrt(self.zeta**2-1)
            s2 = -self.zeta*self.omega - self.omega*np.sqrt(self.zeta**2-1)
            y = self.K * (1 + (s2*np.exp(s1*t) - s1*np.exp(s2*t))/(s1-s2))
        return y
    
    def get_metrics(self):
        t = np.linspace(0, 20, 1000)
        y = self.step_response(t)
        
        # Settling time (2% criterion)
        final = y[-1]
        idx = np.where(np.abs(y - final) < 0.02 * final)[0]
        settling_time = t[idx[0]] if len(idx) > 0 else t[-1]
        
        # Rise time (10% to 90%)
        idx10 = np.where(y >= 0.1 * final)[0]
        idx90 = np.where(y >= 0.9 * final)[0]
        rise_time = t[idx90[0]] - t[idx10[0]] if len(idx10) > 0 and len(idx90) > 0 else 0
        
        # Overshoot
        overshoot = (np.max(y) - final) / final * 100 if self.zeta < 1 else 0
        
        return {
            'settling_time': settling_time,
            'rise_time': rise_time,
            'overshoot': max(0, overshoot),
            'final_value': final
        }

class AnalysisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Response Analysis")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        self.tf = TransferFunction()
        self._create_widgets()
        self.update_plot()
    
    def _create_widgets(self):
        # Title
        tk.Label(self.root, text="System Response Analysis Tool", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=5)
        
        main = tk.Frame(self.root, bg='#2c3e50')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Plot
        left = tk.Frame(main, bg='#2c3e50')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Response')
        self.ax.grid(True)
        self.ax.set_title('Step Response')
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        
        self.canvas = FigureCanvasTkAgg(fig, left)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Right: Controls
        right = tk.Frame(main, bg='#2c3e50', width=250)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        
        ctrl = tk.LabelFrame(right, text="Parameters", font=('Arial', 11, 'bold'),
                            bg='#2c3e50', fg='white', padx=10, pady=10)
        ctrl.pack(fill=tk.X, pady=5)
        
        # K
        tk.Label(ctrl, text="K (Gain):", bg='#2c3e50', fg='white').pack()
        self.K_var = tk.StringVar(value="1.0")
        ttk.Spinbox(ctrl, from_=0.1, to=10, textvariable=self.K_var, width=10).pack(pady=5)
        
        # Zeta
        tk.Label(ctrl, text="ζ (Damping):", bg='#2c3e50', fg='white').pack()
        self.zeta_var = tk.StringVar(value="0.5")
        ttk.Spinbox(ctrl, from_=0, to=2, textvariable=self.zeta_var, width=10, increment=0.1).pack(pady=5)
        
        # Omega
        tk.Label(ctrl, text="ωn (Natural Freq):", bg='#2c3e50', fg='white').pack()
        self.omega_var = tk.StringVar(value="1.0")
        ttk.Spinbox(ctrl, from_=0.1, to=5, textvariable=self.omega_var, width=10, increment=0.1).pack(pady=5)
        
        tk.Button(ctrl, text="Plot", bg='#3498db', fg='white',
                 font=('Arial', 10, 'bold'), command=self.update_plot).pack(pady=10)
        
        # Metrics
        metrics = tk.LabelFrame(right, text="Metrics", font=('Arial', 11, 'bold'),
                               bg='#2c3e50', fg='white', padx=10, pady=10)
        metrics.pack(fill=tk.X, pady=5)
        
        self.metrics_labels = []
        for text in ["Settling Time: -- s", "Rise Time: -- s", "Overshoot: -- %", "Final Value: --"]:
            lbl = tk.Label(metrics, text=text, bg='#2c3e50', fg='white', font=('Consolas', 10))
            lbl.pack(anchor=tk.W, pady=2)
            self.metrics_labels.append(lbl)
        
        # Examples
        ex = tk.LabelFrame(right, text="Examples", font=('Arial', 11, 'bold'),
                          bg='#2c3e50', fg='white', padx=10, pady=10)
        ex.pack(fill=tk.X, pady=5)
        
        for text, K, zeta, omega in [
            ("Underdamped (ζ=0.3)", 1, 0.3, 1),
            ("Critically Damped (ζ=1)", 1, 1, 1),
            ("Overdamped (ζ=1.5)", 1, 1.5, 1)
        ]:
            tk.Button(ex, text=text, bg='#2ecc71', fg='white',
                     font=('Arial', 8), command=lambda k=K, z=zeta, o=omega: self.load_example(k, z, o),
                     width=20).pack(pady=2)
    
    def load_example(self, K, zeta, omega):
        self.K_var.set(str(K))
        self.zeta_var.set(str(zeta))
        self.omega_var.set(str(omega))
        self.update_plot()
    
    def update_plot(self):
        try:
            K = float(self.K_var.get())
            zeta = float(self.zeta_var.get())
            omega = float(self.omega_var.get())
            
            self.tf = TransferFunction(K, zeta, omega)
            t = np.linspace(0, 20, 1000)
            y = self.tf.step_response(t)
            
            self.line.set_data(t, y)
            self.ax.relim()
            self.ax.autoscale_view()
            self.ax.axhline(y=K, color='r', linestyle='--', alpha=0.5, label='Final')
            self.ax.legend()
            self.canvas.draw()
            
            # Update metrics
            metrics = self.tf.get_metrics()
            self.metrics_labels[0].config(text=f"Settling Time: {metrics['settling_time']:.2f} s")
            self.metrics_labels[1].config(text=f"Rise Time: {metrics['rise_time']:.2f} s")
            self.metrics_labels[2].config(text=f"Overshoot: {metrics['overshoot']:.1f} %")
            self.metrics_labels[3].config(text=f"Final Value: {metrics['final_value']:.2f}")
            
        except:
            messagebox.showwarning("Error", "Invalid input!")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    AnalysisGUI().run()