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
    Modified by Frank Tompa, 2015
    Packaged with mathtuples. Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
__author__ = 'Nidhin, FWTompa'


class MathML:
    """
    List of recognized tags
    """
    namespace = '{http://www.w3.org/1998/Math/MathML}'
    math = namespace + 'math'
    mn = namespace + 'mn'
    mo = namespace + 'mo'
    mi = namespace + 'mi'
    mtext = namespace + 'mtext'
    mrow = namespace + 'mrow'
    msub = namespace + 'msub'
    msup = namespace + 'msup'
    msubsup = namespace + 'msubsup'
    munderover = namespace + 'munderover'
    msqrt = namespace + 'msqrt'
    mroot = namespace + 'mroot'
    mfrac = namespace + 'mfrac'
    menclose = namespace + 'menclose'
    mfenced = namespace + 'mfenced'
    mover = namespace + 'mover'
    munder = namespace + 'munder'
    mpadded = namespace + 'mpadded'
    mphantom = namespace + 'mphantom'
    none = namespace + 'none'
    mstyle = namespace + 'mstyle'
    mspace = namespace + 'mspace'
    mtable = namespace + 'mtable'
    mtr = namespace + 'mtr'
    mtd = namespace + 'mtd'
    semantics = namespace + 'semantics'
    mmultiscripts = namespace + 'mmultiscripts'
    mprescripts = namespace + 'mprescripts'
    mqvar = '{http://search.mathweb.org/ns}qvar'
    mqvar2 = namespace + 'qvar' # for erroneous namespace
    merror = namespace + 'merror'  # To deal with Errors in MathML conversion from tools (KMD)
