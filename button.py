class Button:
    def __init__(
        self,
        image=None,
        pos=(0, 0),
        text_input="",
        font=None,
        base_color=None,
        hovering_color=None,
        base_colour=None,
        hovering_colour=None,):

        self.image = image

        #Centre position of the button on screen
        self.x_position = pos[0]
        self.y_position = pos[1]

        #Font is required to render the label
        self.font = font
        if self.font is None:
            raise ValueError("Button requires font object")

        # Accept both UK and US colour spellings, no breaks
        self.base_colour = base_colour if base_colour is not None else base_color
        self.hovering_colour = hovering_colour if hovering_colour is not None else hovering_color

        # Safe defaults so drawing never crashes on a missing colour
        if self.base_colour is None:
            self.base_colour = "White"
        if self.hovering_colour is None:
            self.hovering_colour = "White"

        self.text_input = text_input

        #render the label in the base colour
        self.text_surface = self.font.render(self.text_input, True, self.base_colour)

        #If no image was supplied, use the text surface itself as the clickable area
        if self.image is None:
            self.image = self.text_surface

        #Rectangles used for click and drawing
        self.rect = self.image.get_rect(center=(self.x_position, self.y_position))
        self.text_rect = self.text_surface.get_rect(center=(self.x_position, self.y_position))

    def update(self, screen):
        """Draws the button image and label onto the given surface."""
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def check_clicked(self, mouse_position):
        """Returns True if the mouse position is inside this button's rectangle."""
        return (
            mouse_position[0] in range(self.rect.left,  self.rect.right)
            and mouse_position[1] in range(self.rect.top, self.rect.bottom))

    def update_color(self, mouse_position):
        """Swaps the label colour to the hover colour when the mouse is over the button."""
        if self.check_clicked(mouse_position):
            self.text_surface = self.font.render(self.text_input, True, self.hovering_colour)
        else:
            self.text_surface = self.font.render(self.text_input, True, self.base_colour)