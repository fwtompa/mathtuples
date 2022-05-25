# Description of math token creation for Tangent-L
Frank Tompa, March 2022
(version 2: May 2022)

As a first step to either indexing or querying, and building on the code from Tangent [1] and Tangent-3 [2], this module takes a document and converts all MathML expressions into math features. To this end, convert_math_expression() in convert.py first transforms any MathML expression to a symbol layout tree and then traverses that tree recursively to extract a list of features.

After extensive experimentation, the optimal set of features was found to comprise four types [3]:
   1. Symbol pairs with window size 1 (symbols on adjacent nodes in the tree and edge label)
   2. Terminal symbols (leaves of the tree)
   3. Compound symbols (nodes with more than one outedge together with sets of outedge labels)
   4. Duplicate symbols (symbols that are repeated in the formula together with their relative paths)
   5. Expanded locations (any of the earlier features plus paths to the feature location if fewer than 8 nodes on that path)
Paths are measured from the root of the tree or from the closest relational (i.e., equality-like) operator.

For example, given the MathML equivalent of _y<sub>i</sub><sup>n</sup> = n + x<sup>n</sup>_, the extracted features are represented by the concatenation of the following string representations of math tuples:
 ```
 #(start)#
 #(v!y,=,n)# #(v!y,v!i,b)# #(v!y,v!n,a)# #(=,v!n,n)# #(v!n,+,n)# #(+,n!x)# #(v!x,v!n,a)#
 #(v!i,!0)# #(v!n,!0)# #(v!,!0)#
 #(v!y,[a,b,n])#
 #{v!n,nna}# #{v!n,a,n}# #{?v,nna}# #{?v,a,n}# 
 #(v!y,=,n,)# #(v!y,v!i,b,)# #(v!y,v!n,a,)# #(=,v!n,n,n)# #(v!n,+,n,n)# #(+,n!x,nn)# #(v!x,v!n,a,nnn)#
 #(v!i,!0,b)# #(v!n,!0,a)# #(v!n,!0,nnna)#
 #(v!y,[a,b,n],)#
 #{v!n,nna,n}# #{v!n,a,n,}# #{?v,nna,n}# #{?v,a,n,}# 
 #(end)#
 ```
where the first token indicates the start of a formula, the tokens on the next line represent adjacent symbol pairs, the tokens on the fourth line represent terminal symbols, the one on the fifth line represents the sole compound symbol, the ones on the next line represent duplicate symbols, the ones on the next four lines represent all the previous features with their locations, and the final line signals the end of the formula.
 
Such text representing the extracted features can be used in place of each mathematical expression found in a document or query. 

Generic wildcard symbols may be included in queries, as in the query formula _?A x ?B = y_, where _?A_ and _?B_ can match anything. Wildcards are matched by expanding math tokens at the time of indexing to include their wildcard token matches (by calling convert_math_expression() with synonyms=True when indexing). For example, when a symbol pair such as `#(v!y,=,n)#` is generated at index time, two additional tokens `#(*,=,n)#` and `#(v!y,*,n)#` are also generated. Similarly, all compound symbols are also extended to include their wildcard equivalents, so `#(v!y,[a,b,n])#` causes `#(*,[a,b,n])#` to be generated as well. (To avoid excessive computation and to save index space, `#(*,*,n)#` is not generated and terminal and symbols are not expanded to their wildcard equivalents.)

Further details can be found in Dallas Fraser's MMath thesis [4] and in a paper describing experiments for the 2022 ARQMath Lab [5].

1. Nidhin Pattaniyil, Richard Zanibbi: "Combining TF-IDF Text Retrieval with an Inverted Index over Symbol Pairs in Math Expressions: The Tangent Math Search Engine at NTCIR 2014." _NTCIR 2014_.
2. Richard Zanibbi, Kenny Davila, Andrew Kane, Frank Wm. Tompa: "Multi-Stage Math Formula Search: Using Appearance-Based Similarity Metrics at Scale." _SIGIR 2016_: 145-154.
3. Dallas J. Fraser, Andrew Kane, Frank Wm. Tompa: "Choosing Math Features for BM25 Ranking with Tangent-L." _DocEng 2018_: 17:1-17:10.
4. Dallas J. Fraser: _Math Information Retrieval using a Text Search Engine._ Master’s thesis, University of Waterloo, Cheriton School of Computer Science, University of Waterloo (2018).
5. Andrew R. Kane, Yin Ki Ng, Frank Wm. Tompa: "Dowsing for Answers to Math Questions: Doing Better with Less." _CLEF (Working Notes) 2022_.

## Setup
- `python3 -m build`
- `python3 -m pip install dist/mathtuples-1.0-py3-none-any.whl`

## Testing
  `python3 -m mathtuples.testConvert`

## Usage
```
convert.py [-h] [-W WINDOW_SIZE] [-S SYMBOL_PAIRS] [-R EDGE_PAIRS] [-T TERMINAL_SYMBOLS] [-E EOL]
                  [-C COMPOUND_SYMBOLS] [-L LONG] [-A ABBREVIATED] [-D DUPLICATE_NODES] [-docid DOCID] [-a ANCHORS] [-c]
                  [-d DUPS] [-s] [-w WILD_DUPS]

Convert - MathML file to file with Math Tuples

optional arguments:
  -h, --help            show this help message and exit
  -W WINDOW_SIZE, --window_size WINDOW_SIZE
                        The size of the window for symbol pairs (99 => unlimited); default = 1
  -S SYMBOL_PAIRS, --symbol_pairs SYMBOL_PAIRS
                        Include Symbol pairs and/or locations*
  -R EDGE_PAIRS, --edge_pairs EDGE_PAIRS
                        Include Relationship edge pairs and/or locations*
  -T TERMINAL_SYMBOLS, --terminal_symbols TERMINAL_SYMBOLS
                        Include Terminal symbols and/or locations*
  -E EOL, --eol EOL     Include End-of-line symbols and/or locations*
  -C COMPOUND_SYMBOLS, --compound_symbols COMPOUND_SYMBOLS
                        Include Compound symbols and/or locations*
  -L LONG, --long_pairs LONG
                        Include Long pairs without relationships and/or locations*
  -A ABBREVIATED, --abbreviated ABBREVIATED
                        Include Abbreviated relationships for long pairs and/or locations*
  -D DUPLICATE_NODES, --duplicate_nodes DUPLICATE_NODES
                        Include Duplicate symbols and/or locations*
  -docid DOCID, --docid DOCID
                        String preceding each document identifier; '' => no docid
  -a ANCHORS, --anchors ANCHORS
                        Enable (e)/disable (d) 'equality' operators to anchor location calculations; default => e
  -c, --context         Return the math tuples in context; default => tuples only
  -d DUPS, --dups DUPS  Include duplication tuples for subset of 'VNOMFRTW'**
  -s, --synonyms        Expand nodes to include wildcard synonyms
  -w WILD_DUPS, --wild_dups WILD_DUPS
                        Wild duplication tuples for subset of 'VNOMFRTW'**

Codes:
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

```

## Example with default (optimal) parameter settings
  `cat Your-Filename-Here | python3 -m mathtuples.convert > Just-Math-Tuples`
## Use in a processing pipeline, replacing MathML by tuples in context
  `pre-process < My-Input | python3 -m mathtuples.convert -c | post-process > My-Output`
