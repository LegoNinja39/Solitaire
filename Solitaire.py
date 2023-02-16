import sys, pygame, random, os
from itertools import cycle

pygame.init()
pygame.font.init()
random.seed()

#region Screen Generation

# Sizes
TILE_SIZE = 76
HALF_TILE = TILE_SIZE // 2
NUMBER_OF_CARDS = 7
BUFFER_SIZE = TILE_SIZE // NUMBER_OF_CARDS
CARD_SIZE = (TILE_SIZE, int(TILE_SIZE + HALF_TILE))
WORLD_WIDTH = NUMBER_OF_CARDS + 1
WORLD_HEIGHT = NUMBER_OF_CARDS + 1
# Because pygame adds a pixel to right and bottom of rects
SCREEN_WIDTH = min(CARD_SIZE[0] * WORLD_WIDTH + NUMBER_OF_CARDS, pygame.display.Info().current_w - TILE_SIZE)
SCREEN_HEIGHT = min(CARD_SIZE[1] * WORLD_HEIGHT, pygame.display.Info().current_h - TILE_SIZE)

# Basic colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (172, 172, 172)
rgb = {0: (255, 0, 0), 1: (0, 255, 0), 2: (0, 0, 255)}

# Keeps everything running
running = True
gameOver = False
FPS = 60
mouseHeld = False
resetDown = False
elapsedTime = FPS // 2

# Makes the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill(BLACK)
pygame.display.set_caption("Solitaire")

# Converts a screen space tuple to world space
def toGrid(screenCoords: tuple) -> tuple:
    # Finds the number of buffer spaces
    bufferNumber = tuple(map(lambda i: (i - BUFFER_SIZE) // TILE_SIZE, screenCoords))

    # Finds the grid coords
    gridCoord = tuple(map(lambda sc, bn: (sc - (bn * BUFFER_SIZE)) // TILE_SIZE, screenCoords, bufferNumber))

    # Makes sure it is not off the screen
    return tuple(max(0, min(i, SCREEN_HEIGHT)) for i in gridCoord)

# Converts a world space tuple to screen space
def toScreen(gridCoords: tuple) -> tuple:
    return tuple(map(lambda i: (i * TILE_SIZE) + ((i + 1) * BUFFER_SIZE), gridCoords))

#endregion

#region Cards
scriptPath = os.path.realpath(__file__).split("\\Solitaire.py")[0]
scriptPath = os.path.join(scriptPath, "PNG-cards-1.3")

try:
    basePath = sys._MEIPASS
except:
    basePath = os.path.abspath(".")

imagePath = os.path.join(basePath, scriptPath)

SUITS = ["hearts", "clubs", "diamonds", "spades"]
NUMBERS = ["ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king"]
CARD_BACK: pygame.Surface = pygame.transform.smoothscale(
    pygame.image.load(os.path.join(imagePath, "cardBack.jpg")), CARD_SIZE).convert()

class Card():
    def __init__(self, cSuit="hearts", cNumber="2"):
        # Initializes some variables
        self._suit = cSuit
        self._colour = SUITS.index(self.suit) % 2
        self._number = cNumber
        self._value = NUMBERS.index(self.number)
        self.location = (-1, -1)
        self.clickable = False

        # Gets the correct card image
        fileName = self.number + "_of_" + self.suit + ".png"
        self.cardFront = pygame.transform.smoothscale(
            pygame.image.load(os.path.join(imagePath, fileName)), CARD_SIZE).convert()

        # Sets the size and makes a Rect around the image
        self.image = CARD_BACK
        self.cardRect = self.image.get_rect()

    # Flips the card and either makes it active or inactve
    def flipCard(self):
        if self.image == CARD_BACK:
            self.image = self.cardFront
            self.clickable = True
        else:
            self.image = CARD_BACK
            self.clickable = True

    @property
    def suit(self): return self._suit
    
    @property
    def number(self): return self._number

    @property
    def value(self): return self._value
    
    @property
    def colour(self): return self._colour

#endregion

#region Locations

TABLEAU_TOP = 2
tableauLocations = [
    pygame.rect.Rect(toScreen((0, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((1, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((2, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((3, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((4, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((5, TABLEAU_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((6, TABLEAU_TOP)), CARD_SIZE)
    ]

FOUNDATION_TOP = 0
foundationLocations= [
    pygame.rect.Rect(toScreen((3, FOUNDATION_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((4, FOUNDATION_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((5, FOUNDATION_TOP)), CARD_SIZE),
    pygame.rect.Rect(toScreen((6, FOUNDATION_TOP)), CARD_SIZE)
]

wasteLocation = pygame.rect.Rect(toScreen((1, 0)), CARD_SIZE)

deckLocation = pygame.rect.Rect(toScreen((0, 0)), CARD_SIZE)

menuLocation = pygame.rect.Rect(toScreen((2, 0)), CARD_SIZE)

resetButton = pygame.rect.Rect((menuLocation.left + BUFFER_SIZE, menuLocation.top), (menuLocation.width - (BUFFER_SIZE * 2), HALF_TILE // 2))

#endregion

#region Text

# Winning text
winMessage = pygame.font.SysFont("Arial", 48).render("You Win", True, WHITE)
winDisplay = winMessage.get_rect()
winDisplay.center = screen.get_rect().center

# A surface that is entirely white with its colour key also white
# which makes it transparent and allows Game Over to flash
# The start message display is a bit larger so it will work for both
displayBlank = pygame.Surface(winDisplay.size)
displayBlank.fill(WHITE)
displayBlank.set_colorkey(WHITE)
displayBlank.set_alpha(0)

# The two surfaces to cycle between
gameOverCycle = cycle([winMessage, displayBlank])
gameOverSurface = next(gameOverCycle)

# Reset Button
resetMessage = pygame.font.SysFont("Arial", 16).render("Reset", True, BLACK, WHITE)
resetRect = resetMessage.get_rect()
resetRect.center = resetButton.center

# Control Text
menuText = [
    pygame.font.SysFont("Arial", 16).render("Press button", True, WHITE, BLACK),
    pygame.font.SysFont("Arial", 16).render("or R to reset", True, WHITE, BLACK),
    pygame.font.SysFont("Arial", 16).render("Press esc to", True, WHITE, BLACK),
    pygame.font.SysFont("Arial", 16).render("quit game", True, WHITE, BLACK),
]

firstlineRect = menuText[0].get_rect()
firstlineRect.centerx = resetButton.centerx
firstlineRect.top = resetButton.bottom + BUFFER_SIZE

# List to call blits with
menuDisplay = [(menuText[0], firstlineRect)]

# Cycle through every line and add it to the blits list
for index, line in enumerate(menuText[1::]):
    # Gets a rect for the line
    lineRect = line.get_rect()

    # Left alines based on the first line and moves the top to the bottom of the previous line
    lineRect.left = firstlineRect.left
    lineRect.top = (menuDisplay[index][1].bottom)

    menuDisplay.append((line, lineRect))

#endregion

#region Lists

# The deck of cards
deckOfCards = [Card(s, n) for s in SUITS for n in NUMBERS]
random.shuffle(deckOfCards)

# Currently picked up cards
activeCards = []
clickedCard: Card = None

# All the cards in the tableaux
tableauCards = [[], [], [], [], [], [], []]

# All the cards in the foundations
foundationCards = [[], [], [], []]

# Waste pile cards
wastePile = []

#endregion

# Updates the screen
def updateScreen():
    screen.fill(BLACK)
    
    # Tableau boxes
    for r in tableauLocations:
        pygame.draw.rect(screen, WHITE, r, 1)

    # Foundation boxes
    for r in foundationLocations:
        pygame.draw.rect(screen, WHITE, r, 1)

    # Deck box
    pygame.draw.rect(screen, WHITE, deckLocation, 1)

    # Waste box
    pygame.draw.rect(screen, WHITE, wasteLocation, 1)

    # Menu text
    screen.blits(menuDisplay)

    # Reset button
    pygame.draw.rect(screen, WHITE, resetButton, 0, resetButton.height // 4)
    screen.blit(resetMessage, resetRect)

    # Cards in the tableau
    for col in tableauCards:
        for card in col:
            screen.blit(card.image, card.cardRect)

    # Cards in the foundations
    for col in foundationCards:
        if len(col) > 0:
            screen.blit(col[-1].image, col[-1].cardRect)

    # If there are still cards in the deck, draw a face down card
    if deckOfCards:
        screen.blit(CARD_BACK, deckLocation)

    # Draws the top waste card
    if wastePile:
        screen.blit(wastePile[-1].image, wasteLocation)

    # Draw any cards that are picked up
    if activeCards:
        screen.blits(tuple(zip((c.image for c in activeCards), (c.cardRect for c in activeCards))))


    # Flashes a win message
    if not running:
        screen.blit(gameOverSurface, winDisplay)

    pygame.display.update()

# Snap a card to a valid location
def snapCard(card: Card, newLoc: bool):
    # If the card is moving to the location of the cursor
    if newLoc:
        # Get the current location of the card
        gridCoords = toGrid(card.cardRect.center)
        card.location = (gridCoords[0], len(tableauCards[gridCoords[0]]))

    # Else the card snaps back to where it started
    # The location property is only changed here

    # If the card needs to snap back to the waste pile
    if card.location[0] == -1: 
        card.cardRect.topleft = wasteLocation.topleft
        wastePile.append(card)

    # Otherwise snap the card to a tableau
    else:
        card.cardRect.topleft = tableauLocations[card.location[0]].topleft
        card.cardRect.top += (len(tableauCards[card.location[0]]) * HALF_TILE)

        tableauCards[card.location[0]].append(card)

# Flips the next tableau card
def flipTableau(column: int):
    # Makes sure it's a valid number
    if column >= 0 and column < len(tableauCards):

        # Flip the next card on the tableau
        if len(tableauCards[column]) > 0 and not tableauCards[column][-1].clickable: tableauCards[column][-1].flipCard()
    
    # Otherwise it's from the waste pile, so flip that
    elif wastePile: wastePile[-1].flipCard()

# Sets the active cards
def setActiveCards(card: Card):
    global activeCards
    global clickedCard

    # Places all the cards available from the tableau in to the active cards list
    activeCards = [c for c in tableauCards[card.location[0]] if c.clickable]

    # Removes all the active cards from the tableau
    for c in activeCards:
        tableauCards[card.location[0]].remove(c)

    clickedCard = activeCards[0]

# Checks for valid placement of active cards
def legalMove(tableauNumber: int) -> bool:
    global activeCards
    global clickedCard

    # Gets the last card of the column
    lastCard: Card = tableauCards[tableauNumber][-1] if len(tableauCards[tableauNumber]) > 0 else None

    # If there is nothing in that tableau
    if lastCard is None:
        # If the clicked card is a King it is valid otherwise it is not
        if clickedCard.number == "king":
            flipTableau(clickedCard.location[0])
            return True
        else: return False

    # Else do checks on the last card in the column
    else:
        # Cards can't be the same colour
        if lastCard.colour == clickedCard.colour: return False

        # Cards can only be placed on a card 1 higher
        elif lastCard.value != clickedCard.value + 1: return False

        # Cards were moved back to their starting location
        elif lastCard.location[0] == clickedCard.location[0]: return False

        # The move is legal
        else: 
            flipTableau(clickedCard.location[0])
            return True

# Checks if the card can be moved to the foundation
def foundationMove(card: Card) -> bool:
    column = SUITS.index(card.suit)

    # If the card is an ace just move it to the correct place
    if card.number == "ace":
        card.cardRect.topleft = foundationLocations[column].topleft
        foundationCards[column].append(card)

        card.clickable = False
        return True

    # If cards have already been added to the foundation
    elif len(foundationCards[column]) > 0:
        # If the card is one more than the current top of the foundation, add it
        if foundationCards[column][-1].value == (card.value - 1):
            card.cardRect.topleft = foundationLocations[column].topleft
            foundationCards[column].append(card)

            card.clickable = False
            return True

    # Else return false
    else: return False

# Deals out the cards to start the game
def dealCards():
    # Places all the cards in the correct columns
    for i in range(len(tableauCards)):
        for j in range(6, i - 1, -1):
            # Get the top card off the deck
            topCard = deckOfCards.pop()

            # Set its location
            topCard.cardRect.topleft = toScreen((j, TABLEAU_TOP))

            # Add it to the correct list
            tableauCards[j].append(topCard)
            topCard.location = (j, i)

    # Fixes the cards after they are dealt
    for col in tableauCards:
        for i, card in enumerate(col):
            # Slides the cards so they can be seen
            card.cardRect.top += (HALF_TILE * i)

            # Flips the bottom card and makes them clickable
            if i == len(col) - 1:
                card.image = card.cardFront
                card.clickable = True

# Moves tableau cards
def tableauClick(column: int) -> bool:
    if foundationMove(tableauCards[column][-1]):
        tableauCards[column].pop()
        flipTableau(column)
        return False

    elif tableauCards[column]:
        setActiveCards(tableauCards[column][-1])
        return True

    else: return False

# Move cards from the deck to the waste pile
def deckClick():
    drawnCard: Card = None

    if not deckOfCards:
        wastePile[-1].flipCard()

        for i in range(len(wastePile)):
            wastePile[-1].cardRect.topleft = deckLocation.topleft
            deckOfCards.append(wastePile.pop())

    else:
        # Make the top of the waste pile unclickable
        if len(wastePile) > 0: wastePile[-1].flipCard()

        # Pop off the top three cards of the deck and add them to the waste pile
        for i in range(3):
            # Make sure there is another card to pop
            if deckOfCards:
                drawnCard = deckOfCards.pop()
                drawnCard.cardRect.topleft = wasteLocation.topleft
                wastePile.append(drawnCard)
            else: break

        # Makes the top card of the waste pile clickable
        wastePile[-1].flipCard()

# Moves cards from the waste pile
def wasteClick() -> bool:
    global clickedCard
    global activeCards
    clickedCard = wastePile.pop()

    # Tries to move the top card to the foundation
    if foundationMove(clickedCard):
        flipTableau(clickedCard.location[0])
        clickedCard = None
        return False
    
    # If it can't then make the top card the active card
    else:
        activeCards.append(clickedCard)
        return True

# Resets everything
def resetClick():
    # WHY PYTHON WHY
    global clickedCard
    global activeCards
    global tableauCards
    global foundationCards
    global wastePile
    global deckOfCards

    # Clears everything
    activeCards.clear()
    for col in tableauCards: col.clear()
    for col in foundationCards: col.clear()
    wastePile.clear()
    deckOfCards.clear()
    clickedCard = None

    # Easier to just release all the memory and make new cards
    deckOfCards = [Card(s, n) for s in SUITS for n in NUMBERS]
    random.shuffle(deckOfCards)

    dealCards()

dealCards()

# Main loop
while running:
    # Checks for any events
    for event in pygame.event.get():
        # Closes the program
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            resetClick()

        # Gets mouse events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Gets the grid of the mouse so it only checks one tableau
            mousePos = toGrid(event.pos)

            # Checks to see if the user clicked on a tableau card
            if mousePos[1] >= TABLEAU_TOP:
                mouseHeld = tableauClick(mousePos[0])

            # Check to see if the user clicked on something above the tableaus
            else:
                if deckLocation.collidepoint(event.pos): deckClick()
                if wasteLocation.collidepoint(event.pos) and wastePile: mouseHeld = wasteClick()
                if resetButton.collidepoint(event.pos): resetDown = True

        # Drops the picked up card
        elif event.type == pygame.MOUSEBUTTONUP:
            # If the player was moving a card around
            if mouseHeld:
                # Checks if the move was valid
                valid = legalMove(toGrid(clickedCard.cardRect.center)[0])

                # Moves the cards to the approriate locations
                for card in activeCards: 
                    snapCard(card, valid)

                # Reset the variables
                clickedCard = None
                activeCards.clear()
                mouseHeld = False
            
            # If the reset button was pressed and the mouse is still over the button
            elif resetDown and resetButton.collidepoint(event.pos): resetClick()


    # Moves the card with the mouse
    if mouseHeld:
        # Makes the top card follow the mouse
        clickedCard.cardRect.center = tuple(map(lambda i, j: (i - j) + j, pygame.mouse.get_pos(), clickedCard.cardRect.center))

        # Makes all the other cards follow the clicked card
        for i, card in enumerate(activeCards[1::], 1):
            card.cardRect.topleft = (clickedCard.cardRect.left, clickedCard.cardRect.top + (HALF_TILE * i))

    # Checks for a win
    for col in foundationCards:
        # If any of the foundations do not have 13 cards,
        # the loop will break and skip the else
        if len(col) != 13: break
    else: running = False

    updateScreen()
    pygame.time.Clock().tick(FPS)

screen.blit(gameOverSurface, winDisplay)

while not running:
    elapsedTime -= 1
    for event in pygame.event.get():
        # Closes the program on exit button or key press
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
            pygame.quit()
            sys.exit()

    if elapsedTime <= 0:
        gameOverSurface = next(gameOverCycle)
        elapsedTime = FPS // 2
        
    updateScreen()
    pygame.time.Clock().tick(FPS)