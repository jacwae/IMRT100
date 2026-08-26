from pathlib import Path
import tkinter as tk


# PNG-filen ligger i samme mappe som Python-programmet.
image_file = Path(__file__).with_name(
    "8360f877-71f0-41d4-8866-5b236ddb9d23.png"
)

if not image_file.is_file():
    raise FileNotFoundError(f"Fant ikke PNG-filen: {image_file}")


# Vis bildet på hele robotskjermen.
window = tk.Tk()
image = tk.PhotoImage(file=str(image_file))

window.attributes("-fullscreen", True)
window.configure(background="black")
window.bind("<Escape>", lambda event: window.destroy())

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# Behold størrelsesforholdet når bildet tilpasses skjermen.
scale_x = max(1, (image.width() + screen_width - 1) // screen_width)
scale_y = max(1, (image.height() + screen_height - 1) // screen_height)
scale = max(scale_x, scale_y)
if scale > 1:
    image = image.subsample(scale, scale)

label = tk.Label(window, image=image, background="black")
label.pack(expand=True)

window.mainloop()
