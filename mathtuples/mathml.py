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
    semantics = namespace + 'semantics'

    # token elements
    mi = namespace + 'mi'
    mn = namespace + 'mn'
    mo = namespace + 'mo'
    mtext = namespace + 'mtext'
    mspace = namespace + 'mspace'
    ms = namespace + 'ms'        # missing
    mglyph = namespace + 'mglyph'

    # general layout schemata
    mrow = namespace + 'mrow'
    mfrac = namespace + 'mfrac'
    msqrt = namespace + 'msqrt'
    mroot = namespace + 'mroot'
    mstyle = namespace + 'mstyle'
    merror = namespace + 'merror'  # To deal with Errors in MathML conversion from tools (KMD)
    mpadded = namespace + 'mpadded'
    mphantom = namespace + 'mphantom'
    mfenced = namespace + 'mfenced'
    menclose = namespace + 'menclose'

    # Script and Limit Schemata
    msub = namespace + 'msub'
    msup = namespace + 'msup'
    msubsup = namespace + 'msubsup'
    munder = namespace + 'munder'
    mover = namespace + 'mover'
    munderover = namespace + 'munderover'
    mmultiscripts = namespace + 'mmultiscripts'
    mprescripts = namespace + 'mprescripts'
    none = namespace + 'none'

    # Tables and Matrices
    mtable = namespace + 'mtable'
    mlabeledtr = namespace + 'mlabeledtr'
    mtr = namespace + 'mtr'
    mtd = namespace + 'mtd'
    maligngroup = namespace + 'maligngroup'
    malignmark = namespace + 'malignmark'

    # Elementary Math Layout
    mstack = namespace + 'mstack'
    mlongdiv = namespace + 'mlogdiv'
    msgroup = namespace + 'msgroup'
    msrow = namespace + 'msrow'
    mscarries = namespace + 'mscarries'
    mscarry = namespace + 'mscarry'
    msline = namespace + 'msline'

    # Enlivening Expresions
    maction = namespace + 'maction'

    # NTCIR Wildcards
    mqvar = '{http://search.mathweb.org/ns}qvar'
    mqvar2 = namespace + 'qvar' # for erroneous namespace
