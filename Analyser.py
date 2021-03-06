#encoding: utf8
"""
Do some data-work
烦的时候写写注释 By H.YC
"""
from __future__ import print_function

try:
    import cPickle as pickle
except:
    import pickle

import sys
import os
import numpy as np
import sklearn
from sklearn import linear_model, datasets, metrics
from sklearn.cross_validation import train_test_split
from sklearn.neural_network import BernoulliRBM
from sklearn.pipeline import Pipeline
from jieba.analyse import textrank
from sklearn.grid_search import GridSearchCV

Trained = False
TopK_per_jd = 50
TopK_Words = 4000

def getWordwithWeightFromJD(jd):
    """
    return
    """
    ret = []
    for (w,f) in textrank(jd,topK=TopK_per_jd,
                          withWeight=True,
                          allowPOS=['n','eng','v','a','i','ns','vn']):
        ret.append((w,f))
    wordlist = [r[0] for r in ret]
    flist = [r[1] for r in ret]
    return ret,wordlist,flist

def getWordwithWeight(sentence):
    """
    return
    """
    try:
        salary = float(sentence.split(',')[0])
        jd = sentence[sentence.index(',')+1:]
    except Exception as e:
        return None,None,None,None
    ret,wordlist,flist = getWordwithWeightFromJD(jd)
    return ret,wordlist,flist,salary

def getCountedDict(count_dict,wl,fl,output='CountDict.pkl'):
    """
    word list
    frequence list
    """
    for i in range(len(wl)):
        if count_dict.get(wl[i]) == None:
            count_dict[wl[i]] = fl[i]
        else:
            count_dict[wl[i]] += fl[i]
    return count_dict

def genCountedDict():
    count_dict = {}
    with open(sys.argv[1]) as f:
        index = 0
        for l in f:
            try:
                print('\r genCountedDict Processed {0} line of jd&salary in {1}. \r'.format(index,sys.argv[1]),file=sys.stdout,end=" ")
                index += 1
                _,wl,fl,_ = getWordwithWeight(l)
                if wl == None:
                    continue
                getCountedDict(count_dict,wl,fl)
            except KeyboardInterrupt as e:
                break
    with open('CountedDict.pkl','a+') as pf:
        pickle.dump(count_dict,pf)

def genWholeDict():
    try:
        with open('CountedDict.pkl') as f:
            cd = pickle.load(f)
        scd = sorted(cd.items(),key=lambda k:k[1],reverse=True)
    except Exception,e:
        print(e)
        return None
    return scd

def gen_func_single_XY():
    if Trained == False:
        return None,None
    whole_word_freq_list = genWholeDict()[:TopK_Words]
    whole_word_list = [wi[0] for wi in whole_word_freq_list]
    def single_XY(sentence):
        _,wl,fl,salary = getWordwithWeight(sentence)
        X = np.zeros(len(whole_word_list))
        Y = salary
        for i in range(len(wl)):
            try:
                windex = whole_word_list.index(wl[i])
                X[windex] = fl[i]
            except Exception as e:
                pass
        return (X,Y)
    def single_X(sentence):
        _,wl,fl = getWordwithWeightFromJD(sentence)
        X = np.zeros(len(whole_word_list))
        for i in range(len(wl)):
            try:
                windex = whole_word_list.index(wl[i])
                X[windex] = fl[i]
            except Exception as e:
                pass
        return X
    return single_XY,single_X

get_single_XY,get_single_X = gen_func_single_XY()

def get_clf(clf_pickle="clf.pkl"):
    if Trained == False:
        return None
    with open(clf_pickle) as f:
        clf = pickle.load(f)
    return clf

def genXY(fName,bSave=False,limit=None,skip=0):
    """
    Ofcause return X,y
    it quite complex
    hard to rewrite
    """
    X = []
    y = []
    whole_word_freq_list = genWholeDict()[:TopK_Words]
    print("whole dict load success!")
    whole_word_list = [wi[0] for wi in whole_word_freq_list]
    #whole_freq_list = [wi[1] for wi in whole_word_list]
    with open(fName) as f:
        index = 0
        skip_index = skip
        for l in f:
            try:
                print('\r GenXY Processed {0} line of jd&salary in {1}. \r'.format(index,fName),file=sys.stdout,end=" ")
                index += 1
                if skip_index > 0:
                    skip_index -= 1
                    continue
                _,wl,fl,salary = getWordwithWeight(l)
                if wl == None:
                    continue
                if not limit == None:
                    if index > limit:
                        break
                Xi = np.zeros(len(whole_word_list))
                yi  = salary
                for i in range(len(wl)):
                    try:
                        windex = whole_word_list.index(wl[i])
                        Xi[windex] = fl[i]
                    except Exception as e:
                        pass
                X.append(Xi.tolist())
                y.append(yi)
            except KeyboardInterrupt:
                print("User keyboard interupt!")
                break
    if bSave == True:
        print("saving X,Y dataset!")
        with open('X.pkl','a+') as Xf:
            pickle.dump(X,Xf)
        with open('Y.pkl','a+') as yf:
            pickle.dump(y,yf)
    return X,y

def Train():
    """
    Train Function
    """
    print("loading data...")
    with open('X.pkl') as Xf:
        X = pickle.load(Xf)
    with open('Y.pkl') as Yf:
        Y = pickle.load(Yf)
    """
    if os.path.exists('X_train.pkl') == False:
        print("generate data and split to train test set.")
        with open('X.pkl') as Xf:
            X = pickle.load(Xf)
        with open('Y.pkl') as Yf:
            Y = pickle.load(Yf)
        print("load X,Y success!")
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=0)
        print("dump Train,Test dataset into pickled files..")
        with open('X_train.pkl') as x_train_f:
            pickle.dump(X_train,x_train_f)
        with open('X_test.pkl')  as x_test_f:
            pickle.load(X_test,x_test_f)
        with open('Y_train.pkl') as y_train_f:
            pickle.load(Y_train,y_train_f)
        with open('Y_test.pkl')  as y_test_f:
            pickle.load(Y_test,y_test_f)
        print("dump Train,Test dataset into pickled files finished..")

    print("load data from pickled files..")
    with open('X_train.pkl') as x_train_f:
        X_train = pickle.load(x_train_f)
    with open('X_test.pkl')  as x_test_f:
        X_test  = pickle.load(x_test_f)
    with open('Y_train.pkl') as y_train_f:
        Y_train = pickle.load(y_train_f)
    with open('Y_test.pkl')  as y_test_f:
        Y_test  = pickle.load(y_test_f)
    print("Load Data success!")
    """
    print("Load Data success!")
    params = {'rbm__learning_rate':0.07,
              'rbm__n_iter':100,
              'rbm__n_components':1100,
              'logistic__C':4500}
    logistic = linear_model.LogisticRegression()
    rbm = BernoulliRBM(random_state=0, verbose=True)
    clf = Pipeline(steps=[('rbm', rbm), ('logistic', logistic)])
    #grid_search = GridSearchCV(clf,params,n_jobs = 1,verbose=1);
    #print("start grid search")
    #grid_search.fit(X[-len(Y)/400:],Y[-len(Y)/400:])
    #print("Best score: %0.3f" % grid_search.best_score_)
    #best_params = grid_search.best_score_
    #clf.set_params(**best_params)
    clf.set_params(**params)
    clf.fit(X[-len(X)/2:],Y[-len(Y)/2:])
    #logistic_classifier = linear_model.LogisticRegression(C=100.0)
    #logistic_classifier.fit(X_train, Y_train)
    #print("Logistic regression using raw pixel features:\n%s\n" % (
    #metrics.classification_report(
    #    Y_test,
    #    logistic_classifier.predict(X_test))))
    print("fit complete..")
    print("Logistic regression using RBM features:\n%s\n" % (
    metrics.classification_report(
        Y[-len(Y)/4:],
        clf.predict(X[-len(X)/4:]))))
    with open('clf.pkl','a+') as clf_f:
        pickle.dump(clf,clf_f)
    #Trained = True

if __name__ == '__main__':
    # generate a counted dictionary named 'CountDict.pkl'
    if len(sys.argv) < 2:
        raise Exception("Wrong Argument number!")
    print(sys.argv)
    if os.path.exists('./CountedDict.pkl') == False:
        genCountedDict()
    # generate X,y ====> Hard work here.
    # 1. build an N-length array, generate X with this array
    # 2. paired with y
    if os.path.exists('X.pkl') == False:
        genXY(sys.argv[1],bSave=True,limit=50000,skip=20000)
    Train()
