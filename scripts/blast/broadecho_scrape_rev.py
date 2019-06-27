import re
import math
import pandas as pd 
import numpy as np
from os import listdir
import seaborn as sns
import matplotlib.pyplot as plt

# read in all blast files, one for each sample
blast_output = [f for f in listdir("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/echo_output")]

match_dict = {}
for filename in blast_output:
    match_dict[filename] = {}
    f = open('/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/echo_output/{}'.format(filename))
    for line in f.readlines():
        if re.search("^NC:", line): 
            query, blon, identity, length, mismatches, gaps, \
            q_start, q_end, s_start, s_end, evalue, bit_score = line.split()
            
            blon = blon.split("-")[0]
            if int(length) > 90: # may need to edit if this is not returned in bp
                if blon not in match_dict[filename]:
                    match_dict[filename][blon] = 1
                else:
                    match_dict[filename][blon] += 1

# need to order blons for each sample to be from 2331 to 2361
sorted_dict = sorted(match_dict.items(), key=lambda kv: kv[1])

blons = open("/Users/laurentso/Desktop/repos/bifido/scripts/blast/blon_map.txt", "r")
blon_names = []
for line in blons.readlines():
   blon, nc = line.split()
   blon_names.append(blon)

lengths = open("/Users/laurentso/Desktop/repos/bifido/blast_broad/query/hmo_genes_lengths.txt", "r")
len_dict = {}
for line in lengths.readlines():
    if re.search("^NC", line):
       blon = line.split()[0]
    else:
        len_dict[blon] = line

df = pd.DataFrame(np.nan, index = [i.split('_S')[0] for i in sorted_dict.keys()], columns = blon_names)
for key in sorted_dict.keys():
    df.loc[key.split('_S')[0]] = pd.Series(sorted_dict[key])

log_df = df.copy()
for key in sorted_dict.keys():
    log_df.loc[key.split('_S')[0]] = [math.log(num+0.00000000001) for num in pd.Series(sorted_dict[key])]

normalized_df = df.copy()
for key in sorted_dict.keys():
    norms = [int(num)/int(len) for num, len in zip(pd.Series(sorted_dict[key]), len_dict.values())]
    normalized_df.loc[key.split('_S')[0]] = [math.log(num+0.00000000001) for num in norms]

normalized_df.to_csv("output/normalized.tsv", sep = '\t')

# normal results
plt.subplots(figsize=(20,15))
heatmap = sns.heatmap(df.astype(int))
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_1.png")

# logged results
plt.subplots(figsize=(20,15))
heatmap = sns.heatmap(log_df.astype(int)) #, cmap="YlGnBu")
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_log_1.png")

# logged and normalized results
plt.subplots(figsize=(20,15))
heatmap = sns.heatmap(normalized_df.astype(int)) #, cmap="YlGnBu")
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_log_norm_1.png")

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
children = [i for i in sorted_dict.keys() if not i.startswith("M")]
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

plt.subplots(figsize=(5,15))
mask = meta_df.isnull()
heatmap = sns.heatmap(meta_df, mask=mask)
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_meta.png")

# ---------------------------------------------------------------------------------------------------------

norm_df = normalized_df.copy()
samples = [re.sub('-', '_', i.split('_S')[0]) for i in sorted_dict.keys()]
subjects = [str(id_dict[sample]) for sample in samples]

# create an adjusted index such that children sorted on top, then mothers sorted on bottom
adj_index = []
for i in subjects:
    if len(i.split("_")) > 1:
        adj_index.append(int(i.split("_")[0]) + 9999) # add 999 to the adjusted index of mothers
    else:
        adj_index.append(int(i))

norm_df.index = subjects

# assign adj_index to column, sort df by it, then drop it
norm_df["adj_index"] = adj_index
norm_df.sort_values(by=['adj_index'], inplace=True)
norm_df = norm_df.drop('adj_index', 1)

plt.subplots(figsize=(20,15))
heatmap = sns.heatmap(norm_df.astype(int)) #, cmap="YlGnBu")
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_log_norm_adj_1.png")

# just samples with blon 2355 to focus in on infantis
df_2355 = norm_df.copy()
df_2355 = df_2355[df_2355['Blon_2355'] > -12]

plt.subplots(figsize=(20,15))
heatmap = sns.heatmap(df_2355.astype(int)) #, cmap="YlGnBu")
fig = heatmap.get_figure()
fig.savefig("/Users/laurentso/Desktop/repos/bifido/scripts/blast/output/existing_broadecho_log_norm_adj_2355.png")

