from distutils.core import setup

setup(
    name='mathtuples',
    keywords=['MathIR','MathML formula retrieval','Tangent-L','MathDowsers'],
    packages=['mathtuples'],
    package_data={"mathtuples":["testFiles/*.html","testFiles/*.xml"]},
)