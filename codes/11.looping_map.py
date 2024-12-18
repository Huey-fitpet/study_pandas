
def add_elements(first, second=1):
    result = first + second
    return result
    

list_first = [1,2,3]
list_second = [4,5,6]

# for
# for number_first in list_first:
#     result = add_elements(number_first)
#     pass
# result_list = []
# for number_first, number_second in zip(list_first, list_second):
#     result = add_elements(number_first, number_second)
#     result_list.append(result)

# # map() : callback function
# result_map = map(add_elements, list_first)

# temp1=list(result_map)
# temp2=list(result_map) # iterator return 이라서 이미 iter의 끝이라서 안나옴 like cursor, 

# result_map = map(add_elements, list_first, list_second)
# temp1=list(result_map)

# apply() with pandas
data = {
    'col_first' : list_first,
    'col_second' : list_second
    }

import pandas as pd
df_first = pd.DataFrame(data)
# result_df = df_first['col_first'].apply(add_elements)
# result_df = df_first.apply(add_elements, axis=0)
# result_df = df_first.apply(add_elements, axis=1)

def add_elements_df(serise_bundle):
    result = serise_bundle['col_first'] + serise_bundle['col_second']
    return result
    

df_first['add_elements'] = df_first.apply(add_elements_df, axis=1) # 한레코드 단위

pass
