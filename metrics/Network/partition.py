import psycopg2
import consts
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import eigs

connection = psycopg2.connect(**consts.db_creds)


def get_users():
    cursor = connection.cursor()
    select_users = ''' SELECT usr, other_usr
                       FROM influences'''
    cursor.execute(select_users)
    users = set()
    fetched = [None]
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        for record in fetched:
            users.add(record[0])
            users.add(record[1])
    return list(users)


def get_incidence_matrix(users_list):
    users_dict = {}
    for i, user in enumerate(users_list):
        users_dict[user] = i
    cursor = connection.cursor()
    get_size = ''' SELECT COUNT(*)
                   FROM influences;'''
    cursor.execute(get_size)
    num_edges = cursor.fetchall()[0]
    select_influence = ''' SELECT usr, other_usr
                           FROM influences'''
    cursor.execute(select_influence)
    data = []
    i = []
    j = []
    fetched = [None]
    count = 0
    while len(fetched) > 0:
        fetched = cursor.fetchall()
        for edge in fetched:
            vertices = (users_dict[edge[0]], users_dict[edge[1]])
            if vertices[0] == vertices[1]:
                continue
            data.extend([-1., 1.])
            i.extend([count, count])
            j.extend([min(*vertices), max(*vertices)])
            count += 1
    return coo_matrix((data, (i, j)), shape = (int(num_edges[0]), len(users_list)))


def get_partition(users_list):
    incidence = get_incidence_matrix(users_list)
    laplacian = incidence.transpose()*incidence
    w, v = eigs(laplacian)
    inds = np.argsort(np.real(w))
    group1 = []
    group2 = []
    for i, value in enumerate(v[:, inds[1]]):
        if value > 0:
            group1.append(users_list[i])
        else:
            group2.append(users_list[i])
    return group1, group2


get_partition(sorted(get_users()))


