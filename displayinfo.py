"""

Display information in console for debugging

Generic functions to display lists of words, formatted into columns
Option to add headers

"""

def align(*words, limit=10, buffer='  '):

    tabbedline = ''
    for word in words:

        word = str(word)
        wordlength = len(word)

        if wordlength < limit:
            numspaces = limit - wordlength
            word = word + ' '*numspaces
        else:
            word = word[0:limit]

        formattedword = word + buffer
        tabbedline += formattedword

    print(tabbedline)
    return(tabbedline)

def alignheader(*words, limit=10):
    """
    displays a header with column names followed by a dividing dashed line 
    """

    dashedlines = []
    for word in words:
        wordlength = len(word)
        dashedlines.append('-'*wordlength)
    
    align(*words, limit=limit)
    align(*dashedlines,limit=limit)


#races = [{'race': 1, 'game': 'supermetroid123456789', 'num': '$$$'}, {'race': 2, 'game': 'smb3', 'num': '$$$'}, {'race': 3, 'game': 'supermetroid', 'num': '$$$'}]
#displayTabbed('racefound!', *races, race=True, game=False, num=True)