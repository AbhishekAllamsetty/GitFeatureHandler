from git import Repo, Commit
from datetime import datetime

path = 'D:\\Office_work\\b2b_s2p_data_platform'

repo = Repo(path)

hash_lst = []
commits_lst = []
dit = {'M':[], 'A': [], 'D': [], 'R': []}
#print(repo)

for edge in ["EDGE-104108", "EDGE-91189"]:
    for commit in repo.iter_commits():
        dt = commit.committed_datetime.strftime("%d-%m-%Y %H:%M:%S")
        if commit.message.__contains__(edge):
            #print("{}   {}    {}".format(commit.hexsha, dt, commit))
            #hash_lst.append(commit)
            #print("{}   {}".format(repo.git.diff(commit, name_only=True), repo.git.diff(commit).iter_change_type))#
            #for objpath, stats in commit.stats.files.items():
            print("\n\n")
            a = [commit, commit.committed_datetime.strftime("%d-%m-%Y %H:%M:%S:%f"), edge]
            commits_lst.append(a)
            print(a)
            print(a[0], a[1])
            for item in repo.index.diff(commit):
                #print(item.a_path, item.change_type)
                if str(item.change_type) == 'A':
                    dit['A'].append(item.a_path)

                elif str(item.change_type) == 'M':
                    dit['M'].append(item.a_path)

                elif str(item.change_type) == 'D':
                    dit['D'].append(item.a_path)

                elif str(item.change_type) == 'R':
                    d = {'old_path': item.b_blob.path, 'new_path': item.a_path}
                    print(item.b_blob.path, item.a_path)
                    dit['R'].append(d)

print(dit['R'])
print(sorted(commits_lst, key=lambda x: datetime.strptime(x[1], "%d-%m-%Y %H:%M:%S:%f"), reverse=False))
print(len(commits_lst))


#for item in repo.index.diff('c760bba00c02cb9a631c3aec7be458d29877b629'):
#    print(item.a_path, item.change_type)
