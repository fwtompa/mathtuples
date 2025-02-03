"""
    Tangent
    Copyright (c) 2013 David Stalnaker, Richard Zanibbi, Kenny Davila

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
    a Non-Commercial Creative Commons License (see the CCL-LICENSE file).  

    For Tangent, contact:
        - David Stalnaker: david.stalnaker@gmail.com
        - Richard Zanibbi: rlaz@cs.rit.edu

    Modified by Nidhin Pattaniyil, 2014
    Modified by Kenny Davila, 2014
    Modified by Frank Tompa, 2015, 2024-5
    Packaged with mathtuples. Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
from collections import deque
from _operator import or_
from sys import stderr
import string
import sys
import re
import symbol
import os

from .exceptions import UnknownTagException
from .mathml import MathML

REP_TAG = "!REP!"
MAX_HEIGHT = 100 # do not calculate tree heights larger than this value


__author__ = 'Nidhin, KDavila, FWTompa'

# many changes throughout to encode simplified and more consistent node and edge structure. FWT

'''
<math display="block" alttext="a+F(a,b)" class="ltx_Math" id="m1">
  <semantics id="m1a">
    <mrow xref="m1.7.cmml" id="m1.7">
      <mi xref="m1.4.cmml" id="m1.4">a</mi>
      <mo xref="m1.5.cmml" id="m1.5">+</mo>
      <mrow xref="m1.6.cmml" id="m1.6d">
        <mi xref="m1.1.cmml" id="m1.1">F</mi>
        <mo xref="m1.6.cmml" id="m1.6e">&ApplyFunction;</mo>    <!-- &#8289; -->
        <mrow xref="m1.6.cmml" id="m1.6c">
          <mo xref="m1.6.cmml" id="m1.6" stretchy="false">(</mo>
          <mi xref="m1.2.cmml" id="m1.2">a</mi>
          <mo xref="m1.6.cmml" id="m1.6a">,</mo>
          <mi xref="m1.3.cmml" id="m1.3">b</mi>
          <mo xref="m1.6.cmml" id="m1.6b" stretchy="false">)</mo>
        </mrow>
      </mrow>
    </mrow>
    <annotation-xml id="m1b" encoding="MathML-Content">
      <apply xref="m1.7" id="m1.7.cmml">
        <plus xref="m1.5" id="m1.5.cmml"/>
        <ci xref="m1.4" id="m1.4.cmml">a</ci>
        <apply xref="m1.6d" id="m1.6.cmml">
          <ci xref="m1.1" id="m1.1.cmml">F</ci>
          <ci xref="m1.2" id="m1.2.cmml">a</ci>
          <ci xref="m1.3" id="m1.3.cmml">b</ci>
        </apply>
      </apply>
    </annotation-xml>
    <annotation id="m1c" encoding="application/x-tex">a+F(a,b)</annotation>
  </semantics>
</math>

-> SLT: V!a(n(+n(V!F(n(M!()2x1(w(V!a(e(V!b)))))))))
   OPT: U!+(-(V!a),-(A!F(-(V!A),-(V!b))))
  
'''

class MathSymbol:
    """
    Node in a math tree, for both layout_symbol (SLT) and semantic_symbol (OpT)
    """

    def __init__(self, tag, children=None, in_label='-'): # FWT
        self.tag = tag
        if children:
            self.children = children
        else:
            self.children = []
        self.in_label = in_label
        
    def get_size(self):
        return 1 + sum(map(get_size,self.children))

    def get_height(self):
        return 1 + max(map(get_height,self.children))

    def is_leaf(self):
        return (len(self.children) == 0)

    def get_tree_leaves(self):
        if self.is_leaf():
            return [self]
        else:
            leaves = []
            for child in self.children:
                leaves.extend(get_tree_leaves(child))
        return leaves

    @staticmethod
    def Copy(other):
        local = MathSymbol(other.tag,in_label = other.in_label)
        if other.children is not None:
            local.children = []
            for original_child in other.children:
                local.children.append(MathSymbol.Copy(original_child))
        return local

  ###########################################################################################################
    # Run length encoding and decoding -- adapted from http://rosettacode.org/wiki/Run-length_encoding#Python #
    ###########################################################################################################
    @classmethod                                                                                              #
    def rlencode(cls,text):                                                                                   #
        '''
        Doctest:
            >>> encode('WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWBWWWWWWWWWWWWWW')
            '12W1B12W3B24W1B14W'    
        '''
        return re.sub(r'(.)\1*', lambda m: str(len(m.group(0))) + m.group(1), text)                           #
    
    @classmethod                                                                                              #
    def rldecode(cls,text):                                                                                   #
        '''
        Doctest:
            >>> decode('12W1B12W3B24W1B14W')
            'WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWWWWWWWWWWWWWWWWWWBWWWWWWWWWWWWWW'
        '''
        return re.sub(r'(\d+)(\D)', lambda m: m.group(2) * int(m.group(1)), text)                             #
    ###########################################################################################################

    @classmethod
    def encode_loc(cls,loc):
        if len(loc) == 0:
            return '-'
        elif len(loc) > 5:
            return cls.rlencode(loc)
        else:
            return loc

    @classmethod
    def decode_loc(cls,loc):
        if loc == '-':
            return ''
        else:
            return cls.rldecode(loc)

    def get_symbols(self, label, window, unbounded=False):
        return MathSymbolIterator(self, label, window, unbounded=unbounded)

    def toString(self):
        s = ""
        for c in self.children:
            if c:
                s = s + "," + c.toString()
        return(self.in_label + "(" + self.tag + ":" + s[1:] + ")")

    def get_features(self,
                  prefix,
                  window,
                  cmml=False,
                  symbol_pairs=True,
                  compound_symbols=False,
                  terminal_symbols=False,
                  edge_pairs=False,
                  eol=False,
                  unbounded=False,
                  repetitions="",
                  repDict = {},
                  # max_dup = 0,
                  shortened=False,
                  anchors=[]):
        """
        Return the features in the symbol tree, as indicated by arguments

        :param prefix: unencoded path from the root or nearest anchor to self (for location id)
        :type  prefix: string
        :param window: the max distance between symbol pairs to include
        :type  window: int
        :param symbol_pairs: If True will include symbol pairs (N, N, e)
        :type symbol_pairs: boolean
        :param compound_pairs: If True will include compound pairs (N, {e})
        :type compound_pairs: boolean
        :param terminal_symbols: If True will include terminal symbols (N)
        :type terminal_symbols: boolean
        :param edge_pairs: If True will include edge pairs (e, e, N)
        :type edge_pairs: boolean
        :param unbounded: If True will include all pairs of nodes (N, N)
        :type unbounded: boolean
        :param repetitions: string of node labels to include all n pairs of locations for each repeated node
        :type repetitions: string
        :param repDict: Dictionary mapping symbols to locations found so far
        :type repDict: dictionary mapping strings to strings
        # :param max_dup: maximum number of repetitions to consider for duplicated node labels
        # :type max_dup: int
        :param shortened: If True will shorten the path for various pairs
        :type shortened: boolean
        :param anchors: List of symbols that reset prefix to empty
        :type anchors: list of strings

        :return list of tuples
        :rtype list
        """
        def get_type(label):
            """
            given string "t!x", returns t
            """
            sep = label.find("!")
            if sep == -1: # no ! present
                if label[0] == "?":
                    return "W" #wildcard of unknown type
                else:
                    return "O" # must be an operator
            elif label[0] == "!":
                return "O" # the operator is "!"
            else:
                return label[0:sep]
       
        def mk_helper(location):
            def helper(tup):
                right, rel_path = tup
                rel_path = self.encode_loc(rel_path)
                if unbounded and len(rel_path) > window:
                    if shortened:
                        # super liberal for now
                        return (self.tag, right.tag, location)
                    else:
                        # little less liberal for now
                        path = rel_path[0] + rel_path[-1]
                        return (self.tag, right.tag, path, location)
                else:
                    return (self.tag, right.tag, rel_path, location)
            return helper

        if len(prefix) > MAX_HEIGHT: # abort: cannot handle very high trees (recursion exception)
             return [] 
        loc = self.encode_loc(prefix)
        ret = []

        if compound_symbols:
            # add the compound feature tuple - (N, {e1,e2, ...})
            available_edges = [child.in_label for child in self.children if child is not None]
            if len(available_edges) > 1:
                # if less than two then information captured
                # by symbol pairs
                ret.append((self.tag, str(available_edges), loc))

        for child in self.children:
            if child:
                label=child.in_label # if not cmml else self.in_label # for OPTs
                if symbol_pairs:
                    ret.extend(filter(lambda x: x is not None,
                                      map(mk_helper(loc),
                                          child.get_symbols(label,
                                                            window,
                                                            unbounded=unbounded
                                                            ))))
                # check for resetting the prefix to a new anchor
                if self.tag in anchors:
                    new_prefix = ""
                else:
                    new_prefix = prefix + label
                ret.extend(child.get_features(new_prefix,
                                           window,
                                           cmml=cmml,
                                           eol=eol,
                                           symbol_pairs=symbol_pairs,
                                           compound_symbols=compound_symbols,
                                           terminal_symbols=terminal_symbols,
                                           edge_pairs=edge_pairs,
                                           unbounded=unbounded,
                                           repetitions=repetitions,
                                           repDict=repDict,
                                           # max_dup=max_dup,
                                           shortened=shortened,
                                           anchors=anchors))
        if terminal_symbols and len(ret) == 0:
            # add the terminal symbols
            ret.append((self.tag, "!0", loc))
        if eol and len(ret) == 0:
            # then we have a small expression and adding eol
            ret.append((self.tag, "!0", "n", loc))
        if edge_pairs and len(prefix) > 0:
            # add the pairs of edges on this node
            ret.extend([(prefix[-1], child.in_label, self.tag, loc)
                        for child in children
                        if child and child.in_label != "w"])

        if get_type(self.tag) in repetitions:
            # insert symbol into dictionary and check for repetitions
            locations = repDict.setdefault(self.tag,[]) # retrieve previous positions
            """
            # no longer use all pairs up to max_dup instances
            if len(locations) < max_dup: # only generate tuples for small number of reps
                # loc is the location of the current symbol and prefix is the same but unencoded
                for pos in locations:
                    common = os.path.commonprefix([prefix,pos])
                    if common == prefix: # both symbols on same path
                        ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(prefix):]),loc))
                    else:
                        ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(common):]),self.encode_loc(prefix[len(common):]),self.encode_loc(common)))
            """
            # use closest pairs in spanning tree only -- is this a good idea? quite different answers possible if one is missing.
            # instead use closest pair in depth first traversal
            # loc is the location of the current symbol and prefix is the same but unencoded
            if len(locations) > 0:
                pos = locations[-1]
                common = os.path.commonprefix([prefix,pos])
                if common == prefix: # both symbols on same path
                    ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(prefix):]),loc))
                else:
                    ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(common):]),self.encode_loc(prefix[len(common):]),self.encode_loc(common)))
            repDict[self.tag].append(prefix)
        return ret

    """
    Symbol in a symbol tree
    """


    def field(self,f):
        for (pos,child) in enumerate(self.children):
           if not child:
              del self.children[pos]
              continue
           if child.in_label==f:
               return child
        return None

    def next(self):
        return self.field('n')

    def above(self):
        return self.field('a')

    def below(self):
        return self.field('b')

    def over(self):
        return self.field('o')

    def under(self):
        return self.field('u')

    def pre_above(self):
        return self.field('c')

    def pre_below(self):
        return self.field('d')

    def within(self):
        return self.field('w')

    def element(self):
        return self.field('e')

    def set_field(self,newchild,f):
        if (newchild == None):
           self.del_field(f)
           return
        newchild.in_label = f
        for (pos,child) in enumerate(self.children):
           if not child:
              del self.children[pos]
              continue
           if child.in_label == f:
              self.children[pos] = newchild	# replace by new value
              return
        self.children.append(newchild)

    def set_next(self,newchild):
        self.set_field(newchild,'n')

    def set_above(self,newchild):
        self.set_field(newchild,'a')

    def set_below(self,newchild):
        self.set_field(newchild,'b')

    def set_over(self,newchild):
        self.set_field(newchild,'o')

    def set_under(self,newchild):
        self.set_field(newchild,'u')

    def set_pre_above(self,newchild):
        self.set_field(newchild,'c')

    def set_pre_below(self,newchild):
        self.set_field(newchild,'d')

    def set_within(self,newchild):
        self.set_field(newchild,'w')

    def set_element(self,newchild):
        self.set_field(newchild,'e')

    def set_label(self,f):
        #if (self.in_label == '-'):
           self.in_label = f
           #return True
        #return False

    def del_field(self,f):
        for (pos,child) in enumerate(self.children):
           if not child:
              del self.children[pos]
              continue
           if child.in_label == f:
              del self.children[pos]
              return

    def del_next(self):
        self.del_field('n')

    def del_above(self):
        self.del_field('a')

    def del_below(self):
        self.del_field('b')

    def del_over(self):
        self.del_field('o')

    def del_under(self):
        self.del_field('u')

    def del_pre_above(self):
        self.del_field('c')

    def del_pre_below(self):
        self.del_field('d')

    def del_within(self):
        self.del_field('w')

    def del_element(self):
        self.del_field('e')

    """
    ----------------------------------------------------------------
    helper functions to deal with implied matrices
    ----------------------------------------------------------------
    """

    @classmethod
    def list2matrix(cls, children, separators):
        """
        Treat a list of trees as if it were a matrix
         -- assumes children starts and ends with fence characters
        :param children: list of trees within mrow, mfenced, or mpadded
        :type  children: list of SymbolTrees
        :param separators: potential punctuation placed between the children
        :type  separators: string
        :return: SymbolTree for a 1xn matrix (where n is number of separated elements)
        :rtype:  root node in a SymbolTree
        """
        def separates(tag):
            return ((tag in separators) or ((tag == '&comma;') and (',' in separators)))
        def invisible_matrix(node):
            if node.tag.startswith('M!'):
                if node.tag[2] in '({|&∥': # inner matrix has fence characters already
                    return False
                return (len(node.children) == 0) # inner matrix has attachment
            else:
                return False
            
        if len(children) < 4 and invisible_matrix(children[1]): # fenced matrix (but omit closing tag, as below)
            fence = children[0].tag
            if len(children) == 3:
                fence = fence + children[2].tag
            children[1].tag = 'M!'+fence+children[1].tag[2:]  # insert fence chararacters into label
            return children[1]
        else:
            mnode = cls('M!')    # mark as if empty matrix
            num_args = 1
            if (len(children) > 2):
                if not separates(children[1].tag): # second child is not a separator
                    mnode.set_within(children[1])
                else:
                    mnode.set_within(cls('W!')) # does this need the mathml attribute set?
                    if len(children) == 3:
                        mnode.within().set_next(children[1]) # set the next field to be the separator
                    else:
                        children.insert(1,None) # insert a dummy element as first child so that separator is next
                elem = mnode.within() # mark the start of the matrix element
                expr = elem # mark the start of the expression (content of matrix element)
                # invariants:
                #     mnode references the matrix node
                #     elem references the start of the matrix element being processed
                #     expr references a symbol in the expression being processed
                if len(children) == 3:  # (fence,expr-list,fence) => look for separators
                    while expr and expr.next():
                        if separates(expr.next().tag):  # nested mrow already processed to link parts
                            num_args += 1

                            # Original: All connected as "element"
                            #elem.element = expr.next   # break on separator
                            #expr.next = None
                            #elem.element.element = elem.element.next # re-link the separator
                            #elem.element.next = None
                            #elem = elem.element.element # move on to the next matrix element

                            # Modified: remove separators, but nodes after separators are element
                            elem.set_element(expr.next().next())
                            expr.del_next()
                            elem = elem.element()

                            expr = elem
                        else:      
                            expr = expr.next()
                else: # (fence, expr, expr, ... expr, fence)
                    for atom_num in range(2,len(children)-1):         # no nested mrow: break when argument is a separator
                        if separates(children[atom_num].tag):
                            num_args += 1
                            # Original: separator connected as "element"
                            #elem.element = children[atom_num]
                            #elem = elem.element

                            # Modified: do not link in the separator, just skip it
                            while expr.next():
                                expr = expr.next()
                            # expr.next = children[atom_num]
                            # expr = expr.next
                        else:
                            if separates(children[atom_num-1].tag): # previous element was a separator
                                elem.set_element(children[atom_num])
                                elem = elem.element()
                                expr = elem
                            else: # no separator: link to the previous expression
                                while expr.next():
                                    expr = expr.next()
                                expr.set_next(children[atom_num])
                mnode.tag = 'M!' + children[0].tag + children[-1].tag + '1x' + str(num_args) # as if fenced 1xn matrix
            else:
                mnode.tag = 'M!' + children[0].tag + (children[-1].tag if len(children)>1 else '')
            return mnode
       
    @classmethod
    def matrixMerge(cls, elem, elem2):
        """
        Two abutting matrices with the same number of rows should be merged into one
        :param elem: first matrix
        :type  elem: mathsymbol (tag starts with 'M!')
        :param elem2: second matrix
        :type  elem2: mathsymbol (tag starts with 'M!')
        """
        (rows1,x1,cols1) = elem.tag[2:].partition('x') # split the tag at the x character
        (rows2,x2,cols2) = elem2.tag[2:].partition('x')
        if str.isdecimal(rows1) and rows1 == rows2:   # both matrices have the same number of rows and no brackets
            # merge them
            content1 = elem.within()
            content2 = elem2.within()
            rows1 = int(rows1) # convert to numeric
            cols1 = int(cols1)
            cols2 = int(cols2)
            for i in range(0,rows1):
                for j in range(1,cols1):
                    content1 = content1.element()
                content11 = content1.element() # hold onto the first element of the next row
                content1.set_element(content2)  # insert elements from second matrix
                for j in range(1,cols2):
                    content2=content2.element()
                content22 = content2.element() # hold onto the first element of the next row
                content2.set_element(content11) # finish linking in the row from second matrix
                content2 = content22  # move to next element
                content1 = content11
            elem.tag = 'M!' + rows2 + 'x' + str(cols1+cols2)
            return elem
        else:
            # concatenate them
            while elem.next():
                elem = elem.next()
            elem.set_next(elem2)
            return elem2


    @classmethod
    def make_matrix(cls, children, original_element):
        """
        Create a matrix structure
        :param children: list of matrix rows
        :type  children: [MathSymbol]
        :param original_element: start of matrix (for MathML)
        :type  original: MathSymbol or None
        """
        num_rows = len(children)
        if num_rows > 0:
            elem = children[0]
            if elem:
                num_cols = 1  # count the number of columns in the first row
                while elem.element():
                    num_cols += 1
                    elem = elem.element()
            else:
                num_cols = 0 # row has no columns
        else:
            num_cols = 0 # no rows => no columns
        root = cls('M!' + str(num_rows) + "x" + str(num_cols))
        if num_rows > 0: # elem points to last entry in first row (row 0)
            root.set_within(children[0] if children[0] or len(children) == 1 else cls('W!'))
            # make all rows have the same number of elements:
            for i in range(1,len(children)):
                 elem.set_element(children[i])  # link last element from row i-1 to first in row i
                 for j in range(0,num_cols):
                     if not elem.element():
                         elem.set_element(cls("W!"))
                     elem = elem.element()
            elem.del_element()
        return root
    
    """
    ----------------------------------------------------------------
    Converter from MathML to simplified tree
    ----------------------------------------------------------------
    """

    @classmethod
    def tree_from_mathml(cls, elem):
        """
        Convert symbol tree from mathml using recursive descent
        :param elem: a node in MathML structure on which an iterator is defined to select children
        :type  elem: a MathML node
        :return: the root of the corresponding SLT or OpT (or a list of roots)
        :rtype:  MathSymbol
        """

        def ignore_tag(elem):  #FWT
            """
            invisible operators and whitespace to be omitted from SymbolTree
            :return: True if node to be ignored
            :rtype:  boolean
            """
            if elem is None:
                return True
            elif elem.tag in ['W!', '']: # simple types with no values and no links
                return (len(elem.children) == 0)
            else:
                return False

        def ensure(children,count):
            """
            check whether the number of children == count 
            """
            if not children or len(children) != count:
                return False
            else:
                for i in range(count):
                    if ignore_tag(children[i]):
                        children[i] = cls("W!")
                return True

        def get_value(elem):
            """
            get contents inside element or "" if no content
            """
            if not elem: # => there are no children (since elem cannot be None)
                return clean(elem.text)
            else: # use the src attribute of the mglyph child
                child = list(elem)[0] # first/only child
                if not child.tag.startswith('{'): # handle missing namespace declaration
                    child.tag = MathML.namespace+child.tag
                if child.tag != MathML.mglyph or 'src' not in child.attrib:
                    return ""
                else:
                     return child.attrib['src']

        def clean(tag):
            """
            :param tag: symbol to store in trees
            :type  tag: string
            :return: stripped symbol with tabs, newlines, returns, spaces,
                     queries, commas, left and right brackets escaped
                     (using std entity names http://www.w3.org/TR/xml-entity-names/bycodes.html)
            :rtype: string
            """
            if not tag:
                return ""
            tag = tag.strip().translate({9:r"\t", 10:r"\n", 13:r"\r", 32:r"␣", 34:"&quot;",
                              39:"&apos;",63:"&quest;", 44:"&comma;", 91:"&lsqb;", 93:"&rsqb;"})
            if tag in ['\u2061', '\u2062', '\u2063', '\u2064']: # invisible operators
                return ""
            return tag

        def infer_mrow(elem,children):
            """
            treat list of children like non-parenthesized mrow
            """
            if "PreScript" in children: # do not alter a list that is inside <mmultiscript>
                return(children)
            children_map = filter(lambda x: not ignore_tag(x), children)
            children = list(children_map)
            if len(children) > 0:
                # handle parenthesized sub-expressions (FWT)
                if (len(children) > 1 and (children[0].tag in '({|∥' or children[0].tag == "&lsqb;")):
                #    and (children[-1].tag in ')}|∥' or children[-1].tag == "&rsqb;")):  # bracketed expression: treat as matrix
                    return cls.list2matrix(children, ',')
                else: # just eliminate mrow and connect its children
                    elem = children[0]
                    for i in range(1,len(children)):
                        if elem.tag.startswith('M!') and children[i].tag.startswith('M!'):
                            elem = cls.matrixMerge(elem,children[i])
                        elif i == 1 and elem.tag == '-' and children[1].tag.startswith('N!'):
                            # should be a negative number: combine nodes
                            children[0].tag = 'N!-' + children[1].tag[2:]
                        else:
                            while elem.next():
                                elem = elem.next()
                            elem.set_next(children[i])
                            elem = elem.next()
                    return children[0]
            else:
                return cls("W!")	# nothing in the row

        """
        ---------------------------------------------------
        Executable code for parsing MathML starts here:
        ---------------------------------------------------
        """
        # print("text tag: " + elem.tag,flush=True)
        if not elem.tag.startswith('{'): # handle missing namespace declaration (FWT) -- should be reported as warning!
            elem.tag = MathML.namespace+elem.tag
        children = list(map(cls.tree_from_mathml, elem))  # before continuing, perform the recursive descent to convert the children
        # print("Children completed")
        # for c in children:
        #     print(c.toString())

        short_tag = elem.tag[elem.tag.index("}")+1:]

        """
        ---------------------------------------------------
            Presentation MathML tags
        ---------------------------------------------------

        N! - Number
        V! - Variable
        F! - Fraction
        T! - Text
        M! - Group, with delimeters and shape (e.g., "M!()3x2")
        R! - Root
        W! - White space
        ?  - Wildcard
        E! - Error
        else - Operator

        edges: a, b, c, d, w, e, n
        """

        """
        ---------------------------------------------------
            Content MathML tags
        ---------------------------------------------------

        N! - Number
        C! - Constant
        V! - Variable
        A! - Apply function (so as not to be confused with F! for fractions)
        T! - Text
        M! - Group Element (M!V-)/Matrix(M!M-)/Set(M!S-)/List(M!L-)/Delimited(M!D-)/MatrixRow(M!R!)/ Case (M!C!)
        O! - Ordered operator (not commutative)
        U! - Unordered operator (commutative)
        E! - Error!
        -! - Unknown type

        edges: f, e, l, a, b, w, v
        """
        if elem.tag ==MathML.mqvar or elem.tag == MathML.mqvar2:
            # added the case where name is given as text within tag instead of attribute (KMD)
            if 'name' in elem.attrib:
                var_name = elem.attrib['name']
            else:
                var_name = clean(elem.text)
            return cls('?'+var_name)
        elif short_tag[0] == 'm':  # peel off most of the presentation tags and a few content tags
 

            if elem.tag == MathML.mn:
                content = get_value(elem)
                return cls('N!' + content if content != '' else 'W!')
            elif elem.tag == MathML.mo:  # future: improve representation (and equivalences) by recognizing and preserving fence="true" and separator="true"
                return cls(get_value(elem))
            elif elem.tag == MathML.mi:
                content = get_value(elem)
                return cls('V!' + content if content != '' else 'W!')
            elif (elem.tag == MathML.mtext) or (elem.tag == MathML.ms):
                content = clean(elem.text)
                return cls('T!' + content if content != '' else 'W!')  # to prevent accidental mis-typing
            elif elem.tag == MathML.mspace:
                return cls('W!')

            elif elem.tag in [MathML.math, MathML.mrow, MathML.mstyle, MathML.mpadded, MathML.msrow, MathML.mscarries, MathML.maction]:
                return infer_mrow(elem,children)    # N.B. Could be W!
            elif elem.tag == MathML.mfrac:
                if not ensure(children,2): # should never happen
                    return cls('E!'+short_tag,children=children)
                else:
                    children[0].set_label("o")
                    children[1].set_label("u")
                    return cls('F!',children=children)
            elif elem.tag == MathML.msqrt:
                root = cls('R!')
                root.set_within(infer_mrow(elem,children))
                return root
            elif elem.tag == MathML.mroot:   
                if not ensure(children,2): # should never happen
                    return cls('E!'+short_tag,children=children)
                else:
                    children[0].set_label("w")
                    children[1].set_label("c")
                    return cls('R!',children=children)
            elif elem.tag == MathML.merror:
                root = cls('E!')
                root.set_within(infer_mrow(elem,children))
                return root
            elif elem.tag == MathML.mphantom:
                return cls("W!")
            elif elem.tag == MathML.mfenced:  # treat like mrow (FWT)
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                separators = elem.attrib.get('separators', ',').split()
                opening = elem.attrib.get('open', '(').replace("[","&lsqb;")
                row = [cls(opening)]
                if children:
                    row.append(children[0])
                for i, child in enumerate(children[1:]):
                    row.append(cls(separators[min(i, len(separators) - 1)]))
                    row.append(child)
                closing = elem.attrib.get('close', ')').replace("]","&rsqb;")
                row.append(cls(closing))
                return cls.list2matrix(row, separators)
            elif elem.tag == MathML.menclose:
                root = cls(elem.attrib.get('notation', 'longdiv'))
                root.set_within(infer_mrow(elem,children))
                return root

            elif elem.tag == MathML.msub:
                if not ensure(children,2): # should never happen!
                    return cls('E!'+short_tag,children=children)
                # FWT handle operators such as \sum_{i+1}^n so that they are treated as "under" and "over"
                if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                    if children[0].next() or children[0].below():  # might have a sub on a sub: {x_y}_z, but not necessarily associative
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_below(children[1])
                else: # FWT future: \delta is an operator, perhaps restrict to "largeop=true" only? but not consistently present
                    if children[0].next() or children[0].under():  # might have an underbar on the operator
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_under( children[1])
                return root
            elif elem.tag == MathML.munder: # FWT - split sub from under
                if not ensure(children,2):
                    return cls('E!'+short_tag,children=children)
                if children[0].next() or children[0].under():  # munder and mover can apply to a whole row rather than a simple symbol
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.set_under(children[1])
                return root
            elif elem.tag == MathML.msup:
                if not ensure(children,2):
                    return cls('E!'+short_tag,children=children)
                # FWT handle operators such as \sum_{i+1}^n so that they are treated as "under" and "over"
                if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                    if children[0].next() or children[0].above():  # might have a sup on a sup: {x^y}^z, but not necessarily associative
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_above(children[1])
                else:
                    if children[0].next() or children[0].over():  # might have an accent on the operator
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_over(children[1])
                return root
            elif elem.tag == MathML.mover: # FWT - split sup from over
                if not ensure(children,2):
                    return cls('E!'+short_tag,children=children)
                if children[0].next() or children[0].over():  # munder and mover can apply to a whole row rather than a simple symbol
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.set_over(children[1])
                return root
            elif elem.tag == MathML.msubsup:
                if not ensure(children,3):
                    return cls('E!'+short_tag,children=children)
                # FWT handle operators such as \sum_{i+1}^n so that they are treated as "under" and "over"
                if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                    if children[0].next() or children[0].below() or children[0].above():  # cascaded use can happen
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_below(children[1])
                    root.set_above(children[2])
                else:
                    if children[0].next() or children[0].under() or children[0].over():  # cascaded use can happen
                        root = cls.make_matrix([children[0]],elem)
                    else:
                        root = children[0]                
                    root.set_under(children[1])
                    root.set_over(children[2])
                return root
            elif elem.tag == MathML.munderover: # split from subsup
                if not ensure(children,3):
                    return cls('E!'+short_tag,children=children)
                if children[0].next() or children[0].under() or children[0].over():  # munder and mover can apply to a whole row rather than a simple symbol
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.set_under(children[1])
                root.set_over(children[2])
                return root
            elif elem.tag == MathML.mprescripts:
                return "PreScript"
            elif elem.tag == MathML.mmultiscripts: #FWT: Future: handle cascading presecripts (like sub and sup above)
                # base {sub sup}* [prescript {pre-sub pre-sup}*]
                if len(children) == 0:
                    return cls('E!'+short_tag)
                if len(children) == 1 and type(children[0]) is list: # mrow or mpadded within mmultiscripts
                    children = children[0]
                if ignore_tag(children[0]):
                    children[0] = cls('W!') # base must be represented
                try:
                    prescript = children.index("PreScript")
                except ValueError: # no PreScript included
                    prescript = len(children)
                if (prescript % 2 == 0) or (prescript < len(children) and len(children) % 2 == 1): # should never happen!
                    return cls('E!'+short_tag,children=children)
                if prescript > 1: # sub sup pairs are present
                    sub = children[1] if prescript > 3 or (children[1] and children[1].tag != "W!") else None
                    children[0].set_below(sub)
                    sup = children[2] if prescript > 3 or (children[2] and children[2].tag != "W!") else None
                    children[0].set_above(sup)
                    for i in range(3,prescript,2):
                        sub.set_next(children[i])
                        sub = sub.next()
                        sup.set_next(children[i+1]) 
                        sup = sup.next()
                if prescript < len(children)-2:
                    sub = children[prescript+1] if prescript < len(children)-4 or (children[prescript+1] and children[prescript+1].tag != "W!") else None
                    children[0].set_pre_below(sub)
                    sup = children[prescript+2] if prescript < len(children)-4 or (children[prescript+2] and children[prescript+2].tag != "W!") else None
                    children[0].set_pre_above(sup)
                    for i in range(prescript+3,len(children),2):
                        sub.set_next(children[i])
                        sub = sub.next()
                        sup.set_next(children[i+1])
                        sup = sup.next()
                return children[0]

            elif (elem.tag == MathML.mtable)\
              or (elem.tag == MathML.mstack) or (elem.tag == MathML.mlongdiv): # mlongdiv: separate divisor and result?
                return cls.make_matrix(children,elem)
            elif (elem.tag == MathML.mtr) or (elem.tag == MathML.mlabeledtr):
                if len(children) > 0:
                    root = children[0] if children[0] else cls('W!')
                    for i in range(1,len(children)):
                        children[i-1].set_element(children[i])  # link by e edges
                    return root
                else:
                    return cls('W!')
            elif (elem.tag == MathML.mtd) or (elem.tag == MathML.mscarry):
                if len(children) > 0 and children[-1] is not None and children[-1].tag == "&comma;":
                    children.pop()   # remove commas between matrix elements (no mrow)
                root = children[0] if len(children) > 0 and children[0] is not None else cls('W!')
                elem = root
                for i in range(1,len(children)):
                    while elem.next():
                        elem = elem.next()
                    elem.set_next(children[i])
                while elem.next():
                    if elem.next().tag == "&comma;" and not elem.next().next():
                        elem.del_next()   # remove commas between matrix elements (mrow)
                    else:
                        elem = elem.next()
                return root
            elif elem.tag == MathML.malignmark or elem.tag == MathML.maligngroup:
                return cls('E!'+short_tag,children=children)
            elif elem.tag == MathML.msline:
                return cls('=') # summation line in an mstack

            # Content MML tags that start with 'm'

            # ... matrices ...
            elif elem.tag == MathML.matrix:
                # a matrix, but this code does not handle constructors
            # check the number of rows ...
                n_cols = 0
                for row in children:
                    n_cols = max(n_cols, len(row.children))
                mat_root = cls("M!M-" + str(len(children)) + "x" + str(n_cols),children=[])

                # check for missing values to make matrix square and keep all cells in row-major order as children
                for row in children:
                    while len(row.children) < n_cols:
                        row.children.append(cls("W!"))
                    mat_root.children.extend(row.children)	# no need to keep the matrix structure
                for child in mat_root.children:
                    child.set_label('w')	# mark all children as within the matrix
                return mat_root

            # ... matrix rows ...
            elif elem.tag == MathML.matrixrow:
                # a matrix row,
                for child in children:
                    child.set_label("w")
                return cls("M!R!", children=children)

            elif elem.tag in [MathML.min, MathML.max]:
                # print("op " + elem.tag,flush=True)
                return cls("U!" + short_tag, in_label="f")
            elif elem.tag in [MathML.minus, MathML.moment]:
                return cls("O!" + short_tag, in_label="f")
            elif elem.tag == MathML.momentabout:
                if not ensure(children,1): # should never happen
                    # print("invalid momentabout")
                    return cls('E!'+short_tag,children=children)
                else:
                    children[0].set_label('b')
                    return children[0]

            else:
                # print("unknown "+short_tag)
                return cls('E!'+short_tag,children=children)

        ##############
        # Content MML:
        ##############
        else:  # tags that do not start with 'm'


            if elem.tag == MathML.none:
                return cls("W!")
            elif elem.tag == MathML.semantics:
                return infer_mrow(elem,children)    # N.B. Could be W!

            # operator tree leaves ...
            elif elem.tag == MathML.ci:
                content = get_value(elem)
                # print("ci: "+content,flush=True)
                return(cls(('V!' + content) if content != '' else 'W!'))

            elif elem.tag == MathML.cn:
                content = get_value(elem)
                return(cls(('N!' + content) if content != '' else 'W!'))

            elif elem.tag == MathML.cerror:
                # print("CERROR tag")
                retval = cls('E!'+short_tag, children=children)

                # check for common error patterns to simplify tree...

                # contiguous "unknown" csymbol....
                pos = 0
                while pos + 1 < len(retval.children):
                    if retval.children[pos].tag[0:2] in ["-!", "T!"] and retval.children[pos + 1].tag[0:2] == "-!":
                        # combine ... change to text ...
                        retval.children[pos].tag = "T!" + retval.children[pos].tag[2:] + retval.children[pos + 1].tag[2:]
                        # remove next ...
                        del retval.children[pos + 1]
                    else:
                        pos += 1
                return retval

            # special mathml operations
            elif elem.tag == MathML.apply:
                # operator ...there should be at least one operand?
                # root (operator)
                op_root = children[0]
                # print("apply to "+op_root.tag, flush=True)
                if op_root.tag[0:2] == "V!":
                    # identifier used as an operator, assume a function!
                    op_root.tag = "A!" + op_root.tag[2:]
                    op_root.set_label("?")
                    # print("it's a function: " + op_root.tag,flush=True)
                elif op_root.tag == "O!SUB":
                    if not ensure(children,3): # should never happen
                        # print("invalid O!SUB")
                        return cls('E!'+short_tag,children=children)
                    else:
                        op_root = children[1]
                        op_root.set_below(children[2])
                    return op_root
                elif op_root.tag == "O!SUP":
                    if not ensure(children,3): # should never happen
                        # print("invalid O!SUP")
                        return cls('E!'+short_tag,children=children)
                    else:
                        op_root = children[1]
                        op_root.set_above(children[2])
                    return op_root
                
                # check for special operators with special name operands
                if (op_root.tag == "A!int" or op_root.tag.endswith("integral")) and len(children) > 1:
                    main_operand = children[-1]
                    lowlimit = op_root.below()	# ARQMath data uses subscript and superscript for limits, else None
                    uplimit = op_root.above()
                    int_var = None 
         
                    for child in children[2:-2]:	# check for other encodings of integral limits and variable
                        if child.tag.startswith("O!interval"):
                            lowlimit = child.children[0]
                            _ = child.children[1]
                        elif child.tag == "A!bvar":
                            int_var = child
                        elif child.tag == "A!lowlimit":
                            lowlimit = child.children[0]
                        elif child.tag == "A!uplimit":
                            uplimit = child.children[0]
                        else:
                            # print("unknown A!INT")
                            return cls("E!",children=children) 

                    main_operand.set_label("w")
                    if main_operand.tag == "U!times":
                        for child in main_operand.children[:]:		# slice makes a copy so that child can be removed
                            if child.tag == "A!differential-d":
                                child.children[0].set_label("v")
                                if int_var:					# for double and triple integrals
                                    if int_var.tag == "O!bvar":
                                        int_var.children.append(child.children[0])
                                    else:
                                        int_var = cls("O!bvar",children=[int_var,child.children[0]],in_label="v")
                                else:
                                   int_var = child.children[0]
                            main_operand.children.remove(child)
                            # else: look for times(d,var) elsewhere in integrand expression
                    if lowlimit:
                        lowlimit.set_label("b")					# can double-integrals have multiple subscripts and superscripts?
                    if uplimit:
                        uplimit.set_label("a")
                    op_root.children = [main_operand, int_var, lowlimit, uplimit]
                    return op_root

                elif op_root.tag == "A!sum" and len(children) > 1:
                    main_operand = children[-1]
                    if op_root.below() == "O!eq":	# e.g. $sum_{k=1}^N ...$
                        sum_var = op_root.below().child[0]
                        sum_var.set_label("v")
                        lowlimit = op_root.below().child[1]
                    else:
                        sum_var = None
                        lowlimit = op_root.below()	
                    uplimit = op_root.above()
         
                    main_operand.set_label("w")
                    if lowlimit:
                        lowlimit.set_label("b")
                    if uplimit:
                        uplimit.set_label("a")
                    op_root.children = [main_operand, sum_var, lowlimit, uplimit]
                    return op_root

                elif (op_root.tag.startswith("A!limit") or op_root.tag.endswith("limit")) and len(children) > 1:
                    main_operand = children[-1]
                    if op_root.below() == "V!":	# e.g. $lim_{k->1} ...$
                        lim_var = op_root.below().child[0]
                        limit = op_root.below().child[1]
                    else:
                        lim_var = None
                    limit = op_root.below()	
         
                    main_operand.set_label("w")
                    if lim_var:
                        lim_var.set_label("v")
                    if limit:
                        limit.set_label("b")
                    op_root.children = [main_operand, lim_var, limit]
                    return op_root

                elif op_root.tag == "A!root":
                    if op_root.children:  # this has already been applied: <apply><apply><root/><...></apply</apply>
                        return op_root
                    main_operand = children[-1]
                    if children[1].tag == 'A!degree':
                        degree = children[1].children[0]
                    else:
                        degree = cls("N!2")	# default to square root
                    main_operand.set_label("w")
                    degree.set_label("c")
                    op_root.children = [main_operand, degree]
                    return op_root

                elif op_root.tag == "O!cases":
                    if len(children) == 2 and children[1].tag[0:2] == "M!": # matrix erroneously marked as cases
                        return children[1]
                    # all the remaining operands (at least one?) are cases
                    op_root.children = children[1:]
                    if len(children) % 2 != 1:	# op_root is children[0], so total number should be odd
                        # print("missing case in O!cases " + str(len(children)) + " children")
                        op_root.children.append(cls("E!missing-case",in_label="w"))
                    for child in op_root.children:
                        child.set_label("w")		# mark all children as within the function
                    return op_root

                elif op_root.tag == "A!matrix":
                    if not ensure(children,2): # should never happen
                        # print("invalid A!matrix")
                        return cls('E!'+short_tag,children=children)
                    if children[1].tag[0:2] == "W!":
                        return cls("M!",children=children[1:],in_label = 'w')
                    return children[1]

                elif op_root.tag[0:9] == "E!csymbol" and len(children) == 2 and children[1].tag[0:2] == "M!": # matrix erroneously marked
                    children[1].in_label = op_root.in_label # preserve the label
                    return children[1]

                else:  # just a normal function or operator
                    op_root.children = children[1:]
                    # print("function completed",flush=True)
                    for c in op_root.children:
                        if c:
                            c.in_label = op_root.in_label       # the operator has the label to use for its children
                    return op_root


#       elif elem.tag == MathML.share:
#            # copy a portion of the tree used before ...
#            if elem.attrib["href"] == ,f(O!minus:f(N!1:))"#.cmml": 	# instead should use ids in identified
#                # special case common in equations, repeat right operand of last operation ...
#                if parent.parent.tag == "U!and":
#                    # identify root of subtree to copy ...
#                    last_operand = parent.parent.children[-1].children[-1]
#                    # copy ...
#                    retval = Copy(last_operand)
#                    retval.parent = parent

            # tags with special handling ...
            # ... groups of elements ...
            elif elem.tag == MathML.vector or elem.tag == MathML.list or elem.tag == MathML.set:
                subtype = "--"
                if elem.tag == MathML.vector:
                    subtype = "V-"
                elif elem.tag == MathML.list:
                    subtype = "L-"
                elif elem.tag == MathML.set:
                    # a vector (or list) ...
                    subtype = "S-"
                for child in children:
                    child.set_label("w")
                return cls("M!" + subtype + str(len(list(elem))), children=children)

            # ... intervals ...
            elif elem.tag == MathML.interval:        
                if not ensure(children,2): # should never happen
                    # print("invalid interval")
                    return cls('E!'+short_tag,children=children)
                inttype = "C-C"	# default, closed
                if "closure" in elem.attrib:
                    closure = elem.attrib["closure"].strip().lower()
                    if closure == "open":
                        inttype = "O-O"
                    elif closure == "closed":
                        inttype = "C-C"
                    elif closure == "open-closed":
                        inttype = "O-C"
                    elif closure == "closed-open":
                        inttype = "C-O"
                    else:
                        # print("invalid closure for interval")
                        return cls('E!'+short_tag+closure,children=children)
                children[0].set_label("b")
                children[1].set_label("a")
                return cls("O!interval(" + inttype + ")", children=children)

            # functions with special tags (but all used with <apply>) ...
            elif elem.tag in [MathML.sin, MathML.cos, MathML.tan, MathML.cot, MathML.sec, MathML.csc,
                              MathML.sinh, MathML.cosh, MathML.tanh, MathML.coth, MathML.sech, MathML.csch,
                              MathML.arccos, MathML.arccot, MathML.arccsc, MathML.arcsec, MathML.arcsin, MathML.arctan,
                              MathML.arccosh, MathML.arccoth, MathML.arccsch, MathML.arcsech, MathML.arcsinh, MathML.arctanh]:
                return cls("A!" + short_tag, in_label='t')
            elif elem.tag in [MathML._abs, MathML.exp, MathML.log, MathML.ln, 
                              MathML.ceiling, MathML.floor, MathML.arg, MathML.determinant,
                              MathML.real, MathML.imaginary, MathML.factorial, MathML.root,
                              MathML.int, MathML.sum, MathML.limit, MathML.partialdiff, MathML.compose]:
                if short_tag == "determinant":
                    short_tag = "det"
                return cls("A!" + short_tag, in_label='f')
            elif elem.tag in [MathML.forall, MathML.exists, MathML._not]:
                return cls("A!" + short_tag, in_label='l')
            elif elem.tag in [MathML.bvar, MathML.lowlimit, MathML.uplimit, MathML.degree]:
                if not ensure(children,1): # should never happen
                    # print("invalid " + short_tag)
                    return cls('E!'+short_tag,children=children)
                children[0].set_label("w")
                return cls("A!" + short_tag,children=children)

            # unordered operators ...
            elif elem.tag in [MathML.approx, MathML.eq, MathML.neq, MathML.equivalent]:
                return cls("U!" + short_tag, in_label="e")
            elif elem.tag in [MathML.union, MathML.intersect]:
                return cls("U!" + short_tag, in_label="s")
            elif elem.tag in [MathML.plus, MathML.times, MathML.gcd]:
                # print("op " + elem.tag,flush=True)
                return cls("U!" + short_tag, in_label="f")
            elif elem.tag in [MathML._and, MathML._or]:
                return cls("U!" + short_tag, in_label="l")

            # ordered operators ...
            elif elem.tag in [MathML.lt, MathML.gt, MathML.leq, MathML.geq]:
                return cls("O!" + short_tag,  in_label="e")
            elif elem.tag == MathML.divide:
                return cls("O!" + short_tag, in_label="f")
            elif elem.tag in [MathML.setdiff]:
                return cls("O!" + short_tag, in_label="s")
            elif elem.tag in [MathML.subset, MathML.prsubset, MathML.notsubset, MathML.notprsubset,
                              MathML._in, MathML.notin, MathML.implies]:
                return cls("O!" + short_tag, in_label='l')

            # special constants
            elif elem.tag in [MathML.infinity, MathML.emptyset, MathML.imaginaryi]:
                if short_tag == "empty_set":
                    label = 's'
                else:
                    label = 'f'
                return cls("C!" + short_tag, in_label = label)	# no children

            # generic tag operators
            elif elem.tag == MathML.csymbol:
                # Operators in general
                # -- for now, the following all set retval and returns from bottom of function
                retval = None
                content = get_value(elem).lower()

                cd = elem.attrib["cd"] if "cd" in elem.attrib else ""

                if cd == "latexml":

                    if content in ["approximately-equals-or-equals", "approximately-equals-or-image-of",
                                   "asymptotically-equals", "equals-or-preceeds", "equals-or-succeeds", "geometrically-equals",
                                   "greater-than-and-not-approximately-equals", "greater-than-and-not-equals",
                                   "greater-than-and-not-equivalent-to",
                                   "greater-than-or-approximately-equals", "greater-than-or-equals-or-less-than",
                                   "greater-than-or-equivalent-to", "greater-than-or-less-than",
                                   "image-of-or-approximately-equals", 
                                   "less-than-or-approximately-equals", "less-than-or-similar-to",
                                   "much-greater-than", "much-less-than",
                                   "not-approximately-equals", "not-equivalent-to", 
                                   "not-greater-than", "not-greater-than-nor-equals", "not-greater-than-or-equals",
                                   "not-less-than", "less-than-and-not-approximately-equals", "less-than-and-not-equals",
                                   "less-than-and-not-equivalent-to", "not-less-than-nor-greater-than",
                                   "not-less-than-nor-equals", "not-less-than-or-equals",
                                   "less-than-or-equals-or-greater-than", "less-than-or-greater-than",
                                   "not-much-greater-than", "not-much-less-than", "not-similar-to-or-equals",
                                   "not-precedes", "not-precedes-nor-equals", "not-precedes-or-equals", 
                                   "not-proportional-to", "not-similar-to", "not-square-image-of-or-equals",
                                   "not-succeeds", "not-succeeds-nor-equals",
                                   "not-very-much-less-than", "not-very-much-greater-than",
                                   "precedes", "precedes-and-not-approximately-equals", "precedes-and-not-equals",
                                   "precedes-and-not-equivalent-to", "precedes-or-approximately-equals",
                                   "precedes-or-equals", "precedes-or-equivalent-to",
                                   "proportional-to", "similar-to", "similar-to-or-equals",
                                   "square-image-of", "square-image-of-or-equals", 
                                   "square-original-of", "square-original-of-or-equals", "square-union",
                                   "succeeds", "succeeds-and-not-approximately-equals", "succeeds-and-not-equals",
                                   "succeeds-and-not-equivalent-to",
                                   "succeeds-or-approximately-equals", "succeeds-or-equals", "succeeds-or-equivalent-to",
                                   "not-asymptotically-equals", "not-greater-than-or-less-than", "not-less-than-or-greater-than",
                                   "not-maps-to", "not-less-than-or-similar-to", "not-not-equals", "not-subgroup-of-or-equals",
                                   "not-subset-of-and-not-equals", "not-succeeds-or-equals", "not-succeeds-or-equivalent-to",
                                   "not-asymptotically-equals", "very-much-greater-than", "very-much-less-than"]:
                        retval = cls("O!" + content, in_label='e')
                    elif content in ["complement", "conditional-set",
                                   "contains", "double-intersection", "double-subset-of", "double-superset-of",
                                   "double-union", "kernel", "not-contains", "contains-as-subgroup-or-equals",
                                   "not-contains-nor-equals", "not-subgroup-of", "not-subgroup-of-nor-equals",
                                   "subgroup-of", "subgroup-of-or-equals", "contains-as-subgroup",
                                   "not-subset-of", "not-subset-of-or-equals", "not-subset-of-nor-equals",
                                   "not-superset-of", "not-superset-of-nor-equals", "not-superset-of-or-equals",
                                   "proper-intersection", "square-intersection", "square-union",
                                   "superset-of", "superset-of-or-equals", "superset-of-and-not-equals",
                                   "join", "not-contains-as-subgroup-or-equals", "not-factorial", "not-empty-set",
                                   "not-intersection", "not-proper-intersection", "symmetric-difference"]:
                        retval = cls("O!" + content, in_label='s')
                    elif content in ["because", "does-not-prove", "not-exists", "not-proves", "proves","therefore","conditional",
                                   "models", "not-and", "not-divides", "not-forces", "not-models", "not-parallel-to",
                                   "not-implies", "implied-by", "leads-to", "not-or", "not-not",
                                   "not-bottom", "not-does-not-prove", "not-exclusive-or", "not-for-all", "not-iff",
                                   "not-partial-differential", "not-perpendicular-to", "parallel-to", "perpendicular-to"]:
                        retval = cls("O!" + content, in_label="l")
                    elif content in ["contour-integral", "double-integral", "injective-limit", "limit-from", "limit-infimum",
                                   "limit-supremum", "matrix", "projective-limit", "quadruple-integral", "triple-integral",
                                   "not-minus", "not-infinity", "not-not-divides", "not-square-image-of", "not-times",
                                   "not-factorial", "not-integral",
                                   "degree", "differential-d", "infinity", "double-factorial", "multiple-integral"]:
                        retval = cls("A!" + content, in_label='f')
                    elif content in ["annotated", "approaches-limit", "assign", "between", "binomial", "bottom",
                                   "bra", "cases", "continued-fraction", 
                                   "coproduct", "currency-dollar", "difference-between", 
                                   "dimension", "direct-product", "direct-sum", "divides", "evaluated-at",
                                   "exclusive-or", "expectation", "forces", 
                                   "iff", "infimum", "inner-product",
                                   "ket", "left-normal-factor-semidirect-product", "left-semidirect-product",
                                   "maps-to", "minus-or-plus", "norm", "percent", "plus-or-minus",
                                   "product", "quantum-operator-product",
                                   "right-normal-factor-semidirect-product", "right-semidirect-product",
                                   "supremum", "tensor-product", "top", "weierstrass-p"]:
                        retval = cls("O!" + content, in_label="f")

                    elif content == "absent":
                        retval = cls("W!")
                    elif content.startswith("delimited-"):
                        # delimited single element, treat as a 1x1 vector ...
                        retval = cls("M!D-" + content[10:])
                        retval.tag = retval.tag.replace("[", "&lsqb;").replace("]", "&rsqb;")
                    elif content == "for-all":
                        retval = cls("O!forall",in_label="l")
                    elif content == "hyperbolic-cotangent":
                        retval = cls("A!coth", in_label="t")
                    elif content == "modulo":
                        retval = cls("O!rem", in_label="f")
                    elif content == "planck-constant-over-2-pi":
                        # special constant
                        retval = cls("C!hbar")
                    elif content == "square-root":
                        # by default, degree two (squared root) will be generated at the parent node
                        retval = cls("O!root", in_label="f")

                    if retval is None:
                        # check if content can be treated as a number ... (it happens .... sometimes ... )
                        try:
                            value = float(content)
                            # will reach this line only if it can be treated as a float value ...
                            retval = cls("N!" + str(value))
                        except:
                            # print("retval is None?")
                            retval = cls("E!"+short_tag+"_cd=latexml_"+content)
                            

                elif cd == "ambiguous":
                    if content == "formulae-sequence":
                        retval = cls("O!form-seq")
                    elif content == "fragments":
                        retval = cls("O!fragments")
                    elif content == "missing-subexpression":
                        retval = cls("W!")
                    elif content == "subscript":	# e.g., used for definite integrals
                        retval = cls("O!SUB")
                    elif content == "superscript":
                        retval = cls("O!SUP")
                    else:
                        # print("unknown ambiguous content")
                        retval = cls("E!"+short_tag+"_cd=ambiguous_"+content)

                elif cd == "mws":		# used in ARQMath for wildcards
                    if 'name' in elem.attrib:
                        var_name = elem.attrib['name']
                    else:
                        var_name = clean(elem.text)
                    retval = cls("?"+var_name)

                elif cd == "unknown":
                    # Unknown type ...
                    retval = cls("-!" + content)

                else:
                    # print ("unknown cd")
                    retval = cls("E!"+short_tag+"_cd="+cd)
                retval.children = children
                return retval

            else:
                # print("unknown "+short_tag)
                return cls('E!'+short_tag,children=children)


class MathSymbolIterator(object):
    """
    Depth-first iterator over a tree
    """

    def __init__(self, node, prefix, window, unbounded=False):
        self.stack = [(node, '')] if node else []
        self.prefix = prefix
        self.window = window
        self.unbounded = unbounded

    def __iter__(self): # required in Python
        return self

    def __next__(self):
        if len(self.stack) < 1:
            raise StopIteration
        (elem, path) = self.stack.pop()
        bound = True
        if not self.window or len(self.prefix)+len(path) < self.window:
            bound = True
            for child in children:
                self.stack.append((child, path+child.in_label))
        elif len(self.prefix)+len(path) >= self.window and self.unbounded:
            for child in children:
                self.stack.append((child, path+child.in_label))
        return (elem, self.prefix+path)
