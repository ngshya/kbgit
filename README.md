# KBGit

KBGit ~~is~~ will be a powerful versioning tool designed specifically for 
managing knowledge bases used by LLM (Large Language Model) based applications. 
By leveraging version control, KBGit allows teams to efficiently track changes, 
collaborate on knowledge assets, and maintain a comprehensive history of updates.

**KBGit is currently in the proof-of-concept (POC) phase.**

To test the code, create a Python environment with `requirements.txt` file, 
rename the  `.env_example` file to `.env` with your own key and start the 
`startup` script. 

The basic unit of KBGit is a Knowledge Base Block, which is an abstraction of
a chunk of text. 

```python
k1 = KBB(kbb_content="UC Berkeley is founded in 2222.")
k2 = KBB(kbb_content="The University of California, Berkeley (UC Berkeley) is a public land-grant research university in Berkeley, California.")
k3 = KBB(kbb_content="Berkeley has an enrollment of more than 45000 students.")
k4 = KBB(kbb_content="UC Berkeley is organized around fifteen schools of study on the same campus.")
k5 = KBB(kbb_content="The official university mascot is Oski the Bear, who debuted in 1941.")

k6 = k5.edit_content("UC Berkeley is founded in 1868 and its mascot is Oski the Bear, who debuted in 1941.")

k1.compute()
k6.compute("Computed after k1 compute.")
```

We can do some basic operations with KBBs. For instance, we could "sum" them 
and then ask for the history of the new KBB. 

```python
k10 = k1 + k3 + k6
k10.compute(msg="Bla bla bla.")
k10.show_kbb_history()
```

The output of the previous block would be:

```
[sum] UC Berkeley was founded in 1868. Its mascot, Oski the Bear, debuted in 1941. The university ha
s an enrollment of more than 45,000 students. [kbb_516361f4-74c3-46bd-a165-601088d88281] [kbn_04c7ad
d5-a27a-4cd3-bc7d-ed31e93fd7a3] [2024-09-30 02:23:03] [2024-09-30 02:23:13] 
     ↑__ [edit] UC Berkeley is founded in 1868 and its mascot is Oski the Bear, who debuted in 1941.
          [kbb_71add81a-4340-4070-8692-a05e51c87a20] [kbn_17a3345d-e8a7-4228-ad89-c88a991cf488] [202
         4-09-30 02:23:02] [2024-09-30 02:23:03] 
     ↑__ [create] Berkeley has an enrollment of more than 45000 students. [kbb_ba74fea8-b280-46dd-85
         24-15b8ac2dc183] [kbn_61934b79-e361-45ff-8c93-3593a67f622f] [2024-09-30 02:23:00] [2024-09-
         30 02:23:05] 
     ↑__ [create] UC Berkeley is founded in 2222. [kbb_6229343d-f936-40e9-99ce-958331321cf0] [kbn_e6
         647a1f-6b7a-437f-93b5-4e43756d344e] [2024-09-30 02:23:00] [2024-09-30 02:23:02] 
```

The information provided by KBB k6 comes later than k1. 
There is conflict when we put them together, the newer information has priority.

Another example of summation of KBBs. 

```python
k11 = sum((k10, k2, k4, k5))
k11.compute(msg="Sum them all!")
print(k11)
```

output: 

```
[sum] The University of California, Berkeley (UC Berkeley) is a public land-grant research university located in Berkeley, California. It was founded in 1868 and has an enrollment of more than 45,000 students. The university is organized around fifteen schools of study on the same campus. The official university mascot is Oski the Bear, who debuted in 1941. [kbb_ed087728-d0b8-48bc-9973-4e54ad4f83c0] [kbn_5a2cb26d-3fda-4fd4-a60b-edcdece4b0ea] [2024-09-30 02:23:13] [2024-09-30 02:23:19] 

```

Of course, we can also forget some pieces of information by using directly the 
"substraction",

```python
k12 = k11 - k6 # k6 was "UC Berkeley is founded in 1868 and its mascot is Oski the Bear, who debuted in 1941." 
k12.compute()
print(k12)
```

output:

```
[sub] The University of California, Berkeley (UC Berkeley) is a public land-grant research university located in Berkeley, California. It has an enrollment of more than 45,000 students. The university is organized around fifteen schools of study on the same campus. [kbb_c2e343ce-2702-4a7f-8742-b2ebf1541710] [kbn_8734ba3b-9f15-43f5-b6ab-6cd464fe8d9d] [2024-09-30 02:23:19] [2024-09-30 02:23:26] 
```

... or, we could re-compute the entire knowledge flow when a particular block 
gets updated. 

```python
k7 = k6.edit_content("Unix was created by alumnus Ken Thompson (BS 1965, MS 1966) along with colleague Dennis Ritchie.") 
k7.compute()
k7.show_node_history()
```

```
[edit] UC Berkeley is founded in 1868 and its mascot is Oski the Bear, who debuted in 1941. [kbb_71add81a-4340-4070-8692-a05e51c87a20] [kbn_17a3345d-e8a7-4228-ad89-c88a991cf488] [2024-09-30 02:23:02] [2024-09-30 02:23:03] 
[create] The official university mascot is Oski the Bear, who debuted in 1941. [kbb_b7b9a55f-0b62-47ed-ab02-32629a2af0bd] [kbn_17a3345d-e8a7-4228-ad89-c88a991cf488] [2024-09-30 02:23:00] [2024-09-30 02:23:01] 
[edit] Unix was created by alumnus Ken Thompson (BS 1965, MS 1966) along with colleague Dennis Ritchie. [kbb_c47fdff0-8eca-489a-baf1-44918e98c9e0] [kbn_17a3345d-e8a7-4228-ad89-c88a991cf488] [2024-09-30 02:23:26] [2024-09-30 02:23:27]
```

```python
k13 = k11.recompute()
print(k13)
```

```python
2024-09-30 02:23:35,912 - kbgit - llm.py -  WARNING - Possible conflicts in the text: There is a contradiction because the text states UC Berkeley was founded in 2222, yet it mentions Ken Thompson as an alumnus who graduated in 1965 and 1966, which is impossible if the university was founded in the future.
[sum] The University of California, Berkeley (UC Berkeley) is a public land-grant research university located in Berkeley, California. It is organized into fifteen schools of study on the same campus and has an enrollment of over 45,000 students. Unix was created by alumni Ken Thompson (BS 1965, MS 1966) and his colleague Dennis Ritchie. [kbb_c16ed54c-70db-4d94-b3fc-97cc8fb17054] [kbn_5a2cb26d-3fda-4fd4-a60b-edcdece4b0ea] [2024-09-30 02:23:39] [2024-09-30 02:23:50] 
```

We can collect many KBBs into a Knowledge Base Document. 

```python
d1 = KBD(kbbs=[k1, k2])
d2 = KBD(kbbs=[k3])
```

and perform operations over them

```python
d3 = d1 + d2
print(d3)
```

```
[kbb_6229343d-f936-40e9-99ce-958331321cf0] UC Berkeley is founded in 2222. 
[kbb_7760805d-b3df-4b99-b7d9-c12b048bae26] The University of California, Berkeley (UC Berkeley) is a public land-grant research university in Berkeley, California. 
[kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183] Berkeley has an enrollment of more than 45000 students. 
```

We could add new blocks to the document in a trivial way

```python
d3 < k4
print(d3)
```

```
[kbb_6229343d-f936-40e9-99ce-958331321cf0] UC Berkeley is founded in 2222. 
[kbb_7760805d-b3df-4b99-b7d9-c12b048bae26] The University of California, Berkeley (UC Berkeley) is a public land-grant research university in Berkeley, California. 
[kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183] Berkeley has an enrollment of more than 45000 students. 
[kbb_c072fc96-591c-428a-b68a-654f501bcdf9] UC Berkeley is organized around fifteen schools of study on the same campus. 

```

or, we could integrate the new knowledge into the document in a smart way

```python
d3 << KBB(kbb_content="UC Berkeley is founded in 1868 and its mascot is Oski the Bear, who debuted in 1941.")
print(d3)
```

```
[kbb_7760805d-b3df-4b99-b7d9-c12b048bae26] The University of California, Berkeley (UC Berkeley) is a public land-grant research university in Berkeley, California. 
[kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183] Berkeley has an enrollment of more than 45000 students. 
[kbb_c072fc96-591c-428a-b68a-654f501bcdf9] UC Berkeley is organized around fifteen schools of study on the same campus. 
[kbb_6f0d1027-2620-4463-89f9-b8fd474892f4] UC Berkeley is an institution founded in 1868. Its mascot is Oski the Bear, who debuted in 1941. 
```

while tracking every updates we are making to the document. 

```python
d3.data["operations"]
```

```
[{'operation': 'sum',
  'kbbs_snapshot': ['kbb_6229343d-f936-40e9-99ce-958331321cf0',
   'kbb_7760805d-b3df-4b99-b7d9-c12b048bae26',
   'kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183'],
  'tms': 1727688231.0164301,
  'parents_kbd': ['kbd_b8157652-4f37-48bc-b439-d73b0be112d6',
   'kbd_fa18add4-1b0b-4235-b239-6dcb87630674']},
 {'operation': 'add',
  'kbb': ['kbb_c072fc96-591c-428a-b68a-654f501bcdf9'],
  'kbbs_snapshot': ['kbb_6229343d-f936-40e9-99ce-958331321cf0',
   'kbb_7760805d-b3df-4b99-b7d9-c12b048bae26',
   'kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183',
   'kbb_c072fc96-591c-428a-b68a-654f501bcdf9'],
  'tms': 1727688231.020071},
 {'operation': 'smart add',
  'kbb': ['kbb_6f0d1027-2620-4463-89f9-b8fd474892f4'],
  'kbbs_snapshot': ['kbb_7760805d-b3df-4b99-b7d9-c12b048bae26',
   'kbb_ba74fea8-b280-46dd-8524-15b8ac2dc183',
   'kbb_c072fc96-591c-428a-b68a-654f501bcdf9',
   'kbb_6f0d1027-2620-4463-89f9-b8fd474892f4'],
  'tms': 1727688232.1469939}]
```


## Next steps
- Idea validation in some experimental settings. 
- Better code design. 
- Unit test. 
- More database back-ends. 
- More LLM services back-ends. 
- Client-server interfaces. Web management tool.