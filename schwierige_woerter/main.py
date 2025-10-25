import re

with open("worter.txt", "r", encoding="utf-8") as f:
    html = f.read()

trs = html.split("<tr>")

sub_patterns = [r"<td>", r"<a .*?>", r"</a>", r"<span .*?>", r"</span>", r"</td>", r"</tr>", r"&nbsp;", r"</tbody>"]
skip_patters = [r"^[A-Z]$", r"<strong>", r"^<tbody>$"]
res = []
for x in trs:
    tds = x.split("<td>")
    tds_c = []
    for y in tds:
        if y:
            for z in sub_patterns:
                y = re.sub(z, "", y)
            if y:
                tds_c.append(y)
    for y in skip_patters:
        if re.search(y, tds_c[0]):
            break
    else:
        if len(tds_c) == 4:
            res.append(tds_c[0])
            res.append(tds_c[2])
        elif len(tds_c) == 2:
            res.append(tds_c[0])
        else:
            res.append(tds_c)



with open("out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(res))

with open("worter2.txt", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()
res2 = []
for x in lines:
    if x and len(x) > 1:
        res2.append(x)




with open("out.txt", "a", encoding="utf-8") as f:
    f.write("\n".join(res2))

with open("worter3.txt", "r", encoding="utf-8") as f:
    liness = f.read().splitlines()


res3 = []

for x in liness:
    if x and ":" in x:
        res3.append(x.split(":")[0])


with open("out.txt", "a", encoding="utf-8") as f:
    f.write("\n".join(res3))


with open("out.txt", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

s = set()

for x in lines:
    s.add(x)

with open("out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(list(s)))