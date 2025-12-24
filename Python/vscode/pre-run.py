"""
Add these two varibles before running the script
#VSCODE_PATH = '' 
#PYTHON_EXE_PATH = ''
"""
import sys, os, subprocess, re

def locatePythonToolFolder(extension, libraryPath):
    """
    figure out the ms-python install location for debugpy library
    """

    vscodeExtensionPath = ''
    if sys.platform.startswith('win'):
        vscodeExtensionPath = os.path.expandvars(r'%USERPROFILE%\.vscode\extensions')
    else:
        vscodeExtensionPath = os.path.expanduser('~/.vscode/extensions')

    if os.path.exists(vscodeExtensionPath) == False:
        return ''

    msPythons = []
    versionPattern = re.compile(fr'ms-python.{extension}-(?P<major>\d+).(?P<minor>\d+).(?P<patch>\d+)')
    for entry in os.scandir(vscodeExtensionPath):
        if entry.is_dir(follow_symlinks=False):
            match = versionPattern.match(entry.name)
            if match:
                try:
                    version = tuple(int(match[key]) for key in ('major', 'minor', 'patch'))
                    msPythons.append((entry, version))
                except:
                    pass

    msPythons.sort(key=lambda pair: pair[1], reverse=True)
    if (msPythons):
        if None == msPythons[0]:
            return ''
        msPythonPath = os.path.expandvars(msPythons[0][0].path)
        msPythonPath = os.path.join(msPythonPath, libraryPath)
        msPythonPath = os.path.normpath(msPythonPath)
        debugpyPath = os.path.join(msPythonPath, 'debugpy')
        if os.path.exists(debugpyPath):
            return msPythonPath
    return ''

def addSearchPath(searchPath):
    """
    add '..\.vscode\extensions\ms-python.debugpy-2024.6.0\bundled\libs' to Python search Path so that we can import debugpy library
    """

    if searchPath:
        sys.path.append(searchPath)
        return True

    return False

def addDebugpyPath():
    """
    Add the path to the debugpy module from the ms-python extension to the system path.
    """

    debugpyPath = locatePythonToolFolder('debugpy', 'bundled/libs') or \
        locatePythonToolFolder('python', 'python_files/lib/python') or \
        locatePythonToolFolder('python', 'pythonFiles/lib/python')
    if (debugpyPath):
        addSearchPath(debugpyPath)

def installVSCodeExtension(vsCodePath,pythonPath):
    if not vsCodePath:
        return False
    my_env = os.environ.copy()
    my_env["PATH"] = pythonPath + os.pathsep + my_env["PATH"]
    sys.executable = os.path.join(pythonPath, 'python')
    subprocess.call([vsCodePath,'--install-extension', 'ms-python.python'],env=my_env)
    return True

def fixOsFile():
    if not hasattr(os, '__file__'):
        import pathlib
        import types
        os.__file__ = str(pathlib.Path(types.__file__).parent / 'os.py')

if __name__ == '__main__':
    installVSCodeExtension(VSCODE_PATH,PYTHON_EXE_PATH)
    addDebugpyPath()
    fixOsFile()
