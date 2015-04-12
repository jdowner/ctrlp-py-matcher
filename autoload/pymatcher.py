import heapq
import logging
import os
import re

try:
    import vim
except ImportError:
    pass

logger = logging.getLogger('ctrlp-py-matcher')
logger.addHandler(logging.FileHandler(os.path.expanduser('~/.ctrp-py-patcher.log')))
logger.setLevel(logging.DEBUG)


def fuzzy_match(items, expr, mode, limit, aregex=1):
    specialChars = ['^','$','.','{','}','(',')','[',']','\\','/','+']

    lowAstr = expr.lower()

    regex = ''
    if aregex == 1:
        regex = expr
    else:
        if len(lowAstr) == 1:
            c = lowAstr
            if c in specialChars:
                c = '\\' + c
            regex += c
        else:
            for c in lowAstr[:-1]:
                if c in specialChars:
                    c = '\\' + c
                regex += c + '[^' + c + ']*'
            else:
                c = lowAstr[-1]
                if c in specialChars:
                    c = '\\' + c
                regex += c

    res = []
    prog = re.compile(regex)

    def filename_score(line):
        # get filename via reverse find to improve performance
        slashPos = line.rfind('/')
        line = line if slashPos == -1 else line[slashPos + 1:]

        lineLower = line.lower()
        result = prog.search(lineLower)
        if result:
            score = result.end() - result.start() + 1
            score = score + ( len(lineLower) + 1 ) / 100.0
            score = score + ( len(line) + 1 ) / 1000.0
            return 1000.0 / score

        return 0


    def path_score(line):
        lineLower = line.lower()
        result = prog.search(lineLower)
        if result:
            score = result.end() - result.start() + 1
            score = score + ( len(lineLower) + 1 ) / 100.0
            return 1000.0 / score

        return 0


    if mode == 'filename-only':
        res = [(filename_score(line), line) for line in items]

    elif mode == 'first-non-tab':
        res = [(path_score(line.split('\t')[0]), line) for line in items]

    elif mode == 'until-last-tab':
        res = [(path_score(line.rsplit('\t')[0]), line) for line in items]

    else:
        res = [(path_score(line), line) for line in items]

    rez = []
    rez.extend([line for score, line in heapq.nlargest(limit, res)])

    # Use double quoted vim strings and escape \
    vimrez = ['"' + line.replace('\\', '\\\\').replace('"', '\\"') + '"' for line in rez]

    return regex, vimrez


def CtrlPPyMatch():
    items = vim.eval('a:items')
    astr = vim.eval('a:str')
    lowAstr = astr.lower()
    limit = int(vim.eval('a:limit'))
    mmode = vim.eval('a:mmode')
    aregex = int(vim.eval('a:regex'))

    logger.debug('searching for {}'.format(astr))

    rez = vim.eval('s:rez')

    regex, vimrez = fuzzy_match(items, astr, mmode, limit, aregex)

    for result in vimrez:
        logger.debug("- {}".format(result))

    vim.command("let s:regex = '%s'" % regex)
    vim.command('let s:rez = [%s]' % ','.join(vimrez))
    
