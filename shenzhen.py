import os
import gi

from datetime import timedelta
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio
from gi.repository import Gdk, GdkPixbuf

from logic import *

DRAG_ACTION = Gdk.DragAction.COPY

class BottomBar(Gtk.Box):
    def __init__(self, wins: int, best_time: int):
        super().__init__(spacing=20)

        self.label_wins = Gtk.Label(label=f"Wins: {str(wins)}")
        self.label_timer = Gtk.Label(label="Time: 00:00:00")
        self.label_best = Gtk.Label(label="Best: {:0>8}".format(str(timedelta(seconds=best_time))))

        self.pack_start(self.label_wins, True, True, 0)
        self.pack_start(self.label_timer, True, True, 0)
        self.pack_start(self.label_best, True, True, 0)

    def setWins(self, c: int) -> None:
        self.label_wins.set_text(f"Wins: {str(c)}")

    def setTime(self, t: int) -> None:
        self.label_timer.set_text("Time: {:0>8}".format(str(timedelta(seconds=t))))

    def setBest(self, t: int) -> None:
        self.label_best.set_text("Best: {:0>8}".format(str(timedelta(seconds=t))))

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title = "Shenzhen Solitaire")

        # init
        self.load_save_data()
        self.board = None
        self.timeout_id = None
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        #region Menu
        self.menu_bar = Gtk.MenuBar()
        self.menu_bar.set_name("menu-bar")

        program_button = Gtk.MenuItem(label="Program")
        program_menu = Gtk.Menu()
        program_button.set_submenu(program_menu)

        about_button = Gtk.MenuItem(label = "O Programie")
        about_button.connect("activate", self.on_about)
        program_menu.append(about_button)

        self.menu_bar.append(program_button)

        game_button = Gtk.MenuItem(label="Gra")
        game_menu = Gtk.Menu()
        game_button.set_submenu(game_menu)

        new_game_button = Gtk.MenuItem(label = "Nowa Gra")
        new_game_button.connect("activate", self.on_new_game)
        game_menu.append(new_game_button)

        rules_button = Gtk.MenuItem(label = "Jak Grać")
        rules_button.connect("activate", self.on_rules)
        game_menu.append(rules_button)

        self.menu_bar.append(game_button)

        self.main_box.pack_start(self.menu_bar, True, True, 0)
        #endregion

        # board
        self.grid = Gtk.Grid()
        self.grid_containder = Gtk.Box()
        self.grid_containder.add(self.grid)
        self.main_box.pack_start(self.grid_containder, True, True, 0)

        # footer
        self.bottom_bar = BottomBar(self.wins, self.best_time)
        self.main_box.pack_start(self.bottom_bar, True, True, 0)

        self.add(self.main_box)
        self.on_new_game()

    def reset_grid(self):
        for _ in range(8):
            self.grid.remove_column(0)
        #todo: spacing
        self.grid_containder.remove(self.grid)
        self.grid = Gtk.Grid()
        self.grid_containder.add(self.grid)

        self.board.grid = self.grid


    def load_save_data(self) -> None:
        self.wins = 0
        self.best_time = 100000
        try:
            with open("save.txt", "r") as f:
                self.wins = int(next(f).split()[0])
                self.best_time = int(next(f).split()[0])
        except IOError:
            self.wins = 0
            self.best_time = 0

    def update_save_data(self) -> None:
        try:
            with open("save.txt", "w+") as f:
                f.write(f"{str(self.wins)}\n")
                f.write(f"{str(self.best_time)}\n")
        except IOError:
            pass

    def on_new_game(self, *args) -> None:
        self.time = 0
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
        self.timeout_id = GLib.timeout_add(1000, self.on_timeout, None)

        self.board = Board(self)
        self.board.generate_deck()
        self.board.deal()

        self.board.redraw()

    def on_timeout(self, *args, **kwargs):
        self.time += 1
        self.bottom_bar.setTime(self.time)
        return True

    def on_about(self, _):
        AboutDialog(self).run()

    def on_rules(self, _):
        RulesDialog(self).run()

    def win(self):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)

        self.wins += 1
        self.best_time = self.time if self.time < self.best_time else self.best_time

        self.bottom_bar.setWins(self.wins)
        self.bottom_bar.setBest(self.best_time)
        self.update_save_data()

class AboutDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "O Programie", parent, 0)
        self.set_default_size(300, 200)
        self.set_name("about-program")

        box = self.get_content_area()

        label = Gtk.Label()
        label.set_text("ShenzhenSolitairePyGtk - Kulpas\n\nOriginalna wersja należy do Zachtronics")
        label.set_margin_top(50)
        box.add(label)

        self.show_all()

class RulesDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Zasady Gry", parent, 0)
        self.set_default_size(300, 200)
        self.set_name("rules-program")

        box = self.get_content_area()
        
        rules = Gtk.Image.new_from_file(os.path.join("images","rules.png"))
        box.add(rules)

        self.show_all()

win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()