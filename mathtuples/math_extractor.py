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

try:
   from mathtuples.mathsymbol import MathSymbol
   from mathtuples.symboltree import SymbolTree
   from mathtuples.latex_mml import LatexToMathML
   from mathtuples.exceptions import UnknownTagException
   from mathtuples.utility import uprint
except ImportError:
   from mathsymbol import MathSymbol
   from symboltree import SymbolTree
   from latex_mml import LatexToMathML
   from exceptions import UnknownTagException
   from utility import uprint

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

    # dollars = r"(?<!\\)\$+"
    # latex_expr = dollars+".{1,200}?"+dollars # converted to math_expr in cleaned text
    ### latex could also be surrounded by \(..\) or \[..\], but these are ignored for now (FWT)
    # text_token = r"[^<\s]+"
    # split_pattern = re.compile(math_expr+"|"+latex_expr+"|"+text_token, re.DOTALL)

    math_pattern = re.compile(math_expr, re.DOTALL)  # TODO: allow for LaTeX as above

    # inner_math = re.compile(".*(<"+math_expr+")", re.DOTALL)  # rightmost <*:math : no longer used: invalid
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
        rtype:  list(string) where each string is a MathML expr; each is preceded by formula id if with_id=True
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
           
            if math_expr.endswith("ath>"): # MathML token
                math_expr = cls.close_tag.sub("</",math_expr) # drop namespaces (FWT)
                math_expr = cls.open_tag.sub("<",math_expr)
                math_expr = math_expr.replace("<Math ","<math ").replace("</Math>","</math>")

                # print("Revised token = ",math_expr,file=stderr)
                # print("id = "+formula_id,file=stderr)
                if with_id:
                    math.append(formula_id)
                math.append(math_expr)
                
            else:  # LaTeX math expression (once they are recognized as well)
                tex = math_expr.strip("$")
                if with_id:
                    math.append("") # TODO: handle other latex delimiters
                math.append(LatexToMathML.convert_to_mathml(tex))           

        if in_context:
            pieces = contexts + math # make a list of the right length
            pieces[::2] = contexts
            pieces[1::2] = math
            return pieces
        else:
            return math


    @classmethod
    def isolate_pmml(cls,math_expr):
        """
        extract the Presentation MathML from a MathML expr
        
        param math_expr: MathML expression
        type  math_expr: string
        return: Presentation MathML
        rtype:  Element
        """
        if (len(math_expr) == 0):
            return None
        #print("MathML: " + math_expr)
        
        math_root = ET.fromstring(math_expr)
##        print("parse_from_mathml tree: " + ET.tostring(xml_root,encoding="unicode"))

        application_tex= math_root.find("annotation",{"encoding":"application/x-tex"})
        
        if application_tex:
##            application_tex_text=application_tex.text
            application_tex.decompose()

        pmml_markup=math_root.find(".//annotation-xml[@encoding='MathML-Presentation']")
        if pmml_markup is not None:
            pmml_markup.tag = "math"
        else:
            pmml_markup=math_root
            cmml_parent=math_root.find(".//annotation-xml[@encoding='MathML-Content']/..")
            if cmml_parent is not None:
                cmml_markup = cmml_parent.find("./annotation-xml[@encoding='MathML-Content']")
                cmml_parent.remove(cmml_markup) # delete any Content MML
        pmml_markup.set('xmlns',"http://www.w3.org/1998/Math/MathML") # set the default namespace
        return pmml_markup

    @classmethod
    def convert_to_mathsymbol(cls, elem):
        """
        Parse expression from MathML


        :param elem: mathml
        :type  elem: Element
        :rtype MathSymbol or None
        :return root of symbol tree

        """
        if (len(elem) == 0):
            return None
        elem_content = io.StringIO(elem) # treat the string as if a file
        parser = ET.XMLParser(encoding="utf-8")
        root = ET.parse(elem_content,
                                           parser=parser).getroot()
        mmathml = ET.tostring(root, encoding="unicode")
        # uprint("parse_from_mathml tree: " + mmathml)
        return MathSymbol.parse_from_mathml(root)

    @classmethod
    def convert_and_link_mathml(cls, elem, document=None, position=None):
        """
        Parse expression from MathML keeping the links to the original MathML for visualization purposes


        :param elem: mathml
        :type  elem: string

        :rtype SymbolTree or None
        :return Symbol tree instance

        """
        if (len(elem) == 0):
            return None

        elem_content = io.StringIO(elem) # treat the string as if a file
        root = ET.parse(elem_content).getroot()
##        print("parse_from_mathml tree: " + ET.tostring(root,encoding="unicode"))
        symbol_root = MathSymbol.parse_from_mathml(root)

        return SymbolTree(symbol_root, document, position, root)


    @classmethod
    def parse_from_tex(cls, tex, file_id=-1, position=[0]):
        """
        Parse expression from Tex string using latexmlmath to convert to presentation markup language


        :param tex: tex string
        :type tex string
        :param file_id: file identifier
        :type  file_id: int

        :rtype SymbolTree
        :return equivalent SymbolTree

        """

        #print("Parsing tex doc %s" % file_id,flush=True)
        mathml=LatexToMathML.convert_to_mathml(tex)
        pmml = cls.isolate_pmml(mathml)
##        print('LaTeX converted to MathML: \n' )
        return SymbolTree(cls.convert_to_mathsymbol(pmml),file_id,position)


    @classmethod
    def parse_from_xml(cls, content, content_id, missing_tags=None, problem_files=None):
        """
        Parse expressions from XML file

        :param content: XML content to be parsed
        :type  content: string
        :param content_id: fileid for indexing or querynum for querying
        :type  content_id: int
        :param missing_tags: dictionary to collect tag errors
        :type  missing_tags: dictionary(tag->set(content_id))
        :param problem_files: dictionary to collect parsing errors
        :type  problem_files: dictionary(str->set(content_id))

        :rtype list(SymbolTree)
        :return list of Symbol trees found in content identified by content_id

        """
        idx = -1
        try:
            trees = cls.math_tokens(content)
            groupBySLT = {}
            for idx, tree in enumerate(trees):
                #print("Parsing doc %s, expr %i" % (content_id,idx),flush=True)
                pmml = cls.isolate_pmml(tree)
                symbol_tree = cls.convert_to_mathsymbol(pmml)
                if symbol_tree:
                    s = symbol_tree.tostring()
                    if s not in groupBySLT:
                        groupBySLT[s] = SymbolTree(symbol_tree,content_id,[idx])
                    else:
                        groupBySLT[s].position.append(idx)
            return(list(groupBySLT.values()))
        
        except UnknownTagException as e:
            print("Unknown tag in file or query "+str(content_id)+": "+e.tag, file=sys.stderr)
            missing_tags[e.tag] = missing_tags.get(e.tag, set())
            missing_tags[e.tag].add([content_id,idx])
        except Exception as err:
            reason = str(err)
            print("Parse error in file or query "+str(content_id)+": "+reason+": "+str(tree), file=sys.stderr)
            raise Exception(reason) # pass on the exception to identify the document or query
