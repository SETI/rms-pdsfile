import os
def get_test_paths(path):
    res = []
    for root, dirs, files in os.walk(path):
        # print('=================')
        # print(root)
        # print(dirs)
        # print(files)
        # print(root.index('/bundles'))
        # print(root[idx:])
        idx = root.index('bundles')
        root = root[idx:]
        for file in files:
            if ('100m' in file or 'atmosphere' in file) and '.tab' in file:
                res.append(f'{root}/{file}')
    return res


TARGET_PATH = '/Users/yu-jenchang/Dropbox (SETI Institute)/Pds4FileTest/pds4-holdings/bundles/uranus_occs_earthbased'
res = get_test_paths(TARGET_PATH)
print(res)
