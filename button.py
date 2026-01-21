class Button:
    def __init__(self, image, pos, text_input, font, base_color=None, hovering_color=None, base_colour=None, hovering_colour=None):
        self.image = image
        
        #Button centre position
        self.x_position = pos[0]
        self.y_position = pos[1]

        self.font = font

        # Colours exception handling issues came with use colour py wouldn't recognise it 
        self.base_colour = base_colour if base_colour is not None else base_color
        self.hovering_colour = hovering_colour if hovering_colour is not None else hovering_color

        self.text_input = text_input
        self.text_surface = self.font.render(self.text_input, True, self.base_colour)

        #If no image is there, use the text as the button image
        if self.image is None:
            self.image = self.text_surface

        self.rect = self.image.get_rect(center=(self.x_position, self.y_position))
        self.text_rect = self.text_surface.get_rect(center=(self.x_position, self.y_position))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def checkForInput(self, mouse_position):
        if (mouse_position[0] in range(self.rect.left, self.rect.right) and mouse_position[1] in range(self.rect.top, self.rect.bottom)):
            return True
        return False

    def changeColor(self, mouse_position):
        if (mouse_position[0] in range(self.rect.left, self.rect.right) and mouse_position[1] in range(self.rect.top, self.rect.bottom)):
            self.text_surface = self.font.render(self.text_input, True, self.hovering_colour)
        else:
            self.text_surface = self.font.render(self.text_input, True, self.base_colour)
