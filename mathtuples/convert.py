#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Tangent-L
    Copyright (c) 2017 Dallas Fraser

    This file is part of Tangent-L.

    Tangent-L is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent-L is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - Dallas Fraser, dallas.fraser.waterloo@gmail.com

    Modified by Frank Tompa, 2021-22 and packaged with mathtuples.
        Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
'''
Name: Dallas Fraser
Date: 2017-08-25
Project: Tangent
Purpose: Convert MathML to Tangent Tuples
'''

import argparse
import logging
import sys
import os
import re
import traceback
__author__ = 'Dallas Fraser, FWTompa'

try:
   from mathtuples.math_extractor import MathExtractor
   from mathtuples.mathsymbol import MathSymbol, REP_TAG
except ImportError:
   from math_extractor import MathExtractor
   from mathsymbol import MathSymbol, REP_TAG

START_TAG = "#(start)#"
END_TAG = "#(end)#"

SYMBOL_PAIR_NODE = "S"
EDGE_PAIR_NODE = "R"
TERMINAL_NODE = "T"
EOL_NODE = "E"
COMPOUND_NODE = "C"
LONG_NODE = "L"
ABBREVIATED_NODE = "A"
DUPLICATE_NODE = "D"

INFINITE_DEPTH = 99
MAX_EOL_HEIGHT = 3
MAX_DUP = 6      # do not generate duplication tuples for more than this many repetitions

EDGES = ['n', 'a', 'b', 'c', 'o', 'u', 'd', 'w', 'e']
VERTEX_TYPES = 'VNOMFRT' # W => wildcard symbol (unknown type)

WILDCARD_MOCK = "??W"
WILDCARD = "*"
PROTECTED_WILDCARD = "--*--"
ENCODING = "utf-8"
NAMESPACE = r"(?:[^>=\s:]*:)?"
MATH_OPENED = re.compile(r"<"+NAMESPACE+r"[Mm]ath[ >]")
MATH_CLOSED = re.compile(r"</"+NAMESPACE+r"[Mm]ath>")

PgmMatch = re.compile(r'^.*/([^/]*.py)"(.*)')

def parse_file(docid="",
               context=False,
               synonyms=False,
               dups="",
               wild_dups="",
               window_size=1,
               loc_info={},
               anchors=[]):
    """Parses a file and outputs to a file with math tuples
    """
    idRE = re.compile("\Z(.)") # an impossible pattern to match
    if docid != "":
        idRE = re.compile(docid + r"([^ <>]*)")
    # with (sys.stdin if (infile is None) else open(infile, 'r', encoding=ENCODING)) as fin:
    with sys.stdin as fin:
        # with (sys.stdout if (outfile is None) else open(outfile, "w+", encoding=ENCODING)) as fout:
        with sys.stdout as fout:
            inMath = False;  # start outside all math expressions
            content = []
            mathID = ""
            lineNum = 0
            for line in fin:  # find a line end outside math expressions
                lineNum += 1
                newID = idRE.search(line)
                if newID:
                    mathID = newID.group(1)
                    lineNum = 0
                frags = MATH_CLOSED.split(line)
                if inMath or MATH_OPENED.search(frags[-1]): 
                    content.append(line)
                    inMath = True
                if MATH_CLOSED.search(line) and not MATH_OPENED.search(frags[-1]): 
                    if inMath:
                        line = "".join(content)
                        content = []
                        inMath = False
                    try:
                        tokens = MathExtractor.math_tokens(line,in_context=context)  # do not precede formula with its formula id
                        for token in tokens:
                            ex = convert_math_expression(mathID,lineNum,token,
                                                     synonyms=synonyms,
                                                     dups=dups,
                                                     wild_dups=wild_dups,
                                                     window_size=window_size,
                                                     loc_info=loc_info,
                                                     anchors=anchors)
                            if ex != "":
                                print(ex, file=fout, end="")
                                if not context:
                                    print(file=fout) # separate math expression on individual lines
                            else:
                                print(token, file=fout, end="")
                    except Exception as err:
                        print("Error in data file or query "+ mathID +", line "+ str(lineNum), file=sys.stderr)
                        stack = traceback.format_exc().split("\n")
                        where = ""
                        pgm = PgmMatch.search(stack[-4])
                        if pgm:
                            where = pgm.group(1) + pgm.group(2)
                        print("    program file",where,stack[-3].strip(),stack[-2].strip(),stack[-1],file=sys.stderr)
                        print("#(error)# ", file=fout, end="")
                elif context and not inMath: 
                    print(line,file=fout,end="")

def convert_math_expression(mathID,lineNum,mathml,
                            synonyms=False,
                            dups="",
                            wild_dups="",
                            window_size=1,
                            loc_info={},
                            anchors=[]):
    """Returns the math tuples for a given math expression

    Parameters:
        mathml: the math expression (string)
        (synonyms): True to expand nodes to include wildcard expansion (during indexing only)
        (dups): string of node types to include duplicated symbols' relative locations
        (wild_dups): string of node types to include wildcards for duplicated symbols' relative locations
        (window_size): the size of the path between nodes for symbols pairs
        (loc_info): dictionary of feature types to maximum length of locations to record
        (anchors): list of operators that reset location calculations
    Returns:
        : a string of the math tuples
    """
    try:
        pmml = MathExtractor.isolate_pmml(mathml)
        if pmml is None:
            return ""
    except: # MathML is mal-formed
        print("Badly formed MathML expression: " + mathml,file=sys.stderr)
        return ""

    tree_root = MathSymbol.parse_from_mathml(pmml)
    if tree_root is not None:
        height = tree_root.get_height(max=MAX_EOL_HEIGHT) # only measure up to max
        eol_check = False
        if height < MAX_EOL_HEIGHT:
            eol_check = (EOL_NODE in loc_info)
        repDict = {}  # dictionary to collect repetitions if necessary
        pairs = tree_root.get_pairs("",    # root's location is empty string
                                    window_size,
                                    eol=eol_check,
                                    symbol_pairs=(SYMBOL_PAIR_NODE in loc_info),
                                    compound_symbols=(COMPOUND_NODE in loc_info),
                                    terminal_symbols=(TERMINAL_NODE in loc_info),
                                    edge_pairs=(EDGE_PAIR_NODE in loc_info),
                                    unbounded=(LONG_NODE in loc_info),
                                    repetitions= dups + wild_dups,
                                    repDict=repDict,
                                    max_dup=MAX_DUP,
                                    shortened=(ABBREVIATED_NODE in loc_info),
                                    anchors=anchors)
        """
        # not relevant if all ***closest*** pairs are used
        # check whether any duplication tuples were omitted max number of repetitions exceeded
        for k in repDict:
            if len(repDict[k]) > MAX_DUP:
                print("Maximum number of duplication tuples per symbol exceeded in data file or query "+ mathID +", line "+ str(lineNum), file=sys.stderr)
                break
        """
        # all tokens returned include their location
        # replace query wildcards and expand with wildcards if synonyms
        node_list = [expanded_node
                     for node in pairs
                     for expanded_node in expand_node_with_wildcards(node,dups,wild_dups,synonyms)
                     ]
        # create a list of nodes with locations, as specified
        nodes_payloads = expand_nodes_with_location(node_list, loc_info)

        node_list = [format_node(node) for node in nodes_payloads]
        # add start and end strings
        node_list = [START_TAG] + node_list + [END_TAG]
        return " ".join(node_list)
    else:
        return ""

def expand_node_with_wildcards(node, dups, wild_dups, synonyms):
    """Returns a list of nodes that replaces wildcards in all non-duplicates and
       dups indicates vertex types to include "as is" in duplicate nodes
       wild_dups indicates vertex types to include as wild cards in duplicate nodes
       For other node types, replace query wildcards by generic wildcard.
       If synonyms, which should be at index time only, expand tuples with wildcards.
    """
    temp = list(node)
    results = []
    node_type = determine_node(node)
    if node_type == DUPLICATE_NODE:
            label = node[1]
            type = make_wild(label)  # e.g. "??V" for V!x" or "??W" for "?a" 
            if type[2:3] in dups and type != WILDCARD_MOCK:
                results.append(node)  # keep the original
            if type[2:3] in wild_dups or synonyms or type == WILDCARD_MOCK:
                temp[1] = type        # augment with wildcard
                results.append(tuple(temp))
    elif node_type == SYMBOL_PAIR_NODE or node_type == ABBREVIATED_NODE: 
            if check_wildcard(temp[0]):
                if not check_wildcard(temp[1]): # (?a,y,n)
                    temp[0] = WILDCARD_MOCK
                    results.append(tuple(temp))
            elif check_wildcard(temp[1]):      # (x,?b,n)
                temp[1] = WILDCARD_MOCK
                results.append(tuple(temp))
            else:                      # (x,y,n)
                results.append(node)
                if synonyms:
                    remember = temp[0]
                    temp[0] = make_wild(temp[0])
                    results.append(tuple(temp))
                    # now do the second node
                    temp[0] = remember
                    temp[1] = make_wild(temp[1])
                    results.append(tuple(temp))
    elif node_type == COMPOUND_NODE:
            if check_wildcard(node[0]):         # (?a,[e,f])
                temp[0] = WILDCARD_MOCK
                results.append(tuple(temp))
            else:                               # (x,[e,f])
                results.append(node)
                if synonyms:
                    temp[0] = make_wild(temp[0])
                    results.append(tuple(temp))
    elif node_type == EDGE_PAIR_NODE:
            if check_wildcard(node[2]):         # (e,f,?a)
                temp[2] = WILDCARD_MOCK
                results.append(tuple(temp))
            else:                               # (e,f,x)
                results.append(node)
                if synonyms:
                    temp[2] = make_wild(temp[2])
                    results.append(tuple(temp))
    elif node_type == TERMINAL_NODE or node_type == EOL_NODE:
            if not check_wildcard(node[0]):     # (x,!0,..)
                results.append(node)
    elif node_type == LONG_NODE:
            if not check_wildcard(node[0]) and not check_wildcard(node[1]): # (x,y)
                results.append(node)
    return results

def determine_node(node):
    """
     Pre: all nodes have location
     Returns the type of node
    """
    if node[1] == "!0":
        if len(node) == 4:  # (x,!0,n,l)
            node_type = EOL_NODE
        else:
            node_type = TERMINAL_NODE
    elif ("[" in node[1] and "]" in node[1]) or isinstance(node[1], list): # (x,[y,z],l)
        node_type = COMPOUND_NODE
    elif node[0] in EDGES and node[1] in EDGES: # (e,e,x,l)
        node_type = EDGE_PAIR_NODE
    elif node[0] == REP_TAG: # (r,x,p,l) or (r,x,p,p,l)
        node_type = DUPLICATE_NODE
    elif len(node) == 3: # (x,x,l)
        node_type = LONG_NODE
    else: # (x,x,e,l)
        node_type = SYMBOL_PAIR_NODE # or could be ABBREVIATED_NODE !
    return node_type

def make_wild(label):
    """
    given string "t!x", returns "?t"
    """
    sep = label.find("!")
    if sep == -1 or label[0] == "!": # no ! present or it is used as an operator
       if label[0] == "?":
           return WILDCARD_MOCK # wildcard can match anything
       else:
           return "??O" # must be an operator
    else:
       type = label[0:sep]
       if type in VERTEX_TYPES:
           return ("??" + type) # symbol before the exclamation point
       else:
           return label # e.g., unchanged for W! -- does this make sense?

def check_wildcard(term):
    """Returns True if term is a wildcard term
    """
    if term.startswith("?"):
    	return True
    else:
    	return False

def expand_nodes_with_location(nodes, loc_info):
    """Returns a list of nodes where each tuple is expanded to one or two tuples:
        one with its location and one without its location

    Parameters:
        nodes: the list of nodes that have been produced (loc != 0), with their locations
	loc_info: for each node type, negative => just locations, |l| = maximum number of nodes on path

    Returns:
        result: the list of nodes after expansion
    """
    result = []
    for node in nodes:
        node_type = determine_node(node) # N.B. ABBREVIATED_NODE is identified as SYMBOL_PAIR_NODE !
        depth = loc_info[node_type] # N.B. Node types that are not in loc_info cannot occur in nodes
        loc_len = 1 + len(MathSymbol.decode_loc(node[-1])) # number of nodes on path
        result.append(pop_location(node))
        if loc_len < depth or depth >= INFINITE_DEPTH:
            result.append(node)
    return result

def pop_location(node):
    """
    Parameters:
        node: the math tuple with its location
    Returns:
        : a tuple representing the node without its location
    """
    # location = node[-1]
    # need to remove the location from the tuple
    return tuple(node[0:-1])

def format_node(old_node):
    """Returns the formatted node
    """
    new_node = []
    for part in old_node:
        # We should escape * so that it is not interpreted as a wildcard symbol
        part = part.replace(WILDCARD,PROTECTED_WILDCARD)
        if part == WILDCARD_MOCK:
            part = WILDCARD
        elif part[0:2] == "??":
            part = part[1:]
        new_node.append(part)

    is_dup_node = (determine_node(old_node) == DUPLICATE_NODE)
    if is_dup_node:
        # remove first field
        new_node.pop(0)
    node = str(tuple(new_node)).lower()
    if is_dup_node:
        # also change parentheses to braces
        node = "{" + node[1:-2] + "}"
    return ("#" + (node
                   .replace(" ", "")
                   .replace("'", "")
                   .replace('"', "")
                   .replace("&comma;", "comma")
                   .replace("&quot;", "quot")
                   .replace("&apos;", "apos")
                   .replace("&lsqb;", "lsqb")
                   .replace("&rsqb;", "rsqb")
                   .replace("&quest;", "quest")
                   .replace("&amp;", "amp")
                   .replace("&", "amp")
                   .replace(">", "gt")
                   .replace("<", "lt")
                   .replace (PROTECTED_WILDCARD, "ast")
                   ) + "#")

if __name__ == "__main__":
    """logging.basicConfig(filename="convert.log",
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')
    logger = logging.getLogger(__name__)
    """

    descp = "Convert - MathML to Math Tuples"
    epilog = '''Codes:
        *tuple types  = S(ymbol pairs), R(elationship edge pairs), 
                        T(erminal symbols), E(nd of line symbols), C(ompound symbols),
                        L(ong pairs empty), A(bbreviated long pairs),
                        D(uplicate symbols)
        *tuple incl'n : (i <= 0) => include no tuples of this type
                        (0 < i < 99) => augment with location tuples whenever path length has fewer that i nodes 
                        (i >= 99) => augment with all location tuples

        **node types  = V(ariables), N(umbers), O(perations),
                        M(atrices and parenthetical expressions),
                        F(ractions), R(adicals), T(ext), W(ildcard of unknown type)
        **dups        : subset of "VNOMFRTW" to appear in duplicate nodes
        **wild dups   : subset of "VNOMFRTW" to be appear as wildcards in duplicate nodes

        defaults    : W=1, S=8, R=0, T=8, E=0, C=8, L=0, A=0, D=8
                      docid="<DOCNO>", no context, no expansion with synonyms
                      anchors enabled, dups = 'VNOMFRTW', wild_dups = 'VNOMFRTW'
    '''
    parser = argparse.ArgumentParser(description=descp,epilog=epilog,formatter_class=argparse.RawDescriptionHelpFormatter)
    #    parser.add_argument('-infile',
    #                        default=None,
    #                        help='The file to read from; omitted =>stdin')
    #    parser.add_argument('-outfile',
    #                        default=None,
    #                        help='The file to output to; omitted => stdout')
    parser.add_argument("-W",'--window_size',
                        dest="window_size",
                        default=1,
                        type=int,
                        help='The size of the window for symbol pairs (99 => unlimited); default = 1')
    parser.add_argument("-S", "--symbol_pairs",
                        dest="symbol_pairs",
                        help="Include Symbol pairs and/or locations*",
                        default=8,
			            type = int)
    parser.add_argument("-R",'--edge_pairs',
                        dest="edge_pairs",
                        help="Include Relationship edge pairs and/or locations*",
                        default=0,
			            type = int)
    parser.add_argument("-T",'--terminal_symbols',
                        dest="terminal_symbols",
                        help="Include Terminal symbols and/or locations*",
                        default=8,
			            type = int)
    parser.add_argument("-E",'--eol',
                        dest="eol",
                        help="Include End-of-line symbols and/or locations*",
                        default=0,
			            type = int)
    parser.add_argument("-C",'--compound_symbols',
                        dest="compound_symbols",
                        help="Include Compound symbols and/or locations*",
                        default=8,
			            type = int)
    parser.add_argument("-L",'--long_pairs',
                        dest="long",
                        help="Include Long pairs without relationships and/or locations*",
                        default=0,
			            type = int)
    parser.add_argument("-A",'--abbreviated',
                        dest="abbreviated",
                        help="Include Abbreviated relationships for long pairs and/or locations*",
                        default=0,
			            type = int)
    parser.add_argument("-D",'--duplicate_nodes',
                        dest="duplicate_nodes",
                        help="Include Duplicate symbols and/or locations*",
                        default=8,
			            type = int)
    parser.add_argument("-docid",'--docid',
                        dest="docid",
                        help="String preceding each document identifier; '' => no docid",
                        default="<DOCNO>")
    parser.add_argument("-a",'--anchors',
                        dest="anchors",
                        help="Enable (e)/disable (d) 'equality' operators to anchor location calculations; default => e",
                        default="e")
    parser.add_argument("-c",'--context',
                        dest="context",
                        action="store_true",
                        help="Return the math tuples in context; default => tuples only",
                        default=False)
    parser.add_argument("-d",'--dups',
                        dest="dups",
                        help="Include duplication tuples for subset of 'VNOMFRTW'**",
                        default="VNOMFRTW")
    parser.add_argument("-s",'--synonyms',
                        dest="synonyms",
                        action="store_true",
                        help="Expand nodes to include wildcard synonyms",
                        default=False)
    parser.add_argument("-w",'--wild_dups',
                        dest="wild_dups",
                        help="Wild duplication tuples for subset of 'VNOMFRTW'**",
                        default="VNOMFRTW")
    args = parser.parse_args()

    # rationalize indicators for duplicates
    dups = args.dups
    wild_dups = args.wild_dups
    duplicate_nodes = args.duplicate_nodes
    if duplicate_nodes != 0 and wild_dups == "" and dups == "":
        wild_dups = VERTEX_TYPES + "W"
        print("duplicates requested, but no types specified, so wilds used for all types",file=sys.stderr)
    if args.anchors:
        if args.anchors[0] == "d":
            anchors = []
        else:
           anchors = [":=","<","=",">","≠","≤","≥",
			   "∝","∼","≅","≈","≡",
			   "→","↔","↦","⇒","⇔","⟹",
			   "⊂","⊆","⊈"]
    else:
        anchors = []
    # store location directives
    loc_info = {SYMBOL_PAIR_NODE: args.symbol_pairs,
                EDGE_PAIR_NODE: args.edge_pairs,
                TERMINAL_NODE: args.terminal_symbols,
                EOL_NODE: args.eol,
                COMPOUND_NODE: args.compound_symbols,
                LONG_NODE: args.long,
                ABBREVIATED_NODE: args.abbreviated,
                DUPLICATE_NODE: duplicate_nodes}
    # remove non-positive entries from loc_info
    dels = []
    for node_type in loc_info:
        if loc_info[node_type] <= 0:
            dels.append(node_type)   # do not include these tuples as features
    for d in dels:
        del loc_info[d]

    parse_file(docid=args.docid,
               context=args.context,
               synonyms=args.synonyms,
               dups=dups,
               wild_dups=wild_dups,
               window_size=args.window_size,
               loc_info=loc_info,
               anchors=anchors)
    # logger.info("Done")
