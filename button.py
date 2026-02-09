class Button:
    def __init__(
        self,
        image=None,
        pos=(0, 0),
        text_input="",
        font=None,
        base_colour="White",
        hovering_colour="White",
    ):
        self.image = image
        self.centre_x = pos[0]
        self.centre_y = pos[1]

        self.font = font
        if self.font is None:
            raise ValueError("Button requires font object")

        self.base_colour = base_colour
        self.hovering_colour = hovering_colour
        self.text_input = text_input

        self.text_surface = self.font.render(self.text_input, True, self.base_colour)

        if self.image is None:
            self.image = self.text_surface

        self.rect = self.image.get_rect(center=(self.centre_x, self.centre_y))
        self.text_rect = self.text_surface.get_rect(center=(self.centre_x, self.centre_y))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def check_clicked(self, mouse_position):
        return self.rect.collidepoint(mouse_position)

    def update_colour(self, mouse_position):
        if self.check_clicked(mouse_position):
            self.text_surface = self.font.render(self.text_input, True, self.hovering_colour)
        else:
            self.text_surface = self.font.render(self.text_input, True, self.base_colour)