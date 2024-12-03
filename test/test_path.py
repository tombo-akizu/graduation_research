from gui_tester.path import Path

def test_path():
    path = Path()
    l = [0, 1, 2, 3, 0, 1, 2, 0]
    for state in l:
        path.append(state)
    print(path.path_list)
    assert path.path_list == l

def test_path1():
    path = Path()
    l = [0, 1, 2, 3, 0, 1, 2, 0, 1, 2, 0]
    for state in l:
        path.append(state)
    assert path.path_list == [0, 1, 2, 3, 0, 1, 2, 0]

def test_path2():
    path = Path()
    l = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    for state in l:
        path.append(state)
    assert path.path_list == [0, 1, 2, 3, 0, 1]

def test_path3():
    path = Path()
    l = [0, 1, 2, 3, 0, 0]
    for state in l:
        path.append(state)
    assert path.path_list == [0, 1, 2, 3, 0]