# -*- coding: utf-8 -*-
#
# Copyright (©) 2012 Gustavo Noronha Silva (gns@gnome.org)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

from gi.repository import GObject, Gedit


class TrailingSpaces(GObject.Object, Gedit.ViewActivatable):
    __gtype_name__ = "TrailingSpaces"

    view = GObject.property(type = Gedit.View)

    regex = re.compile('\s+$')


    def do_activate(self):
        self.buffer = self.view.get_buffer()

        self.cursor_line = self._get_cursor_line()

        if not self.buffer.get_tag_table().lookup('tailing_spaces'):
            self.tag = self.buffer.create_tag('trailing_spaces')
            self.tag.set_property('background', 'red')

        self.buffer.connect('loaded', self._check_buffer_cb)
        self.buffer.connect_after('insert-text', self._text_inserted_cb)
        self.buffer.connect('notify::cursor-position', self._cursor_moved_cb)


    def _check_buffer_cb(self, *args):
        self.check_buffer()


    def _text_inserted_cb(self, buffer, location, text, length):
        if text == '\n':
            self.untrail_previous(location)
            return


    def _get_cursor_line(self):
        cursor_offset = self.buffer.get_property('cursor-position')
        return self.buffer.get_iter_at_offset(cursor_offset).get_line()


    def _cursor_moved_cb(self, *args):
        current_line = self._get_cursor_line()
        if self.cursor_line == current_line:
            return

        previous_line = self.buffer.get_iter_at_line(self.cursor_line)
        self.check_line(previous_line)

        self.cursor_line = current_line

        line = self.buffer.get_iter_at_line(current_line)
        if line.get_char() == u'\n':
            return

        line_end = line.copy()
        line_end.forward_to_line_end()

        self.buffer.remove_tag_by_name('trailing_spaces', line, line_end)



    def find_trailing_spaces(self, line):
        line_end = line.copy()
        line_end.forward_to_line_end()

        text = line.get_visible_text(line_end)
        match = self.regex.search(text)

        if not match or match.string == '\n':
            return None, None

        trailing_start = line_end.copy()
        trailing_start.backward_chars(match.end() - match.start())
        return trailing_start, line_end


    def untrail_previous(self, line):
        previous = line.copy()

        previous.backward_line()
        if previous.get_line() == line.get_line():
            return

        trailing_start, line_end = self.find_trailing_spaces(previous)
        if not trailing_start:
            return

        line_number = line.get_line()

        self.buffer.delete(trailing_start, line_end)

        # Revalidate the iter, for other plugins to act.
        line.assign(self.buffer.get_iter_at_line(line_number))


    def check_buffer(self):
        line = self.buffer.get_start_iter()
        if line.get_line() != self.cursor_line:
            self.check_line(line)

        while line.forward_line():
            if line.get_line() != self.cursor_line:
                self.check_line(line)


    def check_line(self, line):
        line_end = line.copy()
        line_end.forward_to_line_end()

        self.buffer.remove_tag_by_name('trailing_spaces', line, line_end)

        trailing_start, line_end = self.find_trailing_spaces(line)
        if not trailing_start:
            return

        self.buffer.apply_tag_by_name('trailing_spaces', trailing_start, line_end)


    def do_deactivate(self):
        pass


    def do_update_state(self):
        self.check_buffer()

