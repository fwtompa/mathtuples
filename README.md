# Description of math token creation for Tangent-L
Frank Tompa, October 2021

As a first step to either indexing or querying, and building on the code from Tangent [1] and Tangent-3 [2], this module takes a document and converts all MathML expressions into math features. To this end, convert_math_expression() in convert.py first transforms any MathML expression to a symbol layout tree and then traverses that tree recursively to extract a list of features.

After extensive experimentation, the optimal set of features was found to comprise four types [3]:
   1. Symbol pairs with window size 1 (symbols on adjacent nodes in the tree and edge label)
   2. Terminal symbols (leaves of the tree)
   3. Compound symbols (nodes with more than one outedge together with sets of outedge labels)
   4. Expanded locations (any of the earlier features plus paths to the feature location)

For example, given the MathML equivalent of _y<sub>i</sub><sup>j</sup> = 1 + x<sup>2</sup>_, the extracted features are represented by the concatenation of the following string representations of math tuples:
 ```
 #(start)#
 #(v!y,=,n)# #(v!y,v!i,b)# #(v!y,v!j,a)# #(=,n!1,n)# #(n!1,+,n)# #(+,n!x)# #(v!x,n!2,a)#
 #(v!i,!0)# #(v!j,!0)# #(n!2,!0)#
 #(v!y,[a,b,n])#
 #(v!y,=,n,)# #(v!y,v!i,b,)# #(v!y,v!j,a,)# #(=,n!1,n,n)# #(n!1,+,n,nn)# #(+,n!x,nnn)# #(v!x,n!2,a,nnnn)#
 #(v!i,!0,b)# #(v!j,!0,a)# #(n!2,!0,nnnna)#
 #(v!y,[a,b,n],)#
 #(end)#
 ```
where the first token indicates the start of a formula, the tokens on the next line represent adjacent symbol pairs, the tokens on the fourth line represent terminal symbols, the one on the fifth line represents the sole compound symbol, the ones on the next three lines represent all the previous features with their locations, and the final line signals the end of the formula.
 
Such text representing the extracted features can be used in place of each mathematical expression found in a document or query. 

Generic wild card symbols may be included in queries, as in the query formula _?A x ?B = y_, where _?A_ and _?B_ can match anything. Wild cards are matched by expanding math tokens at the time of indexing to include their wild card token matches (by calling convert_math_expression() with synonyms=True when indexing). For example, when a symbol pair such as `#(v!y,=,n)#` is generated at index time, two additional tokens `#(*,=,n)#` and `#(v!y,*,n)#` are also generated. Similarly, all compound symbols are also extended to include their wild card equivalents, so `#(v!y,[a,b,n])#` causes `#(*,[a,b,n])#` to be generated as well. (To avoid excessive computation and to save index space, `#(*,*,n)#` is not generated and terminal and symbols are not expanded to their wild card equivalents.)

Further details can be found in Dallas Fraser's Mmath thesis [4].

Fraser's thesis did not consider capturing a feature that reflects repetitions of symbols. As a result, a search for _x<sup>2</sup> + 3x_ matches _x<sup>2</sup> + 3y_ fairly well, but _y<sup>2</sup> + 3y_ fairly poorly. Even if _x_ is replaced by the wild card variable _?x_, mismatched variables match as well as matched variables. To address this shortfall, a new feature has been added to capture repetitions [5]. 

For every pair of repeated symbols (including variables, operators, numbers, etc.) in an SLT, based on their relative  positions one of the following tuples are generated:

- `#{symbol,p}#` is generated for symbols that reside on the same path from the root of the SLT, where the path between the repeated symbols is represented by _p_. For example the repeated _x_ symbol in _x<sup>2</sup> + 3x_ is encoded as `#{v!x,nnn}#`.
- `#{symbol,p1,p2}#` is generated for a pair of repeated symbols that reside on different paths from the root of SLT, where _p1_ and _p2_ represent the paths from the nearest common ancestor to each symbol. For example the tuple `#{v!x,a,nn}#` is generated for the repeated _x_ in _2<sup>x</sup>+x_.  

Note that if a symbol appears _k_ times where _k_ > 1, _C(k,2)_ repetition tuples are indexed for that symbol.
 
To expand with location, an additional tuple is generated with the path, traversing from the root, to the first symbol or to the closest common ancestor if the repetition occurs in different paths. For example `#{V!x,a,nn,-}#` is additionally generated for _2<sup>x</sup>+x_. 

Note that we use braces `#{...}#` to distinguish tuples representing repeated symbols from all other math tuples, which are enclosed by parentheses `#(...)#`.

Wild card expansion is also applicable to tuples representing repeated symbols. For instance, `#{*,a,nn}#` and (assuming location expansion is requested as well) `#{*,a,nn,-}#` are additionally generated for _2<sup>x</sup>+x_.

1. Nidhin Pattaniyil, Richard Zanibbi: "Combining TF-IDF Text Retrieval with an Inverted Index over Symbol Pairs in Math Expressions: The Tangent Math Search Engine at NTCIR 2014." _NTCIR 2014_.
2. Richard Zanibbi, Kenny Davila, Andrew Kane, Frank Wm. Tompa: "Multi-Stage Math Formula Search: Using Appearance-Based Similarity Metrics at Scale." _SIGIR 2016_: 145-154.
3. Dallas J. Fraser, Andrew Kane, Frank Wm. Tompa: "Choosing Math Features for BM25 Ranking with Tangent-L." _DocEng 2018_: 17:1-17:10.
4. Dallas J. Fraser: _Math Information Retrieval using a Text Search Engine._ Master’s thesis, University of Waterloo, Cheriton School of Computer Science, University of Waterloo (2018).
5. Yin Ki Ng, Dallas J. Fraser, Besat Kassaie, Frank Wm. Tompa: "Dowsing for Answers to Math Questions: Ongoing Viability of Traditional MathIR." _CLEF (Working Notes) 2021_: 63-81.

## Setup
- `python3 -m build`
- `python3 -m pip install dist/mathtuples-1.0-py3-none-any.whl`

## Testing
  python3 -m mathtuples.testConvert

## Usage
```
  mathtuples.convert.py [-h] [-infile INFILE] [-outfile OUTFILE] [-symbol_pairs]
                  [-eol] [-compound_symbols] [-terminal_symbols] [-edge_pairs]
                  [-unbounded] [-shortened] [-synonyms] [-location]
                  [-window_size [WINDOW_SIZE]]

  optional arguments:
  -h, --help            show this help message and exit
  -infile INFILE, --infile INFILE
                        The file to read from
  -outfile OUTFILE, --outfile OUTFILE
                        The file to output to
  -symbol_pairs         Do not use symbol pairs
  -eol                  Use EOL tuples
  -compound_symbols     Do not use compound symbols
  -terminal_symbols     Use terminal symbols
  -edge_pairs           Use edge pairs
  -unbounded            Symbol pairs should be unbounded
  -shortened            Unbounded symbol pairs should not include abbreviated path
  -synonyms             Expand nodes to include synonyms
  -location             Do not include location
  -window_size [WINDOW_SIZE]
  ```

## Example with default (optimal) parameter settings
  `python3 -m convert -infile [your-file]`
