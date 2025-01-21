"""
    Tangent
    Copyright (c) 2013 David Stalnaker, Richard Zanibbi

    This file is part of Tangent.

    Tangent is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - David Stalnaker: david.stalnaker@gmail.com
        - Richard Zanibbi: rlaz@cs.rit.edu
    Modified by Nidhin Pattaniyil, 2014
    Packaged with mathtuples. Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
__author__ = 'Nidhin'


class UnknownTagException(Exception):
    """
    An exception to indicate unknown Mathml tag
    """

    def __init__(self, tag):
        self.tag = tag
