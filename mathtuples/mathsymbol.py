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
from collections import deque
from _operator import or_
from sys import stderr
import string
import sys
import re
from html.parser import HTMLParser #RZ
import symbol
import os

try:
   from mathtuples.exceptions import UnknownTagException
   from mathtuples.mathml import MathML
except ImportError:
   from exceptions import UnknownTagException
   from mathml import MathML

REP_TAG = "!REP!"

__author__ = 'Nidhin, FWTompa'

# many changes throughout to encode simplified and more consistent node and edge structure. FWT

class MathSymbol:
    """
    Symbol in a symbol tree
    """

    def __init__(self, tag, next_elem=None, above=None, below=None, over=None, under=None, within=None,
                 pre_above=None, pre_below=None, element=None, mathml=[]): # FWT
                 
        # todo: improve representation (and equivalences) by recognizing and preserving fence="true" and separator="true"
        self.tag = tag
        self.next = next_elem
        self.above = above
        self.below = below
        self.over = over #FWT
        self.under = under #FWT
        self.within = within
        self.pre_above = pre_above #FWT
        self.pre_below = pre_below #FWT
        self.element = element # FWT
        self.mathml = mathml  #KMD

    def get_symbols(self, label, window, unbounded=False):
        return MathSymbolIterator(self, label, window, unbounded=unbounded)

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

    def get_height(self, height=0):
        children = [(self.next, 'n'), (self.above, 'a'),
                    (self.below, 'b'), (self.pre_above, 'c'),
                    (self.over, 'o'), (self.under, 'u'),
                    (self.pre_below, 'd'), (self.within, 'w'),
                    (self.element, 'e')]
        max_height = height
        for child, __ in children:
            if child:
                temp = child.get_height(height=height+1)
                if temp + height > max_height:
                    max_height = temp + height
        return max_height

    def get_pairs(self,
                  prefix,
                  window,
                  symbol_pairs=True,
                  compound_symbols=False,
                  terminal_symbols=False,
                  edge_pairs=False,
                  eol=False,
                  unbounded=False,
                  repetitions=False,
                  repDict = {},
                  shortened=False):
        """
        Return the pairs in the symbol tree

        :param prefix: unencoded path from the root to self (for location id)
        :type  prefix: string
        :param window: the max distance between symbol pairs to include
        :type  window: int
        :param compound_pairs: If True will include compout pairs (N, {e})
        :type compound_pairs: boolean
        :param terminal_symbols: If True will include terminal symbols (N)
        :type terminal_symbols: boolean
        :param edge_pairs: If True will include edge pairs (e, e, N)
        :type edge_pairs: boolean
        :param unbounded: If True will include all pairs of nodes (N, N)
        :type unbounded: boolean
        :param repetitions: If True will include all C(n,2) pairs of locations for each repeated node
        :type repetitions: boolean
        :param repDict: Dictionary mapping symbols to locations found so far
        :type repetitions: dictionary
        :param shortened: If True will shorten the path for various pairs
        :type shortened: boolean

        :return list of tuples
        :rtype list
        """
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

        loc = self.encode_loc(prefix)
        ret = []
        children = [(self.next, 'n'), (self.above, 'a'),
                    (self.below, 'b'), (self.pre_above, 'c'),
                    (self.over, 'o'), (self.under, 'u'),
                    (self.pre_below, 'd'), (self.within, 'w'),
                    (self.element, 'e')]
        if compound_symbols:
            # add the compound feature tuple - (N, {e1,e2, ...})
            available_edges = [label for child, label in children
                               if child is not None]
            if len(available_edges) > 1:
                # if less than one then information captured
                # by symbol pairs
                ret.append((self.tag, str(available_edges), loc))
        for child, label in children:
            if child:
                if symbol_pairs:
                    ret.extend(filter(lambda x: x is not None,
                                      map(mk_helper(loc),
                                          child.get_symbols(label,
                                                            window,
                                                            unbounded=unbounded
                                                            ))))
                ret.extend(child.get_pairs(prefix+label,
                                           window,
                                           eol=eol,
                                           symbol_pairs=symbol_pairs,
                                           compound_symbols=compound_symbols,
                                           terminal_symbols=terminal_symbols,
                                           edge_pairs=edge_pairs,
                                           unbounded=unbounded,
                                           repetitions=repetitions,
                                           repDict=repDict,
                                           shortened=shortened))
        if terminal_symbols and len(ret) == 0:
            # add the terminal symbols
            ret.append((self.tag, "!0", loc))
        if eol and len(ret) == 0:
            # then we have a small expression and adding eol
            ret.append((self.tag, "!0", "n", loc))
        if edge_pairs and len(prefix) > 0:
            # add the pairs of edges on this node
            ret.extend([(prefix[-1], label, self.tag, loc)
                        for child, label in children
                        if child and label != "w"])
        if repetitions:
            # insert symbol into dictionary and check for repetitions
            locations = repDict.setdefault(self.tag,[]) # retrieve previous positions
            # loc is the location of the current symbol and prefix is the same but unencoded
            for pos in locations:
                common = os.path.commonprefix([prefix,pos])
                if common == prefix: # both symbols on same path
                    ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(prefix):]),loc))
                else:
                    ret.append((REP_TAG,self.tag,self.encode_loc(pos[len(common):]),self.encode_loc(prefix[len(common):]),self.encode_loc(common)))
            repDict[self.tag].append(prefix)
        return ret

    @classmethod
    def list2matrix(cls, children, separators, parent_element):
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
                return not (node.next or node.above or node.below or node.over or node.under
                            or node.pre_above or node.pre_below) # inner matrix has attachment
            else:
                return False
                
        if len(children) < 4 and invisible_matrix(children[1]): # fenced matrix (but omit closing tag, as below)
            fence = children[0].tag
            if len(children) == 3:
                fence = fence + children[2].tag
            children[1].tag = 'M!'+fence+children[1].tag[2:]  # insert fence chararacters into label
            children[1].mathml.append(parent_element)

            return children[1]
        else:
            mnode = cls('M!',mathml=[parent_element])    # mark as if empty matrix
            num_args = 1
            if (len(children) > 2):
                if not separates(children[1].tag): # second child is not a separator
                    mnode.within = children[1]
                else:
                    mnode.within = cls('W!') # does this need the mathml attribute set?
                    if len(children) == 3:
                        mnode.within.next = children[1] # set the next field to be the separator
                    else:
                        children.insert(1,None) # insert a dummy element as first child so that separator is next
                elem = mnode.within # mark the start of the matrix element
                expr = elem # mark the start of the expression (content of matrix element)
                # invariants:
                #     mnode references the matrix node
                #     elem references the start of the matrix element being processed
                #     expr references a symbol in the expression being processed
                if len(children) == 3:  # (fence,expr-list,fence) => look for separators
                    while expr and expr.next:
                        if separates(expr.next.tag):  # nested mrow already processed to link parts
                            num_args += 1

                            # Original: All connected as "element"
                            #elem.element = expr.next   # break on separator
                            #expr.next = None
                            #elem.element.element = elem.element.next # re-link the separator
                            #elem.element.next = None
                            #elem = elem.element.element # move on to the next matrix element

                            # Modified: remove separators, but nodes after separators are element
                            elem.element = expr.next.next
                            expr.next = None
                            elem = elem.element

                            expr = elem
                        else:      
                            expr = expr.next
                else: # (fence, expr, expr, ... expr, fence)
                    for atom_num in range(2,len(children)-1):         # no nested mrow: break when argument is a separator
                        if separates(children[atom_num].tag):
                            num_args += 1
                            # Original: separator connected as "element"
                            #elem.element = children[atom_num]
                            #elem = elem.element

                            # Modified: do not link in the separator, just skip it
                            while expr.next:
                                expr = expr.next
                            # expr.next = children[atom_num]
                            # expr = expr.next
                        else:
                            if separates(children[atom_num-1].tag): # previous element was a separator
                                elem.element = children[atom_num]
                                elem = elem.element
                                expr = elem
                            else: # no separator: link to the previous expression
                                while expr.next:
                                    expr = expr.next
                                expr.next = children[atom_num]
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
            content1 = elem.within
            content2 = elem2.within
            rows1 = int(rows1) # convert to numeric)
            cols1 = int(cols1)
            cols2 = int(cols2)
            for i in range(0,rows1):
                for j in range(1,cols1):
                    content1 = content1.element
                content11 = content1.element # hold onto the first element of the next row
                content1.element = content2  # insert elements from second matrix
                for j in range(1,cols2):
                    content2=content2.element
                content22 = content2.element # hold onto the first element of the next row
                content2.element = content11 # finish linking in the row from second matrix
                content2 = content22  # move to next element
                content1 = content11
            elem.tag = 'M!' + rows2 + 'x' + str(cols1+cols2)
            return elem
        else:
            # concatenate them
            while elem.next:
                elem = elem.next
            elem.next = elem2
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
                while elem.element:
                    num_cols = num_cols + 1
                    elem = elem.element
            else:
                num_cols = 0 # row has no columns
        else:
            num_cols = 0 # no rows => no columns
        root = cls('M!' + str(num_rows) + "x" + str(num_cols),mathml=[original_element])
        if num_rows > 0: # elem points to last entry in first row (row 0)
            root.within = children[0] if children[0] or len(children) == 1 else cls('W!')
            for i in range(1,len(children)):
                while elem.element:
                    elem = elem.element
                elem.element = children[i]
        return root
    
    @classmethod
    def parse_from_mathml(cls, elem):
        """
        Parse symbol tree from mathml using recursive descent
        :param elem: a node in MathML structure on which an iterator is defined to select children
        :type  elem: a MathML node
        """

        #print(elem.tag,flush=True)
        
        def ignore_tag(elem):  #FWT
            """
            invisible operators and whitespace to be omitted from SymbolTree
            :return: True if node to be ignored
            :rtype:  boolean
            """
            if not elem:
                return True
            if elem.tag in ['W!', '']: # simple types with no values and no links
                return not (elem.next or elem.above or elem.below or elem.over or elem.under
                            or elem.within or elem.pre_above or elem.pre_below or elem.element)

        def clean(tag):
            """
            :param tag: symbol to store in pairs
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
        if not elem.tag.startswith('{'): # handle missing namespace declaration (FWT) -- should be reported as warning!
            elem.tag = MathML.namespace+elem.tag

        if elem.tag == MathML.math:
            children = list(elem)
            if len(children) == 1:
                return cls.parse_from_mathml(children[0])
            elif len(children) == 0:
                return None
            else:
                raise Exception('math element with more than 1 child')
        elif elem.tag == MathML.semantics:
            children = list(elem)
            if len(children) >= 1:
                return cls.parse_from_mathml(children[0])
            elif len(children) == 0:
                return None
        elif elem.tag == MathML.mstyle:
            children = list(elem)
            if len(children) >= 1:
                return cls.parse_from_mathml(children[0])
            elif len(children) == 0:
                return None
        elif (elem.tag == MathML.mrow) or (elem.tag == MathML.mpadded):
            children_map = filter(lambda x: not ignore_tag(x), list(map(cls.parse_from_mathml, elem)))
            children = list(children_map)
            if len(children) > 0:
                # handle parenthesized sub-expressions (FWT)
                if (len(children) > 1 and (children[0].tag in '({|∥' or children[0].tag == "&lsqb;")):
                #    and (children[-1].tag in ')}|∥' or children[-1].tag == "&rsqb;")):  # bracketed expression: treat as matrix
                    return cls.list2matrix(children , ',', elem)
                else: # just eliminate mrow and connect its children
                    elem = children[0]
                    for i in range(1,len(children)):
                        if elem.tag.startswith('M!') and children[i].tag.startswith('M!'):
                            elem = cls.matrixMerge(elem,children[i])
                        elif i == 1 and elem.tag == '-' and children[1].tag.startswith('N!'):
                            # should be a negative number: combine nodes
                            children[0].tag = 'N!-' + children[1].tag[2:]
                        else:
                            while elem.next:
                                elem = elem.next
                            elem.next = children[i]
                            elem = elem.next
                    return children[0]
            else:
                return None
        elif elem.tag == MathML.mfenced:  # treat like mrow (FWT)
            children_map = filter(lambda x: not ignore_tag(x), list(map(cls.parse_from_mathml, elem)))
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
            return cls.list2matrix(row, separators, elem)
        elif elem.tag == MathML.menclose:
            root = cls(elem.attrib.get('notation', 'longdiv'),mathml=[elem])
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) >= 1:   # allowed in standard (FWT)
                elem = children[0] if children[0] or len(children) == 1 else cls('W!')
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                root.within = children[0]
            return root
        elif elem.tag == MathML.mn:
            content = clean(elem.text)
            return cls('N!' + content if content != '' else 'W!',mathml=[elem])
        elif elem.tag == MathML.mo:  # future: improve representation (and equivalences) by recognizing and preserving fence="true" and separator="true"
            return cls(clean(elem.text),mathml=[elem])
        elif elem.tag == MathML.mi:
            content = clean(elem.text)
            return cls('V!' + content if content != '' else 'W!',mathml=[elem])
        elif elem.tag == MathML.mtext:
            content = clean(elem.text)
            return cls('T!' + content if content != '' else 'W!',mathml=[elem])  # to prevent accidental mis-typing
        elif elem.tag == MathML.mspace:
            return cls('W!',mathml=[elem])
        elif elem.tag == MathML.msub:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 2:
                # raise Exception("msub != 2 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):  # in case the base is None ... and ditto for all tags below(FWT)
                children[0] = cls('W!')         
            # FWT handle operators such as \sum_{i+1}^n so that they parse as "under" and "over"
            if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                if children[0].next or children[0].below:  # might have a sub on a sub: {x_y}_z, but not necessarily associative
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.below = children[1]
            else: # FWT future: \delta is an operator, perhaps restrict to "largeop=true" only? but not consistently present
                if children[0].next or children[0].under:  # might have an underbar on the operator
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.under = children[1]
            return root
        elif elem.tag == MathML.munder: # FWT - split sub from under
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 2:
                # raise Exception("munder != 2 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):
                children[0] = cls('W!')         
            if children[0].next or children[0].under:  # munder and mover can apply to a whole row rather than a simple symbol
                root = cls.make_matrix([children[0]],elem)
            else:
                root = children[0]                
            root.under = children[1]
            return root
        elif elem.tag == MathML.msup:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 2:
                # raise Exception("msup != 2 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):
                children[0] = cls('W!')
            # FWT handle operators such as \sum_{i+1}^n so that they parse as "under" and "over"
            if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                if children[0].next or children[0].above:  # might have a sup on a sup: {x^y}^z, but not necessarily associative
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.above = children[1]
            else:
                if children[0].next or children[0].over:  # might have an accent on the operator
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.over = children[1]
            return root
        elif elem.tag == MathML.mover: # FWT - split sup from over
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 2:
                # raise Exception("mover != 2 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):
                children[0] = cls('W!')
            if children[0].next or children[0].over:  # munder and mover can apply to a whole row rather than a simple symbol
                root = cls.make_matrix([children[0]],elem)
            else:
                root = children[0]                
            root.over = children[1]
            return root
        elif elem.tag == MathML.msubsup:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 3:
                # raise Exception("msubsup != 3 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):
                children[0] = cls('W!')
            # FWT handle operators such as \sum_{i+1}^n so that they parse as "under" and "over"
            if children[0].tag[0] == '?' or (len(children[0].tag) > 1 and children[0].tag[1] == '!'): # root is not an operator
                if children[0].next or children[0].below or children[0].above:  # cascaded use can happen
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.below = children[1]
                root.above = children[2]
            else:
                if children[0].next or children[0].under or children[0].over:  # cascaded use can happen
                    root = cls.make_matrix([children[0]],elem)
                else:
                    root = children[0]                
                root.under = children[1]
                root.over = children[2]
            return root
        elif elem.tag == MathML.munderover: # split from subsup
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) != 3:
                # raise Exception("munderover != 3 children")
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
            if ignore_tag(children[0]):
                children[0] = cls('W!')
            if children[0].next or children[0].under or children[0].over:  # munder and mover can apply to a whole row rather than a simple symbol
                root = cls.make_matrix([children[0]],elem)
            else:
                root = children[0]                
            root.under = children[1]
            root.over = children[2]
            return root
        elif elem.tag == MathML.msqrt:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return cls("W!",mathml=[elem])
            else:
                root = cls('R!',mathml=[elem])
                # RZ - square root as single symbol, rather than with a '2'
				#      for nth-root.
                elem = children[0] if children[0] or len(children) == 1 else cls('W!')
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                root.within = children[0]
                return root
        elif elem.tag == MathML.mroot:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) == 2:
                return cls('R!',mathml=[elem],pre_above=children[1],within=children[0])
            else:
                # raise Exception('mroot element with != 2 children')
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
        elif elem.tag == MathML.mfrac:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if len(children) == 2:
                return cls('F!',mathml=[elem],over=children[0],under=children[1]) #FWT
            else:
                # raise Exception('frac element with != 2 children')
                # instead of raising an error, treat it like non-parenthesized mrow
                children_map = filter(lambda x: not ignore_tag(x), children)
                children = list(children_map)
                if len(children) == 0:
                    return None
                elem = children[0]
                for i in range(1,len(children)):
                    while elem.next:
                        elem = elem.next
                    elem.next = children[i]
                return children[0]
        elif elem.tag == MathML.none or elem.tag == MathML.mphantom:
            return cls("W!")
        elif elem.tag == MathML.mtd:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) > 0 and children[-1].tag == "&comma;":
                children.pop()   # remove commas between matrix elements (no mrow)
            root = children[0] if len(children) > 0 and children[0] else cls('W!')
            elem = root
            for i in range(1,len(children)):
                while elem.next:
                    elem = elem.next
                elem.next = children[i]
            while elem.next:
                if elem.next.tag == "&comma;" and not elem.next.next:
                    elem.next = elem.next.next   # remove commas between matrix elements (mrow)
                else:
                    elem = elem.next
            return root
        elif elem.tag == MathML.mtr:
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) > 0:
                root = children[0] if children[0] else cls('W!')
                for i in range(1,len(children)):
                    children[i-1].element = children[i]  # link by e edges
                return root
            else:
                return cls('W!')
        elif elem.tag == MathML.mtable:
            children = list(map(cls.parse_from_mathml, elem))
            return cls.make_matrix(children,elem)
        elif elem.tag == MathML.mprescripts:
            return "PreScript"
        elif elem.tag == MathML.mmultiscripts: #FWT: Future: handle cascading presecripts (like sub and sup above)
            # base {sub sup}* [prescript {pre-sub pre-sup}*]
            children = list(map(cls.parse_from_mathml, elem))
            if len(children) == 0:
                return None
            if ignore_tag(children[0]):
                children[0] = cls('W!') # base must be represented
            try:
                prescript = children.index("PreScript")
            except ValueError: # no PreScript included
                prescript = len(children)
            if prescript > 1: # sub sup pairs are present
                sub = children[1] if prescript > 3 or (children[1] and children[1].tag != "W!") else None
                children[0].below = sub
                sup = children[2] if prescript > 3 or (children[2] and children[2].tag != "W!") else None
                children[0].above = sup
                for i in range(3,prescript,2):
                    sub.next = children[i] if prescript > i+2 or (children[i] and children[i].tag != "W!") else None
                    sub = sub.next
                    sup.next = children[i+1] if prescript > i+2 or (children[i+1] and children[i+1].tag != "W!") else None
                    sup=sup.next
            if prescript < len(children)-2:
                sub = children[prescript+1] if prescript < len(children)-4 or (children[prescript+1] and children[prescript+1].tag != "W!") else None
                children[0].pre_below = sub
                sup = children[prescript+2] if prescript < len(children)-4 or (children[prescript+2] and children[prescript+2].tag != "W!") else None
                children[0].pre_above = sup
                for i in range(prescript+3,len(children),2):
                    sub.next = children[i] if len(children) < i+2 or (children[i] and children[i].tag != "W!") else None
                    sub = sub.next
                    sup.next = children[i+1] if len(children) < i+2 or (children[i+1] and children[i+1].tag != "W!") else None
                    sup=sup.next
            return children[0]
        elif elem.tag ==MathML.mqvar or elem.tag == MathML.mqvar2:
            # added the case where name is given as text within tag instead of attribute (KMD)
            if 'name' in elem.attrib:
                var_name = elem.attrib['name']
            else:
                var_name = clean(elem.text)
            return cls('?'+var_name,mathml=[elem])
        elif elem.tag == MathML.merror:
            # Handle errors from conversion tools without crashing (KMD)
            inner_text = clean(elem.text)
            return cls('E!' + inner_text)
        else:
            raise UnknownTagException(elem.tag)

    def build_str(self, builder):  # added for building string representation (FWT)
        """
        Build string representation of symbol
        """

        builder.append('[')
        builder.append(self.tag)
        if self.next:
            self.next.build_str(builder)
        for child, label in [(self.above, 'a'), (self.below, 'b'), (self.over, 'o'), (self.under, 'u'), 
                             (self.pre_above, 'c'), (self.pre_below, 'd'), (self.within, 'w'), (self.element, 'e')]:
            if child:
                builder.append(','+label)
                child.build_str(builder)
        builder.append(']')

    def tostring(self):  # added to print out tree (FWT)
        str = []
        self.build_str(str)
        
        return ''.join(str)

    def get_dot_strings(self, prefix, rank_strings, node_names, node_strings, link_strings,
                        highlight=None, unified=None, wildcard=None, generic=False):

        # RZ: adding HTML parser (from Python libs) to convert HTML escape sequences to 
        # unicode symbols.
        htmlParser = HTMLParser()

        current_id = len(node_names)

        is_cluster = (self.within is not None)

        color_unification = "#EA7300"
        color_wildcards = "#FF0000"

        if len(prefix) == 0:
            loc = '-'
        elif len(prefix) > 5:
            loc = self.rlencode(prefix)
        else:
            loc = prefix

        penwidth = 1
        style = None
        peripheries = 1

        use_filled_style = False

        if wildcard is not None and loc in wildcard:
            # Wildcard matches nodes
            if is_cluster:
                color = color_wildcards
                style = "bold"
                peripheries = 2
                fontcolor = "#000000"
            else:
                if use_filled_style:
                    # Filled style
                    fillcolor = color_wildcards
                    style = "filled"
                    fontcolor = "#ffffff"
                    peripheries = 2
                else:
                    color = color_wildcards
                    style = "bold"
                    fontcolor = "#000000"
                    peripheries = 2

            if generic:
                node_label = htmlParser.unescape( self.tag[0:2] )
            else:
                node_label = htmlParser.unescape( self.tag )

        elif unified is not None and loc in unified:
            # Unified nodes
            if is_cluster:
                color = color_unification
                style = "bold"
                peripheries = 2
                fontcolor = "#000000"
            else:
                if use_filled_style:
                    # Filled style
                    fillcolor = color_unification
                    style = "filled"
                    fontcolor = "#ffffff"
                    peripheries = 2
                else:
                    color = color_unification
                    style = "bold"
                    fontcolor = "#000000"
                    peripheries = 2

            if generic:
                node_label = htmlParser.unescape( self.tag[0:2] )
            else:
                node_label = htmlParser.unescape( self.tag )

        # Exact matches
        elif highlight is not None and loc in highlight:
            if is_cluster:
                color = "#004400"
                style = "bold"
                fontcolor = "#000000"
            else:
                if use_filled_style:
                    # filled style
                    style = "bold,filled"
                    fillcolor = "#008800"
                    fontcolor = "#ffffff"
                else:
                    # thick border style
                    style = "bold"
                    fontcolor = "#000000"
                    color = "#008800"


            if self.tag[1:2] == "!":
                node_label = htmlParser.unescape( self.tag[2:] )
            else:
                node_label = htmlParser.unescape( self.tag )
        
        # Unmatched, or no unification/highlighting visualization requested.
        else:
            fontcolor = "#000000"
            if (highlight is not None) and (unified is not None):
                style = "dashed"
            else:
                if is_cluster:
                    style = "bold"
                else:
                    if use_filled_style:
                        style = "filled"
                    else:
                        style = "bold"

            if is_cluster:
                color = "#000000"
            else:
                if use_filled_style:
                    fillcolor = "#ffffff"
                else:
                    color = "#000000"


            if (highlight is not None) and generic:
                node_label = ""
            # RZ: small modification to remove types in 'query' .dot output.
            elif self.tag[1:2] == "!":
                node_label = htmlParser.unescape( self.tag[2:] )
            else:
                node_label = htmlParser.unescape( self.tag )

        # add all types of children (except within which needs special handling)
        children = []
        if self.above is not None:
            children.append(("a", self.above))
        if self.over is not None:
            children.append(("o", self.over))
        if self.pre_above is not None:
            children.append(("c", self.pre_above))
        if self.next is not None:
            children.append(("n", self.next))
        if self.below is not None:
            children.append(("b", self.below))
        if self.under is not None:
            children.append(("u", self.under))
        if self.pre_below is not None:
            children.append(("d", self.pre_below))
        if self.element is not None:
            children.append(("e", self.element))

        if self.within is not None:
            # special handling with clusters
            node_names.append("cluster" + str(current_id))

            # create a subgraph starting with the within node as root
            cluster_str = "subgraph cluster" + str(current_id) + " {\n"
            cluster_str += " style= \"" + style + "\";\n"
            cluster_str += " color= \"" + color + "\";\n"
            cluster_str += " fontcolor= \"" + fontcolor + "\";\n"
            cluster_str += " label=\"" + node_label + "\";\n"

            # generate sub-graph from the children within ...
            child_n_strings = []
            child_l_strings = []
            within_info = self.within.get_dot_strings(prefix + "w", rank_strings, node_names, child_n_strings, child_l_strings,
                                                     highlight, unified, wildcard, generic)
            within_id, within_cluster, within_head_id, within_tail = within_info
            within_tail_id, within_tail_depth = within_tail
            head_id = within_head_id

            child_content = " ".join(child_n_strings) + " ".join(child_l_strings)
            cluster_str += child_content
            cluster_str += "}\n"

            # add cluster as a node
            node_strings.append(cluster_str)

            # source for links to children
            source_name = "n_" + str(within_tail_id)

        else:
            # other nodes that are not handled as clusters...
            head_id = current_id
            node_name = "n_" + str(current_id)
            node_names.append(node_name)

            # create node string
            if use_filled_style:
                # fill style nodes....
                style_str = "style=\"" + style + "\" fillcolor=\"" + fillcolor + "\" fontcolor=\"" + fontcolor + "\""
            else:
                style_str = "style=\"" + style + "\" color=\"" + color + "\" fontcolor=\"" + fontcolor + "\""

            if peripheries > 1:
                style_str += " peripheries=\"2\""
            current_str = node_name + "[label=\"" + node_label + "\" " + style_str + "];\n"

            # add node
            node_strings.append(current_str)

            # source for links to children
            source_name = node_name

        # now, add node children
        tail_id = None
        tail_depth = 0
        
        for relation, child in children:
            # call recursively ...
            child_info = child.get_dot_strings(prefix + relation, rank_strings, node_names, node_strings, link_strings,
                                               highlight, unified, wildcard, generic)
            child_id, child_cluster, child_head_id, child_tail = child_info
            child_tail_id, child_tail_depth = child_tail

            # check if new deepest tail has been found
            if tail_id is None or child_tail_depth > tail_depth:
                # keep the deepest tail only
                tail_id = child_tail_id
                tail_depth = child_tail_depth

            # connect to child (or grand child if child is a cluster)
            child_name = "n_" + str(child_head_id)
            

            modificationString = ""
            relationLabel = relation
            if relation == "n":
                relationLabel = ""
                modificationString = " weight=\"5\""
            elif relation == "e":
                relationLabel = ""
                modificationString = " weight=\"3\", arrowhead=\"odot\""
            elif relation == "a":
                relationLabel = '\u2191'
            elif relation == "b":
                relationLabel = '\u2193'
            elif relation == "c":
                relationLabel = '\u2196'
            elif relation == "d":
                relationLabel = '\u2199'

            # check source type of link
            if is_cluster:
                # source is cluster ...
                if child_cluster:
                    child_link = source_name + " -> " + child_name + " [label=\"" + relationLabel + "\", lhead=\"cluster" + \
                                 str(child_id) + "\", ltail=\"cluster" + str(current_id) + "\"" + modificationString + " ];\n"
                else:
                    child_link = source_name + " -> " + child_name + " [label=\"" + relationLabel + \
                                 "\", ltail=\"cluster" + str(current_id) + "\"" + modificationString + " ];\n"
            else:
                # source is node ...
                if child_cluster:
                    child_link = node_name + " -> " + child_name + " [label=\"" + relationLabel + "\", lhead=\"cluster" + \
                                 str(child_id) + "\"" + modificationString + " ];\n"
                else:
                    child_link = node_name + " -> " + child_name + " [label=\"" + relationLabel + "\"" + modificationString + " ];\n"

            link_strings.append(child_link)

            # RZ: Add 'rank=same' information for adjacent nodes.
            #leftNode = None
            #rightNode = child_name
            #if relation == 'e':
            #    if is_cluster:
             #       leftNode = source_name
             #   else:
              #      leftNode = node_name
              #  rank_strings.append("{ rank=same; " + leftNode + "; " + rightNode + "; }\n")

        # set the tail ....
        if tail_id is None:
            # no children ...
            if is_cluster:
                # use inner tail as tail ...
                tail = (within_tail_id, within_tail_depth)
            else:
                # use itself as tail
                # (remove "w" boxes of parents as part of the current depth)
                no_box_prefix = prefix.replace("w", "")
                tail = (current_id, len(no_box_prefix))
        else:
            tail = (tail_id, tail_depth)


        #print(str((self.tag, current_id, is_cluster, head_id, tail)))

        return current_id, is_cluster, head_id, tail

    def mark_matches(self, location, matches, unified, wildcard_matches):
        if location == "":
            short_loc = "-"
        elif len(location) <= 5:
            short_loc = location
        else:
            short_loc = MathSymbol.rlencode(location)


        if short_loc in wildcard_matches:
            color = "#FD2020"
        elif short_loc in unified:
            #color = "#FD6120"
            color = "#FD9D20"
        elif short_loc in matches:
            color = "#1B7A1B"
        else:
            color ="#000000"

        #print(location)
        #print(self.mathml)
        #print(self.tag)
        for elem in self.mathml:
            #if isinstance(elem, MathSymbol):
            #    print(elem.tag)

            elem.attrib["mathcolor"] = color

        #call recursively...
        if self.next is not None:
            self.next.mark_matches(location + "n", matches, unified, wildcard_matches)
        if self.above is not None:
            self.above.mark_matches(location + "a", matches, unified, wildcard_matches)
        if self.below is not None:
            self.below.mark_matches(location + "b", matches, unified, wildcard_matches)
        if self.over is not None:
            self.over.mark_matches(location + "o", matches, unified, wildcard_matches)
        if self.under is not None:
            self.under.mark_matches(location + "u", matches, unified, wildcard_matches)
        if self.pre_above is not None:
            self.pre_above.mark_matches(location + "c", matches, unified, wildcard_matches)
        if self.pre_below is not None:
            self.pre_below.mark_matches(location + "d", matches, unified, wildcard_matches)
        if self.within is not None:
            self.within.mark_matches(location + "w", matches, unified, wildcard_matches)
        if self.element is not None:
            self.element.mark_matches(location + "e", matches, unified, wildcard_matches)


class MathSymbolIterator(object):
    """
    Iterator over a symbol tree
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
            for child, label in [(elem.next, 'n'), (elem.above, 'a'), (elem.below, 'b'), (elem.over, 'o'), (elem.under, 'u'),
                                 (elem.pre_above, 'c'), (elem.pre_below, 'd'), (elem.within, 'w'), (elem.element, 'e')]:
                if child:
                    self.stack.append((child, path+label))
        elif len(self.prefix)+len(path) >= self.window and self.unbounded:
            for child, label in [(elem.next, 'n'), (elem.above, 'a'), (elem.below, 'b'), (elem.over, 'o'), (elem.under, 'u'),
                                 (elem.pre_above, 'c'), (elem.pre_below, 'd'), (elem.within, 'w'), (elem.element, 'e')]:
                if child:
                    self.stack.append((child, path+label))
        return (elem, self.prefix+path)
