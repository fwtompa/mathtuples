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
    Modified by Frank Tompa, 2021
    Packaged with mathtuples. Contact:
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
__author__ = 'Dallas Fraser, FWTompa'

try:
   from mathtuples.math_extractor import MathExtractor
   from mathtuples.mathsymbol import MathSymbol, REP_TAG
except ImportError:
   from math_extractor import MathExtractor
   from mathsymbol import MathSymbol, REP_TAG


START_TAG = "#(start)#"
END_TAG = "#(end)#"
TERMINAL_NODE = "terminal_node"
COMPOUND_NODE = "compound_node"
EDGE_PAIR_NODE = "edge_pair"
EOL_NODE = "eol_node"
REPETITION_NODE = "repetition_node"
SYMBOL_PAIR_NODE = "symbol_pair"
EDGES = ['n', 'a', 'b', 'c', 'o', 'u', 'd', 'w', 'e']
WILDCARD_MOCK = "?x"
WILDCARD = "*"
ENCODING = "utf-8"



def convert_math_expression(mathml,
                            window_size=1,
                            symbol_pairs=True,
                            terminal_symbols=True,
                            compound_symbols=True,
                            location=True,
                            eol=False,
                            edge_pairs=False,
                            unbounded=False,
                            shortened=True,
                            repetitions=False,
                            synonyms=False):
    """Returns the math tuples for a given math expression

    Parameters:
        mathml: the math expression (string)
        (window_size): The size of the path between nodes for symbols pairs
        (symbol_pairs): True will include symbol pairs
        (terminal_symbols): True to include terminal symbols nodes
        (compound_symbols): True to include compound symbols nodes
        (location): True to include locations as well
        (eol): True will included eol nodes
        (edge_pairs): True to include edge pairs nodes
        (unbounded): True - unbounded window size
        (shortened): True - shorten symbol pair paths (if unbounded=True)
        (repetitions): True to include repeated symbol's relative locations
        (synonyms): True to expand nodes to include wildcard expansion (during indexing only)
    Returns:
        : a string of the math tuples
    """
    pmml = MathExtractor.isolate_pmml(mathml)
    tree_root = MathSymbol.parse_from_mathml(pmml)
    if tree_root is not None:
        height = tree_root.get_height()
        eol_check = False
        if height <= 2:
            eol_check = eol
        repDict = {}  # dictionary to collect repetitions if necessary
        pairs = tree_root.get_pairs("",    # root's location is empty string
                                    window_size,
                                    eol=eol_check,
                                    symbol_pairs=symbol_pairs,
                                    compound_symbols=compound_symbols,
                                    terminal_symbols=terminal_symbols,
                                    edge_pairs=edge_pairs,
                                    unbounded=unbounded,
                                    repetitions=repetitions,
                                    repDict=repDict,
                                    shortened=shortened)
        # all tokens returned include their location
        if not synonyms:
            node_list = [node
                         for node in pairs
                         if check_node(node)]
        else:
            # loop through all kept nodes and their expanded nodes
            node_list = [expanded_node
                         for node in pairs
                         if check_node(node)
                         for expanded_node in expand_node_with_wildcards(node)
                         ]
        # create a list of nodes
        # do we want to expand with location
        if location:
            nodes_payloads = expand_nodes_with_location(node_list)
        else:
            # remove the location if not wanted
            nodes_payloads = [pop_location(node, False)
                              for node in node_list]
        node_list = [format_node(node) for node in nodes_payloads]
        # add start and end strings
        node_list = [START_TAG] + node_list + [END_TAG]
        return " ".join(node_list)
    else:
        return ""


def check_node(node):
    """Returns False if the node is not needed
    """
    node_type = determine_node(node)
    check = True
    if node_type == EOL_NODE or node_type == TERMINAL_NODE:
        # only need to look at first part
        check = not check_wildcard(node[0])
    elif node_type == SYMBOL_PAIR_NODE:
        # does it make sense to keep pairs of symbols with no path
        # if one of those symbols is a wildcard
        if len(node) == 3:
            # if one is a wildcard then dont want to keep it
            check = not(check_wildcard(node[0]) or check_wildcard(node[1]))
        else:
            # then both need to be a wildcard
            check = not(check_wildcard(node[0]) and check_wildcard(node[1]))
    elif node_type == EDGE_PAIR_NODE or node_type == COMPOUND_NODE or node_type == REPETITION_NODE:
        # keep them regardless at this point
        pass
    return check


def expand_nodes_with_location(nodes):
    """Returns a list of nodes where each tuple is expanded to two tuples
        one with its location and one without its location

    Parameters:
        nodes: the list of nodes with their locations
    Returns:
        result: the list of nodes after expansion
    """
    result = []
    for node in nodes:
        # add the first node
        result.append(pop_location(node,True))
        # add the second node
        result.append(pop_location(node,False))
    return result


def pop_location(node, include_location):
    """Returns the node without location

    Parameters:
        node: the math tuple with its location
        include_location: whether to include the location in the tuple
    Returns:
        : a tuple representing the node with or without its location
    """
    # location = node[-1]
    if not include_location:
        # need to remove the location from the tuple
        node = list(node)
        node.pop()
        node = tuple(node)
    return node


def check_wildcard(term):
    """Returns True if term is a wildcard term
    """
    if term.startswith("?"):
    	return True
    else:
    	return False


def format_node(old_node):
    """Returns the formatted node
    """
    new_node = []
    for part in old_node:
        new_node.append(part)
        if "*" in part:
            new_node[-1] = "/*"
        if "?" in part:
            new_node[-1] = WILDCARD
    if determine_node(old_node) == REPETITION_NODE:
        # remove first field
        new_node.pop(0)
    node = tuple(new_node)
    node = str(node).lower()
    if determine_node(old_node) == REPETITION_NODE:
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
                   .replace(">", "gt")
                   .replace("<", "lt")
                   ) + "#")


def determine_node(node):
    """Returns the type of node
    """
    node_type = SYMBOL_PAIR_NODE
    if node[1] == "!0":
        if len(node) == 2:
            node_type = TERMINAL_NODE
        elif node[2] == "n":
            node_type = EOL_NODE
        else:
            node_type = TERMINAL_NODE
    elif ("[" in node[1] and "]" in node[1]) or isinstance(node[1], list):
        node_type = COMPOUND_NODE
    elif node[0] in EDGES:
        node_type = EDGE_PAIR_NODE
    elif node[0] == REP_TAG:
        node_type = REPETITION_NODE
    return node_type

def expand_node_with_wildcards(node):
    """Returns a list of nodes that includes the expanded nodes
    """
    results = [node]
    node_type = determine_node(node)
    if node_type == SYMBOL_PAIR_NODE:
        # if just two symbols (no path) then no point in expanding
        if len(node) > 3:
            # expands to two nodes
            # one with first tag as wc and second tag as wc
            temp = list(node)
            remember = temp[0]
            if (not check_wildcard(remember) and not check_wildcard(temp[1])):
                temp[0] = WILDCARD_MOCK
                results.append(tuple(temp))
            	# now do the second node
                temp[0] = remember
                temp[1] = WILDCARD_MOCK
                results.append(tuple(temp))
    elif node_type == COMPOUND_NODE:
        # add an expansion of the compound node
        # the node tag is replaced with a wildcard
        if (not check_wildcard(node[0])):
            temp = list(node)
            temp[0] = WILDCARD_MOCK
            results.append(tuple(temp))
    elif node_type == EDGE_PAIR_NODE:
        # replace tag with a wildcard
        if (not check_wildcard(node[-2])):
            temp = list(node)
            temp[-2] = WILDCARD_MOCK
            results.append(tuple(temp))
    elif node_type == REPETITION_NODE:
        # add an expansion of the repetition node
        # the node tag is replaced with a wildcard
        if (not check_wildcard(node[1])):
            temp = list(node)
            temp[1] = WILDCARD_MOCK
            results.append(tuple(temp))
    elif node_type == TERMINAL_NODE or EOL_NODE:
        # no expansion for them
        pass
    return results

def parse_file(filename,
               outfile,
               window_size=1,
               symbol_pairs=True,
               eol=False,
               compound_symbols=True,
               terminal_symbols=True,
               edge_pairs=False,
               unbounded=False,
               shortened=True,
               location=True,
               repetitions=False,
               synonyms=False):
    """Parses a file and outputs to a file with math tuples

    Parameters:
        filename: the name of the file to parse
        outfile: the name of the file to output to; NONE => use sys.stdout
    """
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    if outfile is not None:
        out = open(outfile, "w+", encoding=ENCODING)
    else:
        out = sys.stdout
    tokens = MathExtractor.math_tokens(content)  # do not precede formula with its formula id
    if len(tokens) == 0:
        print("No math formulas detected.")
    for token in tokens:
        ex = convert_math_expression(token,
                                     window_size=window_size,
                                     symbol_pairs=symbol_pairs,
                                     eol=eol,
                                     compound_symbols=compound_symbols,
                                     terminal_symbols=terminal_symbols,
                                     edge_pairs=edge_pairs,
                                     unbounded=unbounded,
                                     shortened=shortened,
                                     location=location,
                                     repetitions=repetitions,
                                     synonyms=synonyms)
        print(ex, file=out)
    if outfile is not None:
        os.close(out)

if __name__ == "__main__":
    """logging.basicConfig(filename="convert.log",
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')
    logger = logging.getLogger(__name__)
    """
    descp = "Convert - MathML file to file with Tangent Tuples"
    parser = argparse.ArgumentParser(description=descp)
    parser.add_argument('-infile',
                        '--infile',
                        help='The file to read from')
    parser.add_argument('-outfile',
                        '--outfile',
                        help='The file to output to')
    parser.add_argument("-symbol_pairs",
                        dest="symbol_pairs",
                        action="store_false",
                        help="Do not use symbol pairs",
                        default=True)
    parser.add_argument('-eol',
                        dest="eol",
                        action="store_true",
                        help="Use EOL tuples",
                        default=False)
    parser.add_argument('-compound_symbols',
                        dest="compound_symbols",
                        action="store_false",
                        help="Do not use compound symbols",
                        default=True)
    parser.add_argument('-terminal_symbols',
                        dest="terminal_symbols",
                        action="store_false",
                        help="Use terminal symbols",
                        default=True)
    parser.add_argument('-edge_pairs',
                        dest="edge_pairs",
                        action="store_true",
                        help="Use edge pairs",
                        default=False)
    parser.add_argument('-unbounded',
                        dest="unbounded",
                        action="store_true",
                        help="Symbol pairs should be unbounded",
                        default=False)
    parser.add_argument('-shortened',
                        dest="shortened",
                        action="store_false",
                        help="Unbounded symbol pairs should not include abbreviated path",
                        default=True)
    parser.add_argument('-synonyms',
                        dest="synonyms",
                        action="store_true",
                        help="Expand nodes to include synonyms",
                        default=False)
    parser.add_argument('-repetitions',
                        dest="repetitions",
                        action="store_true",
                        help="Include repeated symbols",
                        default=False)
    parser.add_argument('-location',
                        dest="location",
                        action="store_false",
                        help="Do not include location",
                        default=True)
    parser.add_argument('-window_size',
                        dest="window_size",
                        default=1,
                        type=int,
                        help='The size of the window',
                        nargs='?')
    args = parser.parse_args()
    if args.infile is not None:
        parse_file(args.infile,
                   args.outfile, # if None, will write to sys.stdout
                   window_size=args.window_size,
                   symbol_pairs=args.symbol_pairs,
                   eol=args.eol,
                   compound_symbols=args.compound_symbols,
                   terminal_symbols=args.terminal_symbols,
                   edge_pairs=args.edge_pairs,
                   unbounded=args.unbounded,
                   shortened=args.shortened,
                   location=args.location,
                   repetitions=repetitions,
                   synonyms=args.synonyms
                   )
    # logger.info("Done")
