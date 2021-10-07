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
import os
import subprocess
import sys
import platform
import re
__author__ = 'Nidhin, FWTompa'

class LatexToMathML(object):
    @classmethod
    def convert_to_mathml(cls, tex_query):
        # print("Convert LaTeX to MathML:$"+tex_query+"$",flush=True)
        qvar_template_file = os.path.join(os.path.dirname(__file__),"mws.sty.ltxml")
        if not os.path.exists(qvar_template_file):
            print('Tried %s' % qvar_template_file, end=": ")
            sys.exit("tex: "+tex_query+ " Stylesheet for wildcard is missing")

        # Make sure there are no isolated % signs in tex_query (introduced by latexmlmath, for example, in 13C.mml test file) (FWT)
        tex_query = re.sub(r'([^\\])%',r'\1',tex_query) # remove % not preceded by backslashes (FWT)

        use_shell= ('Windows' in platform.system())
        p2 = subprocess.Popen(['latexmlmath' ,'--pmml=-','--preload=amsmath', '--preload=amsfonts', '--preload='+qvar_template_file, '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = p2.communicate(input=tex_query.encode())
        
        if (not output) and err:
            print("Error in converting LaTeX to MathML: "+tex_query, file=sys.stderr)
            raise Exception(str(err))
        try:
            result= output.decode('utf-8')
            # strangely, not getting expected conversion. Instead      (FWT)
            #    <mi mathcolor="red" mathvariant="italic">qvar_B</mi>
            # should have been
            #    <mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="B"/>
            
            result = re.sub(r'<mi.*?>qvar_(.*)</mi>', r'<mws:qvar xmlns:mws="http://search.mathweb.org/ns" name="\1"/>', result)  # FWT
        except UnicodeDecodeError as uae:
            print("Failed to decode " + uae.reason, file=sys.stderr)
            result=output.decode('utf-8','replace')
            print ("Decoded %s" % result)
        except:
            print("Failure in converting LaTeX in "+tex_query, file=sys.stderr)
            raise # pass on the exception to identify context
        return result
