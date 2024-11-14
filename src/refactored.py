import os
import tkinter as tk
from datetime import datetime
from functools import partial
from sys import platform
import shutil
import threading
from cryptography.fernet import Fernet
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.dialogs.dialogs import Querybox
import psutil
import pymysql

# Global variables
global file_path
file_path = os.path.join(os.path.dirname(__file__), "../icons/")
Encryption_Password = ""

class DatabaseManager:
    def __init__(self):
        self.con = pymysql.connect(
            host='localhost',
            user='root',
            password='mysql'
        )
        self.myc = self.con.cursor()
        self.initialize_database()

    def initialize_database(self):
        self.myc.execute("show databases")
        out1 = self.myc.fetchall()
        if ("explora",) not in out1:
            self.myc.execute("create database Explora")
        self.myc.execute("use explora")
        self.myc.execute("create table if not exists encrypted(File varchar(255), EnKey varchar(255))")
        self.con.commit()

    def close_connection(self):
        self.con.close()

    def insert_encrypted_file(self, file_path, key):
        self.myc.execute("insert into encrypted values(%s, %s)", (file_path, key))
        self.con.commit()

    def get_encrypted_key(self, file_path):
        self.myc.execute("SELECT EnKey FROM encrypted WHERE File = %s", (file_path,))
        return self.myc.fetchone()

    def delete_encrypted_file(self, file_path):
        self.myc.execute("delete from encrypted where file=%s", (file_path,))
        self.con.commit()

class SystemMonitor:
    @staticmethod
    def get_drives():
        if platform == "win32":
            return [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
        elif platform == "linux":
            return ["/"]

    @staticmethod
    def get_drive_stats(drive):
        usage = psutil.disk_usage(drive)
        total_gb = round(usage.total / (1024 * 1024 * 1024))
        used_gb = round(usage.used / (1024 * 1024 * 1024))
        return total_gb, used_gb

    @staticmethod
    def get_cpu_stats():
        return psutil.cpu_count(), psutil.cpu_count(logical=False), psutil.cpu_percent(), psutil.cpu_freq().current

    @staticmethod
    def get_memory_stats():
        mem = psutil.virtual_memory()
        return mem.total, mem.available, mem.percent, mem.used

    @staticmethod
    def get_network_stats():
        return psutil.net_io_counters(pernic=True)

    @staticmethod
    def get_processes():
        return [p for p in psutil.process_iter(['name', 'pid', 'status', 'memory_info'])]

class UIManager:
    def __init__(self, file_explorer):
        self.file_explorer = file_explorer
        self.root = None
        self.items = None
        self.cwdLabel = None
        self.footer = None
        self.photo_ref = []
        self.theme = ""
        self.font_size = "10"
        self.style = ttk.Style()

    def create_window(self):
        self.root = ttk.Window(themename=self.theme)
        self.root.title("Explora")
        self.root.geometry("1280x720")
        self.root.resizable(True, True)
        icon_image = ImageTk.PhotoImage(Image.open(file_path+ "icon.png"))
        self.root.iconphoto(False, icon_image)
        return self.root
    

    def create_widgets(self):
        # Browse Frame
        browseFrame = ttk.Frame(self.root)
        scroll = ttk.Scrollbar(browseFrame, orient="vertical")
        self.items = ttk.Treeview(
            browseFrame,
            columns=("Name", "Date modified", "Type", "Size"),
            yscrollcommand=scroll.set,
            height=15,
            style="Custom.Treeview",
        )
        scroll.config(command=self.items.yview)  # scroll with mouse drag
        # --Browse Frame

        # Footer Frame
        footerFrame = ttk.Frame(self.root)
        self.footer = ttk.Label(footerFrame)
        grip = ttk.Sizegrip(footerFrame, bootstyle="default")
        # --Footer Frame

        folderIcon = tk.PhotoImage(file=file_path + "Folder-icon.png", width=20, height=16)
        fileIcon = tk.PhotoImage(file=file_path + "File-icon.png", width=20, height=16)

        # Header Frame
        refreshIcon = tk.PhotoImage(file=file_path + "Very-Basic-Reload-icon.png")
        backArrowIcon = tk.PhotoImage(file=file_path + "Arrows-Back-icon.png")
        frontArrowIcon = tk.PhotoImage(file=file_path + "Arrows-Front-icon.png")
        headerFrame = ttk.Frame()
        self.cwdLabel = ttk.Label(
            headerFrame,
            text=" " + os.getcwd(),
            relief="flat",
            # width=110,
        )
        searchEntry = ttk.Entry(headerFrame, width=30, font=("TkDefaultFont", self.font_size))
        searchEntry.insert(0, "Search files..")
        searchEntry.bind("<Button-1>", partial(self.click, searchEntry))
        searchEntry.bind("<FocusOut>", partial(self.focus_out, searchEntry, self.root))
        backButton = ttk.Button(
            headerFrame,
            image=backArrowIcon,
            command=self.file_explorer.previous,
            bootstyle="light",
        )
        forwardButton = ttk.Button(
            headerFrame,
            image=frontArrowIcon,
            command=self.file_explorer.next,
            bootstyle="light",
        )
        refreshButton = ttk.Button(
            headerFrame,
            command=partial(self.file_explorer.refresh, []),
            image=refreshIcon,
            bootstyle="light",
        )

        # tooltips for buttons
        ToolTip(backButton, text="Back", bootstyle=("default", "inverse"))
        ToolTip(forwardButton, text="Forward", bootstyle=("default", "inverse"))
        ToolTip(refreshButton, text="Refresh", bootstyle=("default", "inverse"))
        # --Header Frame

        # imgs
        open_img = Image.open(file_path + "icon.png")
        open_photo = ImageTk.PhotoImage(open_img)

        refresh_img = Image.open(file_path + "Very-Basic-Reload-icon.png")
        refresh_photo = ImageTk.PhotoImage(refresh_img)

        rename_img = Image.open(file_path + "rename.png")
        rename_photo = ImageTk.PhotoImage(rename_img)

        drive_img = Image.open(file_path + "drive.png")
        drive_photo = ImageTk.PhotoImage(drive_img)

        info_img = Image.open(file_path + "info.png")
        info_photo = ImageTk.PhotoImage(info_img)

        pie_img = Image.open(file_path + "pie.png")
        pie_photo = ImageTk.PhotoImage(pie_img)

        cpu_img = Image.open(file_path + "cpu.png")
        cpu_photo = ImageTk.PhotoImage(cpu_img)

        memory_img = Image.open(file_path + "memory.png")
        memory_photo = ImageTk.PhotoImage(memory_img)

        network_img = Image.open(file_path + "network.png")
        network_photo = ImageTk.PhotoImage(network_img)

        process_img = Image.open(file_path + "process.png")
        process_photo = ImageTk.PhotoImage(process_img)

        file_img = Image.open(file_path + "File-icon.png")
        file_photo = ImageTk.PhotoImage(file_img)

        dir_img = Image.open(file_path + "Folder-icon.png")
        dir_photo = ImageTk.PhotoImage(dir_img)

        themes_img = Image.open(file_path + "themes.png")
        themes_photo = ImageTk.PhotoImage(themes_img)

        scale_img = Image.open(file_path + "scale.png")
        scale_photo = ImageTk.PhotoImage(scale_img)

        font_img = Image.open(file_path + "font.png")
        font_photo = ImageTk.PhotoImage(font_img)

        copy_img = Image.open(file_path + "copy.png")
        copy_photo = ImageTk.PhotoImage(copy_img)

        paste_img = Image.open(file_path + "paste.png")
        paste_photo = ImageTk.PhotoImage(paste_img)

        delete_img = Image.open(file_path + "delete.png")
        delete_photo = ImageTk .PhotoImage(delete_img)

        encrypt_img = Image.open(file_path + "encrypt.png")
        encrypt_photo = ImageTk.PhotoImage(encrypt_img)

        decrypt_img = Image.open(file_path + "decrypt.png")
        decrypt_photo = ImageTk.PhotoImage(decrypt_img)

        # Right click menu
        m = ttk.Menu(self.root, tearoff=False, font=("TkDefaultFont", self.font_size))
        m.add_command(
            label="Open",
            image=open_photo,
            compound="left",
            command=self.file_explorer.on_double_click,
        )
        m.add_separator()
        m.add_command(
            label="New file", image=file_photo, compound="left", command=self.file_explorer.new_file_popup
        )
        m.add_command(
            label="New directory", image=dir_photo, compound="left", command=self.file_explorer.new_dir_popup
        )
        m.add_separator()
        m.add_command(
            label="Copy Selected",
            image=copy_photo,
            compound="left",
            command=self.file_explorer.copy,
        )
        m.add_command(
            label="Paste Selected", image=paste_photo, compound="left", command=self.file_explorer.paste
        )
        m.add_command(
            label="Delete selected",
            image=delete_photo,
            compound="left",
            command=self.file_explorer.del_file_popup,
        )
        m.add_command(
            label="Rename selected",
            image=rename_photo,
            compound="left",
            command=self.file_explorer.rename_popup,
        )
        m.add_separator()
        m.add_command(
            label="Encrypt selected",
            image=encrypt_photo,
            compound="left",
            command=self.file_explorer.encrypt_file_popup,
        )
        m.add_command(
            label="Decrypt selected",
            image=decrypt_photo,
            compound="left",
            command=self.file_explorer.decrypt_file_popup,
        )
        m.add_separator()
        m.add_command(
            label="Refresh",
            image=refresh_photo,
            compound="left",
            command=partial(self.file_explorer.refresh, []),
        )
        # --Right click menu

        self.style.configure(".", font=("TkDefaultFont", self.font_size))  # set font size
        self.style.configure("Treeview", rowheight=28)  # customize treeview
        self.style.configure(
            "Treeview.Heading", font=("TkDefaultFont", str(int(self.font_size) + 1), "bold")
        )
        self.style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])  # remove borders

        self.items.column("#0", width=40, stretch=tk.NO)
        self.items.column("Name", anchor=tk.W, width=150, minwidth=120)
        self.items.column("Date modified", anchor=tk.CENTER, width=200, minwidth=120)
        self.items.column("Size", anchor=tk.CENTER, width=80, minwidth=60)
        self.items.column("Type", anchor=tk.CENTER, width=120, minwidth=60)
        self.items.heading(
            "Name",
            text="Name",
            anchor=tk.CENTER,
            command=partial(self.file_explorer.sort_col, "Name", False),
        )
        self.items.heading(
            "Date modified",
            text="Date modified",
            anchor=tk.CENTER,
            command=partial(self.file_explorer.sort_col, "Date modified", False),
        )
        self.items.heading(
            "Type",
            text="Type",
            anchor=tk.CENTER,
            command=partial(self.file_explorer.sort_col, "Type", False),
        )
        self.items.heading(
            "Size",
            text="Size",
            anchor=tk.CENTER,
            command=partial(self.file_explorer.sort_col, "Size", False),
        )
        self.items.bind(
            "<Double-1>",
            self.file_explorer.on_double_click,
        )  # command on double click
        self.items.bind("<ButtonRelease-1>", self.file_explorer.select_item)
        self.items.bind("<Button-3>", partial(self.file_explorer.on_right_click, m))  # command on right click
        self.items.bind("<Up>", self.file_explorer.up_key)  # bind up arrow key
        self.items.bind("<Down>", self.file_explorer.down_key)  # bind down arrow key
        # --Browse Frame

        # Menu bar
        bar = ttk.Menu(self.root, font=("TkDefaultFont", self.font_size))
        self.root.config(menu=bar)

        file_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        file_menu.add_command(
            label="Open",
            image=open_photo,
            compound="left",
            command=self.file_explorer.on_double_click,
        )
        file_menu.add_command(
            label="New file",
            image=file_photo,
            compound="left",
            command=self.file_explorer.new_file_popup,
        )
        file_menu.add_command(
            label="New directory", image=dir_photo, compound="left", command=self.file_explorer.new_dir_popup
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Copy Selected",
            image=copy_photo,
            compound="left",
            command=self.file_explorer.copy,
        )
        file_menu.add_command(
            label="Paste Selected", image=paste_photo, compound="left", command=self.file_explorer.paste
        )
        file_menu.add_command(
            label="Delete selected",
            image=delete_photo,
            compound="left",
            command=self.file_explorer.del_file_popup,
        )
        file_menu.add_command(
            label="Rename selected",
            image=rename_photo,
            compound="left",
            command=self.file_explorer.rename_popup,
        )
        file_menu.add_command(
            label="Encrypt selected",
            image=encrypt_photo,
            compound="left",
            command=self.file_explorer.encrypt_file_popup,
        )
        file_menu.add_command(
            label="Decrypt selected",
            image=decrypt_photo,
            compound="left",
            command=self.file_explorer.decrypt_file_popup,
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        drives_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        for drive in SystemMonitor.get_drives():
            drives_menu.add_command(
                label=drive,
                image=drive_photo,
                compound="left",
                command=partial(self.file_explorer.cd_drive, drive, []),
            )

        system_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        system_menu.add_command(
            label="Drives",
            image=pie_photo,
            compound="left",
            command=partial(self.file_explorer.drive_stats, self.root),
        )
        system_menu.add_command(
            label="CPU", image=cpu_photo, compound="left", command=self.file_explorer.cpu_stats
        )
        system_menu.add_command(
            label="Memory", image=memory_photo, compound="left", command=self.file_explorer.memory_stats
        )
        system_menu.add_command(
            label="Network", image=network_photo, compound="left", command=self.file_explorer.network_stats
        )
        system_menu.add_command(
            label="Processes",
            image=process_photo,
            compound="left",
            command=partial(self.file_explorer.processes_win, self.root),
        )

        sub_themes = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        sub_themes.add_command(label="Darkly", command=partial(self.write_theme, "darkly"))
        sub_themes.add_command(label="Solar Dark", command=partial(self.write_theme, "solar"))
        sub_themes.add_command(
            label="Superhero Dark", command=partial(self.write_theme, "superhero")
        )
        sub_themes.add_command(label="Cyborg Dark", command=partial(self.write_theme, "cyborg"))
        sub_themes.add_command(label="Vapor Dark", command=partial(self.write_theme, "vapor"))
        sub_themes.add_separator()
        sub_themes.add_command(label="Litera Light", command=partial(self.write_theme, "litera"))
        sub_themes.add_command(label="Minty Light", command=partial(self.write_theme, "minty"))
        sub_themes.add_command(label="Morph Light", command=partial(self.write_theme, "morph"))
        sub_themes.add_command(label="Yeti Light", command=partial(self.write_theme, "yeti"))

        sub_font_size = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        sub_font_size.add_command(label="14", command=partial(self.change_font_popup, 14))
        sub_font_size.add_command(label="12", command=partial(self.change_font_popup, 12))
        sub_font_size.add_command(label="11", command=partial(self.change_font_popup, 11))
        sub_font_size.add_command(
            label="10 - default", command=partial(self.change_font_popup, 10)
        )
        sub_font_size.add_command(label="9", command=partial(self.change_font_popup, 9))
        sub_font_size.add_command(label="8", command=partial(self.change_font_popup, 8))
        sub_font_size.add_command(label="7", command=partial(self.change_font_popup, 7))

        sub_scale = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        sub_scale.add_command(label="150%", command=partial(self.change_scale, 1.5))
        sub_scale.add_command(label="125%", command=partial(self.change_scale, 1.25))
        sub_scale.add_command(label="100%", command=partial(self.change_scale, 1.0))
        sub_scale.add_command (label="75%", command=partial(self.change_scale, 0.75))
        sub_scale.add_command(label="50%", command=partial(self.change_scale, 0.5))

        preferences_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        preferences_menu.add_cascade(
            label="Themes", image=themes_photo, compound="left", menu=sub_themes
        )
        preferences_menu.add_cascade(
            label="Scale", image=scale_photo, compound="left", menu=sub_scale
        )
        preferences_menu.add_cascade(
            label="Font size", image=font_photo, compound="left", menu=sub_font_size
        )

        help_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        help_menu.add_command(
            label="Keybinds", image=info_photo, compound="left", command=self.file_explorer.keybinds
        )

        help_menu.add_command(
            label="Know Encryption Key", command=self.file_explorer.encryption_popup, image=info_photo, compound="left"
        )

        help_menu.add_command(
            label="Change Encryption Key", command=self.file_explorer.change_encryption_popup, image=info_photo, compound="left"
        )

        about_menu = ttk.Menu(bar, tearoff=False, font=("TkDefaultFont", self.font_size))
        about_menu.add_command(
            label="About the app", command=self.file_explorer.about_popup, image=info_photo, compound="left"
        )

        bar.add_cascade(label="File", menu=file_menu, underline=0)
        bar.add_cascade(label="Drives", menu=drives_menu, underline=0)
        bar.add_cascade(label="System", menu=system_menu, underline=0)
        bar.add_cascade(label="Preferences", menu=preferences_menu, underline=0)
        bar.add_cascade(label="Help", menu=help_menu, underline=0)
        bar.add_cascade(label="About", menu=about_menu, underline=0)
        # --Menu bar

        # packs
        scroll.pack(side=tk.RIGHT, fill=tk.BOTH)
        backButton.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH)
        forwardButton.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH)
        self.cwdLabel.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH, expand=True)
        refreshButton.pack(side=tk.LEFT, padx=1, pady=10, fill=tk.BOTH)
        searchEntry.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.BOTH)
        grip.pack(side=tk.RIGHT, fill=tk.BOTH, padx=2, pady=2)

        headerFrame.pack(fill=tk.X)
        browseFrame.pack(fill=tk.BOTH, expand=True)
        footerFrame.pack(side=tk.BOTTOM, fill=tk.BOTH)

        searchEntry.bind(
            "<Return>",
            partial(self.file_explorer.search, searchEntry),
        )  # on enter press, run search1

        # img references
        self.photo_ref.append(backArrowIcon)
        self.photo_ref.append(frontArrowIcon)
        self.photo_ref.append(refreshIcon)
        self.photo_ref.append(open_photo)
        self.photo_ref.append(refresh_photo)
        self.photo_ref.append(rename_photo)
        self.photo_ref.append(drive_photo)
        self.photo_ref.append(info_photo)
        self.photo_ref.append(pie_photo)
        self.photo_ref.append(cpu_photo)
        self.photo_ref.append(memory_photo)
        self.photo_ref.append(network_photo)
        self.photo_ref.append(process_photo)
        self.photo_ref.append(file_photo)
        self.photo_ref.append(dir_photo)
        self.photo_ref.append(themes_photo)
        self.photo_ref.append(scale_photo)
        self.photo_ref.append(font_photo)
        self.photo_ref.append(copy_photo)
        self.photo_ref.append(paste_photo)
        self.photo_ref.append(delete_photo)
        self.photo_ref.append(encrypt_photo)
        self.photo_ref.append(decrypt_photo)

        # wrappers for keybinds
        self.root.bind("<F5>", self.file_explorer.wrap_refresh)
        self.root.bind("<Delete>", self.file_explorer.wrap_del)
        self.root.bind("<Control-c>", self.file_explorer.wrap_copy)
        self.root.bind("<Control-v>", self.file_explorer.wrap_paste)
        self.root.bind("<Control-Shift-N>", self.file_explorer.wrap_new_dir)
        self.root.bind("<Control-Shift-F>", self.file_explorer.wrap_new_file)

    def click(self, searchEntry, event):
        if searchEntry.get() == "Search files..":
            searchEntry.delete(0, "end")

    def focus_out(self, searchEntry, window, event):
        searchEntry.delete(0, "end")
        searchEntry.insert(0, "Search files..")
        window.focus()

    def write_theme(self, theme ):
        with open(file_path + "../res/theme.txt", "w") as f:  # closes file automatically
            f.write(theme)
        self.file_explorer.warning_popup()

    def change_font_popup(self, size):
        self.file_explorer.warning_popup()
        self.change_font_size(size)

    def change_font_size(self, size):
        with open(file_path + "../res/font.txt", "w") as f:  # closes file automatically
            f.write(str(size))

    def change_scale(self, multiplier):
        scale = round(multiplier * 28)  # 28 is default
        self.style.configure("Treeview", rowheight=scale)

class FileExplorer:
    def __init__(self):
        self.ui_manager = UIManager(self)
        self.database_manager = DatabaseManager()
        self.fileNames = []
        self.lastDirectory = ""
        self.selectedItem = ""
        self.src = ""
        self.theme = ""
        self.font_size = "10"
        self.available_drives = SystemMonitor.get_drives()
        self.currDrive = self.available_drives[0]
        self.cwdLabel = None
        self.footer = None
        self.photo_ref = []
        self.items = None

    def create_window(self):
        return self.ui_manager.create_window()

    def create_widgets(self):
        self.ui_manager.create_widgets()

    def refresh(self, queryNames):
        # Refresh Header
        self.ui_manager.cwdLabel.config(text=" " + os.getcwd())
        # --Refresh Header

        # Refresh Browse
        fileSizesSum = 0
        if queryNames:  # if user gave query and pressed enter
            self.fileNames = queryNames
        else:
            self.fileNames = os.listdir(os.getcwd())
        fileTypes = [None] * len(self.fileNames)
        fileSizes = [None] * len(self.fileNames)
        fileDateModified = []
        for i in self.items.get_children():  # delete data from previous directory
            self.items.delete(i)
        for i in range(len(self.fileNames)):
            try:
                # modification time of file
                fileDateModified.append(
                    datetime.fromtimestamp(os.path.getmtime(self.fileNames[i])).strftime(
                        "%d-%m-%Y %I:%M"
                    )
                )
                # size of file
                fileSizes[i] = str(
                    round(os.stat(self.fileNames[i]).st_size / 1024)
                )  # str->round->size of file in KB
                fileSizesSum += int(fileSizes[i])
                fileSizes[i] = str(round(os.stat(self.fileNames[i]).st_size / 1024)) + " KB"
                # check file type
                self.extensions(fileTypes, self.fileNames, i)

                # insert
                if fileTypes[i] == "Directory":
                    self.items.insert(
                        parent="",
                        index=i,
                        values=(self.fileNames[i], fileDateModified[i], fileTypes[i], ""),
                        image=tk.PhotoImage(file=file_path + "Folder-icon.png", width=20, height=16),
                    )
                else:
                    self.items.insert(
                        parent="",
                        index=i,
                        values=(
                            self.fileNames[i],
                            fileDateModified[i],
                            fileTypes[i],
                            fileSizes[i],
                        ),
                        image=tk.PhotoImage(file=file_path + "File-icon.png", width=20, height=16),
                    )
            except:
                pass
        # --Refresh Browse

        # Draw browse
        self.items.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # --Draw browse

        # Refresh Footer
        self.ui_manager.footer.config(
            text=" "
            + str(len(self.fileNames))
            + " items | "
            + str(round(fileSizesSum / 1024, 1))
            + " MB Total"
        )
        self.ui_manager.footer.pack(fill=tk.BOTH)
        # --Refresh Footer

    def extensions(self, fileTypes, fileNames, i):
        split = os.path.splitext(fileNames[i])  # split file extension
        path = os.getcwd() + "/" + fileNames[i]
        ext = split[1]

        if os.path.isdir(path):
            fileTypes[i] = "Directory"
        else:
            if ext == "":
                fileTypes[i] = "Unknown file"
            else:
                fileTypes[i] = ext.upper()[1:] + " file"

    def previous(self):
        self.lastDirectory = os.getcwd()
        os.chdir("../")
        self.refresh([])

    def next(self):
        try:
            os.chdir(self.lastDirectory)
            self.refresh([])
        except:
            return

    def on_double_click(self, event=None):
        iid = self.items.focus()
        # iid = self.items.identify_row(event.y) # old
        if iid == "":  # if double click on blank, don't do anything
            return
        for item in self.items.selection ():
            tempDictionary = self.items.item(item)
            tempName = tempDictionary["values"][0]  # get first value of dictionary
        try:
            newPath = os.getcwd() + "/" + tempName
            if os.path.isdir(
                newPath
            ):  # if file is directory, open directory else open file
                os.chdir(newPath)
            else:
                os.startfile(newPath)
            self.refresh([])
        except:
            newPath = newPath.replace(tempName, "")
            os.chdir("../")

    def on_right_click(self, m, event):
        self.select_item(event)
        m.tk_popup(event.x_root, event.y_root)

    def search(self, searchEntry, event):
        fileNames = os.listdir()
        query = searchEntry.get()  # get query from text box
        query = query.lower()
        queryNames = []

        for name in fileNames:
            if name.lower().find(query) != -1:  # if query in name
                queryNames.append(name)
        self.refresh(queryNames)

    def sort_col(self, col, reverse):
        l = [(self.items.set(k, col), k) for k in self.items.get_children("")]
        if col == "Name" or col == "Type":
            l.sort(reverse=reverse)
        elif col == "Date modified":
            l = sorted(l, key=self.sort_key_dates, reverse=reverse)
        elif col == "Size":
            l = sorted(l, key=self.sort_key_size, reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.items.move(k, "", index)

        # reverse sort next time
        self.items.heading(col, command=partial(self.sort_col, col, not reverse))

    def sort_key_dates(self, item):
        return datetime.strptime(item[0], "%d-%m-%Y %I:%M")

    def sort_key_size(self, item):
        num_size = item[0].split(" ")[0]
        if num_size != "":
            return int(num_size)
        else:
            return -1  # if it's a directory, give it negative size value, for sorting

    def warning_popup(self):
        Messagebox.show_info(
            message="Please restart the application to apply changes.", title="Info"
        )

    def change_font_popup(self, size):
        self.warning_popup()
        self.change_font_size(size)

    def change_font_size(self, size):
        with open(file_path + "../res/font.txt", "w") as f:  # closes file automatically
            f.write(str(size))

    def change_scale(self, multiplier):
        scale = round(multiplier * 28)  # 28 is default
        self.ui_manager.style.configure("Treeview", rowheight=scale)

    def drive_stats(self, window):
        top = ttk.Toplevel(window)
        top.resizable(False, False)
        top.iconphoto(False, tk.PhotoImage(file=file_path + "info.png"))
        top.title("Drives")

        meters = []
        for drive in self.available_drives:
            meters.append(
                ttk.Meter(
                    top,
                    bootstyle="default",
                    metersize=180,
                    padding=5,
                    metertype="semi",
                    subtext="GB Used",
                    textright="/ "
                    + str(
                        round(psutil.disk_usage(drive).total / (1024 * 1024 * 1024))
                    ),  # converts bytes to GB
                    textleft=drive,
                    interactive=False,
                    amounttotal=round(
                        psutil.disk_usage(drive).total / (1024 * 1024 * 1024)
                    ),  # converts bytes to GB
                    amountused=round(
                        psutil.disk_usage(drive).used / (1024 * 1024 * 1024)
                    ),  # converts bytes to GB
                )
            )
        top.geometry(str(len(meters) * 200) + "x200")  # Add 200px width for every drive
        for meter in meters:
            meter.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def cpu_stats(self):
        cpu_count_log = psutil.cpu_count()
        cpu_count = psutil.cpu_count(logical=False)
        cpu_per = psutil.cpu_percent()
        cpu_freq = round(psutil.cpu_freq().current / 1000, 2)
        Messagebox.ok(
            message="Usage: "
            + str(cpu_per)
            + "%"
            + "\nLogical Processors: "
            + str(cpu_count)
            + "\nCores: "
            + str(cpu_count_log)
            + "\nFrequency: "
            + str(cpu_freq)
            + " GHz",
            title="CPU",
        )

    def memory_stats(self):
        memory_per = psutil.virtual_memory().percent
        memory_total = round(psutil.virtual_memory(). total / (1024 * 1024 * 1024), 2)
        memory_used = round(psutil.virtual_memory().used / (1024 * 1024 * 1024), 2)
        memory_avail = round(psutil.virtual_memory().available / (1024 * 1024 * 1024), 2)
        Messagebox.ok(
            message="Usage: "
            + str(memory_per)
            + "%"
            + "\nTotal: "
            + str(memory_total)
            + " GB"
            + "\nUsed: "
            + str(memory_used)
            + " GB"
            + "\nAvailable: "
            + str(memory_avail)
            + " GB",
            title="Memory",
        )

    def network_stats(self):
        net = psutil.net_io_counters(pernic=True)
        mes = ""
        for key, value in net.items():
            mes += (
                str(key)
                + ":\n"
                + "Sent: "
                + str(round(value.bytes_sent / (1024 * 1024 * 1024), 2))
                + " GB\n"
                + "Received: "
                + str(round(value.bytes_recv / (1024 * 1024 * 1024), 2))
                + " GB\n\n"
            )
        Messagebox.ok(message=mes, title="Network")

    def processes_win(self, window):
        top = ttk.Toplevel(window)
        top.geometry("1024x600")
        top.resizable(True, True)
        top.iconphoto(False, tk.PhotoImage(file=file_path + "process.png"))
        top.title("Processes")
        scroll = ttk.Scrollbar(top, orient="vertical")

        processes_list = []
        for i in psutil.pids():
            p = psutil.Process(i)
            processes_list.append(
                (p.name(), p.pid, p.status(), str(round(p.memory_info().rss / 1024)) + "KB")
            )

        processes = ttk.Treeview(
            top,
            columns=("Name", "PID", "Status", "Memory"),
            yscrollcommand=scroll.set,
            style="Custom.Treeview",
        )
        for p in processes_list:
            processes.insert(parent="", index=0, values=p)
        processes.heading("Name", text="Name", anchor="w")
        processes.heading("PID", text="PID", anchor="w")
        processes.heading("Status", text="Status", anchor="w")
        processes.heading("Memory", text="Memory", anchor="w")
        scroll.config(command=processes.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.BOTH)
        processes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def cd_drive(self, drive, queryNames):
        self.ui_manager.cwdLabel.config(text=" " + drive)
        self.currDrive = drive
        self.fileNames = os.listdir(drive)
        os.chdir(drive + "/")
        self.refresh(queryNames)

    def up_key(self, event):
        iid = self.items.focus()
        iid = self.items.prev(iid)
        if iid:
            self.items.selection_set(iid)
            self.selectedItem = self.items.item(iid)["values"][0]
            print(self.selectedItem)
        else:
            pass

    def down_key(self, event):
        iid = self.items.focus()
        iid = self.items.next(iid)
        if iid:
            self.items.selection_set(iid)
            self.selectedItem = self.items.item(iid)["values"][0]
            print(self.selectedItem)
        else:
            pass

    def click(self, searchEntry, event):
        if searchEntry.get() == "Search files..":
            searchEntry.delete(0, "end")

    def focus_out(self, searchEntry, window, event):
        searchEntry.delete(0, "end")
        searchEntry.insert(0, "Search files..")
        window.focus()

    def rename_popup(self):
        if self.items.focus() != "":
            try:
                name = Querybox.get_string(prompt="Name: ", title="Rename")
                old = os.getcwd() + "/" + self.selectedItem
                os.rename(old, name)
                self.refresh([])
            except:
                pass
        else:
            Messagebox.show_info(
                message="There is no selected file or directory.", title="Info"
            )

    def select_item(self, event):
        iid = self.items.identify_row(event.y)
        if iid:
            self.items.selection_set(iid)
            self.selectedItem = self.items.item(iid)["values"][0]
            print(self.selectedItem)
            self.items.focus(iid)  # Give focus to iid
        else:
            pass


    def keybinds(self):
        Messagebox.ok(
            message="Copy - <Control + C>\nPaste - <Control + V>\nDelete - <Del>\n"
            + "New File - <Control + Shift + F>\ nNew Directory - <Control + Shift + N>\n"
            + "Refresh - <F5>",
            title="Keybinds",
        )

    def del_file_popup(self):
        if self.items.focus() != "":
            try:
                os.remove(os.getcwd() + "/" + self.selectedItem)
                self.refresh([])
            except:
                pass
        else:
            Messagebox.show_info(
                message="There is no selected file or directory.", title="Info"
            )

    def new_file_popup(self):
        try:
            name = Querybox.get_string(prompt="Name: ", title="New File")
            open(name, "w").close()
            self.refresh([])
        except:
            pass

    def new_dir_popup(self):
        try:
            name = Querybox.get_string(prompt="Name: ", title="New Directory")
            os.mkdir(name)
            self.refresh([])
        except:
            pass

    def copy(self):
        if self.items.focus() != "":
            self.src = os.getcwd() + "/" + self.selectedItem
        else:
            Messagebox.show_info(
                message="There is no selected file or directory.", title="Info"
            )

    def paste(self):
        if self.src != "":
            try:
                shutil.copy(self.src, os.getcwd())
                self.refresh([])
            except:
                pass
        else:
            Messagebox.show_info(
                message="There is no copied file or directory.", title="Info"
            )

    def wrap_refresh(self, event):
        self.refresh([])

    def wrap_del(self, event):
        self.del_file_popup()

    def wrap_copy(self, event):
        self.copy()

    def wrap_paste(self, event):
        self.paste()

    def wrap_new_dir(self, event):
        self.new_dir_popup()

    def wrap_new_file(self, event):
        self.new_file_popup()

    def encryption_popup(self):
        Messagebox.ok(
            message="Encryption key is: " + self.database_manager.get_key(),
            title="Encryption Key",
        )

    def change_encryption_popup(self):
        new_key = Querybox.get_string(prompt="New key: ", title="Change Encryption Key")
        self.database_manager.change_key(new_key)
        Messagebox.ok(
            message="Encryption key is changed to: " + new_key,
            title="Encryption Key",
        )

    def encrypt_file_popup(self):
        if self.items.focus() != "":
            try:
                self.database_manager.encrypt_file(
                    os.getcwd() + "/" + self.selectedItem
                )
                self.refresh([])
            except:
                pass
        else:
            Messagebox.show_info(
                message="There is no selected file or directory.", title="Info"
            )

    def decrypt_file_popup(self):
        if self.items.focus() != "":
            try:
                self.database_manager.decrypt_file(
                    os.getcwd() + "/" + self.selectedItem
                )
                self.refresh([])
            except:
                pass
        else:
            Messagebox.show_info(
                message="There is no selected file or directory.", title="Info"
            )

    def about_popup(self):
        Messagebox.ok(
            message="File Explorer\n\n"
            + "Version: 1.0.0\n"
            + "Developer: Mertcan Kılıç\n"
            + "Date: 2022\n\n"
            + "This application is a file explorer with some additional features.\n"
            + "It is written in Python using Tkinter library.\n"
            + "It is open source and free to use.",
            title="About",
        )

    def run(self):
        root = self.create_window()
        self.create_widgets()
        self.refresh([])
        root.mainloop()

def main():
    file_explorer = FileExplorer()
    file_explorer.run()

if __name__ == "__main__":
    print(file_path)
    main()