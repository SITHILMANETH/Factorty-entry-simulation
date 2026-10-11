"""Desktop dashboard for the factory queue simulation."""

import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from .config import DEFAULT_CONFIG
from .experiments import clock_to_seconds, run_baseline_experiment


class SimulationDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Factory Morning Entry Simulation")
        self.root.geometry("1220x850")
        self.root.minsize(980, 700)
        self.animation = None
        self.events = []
        self.duration = 1.0

        self.worker_count = tk.StringVar(value=str(DEFAULT_CONFIG["total_workers"]))
        self.arrival_count = tk.StringVar(value=str(DEFAULT_CONFIG["arrivals"]))
        self.arrival_start = tk.StringVar(value=DEFAULT_CONFIG["arrival_start_time"])
        self.arrival_end = tk.StringVar(value=DEFAULT_CONFIG["arrival_end_time"])
        self.seed = tk.StringVar(value="42")
        self.speed = tk.DoubleVar(value=1.0)
        self.status = tk.StringVar(value="Ready")

        self._build_controls()
        self._build_results()
        self.run_simulation()

    def _build_controls(self):
        controls = ttk.LabelFrame(self.root, text="Morning rush settings", padding=10)
        controls.pack(fill=tk.X, padx=12, pady=(12, 6))

        fields = (
            ("Factory workers", self.worker_count),
            ("Morning arrivals", self.arrival_count),
            ("Start time (HH:MM)", self.arrival_start),
            ("End time (HH:MM)", self.arrival_end),
            ("Random seed", self.seed),
        )
        for column, (label, variable) in enumerate(fields):
            ttk.Label(controls, text=label).grid(row=0, column=column * 2, padx=(0, 6))
            ttk.Entry(controls, textvariable=variable, width=12).grid(
                row=0, column=column * 2 + 1, padx=(0, 18)
            )

        ttk.Button(controls, text="Run simulation", command=self.run_simulation).grid(
            row=0, column=10, padx=(8, 0)
        )
        ttk.Button(controls, text="Replay", command=self.replay).grid(
            row=0, column=11, padx=(8, 0)
        )
        ttk.Label(controls, text="Speed").grid(row=0, column=12, padx=(18, 6))
        ttk.Scale(
            controls,
            from_=0.25,
            to=4.0,
            variable=self.speed,
            orient=tk.HORIZONTAL,
            length=120,
        ).grid(row=0, column=13, padx=(0, 18))
        ttk.Label(controls, textvariable=self.status).grid(
            row=0, column=14, padx=(8, 0), sticky=tk.W
        )
        ttk.Label(
            controls,
            text="Workers are round dots; arrivals are distributed between the selected clock times.",
        ).grid(row=1, column=0, columnspan=15, pady=(8, 0), sticky=tk.W)

    def _build_results(self):
        self.figure = Figure(figsize=(12, 8), dpi=100)
        layout = self.figure.add_gridspec(2, 2, height_ratios=(1.5, 1))
        self.animation_axis = self.figure.add_subplot(layout[0, :])
        self.wait_axis = self.figure.add_subplot(layout[1, 0])
        self.jobs_axis = self.figure.add_subplot(layout[1, 1])
        self.figure.tight_layout(pad=3)
        self.chart = FigureCanvasTkAgg(self.figure, master=self.root)
        self.chart.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 12))

    def run_simulation(self):
        try:
            worker_count = int(self.worker_count.get())
            arrival_count = int(self.arrival_count.get())
            seed = int(self.seed.get())
            start_seconds = clock_to_seconds(self.arrival_start.get())
            end_seconds = clock_to_seconds(self.arrival_end.get())
            if worker_count < 1 or arrival_count < 1:
                raise ValueError
            if end_seconds <= start_seconds:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid settings",
                "Use positive numbers and clock times in HH:MM format. End time must be later than start time.",
            )
            return

        if self.animation is not None:
            self.animation.event_source.stop()

        result = run_baseline_experiment(
            seed=seed,
            config={
                "total_workers": worker_count,
                "arrivals": arrival_count,
                "arrival_start_time": self.arrival_start.get(),
                "arrival_end_time": self.arrival_end.get(),
            },
        )
        self.events = result["worker_events"]
        self.duration = max(result["duration"], end_seconds - start_seconds)
        self.arrival_start_seconds = start_seconds
        metrics = result["metrics"]

        pathways = metrics["pathway"].tolist()
        self.wait_axis.clear()
        self.wait_axis.bar(pathways, metrics["average_wait_time"], color="#d95f59")
        self.wait_axis.set_title("Average queue wait by pathway")
        self.wait_axis.set_xlabel("Pathway")
        self.wait_axis.set_ylabel("Seconds")
        self.wait_axis.grid(axis="y", alpha=0.25)

        self.jobs_axis.clear()
        self.jobs_axis.bar(pathways, metrics["jobs"], color="#3478a4")
        self.jobs_axis.set_title("Arrivals using each pathway")
        self.jobs_axis.set_xlabel("Pathway")
        self.jobs_axis.set_ylabel("Workers")
        self.jobs_axis.grid(axis="y", alpha=0.25)

        self.animation_axis.clear()
        self.animation_axis.set_xlim(-1.0, 1.15)
        self.animation_axis.set_ylim(-0.8, 9.8)
        self.animation_axis.set_yticks(range(10))
        self.animation_axis.set_yticklabels([f"Pathway {index + 1}" for index in range(10)])
        self.animation_axis.set_xticks([-0.7, 0.12, 0.52, 0.9])
        self.animation_axis.set_xticklabels(
            ["Waiting queue", "Face / fingerprint", "Spin gate", "Factory"]
        )
        self.animation_axis.set_xlabel("Worker movement from left to right")
        self.animation_axis.set_title("Morning entry: 10 pathways, one scanner and one spin gate per pathway")
        self.animation_axis.grid(axis="y", alpha=0.2)
        self.animation_axis.axvspan(-0.95, -0.05, color="#f4c95d", alpha=0.12)
        self.animation_axis.axvspan(-0.05, 0.3, color="#d95f59", alpha=0.12)
        self.animation_axis.axvspan(0.3, 0.75, color="#3478a4", alpha=0.12)
        self.animation_axis.axvspan(0.75, 1.15, color="#5aa469", alpha=0.12)
        self.animation_axis.legend(
            handles=[
                Patch(color="#f0a202", label="Waiting"),
                Patch(color="#d95f59", label="Scanning"),
                Patch(color="#3478a4", label="Gate opening"),
            ],
            loc="upper right",
            ncol=3,
            frameon=False,
        )
        self.figure.tight_layout(pad=3)
        self._start_animation()

    def _start_animation(self):
        self.animation = FuncAnimation(
            self.figure,
            self._draw_frame,
            frames=180,
            interval=max(10, int(50 / self.speed.get())),
            repeat=False,
        )
        self.chart.draw_idle()

    def _draw_frame(self, frame):
        simulation_time = self.duration * frame / 179
        offsets = []
        colors = []
        for event in self.events:
            if event["arrival_time"] > simulation_time or event["exit_time"] <= simulation_time:
                continue
            lane = event["pathway"]
            if simulation_time < event["auth_start"]:
                queue_rank = sum(
                    other["pathway"] == lane
                    and other["arrival_time"] <= simulation_time
                    and other["auth_start"] > simulation_time
                    and other["job_id"] < event["job_id"]
                    for other in self.events
                )
                x_position = max(-0.9, -0.12 - queue_rank * 0.055)
                colors.append("#f0a202")
            elif simulation_time < event["auth_end"]:
                x_position = 0.12
                colors.append("#d95f59")
            else:
                x_position = 0.52
                colors.append("#3478a4")
            offsets.append((x_position, lane))

        for collection in list(self.animation_axis.collections):
            collection.remove()
        if offsets:
            self.animation_axis.scatter(
                [position[0] for position in offsets],
                [position[1] for position in offsets],
                s=42,
                c=colors,
                edgecolors="white",
                linewidths=0.4,
                zorder=5,
            )
        clock_minutes = self.arrival_start_seconds / 60 + simulation_time / 60
        hour = int(clock_minutes // 60) % 24
        minute = int(clock_minutes % 60)
        self.status.set(
            f"Clock {hour:02d}:{minute:02d} | visible workers: {len(offsets)}"
        )
        return self.animation_axis.collections

    def replay(self):
        if self.events:
            self._start_animation()


def launch():
    root = tk.Tk()
    SimulationDashboard(root)
    root.mainloop()