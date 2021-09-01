import tkinter as tk
from tkinter.constants import DISABLED, END, LEFT, NORMAL
from tkinter import RIGHT, BOTH, RAISED
from tkinter.ttk import Frame
from datetime import datetime, timezone


def current_time():
    date_time = (datetime.now(tz=timezone.utc))
    return date_time.isoformat()


def copy_text(text):
    if str(text):
        text = current_time() + " | " + text + "\n"
        textVar.set(text)
        txt_text.configure(state=NORMAL)
        txt_text.insert(tk.END, text)
        txt_text.configure(state=DISABLED)
        ent_entry.delete(0, 'end')  # clear the entry field


def clear_text():
    txt_text.configure(state=NORMAL)
    txt_text.delete('1.0', END)  # clear the text field
    txt_text.configure(state=DISABLED)


def save_text(text):
    window.clipboard_clear()
    window.clipboard_append(text)


def callback(entry):
    copy_text(ent_entry.get())


window = tk.Tk()
lbl_label = tk.Label(text="Case Log")
lbl_label.pack()
textVar = tk.StringVar()
textVar.set("")

ent_entry = tk.Entry(
    width="80"
)
txt_text = tk.Text(
    height="30",
    state=DISABLED
)

btn_clear = tk.Button(
    master=window,
    text="Clear",
    command=lambda: clear_text()
)

btn_main = tk.Button(
    master=window,
    text="Submit",
    command=lambda: copy_text(ent_entry.get())
)

btn_save = tk.Button(
    master=window,
    text="Save to Clipboard",
    command=lambda: save_text(txt_text.get("1.0", END))
)

lbl_label.pack()
ent_entry.pack()
frame = Frame(window, relief=RAISED, borderwidth=1)
frame.pack(fill=BOTH, expand=True)

txt_text.pack()
btn_clear.pack(side=LEFT, padx=5, pady=5)
btn_save.pack(side=RIGHT, padx=5, pady=5)
btn_main.pack(side=RIGHT, padx=5, pady=5)

ent_entry.focus_set()
window.bind('<Return>', callback)

window.mainloop()
