"""
Windows-style Klondike Solitaire
=================================
A complete recreation of the classic Windows Solitaire game using Pygame.

How to play Klondike Solitaire:
- The goal is to move all 52 cards to the four "foundation" piles at the top right.
- Each foundation pile holds one suit, built up from Ace to King.
- The seven "tableau" piles at the bottom are built DOWN in value and alternate colors.
  (For example: a red 5 can be placed on a black 6.)
- Only a King (or a stack starting with a King) can be moved to an empty tableau pile.
- Click the "stock" pile (top-left, face-down) to flip cards into the "waste" pile.
- When the stock is empty, click it to recycle the waste back into the stock.
- Drag cards with the mouse to move them between piles.
- Double-click a card to auto-send it to a foundation if possible.

Run with:  python solitaire.py
Requires:  pip install pygame
"""

# --- Imports ----------------------------------------------------------------
# `pygame` is the library we use for graphics, input, and the game window.
# `random` lets us shuffle the deck of cards.
# `sys` is used to cleanly exit the program.
# `os` helps us build file paths that work on any operating system.
import pygame
import random
import sys
import os

# --- Constants --------------------------------------------------------------
# Constants are values that never change while the game is running.
# We put them in ALL_CAPS by convention so they're easy to spot in the code.

# Window dimensions (in pixels). The classic Solitaire window was roughly 4:3.
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 720

# Card dimensions. These numbers were picked so 7 cards fit nicely across.
CARD_WIDTH = 100
CARD_HEIGHT = 140

# How many pixels to offset stacked cards vertically in the tableau,
# so you can see the rank/suit of cards beneath the top card.
# Face-down cards stack tighter than face-up cards.
FACE_DOWN_OFFSET = 15
FACE_UP_OFFSET = 28

# Margins and spacing between piles.
MARGIN_X = 20           # Distance from the left edge of the screen.
MARGIN_Y = 20           # Distance from the top edge of the screen.
PILE_SPACING = 25       # Horizontal gap between the 7 tableau piles.

# Frames per second. Higher is smoother, but uses more CPU.
FPS = 60

# Colors are represented as (Red, Green, Blue) tuples, each from 0 to 255.
# The classic Windows Solitaire green felt background:
BG_COLOR = (0, 120, 40)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
DARK_GRAY = (60, 60, 60)
LIGHT_GRAY = (200, 200, 200)
# Color used to outline empty piles so you can see where cards can go:
EMPTY_PILE_COLOR = (0, 90, 30)
# Highlight color for the "auto-win" animation & winning message:
GOLD = (255, 215, 0)

# The four suits in a standard deck. Hearts and Diamonds are red; the others black.
# We use Unicode suit symbols so we don't need any image files for the suits.
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
SUIT_SYMBOLS = {
    'hearts': '\u2665',    # ♥
    'diamonds': '\u2666',  # ♦
    'clubs': '\u2663',     # ♣
    'spades': '\u2660',    # ♠
}
# Which suits are red (used to enforce the "alternating colors" rule):
RED_SUITS = {'hearts', 'diamonds'}

# Ranks from Ace (value 1) to King (value 13). We store the display label
# separately because rank 1 shows as "A", not "1", etc.
RANKS = list(range(1, 14))   # [1, 2, 3, ..., 13]
RANK_LABELS = {
    1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
    8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K',
}


# --- Card Class -------------------------------------------------------------
class Card:
    """
    Represents a single playing card.

    A Card knows:
      - its suit and rank,
      - whether it is currently face-up or face-down,
      - where it is drawn on the screen (x, y),
      - which pile currently contains it.
    """

    def __init__(self, suit, rank):
        # Store the card's identity.
        self.suit = suit
        self.rank = rank
        # Cards start face-down; we flip some of them when setting up the game.
        self.face_up = False
        # On-screen position of the card's top-left corner.
        self.x = 0
        self.y = 0
        # `pile` is a reference back to the list (pile) this card belongs to.
        # It's useful during drag-and-drop so we know where a card came from.
        self.pile = None

    @property
    def color(self):
        """Return 'red' or 'black' depending on the suit."""
        return 'red' if self.suit in RED_SUITS else 'black'

    @property
    def rect(self):
        """
        A pygame.Rect describing the card's screen position & size.
        We generate it fresh each time so it always matches x/y.
        Rects are handy for collision detection (e.g., "did the mouse click me?").
        """
        return pygame.Rect(self.x, self.y, CARD_WIDTH, CARD_HEIGHT)

    def draw(self, surface, font_rank, font_suit_small, font_suit_big):
        """
        Draw this card onto the given surface (the screen).

        We pass in the fonts we need rather than loading them every frame,
        which would be slow.
        """
        if self.face_up:
            # --- Face-up card: white background with rank + suit -----------
            # Draw the rounded-rectangle card body.
            pygame.draw.rect(surface, WHITE, self.rect, border_radius=8)
            # Thin black outline so cards are visible on white piles.
            pygame.draw.rect(surface, BLACK, self.rect, width=2, border_radius=8)

            # Pick red or black text depending on the suit.
            text_color = RED if self.color == 'red' else BLACK
            label = RANK_LABELS[self.rank]
            symbol = SUIT_SYMBOLS[self.suit]

            # Top-left corner: rank on top, small suit below it.
            rank_surf = font_rank.render(label, True, text_color)
            surface.blit(rank_surf, (self.x + 8, self.y + 6))
            suit_small_surf = font_suit_small.render(symbol, True, text_color)
            surface.blit(suit_small_surf, (self.x + 8, self.y + 34))

            # Big centered suit symbol in the middle of the card.
            big_suit_surf = font_suit_big.render(symbol, True, text_color)
            big_rect = big_suit_surf.get_rect(
                center=(self.x + CARD_WIDTH // 2, self.y + CARD_HEIGHT // 2 + 8)
            )
            surface.blit(big_suit_surf, big_rect)

            # Bottom-right corner: mirrored rank + suit (upside-down style).
            # To keep things simple we just draw them normally in that corner.
            rank_surf2 = font_rank.render(label, True, text_color)
            r2_rect = rank_surf2.get_rect(
                bottomright=(self.x + CARD_WIDTH - 8, self.y + CARD_HEIGHT - 30)
            )
            surface.blit(rank_surf2, r2_rect)
            suit_small2 = font_suit_small.render(symbol, True, text_color)
            s2_rect = suit_small2.get_rect(
                bottomright=(self.x + CARD_WIDTH - 8, self.y + CARD_HEIGHT - 6)
            )
            surface.blit(suit_small2, s2_rect)
        else:
            # --- Face-down card: blue patterned back ------------------------
            # Main card back color.
            pygame.draw.rect(surface, (30, 60, 160), self.rect, border_radius=8)
            # A simple diagonal-crosshatch pattern so the back looks like a
            # real playing card, not just a solid rectangle. We use Pygame's
            # "clip" feature to make sure the lines don't spill outside the
            # card. set_clip limits all subsequent drawing to the given area.
            prev_clip = surface.get_clip()
            inner = self.rect.inflate(-12, -12)   # shrink rect by 12 px on each side
            surface.set_clip(inner)
            for i in range(-CARD_HEIGHT, CARD_WIDTH, 10):
                start = (self.x + 6 + i, self.y + 6)
                end = (self.x + 6 + i + CARD_HEIGHT, self.y + 6 + CARD_HEIGHT)
                pygame.draw.line(surface, (80, 120, 220), start, end, 1)
            # Restore whatever clip was in effect before we touched it.
            surface.set_clip(prev_clip)
            # A small inset rectangle decoration, like a real card back.
            pygame.draw.rect(surface, (80, 120, 220), inner, width=2, border_radius=6)
            # Black border on top of everything, so no pattern leaks past it.
            pygame.draw.rect(surface, BLACK, self.rect, width=2, border_radius=8)


# --- Game Class -------------------------------------------------------------
class SolitaireGame:
    """
    The main game class. It owns the deck, all seven tableau piles,
    the four foundations, the stock and waste piles, and runs the main loop.
    """

    def __init__(self):
        # Initialize pygame's subsystems (display, fonts, etc.).
        pygame.init()
        # Create the game window.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Solitaire")
        # The Clock object lets us control the frame rate so the game runs
        # at a consistent speed regardless of how fast the CPU is.
        self.clock = pygame.time.Clock()

        # --- Load fonts --------------------------------------------------
        # `None` means "use the default system font."
        # Using a system font instead of a custom .ttf file keeps things simple.
        self.font_rank = pygame.font.SysFont('arial', 22, bold=True)
        self.font_suit_small = pygame.font.SysFont('arial', 22)
        self.font_suit_big = pygame.font.SysFont('arial', 48)
        self.font_ui = pygame.font.SysFont('arial', 20, bold=True)
        self.font_big = pygame.font.SysFont('arial', 64, bold=True)

        # --- Pile containers --------------------------------------------
        # Each pile is a Python list of Cards. The LAST card in the list is
        # the TOP of the pile (the one you can see / interact with).
        self.stock = []                             # face-down draw pile
        self.waste = []                             # face-up discards from the stock
        self.foundations = [[], [], [], []]          # four foundation piles
        self.tableau = [[] for _ in range(7)]       # seven tableau columns

        # These hold the static screen positions of each pile so we can draw
        # empty-pile outlines and know where to snap cards.
        self.stock_pos = (MARGIN_X, MARGIN_Y)
        self.waste_pos = (MARGIN_X + CARD_WIDTH + PILE_SPACING, MARGIN_Y)
        # The four foundation piles sit in the top-right area.
        # We compute their positions so they're evenly spaced across columns 4-7.
        self.foundation_positions = []
        for i in range(4):
            x = MARGIN_X + (3 + i) * (CARD_WIDTH + PILE_SPACING)
            y = MARGIN_Y
            self.foundation_positions.append((x, y))
        # The seven tableau columns are below the top row, with a bigger y offset.
        self.tableau_positions = []
        tableau_y = MARGIN_Y + CARD_HEIGHT + 40
        for i in range(7):
            x = MARGIN_X + i * (CARD_WIDTH + PILE_SPACING)
            self.tableau_positions.append((x, tableau_y))

        # --- Drag-and-drop state ----------------------------------------
        # When the player starts dragging cards, we store them here.
        # `dragging_cards` is a list because you can drag a stack of cards.
        self.dragging_cards = []
        # Remember where the cards came from, so we can put them back if
        # the drop is invalid.
        self.drag_source_pile = None
        # Offset between the mouse cursor and the top-left of the dragged card,
        # so the card doesn't "jump" to the cursor when you start dragging.
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Double-click detection. We compare click times in milliseconds.
        self.last_click_time = 0
        self.last_clicked_card = None
        self.DOUBLE_CLICK_MS = 400

        # Game status flags.
        self.won = False
        self.move_count = 0

        # Deal a brand-new game.
        self.deal_new_game()

    # ---- Game setup -----------------------------------------------------
    def deal_new_game(self):
        """Create a fresh shuffled deck and deal it out Klondike-style."""
        # Reset every pile.
        self.stock.clear()
        self.waste.clear()
        for f in self.foundations:
            f.clear()
        for t in self.tableau:
            t.clear()
        self.won = False
        self.move_count = 0

        # Build a full 52-card deck.
        deck = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        # Shuffle in place (uses Python's built-in random number generator).
        random.shuffle(deck)

        # Deal cards into the seven tableau columns.
        # Column 1 gets 1 card, column 2 gets 2, ..., column 7 gets 7 cards.
        # The TOP card of each column is flipped face-up; the rest stay down.
        for col in range(7):
            for row in range(col + 1):
                card = deck.pop()          # take the top card off the deck
                self.tableau[col].append(card)
                card.pile = self.tableau[col]
            # Flip the last card in this column face up.
            self.tableau[col][-1].face_up = True

        # Everything left in the deck becomes the stock pile (face-down).
        for card in deck:
            card.face_up = False
            card.pile = self.stock
            self.stock.append(card)

        # Finally, compute where each card should be drawn on screen.
        self.update_card_positions()

    # ---- Position updates -----------------------------------------------
    def update_card_positions(self):
        """
        Recompute each card's (x, y) based on which pile it's in and how far
        down the pile it is. Call this any time cards change piles.
        """
        # Stock pile: all cards stacked at the same spot.
        for card in self.stock:
            card.x, card.y = self.stock_pos

        # Waste pile: also all at the same spot (we only show the top card).
        for card in self.waste:
            card.x, card.y = self.waste_pos

        # Foundation piles: one position each, all cards stacked at that spot.
        for i, foundation in enumerate(self.foundations):
            fx, fy = self.foundation_positions[i]
            for card in foundation:
                card.x, card.y = fx, fy

        # Tableau piles: cards are fanned downwards so multiple are visible.
        for i, column in enumerate(self.tableau):
            col_x, col_y = self.tableau_positions[i]
            y = col_y
            for card in column:
                card.x = col_x
                card.y = y
                # Face-down cards stack tighter; face-up cards are spaced more.
                if card.face_up:
                    y += FACE_UP_OFFSET
                else:
                    y += FACE_DOWN_OFFSET

    # ---- Rule checks ----------------------------------------------------
    def can_place_on_tableau(self, card, target_pile):
        """
        Return True if `card` can legally be placed on top of `target_pile`
        (a tableau column).

        Rules:
          - Empty column only accepts a King.
          - Otherwise, card must be one less in rank AND opposite color
            from the current top card.
        """
        if not target_pile:
            return card.rank == 13   # only King (rank 13) on an empty column
        top = target_pile[-1]
        # Rule: must alternate colors (red on black, black on red).
        if top.color == card.color:
            return False
        # Rule: must be exactly one less in rank than the top card.
        return card.rank == top.rank - 1

    def can_place_on_foundation(self, card, foundation_pile):
        """
        Return True if `card` can be placed on the given foundation pile.

        Rules:
          - Empty foundation only accepts an Ace.
          - Otherwise, card must be same suit AND exactly one higher in rank.
          - Only a single card can be moved to the foundation at a time
            (this is checked by the caller, which only passes one card).
        """
        if not foundation_pile:
            return card.rank == 1   # Ace only
        top = foundation_pile[-1]
        return card.suit == top.suit and card.rank == top.rank + 1

    # ---- Mouse helpers --------------------------------------------------
    def get_clicked_card(self, pos):
        """
        Given a mouse position, figure out which card (if any) is at that spot.
        We check piles in reverse draw order so the topmost card is found first.

        Returns: (card, pile) or (None, None) if nothing was clicked.
        """
        mx, my = pos

        # Check tableau columns. Iterate cards from TOP (end of list) to BOTTOM
        # so overlapping cards are handled correctly.
        for column in self.tableau:
            for card in reversed(column):
                if card.rect.collidepoint(mx, my):
                    return card, column
                # Important: only the TOP card has the full visible hitbox;
                # lower cards are partly covered. But because we use the full
                # rect for each card and iterate top-down, we'll still find
                # the correct top-most one first. So no special case needed.

        # Check waste pile (only the top card is visible/clickable).
        if self.waste and self.waste[-1].rect.collidepoint(mx, my):
            return self.waste[-1], self.waste

        # Check foundations (only top card is clickable; you can move it back).
        for foundation in self.foundations:
            if foundation and foundation[-1].rect.collidepoint(mx, my):
                return foundation[-1], foundation

        # Check stock (clicking it flips cards; handled elsewhere).
        if self.stock and self.stock[-1].rect.collidepoint(mx, my):
            return self.stock[-1], self.stock

        return None, None

    def get_pile_at_position(self, pos):
        """
        Figure out which pile the player dropped cards onto.
        Used when the player releases the mouse after dragging.

        Returns: the pile (a list), or None if the drop point isn't over a pile.
        """
        mx, my = pos

        # Check foundation drop zones.
        for i, (fx, fy) in enumerate(self.foundation_positions):
            rect = pygame.Rect(fx, fy, CARD_WIDTH, CARD_HEIGHT)
            if rect.collidepoint(mx, my):
                return self.foundations[i]

        # Check tableau drop zones. A tableau drop zone extends from the top
        # of the column downwards to include all its cards (or just the empty
        # slot if the column is empty).
        for i, column in enumerate(self.tableau):
            col_x, col_y = self.tableau_positions[i]
            if column:
                # The drop zone ends at the bottom card's bottom edge.
                bottom_card = column[-1]
                bottom = bottom_card.y + CARD_HEIGHT
            else:
                bottom = col_y + CARD_HEIGHT
            rect = pygame.Rect(col_x, col_y, CARD_WIDTH, bottom - col_y)
            if rect.collidepoint(mx, my):
                return self.tableau[i]

        return None

    # ---- Move actions ---------------------------------------------------
    def flip_stock_card(self):
        """
        Player clicked the stock pile:
          - If there are cards in stock, move the top one to the waste, face up.
          - If the stock is empty, recycle the waste back into the stock.
        """
        if self.stock:
            card = self.stock.pop()
            card.face_up = True
            card.pile = self.waste
            self.waste.append(card)
            self.move_count += 1
        else:
            # Recycle waste -> stock. Flip each card face down and reverse order.
            while self.waste:
                card = self.waste.pop()
                card.face_up = False
                card.pile = self.stock
                self.stock.append(card)
            self.move_count += 1
        self.update_card_positions()

    def try_auto_move_to_foundation(self, card):
        """
        Double-click handler: try to move `card` to any foundation pile
        where it legally fits. Only works for single cards (not stacks).

        Returns True if the card was moved.
        """
        # The card must be the TOP card of a pile (you can't yank one from below).
        source_pile = card.pile
        if source_pile is None or source_pile[-1] is not card:
            return False
        # Can't auto-move a face-down card.
        if not card.face_up:
            return False

        # Try each foundation and take the first one that works.
        for foundation in self.foundations:
            if self.can_place_on_foundation(card, foundation):
                source_pile.remove(card)
                foundation.append(card)
                card.pile = foundation
                # If we just uncovered a face-down card in the tableau, flip it.
                self.flip_top_if_needed(source_pile)
                self.move_count += 1
                self.update_card_positions()
                self.check_win()
                return True
        return False

    def flip_top_if_needed(self, pile):
        """After removing a card from a tableau pile, flip the new top card
        face-up if it was face-down. (Stock/waste/foundation cards don't need this.)"""
        # Only tableau piles have face-down cards that need flipping here.
        if pile in self.tableau:
            if pile and not pile[-1].face_up:
                pile[-1].face_up = True

    # ---- Drag-and-drop --------------------------------------------------
    def start_drag(self, card, pile, mouse_pos):
        """
        Begin dragging `card` and all face-up cards on top of it.

        From the tableau you can drag a whole group (e.g., a 5 with a 4 and
        a 3 on top). From the waste/foundation you can only drag one card.
        """
        if not card.face_up:
            # Can't drag face-down cards.
            return

        if pile in self.tableau:
            # Grab this card AND everything above it in the column.
            idx = pile.index(card)
            self.dragging_cards = pile[idx:]
            # For dragging to look correct, every card in the group must be face up.
            # (In Klondike they always will be, because face-down cards are
            # always below all face-up ones in a column.)
            if any(not c.face_up for c in self.dragging_cards):
                self.dragging_cards = []
                return
        else:
            # Single-card drag from waste or foundation.
            self.dragging_cards = [card]

        self.drag_source_pile = pile
        # Remember the click offset so the card sits naturally under the cursor.
        self.drag_offset_x = mouse_pos[0] - card.x
        self.drag_offset_y = mouse_pos[1] - card.y

    def update_drag(self, mouse_pos):
        """Move the dragged stack so it follows the mouse."""
        if not self.dragging_cards:
            return
        # Compute where the top card of the drag stack should go.
        new_x = mouse_pos[0] - self.drag_offset_x
        new_y = mouse_pos[1] - self.drag_offset_y
        # Each subsequent card in the stack is offset by FACE_UP_OFFSET below.
        for i, card in enumerate(self.dragging_cards):
            card.x = new_x
            card.y = new_y + i * FACE_UP_OFFSET

    def end_drag(self, mouse_pos):
        """
        Attempt to drop the dragged cards at the mouse position.
        If the drop is illegal, snap the cards back to where they came from.
        """
        if not self.dragging_cards:
            return

        target_pile = self.get_pile_at_position(mouse_pos)
        first_card = self.dragging_cards[0]
        move_succeeded = False

        if target_pile is not None and target_pile is not self.drag_source_pile:
            # Decide which rule set applies based on which pile type we're over.
            if target_pile in self.foundations:
                # Foundations only accept single cards.
                if len(self.dragging_cards) == 1 and \
                        self.can_place_on_foundation(first_card, target_pile):
                    move_succeeded = True
            elif target_pile in self.tableau:
                if self.can_place_on_tableau(first_card, target_pile):
                    move_succeeded = True
            # (Stock/waste piles are never valid drop targets for the player.)

        if move_succeeded:
            # Remove dragged cards from the source pile (preserving order).
            for c in self.dragging_cards:
                self.drag_source_pile.remove(c)
            # Add them to the destination pile in the same order.
            for c in self.dragging_cards:
                target_pile.append(c)
                c.pile = target_pile
            # After pulling cards off a tableau column, flip the new top card.
            self.flip_top_if_needed(self.drag_source_pile)
            self.move_count += 1
            self.check_win()

        # Either way, clear the drag state and refresh positions.
        self.dragging_cards = []
        self.drag_source_pile = None
        self.update_card_positions()

    # ---- Win detection --------------------------------------------------
    def check_win(self):
        """The game is won when all four foundations have 13 cards each."""
        if all(len(f) == 13 for f in self.foundations):
            self.won = True

    # ---- Drawing --------------------------------------------------------
    def draw_empty_slot(self, pos, label=None):
        """Draw an outlined rectangle for an empty pile, with optional label."""
        x, y = pos
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        # Filled darker-green background so the slot is visible.
        pygame.draw.rect(self.screen, EMPTY_PILE_COLOR, rect, border_radius=8)
        # Thin outline.
        pygame.draw.rect(self.screen, LIGHT_GRAY, rect, width=2, border_radius=8)
        if label:
            txt = self.font_ui.render(label, True, LIGHT_GRAY)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

    def draw(self):
        """Draw the entire game frame."""
        # 1) Background (green felt).
        self.screen.fill(BG_COLOR)

        # 2) Stock pile.
        if self.stock:
            # Only draw the top card of the stock (they all overlap anyway).
            self.stock[-1].draw(
                self.screen, self.font_rank, self.font_suit_small, self.font_suit_big
            )
        else:
            # Empty stock = "recycle" indicator.
            self.draw_empty_slot(self.stock_pos, label='\u21BB')  # ↻

        # 3) Waste pile — draw only the top card.
        if self.waste:
            self.waste[-1].draw(
                self.screen, self.font_rank, self.font_suit_small, self.font_suit_big
            )
        else:
            self.draw_empty_slot(self.waste_pos)

        # 4) Foundation piles (top card only).
        for i, foundation in enumerate(self.foundations):
            if foundation:
                foundation[-1].draw(
                    self.screen, self.font_rank, self.font_suit_small, self.font_suit_big
                )
            else:
                # Empty foundation: show the suit symbol faintly to hint where
                # that suit's Ace should go... but classic Solitaire doesn't
                # actually assign suits to specific foundations, so leave blank.
                self.draw_empty_slot(self.foundation_positions[i], label='A')

        # 5) Tableau columns — draw EVERY card in each column, from bottom up.
        for i, column in enumerate(self.tableau):
            if not column:
                self.draw_empty_slot(self.tableau_positions[i], label='K')
            else:
                for card in column:
                    # Don't draw cards that are currently being dragged; we'll
                    # draw those last so they appear on top of everything.
                    if card in self.dragging_cards:
                        continue
                    card.draw(
                        self.screen, self.font_rank, self.font_suit_small, self.font_suit_big
                    )

        # 6) Dragged cards — drawn last so they sit on top of other cards.
        for card in self.dragging_cards:
            card.draw(
                self.screen, self.font_rank, self.font_suit_small, self.font_suit_big
            )

        # 7) UI text: move count and instructions.
        move_text = self.font_ui.render(f"Moves: {self.move_count}", True, WHITE)
        self.screen.blit(move_text, (SCREEN_WIDTH - 160, SCREEN_HEIGHT - 60))

        help_text = self.font_ui.render(
            "N: New game   |   Esc: Quit   |   Double-click to auto-move to foundation",
            True, WHITE
        )
        self.screen.blit(help_text, (MARGIN_X, SCREEN_HEIGHT - 30))

        # 8) Win banner.
        if self.won:
            self.draw_win_banner()

        # Finally, flip (swap) the back buffer to the screen so the player
        # sees everything we just drew.
        pygame.display.flip()

    def draw_win_banner(self):
        """Draw a big "You Win!" overlay when the game is complete."""
        # Semi-transparent dark overlay across the whole screen.
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))   # last value is alpha (transparency)
        self.screen.blit(overlay, (0, 0))

        # Big gold "You Win!" text, centered.
        title = self.font_big.render("You Win!", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(title, title_rect)

        # Subtitle with the move count.
        sub = self.font_ui.render(
            f"Completed in {self.move_count} moves.  Press N for a new game.",
            True, WHITE
        )
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(sub, sub_rect)

    # ---- Event handling -------------------------------------------------
    def handle_mouse_down(self, pos):
        """A mouse button was just pressed."""
        # If the player clicked the stock pile area, flip/recycle a card.
        stock_rect = pygame.Rect(*self.stock_pos, CARD_WIDTH, CARD_HEIGHT)
        if stock_rect.collidepoint(pos):
            self.flip_stock_card()
            return

        # Otherwise, see if they clicked a card.
        card, pile = self.get_clicked_card(pos)
        if card is None:
            return

        # Check for double-click (for auto-moving to foundation).
        now = pygame.time.get_ticks()
        is_double_click = (
            self.last_clicked_card is card
            and now - self.last_click_time <= self.DOUBLE_CLICK_MS
        )
        self.last_click_time = now
        self.last_clicked_card = card

        if is_double_click:
            # Try to auto-send this card to a foundation.
            if self.try_auto_move_to_foundation(card):
                # Reset double-click tracking so a triple-click doesn't
                # trigger another action accidentally.
                self.last_clicked_card = None
                return

        # Otherwise, begin dragging.
        self.start_drag(card, pile, pos)

    def handle_mouse_up(self, pos):
        """A mouse button was released: finish any ongoing drag."""
        self.end_drag(pos)

    def handle_key(self, key):
        """Keyboard shortcuts."""
        if key == pygame.K_n:
            self.deal_new_game()
        elif key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

    # ---- Main loop ------------------------------------------------------
    def run(self):
        """The main game loop. Runs until the user closes the window."""
        running = True
        while running:
            # --- Handle input events ------------------------------------
            # pygame.event.get() returns all events that have happened since
            # the last call. We loop through and respond to each one.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # User clicked the window's X button.
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Left mouse button pressed.
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    # Left mouse button released.
                    self.handle_mouse_up(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    # Mouse moved: if dragging, update the card positions.
                    if self.dragging_cards:
                        self.update_drag(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            # --- Draw the current frame ---------------------------------
            self.draw()

            # --- Cap the frame rate -------------------------------------
            # tick(FPS) pauses just long enough to maintain the target FPS.
            self.clock.tick(FPS)

        # Cleanup when the loop exits.
        pygame.quit()
        sys.exit()


# --- Entry point ------------------------------------------------------------
# This idiom means: "only run the game if this file was executed directly
# (not imported as a module from another script)."
if __name__ == "__main__":
    game = SolitaireGame()
    game.run()
