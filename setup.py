
from cx_Freeze import setup, Executable

build_exe_options = {
    "zip_include_packages": ['pew', 'micromoth', 'quantumblur'],
}
  
setup( 
    name='quantum_blur_demo', 
    version='0.1', 
    description='Demo of Quantum Blur', 
    author='James Wootton', 
    author_email='decodoku@gmail.com', 
    install_requires=[ 
        'pygame', 
    ],
    executables=[Executable("main.py")]
) 