import os
import mido
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

# Default mapping (EZdrummer → SSD)
DEFAULT_MAPPING = {

    42: 67, 
    46: 70, 
    22: 67, 
    49: 57,  
    51: 50, 
    52: 31, 
    3: 79, 
    2: 82,
    # Additional mappings 
    66:40, #snare
    48:48, #t1
    47:47, #t2
    45:43, #t3
    43:41, #t4
    51:52, #ride
    60:65, #hh-open
    18:26, #hh-open
    62:60, #hh-semi open
    63:66, #hh-closed
    21:22, #hh-closed
    25:68, #more hh
    24:61, #hh
    55:50, #splash
    49:55, #crash L
    57:57, #crash R
    27:50, #china/splash
    28:50,
    29:31,
    30:55,
    52:31 #china
    }

def clean_sng_name(name):
    """Remove everything before @ (including @) from .sng folder names"""
    if '@' in name:
        return name.split('@')[-1]
    return name

class MIDIConverterApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("EZdrummer to SSD Batch Converter")
        self.geometry("450x650")
        self.note_map = DEFAULT_MAPPING.copy()
        self.parent_path = ""
        self.output_path = ""
        self.ezdrummer_folders = []
        self.create_widgets()

    

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="EZdrummer to SSD Batch Converter", 
                 font=('Helvetica', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        # Drag and drop area for parent folder
        ttk.Label(main_frame, text="1. Drag & Drop Parent Folder (contains EZdrummer folders):").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.input_frame = ttk.LabelFrame(main_frame, text="Parent Folder", height=60)
        self.input_frame.grid(row=2, column=0, sticky=tk.EW, padx=5, pady=5)
        self.input_frame.drop_target_register(DND_FILES)
        self.input_frame.dnd_bind('<<Drop>>', self.on_input_drop)
        
        self.input_label = ttk.Label(self.input_frame, text="Drop folder here", relief=tk.SUNKEN, wraplength=500)
        self.input_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Drag and drop area for output folder
        ttk.Label(main_frame, text="2. Drag & Drop Output Base Folder:").grid(
            row=3, column=0, sticky=tk.W, pady=5)
        
        self.output_frame = ttk.LabelFrame(main_frame, text="Output Folder", height=60)
        self.output_frame.grid(row=4, column=0, sticky=tk.EW, padx=5, pady=5)
        self.output_frame.drop_target_register(DND_FILES)
        self.output_frame.dnd_bind('<<Drop>>', self.on_output_drop)
        
        self.output_label = ttk.Label(self.output_frame, text="Drop folder here", relief=tk.SUNKEN, wraplength=500)
        self.output_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Folder list display
        ttk.Label(main_frame, text="Detected EZdrummer Folders:").grid(
            row=5, column=0, sticky=tk.W, pady=5)
        
        self.folder_listbox = tk.Listbox(main_frame, height=5)
        self.folder_listbox.grid(row=6, column=0, sticky=tk.EW, pady=5)
        
        # Mapping editor
        ttk.Label(main_frame, text="3. Note Mapping (EZdrummer → SSD):", 
                 font=('Helvetica', 10, 'bold')).grid(row=7, column=0, pady=10, sticky=tk.W)
        
        self.mapping_text = tk.Text(main_frame, height=10, width=50)
        self.mapping_text.grid(row=8, column=0, sticky=tk.NSEW)
        self.mapping_text.insert(tk.END, "\n".join(f"{k}: {v}" for k, v in self.note_map.items()))

        # Convert button
        ttk.Button(main_frame, text="Convert All MIDI Files", command=self.convert_files).grid(
            row=9, column=0, pady=20)

        # Status bar
        self.status_var = tk.StringVar(value="Drag & drop folders to begin")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(
            row=10, column=0, sticky=tk.EW)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)

    def on_input_drop(self, event):
        path = self.process_dropped_path(event.data)
        if path:
            self.parent_path = path
            self.input_label.config(text=path)
            self.find_ezdrummer_folders(path)
            
    def on_output_drop(self, event):
        path = self.process_dropped_path(event.data)
        if path:
            self.output_path = path
            self.output_label.config(text=path)
            self.update_status()

    def process_dropped_path(self, data):
        path = data.strip()
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        if os.path.isfile(path):
            path = os.path.dirname(path)
        if os.path.isdir(path):
            return os.path.normpath(path)
        return None

    def find_ezdrummer_folders(self, parent_path):
        self.ezdrummer_folders = []
        self.folder_listbox.delete(0, tk.END)
        
        try:
            for item in os.listdir(parent_path):
                full_path = os.path.join(parent_path, item)
                if os.path.isdir(full_path):
                    self.ezdrummer_folders.append(full_path)
                    self.folder_listbox.insert(tk.END, item)
            
            if not self.ezdrummer_folders:
                messagebox.showwarning("Warning", "No subfolders found in the parent directory!")
            
            self.update_status()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read folders: {e}")

    def update_status(self):
        status = []
        if self.parent_path:
            status.append(f"Input: {os.path.basename(self.parent_path)} ({len(self.ezdrummer_folders)} folders)")
        if self.output_path:
            status.append(f"Output: {self.output_path}")
        self.status_var.set(" | ".join(status) if status else "Drag & drop folders to begin")

    def update_mapping(self):
        try:
            new_map = {}
            for line in self.mapping_text.get("1.0", tk.END).splitlines():
                if line.strip():
                    k, v = map(int, line.split(":"))
                    new_map[k] = v
            self.note_map = new_map
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Invalid mapping format:\n{e}")
            return False

    def convert_files(self):
        if not self.parent_path or not self.output_path:
            messagebox.showerror("Error", "Please drag & drop both parent and output folders!")
            return
        if not self.ezdrummer_folders:
            messagebox.showerror("Error", "No EZdrummer folders found to convert!")
            return
        if not self.update_mapping():
            return

        try:
            total_converted = 0
            
            for ezdrummer_folder in self.ezdrummer_folders:
                original_name = os.path.basename(ezdrummer_folder)
                folder_name = clean_sng_name(original_name)
                converted = 0
                
                for root, dirs, files in os.walk(ezdrummer_folder):
                    for file in files:
                        if file.lower().endswith('.mid'):
                            input_path = os.path.join(root, file)
                            rel_path = os.path.relpath(root, ezdrummer_folder)
                            path_parts = rel_path.split(os.sep)
                            
                            if not path_parts or path_parts == ['.']:
                                continue
                                
                            folder1_sng = f"{folder_name}.sng"
                            folder2_prt = f"{path_parts[-1]}.prt"

                            output_dir = os.path.join(self.output_path, folder1_sng, folder2_prt)
                            os.makedirs(output_dir, exist_ok=True)
                            
                            output_path = os.path.join(output_dir, file)

                            mid = mido.MidiFile(input_path)
                            for track in mid.tracks:
                                for msg in track:
                                    if msg.type in ['note_on', 'note_off']:
                                        msg.note = self.note_map.get(msg.note, msg.note)
                            
                            mid.save(output_path)
                            converted += 1
                
                total_converted += converted
                print(f"Converted {converted} files from {original_name} → {folder_name}.sng")

            self.status_var.set(f"Done! Converted {total_converted} files total")
            messagebox.showinfo("Success", f"Batch conversion complete!\n{total_converted} files saved in:\n{self.output_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed:\n{e}")

if __name__ == "__main__":
    app = MIDIConverterApp()
    app.mainloop()