import re
import math
import pandas as pd 
import numpy as np
from os import listdir
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix

# read in all blast files, one for each sample
blast_output = [f for f in listdir("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/echo_output")]

match_dict = {}
for filename in blast_output:
    match_dict[filename] = {}
    f = open('/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/echo_output/{}'.format(filename))
    for line in f.readlines():
        if re.search("^# Query:", line): # if line with the HMO query
            query = "NC_011593.1:"+(line.split(":")[2].split()[0].strip())

        if re.search("hits found$", line): # if line with the number of hits
            num_hits = line.split()[1].strip()
            if query not in match_dict[filename]:
                match_dict[filename][query] = int(num_hits)
            else:
                match_dict[filename][query] += int(num_hits)

        # if alignment length is less than 90bp, consider number of hits to be 0
        if re.search("^NC", line):
            query, genome, identity, length, mismatches, gaps, \
            q_start, q_end, s_start, s_end, evalue, bit_score = line.split()
            if int(length) < 90:
                match_dict[filename][query] -= 1

blons = open("/Users/laurentso/Desktop/repos/bifido/scripts/blast/blon_map.txt", "r")
queries = []
blon_names = []
for line in blons.readlines():
   blon, nc = line.split()
   queries.append(nc)
   blon_names.append(blon)

lengths = open("/Users/laurentso/Desktop/repos/bifido/blast_broad/query/hmo_genes_lengths.txt", "r")
len_dict = {}
for line in lengths.readlines():
    if re.search("^NC", line):
       blon = line.split()[0]
    else:
        len_dict[blon] = line

df = pd.DataFrame(np.nan, index = [i.split('_S')[0] for i in match_dict.keys()], columns = queries)
for key in match_dict.keys():
    df.loc[key.split('_S')[0]] = pd.Series(match_dict[key])
df.columns = blon_names

log_df = df.copy()
for key in match_dict.keys():
    log_df.loc[key.split('_S')[0]] = [math.log(num+0.00000000001) for num in pd.Series(match_dict[key])]

normalized_df = df.copy()
for key in match_dict.keys():
    norms = [int(num)/int(len) for num, len in zip(pd.Series(match_dict[key]), len_dict.values())]
    normalized_df.loc[key.split('_S')[0]] = [math.log(num+0.00000000001) for num in norms]

# normalized_df.to_csv("output/normalized.tsv", sep = '\t')

# # normal results
# plt.subplots(figsize=(20,15))
# heatmap = sns.heatmap(df.astype(int))
# fig = heatmap.get_figure()
# fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/broadecho.png")

# # logged results
# plt.subplots(figsize=(20,15))
# heatmap = sns.heatmap(log_df.astype(int)) #, cmap="YlGnBu")
# fig = heatmap.get_figure()
# fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/broadecho_log.png")

# # logged and normalized results
# plt.subplots(figsize=(20,15))
# heatmap = sns.heatmap(normalized_df.astype(int), cmap="diverging")
# fig = heatmap.get_figure()
# fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/broadecho_log_norm.png")

# ---------------------------------------------------------------------------------------------------------

mapping = pd.read_csv('/Users/laurentso/Desktop/repos/bifido/scripts/metadata/master_fecal_samples.csv')
metadata = pd.read_csv('/Users/laurentso/Desktop/repos/bifido/scripts/metadata/metadata_with_brain.csv')

# need to get a dictionary of sample id to subject id
ids = list(zip(mapping["SampleID"], mapping["SubjectID"]))
id_dict = {}
for sample, subject in ids:
    if sample.startswith("M"):
        id_dict[sample] = str(subject)+"_m"
    else:
        id_dict[sample] = subject

# need to create dataframe with ids as subject ids and age (metadata)
children = [i for i in match_dict.keys() if not i.startswith("M")]
samples = [re.sub('-', '_', i.split('_S')[0]) for i in children]
subjects = [id_dict[sample] for sample in samples]
meta_df = pd.DataFrame(np.nan, index = subjects, columns = ["age"])
meta_df.sort_index(inplace=True)

for key in subjects:
    if key in list(metadata["subject"]):
        index = metadata.index[metadata['subject'] == key]
        meta_df.loc[key] = metadata.iloc[index[0]]['correctedAgeDays'] / 365
    else:
        meta_df.loc[key] = np.nan

print(len(meta_df[meta_df["age"] <= 2.]))
print(len(set(meta_df.index[meta_df["age"] <= 2.].tolist())))
print(len(set(meta_df.index[meta_df["age"] > 2.].tolist())))

# plt.subplots(figsize=(5,15))
# mask = meta_df.isnull()
# heatmap = sns.heatmap(meta_df, mask=mask)
# fig = heatmap.get_figure()
# fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_meta.png")

# ---------------------------------------------------------------------------------------------------------

norm_df = normalized_df.copy()
samples = [re.sub('-', '_', i.split('_S')[0]) for i in match_dict.keys()]
subjects = [str(id_dict[sample]) for sample in samples]

# create an adjusted index such that children sorted on top, then mothers sorted on bottom
adj_index = []
for i in subjects:
    if len(i.split("_")) > 1:
        adj_index.append(int(i.split("_")[0]) + 9999) # add 9999 to the adjusted index of mothers
    else:
        adj_index.append(int(i))

norm_df.index = subjects

# assign adj_index to column, sort df by it, then drop it
norm_df["adj_index"] = adj_index
norm_df.sort_values(by=['adj_index'], inplace=True)
kid_df = norm_df.copy()
norm_df = norm_df.drop('adj_index', 1)

kid_df = kid_df[kid_df["adj_index"] < 9999]
kid_df = kid_df.drop('adj_index', 1)

# dm = pd.DataFrame(distance_matrix(norm_df.values, norm_df.values), index=norm_df.index, columns=norm_df.index)
# dm.to_csv("output/broadecho_dm.csv")

plt.subplots(figsize=(20,15))
# heatmap = sns.clustermap(norm_df.astype(int), yticklabels=False) #, yticklabels=True, figsize=(100, figure_height)) #, cmap="YlGnBu")
heatmap = sns.heatmap(kid_df.astype(int), yticklabels=False) #, yticklabels=True, figsize=(100, figure_height)) #, cmap="YlGnBu")
fig = heatmap.get_figure()
# heatmap.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/broadecho_cluster.png")
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/broadecho_log_norm_adj.png")

# # just samples with blon 2355 to focus in on infantis
# df_2355 = norm_df.copy()
# df_2355 = df_2355[df_2355['Blon_2355'] > -12]

# plt.subplots(figsize=(20,15))
# heatmap = sns.heatmap(df_2355.astype(int)) #, cmap="YlGnBu")
# fig = heatmap.get_figure()
# fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_log_norm_adj_2355.png")