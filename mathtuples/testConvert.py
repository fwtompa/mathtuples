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
    Modified by Frank Tompa, 20expand21
    Packaged with mathtuples. Contact:
        - Frank Tompa, fwtompa@uwaterloo.ca
"""
'''
Name: Dallas Fraser
Date: 2017-08-25
Project: Tangent
Purpose: To test the conversion of mathml to Tangent Tuples
'''
import unittest
import os
WINDOWS = "nt"
ROOTPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from mathtuples.convert import convert_math_expression,\
                                check_wildcard, make_wild,\
                                determine_node,\
                                expand_nodes_with_location,\
                                expand_node_with_wildcards,\
                                EDGE_PAIR_NODE, COMPOUND_NODE, \
                                EOL_NODE, TERMINAL_NODE, SYMBOL_PAIR_NODE,\
                                DUPLICATE_NODE, LONG_NODE, ABBREVIATED_NODE,\
                                WILDCARD_MOCK, START_TAG, END_TAG,\
                                INFINITE_DEPTH, MAX_EOL_HEIGHT, MAX_DUP
    from mathtuples.mathsymbol import REP_TAG
except ImportError:
    from convert import convert_math_expression,\
                                check_wildcard, make_wild,\
                                determine_node,\
                                expand_nodes_with_location,\
                                expand_node_with_wildcards,\
                                EDGE_PAIR_NODE, COMPOUND_NODE, \
                                EOL_NODE, TERMINAL_NODE, SYMBOL_PAIR_NODE,\
                                DUPLICATE_NODE, LONG_NODE, ABBREVIATED_NODE,\
                                WILDCARD_MOCK, START_TAG, END_TAG,\
                                INFINITE_DEPTH, MAX_EOL_HEIGHT, MAX_DUP
    from mathsymbol import REP_TAG


def convert_test(mathml,
               synonyms=False,
               dups="",
               wild_dups="",
               window_size=1,
               loc_info={SYMBOL_PAIR_NODE: 1},
               anchors=[]):
    """Use 1 as default value for symbol_pairs and use 0 
       as default value for other fields regardless of actual (optimal) defaults
    """
    return convert_math_expression("test",1,mathml,
               synonyms=synonyms,
               dups=dups,
               wild_dups=wild_dups,
               window_size=window_size,
               loc_info=loc_info,
               anchors=anchors)
class TestBase(unittest.TestCase):
    def loadFile(self, math_file):
        if os.name == WINDOWS:
            with open(math_file, encoding="utf8") as f:
                lines = []
                for line in f:
                    lines.append(line)
        else:
            with open(math_file) as f:
                lines = []
                for line in f:
                    lines.append(line)
        return " ".join(lines)

    def log(self, out):
        if self.debug:
            print(out)


class TestPmmlExtraction(TestBase):
    def setUp(self):
        self.debug = True
        self.mathml1 = """
<m:math>
  <m:semantics xml:id="m1.1a">
    <m:apply xml:id="m1.1.4" xref="m1.1.4.pmml">
      <m:plus xml:id="m1.1.2" xref="m1.1.2.pmml"/>
      <m:ci xml:id="m1.1.1" xref="m1.1.1.pmml">x</m:ci>
      <mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="y"/>
    </m:apply>
    <m:annotation-xml encoding="MathML-Presentation" xml:id="m1.1b">
      <m:mrow xml:id="m1.1.4.pmml" xref="m1.1.4">
        <m:mi xml:id="m1.1.1.pmml" xref="m1.1.1">x</m:mi>
        <m:mo xml:id="m1.1.2.pmml" xref="m1.1.2">+</m:mo>
        <mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="y"/>
      </m:mrow>
    </m:annotation-xml>
    <m:annotation encoding="application/x-tex" xml:id="m1.1c">
        x+\qvar@construct{y}
    </m:annotation>
  </m:semantics>
</m:math>
                      """
        self.mathml2 = """
<m:math>
  <m:semantics xml:id="m1.1a">
    <m:mrow xml:id="m1.1.4.pmml" xref="m1.1.4">
      <m:mi xml:id="m1.1.1.pmml" xref="m1.1.1">x</m:mi>
      <m:mo xml:id="m1.1.2.pmml" xref="m1.1.2">+</m:mo>
      <mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="y"/>
    </m:mrow>
    <m:annotation-xml encoding="MathML-Content" xml:id="m1.1b">
      <m:apply xml:id="m1.1.4" xref="m1.1.4.pmml">
        <m:plus xml:id="m1.1.2" xref="m1.1.2.pmml"/>
        <m:ci xml:id="m1.1.1" xref="m1.1.1.pmml">x</m:ci>
        <mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="y"/>
      </m:apply>
    </m:annotation-xml>
    <m:annotation encoding="application/x-tex" xml:id="m1.1c">
        x+\qvar@construct{y}
    </m:annotation>
  </m:semantics>
</m:math>
                      """
        self.expect = [START_TAG,
                  """#(v!x,+,n)#""",
                  """#(v!x,+,n,-)#""",
                  """#(?v,+,n)#""",
                  """#(?v,+,n,-)#""",
                  """#(v!x,?o,n)#""",
                  """#(v!x,?o,n,-)#""",
                  """#(v!x,*,nn)#""",
                  """#(v!x,*,nn,-)#""",
                  """#(+,*,n)#""",
                  """#(+,*,n,n)#""",
                  END_TAG]

    def testPmmlMain(self):
        results = convert_test(self.mathml1,
                               loc_info = {SYMBOL_PAIR_NODE: 99,
                                           TERMINAL_NODE: 99,
                                           LONG_NODE: 99},
                               synonyms = True)
        self.assertEqual(" ".join(self.expect), results)

    def testPmmlNested(self):
        results = convert_test(self.mathml2,
                               loc_info = {SYMBOL_PAIR_NODE: 99,
                                           TERMINAL_NODE: 99,
                                           LONG_NODE: 99},
                               synonyms = True)
        self.assertEqual(" ".join(self.expect), results)


class TestSymbolPairs(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_1.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testConvert(self):
        results = convert_test(self.mathml, loc_info={})
        expect = [START_TAG,
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertNotFalse(self):
        results = convert_test(self.mathml,
                               loc_info = {EOL_NODE: 1})
        expect = [START_TAG,
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertEdgePairs(self):
        file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        mathml = self.loadFile(file)
        results = convert_test(mathml,
                              loc_info = {EDGE_PAIR_NODE: 1})
        expect = [START_TAG,
                  """#(n,a,v!k)#""",
                  """#(n,n,/)#""",
                  """#(n,n,n!2)#""",
                  """#(n,a,n!2)#""",
                  """#(n,n,gt)#""",
                  """#(w,e,n!2)#""",
                  """#(n,n,m!()1x2)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)


class TestExpandLocation(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_2.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testExpandLocation(self):
        file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        mathml = self.loadFile(file)
        results = convert_test(mathml,
                               loc_info = {SYMBOL_PAIR_NODE: 99})
        expect = [START_TAG,
                  """#(v!w,m!()1x2,n)#""",
                  """#(v!w,m!()1x2,n,-)#""",
                  """#(m!()1x2,gt,n)#""",
                  """#(m!()1x2,gt,n,n)#""",
                  """#(gt,n!2,n)#""",
                  """#(gt,n!2,n,nn)#""",
                  """#(n!2,/,n)#""",
                  """#(n!2,/,n,nnn)#""",
                  """#(/,v!k,n)#""",
                  """#(/,v!k,n,nnnn)#""",
                  """#(v!k,v!ε,a)#""",
                  """#(v!k,v!ε,a,nnnnn)#""",
                  """#(n!2,v!k,a)#""",
                  """#(n!2,v!k,a,nnn)#""",
                  """#(m!()1x2,n!2,w)#""",
                  """#(m!()1x2,n!2,w,n)#""",
                  """#(n!2,v!k,e)#""",
                  """#(n!2,v!k,e,nw)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testExpandLocation2(self):
        nodes_list = [('m!()1x1', '?w', 'n', "-")]
        result = expand_nodes_with_location(nodes_list,{SYMBOL_PAIR_NODE: 99})
        expect = [('m!()1x1', '?w', 'n'),
                  ('m!()1x1', '?w', 'n', '-')]
        self.assertEqual(expect, result)

    def testAnchors(self):
        results = convert_test(self.mathml,
                               loc_info = {SYMBOL_PAIR_NODE: 99, TERMINAL_NODE: 99, DUPLICATE_NODE: 99},
                               anchors = ["=","?"], wild_dups = "W")
        expect = [START_TAG,
                  """#(v!π,=,n)#""",
                  """#(v!π,=,n,-)#""",
                  """#(=,v!a,n)#""",
                  """#(=,v!a,n,n)#""",
                  """#(v!a,m!()1x1,n)#""",
                  """#(v!a,m!()1x1,n,-)#""",
                  """#(m!()1x1,*,w)#""",
                  """#(m!()1x1,*,w,n)#""",
                  """#(*,+,n)#""",
                  """#(*,+,n,nw)#""",
                  """#(+,v!c,n)#""",
                  """#(+,v!c,n,nwn)#""",
                  """#(v!c,!0)#""",
                  """#(v!c,!0,nwnn)#""",
                  """#(v!π,*,a)#""",
                  """#(v!π,*,a,-)#""",
                  """#{*,nw,a}#""",
                  """#{*,nw,a,-}#""",
                  """#(v!π,*,b)#""",
                  """#(v!π,*,b,-)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testExpandLocationLimited(self):
        file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        mathml = self.loadFile(file)
        results = convert_test(mathml,
                               loc_info = {SYMBOL_PAIR_NODE: 3})
        expect = [START_TAG,
                  """#(v!w,m!()1x2,n)#""",
                  """#(v!w,m!()1x2,n,-)#""",
                  """#(m!()1x2,gt,n)#""",
                  """#(m!()1x2,gt,n,n)#""",
                  """#(gt,n!2,n)#""",
                  """#(n!2,/,n)#""",
                  """#(/,v!k,n)#""",
                  """#(v!k,v!ε,a)#""",
                  """#(n!2,v!k,a)#""",
                  """#(m!()1x2,n!2,w)#""",
                  """#(m!()1x2,n!2,w,n)#""",
                  """#(n!2,v!k,e)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)


class TestWildcards(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_2.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testConvertEOL(self):
        results = convert_test(self.mathml,
                               loc_info = {TERMINAL_NODE: 99})
        expect = [START_TAG,
                  """#(v!c,!0)#""",
                  """#(v!c,!0,3n1w2n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertStandard(self):
        results = convert_test(self.mathml,
                               loc_info = {SYMBOL_PAIR_NODE: 1,
                                           COMPOUND_NODE: 1,
                                           TERMINAL_NODE: 1})
        expect = [START_TAG,
                  """#(v!π,[n,a,b])#""",
                  """#(v!π,=,n)#""",
                  """#(=,v!a,n)#""",
                  """#(v!a,m!()1x1,n)#""",
                  """#(m!()1x1,*,w)#""",
                  """#(*,+,n)#""",
                  """#(+,v!c,n)#""",
                  """#(v!c,!0)#""",
                  """#(v!π,*,a)#""",
                  """#(v!π,*,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)


class TestDetermineNode(TestBase):
    def setUp(self):
        self.debug = True

    def tearDown(self):
        pass

    def testDetermineNode(self):
        self.assertEqual(determine_node(('M!()1x1', '?W', 'n', "-")),
                         SYMBOL_PAIR_NODE)
        self.assertEqual(determine_node(('M!()1x1', '?W', "-")),
                         LONG_NODE)
        self.assertEqual(determine_node(('N!0', '!0', "-")),
                         TERMINAL_NODE)
        self.assertEqual(determine_node(('N!0', '!0', "n", "-")),
                         EOL_NODE)
        self.assertEqual(determine_node(('v!α', "[n,b]", "-")),
                         COMPOUND_NODE)
        self.assertEqual(determine_node(('n', 'b', 'V!y', "-")),
                         EDGE_PAIR_NODE)
        self.assertEqual(determine_node(('n', 'n', 'V!y', "-")),
                         EDGE_PAIR_NODE)
        self.assertEqual(determine_node((REP_TAG, 'V!y', 'nn')),
                         DUPLICATE_NODE)
        self.assertEqual(determine_node((REP_TAG, 'V!y', 'nn', 'a')),
                         DUPLICATE_NODE)
        self.assertEqual(determine_node((REP_TAG, 'V!y', 'nn', 'a', 'nnn')),
                         DUPLICATE_NODE)


class TestSynonym(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_1.xml")
        self.mathml = self.loadFile(self.file)
        self.file2 = os.path.join(ROOTPATH, "testFiles", "test_2.xml")
        self.mathml2 = self.loadFile(self.file2)

    def tearDown(self):
        pass

    def testExpandNodeWithWildcards(self):
        # symbol pair with wildcard
        expect = [('M!()1x1', WILDCARD_MOCK,'n', '-')]
        result = expand_node_with_wildcards(('M!()1x1', '?a', 'n', '-'),"","",True)
        self.log(result)
        self.assertEqual(expect, result)

        # normal symbol pair
        expect = [('M!()1x1', 'N!1', 'n', "-"),
                  ('??M', 'N!1', 'n', "-"),
                  ('M!()1x1', '??N', 'n', "-"),
                  ]
        result = expand_node_with_wildcards(('M!()1x1', 'N!1', 'n', "-"),"","",True)
        self.log(result)
        self.assertEqual(expect, result)

        # normal symbol pair
        expect = [('M!()1x1', 'N!1', 'n', "-"),
                  ('??M', 'N!1', 'n', "-"),
                  ('M!()1x1', '??N', 'n', "-"),
                  ]
        result = expand_node_with_wildcards(('M!()1x1', 'N!1', 'n', "-"),"","",True)
        self.log(result)
        self.assertEqual(expect, result)

        # terminal symbol
        result = expand_node_with_wildcards(('N!0', '!0', "-"),"","",True)
        self.log(result)
        expect = [('N!0', '!0', "-")]
        self.assertEqual(expect, result)

        # eol symbol
        result = expand_node_with_wildcards(('N!0', '!0', "n", "-"),"","",True)
        expect = [('N!0', '!0', "n", "-")]
        self.log(result)
        self.assertEqual(expect, result)

        # compound symbol
        expect = [('V!α', "[n,b]", "-"),
                  ('??V', "[n,b]", "-")]
        result = expand_node_with_wildcards(('V!α', "[n,b]", "-"),"","",True)
        self.log(result)
        self.assertEqual(expect, result)

        # repetition node
        expect = [(REP_TAG, '??V', 'nn', 'a')]
        result = expand_node_with_wildcards((REP_TAG, 'V!y', 'nn', 'a'),"","",True)
        self.log(result)
        self.assertEqual(expect, result)

        # repetition node
        expect = [(REP_TAG, '??V', 'nn', 'a')]
        result = expand_node_with_wildcards((REP_TAG, 'V!y', 'nn', 'a'),"","V",False)
        self.log(result)
        self.assertEqual(expect, result)

        # repetition node
        expect = [(REP_TAG, 'V!y', 'nn', 'a')]
        result = expand_node_with_wildcards((REP_TAG, 'V!y', 'nn', 'a'),"V","",False)
        self.log(result)
        self.assertEqual(expect, result)

        # repetition node
        expect = [(REP_TAG, 'V!y', 'nn', 'a'),
                  (REP_TAG, '??V', 'nn', 'a')]
        result = expand_node_with_wildcards((REP_TAG, 'V!y', 'nn', 'a'),"V","V",False)
        self.log(result)
        self.assertEqual(expect, result)

    def testConvertWithSynonyms(self):
        results = convert_test(self.mathml,
                               loc_info = {SYMBOL_PAIR_NODE: 1,
                                           COMPOUND_NODE: 1,
                                           EDGE_PAIR_NODE: 1,
                                           TERMINAL_NODE: 1,
                                           EOL_NODE: 1},
                               synonyms=True)
        expect = [START_TAG,
                  """#(*,[n,b])#""",
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  """#(?o,n!1,n)#""",
                  """#(ast,?n,n)#""",
                  """#(n!1,!0)#""",
                  """#(n,n,ast)#""",
                  """#(n,n,?o)#""",
                  """#(b,n,*)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

        # test the other file
        results = convert_test(self.mathml2,
                               loc_info = {SYMBOL_PAIR_NODE: 1,
                                           COMPOUND_NODE: 1,
                                           EDGE_PAIR_NODE: 1,
                                           TERMINAL_NODE: 1,
                                           EOL_NODE: 1},
                               synonyms=True)
        expect = [START_TAG,
                  """#(v!α,[n,b])#""",
                  """#(?v,[n,b])#""",
                  """#(v!α,m!()1x1,n)#""",
                  """#(?v,m!()1x1,n)#""",
                  """#(v!α,?m,n)#""",
                  """#(m!()1x1,[n,w])#""",
                  """#(?m,[n,w])#""",
                  """#(m!()1x1,=,n)#""",
                  """#(?m,=,n)#""",
                  """#(m!()1x1,?o,n)#""",
                  """#(=,v!y,n)#""",
                  """#(?o,v!y,n)#""",
                  """#(=,?v,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(?v,n!0,b)#""",
                  """#(v!y,?n,b)#""",
                  """#(n!0,!0)#""",
                  """#(n,b,v!y)#""",
                  """#(n,b,?v)#""",
                  """#(n,n,=)#""",
                  """#(n,n,?o)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(?m,v!x,w)#""",
                  """#(m!()1x1,?v,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(?v,n!0,b)#""",
                  """#(v!x,?n,b)#""",
                  """#(n!0,!0)#""",
                  """#(w,b,v!x)#""",
                  """#(w,b,?v)#""",
                  """#(n,n,m!()1x1)#""",
                  """#(n,n,?m)#""",
                  """#(v!α,n!0,b)#""",
                  """#(?v,n!0,b)#""",
                  """#(v!α,?n,b)#""",
                  """#(n!0,!0)#""",
                  END_TAG]
        self.log(results)
        self.maxDiff = None
        self.assertEqual(" ".join(expect), results)


class TestWildcardReductionAndCheck(TestBase):
    def setUp(self):
        self.debug = True

    def tearDown(self):
        pass

    def testCheckWildcard(self):
        self.assertEqual(check_wildcard("?V"), True)
        self.assertEqual(check_wildcard("N!6"), False)
        self.assertEqual(check_wildcard("V!x"), False)

class TestRepetitions(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_repetitions.xml")
        self.mathml = self.loadFile(self.file)
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_2.xml")
        self.mathml2 = self.loadFile(self.file)
        self.file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        self.mathml3 = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testRepetitions(self):
        results = convert_test(self.mathml,loc_info={DUPLICATE_NODE: 1},
                               dups="VNOMFRTW")
        expect = [START_TAG,
                  """#{n!2,ob,ub}#""",
                  """#{v!b,no,o}#""",
                  """#{!,nun,un}#""",
                  """#{n!1,ob,ub}#""",
                  """#{v!a,nu,u}#""",
                  """#{f!,n}#""",
                  """#{!,nun}#""",
                  """#{v!a,nnu}#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

        results = convert_test(self.mathml,loc_info={DUPLICATE_NODE: 99},
                               dups="VN", wild_dups="VF")
        expect = [START_TAG,
                  """#{n!2,ob,ub}#""",
                  """#{n!2,ob,ub,nnn}#""",
                  """#{v!b,no,o}#""",
                  """#{v!b,no,o,nn}#""",
                  """#{?v,no,o}#""",
                  """#{?v,no,o,nn}#""",
                  """#{n!1,ob,ub}#""",
                  """#{n!1,ob,ub,nn}#""",
                  """#{v!a,nu,u}#""",
                  """#{v!a,nu,u,nn}#""",
                  """#{?v,nu,u}#""",
                  """#{?v,nu,u,nn}#""",
                  """#{?f,n}#""",
                  """#{?f,n,nn}#""",
                  """#{v!a,nnu}#""",
                  """#{v!a,nnu,-}#""",
                  """#{?v,nnu}#""",
                  """#{?v,nnu,-}#""",
                  END_TAG]
        self.log(results)
        self.maxDiff = None
        self.assertEqual(" ".join(expect), results)

    def testRepeatedWildCards(self):
        results = convert_test(self.mathml2,
                               loc_info={SYMBOL_PAIR_NODE: 1,
                                         DUPLICATE_NODE: 1},
                               wild_dups="W")
        expect = [START_TAG,
                  """#(v!π,=,n)#""",
                  """#(=,v!a,n)#""",
                  """#(v!a,m!()1x1,n)#""",
                  """#(m!()1x1,*,w)#""",
                  """#(*,+,n)#""",
                  """#(+,v!c,n)#""",
                  """#(v!π,*,a)#""",
                  """#{*,nnnw,a}#""", 
                  """#(v!π,*,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testRepeatedSymbolSynonyms(self):
        results = convert_test(self.mathml3,
                               loc_info={DUPLICATE_NODE: 1},
                               dups="VN",
                               wild_dups="VN",
                               synonyms=True)
        expect = [START_TAG,
                  """#{v!k,nn,a}#""",
                  """#{?v,nn,a}#""",
                  """#{v!k,nna,we}#""",
                  """#{?v,nna,we}#""",
                  """#{n!2,nn,w}#""",
                  """#{?n,nn,w}#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

class TestTerminalQuery(TestBase):
    def setUp(self):
        self.debug = True
        self.f1 = os.path.join(ROOTPATH, 
                               "testFiles",
                               "test_terminal_small_1.xml")
        self.f2 = os.path.join(ROOTPATH, 
                               "testFiles",
                               "test_terminal_small_2.xml")

    def testF1(self):
        self.mathml = self.loadFile(self.f1)
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        TERMINAL_NODE: 1})
        self.log(results)
        expect = [START_TAG,
                  """#(v!𝖿𝗏,!0)#""",
                  END_TAG]
        self.assertEqual(results, " ".join(expect))

    def testF2(self):
        self.mathml = self.loadFile(self.f2)
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        TERMINAL_NODE: 1})
        self.log(results)
        expect = [START_TAG,
                  """#(v!𝒔,!0)#""",
                  END_TAG]
        self.assertEqual(results, " ".join(expect))


class TestMatrix(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "Arith_cases.html")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testBase(self):
        results = convert_test(self.mathml,loc_info = {SYMBOL_PAIR_NODE: 1,
                                                       TERMINAL_NODE: 1,
                                                       COMPOUND_NODE: 1})
        expect = [START_TAG,
                  """#(v!χ,m!()1x1,n)#""",
                  """#(m!()1x1,[n,w])#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,m!()1x1,n)#""",
                  """#(m!()1x1,[n,w])#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,m!{3x2,n)#""",
                  """#(m!{3x2,n!0,w)#""",
                  """#(n!0,t!if,e)#""",
                  """#(t!if,[n,e])#""",
                  """#(t!if,v!n,n)#""",
                  """#(v!n,t!is␣even,n)#""",
                  """#(t!is␣even,!0)#""",
                  """#(t!if,n!1,e)#""",
                  """#(n!1,t!if,e)#""",
                  """#(t!if,[n,e])#""",
                  """#(t!if,v!n,n)#""",
                  """#(v!n,≡,n)#""",
                  """#(≡,n!1,n)#""",
                  """#(n!1,mod,n)#""",
                  """#(mod,n!4,n)#""",
                  """#(n!4,!0)#""",
                  """#(t!if,n!-1,e)#""",
                  """#(n!-1,t!if,e)#""",
                  """#(t!if,v!n,n)#""",
                  """#(v!n,≡,n)#""",
                  """#(≡,n!3,n)#""",
                  """#(n!3,mod,n)#""",
                  """#(mod,n!4,n)#""",
                  """#(n!4,!0)#""",
                  """#(m!()1x1,f!,w)#""",
                  """#(f!,[o,u])#""",
                  """#(f!,n!-4,o)#""",
                  """#(n!-4,!0)#""",
                  """#(f!,v!n,u)#""",
                  """#(v!n,!0)#""",
                  """#(m!()1x1,v!n,w)#""",
                  """#(v!n,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

class TestArxivQuery(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_1.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testBase(self):
        results = convert_test(self.mathml)
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testWindowSize(self):
        results = convert_test(self.mathml, window_size=2)
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(*,n!1,nn)#""",
                  """#(ast,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEOL(self):
        # height too big
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        EOL_NODE: 1})
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testCompoundSymbols(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        COMPOUND_NODE: 1})
        expect = [START_TAG,
                  """#(*,[n,b])#""",
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testTerminalSymbols(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        TERMINAL_NODE: 1})
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  """#(n!1,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEdgePairs(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        EDGE_PAIR_NODE: 1})
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(ast,n!1,n)#""",
                  """#(n,n,ast)#""",
                  """#(b,n,*)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testUnbounded(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        LONG_NODE: 1})
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(*,n!1,nn)#""",
                  """#(ast,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testLocation(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 99})
        expect = [START_TAG,
                  """#(*,ast,n)#""",
                  """#(*,ast,n,-)#""",
                  """#(ast,n!1,n)#""",
                  """#(ast,n!1,n,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)


class TestRandomEquation(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_2.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testBase(self):
        results = convert_test(self.mathml)
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testWindowSize(self):
        results = convert_test(self.mathml, window_size=2)
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(v!α,v!x,nw)#""",
                  """#(v!α,=,nn)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(m!()1x1,v!y,nn)#""",
                  """#(=,v!y,n)#""",
                  """#(=,n!0,nb)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(m!()1x1,n!0,wb)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEOL(self):
        # height too big
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        EOL_NODE: 1})
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testCompoundSymbols(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        COMPOUND_NODE: 1})
        expect = [START_TAG,
                  """#(v!α,[n,b])#""",
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,[n,w])#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testTerminalSymbols(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        TERMINAL_NODE: 1})
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(n!0,!0)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(n!0,!0)#""",
                  """#(v!α,n!0,b)#""",
                  """#(n!0,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEdgePairs(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        EDGE_PAIR_NODE: 1})
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(n,b,v!y)#""",
                  """#(n,n,=)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(w,b,v!x)#""",
                  """#(n,n,m!()1x1)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testUnbounded(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 1,
                                                        LONG_NODE: 1})
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(v!α,v!x,nw)#""",
                  """#(v!α,n!0,nb)#""",
                  """#(v!α,=,nn)#""",
                  """#(v!α,v!y,nn)#""",
                  """#(v!α,n!0,nb)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(m!()1x1,v!y,nn)#""",
                  """#(m!()1x1,n!0,nb)#""",
                  """#(=,v!y,n)#""",
                  """#(=,n!0,nb)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(m!()1x1,n!0,wb)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testLocation(self):
        results = convert_test(self.mathml, loc_info = {SYMBOL_PAIR_NODE: 99})
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n)#""",
                  """#(v!α,m!()1x1,n,-)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(m!()1x1,=,n,n)#""",
                  """#(=,v!y,n)#""",
                  """#(=,v!y,n,nn)#""",
                  """#(v!y,n!0,b)#""",
                  """#(v!y,n!0,b,nnn)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(m!()1x1,v!x,w,n)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!x,n!0,b,nw)#""",
                  """#(v!α,n!0,b)#""",
                  """#(v!α,n!0,b,-)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
