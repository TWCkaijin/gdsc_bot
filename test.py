import os 

ID_list = {}
user_id = '123'
stu_id = '567'
ID_list[user_id] = stu_id


# Load the ID_list from a file
with open(f'{os.getcwd()}/ID_list.txt', 'r') as f:
    for line in f:
        (key, val) = line[0:-1].split(':')
        ID_list[key] = val
    f.close()

with open(f'{os.getcwd()}/ID_list.txt', 'w') as f:
    for user, id in ID_list.items():
        f.writelines(f'{user}:{id}\n')
    f.close()


print(ID_list)