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

        #Button centre position
        self.x_position = pos[0]
        self.y_position = pos[1]

        # Font must be provided to render text
        self.font = font
        if self.font is None:
            raise ValueError("Button requires font object")

        # Support both UK and US spellings (swapping systems would cause issues with spellings - e.g base_colour not found should be base_color) so made this accept both just so i didnt have to debug
        self.base_colour = base_colour if base_colour is not None else base_color
        self.hovering_colour = hovering_colour if hovering_colour is not None else hovering_color

        #defaults to avoid crashes 
        if self.base_colour is None:
            self.base_colour = "White"
        if self.hovering_colour is None:
            self.hovering_colour = "White"

        self.text_input = text_input

        # Render text 
        self.text_surface = self.font.render(self.text_input, True, self.base_colour)

        # If no image is provided, use the text surface as the clickable image
        if self.image is None:
            self.image = self.text_surface

        # Rectangles for collision checking and drawing
        self.rect = self.image.get_rect(center=(self.x_position, self.y_position))
        self.text_rect = self.text_surface.get_rect(center=(self.x_position, self.y_position))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def checkForInput(self, mouse_position):
        return (
            mouse_position[0] in range(self.rect.left, self.rect.right)
            and mouse_position[1] in range(self.rect.top, self.rect.bottom))

    def changeColor(self, mouse_position):
        if self.checkForInput(mouse_position):
            self.text_surface = self.font.render(self.text_input, True, self.hovering_colour)
        else:
            self.text_surface = self.font.render(self.text_input, True, self.base_colour)
