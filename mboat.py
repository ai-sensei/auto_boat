#%%
#test
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import datetime

#小数変換可能か
def float_convertable(value):
    try:
        temp = float(value)
        return True
    except:
        return False

#日付が存在するかどうかチェック関数
def checkDate(year,month,day):
    try:
        newDataStr="%04d/%02d/%02d"%(year,month,day)
        newDate=datetime.datetime.strptime(newDataStr,"%Y/%m/%d")
        return True
    except ValueError:
        return False

# urlからbeautifulsoupオブジェクトを返す関数
def ret_soup(url, params=False):
    if params:
        response = requests.get(url, params=params)
    else:
        response = requests.get(url)

    if response.status_code == 200:
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text,'html.parser')

        return soup
    else:
        return False

# その日開催されているレース場を返す関数
def ret_open_fields(hd):
    url = 'https://www.boatrace.jp/owpc/pc/race/index?hd='+hd
    soup = ret_soup(url)
    if soup:
        field_list = []
        for i in soup.find_all('td',class_='is-arrow1 is-fBold is-fs15'):
            field_list.append(i.find('img')['alt'])
        
        return field_list # ex:['戸田', '江戸川']
    else:
        return []

# 侵入コースを返す関数
def ret_invasion_course(soup):
    course = soup.find('tbody',class_='is-p10-0')
    invasion_course_list = []
    for i in course.find_all('span'):
        if 'table1_boatImage1Number' in str(i):
            invasion_course_list.append(int(i.text))
    if len(invasion_course_list) == 6:
        col = ['in1','in2','in3','in4','in5','in6']
        invasion_course = pd.DataFrame([invasion_course_list],columns=col)

        return invasion_course
    else:
        return False

# レース場コンディションを返す関数
def ret_field_conditions(soup):
    conditions = soup.find('div',class_='weather1_body').find_all('p')
    wether = int(str(conditions[1]).split('is-weather')[1].split('"')[0]) #1:晴れ 2:曇り、、、、
    wind_vector = int(str(conditions[2]).split('is-wind')[1].split('"')[0]) # 時計回りに1~16

    conditions = soup.find('div',class_='weather1_body').find_all('span')
    tempreature = float(conditions[1].text.split('℃')[0])
    wind_speed = float(conditions[4].text.split('m')[0])
    water_tempreature = float(conditions[6].text.split('℃')[0])
    water_hight = float(conditions[8].text.split('cm')[0])

    col = ['wether','wind vector','tempreature','wind speed','water tempreature','water hight']
    conditions = pd.DataFrame([[wether, wind_vector, tempreature, wind_speed, water_tempreature, water_hight]],columns=col)
    
    return conditions

# 展示タイムを返す関数
def ret_exhibition_times(soup):
    racers = soup.find_all('div', class_='table1')[1].find('table').find_all('tbody')

    time_list = []
    for r in racers:
        time_list.append(float(r.find_all('td')[4].text))

    col = ['t1','t2','t3','t4','t5','t6']
    exhibition_times = pd.DataFrame([time_list], columns=col)

    return exhibition_times

# 展示スタートタイムを返す関数
def ret_exhibition_starts(soup, invasion_course):
    course = soup.find('tbody',class_='is-p10-0')
    starts = course.find_all('span', class_='table1_boatImage1Time')
    
    exhibition_starts = {}
    starts = [float(i.text) if float_convertable(i.text) else 1 for i in starts]
    for i in range(6):
        rnum = invasion_course['in{}'.format(i+1)]
        exhibition_starts['st{}'.format(rnum[0])] = starts[i]
    exhibition_starts = pd.DataFrame([exhibition_starts])

    return exhibition_starts

# そのレースの事前情報を返す関数
def ret_prior_information(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/beforeinfo'
    soup = ret_soup(url, params)
    
    if soup:
        invasion_course = ret_invasion_course(soup)
        field_conditions = ret_field_conditions(soup)
        exhibition_times = ret_exhibition_times(soup)
        exhibition_starts = ret_exhibition_starts(soup, invasion_course)
        
        prior_information = pd.concat([exhibition_times,exhibition_starts, invasion_course, field_conditions],axis=1)

        return prior_information
    
    else:
        return False

# そのレースの出走表と結果を返す関数
def ret_racecard_results(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/raceresult'
    soup = ret_soup(url, params)
    
    if soup:
        race_result = soup.find('table',class_='is-w495')
        table = race_result.find_all('td')
        arrive = []
        for i in range(6):
            if table[1+4*i].text in ['1','2','3','4','5','6']:
                arrive.append(table[1+4*i].text)
        
        race_card = []
        if len(arrive) == 6:
            arrive=pd.DataFrame([arrive],columns=['ar1','ar2','ar3','ar4','ar5','ar6'])
            for i in ['1','2','3','4','5','6']:
                for j in range(6):
                    if table[1+4*j].text == i:
                        race_card.append(table[2+4*j].find_all('span')[0].text)
            race_card = pd.DataFrame([race_card],columns=['e1','e2','e3','e4','e5','e6'])

            return race_card, arrive
        else:
            return False
    else:
        return False

# そのレースの選手グレードと勝率を返す関数
def ret_grade_rate(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/racelist'
    soup = ret_soup(url, params)
    if soup:
        h2 = soup.find_all('td', class_='is-lineH2')

        grade = []
        for i in range(6):
            gn = soup.find_all('div', class_='is-fs11')[i*2].find('span').text
            grade.append(gn)
        
        grade = pd.DataFrame(grade).T
        grade.columns = ['g1', 'g2', 'g3', 'g4', 'g5', 'g6']

        rate = {}
        for i in range(6):
            zenkoku = h2[1+5*i].text.split('\n')
            z1 = zenkoku[0].replace(' ','').replace('\r','')
            z2 = zenkoku[1].replace(' ','').replace('\r','')
            z3 = zenkoku[2].replace(' ','').replace('\r','')
            rate['{}_z1'.format(i+1)] = z1
            rate['{}_z2'.format(i+1)] = z2
            rate['{}_z3'.format(i+1)] = z3

            tochi = h2[2+5*i].text.split('\n')
            to1 = tochi[0].replace(' ','').replace('\r','')
            to2 = tochi[1].replace(' ','').replace('\r','')
            to3 = tochi[2].replace(' ','').replace('\r','')
            rate['{}_to1'.format(i+1)] = to1
            rate['{}_to2'.format(i+1)] = to2
            rate['{}_to3'.format(i+1)] = to3

        rate = pd.DataFrame([rate])

        return grade, rate
    
    else:
        return False


# オッズの雛形を返す関数
def ret_odds(url, params):
    soup = ret_soup(url, params)
    if soup:
        oddslist = []
        odds = soup.find_all('td',class_='oddsPoint')
        if len(odds) == 0:
            return False
        else:
            for o in odds:
                if o.text == '欠場':
                    oddslist.append(0)
                else:
                    oddslist.append(float(o.text.split('-')[0]))

            return oddslist
    else:
        return False 

def ret_san_rentan(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/odds3t'
    odds_list = ret_odds(url, params)
    if odds_list:
        col = []
        for i in range(6):
            for j in range(6):
                if not i == j:
                    for k in range(6):
                        if not (j == k or i == k):
                            col.append('t'+str((i+1)*100+(j+1)*10+(k+1)))
        col = np.array(col).reshape(6,20).T
        col = list(col.reshape(120,))
        odds_san_rentan = pd.DataFrame([odds_list],columns=col)

        return odds_san_rentan
    
    else:
        return False

def ret_san_renfuk(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/odds3f'
    odds_list = ret_odds(url, params)
    if odds_list:
        col = ['p123','p124','p125','p126',
                'p134','p234','p135','p235','p136','p236',
                'p145','p245','p345','p146','p246','p346',
                'p156','p256','p356','p456']
        odds_san_renfuk = pd.DataFrame([odds_list],columns=col)

        return odds_san_renfuk
    
    else:
        return False

def ret_ni_rentan_fuk(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/odds2tf'
    odds_list = ret_odds(url, params)
    if odds_list:
        odds_ni_rentan = odds_list[:30]
        odds_ni_renfuk = odds_list[30:]
        col_t2 = ['t12','t21','t31','t41','t51','t61',
                  't13','t23','t32','t42','t52','t62',
                  't14','t24','t34','t43','t53','t63',
                  't15','t25','t35','t45','t54','t64',
                  't16','t26','t36','t46','t56','t65']
        odds_ni_rentan = pd.DataFrame([odds_ni_rentan],columns=col_t2)

        col_p2 = ['p12',
                  'p13','p23',
                  'p14','p24','p34',
                  'p15','p25','p35','p45',
                  'p16','p26','p36','p46','p56']
        odds_ni_renfuk = pd.DataFrame([odds_ni_renfuk],columns=col_p2)

        return odds_ni_rentan, odds_ni_renfuk
    
    else:
        return False, False

def ret_kakuren_fuk(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/oddsk'
    odds_list = ret_odds(url, params)
    if odds_list:
        col = ['p12',
               'p13','p23',
               'p14','p24','p34',
               'p15','p25','p35','p45',
               'p16','p26','p36','p46','p56']
        odds_kakuren_fuk = pd.DataFrame([odds_list],columns=col)

        return odds_kakuren_fuk
    
    else:
        return False

def ret_tan_fuk(hd, jcd, rno):
    params = {'hd': hd, 'jcd': jcd, 'rno': rno}
    url = 'https://www.boatrace.jp/owpc/pc/race/oddstf'
    odds_list = ret_odds(url, params)
    if odds_list:
        odds_tansho = odds_list[:6]
        col_t = ['t1.1','t2.1','t3.1','t4.1','t5.1','t6.1']
        odds_tansho = pd.DataFrame([odds_tansho],columns=col_t)

        odds_fuksho = odds_list[6:]
        col_f = ['f1','f2','f3','f4','f5','f6']
        odds_fuksho = pd.DataFrame([odds_fuksho],columns=col_f)

        return odds_tansho, odds_fuksho
    
    else:
        return False

def ret_all_odds(hd, jcd, rno):
    san_rentan = ret_san_rentan(hd, jcd, rno)
    san_renfuk = ret_san_renfuk(hd, jcd, rno)
    ni_rentan, ni_renfuk = ret_ni_rentan_fuk(hd, jcd, rno)
    kakuren_fuk = ret_kakuren_fuk(hd, jcd, rno)
    tansho, fuksho = ret_tan_fuk(hd, jcd, rno)

    odds_data = pd.concat([san_rentan,
                           san_renfuk,
                           ni_rentan,
                           ni_renfuk,
                           kakuren_fuk,
                           tansho,
                           fuksho], axis=1)
    
    return odds_data

field_dic = {'桐生':'01','戸田':'02','江戸川':'03', 
            '平和島':'04','多摩川':'05','浜名湖':'06',
            '蒲郡':'07','常滑':'08','津':'09',
            '三国':'10','びわこ':'11','住之江':'12',
            '尼崎':'13','鳴門':'14','丸亀':'15',
            '児島':'16','宮島':'17','徳山':'18',
            '下関':'19','若松':'20','芦屋':'21',
            '福岡':'22','唐津':'23','大村':'24'}

#%%
dataframe = pd.read_csv('https://boatrace--data.s3.ap-northeast-1.amazonaws.com/boatrace_data.csv', index_col=0)
#%%
hd = '{}{}{}'.format(2022, str(2).zfill(2), str(12).zfill(2))
jcd = '03'
rno = 1

open_fields = ret_open_fields(hd)
print(open_fields)
#%%
racecard, results = ret_racecard_results(hd,jcd,rno)
grades, rates = ret_grade_rate(hd,jcd,rno)
prior_information = ret_prior_information(hd,jcd,rno)
odds = ret_all_odds(hd,jcd,rno)
#%%
race_data = pd.concat([racecard, grades, rates, prior_information, results, odds],axis=1)
race_data = race_data.rename(index={0: int('{}{}{}'.format(hd, str(jcd).zfill(2), str(rno).zfill(2)))})
# %%
race_data
# %%
