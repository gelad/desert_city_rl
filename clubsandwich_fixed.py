"""
    This module contains some fixes for Clubsanwich classes
"""
from clubsandwich.ui import View
from clubsandwich.geom import Size, Point
from bearlibterminal import terminal

class LabelViewFixed(View):
  """
  Draws the given string inside its bounds. Multi-line strings work fine.

  :param str text: Text to draw
  :param str color_fg: Foreground color
  :param str color_bg: Background color (only applies on terminal layer zero)
  :param 'center'|'left'|'right' align_horz: Horizontal alignment
  :param 'center'|'top'|'bottom' align_vert: Vertical alignment

  See :py:class:`View` for the rest of the init arguments.
  
  FIX: bearlib tags in [] now don't affect text alignment
  """
  def __init__(
      self, text, color_fg='#ffffff', color_bg='#000000',
      align_horz='center', align_vert='center',
      *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.align_horz = align_horz
    self.align_vert = align_vert
    self.text = text
    self.color_fg = color_fg
    self.color_bg = color_bg

  @property
  def intrinsic_size(self):
      width, height = terminal.measure(self.text)
      return Size(width, height)

  def draw(self, ctx):
    ctx.color(self.color_fg)
    ctx.bkcolor(self.color_bg or '#000000')
    if self.clear:
      ctx.clear_area(self.bounds)
    x = 0
    if self.align_horz == 'center':
      x = self.bounds.width / 2 - self.intrinsic_size.width / 2
    elif self.align_horz == 'right':
      x = self.bounds.width - self.intrinsic_size.width

    y = 0
    if self.align_vert == 'center':
      y = self.bounds.height / 2 - self.intrinsic_size.height / 2
    elif self.align_vert == 'bottom':
      y = self.bounds.height - self.intrinsic_size.height

    ctx.print(Point(x, y).floored, self.text)

  def debug_string(self):
    return super().debug_string() + ' ' + repr(self.text)


class ButtonViewFixed(View):
  """
  :param str text: Button title
  :param func callback: Function to call when button is activated. Takes no
                        arguments.
  :param str align_horz: Horizontal alignment. See :py:class:`LabelView`.
  :param str align_vert: Vertical alignment. See :py:class:`LabelView`.

  See :py:class:`View` for the rest of the init arguments.

  Contains a label. Can be first responder. When a button is the first
  responder:

  * The label is drawn black-on-white instead of white-on-black
  * Pressing the Enter key calls *callback*
  FIX: bearlib tags in [] now don't affect text alignment (LabelViewFixed is used)
  """
  def __init__(
      self, text, callback, align_horz='center', align_vert='center',
      *args, **kwargs):
    self.label_view = LabelViewFixed(text, align_horz=align_horz, align_vert=align_vert)
    super().__init__(subviews=[self.label_view], *args, **kwargs)
    self.callback = callback

  def set_needs_layout(self, val):
    super().set_needs_layout(val)
    self.label_view.set_needs_layout(val)

  def did_become_first_responder(self):
      self.label_view.color_fg = '#000000'
      self.label_view.color_bg = '#ffffff'

  def did_resign_first_responder(self):
      self.label_view.color_fg = '#ffffff'
      self.label_view.color_bg = '#000000'

  def draw(self, ctx):
    if self.clear:
      ctx.bkcolor(self.color_bg)
      ctx.clear_area(self.bounds)

  @property
  def text(self):
    return self.label_view.text

  @text.setter
  def text(self, new_value):
    self.label_view.text = new_value

  @property
  def intrinsic_size(self):
    return self.label_view.intrinsic_size

  def layout_subviews(self):
    super().layout_subviews()
    self.label_view.frame = self.bounds

  @property
  def can_become_first_responder(self):
    return True

  def terminal_read(self, val):
    if val == terminal.TK_ENTER:
      self.callback()
      return True
