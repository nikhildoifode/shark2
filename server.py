# References:
# https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
# SHARK2: A Large Vocabulary Shorthand Writing System for Pen-based Computers - Per-Ola Kristensson, Shumin Zhai

'''

You can modify the parameters, return values and data structures used in every function if it conflicts with your
coding style or you want to accelerate your code.

You can also import packages you want.

But please do not change the basic structure of this file including the function names. It is not recommended to merge
functions, otherwise it will be hard for TAs to grade your code. However, you can add helper function if necessary.

'''

from flask import Flask, request
from flask import render_template
import time
import json
import math
from scipy.interpolate import interp1d

app = Flask(__name__)

# Centroids of 26 keys
centroids_X = [50, 205, 135, 120, 100, 155, 190, 225, 275, 260, 295, 330, 275, 240, 310, 345, 30, 135, 85, 170, 240, 170, 65, 100, 205, 65]
centroids_Y = [85, 120, 120, 85, 50, 85, 85, 85, 50, 85, 85, 85, 120, 120, 50, 50, 50, 50, 85, 50, 50, 120, 50, 120, 50, 120]

# Pre-process the dictionary and get templates of 10000 words
words, probabilities = [], {}
template_points_X, template_points_Y = [], []
file = open('words_10000.txt')
content = file.read()
file.close()
content = content.split('\n')
for line in content:
    line = line.split('\t')
    words.append(line[0])
    probabilities[line[0]] = float(line[2])
    template_points_X.append([])
    template_points_Y.append([])
    for c in line[0]:
        template_points_X[-1].append(centroids_X[ord(c) - 97])
        template_points_Y[-1].append(centroids_Y[ord(c) - 97])


def distance (x1, y1, x2, y2):
    return round(math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), 2)


def getEquidistantPoints(p1, p2, n):
    return [p1 + (((1./n) * i) * (p2 - p1)) for i in range(n + 1)]


def generate_sample_points(points_X, points_Y):
    '''Generate 100 sampled points for a gesture.

    In this function, we should convert every gesture or template to a set of 100 points, such that we can compare
    the input gesture and a template computationally.

    :param points_X: A list of X-axis values of a gesture.
    :param points_Y: A list of Y-axis values of a gesture.

    :return:
        sample_points_X: A list of X-axis values of a gesture after sampling, containing 100 elements.
        sample_points_Y: A list of Y-axis values of a gesture after sampling, containing 100 elements.
    '''

    sample_points_X, sample_points_Y = [], []
    # TODO: Start sampling (12 points)
    X = points_X
    Y = points_Y

    lenSample = len(X)
    strokeLength = [0]
    for index in range(1, lenSample):
        strokeLength.append(strokeLength[index-1] + distance(X[index], Y[index], X[index-1], Y[index-1]))

    equiDistPts = getEquidistantPoints(min(strokeLength), max(strokeLength), 99)
    ptObjX = interp1d(strokeLength, X)
    ptObjY = interp1d(strokeLength, Y)
    sample_points_X = ptObjX(equiDistPts)
    sample_points_Y = ptObjY(equiDistPts)

    return sample_points_X, sample_points_Y


# Pre-sample every template
template_sample_points_X, template_sample_points_Y = [], []
for i in range(10000):
    X, Y = generate_sample_points(template_points_X[i], template_points_Y[i])
    template_sample_points_X.append(X)
    template_sample_points_Y.append(Y)


def do_pruning(gesture_points_X, gesture_points_Y, template_sample_points_X, template_sample_points_Y):
    '''Do pruning on the dictionary of 10000 words.

    In this function, we use the pruning method described in the paper (or any other method you consider it reasonable)
    to narrow down the number of valid words so that the ambiguity can be avoided to some extent.

    :param gesture_points_X: A list of X-axis values of input gesture points, which has 100 values since we have
        sampled 100 points.
    :param gesture_points_Y: A list of Y-axis values of input gesture points, which has 100 values since we have
        sampled 100 points.
    :param template_sample_points_X: 2D list, containing X-axis values of every template (10000 templates in total).
        Each of the elements is a 1D list and has the length of 100.
    :param template_sample_points_Y: 2D list, containing Y-axis values of every template (10000 templates in total).
        Each of the elements is a 1D list and has the length of 100.

    :return:
        valid_words: A list of valid words after pruning.
        valid_probabilities: The corresponding probabilities of valid_words.
        valid_template_sample_points_X: 2D list, the corresponding X-axis values of valid_words. Each of the elements
            is a 1D list and has the length of 100.
        valid_template_sample_points_Y: 2D list, the corresponding Y-axis values of valid_words. Each of the elements
            is a 1D list and has the length of 100.
    '''
    valid_words, valid_template_sample_points_X, valid_template_sample_points_Y = [], [], []
    # TODO: Set your own pruning threshold
    threshold = 20

    # TODO: Do pruning (12 points)
    lenTemplate = len(template_sample_points_X)
    for index in range(lenTemplate):
        templateX = template_sample_points_X[index]
        templateY = template_sample_points_Y[index]
        if (distance(gesture_points_X[0], gesture_points_Y[0], templateX[0], templateY[0]) < threshold and
        (distance(gesture_points_X[99], gesture_points_Y[99], templateX[99], templateY[99]) < threshold)):
            valid_words.append(words[index])
            valid_template_sample_points_X.append(templateX)
            valid_template_sample_points_Y.append(templateY)

    return valid_words, valid_template_sample_points_X, valid_template_sample_points_Y


def get_shape_scores(gesture_sample_points_X, gesture_sample_points_Y, valid_template_sample_points_X, valid_template_sample_points_Y):
    '''Get the shape score for every valid word after pruning.

    In this function, we should compare the sampled input gesture (containing 100 points) with every single valid
    template (containing 100 points) and give each of them a shape score.

    :param gesture_sample_points_X: A list of X-axis values of input gesture points, which has 100 values since we
        have sampled 100 points.
    :param gesture_sample_points_Y: A list of Y-axis values of input gesture points, which has 100 values since we
        have sampled 100 points.
    :param valid_template_sample_points_X: 2D list, containing X-axis values of every valid template. Each of the
        elements is a 1D list and has the length of 100.
    :param valid_template_sample_points_Y: 2D list, containing Y-axis values of every valid template. Each of the
        elements is a 1D list and has the length of 100.

    :return:
        A list of shape scores.
    '''
    shape_scores = []
    # TODO: Set your own L
    L = 1

    # TODO: Calculate shape scores (12 points)
    gestNormX = round(L / max(gesture_sample_points_X), 2)
    gestNormY = round(L / max(gesture_sample_points_Y), 2)

    lenTemplate = len(valid_template_sample_points_X)
    lenGesture = len(gesture_sample_points_X)
    for index in range(lenTemplate):
        sum = 0
        templateX = valid_template_sample_points_X[index]
        templateY = valid_template_sample_points_Y[index]
        tempNormX = round(L / max(templateX), 2)
        tempNormY = round(L / max(templateY), 2)
        for j in range(lenGesture):
            sum += distance(gesture_sample_points_X[j] * gestNormX, gesture_sample_points_Y[j] * gestNormY,
            templateX[j] * tempNormX, templateY[j] * tempNormY)

        sum = round(sum / lenGesture, 2)
        shape_scores.append(sum)

    return shape_scores


def get_min_pq(pxi, pyi, qx, qy):
    minVal = float('inf')
    index = 0
    lenShape = len(qx)
    for j in range(lenShape):
        val = ((pxi - qx[j]) ** 2) + ((pyi - qy[j]) ** 2)
        if (val < minVal):
            minVal = val
            index = j
        
    return distance(pxi, qx[index], pyi, qy[index])


def get_location_scores(gesture_sample_points_X, gesture_sample_points_Y, valid_template_sample_points_X, valid_template_sample_points_Y):
    '''Get the location score for every valid word after pruning.

    In this function, we should compare the sampled user gesture (containing 100 points) with every single valid
    template (containing 100 points) and give each of them a location score.

    :param gesture_sample_points_X: A list of X-axis values of input gesture points, which has 100 values since we
        have sampled 100 points.
    :param gesture_sample_points_Y: A list of Y-axis values of input gesture points, which has 100 values since we
        have sampled 100 points.
    :param template_sample_points_X: 2D list, containing X-axis values of every valid template. Each of the
        elements is a 1D list and has the length of 100.
    :param template_sample_points_Y: 2D list, containing Y-axis values of every valid template. Each of the
        elements is a 1D list and has the length of 100.

    :return:
        A list of location scores.
    '''
    location_scores = []
    radius = 15

    # TODO: Calculate location scores (12 points)
    gestureX = gesture_sample_points_X
    gestureY = gesture_sample_points_Y

    lenGesture = len(gesture_sample_points_X)
    lenTemplate = len(valid_template_sample_points_X)
    for index in range(lenTemplate):
        templateX = valid_template_sample_points_X[index]
        templateY = valid_template_sample_points_Y[index]

        # Calculate location score
        locScore = 0

        # Calculate dut
        sum_dut = 0
        for j in range(lenGesture):
            sum_dut += max(get_min_pq(gestureX[j], gestureY[j], templateX, templateY) - radius, 0)

        if (sum_dut == 0):
            # Calculate dtu
            sum_dtu = 0
            for j in range(lenGesture):
                sum_dtu += max(get_min_pq(templateX[j], templateY[j], gestureX, gestureY) - radius, 0)

            if sum_dtu == 0:
                location_scores.append(locScore)
                continue
    
        alphaSum = 0
        for i in range(lenGesture):
            # Calculate delta and alpha
            alpha = distance(templateX[i], templateY[i], gestureX[i], gestureY[i])
            alphaSum += alpha
            delta = alpha
            delta = distance(templateX[i], templateY[i], gestureX[i], gestureY[i])
            locScore = round(locScore + (alpha * delta), 2)

        locScore = round(locScore / alphaSum, 2)
        location_scores.append(locScore)

    return location_scores


def get_integration_scores(shape_scores, location_scores):
    integration_scores = []
    # TODO: Set your own shape weight
    shape_coef = 0.5
    # TODO: Set your own location weight
    location_coef = 0.5

    lenScores = len(shape_scores)
    for index in range(lenScores):
        integration_scores.append(round((shape_coef * shape_scores[index]) + (location_coef * location_scores[index]), 2))

    return integration_scores


def get_best_word(valid_words, integration_scores):
    '''Get the best word.

    In this function, you should select top-n words with the highest integration scores and then use their corresponding
    probability (stored in variable "probabilities") as weight. The word with the highest weighted integration score is
    exactly the word we want.

    :param valid_words: A list of valid words.
    :param integration_scores: A list of corresponding integration scores of valid_words.
    :return: The most probable word suggested to the user.
    '''
    best_word = 'the'
    # TODO: Set your own range.
    n = 3
    # TODO: Get the best word (12 points)
    large1 = large2 = large3 = float('inf')
    index1 = 0
    index2 = 1
    index3 = 2
    lenScores = len(integration_scores)
    if (lenScores >= 3):
        for index in range(lenScores):
            if (integration_scores[index] < large3):
                large3 = integration_scores[index]
                index3 = index
                if (integration_scores[index] < large2):
                    large3 = large2
                    index3 = index2
                    large2 = integration_scores[index]
                    index2 = index
                    if (integration_scores[index] < large1):
                        large2 = large1
                        index2 = index1
                        large1 = integration_scores[index]
                        index1 = index

        if (integration_scores[index1] == integration_scores[index2] and integration_scores[index1] == integration_scores[index3]):
            best_word = valid_words[index1] + ', ' + valid_words[index2] + ', ' + valid_words[index3]
        elif(integration_scores[index1] == integration_scores[index2]):
            best_word = valid_words[index1] + ', ' + valid_words[index2]
        else:
            best_word = valid_words[index1]
    elif (lenScores == 2):
        if(integration_scores[index1] == integration_scores[index2]):
            best_word = valid_words[index1] + ', ' + valid_words[index2]
        else:
            best_word = valid_words[index1]
    elif (lenScores == 1):
        best_word = valid_words[index1]
    else:
        best_word = 'No Result'

    return best_word


@app.route("/")
def init():
    return render_template('index.html')


@app.route('/shark2', methods=['POST'])
def shark2():

    start_time = time.time()
    data = json.loads(request.get_data())

    gesture_points_X = []
    gesture_points_Y = []
    for i in range(len(data)):
        gesture_points_X.append(data[i]['x'])
        gesture_points_Y.append(data[i]['y'])
    gesture_points_X = [gesture_points_X]
    gesture_points_Y = [gesture_points_Y]

    gesture_sample_points_X, gesture_sample_points_Y = generate_sample_points(gesture_points_X[0], gesture_points_Y[0])

    # valid_words, valid_template_sample_points_X, valid_template_sample_points_Y = do_pruning(gesture_points_X, gesture_points_Y, template_sample_points_X, template_sample_points_Y)
    valid_words, valid_template_sample_points_X, valid_template_sample_points_Y = do_pruning(gesture_sample_points_X, gesture_sample_points_Y, template_sample_points_X, template_sample_points_Y)

    shape_scores = get_shape_scores(gesture_sample_points_X, gesture_sample_points_Y, valid_template_sample_points_X, valid_template_sample_points_Y)

    location_scores = get_location_scores(gesture_sample_points_X, gesture_sample_points_Y, valid_template_sample_points_X, valid_template_sample_points_Y)

    integration_scores = get_integration_scores(shape_scores, location_scores)

    best_word = get_best_word(valid_words, integration_scores)

    end_time = time.time()

    return '{"best_word":"' + best_word + '", "elapsed_time":"' + str(round((end_time - start_time) * 1000, 5)) + 'ms"}'


if __name__ == "__main__":
    app.run()
