from enum import Enum
import os
import gi
import random
from typing import List

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

class Suit(Enum):
    NONE = 0
    BLACK = 1
    RED = 2
    GREEN = 3

class Rank(Enum):
    NONE = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

class Card(Gtk.EventBox):
    def __init__(self, rank: Rank, suit: Suit, board: "Board") -> None:
        super().__init__()
        self.rank = rank
        self.suit = suit
        self.board = board

        self.stack: Stack | Cell = None
        self.child: Card = None
        
        self.img = Gtk.Image.new_from_file(os.path.join("images","cards",f"{self.name}.png"))
        self.add(self.img)

        self.connect("button_press_event", board.card_clicked)

    @property
    def is_special_card(self) -> bool:
        return self.rank == Rank.NONE or self.suit == Suit.NONE
    
    @property
    def is_free(self) -> bool:
        return self.child == None or self.can_receive_card(self.child)
    
    @property
    def can_be_picked_up(self) -> bool:
        return self.is_free and not isinstance(self.stack, (FoundationStack, FlowerCell))
    
    def is_dragon(self, suit: Suit) -> bool:
        return self.suit == suit and self.rank == Rank.NONE

    def can_receive_card(self, other: "Card") -> bool:
        if(self.is_special_card or other.is_special_card):
            return False
        return other.suit != self.suit and other.rank == Rank(self.rank.value - 1)

    def setXY(self, x:int, y:int) -> None:
        offset = -y if isinstance(self.stack, FoundationStack) else 0

        self.x = x
        self.y = y + offset

    def __str__(self) -> str:
        s = self.suit.name.title() if self.suit != Suit.NONE else "Flower"
        return f"{self.rank.value} of {s}"
    
    def __repr__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        s = self.suit.name[0] if self.suit != Suit.NONE else "F"
        return f"{self.rank.value}{s}"
    
    def redraw(self, grid):
        grid.attach(self, self.x, self.y, 1, 1)
        grid.show_all()

class Cell(Gtk.EventBox):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__()
        self.card = None

        self.x = x
        self.y = y
        self.board = board

        self.connect("button_press_event", board.cell_clicked)

    def can_accept(self, card: Card) -> bool:
        raise NotImplementedError()
    
    def add_card(self, card: Card) -> None:
        card.stack = self
        card.setXY(self.x, self.y)

        self.card = card

    def remove_card(self, card: Card) -> None:
        self.card.stack = None
        self.card.child = None
        self.card = None

    def redraw(self, grid):
        grid.attach(self, self.x, self.y, 1, 1)
        if self.card:
            self.card.redraw(grid)
        grid.show_all()
        

class TempCell(Cell):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__(x, y, board)
        self.collapsed = False

        self.img = Gtk.Image.new_from_file(os.path.join("images","temp_cell.png"))
        self.add(self.img)

    @property
    def empty(self) -> bool:
        return not self.card and not self.collapsed
    
    def has_dragon(self, suit: Suit) -> bool:
        return self.card and self.card.is_dragon(suit)

    def can_accept(self, card: Card) -> bool:
        return not self.collapsed and not self.card and not card.child
    
    def collapse(self):
        self.collapsed = True

        self.remove(self.img)
        self.img = Gtk.Image.new_from_file(os.path.join("images","collapsed_cell.png"))
        self.add(self.img)

    
class FlowerCell(Cell):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__(x, y, board)

        self.img = Gtk.Image.new_from_file(os.path.join("images","flower_cell.png"))
        self.add(self.img)

    def can_accept(self, card: Card) -> bool:
        return card.suit == Suit.NONE and card.rank == Rank.NONE and not self.card and not card.child

class Stack(Gtk.EventBox):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__()

        self.cards: List[Card] = []

        self.x = x
        self.y = y
        self.board = board

    @property
    def size(self) -> int:
        return len(self.cards)
    
    def can_accept(self, card: Card) -> bool:
        raise NotImplementedError()

    def add_card(self, card: Card) -> None:
        if(self.size > 0):
            self.cards[-1].child = card

        card.stack = self

        card.setXY(self.x, self.y + len(self.cards))

        self.cards.append(card)

        if(card.child):
            self.add_card(card.child)

    def remove_card(self, card: Card) -> None:
        idx = self.cards.index(card)
        self.cards[idx-1].child = None

        for c in self.cards[idx:]:
            c.stack = None
            self.cards.remove(c)

    def __str__(self) -> str:
        return str(self.cards)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def redraw(self, grid):
        if (len(self.cards) == 0):
            grid.attach(self, self.x, self.y, 1, 1)
        for card in self.cards:
            card.redraw(grid)
        grid.show_all()

class WorkStack(Stack):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__(x, y, board)

        self.img = Gtk.Image.new_from_file(os.path.join("images","work_stack.png"))
        self.add(self.img)

        self.connect("button_press_event", board.workstack_clicked)    
    
    def can_accept(self, card: Card) -> bool:
        return self.size == 0 or (self.cards[-1].can_receive_card(card))

class FoundationStack(Stack):
    def __init__(self, x: int, y: int, board: "Board") -> None:
        super().__init__(x, y, board)

        self.img = Gtk.Image.new_from_file(os.path.join("images","foundation_cell.png"))
        self.add(self.img)

        self.connect("button_press_event", board.foundation_clicked)        

    def can_accept(self, card: Card) -> bool:
        if card.is_special_card or card.child:
            return False
        if self.size == 0:
            return card.rank == Rank.ONE
        return self.cards[-1].rank == Rank(card.rank.value - 1) and self.cards[-1].suit == card.suit
    
    def redraw(self, grid):
        grid.attach(self, self.x, self.y, 1, 1)
        for card in self.cards:
            card.redraw(grid)
        grid.show_all()

class Button(Gtk.EventBox):
    def __init__(self, suit: Suit, board: "Board") -> None:
        super().__init__()

        self.suit = suit
        self.enabled: bool = True

        self.img_off = Gtk.Image.new_from_file(os.path.join("images","buttons",f"B0{suit.name[0]}.png"))
        self.img_on = Gtk.Image.new_from_file(os.path.join("images","buttons",f"B1{suit.name[0]}.png"))

        self.board: "Board" = board

        self.connect("button_press_event", board.button_clicked)  

        self.add(self.img_on)
        self.disable()
        
    def enable(self) -> None:
        if(not self.enabled):
            self.remove(self.img_off)
            self.add(self.img_on)
            self.enabled = True

    def disable(self) -> None:
        if (self.enabled):
            self.remove(self.img_on)
            self.add(self.img_off)
            self.enabled = False

    def redraw(self, grid):
        grid.attach(self, 3, 0, 1, 1)
        grid.show_all()

class ButtonHolder(Gtk.Box):
    def __init__(self, board: "Board") -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

    def redraw(self, grid):
        grid.attach(self, 3, 0, 1, 1)
        grid.show_all()

class Board():
    def __init__(self, game) -> None:
        super().__init__()
        self.game = game
        self.grid: Gtk.Grid = game.grid

        self.temp_cells: List[TempCell] = []
        self.foundation: List[FoundationStack] = []
        self.work_stacks: List[WorkStack] = []
        self.buttons: List[Button] = []
        self.deck: List[Card] = []

        self.flower_cell = FlowerCell(4, 0, self)

        self.selected_card: Card = None

        self.button_holder = ButtonHolder(self)

        for i in range(3):
            cell = TempCell(i, 0, self)
            self.temp_cells.append(cell)

            foun = FoundationStack(5+i, 0, self)
            self.foundation.append(foun)

            button = Button(Suit(i+1), self)
            self.buttons.append(button)
            self.button_holder.pack_start(button, True, True, 0)
            
        
        for i in range(8):
            stack = WorkStack(i, 1, self)
            self.work_stacks.append(stack)

    def generate_deck(self) -> None:
        for suit in [Suit.BLACK, Suit.GREEN, Suit.RED]:
            for rank in range(1,10):
                self.deck.append(Card(Rank(rank), suit, self))
                pass
            for _ in range(4):
                self.deck.append(Card(Rank.NONE, suit, self))
        self.deck.append(Card(Rank.NONE, Suit.NONE, self))

    def deal(self) -> None:
        random.shuffle(self.deck)
        #deal what you can evenly
        n = len(self.deck)//len(self.work_stacks)
        for i, stack in enumerate(self.work_stacks):
            for j in range(n):
                stack.add_card(self.deck[i*n+j])

        #deal extra cards to leftmost stacks
        for i in range(len(self.deck)%len(self.work_stacks)):
            self.work_stacks[i].add_card(self.deck[-(i+1)])
    
    def card_clicked(self, card: Card, _):
        if self.selected_card == None and not isinstance(card.stack, FoundationStack):
            self.selected_card = card
        elif self.selected_card == card:
            self.auto_drop(card)
            self.selected_card = None
        else:
            if card.stack.can_accept(self.selected_card):
                self.selected_card.stack.remove_card(self.selected_card)
                card.stack.add_card(self.selected_card)

                self.update()
            self.selected_card = None

    def cell_clicked(self, cell: Cell, _):
        if self.selected_card:
            if cell.can_accept(self.selected_card):
                self.selected_card.stack.remove_card(self.selected_card)
                cell.add_card(self.selected_card)

                self.update()
            self.selected_card = None

    def foundation_clicked(self, stack: FoundationStack, _):
        if self.selected_card:
            if stack.can_accept(self.selected_card):
                self.selected_card.stack.remove_card(self.selected_card)
                stack.add_card(self.selected_card)

                self.update()
            self.selected_card = None

    def workstack_clicked(self, stack: FoundationStack, _):
        if self.selected_card:
            if stack.can_accept(self.selected_card):
                self.selected_card.stack.remove_card(self.selected_card)
                stack.add_card(self.selected_card)

                self.update()
            self.selected_card = None

    def auto_drop(self, card: Card):
        for stack in [*self.foundation, self.flower_cell]:
            if stack.can_accept(card):
                card.stack.remove_card(card)
                stack.add_card(card)

                self.update()

    def button_clicked(self, button: Button, _):
        if button.enabled:
            self.collapse_dragon(button.suit)


    def check_buttons(self) -> None:
        for button in self.buttons:
            suit = button.suit
            count = 0
            free_cell = False

            for cell in self.temp_cells:
                if cell.empty or cell.has_dragon(suit):
                    free_cell = True
        
            #todo: could just loop through deck probably
            for stack in self.work_stacks:
                if stack.size > 0:
                    if stack.cards[-1].is_dragon(suit):
                        count +=1
            for cell in self.temp_cells:
                if cell.has_dragon(suit):
                    count +=1
            if(count == 4 and free_cell):
                button.enable()
            else:
                button.disable()

    def collapse_dragon(self, suit: Suit):
        for stack in self.work_stacks:
            if stack.size > 0:
                if stack.cards[-1].is_dragon(suit):
                    stack.remove_card(stack.cards[-1])
        for cell in self.temp_cells:
            if cell.card:
                if cell.card.is_dragon(suit):
                    cell.remove_card(cell.card)
        for cell in self.temp_cells:
            if cell.empty:
                cell.collapse()
                break

        self.update()

    def check_win(self) -> None:
        for stack in self.foundation:
            if stack.size < 9:
                return
        if not self.flower_cell.card:
            return
        self.game.win()

    def update(self) -> None:
        self.check_buttons()
        self.check_win()
        self.redraw()

    def redraw(self) -> None:
        self.game.reset_grid()
        for stack in self.work_stacks:
            stack.redraw(self.grid)
        for temp in self.temp_cells:
            temp.redraw(self.grid)
        for foun in self.foundation:
            foun.redraw(self.grid)
        self.flower_cell.redraw(self.grid)
        self.button_holder.redraw(self.grid)
        