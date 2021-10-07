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
Purpose: To test the conversion of mathml to Tangent Tuples
'''
import unittest
import os
WINDOWS = "nt"
ROOTPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from mathtuples.convert import convert_math_expression,\
                                check_node,\
                                check_wildcard,\
                                determine_node,\
                                expand_nodes_with_location,\
                                expand_node_with_wildcards,\
                                EDGE_PAIR_NODE, COMPOUND_NODE, \
                                EOL_NODE, TERMINAL_NODE, SYMBOL_PAIR_NODE,\
                                WILDCARD_MOCK, START_TAG, END_TAG,\
                                REPETITION_NODE
    from mathtuples.mathsymbol import REP_TAG
except ImportError:
    from convert import convert_math_expression,\
                                check_node,\
                                check_wildcard,\
                                determine_node,\
                                expand_nodes_with_location,\
                                expand_node_with_wildcards,\
                                EDGE_PAIR_NODE, COMPOUND_NODE, \
                                EOL_NODE, TERMINAL_NODE, SYMBOL_PAIR_NODE,\
                                WILDCARD_MOCK, START_TAG, END_TAG,\
                                REPETITION_NODE
    from mathsymbol import REP_TAG


def convert_test(mathml,
                            window_size=1,
                            symbol_pairs=True,
                            terminal_symbols=False,
                            compound_symbols=False,
                            location=False,
                            eol=False,
                            edge_pairs=False,
                            unbounded=False,
                            shortened=False,
                            repetitions=False,
                            synonyms=False):
    """Use True as default value for symbol_pairs and use False 
       as default value for all fields regardless of actual (optimal) defaults
    """
    return convert_math_expression(mathml,
                            window_size=window_size,
                            symbol_pairs=symbol_pairs,
                            terminal_symbols=terminal_symbols,
                            compound_symbols=compound_symbols,
                            location=location,
                            eol=eol,
                            edge_pairs=edge_pairs,
                            unbounded=unbounded,
                            shortened=shortened,
                            repetitions=repetitions,
                            synonyms=synonyms)

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
                  """#(v!x,+,n,-)#""",
                  """#(v!x,+,n)#""",
                  """#(*,+,n,-)#""",
                  """#(*,+,n)#""",
                  """#(v!x,*,n,-)#""",
                  """#(v!x,*,n)#""",
                  """#(v!x,*,nn,-)#""",
                  """#(v!x,*,nn)#""",
                  """#(+,*,n,n)#""",
                  """#(+,*,n)#""",
                  END_TAG]

    def testPmmlMain(self):
        results = convert_test(self.mathml1,
                                          terminal_symbols=True,
                                          location=True,
                                          unbounded=True,
                                          synonyms=True)
        self.assertEqual(" ".join(self.expect), results)

    def testPmmlNested(self):
        results = convert_test(self.mathml2,
                                          terminal_symbols=True,
                                          location=True,
                                          unbounded=True,
                                          synonyms=True)
        self.assertEqual(" ".join(self.expect), results)


class TestSymbolPairs(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_1.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testConvert(self):
        results = convert_test(self.mathml, symbol_pairs=False)
        expect = [START_TAG,
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertNotFalse(self):
        results = convert_test(self.mathml,
                                          symbol_pairs=False,
                                          eol=True)
        expect = [START_TAG,
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertEdgePairs(self):
        file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        mathml = self.loadFile(file)
        results = convert_test(mathml,
                                          symbol_pairs=False,
                                          edge_pairs=True)
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
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_1.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testExpandLocation(self):
        file = os.path.join(ROOTPATH, "testFiles", "test_edge_pair.xml")
        mathml = self.loadFile(file)
        results = convert_test(mathml,
                                          location=True)
        expect = [START_TAG,
                  """#(v!w,m!()1x2,n,-)#""",
                  """#(v!w,m!()1x2,n)#""",
                  """#(m!()1x2,gt,n,n)#""",
                  """#(m!()1x2,gt,n)#""",
                  """#(gt,n!2,n,nn)#""",
                  """#(gt,n!2,n)#""",
                  """#(n!2,/,n,nnn)#""",
                  """#(n!2,/,n)#""",
                  """#(/,v!k,n,nnnn)#""",
                  """#(/,v!k,n)#""",
                  """#(v!k,v!ε,a,nnnnn)#""",
                  """#(v!k,v!ε,a)#""",
                  """#(n!2,v!k,a,nnn)#""",
                  """#(n!2,v!k,a)#""",
                  """#(m!()1x2,n!2,w,n)#""",
                  """#(m!()1x2,n!2,w)#""",
                  """#(n!2,v!k,e,nw)#""",
                  """#(n!2,v!k,e)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testExpandLocation2(self):
        nodes_list = [('m!()1x1', '?w', 'n', "-")]
        result = expand_nodes_with_location(nodes_list)
        self.assertEqual(len(result), 2)
        expect = [('m!()1x1', '?w', 'n', '-'),
                  ('m!()1x1', '?w', 'n')]
        self.assertEqual(result, expect)


class TestWildcards(TestBase):
    def setUp(self):
        self.debug = True
        self.file = os.path.join(ROOTPATH, "testFiles", "test_wildcard_2.xml")
        self.mathml = self.loadFile(self.file)

    def tearDown(self):
        pass

    def testConvertEOL(self):
        results = convert_test(self.mathml, terminal_symbols=True,location=True,symbol_pairs=False)
        expect = [START_TAG,
                  """#(v!c,!0,3n1w2n)#""",
                  """#(v!c,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testConvertStandard(self):
        results = convert_test(self.mathml,
                                          terminal_symbols=True,
                                          compound_symbols=True)
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
        self.assertEqual(determine_node(('m!()1x1', '?w', 'n', "-")),
                         SYMBOL_PAIR_NODE)
        self.assertEqual(determine_node(('m!()1x1', '?w', "-")),
                         SYMBOL_PAIR_NODE)
        self.assertEqual(determine_node(('n!0', '!0', "-")),
                         TERMINAL_NODE)
        self.assertEqual(determine_node(('n!0', '!0', "n", "-")),
                         EOL_NODE)
        self.assertEqual(determine_node(('v!α', "[n,b]", "-")),
                         COMPOUND_NODE)
        self.assertEqual(determine_node(('n', 'b', 'v!y', "-")),
                         EDGE_PAIR_NODE)
        self.assertEqual(determine_node(('n', 'n', 'v!y', "-")),
                         EDGE_PAIR_NODE)
        self.assertEqual(determine_node((REP_TAG, 'v!y', 'nn')),
                         REPETITION_NODE)
        self.assertEqual(determine_node((REP_TAG, 'v!y', 'nn', 'a')),
                         REPETITION_NODE)
        self.assertEqual(determine_node((REP_TAG, 'v!y', 'nn', 'a', 'nnn')),
                         REPETITION_NODE)


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
        expect = [('m!()1x1', '?w', 'n')]
        result = expand_node_with_wildcards(('m!()1x1', '?w', 'n'))
        self.log(result)
        self.assertEqual(result, expect)

        # normal symbol pair
        expect = [('m!()1x1', 'n!1', 'n', "-"),
                  (WILDCARD_MOCK, 'n!1', 'n', "-"),
                  ('m!()1x1', WILDCARD_MOCK, 'n', "-"),
                  ]
        result = expand_node_with_wildcards(('m!()1x1', 'n!1', 'n', "-"))
        self.log(result)
        self.assertEqual(result, expect)

        # terminal symbol
        result = expand_node_with_wildcards(('n!0', '!0', "-"))
        self.log(result)
        expect = [('n!0', '!0', "-")]
        self.assertEqual(result, expect)

        # eol symbol
        result = expand_node_with_wildcards(('n!0', '!0', "n", "-"))
        expect = [('n!0', '!0', "n", "-")]
        self.log(result)
        self.assertEqual(result, expect)

        # compound symbol
        expect = [('v!α', "[n,b]", "-"),
                  (WILDCARD_MOCK, "[n,b]", "-")]
        result = expand_node_with_wildcards(('v!α', "[n,b]", "-"))
        self.log(result)
        self.assertEqual(result, expect)

    def testConvertWithSynonyms(self):
        results = convert_test(self.mathml,
                                          compound_symbols=True,
                                          edge_pairs=True,
                                          terminal_symbols=True,
                                          eol=True,
                                          synonyms=True)
        expect = [START_TAG,
                  """#(*,[n,b])#""",
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  """#(*,n!1,n)#""",
                  """#(=,*,n)#""",
                  """#(n!1,!0)#""",
                  """#(n,n,=)#""",
                  """#(n,n,*)#""",
                  """#(b,n,*)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

        # test the other file
        results = convert_test(self.mathml2,
                                          compound_symbols=True,
                                          edge_pairs=True,
                                          terminal_symbols=True,
                                          eol=True,
                                          synonyms=True)
        expect = [START_TAG,
                  """#(v!α,[n,b])#""",
                  """#(*,[n,b])#""",
                  """#(v!α,m!()1x1,n)#""",
                  """#(*,m!()1x1,n)#""",
                  """#(v!α,*,n)#""",
                  """#(m!()1x1,[n,w])#""",
                  """#(*,[n,w])#""",
                  """#(m!()1x1,=,n)#""",
                  """#(*,=,n)#""",
                  """#(m!()1x1,*,n)#""",
                  """#(=,v!y,n)#""",
                  """#(*,v!y,n)#""",
                  """#(=,*,n)#""",
                  """#(v!y,n!0,b)#""",
                  """#(*,n!0,b)#""",
                  """#(v!y,*,b)#""",
                  """#(n!0,!0)#""",
                  """#(n,b,v!y)#""",
                  """#(n,b,*)#""",
                  """#(n,n,=)#""",
                  """#(n,n,*)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(*,v!x,w)#""",
                  """#(m!()1x1,*,w)#""",
                  """#(v!x,n!0,b)#""",
                  """#(*,n!0,b)#""",
                  """#(v!x,*,b)#""",
                  """#(n!0,!0)#""",
                  """#(w,b,v!x)#""",
                  """#(w,b,*)#""",
                  """#(n,n,m!()1x1)#""",
                  """#(n,n,*)#""",
                  """#(v!α,n!0,b)#""",
                  """#(*,n!0,b)#""",
                  """#(v!α,*,b)#""",
                  """#(n!0,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)


class TestWildcardReductionAndCheck(TestBase):
    def setUp(self):
        self.debug = True

    def tearDown(self):
        pass

    def testCheckNode(self):
        valid_nodes = [('?w', 'm!()1x1', 'n', '-'),
                       ('m!()1x1', '?w', 'n', '-'),
                       ('=', 'v!y', 'n', '-'),
                       ('v!y', 'n!0', 'b', '-'),
                       ('m!()1x1', 'v!x', 'w', '-'),
                       ('v!x', 'n!0', 'b', '-'),
                       ('v!Î±', 'n!0', 'b', '-'),
                       ('v!Î±', "['n','b']", '-'),
                       ('m!()1x1', "['n','w']", '-'),
                       ('n!0', '!0', '-'),
                       ('n', 'b', '?w', '-'),
                       ('n', 'n', '=', '-'),
                       ('w', 'b', 'v!x', '-'),
                       ('n', 'n', 'm!()1x1', '-'),
                       ('n', 'w', 'm!()1x1', '-')]
        invalid_nodes = [('?v', '!0', '-'),
                         ('?w', '?w', 'b', '-'),
                         ("?w", "?w", "b", "nn", '-'),
                         ("?w", "!0", "n", '-')]
        for node in valid_nodes:
            self.assertEqual(check_node(node), True)
        for node in invalid_nodes:
            self.assertEqual(check_node(node), False)

    def testCheckWildcard(self):
        self.assertEqual(check_wildcard("?v"), True)
        self.assertEqual(check_wildcard("n!6"), False)
        self.assertEqual(check_wildcard("v!x"), False)

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
        results = convert_test(self.mathml,repetitions=True,symbol_pairs=False,location=True)
        expect = [START_TAG,
                  """#{n!2,ob,ub,nnn}#""",
                  """#{n!2,ob,ub}#""",
                  """#{v!b,no,o,nn}#""",
                  """#{v!b,no,o}#""",
                  """#{+,nun,un,nn}#""",
                  """#{+,nun,un}#""",
                  """#{n!1,ob,ub,nn}#""",
                  """#{n!1,ob,ub}#""",
                  """#{v!a,nu,u,nn}#""",
                  """#{v!a,nu,u}#""",
                  """#{f!,n,nn}#""",
                  """#{f!,n}#""",
                  """#{+,nnun,n}#""",
                  """#{+,nnun}#""",
                  """#{+,nun,n}#""",
                  """#{+,nun}#""",
                  """#{v!a,nnnu,-}#""",
                  """#{v!a,nnnu}#""",
                  """#{v!a,nnu,-}#""",
                  """#{v!a,nnu}#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testRepeatedWildCards(self):
        results = convert_test(self.mathml2,repetitions=True)
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
        results = convert_test(self.mathml3,repetitions=True,synonyms=True,symbol_pairs=False)
        expect = [START_TAG,
                  """#{v!k,nn,a}#""",
                  """#{*,nn,a}#""",
                  """#{v!k,nnnn,we}#""",
                  """#{*,nnnn,we}#""",
                  """#{v!k,nna,we}#""",
                  """#{*,nna,we}#""",
                  """#{n!2,nn,w}#""",
                  """#{*,nn,w}#""",
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
        results = convert_test(self.mathml, terminal_symbols=True)
        self.log(results)
        expect = [START_TAG,
                  """#(v!𝖿𝗏,!0)#""",
                  END_TAG]
        self.assertEqual(results, " ".join(expect))

    def testF2(self):
        self.mathml = self.loadFile(self.f2)
        results = convert_test(self.mathml, terminal_symbols=True)
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
        results = convert_test(self.mathml,terminal_symbols=True,compound_symbols=True)
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
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testWindowSize(self):
        results = convert_test(self.mathml, window_size=2)
        expect = [START_TAG,
                  """#(*,=,n)#""",
                  """#(*,n!1,nn)#""",
                  """#(=,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEOL(self):
        # height too big
        results = convert_test(self.mathml, eol=True)
        expect = [START_TAG,
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testCompoundSymbols(self):
        results = convert_test(self.mathml, compound_symbols=True)
        expect = [START_TAG,
                  """#(*,[n,b])#""",
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testTerminalSymbols(self):
        results = convert_test(self.mathml, terminal_symbols=True)
        expect = [START_TAG,
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  """#(n!1,!0)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testEdgePairs(self):
        results = convert_test(self.mathml, edge_pairs=True)
        expect = [START_TAG,
                  """#(*,=,n)#""",
                  """#(=,n!1,n)#""",
                  """#(n,n,=)#""",
                  """#(b,n,*)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testUnbounded(self):
        results = convert_test(self.mathml, unbounded=True)
        expect = [START_TAG,
                  """#(*,=,n)#""",
                  """#(*,n!1,nn)#""",
                  """#(=,n!1,n)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

    def testLocation(self):
        results = convert_test(self.mathml, location=True)
        expect = [START_TAG,
                  """#(*,=,n,-)#""",
                  """#(*,=,n)#""",
                  """#(=,n!1,n,n)#""",
                  """#(=,n!1,n)#""",
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
        results = convert_test(self.mathml, eol=True)
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
        results = convert_test(self.mathml, compound_symbols=True)
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
        results = convert_test(self.mathml, terminal_symbols=True)
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
        results = convert_test(self.mathml, edge_pairs=True)
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
        results = convert_test(self.mathml, unbounded=True)
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
        results = convert_test(self.mathml, location=True)
        expect = [START_TAG,
                  """#(v!α,m!()1x1,n,-)#""",
                  """#(v!α,m!()1x1,n)#""",
                  """#(m!()1x1,=,n,n)#""",
                  """#(m!()1x1,=,n)#""",
                  """#(=,v!y,n,nn)#""",
                  """#(=,v!y,n)#""",
                  """#(v!y,n!0,b,nnn)#""",
                  """#(v!y,n!0,b)#""",
                  """#(m!()1x1,v!x,w,n)#""",
                  """#(m!()1x1,v!x,w)#""",
                  """#(v!x,n!0,b,nw)#""",
                  """#(v!x,n!0,b)#""",
                  """#(v!α,n!0,b,-)#""",
                  """#(v!α,n!0,b)#""",
                  END_TAG]
        self.log(results)
        self.assertEqual(" ".join(expect), results)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
