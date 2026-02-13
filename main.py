import tkinter as tk
from tkinter import messagebox
import pyttsx3
import sounddevice as sd
import numpy as np
import tempfile
import wave
import os

def tts_to_array(text):
    """Синтезирует речь в WAV-файл и загружает аудио в numpy-массив."""
    if not text.strip():
        return None, None, None

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
        filename = f.name

    engine.save_to_file(text, filename)
    engine.runAndWait()

    with wave.open(filename, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        sample_width = wf.getsampwidth()
        channels = wf.getnchannels()
        rate = wf.getframerate()

    os.remove(filename)

    if sample_width == 2:
        audio = np.frombuffer(frames, dtype=np.int16)
    else:
        messagebox.showerror("Ошибка", f"Unsupported sample width: {sample_width}")
        return None, None, None

    if channels == 2:
        audio = audio.reshape(-1, 2)
    else:
        audio = audio.reshape(-1, 1)

    audio = audio.astype(np.float32) / 32768.0
    return audio, rate, channels

def play_audio(audio, rate, channels, device=None):
    """Воспроизводит аудио через выбранное устройство."""
    if audio is None:
        return

    sd.play(audio, samplerate=rate, device=device)
    sd.wait()

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Озвучивание текста через аудиокабель")

        self.label = tk.Label(root, text="Введите текст:")
        self.label.pack(padx=10, pady=(10, 0))

        self.entry = tk.Entry(root, width=50)
        self.entry.pack(padx=10, pady=5)
        self.entry.focus()
        self.entry.bind("<Return>", self.speak)

        self.device_label = tk.Label(root, text="Выберите устройство вывода (виртуальный кабель):")
        self.device_label.pack(padx=10, pady=(10, 0))

        self.device_listbox = tk.Listbox(root, height=6, width=50)
        self.device_listbox.pack(padx=10, pady=5)

        self.refresh_devices()

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.speak_button = tk.Button(self.button_frame, text="Озвучить", command=self.speak)
        self.speak_button.pack(side=tk.LEFT, padx=5)

        self.refresh_button = tk.Button(self.button_frame, text="Обновить устройства", command=self.refresh_devices)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

    def refresh_devices(self):
        self.device_listbox.delete(0, tk.END)
        devices = sd.query_devices()
        self.output_devices = []
        for i, dev in enumerate(devices):
            if dev['max_output_channels'] > 0:
                name = dev['name']
                self.device_listbox.insert(tk.END, f"{i}: {name}")
                self.output_devices.append(i)
        if self.output_devices:
            self.device_listbox.selection_set(0)

    def speak(self, event=None):
        text = self.entry.get()
        if not text.strip():
            messagebox.showwarning("Внимание", "Введите текст для озвучивания.")
            return

        selected = self.device_listbox.curselection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите устройство вывода.")
            return

        device_index = self.output_devices[selected[0]]
        audio, rate, channels = tts_to_array(text)
        if audio is not None:
            try:
                play_audio(audio, rate, channels, device=device_index)
            except Exception as e:
                messagebox.showerror("Ошибка воспроизведения", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
