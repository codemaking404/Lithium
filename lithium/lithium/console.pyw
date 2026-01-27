import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import webbrowser
import urllib.request
import os
import time
import sys
import random
import threading

class DualWindowConsole:
    def __init__(self, startup_file=None):
        # Variables and buffers
        self.vars = {}
        self.list_buffer = []
        self.in_list = False
        self.history = []
        self.history_index = -1
        self.plugins = {}
        self.plugin_help = {}
        self.snapshot_history = []
        self.stop_autosave = False
        self.notes = []

        # --- New State Flags ---
        self.linked_lang = None
        self.quit_flag = False

        # --- Help descriptions ---
        self.help_docs = {
            "help": "Usage: help [command]. Shows general or detailed help about a command.",
            "input": "Opens an input dialog and captures text.",
            "export": "Usage: export <file>. Saves console text to a file.",
            "import": "Usage: import <file>. Loads a file and prints its contents.",
            "website": "Usage: website <url>. Opens the given website in a browser.",
            "request": "Usage: request <url>. Fetches a webpage and prints status + preview.",
            "vars": "Prints all currently stored variables.",
            "clear": "Clears the output window.",
            "exit": "Closes Lithium.",
            "quit": "Stops the currently running .lit script.",
            "time": "Prints the current time.",
            "math": "Usage: math <expression>. Evaluates a math expression.",
            "run": "Usage: run <file.lit>. Executes a Lithium script file.",
            "list": "List block system. {list:start}...{list:end} wraps multiple commands.",
            "chain": "Chain block system. [chain_start]... [chain_end_loop_number=n] loops commands.",
            "window.create": "Creates a new window for text display/editing.",
            "edit_window_contents": "Usage: edit_window_contents(text='...', allow_text_editing=True/False).",
            "colors": "Changes console foreground/background colors.",
            "undo": "Undoes the last console output change.",
            "random": "Usage: random <min> <max>. Generates a random integer.",
            "credits": "Shows Lithium credits.",
            "version": "Shows Lithium version.",
            "command_add": "Adds a custom command inside a .lit file.",
            "lithium_help_add": "Adds custom help text for a plugin or command.",
            "delete plugin": "Usage: delete plugin (<name>). Removes a plugin from Lithium.",
            "plugin info": "Usage: plugin info (<name>). Shows information about a loaded plugin.",
            "gate": "Logic gates. Usage: gate <and/or/xor/not> <values>.",
            "note": "Usage: note <text>. Saves text into notes.",
            "note_load": "Loads all saved notes into the output.",
            "note_clear": "Clears all saved notes.",
            "anote": "Acts like print inside .lit files, saves note text.",
            "link": "Usage: link <language>. Example: link python. Routes future code to that language."
        }

        # --- Output Window ---
        self.output_window = tk.Tk()
        self.output_window.overrideredirect(True)  # Remove OS borders
        self.output_window.title("Lithium Output")

        # ✅ Drag support
        def start_move(event):
            self._x = event.x
            self._y = event.y

        def stop_move(event):
            self._x = None
            self._y = None

        def do_move(event, window=self.output_window):
            deltax = event.x - self._x
            deltay = event.y - self._y
            x = window.winfo_x() + deltax
            y = window.winfo_y() + deltay
            window.geometry(f"+{x}+{y}")

        # Green outer border
        outer_frame = tk.Frame(self.output_window, bg="green", bd=4)
        outer_frame.pack(fill=tk.BOTH, expand=True)

        # Black inner border
        inner_frame = tk.Frame(outer_frame, bg="black")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Bind drag movement
        outer_frame.bind("<Button-1>", start_move)
        outer_frame.bind("<ButtonRelease-1>", stop_move)
        outer_frame.bind("<B1-Motion>", do_move)

        # ✅ Set icon for output window
        try:
            self.output_window.iconbitmap("lithium.ico")
        except Exception:
            try:
                icon = tk.PhotoImage(file="lithium.png")
                self.output_window.iconphoto(False, icon)
            except:
                pass

        self.output_text = ScrolledText(
            inner_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            state='disabled',
            bg="black",
            fg="lime"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # --- Console Window ---
        self.console_window = tk.Toplevel(self.output_window)
        self.console_window.overrideredirect(True)
        self.console_window.title("Lithium Console")

        # ✅ Drag support for console
        def do_move_console(event, window=self.console_window):
            deltax = event.x - self._x
            deltay = event.y - self._y
            x = window.winfo_x() + deltax
            y = window.winfo_y() + deltay
            window.geometry(f"+{x}+{y}")

        outer_frame2 = tk.Frame(self.console_window, bg="green", bd=4)
        outer_frame2.pack(fill=tk.BOTH, expand=True)

        inner_frame2 = tk.Frame(outer_frame2, bg="black")
        inner_frame2.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        outer_frame2.bind("<Button-1>", start_move)
        outer_frame2.bind("<ButtonRelease-1>", stop_move)
        outer_frame2.bind("<B1-Motion>", do_move_console)

        try:
            self.console_window.iconbitmap("lithium.ico")
        except Exception:
            try:
                icon2 = tk.PhotoImage(file="lithium.png")
                self.console_window.iconphoto(False, icon2)
            except:
                pass

        self.console_text = ScrolledText(
            inner_frame2,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="black",
            fg="lime",
            insertbackground="lime"
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        self.console_text.focus_set()

        # Bind keys
        self.console_text.bind("<Return>", self.execute_command)
        self.console_text.bind("<Up>", self.prev_history)
        self.console_text.bind("<Down>", self.next_history)
        self.console_text.bind("<Key>", self.check_cursor)

        # Prompt
        self.prompt = "> "
        self.console_text.insert(tk.END, self.prompt)
        self.input_start = self.console_text.index(tk.INSERT)

        # Load plugins
        self.load_plugins_and_bootup()

        # Autosave snapshots
        threading.Thread(target=self.autosave_snapshots, daemon=True).start()

        # Auto-run startup .lit
        if startup_file and startup_file.endswith(".lit") and os.path.exists(startup_file):
            self.run_line(f"run {startup_file}")

    # --- Printing ---
    def print_output(self, text, type="normal"):
        self.output_text.config(state='normal')
        tag = None
        if type == "error":
            tag = "error"
        elif type == "info":
            tag = "info"
        self.output_text.insert(tk.END, str(text) + "\n", tag)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

    # --- Cursor protect ---
    def check_cursor(self, event):
        cursor_index = self.console_text.index(tk.INSERT)
        if self.console_text.compare(cursor_index, "<", self.input_start):
            self.console_text.mark_set(tk.INSERT, self.input_start)
        return None

    # --- Execute command ---
    def execute_command(self, event):
        line_start = self.input_start
        line_end = self.console_text.index(tk.END + "-1c")
        full_command = self.console_text.get(line_start, line_end).strip()
        self.console_text.insert(tk.END, "\n")

        if full_command:
            self.history.append(full_command)
            self.history_index = len(self.history)
            self.run_line(full_command)

        self.print_prompt()
        return "break"

    # --- Run a line ---
    def run_line(self, line):
        local_vars = self.vars.copy()
        local_vars['print'] = self.print_output

        stripped_line = line.strip().replace(" ", "")
        if stripped_line.lower() in ['cake="lie"', "cake='lie'"]:
            self.vars['cake'] = "lie"
            self.print_output("The cake is a lie", "info")
            return

        parts = line.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            # --- New Commands ---
            if cmd == "quit":
                self.quit_flag = True
                self.print_output("Quit signal received. Stopping execution.", "info")
                return

            elif cmd == "exit":
                self.print_output("Exiting Lithium...", "info")
                self.stop_autosave = True
                self.output_window.destroy()
                return

            elif cmd == "link":
                if not args:
                    self.print_output("Usage: link <language>", "error")
                else:
                    lang = args[0].lower()
                    if lang == "python":
                        self.linked_lang = "python"
                        self.print_output("Linked to Python. You can now run Python code directly.", "info")
                    else:
                        self.print_output(f"Unsupported link: {lang}", "error")
                return

            elif cmd == "run":
                if not args:
                    self.print_output("Usage: run <file.lit>", "error")
                    return
                filepath = args[0]
                if not os.path.exists(filepath):
                    self.print_output(f"File not found: {filepath}", "error")
                    return
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                self.quit_flag = False
                for raw_line in lines:
                    if self.quit_flag:
                        break
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.lower().startswith("bootup:"):
                        code = line[len("bootup:"):].strip()
                        self.run_line(code)
                        continue
                    if line.lower().startswith("plug:"):
                        plugname = line[len("plug:"):].strip()
                        self.plugins[plugname] = f"# plugin placeholder for {plugname}"
                        self.plugin_help[plugname] = "Custom plugin loaded from .lit file."
                        self.print_output(f"Plugin loaded: {plugname}", "info")
                        continue
                    self.run_line(line)
                return

            # --- If linked to Python ---
            elif self.linked_lang == "python":
                try:
                    result = eval(line, {}, local_vars)
                    if result is not None:
                        self.print_output(result)
                    self.vars.update(local_vars)
                except SyntaxError:
                    try:
                        exec(line, {}, local_vars)
                        self.vars.update(local_vars)
                    except Exception as e:
                        self.print_output(f"Python error: {e}", "error")
                except Exception as e:
                    self.print_output(f"Python error: {e}", "error")
                return

            # --- Built-in Commands ---
            elif cmd == "help":
                if args:
                    key = args[0].lower()
                    if key in self.help_docs:
                        self.print_output(self.help_docs[key], "info")
                    elif key in self.plugins:
                        help_text = self.plugin_help.get(key, "This command is meant for .lit files")
                        self.print_output(help_text, "info")
                    else:
                        self.print_output(f"No detailed help for '{key}'", "error")
                else:
                    all_cmds = sorted(set(list(self.help_docs.keys()) + list(self.plugins.keys())))
                    self.print_output("Commands: " + ", ".join(all_cmds), "info")
                    self.print_output("You can type help <command> for more information.", "info")

            elif cmd == "credits":
                self.print_output("Lithium Console by Maddox Sjogren!", "info")

            elif cmd == "version":
                self.print_output("Lithium v1.0.0", "info")

            elif cmd == "note":
                if not args:
                    self.print_output("Usage: note <text>", "error")
                else:
                    text = " ".join(args)
                    self.notes.append(text)
                    self.print_output(f"Note saved: {text}")

            elif cmd == "note_load":
                if not self.notes:
                    self.print_output("No notes saved.", "error")
                else:
                    for note in self.notes:
                        self.print_output(note)

            elif cmd == "note_clear":
                self.notes.clear()
                self.print_output("All notes cleared.", "info")

            elif cmd == "random":
                if len(args) != 2:
                    self.print_output("Usage: random <min> <max>", "error")
                else:
                    try:
                        r = random.randint(int(args[0]), int(args[1]))
                        self.print_output(f"Random: {r}")
                    except:
                        self.print_output("Invalid range", "error")

            elif cmd == "colors":
                fg = args[0] if len(args) > 0 else "lime"
                bg = args[1] if len(args) > 1 else "black"
                self.console_text.config(fg=fg, bg=bg, insertbackground=fg)
                self.output_text.config(fg=fg, bg=bg)

            else:
                if cmd in self.plugins:
                    try:
                        exec(self.plugins[cmd], {}, {"args": args, "print": self.print_output})
                    except Exception as e:
                        self.print_output(f"Plugin error: {e}", "error")
                else:
                    try:
                        result = eval(line, {}, local_vars)
                        if result is not None:
                            self.print_output(result)
                        self.vars.update(local_vars)
                    except SyntaxError:
                        try:
                            exec(line, {}, local_vars)
                            self.vars.update(local_vars)
                        except Exception as e:
                            self.print_output(f"Error: {e}", "error")
                    except Exception as e:
                        self.print_output(f"Error: {e}", "error")

        except Exception as e:
            self.print_output(f"Error: {e}", "error")

    # --- Prompt ---
    def print_prompt(self):
        self.console_text.insert(tk.END, self.prompt)
        self.console_text.see(tk.END)
        self.input_start = self.console_text.index(tk.END + "-1c")

    # --- History navigation ---
    def prev_history(self, event):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            self.replace_input(self.history[self.history_index])
        return "break"

    def next_history(self, event):
        if self.history:
            self.history_index = min(len(self.history) - 1, self.history_index + 1)
            self.replace_input(self.history[self.history_index])
        return "break"
    # --- Plugins / bootup loader ---
    def load_plugins_and_bootup(self):
        plugin_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Lithium Plugins")
        if not os.path.exists(plugin_folder):
            os.makedirs(plugin_folder)
            self.print_output("Created Lithium Plugins folder.", "info")

        for file in os.listdir(plugin_folder):
            if not file.endswith(".lit"):
                continue

            filepath = os.path.join(plugin_folder, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if not lines:
                    continue

                first_line = lines[0].strip().lower()

                # Bootup file → run every line inside
                if first_line.startswith("bootup:"):
                    self.print_output(f"Booting up from {file}...", "info")
                    self.quit_flag = False
                    for raw_line in lines:
                        if self.quit_flag:
                            break
                        line = raw_line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.lower().startswith("bootup:"):
                            # skip the bootup: prefix itself
                            continue
                        self.run_line(line)

                # Plugin file → register but don't execute
                elif first_line.startswith("plug:"):
                    plugname = first_line[len("plug:"):].strip()
                    with open(filepath, "r", encoding="utf-8") as f:
                        plugin_code = f.read()
                    self.plugins[plugname] = plugin_code
                    self.plugin_help[plugname] = "Custom plugin loaded from Lithium Plugins folder."
                    self.print_output(f"Plugin registered: {plugname}", "info")

            except Exception as e:
                self.print_output(f"Failed to load {file}: {e}", "error")

    def replace_input(self, text):
        self.console_text.delete(self.input_start, tk.END)
        self.console_text.insert(tk.END, text)

    # --- Plugins / bootup loader ---
    def load_plugins_and_bootup(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(folder):
            if file.endswith(".lit"):
                filepath = os.path.join(folder, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content.startswith("exec"):
                        self.run_line(f"run {filepath}")
                    elif content.startswith("plug"):
                        self.print_output(f"Loaded plugin: {file}", "info")
                except Exception as e:
                    self.print_output(f"Failed to load {file}: {e}", "error")

    # --- Autosave snapshots ---
    def autosave_snapshots(self):
        while not self.stop_autosave:
            time.sleep(5)
            self.output_text.config(state='normal')
            snapshot = self.output_text.get("1.0", tk.END)
            self.snapshot_history.append(snapshot)
            self.output_text.config(state='disabled')

    # --- Run loop ---
    def run(self):
        self.print_prompt()
        self.output_window.mainloop()
        self.stop_autosave = True


if __name__ == "__main__":
    startup_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = DualWindowConsole(startup_file)
    app.run()
