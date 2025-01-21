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
import sys
import re
import string
import io
import xml
import os
import codecs
import platform
from xml.parsers import expat
import xml.etree.ElementTree as ET
from sys import stderr

from .mathsymbol import MathSymbol
from .symboltree import SymbolTree
from .exceptions import UnknownTagException
from .utility import uprint

__author__ = 'Nidhin, FWTompa'

## TODO: simplify math extraction by creating simple list of math expressions and then grouping them by SLT, rather than by LaTeX


class MathExtractor:
    def __init__(self):
        pass

    namespace = r"(?:[^>=\s:]*:)?"
    # attributes = r"(?: [^>]*)?"
    attr_val = "(?:\"[^\"]+\"|'[^']+')"
    id_attr = r"(?:\s+"+"id="+attr_val+")?"
    named_id = r"(?:\s+[^>=\s:]*:id="+attr_val+")"
    notid_attrs = r"(?:(?:\s+"+namespace+"(?:[^=>:\s][^=>:\s][^=>:\s]+|[^=>\s]|[^i][^=]|i[^d=])="+attr_val+")|"+named_id+")*" # >2 chars | 1 char | !i. | .!d | with a namespace
    attributes = notid_attrs + "(" + id_attr + ")" + notid_attrs
    math_expr = "(<("+namespace+"[Mm]ath)"+ attributes +r">.*?</\2>)" # match same QName to handle nesting
    # print("match: "+math_expr,file=stderr)

    math_pattern = re.compile(math_expr, re.DOTALL)  # does not allow for LaTeX

    open_tag = re.compile("<(?!/)(?!mws:qvar)"+namespace, re.DOTALL) # up to and including namespace
    close_tag = re.compile("</(?!mws:qvar)"+namespace, re.DOTALL)    # but keep qvar namespace

    @classmethod
    def math_tokens(cls, content, in_context=False, with_id=False):
        """
        extract Math expressions from XML (incl. HTML) file
        
        param content: XML document
        type  content: string
        
        param (in_context): whether to include text fragments as well (even numbered elements are math)
        type  (in_context): boolean

        param (with_id): whether to include the math formula id, if present
        type  (with_id): boolean

        return: embedded math expressions
        rtype:  list(string) where every (other) string is a MathML expr; each is preceded by formula id if with_id=True
                N.B. All namespaces are removed
        """

        if in_context:
            pieces = cls.math_pattern.split(content)  # include surrounding text
            contexts = pieces[0::4] # each math piece uses 3 slots
            # print("Number of contexts detected: "+ str(len(contexts)))
        exprs = cls.math_pattern.findall(content) # just the math expressions
        # print("Number of formulas detected: "+ str(len(exprs)))
        math = []

        for (math_expr,QName,formula_id) in exprs:
            # print("Math expression = ",math_expr.encode("utf-8"),file=stderr)
           
            # assert: math_expr.endswith("ath>"): # MathML token
            math_expr = cls.close_tag.sub("</",math_expr) # drop namespaces (FWT)
            math_expr = cls.open_tag.sub("<",math_expr)
            math_expr = math_expr.replace("<Math ","<math ").replace("</Math>","</math>")
            # print("Revised token = ",math_expr,file=stderr)
            # print("id = "+formula_id,file=stderr)
            if with_id:
                math.append(formula_id)
            math.append(math_expr)
                
        if in_context:
            pieces = contexts + math # make a list of the right length
            pieces[::2] = contexts
            pieces[1::2] = math
            return pieces
        else:
            return math

    '''
    as produced by LaTeXML:

    <math display="block" alttext="a+F(a,b)" class="ltx_Math" id="m1">
      <semantics id="m1a">
        <mrow xref="m1.7.cmml" id="m1.7">
          <mi xref="m1.4.cmml" id="m1.4">a</mi>
          <mo xref="m1.5.cmml" id="m1.5">+</mo>
          <mrow xref="m1.6.cmml" id="m1.6d">
            <mi xref="m1.1.cmml" id="m1.1">F</mi>
            <mo xref="m1.6.cmml" id="m1.6e">&ApplyFunction;</mo>
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
    '''

    @classmethod
    def isolate_mml(cls,math_expr,wants_cmml=False):
        """
        extract the desired form of MathML from an MathML expr
        
        param math_expr: MathML expression
        type  math_expr: string surrounded by "<math ...</math>"
        param wants_cmml: flag to indicate whether Content (as opposed to Presentation) desired
        type  wants_cmml: boolean
        return: Presentation MathML (default) or Content MathML
        rtype:  Element
        """
        if (len(math_expr) == 0):
            return None
        #print("MathML: " + math_expr)
        
        math_root = ET.fromstring(math_expr)
##        print("isolate_" + (wants_cmml if "cmml" else "pmml") + " math_expr: " + ET.tostring(xml_root,encoding="unicode"))

        tex_parent=math_root.find(".//annotation[@encoding='application/x-tex']/..")
        if tex_parent is not None:
            tex_markup = tex_parent.find("./annotation[@encoding='application/x-tex']")
            tex_parent.remove(tex_markup) # delete any tex annotation

        want="Content" if wants_cmml else "Presentation"
        other="Presentation" if wants_cmml else "Content"
        markup=math_root.find(".//annotation-xml[@encoding='MathML-" + want + "']")
        if markup is not None:    # found an annotation of the correct type
            markup.tag = "math"
        else:
            markup=math_root
            other_parent=math_root.find(".//annotation-xml[@encoding='MathML-" + other +"']/..")
            if other_parent is not None:    # found an annotaion of the other type
                other_markup = other_parent.find("./annotation-xml[@encoding='MathML-" + other + "']")
                other_parent.remove(other_markup) # delete any other MML
            else:  # only one markup present
                if (markup.get("encoding") == "MathML-Content"):  # seems to be CMML
                #if (markup.find("..//apply") is not None):  # seems to be CMML --- why does this not find a subelement tagged "apply"?
                    if not wants_cmml:
                       return None
                else:  # seems to be PMML
                    if wants_cmml:
                       return None
        markup.set('xmlns',"http://www.w3.org/1998/Math/MathML") # set the default namespace
        return markup

