#%%
import time
from multiprocessing import Pool

import pandas as pd
import mboat as mb
#%%
def get_racedata(hd_jcd_rno):
    hd = hd_jcd_rno[0]
    jcd = hd_jcd_rno[1]
    rno = hd_jcd_rno[2]

    racecard, results = mb.ret_racecard_results(hd,jcd,rno)
    grades, rates = mb.ret_grade_rate(hd,jcd,rno)
    prior_information = mb.ret_prior_information(hd,jcd,rno)
    odds = mb.ret_all_odds(hd,jcd,rno)

    race_data = pd.concat([racecard, grades, rates, prior_information, results, odds],axis=1)
    race_data = race_data.rename(index={0: int('{}{}{}'.format(hd, str(jcd).zfill(2), str(rno).zfill(2)))})

    return race_data

#%%
mb.field_dic
#%%
dataframe = pd.read_csv('https://boatrace--data.s3.ap-northeast-1.amazonaws.com/boatrace_data.csv', index_col=0)

#%%
yy = 2018
mm = 1
dd = 1
rno = 1
hd = '{}{}{}'.format(yy, str(mm).zfill(2), str(dd).zfill(2))
open_fields = mb.ret_open_fields(hd)
print(open_fields)
#%%
i = 0
jcd = mb.field_dic[open_fields[i]]
r = 0
rno = r+1

hd_jcd_rno = [hd, jcd, rno]
race_data = get_racedata(hd_jcd_rno)
race_data
#%%
val_list = []
for r in range(12):
    rno = r+1
    val_list.append([hd, jcd, rno])
val_list
#%%
if __name__ == '__main__':
    tt = time.time()
    with Pool(processes=6) as p:
        result = p.map(get_racedata, val_list)
    print(time.time()-tt)

# %%
