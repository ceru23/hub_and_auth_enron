import numpy as np
from email.parser import Parser
import os
from tqdm import tqdm
import re
from collections import Counter,defaultdict


def read_files(dir):
    '''
    Generates two lists of senders and relative receivers
    All the file are stored in subfolders of dir passed as input
    Files are read and preprocessed during extraction
    Mails are collected only if both sender and at least one receiver
    are mail accounts of Enron employees

    Returns:     two lists with sender[i] -> recevier[i]
    '''

    sender = []
    receiver = []

    for directory, subdirectory, filenames in tqdm(os.walk(dir)):
        for file in filenames:
            mail_file = os.path.join(directory,file)
            with open(mail_file,"r",encoding='utf-8',errors='ignore') as f:
                mail = Parser().parse(f)
                s = mail['from']
                r = mail['to']
                c = mail['cc']
                s_clean = ""
                r_clean = ""
                c_clean = ""

                if(s is None or len(s.split(","))>1):
                    break
                else:
                    if("enron" in s and not 'email' in s):
                        s_clean = re.sub("[ \t\n]","",s)
                if(r is None):
                    break
                else:
                    r_clean = [re.sub("[ \t\n]","",l) for l in r.split(",") \
                                if "enron" in l and not 'email' in l]
                if(c is not None):
                    c_clean = [re.sub("[ \t\n]","",l) for l in c.split(",") \
                                if "enron" in l and not 'email' in l]
                    r_clean = r_clean+c_clean

                if(len(s_clean)>0 and len(r_clean)>0):
                    sender.append(s_clean)
                    receiver.append(r_clean)

    return sender,receiver

def create_adjacency_matrix(sender,receiver):
    '''
    Generates adjacency matrix given sender and receiver lists
    Return a collections.Counter matrix indexed by a tuple
    (sender,receiver) that contains the number of mail exchanged
    between the two. It also returns indexing of accounts
    with integer and vice versa.

    Returns:    adjacency matrix Counter
                two dictionaries ind[account->int], rev_ind[int->account]

    '''

    adj_mat = Counter()
    account = set()

    for i in range(len(sender)):
        s = sender[i]
        account.add(s)
        for r in receiver[i]:
            if(s!=r):               ###Avoid self messaging
                adj_mat[(s,r)] += 1
                account.add(r)

    ind = {a:i for i,a in enumerate(account)}
    rev_ind = {i:a for i,a in enumerate(account)}

    return adj_mat,ind,rev_ind


def create_graph(adj_mat):
    '''
    Generates a graph based on the input adjacency matrix
    Graph is a dictionary where each item (sender)
    is a set (receivers)

    Returns:    graph dictionary
    '''

    graph = defaultdict(set)
    for i,_ in adj_mat.items():
        graph[i[0]].add(i[1])
    return graph


def hits(graph,adj_mat,ind,rev_ind,iters=20,k=5):
    '''
    HITS algorithm on weighted directed Graph
    in input requires a graph, its adjacency matrix,
    indexes of node to int, and int to node
    Default number of iterations is 20
    and k (default=5) is the top-k score for
    authority and hub scores

    Returns:    two lists hub and authority score
                for every node in the graph

    '''


    hub = np.ones(len(ind))
    aut = np.ones(len(ind))

    for it in range(iters):
        norm_aut = 0
        for account,_ in ind.items():
            incoming_acc = [asend for (asend,arec) in graph.items() if account in arec] # get incoming accounts
            t_aut = 0
            if(len(incoming_acc)>0):
                aut_incoming = [adj_mat[(send,account)]*hub[ind[send]] for send in incoming_acc] # weight*hub
                t_aut = np.sum(aut_incoming)
            aut[ind[account]] = t_aut

            norm_aut += t_aut**2

        norm_aut = np.sqrt(norm_aut)
        aut = aut/norm_aut

        norm_hub = 0
        for account,_ in ind.items():
            outgoing_acc = graph[account] # get outgoing accounts
            t_hub = 0
            if(len(outgoing_acc)>0):
                hub_outgoing = [adj_mat[(account,rec)]*aut[ind[rec]] for rec in outgoing_acc] # weight * authority
                t_hub = np.sum(hub_outgoing)
            hub[ind[account]] = t_hub

            norm_hub += t_hub**2


        norm_hub = np.sqrt(norm_hub)
        hub = hub/norm_hub


        top_k_hub = np.argsort(hub).tolist()[::-1][:k]
        top_k_aut = np.argsort(aut).tolist()[::-1][:k]

        print("-----------------------")
        print("Finished iteration ",it)
        print("-----------------------")
        print("TOP HUBS:        ",[rev_ind[x] for x in top_k_hub])
        print("TOP AUTHORITIES: ",[rev_ind[x] for x in top_k_aut])
        print("-----------------------")

    return aut,hub


if __name__ == '__main__':

    DIR = "enron_mail_20150507/maildir/"

    s,r = read_files(DIR)
    adj_mat,ind,rev_ind = create_adjacency_matrix(s,r)
    graph = create_graph(adj_mat)
    aut,hub = hits(graph,adj_mat,ind,rev_ind)
