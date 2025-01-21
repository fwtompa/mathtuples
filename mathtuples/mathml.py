"""
    Tangent
    Copyright (c) 2013 David Stalnaker, Richard Zanibbi

    This file is part of Tangent and Tangent-S.

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

    Note, however, that Tangent-S source code (used for converting
    Content MathML to OpT trees), data and results were released under
    a Non-Commercial Creative Commons License (see the LICENSE file).  

    Contact:
        - David Stalnaker: david.stalnaker@gmail.com
        - Richard Zanibbi: rlaz@cs.rit.edu
    Modified by Nidhin Pattaniyil, 2014
    Modified by Kenny Davila, 2014
    Modified by Frank Tompa, 2015
    Packaged with mathtuples. Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
__author__ = 'Nidhin, KDavila, FWTompa'


class MathML:
    """
    List of recognized tags
    """
    namespace_URL = 'http://www.w3.org/1998/Math/MathML'
    namespace = '{' + namespace_URL + '}'

    """
        Presentation MathML only
    """
    math = namespace + 'math'

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


    """
        Content MathML only
    """
    semantics = namespace + 'semantics'

    ci = namespace + "ci"
    cn = namespace + "cn"
    csymbol = namespace + "csymbol"
    cerror = namespace + "cerror"

    apply = namespace + "apply"
    matrix = namespace + "matrix"
    matrixrow = namespace + "matrixrow"
    share = namespace + "share"
    vector = namespace + "vector"

    _abs = namespace + "abs"
    _and = namespace + "and"
    _in = namespace + "in"
    _not = namespace + "not"
    _or = namespace + "or"
    approx = namespace + "approx"
    arccos = namespace + "arccos"
    arccot = namespace + "arccot"
    arccsc = namespace + "arccsc"
    arcsin = namespace + "arcsin"
    arcsec = namespace + "arcsec"
    arctan = namespace + "arctan"

    arccosh = namespace + "arccosh"
    arccoth = namespace + "arccoth"
    arccsch = namespace + "arccsch"
    arcsinh = namespace + "arcsinh"
    arcsech = namespace + "arcsech"
    arctanh = namespace + "arctanh"

    arg = namespace + "arg"
    bvar = namespace + "bvar"
    ceiling = namespace + "ceiling"
    compose = namespace + "compose"
    cos = namespace + "cos"
    cosh = namespace + "cosh"
    cot = namespace + "cot"
    coth = namespace + "coth"
    csc = namespace + "csc"
    csch = namespace + "csch"
    degree = namespace  + "degree"
    determinant = namespace + "determinant"
    divide = namespace + "divide"
    emptyset = namespace + "emptyset"
    eq = namespace + "eq"
    equivalent = namespace + "equivalent"
    exp = namespace + "exp"
    exists = namespace + "exists"
    factorial = namespace + "factorial"
    floor = namespace + "floor"
    forall = namespace + "forall"
    gcd = namespace + "gcd"
    geq = namespace + "geq"
    gt = namespace + "gt"
    imaginary = namespace + "imaginary"
    imaginaryi = namespace + "imaginaryi"
    implies = namespace + "implies"
    infinity = namespace + "infinity"
    int = namespace + "int"
    interval = namespace + "interval"
    intersect = namespace + "intersect"
    leq = namespace + "leq"
    list = namespace + "list"
    limit = namespace + "limit"
    log = namespace + "log"
    lowlimit = namespace + "lowlimit"
    ln = namespace + "ln"
    lt = namespace + "lt"
    max = namespace + "max"
    min = namespace + "min"
    minus = namespace + "minus"
    moment = namespace + "moment"
    momentabout = namespace + "momentabout"
    notin = namespace + "notin"
    notsubset = namespace + "notsubset"
    notprsubset = namespace + "notprsubset"
    neq = namespace + "neq"
    partialdiff = namespace + "partialdiff"
    plus = namespace + "plus"
    prsubset = namespace + "prsubset"
    real = namespace + "real"
    root = namespace + "root"
    sec = namespace + "sec"
    sech = namespace + "sech"
    set = namespace + "set"
    setdiff = namespace + "setdiff"
    sin = namespace + "sin"
    sinh = namespace + "sinh"
    subset = namespace + "subset"
    sum = namespace + "sum"
    tan = namespace + "tan"
    tanh = namespace + "tanh"
    times = namespace + "times"
    union = namespace + "union"
    uplimit = namespace + "uplimit"
