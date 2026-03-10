# encoding: utf-8
"""
VisionFit – Optimised Animated UI
Single 20-fps master clock drives ALL canvas animations.
No emoji glyphs, no per-widget after() loops.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os, threading, importlib.util, sys, subprocess, math, time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette — matches HTML design system exactly ──────────────────────────────
BG       = "#060F1E"   # --ink-deep
PANEL    = "#0B2545"   # --ink
CARD     = "#0f3260"   # --card
CARD_LIT = "#133570"   # --card2
BORDER   = "#1d4a8a"   # --rule
CYAN     = "#4CC9F0"   # --hi
VIOLET   = "#38B2D8"   # --hi2
GREEN    = "#06D6A0"   # --green
AMBER    = "#FFD166"   # --amber
RED      = "#FF6B6B"   # --red
WHITE    = "#ffffff"   # --cream
MUTED    = "#6e95bb"   # --muted

# ── Fonts — matches HTML design system ───────────────────────────────────────
# --serif: "Playfair Display", Georgia, serif
# --sans:  "IBM Plex Sans", system-ui, sans-serif
# --mono:  "IBM Plex Mono", monospace
FONT_SERIF = "Playfair Display"   # falls back to Georgia if not installed
FONT_SANS  = "IBM Plex Sans"      # falls back to system default sans
FONT_MONO  = "IBM Plex Mono"      # falls back to Consolas/Courier

ACT_COLORS = {
    "Jumping Jacks":    ("#4CC9F0", "#38B2D8"),   # cyan family
    "Flamingo Balance": ("#FFD166", "#F59E3A"),   # amber family
    "Squats":           ("#8B5CF6", "#6D28D9"),   # violet (one-off for contrast)
    "Vertical Jumps":   ("#06D6A0", "#059669"),   # green family
}
# Simple Unicode symbols (not emoji) for each activity
ACT_SYMBOL = {
    "Jumping Jacks":    "\u2605",   # filled star
    "Flamingo Balance": "\u25C6",   # filled diamond
    "Squats":           "\u25BC",   # filled triangle down
    "Vertical Jumps":   "\u25B2",   # filled triangle up
}
ACT_ABBREV = {
    "Jumping Jacks":    "JJ",
    "Flamingo Balance": "FB",
    "Squats":           "SQ",
    "Vertical Jumps":   "VJ",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def lerp(a, b, t): return a + (b - a) * t

def hex_lerp(h1, h2, t):
    r1,g1,b1 = int(h1[1:3],16), int(h1[3:5],16), int(h1[5:7],16)
    r2,g2,b2 = int(h2[1:3],16), int(h2[3:5],16), int(h2[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        max(0,min(255,int(lerp(r1,r2,t)))),
        max(0,min(255,int(lerp(g1,g2,t)))),
        max(0,min(255,int(lerp(b1,b2,t)))))


# ─────────────────────────────────────────────────────────────────────────────
# MASTER CLOCK  – all canvas widgets register here, one after() loop total
# ─────────────────────────────────────────────────────────────────────────────
class Clock:
    FPS = 20   # 50 ms per tick — smooth enough, low CPU

    def __init__(self, root: tk.Misc):
        self._root = root
        self._t    = 0.0
        self._subs: list = []
        self._active = True
        self._tick()

    def register(self, fn):
        """Register a callable(t) that will be called every tick."""
        self._subs.append(fn)

    def _tick(self):
        if not self._active:
            return
        self._t += 1 / self.FPS
        for fn in self._subs:
            try:
                fn(self._t)
            except Exception:
                pass
        self._root.after(int(1000 / self.FPS), self._tick)

    def stop(self):
        self._active = False


# ─────────────────────────────────────────────────────────────────────────────
# Aurora Header Canvas  – simple, cheap colour-band animation
# ─────────────────────────────────────────────────────────────────────────────
class AuroraHeader(tk.Canvas):
    """
    Lightweight animated header: 3 wide colour blobs that drift slowly,
    drawn as just a handful of rectangles + text. Very low CPU cost.
    """
    def __init__(self, master, clock: Clock, **kw):
        super().__init__(master, highlightthickness=0, bd=0, bg=BG, **kw)
        self._tw_messages = [
            "AI-Powered Fitness Activity Analysis",
            "Real-time Pose Estimation & Tracking",
            "Powered by Computer Vision",
            "Smart Workout Insights",
        ]
        self._tw_mi   = 0
        self._tw_ci   = 0
        self._tw_del  = False
        self._tw_text = ""
        self._tw_pause = False
        self._tw_counter = 0       # tick counter for typewriter pacing
        clock.register(self._on_tick)
        self._do_typewriter_tick()  # kick off typewriter independently

    # typewriter is paced via after() at its own slow rate (no extra CPU)
    def _do_typewriter_tick(self):
        msg = self._tw_messages[self._tw_mi]
        if not self._tw_del:
            self._tw_ci = min(self._tw_ci + 1, len(msg))
            self._tw_text = msg[:self._tw_ci]
            if self._tw_ci >= len(msg):
                self.after(2500, self._start_delete)
                return
        else:
            self._tw_ci = max(self._tw_ci - 1, 0)
            self._tw_text = msg[:self._tw_ci]
            if self._tw_ci == 0:
                self._tw_del = False
                self._tw_mi  = (self._tw_mi + 1) % len(self._tw_messages)
                self.after(200, self._do_typewriter_tick)
                return
        self.after(55, self._do_typewriter_tick)

    def _start_delete(self):
        self._tw_del = True
        self._do_typewriter_tick()

    def _on_tick(self, t: float):
        self.delete("all")
        w = self.winfo_width()  or 980
        h = self.winfo_height() or 110

        # base background
        self.create_rectangle(0, 0, w, h, fill=BG, outline="")

        # 3 moving colour blobs (just 3 wide ovals – very cheap)
        blobs = [
            (0.15, 0.5, CYAN,   70, 0.22),
            (0.85, 0.5, VIOLET, 80, 0.16),
            (0.50, 0.8, "#0066FF", 60, 0.12),
        ]
        for bx, by, col, brad, intensity in blobs:
            pulse = 0.5 + 0.5 * math.sin(t * 1.4 + bx * 5)
            ox = bx * w + 0.04 * w * math.sin(t * 0.7 + bx)
            oy = by * h + 0.05 * h * math.cos(t * 0.5 + by)
            r  = int(brad * (0.85 + 0.15 * pulse))
            # 5-ring glow (only 5 ovals per blob = 15 ovals total)
            for ring in range(5, 0, -1):
                frac  = ring / 5
                alpha = intensity * frac * pulse
                rc, gc, bc = int(col[1:3],16), int(col[3:5],16), int(col[5:7],16)
                rc2 = max(0, min(255, int(rc * alpha * 2.5)))
                gc2 = max(0, min(255, int(gc * alpha * 2.5)))
                bc2 = max(0, min(255, int(bc * alpha * 2.5)))
                glow = "#{:02x}{:02x}{:02x}".format(rc2, gc2, bc2)
                r2   = int(r * frac)
                self.create_oval(ox-r2, oy-r2, ox+r2, oy+r2,
                                 fill="", outline=glow, width=2)

        # title — Playfair Display (serif), matching HTML --serif
        self.create_text(w//2, h//2 - 14,
                         text="VISIONFIT",
                         font=(FONT_SERIF, 26, "bold"),
                         fill=WHITE, anchor="center")
        # typewriter subtitle — IBM Plex Sans, matching HTML --sans
        cursor = "|" if (int(t * 3) % 2 == 0) else " "
        self.create_text(w//2, h//2 + 14,
                         text=self._tw_text + cursor,
                         font=(FONT_SANS, 11),
                         fill=CYAN, anchor="center")


# ─────────────────────────────────────────────────────────────────────────────
# Neon Activity Card (canvas, clock-driven)
# ─────────────────────────────────────────────────────────────────────────────
class NeonCard(tk.Canvas):
    W, H = 160, 140

    def __init__(self, master, name, clock: Clock, **kw):
        super().__init__(master, width=self.W, height=self.H,
                         highlightthickness=0, bd=0, bg=PANEL, **kw)
        self.name    = name
        self.col_a, self.col_b = ACT_COLORS[name]
        self.symbol  = ACT_SYMBOL[name]
        self.abbrev  = ACT_ABBREV[name]
        self.selected = False
        self._hover   = 0.0
        self._target  = 0.0
        self._phase   = hash(name) % 100 / 100 * math.tau  # stagger per card
        self.bind("<Enter>",    lambda _: setattr(self, "_target", 1.0))
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", lambda _: None)   # filled by parent
        clock.register(self._on_tick)

    def _on_leave(self, _=None):
        if not self.selected:
            self._target = 0.0

    def set_selected(self, sel: bool):
        self.selected = sel
        self._target  = 1.0 if sel else 0.0

    def _on_tick(self, t: float):
        # smooth hover interpolation (each tick = 50ms → step ~0.12)
        step = 0.12
        if self._hover < self._target:
            self._hover = min(self._hover + step, self._target)
        elif self._hover > self._target:
            self._hover = max(self._hover - step, self._target)
        self._draw(t)

    def _draw(self, t: float):
        self.delete("all")
        w, h = self.W, self.H
        hv    = self._hover
        pulse = 0.5 + 0.5 * math.sin(t * 1.8 + self._phase)
        glow  = lerp(0.25, 1.0, hv) * pulse

        # background
        bg = hex_lerp(CARD, CARD_LIT, hv)
        self.create_rectangle(0, 0, w, h, fill=bg, outline="")

        # border glow (4 inset rectangles, cheap)
        for ring in range(4, 0, -1):
            alpha  = glow * (ring / 4)
            b_col  = hex_lerp(BORDER, self.col_a, alpha)
            pad    = ring
            self.create_rectangle(pad, pad, w-pad, h-pad,
                                  outline=b_col, width=1, fill="")

        # top accent bar
        bar_col = hex_lerp(self.col_a, self.col_b, 0.5)
        self.create_rectangle(12, 10, w-12, 13, fill=bar_col, outline="")

        # icon symbol — IBM Plex Sans bold
        icon_col = hex_lerp(self.col_a, WHITE, hv * 0.35)
        self.create_text(w//2, h//2 - 12,
                         text=self.symbol,
                         font=(FONT_SANS, 30, "bold"),
                         fill=icon_col, anchor="center")

        # card label — IBM Plex Sans small caps style
        lbl_col = hex_lerp(MUTED, WHITE, hv)
        self.create_text(w//2, h//2 + 26,
                         text=self.name,
                         font=(FONT_SANS, 9, "bold"),
                         fill=lbl_col, anchor="center",
                         width=w - 16)

        # selected tick
        if self.selected:
            self.create_text(w - 14, 18, text="\u2713",
                             font=(FONT_SANS, 11, "bold"),
                             fill=self.col_a)


# ─────────────────────────────────────────────────────────────────────────────
# Status Bar Canvas (clock-driven)
# ─────────────────────────────────────────────────────────────────────────────
class StatusBar(tk.Canvas):
    H = 52

    def __init__(self, master, clock: Clock, **kw):
        super().__init__(master, height=self.H, highlightthickness=0,
                         bd=0, bg=CARD, **kw)
        self._state = "ready"
        self._msg   = "Ready"
        clock.register(self._on_tick)

    STATE_COLORS = {"ready": MUTED, "processing": CYAN,
                    "success": GREEN, "error": RED}

    def set_state(self, state, msg=""):
        self._state = state
        labels = {
            "ready":      "Ready  \u2013  select an activity and a video",
            "processing": f"Processing  \u00b7  {msg}",
            "success":    f"Complete  \u2714  {msg}",
            "error":      f"Error  \u2718  {msg}",
        }
        self._msg = labels.get(state, msg)

    def _on_tick(self, t: float):
        self.delete("all")
        w = self.winfo_width() or 900
        h = self.H
        accent = self.STATE_COLORS.get(self._state, MUTED)

        # background + top stripe
        self.create_rectangle(0, 0, w, h, fill=CARD, outline="")
        self.create_rectangle(0, 0, w, 2, fill=accent, outline="")

        # simple sine wave (only 40 line segments)
        pts: list[int] = []
        npts = 40
        for i in range(npts + 1):
            x = int(20 + (w * 0.5) * i / npts)
            if self._state == "processing":
                y = h//2 + int(9 * math.sin(t * 5 + i * 0.5))
            else:
                y = h//2 + int(2 * math.sin(t * 1.2 + i * 0.3))
            pts.extend([x, y])
        if len(pts) >= 4:
            self.create_line(*pts, fill=hex_lerp(BORDER, accent, 0.55),
                             width=2, smooth=True)

        # blinking dot
        blink = abs(math.sin(t * (4 if self._state == "processing" else 1)))
        dot_col = hex_lerp(CARD, accent, blink)
        self.create_oval(w-20, h//2-5, w-10, h//2+5,
                         fill=dot_col, outline="")

        # status text — IBM Plex Mono matching HTML --mono
        text_col = self.STATE_COLORS.get(self._state, MUTED)
        self.create_text(w * 0.55, h//2,
                         text=self._msg,
                         font=(FONT_MONO, 11),
                         fill=text_col, anchor="w")


# ─────────────────────────────────────────────────────────────────────────────
# Simple spin ring (clock-driven)
# ─────────────────────────────────────────────────────────────────────────────
class SpinRing(tk.Canvas):
    SZ = 44

    def __init__(self, master, clock: Clock, **kw):
        super().__init__(master, width=self.SZ, height=self.SZ,
                         highlightthickness=0, bd=0, bg=CARD, **kw)
        self._color   = CYAN
        self._visible = False
        self._angle   = 0
        clock.register(self._on_tick)

    def start(self, color=CYAN):
        self._color   = color
        self._visible = True

    def stop(self):
        self._visible = False
        self.delete("all")

    def _on_tick(self, t: float):
        if not self._visible:
            return
        self.delete("all")
        s, p = self.SZ, 6
        self._angle = (self._angle + 12) % 360
        extent = int(100 + 60 * math.sin(t * 4))
        self.create_arc(p, p, s-p, s-p, start=0, extent=359,
                        style="arc", outline=BORDER, width=4)
        self.create_arc(p, p, s-p, s-p,
                        start=self._angle, extent=extent,
                        style="arc", outline=self._color, width=4)


# ─────────────────────────────────────────────────────────────────────────────
# Pulsing run button (clock-driven)
# ─────────────────────────────────────────────────────────────────────────────
class PulseButton(ctk.CTkButton):
    def __init__(self, master, clock: Clock, **kw):
        super().__init__(master, **kw)
        self._pt = 0.0
        clock.register(self._on_tick)

    def _on_tick(self, t: float):
        v  = int(160 + 95 * abs(math.sin(t * 2.5)))
        cv = int(v * 0.45)
        col = "#{:02x}{:02x}{:02x}".format(cv, cv, v)
        try:
            self.configure(border_color=col)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Section title helper
# ─────────────────────────────────────────────────────────────────────────────
def section_title(parent, text):
    f = tk.Frame(parent, bg=PANEL)
    f.pack(fill="x", pady=(14, 6))
    tk.Label(f, text="\u25cf", bg=PANEL, fg=CYAN,
             font=(FONT_SANS, 8)).pack(side="left", padx=(0, 6))
    tk.Label(f, text=text, bg=PANEL, fg=CYAN,
             font=(FONT_MONO, 9, "bold")).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1).pack(
        side="left", fill="x", expand=True, padx=(10, 0))
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────────────────────
class ModernUI(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("VisionFit \u2014 Activity Analysis")
        self.geometry("980x760")
        self.minsize(860, 680)
        self.configure(fg_color=BG)

        self.selected_activity   = None
        self.selected_video_path = tk.StringVar()
        self.is_processing       = False

        self.activities = {
            "Jumping Jacks":    "jump_jack",
            "Flamingo Balance": "flam_bal",
            "Squats":           "squats",
            "Vertical Jumps":   "vert_jumps",
        }
        self._cards: dict[str, NeonCard] = {}

        # single master clock – ALL animations driven from here
        self._clock = Clock(self)
        self._build()

    # ── layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # Animated header
        self._header = AuroraHeader(self, self._clock, height=110)
        self._header.pack(fill="x")

        # thin separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30)

        # scrollable body
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=PANEL, corner_radius=0,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=CYAN,
        )
        self._scroll.pack(fill="both", expand=True, padx=24, pady=(8, 0))

        self._build_activity_section()
        self._build_video_section()
        self._build_run_section()
        self._build_status_section()

    # activity cards ──────────────────────────────────────────────────────────
    def _build_activity_section(self):
        section_title(self._scroll, "01   SELECT ACTIVITY")

        row = tk.Frame(self._scroll, bg=PANEL)
        row.pack(fill="x", pady=(0, 8))

        names = list(self.activities.keys())
        for i in range(len(names)):
            row.columnconfigure(i, weight=1)

        for col, name in enumerate(names):
            card = NeonCard(row, name, self._clock)
            card.grid(row=0, column=col, padx=8, pady=4, sticky="nsew")
            card.bind("<Button-1>", lambda _, n=name: self._select_activity(n))
            self._cards[name] = card

    # video selection ─────────────────────────────────────────────────────────
    def _build_video_section(self):
        section_title(self._scroll, "02   SELECT VIDEO FILE")

        row = tk.Frame(self._scroll, bg=PANEL)
        row.pack(fill="x", pady=(0, 8))
        row.columnconfigure(0, weight=1)

        self._video_entry = ctk.CTkEntry(
            row,
            textvariable=self.selected_video_path,
            placeholder_text="No video selected \u2014 click Browse to choose...",
            font=ctk.CTkFont(family=FONT_SANS, size=12),
            fg_color=CARD, border_color=BORDER,
            text_color=WHITE, placeholder_text_color=MUTED,
            height=46, state="readonly", corner_radius=12,
        )
        self._video_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            row, text="Browse", width=120, height=46,
            corner_radius=12, fg_color=CARD, hover_color=CARD_LIT,
            border_width=2, border_color=CYAN, text_color=CYAN,
            font=ctk.CTkFont(family=FONT_SANS, size=12, weight="bold"),
            command=self._browse_video,
        ).grid(row=0, column=1)

    # run button ──────────────────────────────────────────────────────────────
    def _build_run_section(self):
        section_title(self._scroll, "03   RUN ANALYSIS")

        self._run_btn = PulseButton(
            self._scroll, self._clock,
            text="\u25b6   Start Analysis",
            height=54, corner_radius=14,
            font=ctk.CTkFont(family=FONT_SERIF, size=15, weight="bold"),
            fg_color="#0F4FCC", hover_color="#0033AA",
            text_color=WHITE, border_width=2, border_color=CYAN,
            command=self._start_analysis,
        )
        self._run_btn.pack(fill="x", pady=(0, 10))

    # status ──────────────────────────────────────────────────────────────────
    def _build_status_section(self):
        section_title(self._scroll, "STATUS")

        wrap = tk.Frame(self._scroll, bg=CARD, bd=0)
        wrap.pack(fill="x", pady=(0, 16))

        self._spin = SpinRing(wrap, self._clock)
        self._spin.pack(side="left", padx=(12, 8), pady=4)

        self._status = StatusBar(wrap, self._clock)
        self._status.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

    # ── logic ─────────────────────────────────────────────────────────────────
    def _select_activity(self, name):
        self.selected_activity = name
        for n, c in self._cards.items():
            c.set_selected(n == name)

    def _browse_video(self):
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"),
                       ("All files", "*.*")]
        )
        if path:
            self.selected_video_path.set(path)

    def _start_analysis(self):
        if not self.selected_activity:
            self._flash_error("Please select an activity first")
            return
        if not self.selected_video_path.get():
            self._flash_error("Please select a video file first")
            return

        self.is_processing = True
        self._run_btn.configure(state="disabled",
                                text="\u23f3   Running...", fg_color="#0A2A6E")
        self._spin.start(CYAN)
        self._status.set_state("processing", self.selected_activity)

        threading.Thread(
            target=self._analysis_thread,
            args=(self.selected_activity, self.selected_video_path.get()),
            daemon=True,
        ).start()

    def _analysis_thread(self, act, vid):
        try:
            script_name = self.activities[act]
            out_name    = f"annotated_{os.path.basename(vid)}"
            out_path    = os.path.abspath(os.path.join("output", out_name))
            script_path = os.path.join("scripts", f"{script_name}.py")

            spec   = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            results = module.run_analysis(vid, out_path)
            self.after(0, self._on_done, out_path, results)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_done(self, out_path, results):
        self.is_processing = False
        self._run_btn.configure(state="normal",
                                text="\u25b6   Start Analysis", fg_color="#0F4FCC")
        self._spin.stop()
        self._status.set_state("success", os.path.basename(out_path))

        msg = f"Analysis finished!\nOutput saved to:\n{out_path}"
        if results:
            msg += "\n\nResults:\n" + "\n".join(f"  {k}: {v}"
                                                 for k, v in results.items())
        messagebox.showinfo("Analysis Complete", msg)
        try:
            if sys.platform == "win32":   os.startfile(out_path)
            elif sys.platform == "darwin": subprocess.run(["open", out_path])
            else:                          subprocess.run(["xdg-open", out_path])
        except Exception as e:
            print(f"Could not open output: {e}")

    def _on_error(self, err):
        self.is_processing = False
        self._run_btn.configure(state="normal",
                                text="\u25b6   Start Analysis", fg_color="#0F4FCC")
        self._spin.stop()
        self._status.set_state("error", "Analysis failed")
        messagebox.showerror("Error", f"An error occurred:\n\n{err}")

    def _flash_error(self, msg):
        self._run_btn.configure(fg_color="#7C2D12",
                                text=f"\u26a0  {msg}")
        self._status.set_state("error", msg)
        self.after(1500, lambda: self._run_btn.configure(
            fg_color="#0F4FCC", text="\u25b6   Start Analysis"))
        self.after(4000, lambda: self._status.set_state("ready"))


if __name__ == "__main__":
    app = ModernUI()
    app.mainloop()
