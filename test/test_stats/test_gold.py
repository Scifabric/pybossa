from pybossa.stats import gold
import numpy as np


def test_count_matches_right():
    gold_ans = {
        'hello': 1
    }
    taskrun = {
        'hello': 1
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 1
    assert stat.value['wrong'] == 0


def test_count_matches_wrong():
    gold_ans = {
        'hello': 1
    }
    taskrun = {
        'hello': 2
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 0
    assert stat.value['wrong'] == 1


def test_count_matches_error():
    gold_ans = {
        'goodbye': 1
    }
    taskrun = {
        'goodbye': 1
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 0
    assert stat.value['wrong'] == 0


def test_count_matches_error_no_ans():
    gold_ans = {
        'hello': {
            'goodbye': 1
        }
    }
    taskrun = {}
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello.goodbye')
    assert stat.value['right'] == 0
    assert stat.value['wrong'] == 1


def test_count_matches_nested_right():
    gold_ans = {
        'hello': {
            'world': 1
        }
    }
    taskrun = {
        'hello': {
            'world': 1
        }
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello.world')
    assert stat.value['right'] == 1
    assert stat.value['wrong'] == 0


def test_count_matches_nested_wrong():
    gold_ans = {
        'hello': {
            'world': 1
        }
    }
    taskrun = {
        'hello': {
            'world': 2
        }
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello.world')
    assert stat.value['right'] == 0
    assert stat.value['wrong'] == 1


def test_count_matches_list_all_right():
    gold_ans = {
        'hello': [1, 2, 3]
    }
    taskrun = {
        'hello': [1, 2, 3]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 3
    assert stat.value['wrong'] == 0


def test_count_matches_list_all_wrong():
    gold_ans = {
        'hello': [1, 2, 3]
    }
    taskrun = {
        'hello': [3, 4, 5]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 0
    assert stat.value['wrong'] == 3


def test_count_matches_list_partially_correct():
    gold_ans = {
        'hello': [1, 2, 3]
    }
    taskrun = {
        'hello': [3, 2, 5, 6]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 1
    assert stat.value['wrong'] == 2


def test_count_matches_matrix():
    gold_ans = {
        'hello': [[1, 2], [3, 4]]
    }
    taskrun = {
        'hello': [[1, 3], [3, 4]]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 3
    assert stat.value['wrong'] == 1


def test_count_matches_different_shapes():
    gold_ans = {
        'hello': [[1, 2, 3]]
    }
    taskrun = {
        'hello': [[1, 2], [3, 4]]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 2
    assert stat.value['wrong'] == 1


def test_count_matches_different_shapes_2():
    gold_ans = {
        'hello': [[1, 2, 3], [4, 5, 6]]
    }
    taskrun = {
        'hello': [[1, 2], [3, 5]]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 3
    assert stat.value['wrong'] == 3


def test_count_matches_different_shapes_3():
    gold_ans = {
        'hello': [[1, 2, 3], [4, 5, 6]]
    }
    taskrun = {
        'hello': [[1, 3]]
    }
    stat = gold.RightWrongCount()
    stat.compute(taskrun, gold_ans, 'hello')
    assert stat.value['right'] == 1
    assert stat.value['wrong'] == 5


def test_confusion_matrix():
    stat = gold.ConfusionMatrix(['True', 'False'])
    gold_ans = {
        'hello': 'True'
    }
    taskrun = {
        'hello': 'True'
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    assert stat.value['matrix'][0][0] == 1, stat.value['matrix']
    assert stat.value['matrix'][0][1] == 0, stat.value['matrix']
    assert stat.value['matrix'][1][0] == 0, stat.value['matrix']
    assert stat.value['matrix'][1][1] == 0, stat.value['matrix']


def test_confusion_matrix_list_1():
    stat = gold.ConfusionMatrix(['True', 'False'])
    gold_ans = {
        'hello': ['True', 'False']
    }
    taskrun = {
        'hello': ['True', 'False']
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    assert stat.value['matrix'][0][0] == 1, stat.value['matrix']
    assert stat.value['matrix'][0][1] == 0, stat.value['matrix']
    assert stat.value['matrix'][1][0] == 0, stat.value['matrix']
    assert stat.value['matrix'][1][1] == 1, stat.value['matrix']


def test_confusion_matrix_list_2():
    stat = gold.ConfusionMatrix(['True', 'False'])
    gold_ans = {
        'hello': ['True', 'False', 'False', 'False']
    }
    taskrun = {
        'hello': ['True', 'True', 'False', 'True']
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    assert stat.value['matrix'][0][0] == 1, stat.value['matrix']
    assert stat.value['matrix'][0][1] == 0, stat.value['matrix']
    assert stat.value['matrix'][1][0] == 2, stat.value['matrix']
    assert stat.value['matrix'][1][1] == 1, stat.value['matrix']


def test_many_labels():
    stat = gold.ConfusionMatrix(['A', 'B', 'C', 'D'])
    true = ['A', 'A', 'B', 'B', 'C', 'C', 'D', 'D']
    obs = ['B', 'C', 'B', 'B', 'D', 'C', 'A', 'B']
    gold_ans = {
        'hello': [{
            'world': value
        } for value in true]
    }
    taskrun = {
        'hello': [{
            'world': value
        } for value in obs]
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello.world')
    assert stat.value['matrix'][0][1] == 1, stat.value['matrix']
    assert stat.value['matrix'][0][2] == 1, stat.value['matrix']
    assert stat.value['matrix'][1][1] == 2, stat.value['matrix']
    assert stat.value['matrix'][2][2] == 1, stat.value['matrix']
    assert stat.value['matrix'][2][3] == 1, stat.value['matrix']
    assert stat.value['matrix'][3][0] == 1, stat.value['matrix']
    assert stat.value['matrix'][3][1] == 1, stat.value['matrix']
    assert (np.array(stat.value['matrix']) >= 0).all(), stat.value['matrix']
    assert np.array(stat.value['matrix']).sum() == len(true)


def test_confusion_matrix_invalueid_gold():
    stat = gold.ConfusionMatrix(['True', 'False'])
    gold_ans = {
        'hello': 'None'
    }
    taskrun = {
        'hello': 'True'
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    stat.value['matrix'] == [[0, 0], [0, 0]]


def test_confusion_matrix_invalueid_answer():
    stat = gold.ConfusionMatrix(['True', 'False'])
    gold_ans = {
        'hello': 'True'
    }
    taskrun = {
        'hello': 'None'
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    stat.value['matrix'] == [[0, 0], [0, 0]]


def test_array_match_right():
    stat = gold.RightWrongCount()
    stat.compare_lists = True
    gold_ans = {
        'hello': [1, 2, 3]
    }
    taskrun = {
        'hello': [1, 2, 3]
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    stat.right == 1
    stat.wrong == 0


def test_array_match_wrong():
    stat = gold.RightWrongCount()
    stat.compare_lists = True
    gold_ans = {
        'hello': [1, 9, 3]
    }
    taskrun = {
        'hello': [1, 2, 3]
    }
    stat = gold.compute(stat, taskrun, gold_ans, 'hello')
    stat.right == 0
    stat.wrong == 1
