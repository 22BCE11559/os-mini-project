import os, json, base64
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from datetime import datetime
from cryptography.fernet import Fernet

BASE = os.path.dirname(__file__)

def log(msg):
    with open(os.path.join(BASE,"logs.txt"),"a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def load_json(name):
    path = os.path.join(BASE,name)
    if not os.path.exists(path): return {}
    with open(path) as f: return json.load(f)

def save_json(name,data):
    with open(os.path.join(BASE,name),"w") as f:
        json.dump(data,f,indent=4)

users = load_json("users.json")
files = load_json("files.json")

def register():
    u = simpledialog.askstring("Register","Username")
    p = simpledialog.askstring("Register","Password",show="*")
    if u in users:
        messagebox.showerror("Error","User exists"); return
    key = Fernet.generate_key().decode()
    users[u]={"password":p,"role":"user","key":key}
    save_json("users.json",users)
    log(f"{u} REGISTERED")
    messagebox.showinfo("OK","Registered")

def login():
    u = simpledialog.askstring("Login","Username")
    p = simpledialog.askstring("Login","Password",show="*")
    if u in users and users[u]["password"]==p:
        log(f"{u} LOGIN")
        dashboard(u)
    else:
        messagebox.showerror("Error","Invalid")

def encrypt_file(src, dst, key):
    f = Fernet(key.encode())
    with open(src,"rb") as fi:
        data = fi.read()
    enc = f.encrypt(data)
    with open(dst,"wb") as fo:
        fo.write(enc)

def decrypt_file(src, key):
    f = Fernet(key.encode())
    with open(src,"rb") as fi:
        data = fi.read()
    return f.decrypt(data)

def upload(user):
    path = filedialog.askopenfilename()
    if not path: return
    name = os.path.basename(path)
    user_dir = os.path.join(BASE,"storage",user)
    os.makedirs(user_dir,exist_ok=True)
    dest = os.path.join(user_dir,name+".enc")
    encrypt_file(path,dest,users[user]["key"])
    files[name]={"owner":user,"shared":[]}
    save_json("files.json",files)
    log(f"{user} uploaded {name}")
    messagebox.showinfo("OK","Encrypted & stored")

def share(user):
    fname = simpledialog.askstring("Share","File name")
    target = simpledialog.askstring("Share","Share with user")
    if fname in files and files[fname]["owner"]==user:
        files[fname]["shared"].append(target)
        save_json("files.json",files)
        log(f"{user} shared {fname} with {target}")
        messagebox.showinfo("OK","Shared")
    else:
        messagebox.showerror("Error","Not allowed")

def download(user):
    fname = simpledialog.askstring("Download","File name")
    if fname not in files:
        messagebox.showerror("Error","No file"); return

    info = files[fname]
    if user!=info["owner"] and user not in info["shared"]:
        messagebox.showerror("Denied","No access"); return

    owner = info["owner"]
    path = os.path.join(BASE,"storage",owner,fname+".enc")

    data = decrypt_file(path, users[owner]["key"])
    save = filedialog.asksaveasfilename(defaultextension=".txt")
    if save:
        with open(save,"wb") as f: f.write(data)
        log(f"{user} downloaded {fname}")
        messagebox.showinfo("OK","Decrypted")

def view_logs():
    with open(os.path.join(BASE,"logs.txt")) as f:
        messagebox.showinfo("Logs",f.read())

def dashboard(user):
    win = tk.Toplevel()
    win.title(user)

    tk.Button(win,text="Upload",command=lambda:upload(user)).pack(pady=5)
    tk.Button(win,text="Download",command=lambda:download(user)).pack(pady=5)
    tk.Button(win,text="Share",command=lambda:share(user)).pack(pady=5)

    if users[user]["role"]=="admin":
        tk.Button(win,text="View Logs",command=view_logs).pack(pady=5)

root = tk.Tk()
root.title("Secure System")

tk.Button(root,text="Register",command=register,width=20).pack(pady=10)
tk.Button(root,text="Login",command=login,width=20).pack(pady=10)

root.mainloop()