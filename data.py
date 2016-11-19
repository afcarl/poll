'''
functions that read in data from path
'''

def read_ffm(path, group_path = None):
    '''
    path: path to the file with libffm format
    group_path: path to the file with group size, default is None
    '''
    if group_path:
        group_size = []
        with open(group_path) as groupfile:
            for row in groupfile:
                group_size.append(int(row.rstrip()))
        x = []
        y = []
        count = 0
        idx = 0
        current_size = group_size[idx]
        with open(path) as infile:
            for row in infile:
                row = row.rstrip().split(" ")
                y_row = int(row[0])
                x_row = []
                for f in row[1:]:
                    x_row.append(f)
                x.append(x_row)
                y.append(y_row)
                count += 1
                if count == current_size:
                    yield idx, x, y
                    if idx < len(group_size) - 1:
                        idx += 1
                        current_size = group_size[idx]
                        x = []
                        y = []
                        count = 0

    else:
        with open(path) as infile:
            for e, row in enumerate(infile):
                row = row.rstrip().split(" ")
                y = int(row[0])
                x = []
                for f in row[1:]:
                    x.append(f)

                yield e, [x], [y]
